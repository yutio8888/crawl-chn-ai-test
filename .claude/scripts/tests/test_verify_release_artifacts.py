#!/usr/bin/env python3
"""Negative-mutation coverage for the desktop release artifact gate."""

from __future__ import annotations

import importlib.util
import io
import os
import shutil
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/verify_release_artifacts.py"
SPEC = importlib.util.spec_from_file_location("verify_release_artifacts", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

TAG = "0.34.1-zh1"
COMMIT = "a" * 40


class ReleaseArtifactTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        self.source_root = self.root / "source"
        self.source_root.mkdir()
        self.rules = MODULE.artifact_rules(TAG)
        for rule in self.rules:
            for contract in rule.content_sources:
                source = self.source_root / contract.source
                source.parent.mkdir(parents=True, exist_ok=True)
                if not source.exists():
                    source.write_bytes(f"source:{contract.source}\n".encode())
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

    def _write_tar(
        self,
        rule,
        payloads: dict[str, bytes],
        *,
        extra: list[tarfile.TarInfo] | None = None,
        mode_overrides: dict[str, int] | None = None,
    ) -> None:
        with tarfile.open(self.artifacts / rule.filename, "w:gz") as archive:
            for name, payload in payloads.items():
                info = tarfile.TarInfo(name)
                info.size = len(payload)
                info.mode = 0o755 if name in rule.executable_files else 0o644
                if mode_overrides and name in mode_overrides:
                    info.mode = mode_overrides[name]
                archive.addfile(info, io.BytesIO(payload))
            for info in extra or []:
                archive.addfile(info)

    def _rewrite(
        self,
        rule,
        payloads,
        *,
        zip_extra=None,
        tar_extra=None,
        mode_overrides=None,
    ) -> None:
        if rule.archive_type == "zip":
            self._write_zip(
                rule,
                payloads,
                extra=zip_extra,
                mode_overrides=mode_overrides,
            )
        else:
            self._write_tar(
                rule,
                payloads,
                extra=tar_extra,
                mode_overrides=mode_overrides,
            )

    def _write_valid_set(self) -> None:
        for rule in self.rules:
            self._rewrite(rule, self._payloads(rule))

    def _validate(self, *, tag=TAG, commit=COMMIT, source_root=None) -> None:
        MODULE.validate_release(
            self.artifacts,
            source_root or self.source_root,
            tag,
            commit,
            self.root / "SHA256SUMS",
            self.root / "RELEASE-MANIFEST.txt",
        )

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
        self.assertIn(b"Deferred: Android", first_manifest)

    def test_tag_and_commit_identity_are_strict(self) -> None:
        for tag in ("0.34.1", "0.34.1-zh0", "v0.34.1-zh1", "0.35.0-zh1"):
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

    def test_source_inputs_fail_closed_when_missing_empty_or_symlinked(self) -> None:
        contract = self.rules[0].content_sources[0]
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

    def test_every_unix_executable_requires_an_executable_bit(self) -> None:
        for rule in self.rules:
            for executable in rule.executable_files:
                with self.subTest(archive=rule.filename, executable=executable):
                    self._rewrite(
                        rule,
                        self._payloads(rule),
                        mode_overrides={executable: 0o644},
                    )
                    self.assert_rejected("executable bit is missing")
                    self._rewrite(rule, self._payloads(rule))

    def test_zip_paths_duplicates_case_collisions_links_and_root_are_rejected(self) -> None:
        rule = self.rules[0]
        payloads = self._payloads(rule)
        mutations = (
            ("unsafe archive member", [("../escape", b"x", None)]),
            ("unsafe archive member", [("/absolute", b"x", None)]),
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

    def test_tar_paths_links_duplicates_case_collisions_and_root_are_rejected(self) -> None:
        rule = self.rules[2]
        payloads = self._payloads(rule)
        for name, pattern in (
            ("../escape", "unsafe archive member"),
            ("/absolute", "unsafe archive member"),
            ("bad\\path", "invalid archive member"),
            (f"{rule.root}//double", "invalid archive member"),
            ("other-root/file", "outside expected root"),
        ):
            with self.subTest(name=name):
                info = tarfile.TarInfo(name)
                self._write_tar(rule, payloads, extra=[info])
                self.assert_rejected(pattern)
        link = tarfile.TarInfo(f"{rule.root}/link")
        link.type = tarfile.SYMTYPE
        link.linkname = "crawl"
        self._write_tar(rule, payloads, extra=[link])
        self.assert_rejected("links and special members")
        duplicate = tarfile.TarInfo(rule.required_files[0])
        self._write_tar(rule, payloads, extra=[duplicate])
        self.assert_rejected("duplicate archive member")
        collision = tarfile.TarInfo(rule.required_files[0].swapcase())
        self._write_tar(rule, payloads, extra=[collision])
        self.assert_rejected("case-insensitive member collision")

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
                self.assert_rejected("invalid (ZIP|tar.gz archive)")
                self._rewrite(rule, self._payloads(rule))

    def test_downstream_version_is_reported_as_final(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / "gen_ver.pl"
            shutil.copy2(ROOT / "crawl-ref/source/util/gen_ver.pl", copied)
            (Path(directory) / "release_ver").write_text(f"{TAG}\n", encoding="utf-8")
            output = Path(directory) / "version.h"
            subprocess.run(
                ["perl", str(copied), str(output)],
                cwd=directory,
                check=True,
                env={**os.environ, "PATH": os.environ["PATH"]},
            )
            generated = output.read_text(encoding="utf-8")
            self.assertIn('#define CRAWL_VERSION_RELEASE VER_FINAL', generated)
            self.assertIn(f'#define CRAWL_VERSION_SHORT "{TAG}"', generated)


if __name__ == "__main__":
    unittest.main()
