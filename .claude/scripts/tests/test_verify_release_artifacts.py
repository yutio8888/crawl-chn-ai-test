#!/usr/bin/env python3
"""Negative-mutation coverage for the desktop release artifact gate."""

from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/verify_release_artifacts.py"
SPEC = importlib.util.spec_from_file_location("verify_release_artifacts", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

TAG = "0.34.1-zh5-1-001"
COMMIT = "a" * 40


class ReleaseArtifactTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        self.source_root = self.root / "source"
        self.source_root.mkdir()
        self.dmg_fixtures = self.root / "dmg-fixtures"
        self.dmg_fixtures.mkdir()
        base_rules = MODULE.artifact_rules(TAG)
        for rule in base_rules:
            for contract in rule.content_sources:
                source = self.source_root / contract.source
                source.parent.mkdir(parents=True, exist_ok=True)
                if not source.exists():
                    source.write_bytes(f"source:{contract.source}\n".encode())
        for relative in (
            "crawl-ref/source/dat/database/zh/messages.txt",
            "crawl-ref/source/dat/descript/zh/monsters.txt",
        ):
            source = self.source_root / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(f"source:{relative}\n".encode())
        self.rules = MODULE.release_rules(TAG, self.source_root)
        self._write_valid_set()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _payloads(self, rule) -> dict[str, bytes]:
        payloads = {
            name: f"fixture:{name}\n".encode() for name in rule.required_files
        }
        for contract in rule.content_sources:
            payload = (self.source_root / contract.source).read_bytes()
            if contract.normalize_crlf:
                payload = payload.replace(b"\n", b"\r\n")
            payloads[contract.member] = payload
        return payloads

    def _write_zip(
        self,
        rule,
        payloads: dict[str, bytes],
        *,
        extra: list[tuple[str, bytes, int | None]] | None = None,
        mode_overrides: dict[str, int] | None = None,
    ) -> None:
        with zipfile.ZipFile(
            self.artifacts / rule.filename, "w", zipfile.ZIP_DEFLATED
        ) as archive:
            for name, payload in payloads.items():
                info = zipfile.ZipInfo(name)
                info.create_system = 3
                mode = (
                    stat.S_IFREG | 0o755
                    if name in rule.executable_files
                    else stat.S_IFREG | 0o644
                )
                if mode_overrides and name in mode_overrides:
                    mode = mode_overrides[name]
                info.external_attr = mode << 16
                archive.writestr(info, payload)
            for name, payload, mode in extra or []:
                info = zipfile.ZipInfo(name)
                if mode is not None:
                    info.create_system = 3
                    info.external_attr = mode << 16
                archive.writestr(info, payload)

    def _write_dmg_fixture(
        self,
        rule,
        payloads: dict[str, bytes],
        *,
        extra: list[tuple[str, bytes, int | None]] | None = None,
        mode_overrides: dict[str, int] | None = None,
    ) -> None:
        mounted = self.dmg_fixtures / f"{rule.filename}.mounted"
        if mounted.exists() or mounted.is_symlink():
            if mounted.is_dir() and not mounted.is_symlink():
                shutil.rmtree(mounted)
            else:
                mounted.unlink()
        mounted.mkdir()
        (self.artifacts / rule.filename).write_bytes(b"DMG fixture")

        entries = [
            (name, payload, None) for name, payload in payloads.items()
        ]
        entries.extend(extra or [])
        for name, payload, mode in entries:
            relative = Path(*Path(name.rstrip("/")).parts)
            target = mounted / relative
            is_directory = (
                name.endswith("/")
                or mode is not None and stat.S_IFMT(mode) == stat.S_IFDIR
            )
            if is_directory:
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if mode is not None and stat.S_IFMT(mode) == stat.S_IFLNK:
                target.symlink_to(payload.decode())
                continue
            if mode is not None and stat.S_IFMT(mode) == stat.S_IFIFO:
                os.mkfifo(target)
                continue
            target.write_bytes(payload)
            effective_mode = mode
            if mode_overrides and name in mode_overrides:
                effective_mode = mode_overrides[name]
            if effective_mode is None:
                effective_mode = (
                    0o755 if name in rule.executable_files else 0o644
                )
            target.chmod(effective_mode & 0o777)

    def _validate_dmg_fixture(self, path, rule, source_root) -> None:
        if path.read_bytes() != b"DMG fixture":
            raise MODULE.ReleaseArtifactError(f"{path.name}: invalid DMG")
        mounted = self.dmg_fixtures / f"{rule.filename}.mounted"
        MODULE._validate_mounted_tree(path.name, mounted, rule, source_root)

    def _rewrite(
        self,
        rule,
        payloads,
        *,
        zip_extra=None,
        mode_overrides=None,
    ) -> None:
        if rule.archive_type == "zip":
            self._write_zip(
                rule,
                payloads,
                extra=zip_extra,
                mode_overrides=mode_overrides,
            )
        elif rule.archive_type == "dmg":
            self._write_dmg_fixture(
                rule,
                payloads,
                extra=zip_extra,
                mode_overrides=mode_overrides,
            )
        else:
            self.fail(f"unknown fixture archive type: {rule.archive_type}")

    def _write_valid_set(self) -> None:
        for rule in self.rules:
            self._rewrite(rule, self._payloads(rule))

    def _validate(
        self,
        *,
        tag=TAG,
        commit=COMMIT,
        source_root=None,
        real_dmg=False,
    ) -> None:
        original_validate_dmg = MODULE._validate_dmg
        if not real_dmg:
            MODULE._validate_dmg = self._validate_dmg_fixture
        try:
            MODULE.validate_release(
                self.artifacts,
                source_root or self.source_root,
                tag,
                commit,
                self.root / "SHA256SUMS",
                self.root / "RELEASE-MANIFEST.txt",
            )
        finally:
            MODULE._validate_dmg = original_validate_dmg

    def assert_rejected(self, pattern: str, **kwargs) -> None:
        with self.assertRaisesRegex(MODULE.ReleaseArtifactError, pattern):
            self._validate(**kwargs)

    def test_valid_closed_world_set_and_deterministic_evidence(self) -> None:
        self._validate()
        first_checksums = (self.root / "SHA256SUMS").read_bytes()
        first_manifest = (self.root / "RELEASE-MANIFEST.txt").read_bytes()
        self._validate()
        self.assertEqual(first_checksums, (self.root / "SHA256SUMS").read_bytes())
        self.assertEqual(first_manifest, (self.root / "RELEASE-MANIFEST.txt").read_bytes())
        self.assertIn(TAG.encode(), first_manifest)
        self.assertIn(COMMIT.encode(), first_manifest)
        self.assertIn(b"Included: Windows Tiles; macOS Tiles", first_manifest)
        self.assertIn(b"Linux (CI build only)", first_manifest)
        self.assertIn(b"Android", first_manifest)
        self.assertNotIn(b"Deferred: macOS", first_manifest)

    def test_release_scope_is_exactly_windows_and_macos_tiles(self) -> None:
        self.assertEqual(2, len(self.rules))
        self.assertEqual(
            {
                f"stone_soup-{TAG}-tiles-win32.zip",
                f"stone_soup-{TAG}-tiles-macosx.dmg",
            },
            {rule.filename for rule in self.rules},
        )
        macos = next(
            rule for rule in self.rules if rule.filename.endswith("-macosx.dmg")
        )
        self.assertIn(
            "Dungeon Crawl Stone Soup - Tiles.app/Contents/Info.plist",
            macos.required_files,
        )

    def test_tag_and_commit_identity_are_strict(self) -> None:
        for tag in (
            "0.34.1",
            "0.34.1-zh5",
            "0.34.1-zh5-0-001",
            "0.34.1-zh5-1-000",
            "0.34.1-zh5-1-1000",
            "v0.34.1-zh5-1-001",
            "0.35.0-zh5-1-001",
        ):
            with self.subTest(tag=tag):
                self.assert_rejected("release tag", tag=tag)
        for commit in ("a" * 39, "A" * 40, "not-a-sha"):
            with self.subTest(commit=commit):
                self.assert_rejected("commit", commit=commit)

    def test_artifact_set_rejects_missing_unknown_and_directory(self) -> None:
        missing = self.artifacts / self.rules[0].filename
        missing.unlink()
        self.assert_rejected("artifact set mismatch")
        self._write_valid_set()
        (self.artifacts / "unexpected.zip").write_bytes(b"x")
        self.assert_rejected("artifact set mismatch")
        (self.artifacts / "unexpected.zip").unlink()
        (self.artifacts / "nested").mkdir()
        self.assert_rejected("unexpected directories")

    def test_artifact_set_rejects_symbolic_links(self) -> None:
        artifact = self.artifacts / self.rules[0].filename
        target = self.root / "outside.zip"
        artifact.replace(target)
        artifact.symlink_to(target)
        self.assert_rejected("symbolic links in artifact set")

    def test_artifact_set_rejects_special_files_and_missing_directory(self) -> None:
        fifo = self.artifacts / "fifo"
        os.mkfifo(fifo)
        self.assert_rejected("special entries in artifact set")
        fifo.unlink()
        missing = self.root / "missing-artifacts"
        original = self.artifacts
        self.artifacts = missing
        try:
            self.assert_rejected("artifact directory does not exist")
        finally:
            self.artifacts = original

    def test_source_root_rejects_missing_and_symbolic_link_directory(self) -> None:
        missing = self.root / "missing-source"
        self.assert_rejected("source root does not exist", source_root=missing)
        linked = self.root / "linked-source"
        linked.symlink_to(self.source_root, target_is_directory=True)
        self.assert_rejected("source root does not exist", source_root=linked)

    def test_every_required_file_has_missing_and_empty_mutations(self) -> None:
        for rule in self.rules:
            original = self._payloads(rule)
            for required in rule.required_files:
                with self.subTest(archive=rule.filename, required=required, mutation="missing"):
                    payloads = dict(original)
                    del payloads[required]
                    self._rewrite(rule, payloads)
                    self.assert_rejected("missing required file")
                    self._rewrite(rule, original)
                with self.subTest(archive=rule.filename, required=required, mutation="empty"):
                    payloads = dict(original)
                    payloads[required] = b""
                    self._rewrite(rule, payloads)
                    self.assert_rejected("required file is empty")
                    self._rewrite(rule, original)

    def test_every_content_source_has_identity_mutation(self) -> None:
        for rule in self.rules:
            original = self._payloads(rule)
            for contract in rule.content_sources:
                with self.subTest(archive=rule.filename, member=contract.member):
                    payloads = dict(original)
                    payloads[contract.member] = b"different but non-empty\n"
                    self._rewrite(rule, payloads)
                    self.assert_rejected("archived content differs")
                    self._rewrite(rule, original)

    def test_new_or_missing_zh_tree_members_fail_closed(self) -> None:
        new_source = (
            self.source_root
            / "crawl-ref/source/dat/database/zh/new-runtime-entry.txt"
        )
        new_source.write_bytes(b"new runtime entry\n")
        self.assert_rejected("missing required file")
        new_source.unlink()

        existing = (
            self.source_root / "crawl-ref/source/dat/descript/zh/monsters.txt"
        )
        original = existing.read_bytes()
        existing.unlink()
        self.assert_rejected("required ZH data tree is empty")
        existing.write_bytes(original)

    def test_zh_tree_rejects_symbolic_links(self) -> None:
        target = self.root / "zh-tree-target"
        target.write_bytes(b"target\n")
        linked = (
            self.source_root
            / "crawl-ref/source/dat/database/zh/symbolic-link.txt"
        )
        linked.symlink_to(target)
        self.assert_rejected("symbolic link in required ZH data tree")

    def test_archives_reject_unknown_zh_files_and_directories(self) -> None:
        for rule in self.rules:
            payloads = self._payloads(rule)
            unknown = f"{rule.data_root}/database/zh/unexpected.txt"
            self._rewrite(
                rule,
                payloads,
                zip_extra=[
                    (unknown, b"unexpected\n", stat.S_IFREG | 0o644)
                ],
            )
            with self.subTest(archive=rule.filename, kind="file"):
                self.assert_rejected("unexpected ZH archive file")
            self._rewrite(rule, payloads)

        zip_rule = self.rules[0]
        unknown_directory = f"{zip_rule.data_root}/database/zh/unexpected/"
        self._write_zip(
            zip_rule,
            self._payloads(zip_rule),
            extra=[(unknown_directory, b"", stat.S_IFDIR | 0o755)],
        )
        self.assert_rejected("unexpected ZH archive directory")

    def test_source_inputs_fail_closed_when_missing_empty_or_symlinked(self) -> None:
        contract = next(
            item for item in self.rules[0].content_sources
            if item.source == "LICENSE"
        )
        source = self.source_root / contract.source
        original = source.read_bytes()
        source.unlink()
        self.assert_rejected("required source file is missing or unsafe")
        source.write_bytes(b"")
        self.assert_rejected("required source file is empty")
        source.unlink()
        target = self.root / "source-target"
        target.write_bytes(original)
        source.symlink_to(target)
        self.assert_rejected("required source file is missing or unsafe")
        source.unlink()
        source.write_bytes(original)

    def test_zip_paths_duplicates_case_collisions_links_and_root_are_rejected(self) -> None:
        rule = self.rules[0]
        payloads = self._payloads(rule)
        mutations = (
            ("unsafe archive member", [("../escape", b"x", None)]),
            ("unsafe archive member", [("/absolute", b"x", None)]),
            (
                "unsafe archive member",
                [(f"{rule.root}/./crawl.exe", b"x", None)],
            ),
            ("invalid archive member", [("bad\\path", b"x", None)]),
            ("invalid archive member", [(f"{rule.root}//double", b"x", None)]),
            ("outside expected root", [("other-root/file", b"x", None)]),
            (
                "symbolic links",
                [(f"{rule.root}/link", b"target", stat.S_IFLNK | 0o777)],
            ),
            (
                "special members",
                [(f"{rule.root}/fifo", b"", stat.S_IFIFO | 0o644)],
            ),
        )
        for pattern, extra in mutations:
            with self.subTest(pattern=pattern):
                self._write_zip(rule, payloads, extra=extra)
                self.assert_rejected(pattern)
        duplicate = rule.required_files[0]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            self._write_zip(rule, payloads, extra=[(duplicate, b"again", None)])
        self.assert_rejected("duplicate archive member")
        collision = duplicate.swapcase()
        self._write_zip(rule, payloads, extra=[(collision, b"again", None)])
        self.assert_rejected("case-insensitive member collision")

    def test_dmg_mount_rejects_unsafe_members_and_outside_root(self) -> None:
        rule = next(item for item in self.rules if item.archive_type == "dmg")
        payloads = self._payloads(rule)
        mutations = (
            (
                "symbolic links",
                [(f"{rule.root}/link", b"target", stat.S_IFLNK | 0o777)],
            ),
            (
                "special mounted member",
                [(f"{rule.root}/fifo", b"", stat.S_IFIFO | 0o644)],
            ),
            (
                "outside expected root",
                [("other-root/file", b"x", stat.S_IFREG | 0o644)],
            ),
        )
        for pattern, extra in mutations:
            with self.subTest(pattern=pattern):
                self._rewrite(rule, payloads, zip_extra=extra)
                self.assert_rejected(pattern)
        self._rewrite(rule, payloads)

    def test_real_dmg_runner_validates_and_detaches(self) -> None:
        rule = next(item for item in self.rules if item.archive_type == "dmg")
        self._write_valid_set()
        mounted_fixture = self.dmg_fixtures / f"{rule.filename}.mounted"
        calls = []

        def fake_run(args, **kwargs):
            calls.append(args)
            if args[0] == "codesign":
                if args[1] == "--verify":
                    return subprocess.CompletedProcess(args, 0, "", "")
                return subprocess.CompletedProcess(
                    args, 0, "", "Signature=adhoc"
                )
            if args[1] == "attach":
                mount_root = Path(args[args.index("-mountpoint") + 1])
                shutil.copytree(mounted_fixture, mount_root, dirs_exist_ok=True)
                return subprocess.CompletedProcess(args, 0, "", "")
            mount_root = Path(args[-1])
            for child in mount_root.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch.object(MODULE.subprocess, "run", side_effect=fake_run):
            self._validate(real_dmg=True)

        self.assertEqual(4, len(calls))
        self.assertEqual(
            ["hdiutil", "attach", "-nobrowse", "-readonly"], calls[0][:4]
        )
        self.assertEqual(
            ["codesign", "--verify", "--deep", "--strict", "--verbose=4"],
            calls[1][:5],
        )
        mount_root = Path(calls[0][calls[0].index("-mountpoint") + 1])
        self.assertEqual(
            rule.root,
            Path(calls[1][-1]).relative_to(mount_root).as_posix(),
        )
        self.assertEqual(["codesign", "--display", "--verbose=2"], calls[2][:3])
        self.assertEqual(["hdiutil", "detach", "-force"], calls[3][:3])

    def test_real_dmg_runner_rejects_non_ad_hoc_signature(self) -> None:
        rule = next(item for item in self.rules if item.archive_type == "dmg")
        self._write_valid_set()
        mounted_fixture = self.dmg_fixtures / f"{rule.filename}.mounted"
        calls = []

        def signed_run(args, **kwargs):
            calls.append(args)
            if args[0] == "codesign":
                if args[1] == "--verify":
                    return subprocess.CompletedProcess(args, 0, "", "")
                return subprocess.CompletedProcess(
                    args, 0, "", "Signature=Apple Development: test"
                )
            if args[1] == "attach":
                mount_root = Path(args[args.index("-mountpoint") + 1])
                shutil.copytree(mounted_fixture, mount_root, dirs_exist_ok=True)
                return subprocess.CompletedProcess(args, 0, "", "")
            mount_root = Path(args[-1])
            for child in mount_root.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch.object(MODULE.subprocess, "run", side_effect=signed_run):
            self.assert_rejected(
                "does not have an ad-hoc code signature", real_dmg=True
            )

        self.assertEqual("codesign", calls[2][0])
        self.assertEqual("detach", calls[3][1])

    def test_real_dmg_runner_rejects_unknown_codesign_failure(self) -> None:
        rule = next(item for item in self.rules if item.archive_type == "dmg")
        self._write_valid_set()
        mounted_fixture = self.dmg_fixtures / f"{rule.filename}.mounted"
        calls = []

        def invalid_signature_run(args, **kwargs):
            calls.append(args)
            if args[0] == "codesign":
                return subprocess.CompletedProcess(
                    args, 1, "", "code has no resources but signature is invalid"
                )
            if args[1] == "attach":
                mount_root = Path(args[args.index("-mountpoint") + 1])
                shutil.copytree(mounted_fixture, mount_root, dirs_exist_ok=True)
                return subprocess.CompletedProcess(args, 0, "", "")
            mount_root = Path(args[-1])
            for child in mount_root.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch.object(
            MODULE.subprocess, "run", side_effect=invalid_signature_run
        ):
            self.assert_rejected(
                "ad-hoc macOS application signature is invalid",
                real_dmg=True,
            )

        self.assertEqual("codesign", calls[1][0])
        self.assertEqual("detach", calls[2][1])

    def test_real_dmg_runner_rejects_attach_and_cleanup_failures(self) -> None:
        rule = next(item for item in self.rules if item.archive_type == "dmg")
        self._write_valid_set()
        calls = []

        def attach_failure(args, **kwargs):
            calls.append(args)
            return subprocess.CompletedProcess(args, 1, "", "bad image")

        with mock.patch.object(
            MODULE.subprocess, "run", side_effect=attach_failure
        ):
            self.assert_rejected("invalid DMG", real_dmg=True)
        self.assertEqual(2, len(calls))
        self.assertEqual("detach", calls[1][1])

        calls.clear()

        def detach_failure(args, **kwargs):
            calls.append(args)
            if args[0] == "codesign":
                return subprocess.CompletedProcess(
                    args, 1, "", "code object is not signed at all"
                )
            if args[1] == "attach":
                mount_root = Path(args[args.index("-mountpoint") + 1])
                mounted_fixture = self.dmg_fixtures / f"{rule.filename}.mounted"
                shutil.copytree(
                    mounted_fixture, mount_root, dirs_exist_ok=True
                )
                return subprocess.CompletedProcess(args, 0, "", "")
            return subprocess.CompletedProcess(args, 1, "", "busy")

        with mock.patch.object(
            MODULE.subprocess, "run", side_effect=detach_failure
        ):
            self.assert_rejected("hdiutil detach failed", real_dmg=True)
        self.assertEqual(3, len(calls))
        self.assertEqual("detach", calls[2][1])

    def test_corrupt_archives_are_rejected(self) -> None:
        zip_rule = self.rules[0]
        zip_path = self.artifacts / zip_rule.filename
        with zipfile.ZipFile(zip_path) as archive:
            info = archive.getinfo(zip_rule.required_files[0])
        raw = bytearray(zip_path.read_bytes())
        name_length, extra_length = struct.unpack_from(
            "<HH", raw, info.header_offset + 26
        )
        data_offset = info.header_offset + 30 + name_length + extra_length
        raw[data_offset] ^= 0x01
        zip_path.write_bytes(raw)
        self.assert_rejected("corrupt ZIP member")
        self._rewrite(zip_rule, self._payloads(zip_rule))

        for rule in self.rules:
            with self.subTest(rule=rule.filename):
                (self.artifacts / rule.filename).write_bytes(b"not an archive")
                self.assert_rejected(
                    "invalid ZIP" if rule.archive_type == "zip" else "invalid DMG"
                )
                self._rewrite(rule, self._payloads(rule))

    def test_downstream_version_is_reported_as_final(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "gen_ver.pl"
            shutil.copy2(ROOT / "crawl-ref/source/util/gen_ver.pl", copied)
            output = Path(directory) / "version.h"
            for tag in (TAG, "0.34.1-zh4"):
                with self.subTest(tag=tag):
                    (Path(directory) / "release_ver").write_text(
                        f"{tag}\n", encoding="utf-8"
                    )
                    subprocess.run(
                        ["perl", str(copied), str(output)],
                        cwd=directory,
                        check=True,
                        env={**os.environ, "PATH": os.environ["PATH"]},
                    )
                    generated = output.read_text(encoding="utf-8")
                    self.assertIn(
                        '#define CRAWL_VERSION_RELEASE VER_FINAL', generated
                    )
                    self.assertIn(
                        f'#define CRAWL_VERSION_SHORT "{tag}"', generated
                    )


if __name__ == "__main__":
    unittest.main()
