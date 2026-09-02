#!/usr/bin/env python3
"""Tests for immutable, single-read review-ledger inputs."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "i18n_shared", SCRIPT_DIR / "i18n_shared.py"
)
SHARED = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules[SPEC.name] = SHARED
SPEC.loader.exec_module(SHARED)
sys.path.insert(0, str(SCRIPT_DIR))
import audit_character_mechanics_inventory as CHARACTER  # noqa: E402
import audit_god_inventory as GOD  # noqa: E402
import audit_item_name_inventory as ITEM  # noqa: E402
import audit_species_background_inventory as SPECIES  # noqa: E402
import audit_world_inventory as WORLD  # noqa: E402
import monster_name_ssot as MONSTER  # noqa: E402


class AuditInputBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name) / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.email",
             "test@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.name", "Test"],
            check=True,
        )
        self.ledger = self.repo / "docs/review.md"
        self.ledger.parent.mkdir(parents=True)
        self.ledger.write_text("GOOD\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.repo), "add", "docs/review.md"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-qm", "good"],
            check=True,
        )
        self.good = self._head()

    def tearDown(self):
        self.temp.cleanup()

    def _head(self):
        return subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD"],
            text=True,
        ).strip()

    def _commit_all(self, message):
        subprocess.run(
            ["git", "-C", str(self.repo), "add", "-A"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-qm", message],
            check=True,
        )
        return self._head()

    def _load_then_replace(self, text):
        self.ledger.write_text(text, encoding="utf-8")
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ZH_VERIFY_AUDIT_COMMIT", None)
            loaded = SHARED.load_review_input(
                self.repo, "docs/review.md"
            )
        self.ledger.unlink()
        self.ledger.write_text("BAD REPLACEMENT\n", encoding="utf-8")
        return loaded

    def test_reads_non_head_target_commit_from_candidate_checkout(self):
        self.ledger.write_text("NEW HEAD\n", encoding="utf-8")
        candidate = self._commit_all("candidate")
        self.assertNotEqual(self.good, candidate)
        self.assertEqual(
            b"GOOD\n",
            SHARED.read_regular_git_blob(
                self.repo, self.good, "docs/review.md"
            ),
        )
        snapshot = SHARED.AuditSnapshot(
            self.repo, self.good, require_head=False
        )
        self.assertEqual("GOOD\n", snapshot.text("docs/review.md"))
        self.assertEqual(self.good, snapshot.metadata()["audit_commit"])

    def test_git_blob_ignores_repository_replace_refs(self):
        self.ledger.write_text("BAD REPLACEMENT\n", encoding="utf-8")
        replacement = self._commit_all("replacement")
        subprocess.run(
            [
                "git", "-C", str(self.repo), "replace",
                self.good, replacement,
            ],
            check=True,
        )
        raw = subprocess.check_output(
            [
                "git", "-C", str(self.repo), "show",
                f"{self.good}:docs/review.md",
            ]
        )
        self.assertEqual(b"BAD REPLACEMENT\n", raw)
        self.assertEqual(
            b"GOOD\n",
            SHARED.read_regular_git_blob(
                self.repo, self.good, "docs/review.md"
            ),
        )
        self.assertEqual(
            "GOOD\n",
            SHARED.AuditSnapshot(
                self.repo, self.good, require_head=False
            ).text("docs/review.md"),
        )

    def test_git_blob_accepts_executable_regular_file(self):
        self.ledger.chmod(0o755)
        executable_commit = self._commit_all("executable ledger")
        mode, data = SHARED.read_regular_git_blob(
            self.repo,
            executable_commit,
            "docs/review.md",
            with_mode=True,
        )
        self.assertEqual("100755", mode)
        self.assertEqual(b"GOOD\n", data)

    def test_bound_input_ignores_bad_delete_symlink_and_restore_worktree_states(self):
        with mock.patch.dict(
            os.environ,
            {"ZH_VERIFY_AUDIT_COMMIT": self.good},
            clear=False,
        ):
            self.ledger.write_text("BAD\n", encoding="utf-8")
            self.assertEqual(
                "GOOD\n",
                SHARED.load_review_input(
                    self.repo, "docs/review.md"
                ).text,
            )
            self.ledger.unlink()
            self.assertEqual(
                "GOOD\n",
                SHARED.load_review_input(
                    self.repo, "docs/review.md"
                ).text,
            )
            self.ledger.symlink_to(self.repo / "outside.md")
            self.assertEqual(
                "GOOD\n",
                SHARED.load_review_input(
                    self.repo, "docs/review.md"
                ).text,
            )
            self.ledger.unlink()
            self.ledger.write_text("GOOD\n", encoding="utf-8")
            self.assertEqual(
                "GOOD\n",
                SHARED.load_review_input(
                    self.repo, "docs/review.md"
                ).text,
            )

    def test_bound_oid_must_equal_checkout_head(self):
        self.ledger.write_text("SECOND\n", encoding="utf-8")
        second = self._commit_all("second")
        self.assertNotEqual(self.good, second)
        with mock.patch.dict(
            os.environ,
            {"ZH_VERIFY_AUDIT_COMMIT": self.good},
            clear=False,
        ):
            with self.assertRaisesRegex(
                SHARED.AuditInputError, "does not equal audit root HEAD"
            ):
                SHARED.load_review_input(self.repo, "docs/review.md")

    def test_git_blob_rejects_invalid_missing_tree_symlink_and_non_utf8(self):
        symlink_path = self.repo / "docs/link.md"
        symlink_path.symlink_to("review.md")
        binary_path = self.repo / "docs/binary.md"
        binary_path.write_bytes(b"\xff\n")
        commit = self._commit_all("unsafe objects")

        with self.assertRaisesRegex(
            SHARED.AuditInputError, "full lowercase object ID"
        ):
            SHARED.read_regular_git_blob(
                self.repo, commit[:12], "docs/review.md"
            )
        for invalid in ("HEAD", commit.upper()):
            with self.subTest(invalid_oid=invalid):
                with self.assertRaisesRegex(
                    SHARED.AuditInputError, "full lowercase object ID"
                ):
                    SHARED.read_regular_git_blob(
                        self.repo, invalid, "docs/review.md"
                    )
        tree_oid = subprocess.check_output(
            ["git", "-C", str(self.repo), "rev-parse", "HEAD^{tree}"],
            text=True,
        ).strip()
        blob_oid = subprocess.check_output(
            [
                "git", "-C", str(self.repo), "rev-parse",
                "HEAD:docs/review.md",
            ],
            text=True,
        ).strip()
        for invalid in ("0" * 40, "0" * 64, tree_oid, blob_oid):
            with self.subTest(non_commit_oid=invalid):
                with self.assertRaises(SHARED.AuditInputError):
                    SHARED.read_regular_git_blob(
                        self.repo, invalid, "docs/review.md"
                    )
        with self.assertRaisesRegex(
            SHARED.AuditInputError, "missing or ambiguous"
        ):
            SHARED.read_regular_git_blob(
                self.repo, commit, "docs/missing.md"
            )
        for path in ("docs", "docs/link.md"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(
                    SHARED.AuditInputError, "not a regular file"
                ):
                    SHARED.read_regular_git_blob(self.repo, commit, path)
        with mock.patch.dict(
            os.environ,
            {"ZH_VERIFY_AUDIT_COMMIT": commit},
            clear=False,
        ):
            with self.assertRaisesRegex(
                SHARED.AuditInputError, "not strict UTF-8"
            ):
                SHARED.load_review_input(self.repo, "docs/binary.md")

    def test_git_blob_rejects_gitlink_mode(self):
        subprocess.run(
            [
                "git", "-C", str(self.repo), "update-index",
                "--add", "--cacheinfo", f"160000,{self.good},docs/gitlink",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-qm", "gitlink"],
            check=True,
        )
        commit = self._head()
        with self.assertRaisesRegex(
            SHARED.AuditInputError, "not a regular file"
        ):
            SHARED.read_regular_git_blob(
                self.repo, commit, "docs/gitlink"
            )

    def test_unbound_mode_rejects_symlink_and_reads_same_descriptor_once(self):
        with mock.patch.dict(
            os.environ, {"ZH_VERIFY_AUDIT_COMMIT": ""}, clear=False
        ):
            os.environ.pop("ZH_VERIFY_AUDIT_COMMIT", None)
            loaded = SHARED.load_review_input(self.repo, "docs/review.md")
            self.assertEqual("GOOD\n", loaded.text)
            self.assertEqual("docs/review.md", loaded.logical_path)
            self.assertEqual("docs/review.md", loaded.relative_path)

            self.ledger.unlink()
            self.ledger.symlink_to(self.repo / "outside.md")
            with self.assertRaisesRegex(
                SHARED.AuditInputError, "not a regular file"
            ):
                SHARED.load_review_input(self.repo, "docs/review.md")

    def test_unbound_mode_rejects_symlink_in_parent_chain(self):
        real_docs = self.repo / "docs-real"
        (self.repo / "docs").rename(real_docs)
        (self.repo / "docs").symlink_to(real_docs, target_is_directory=True)
        try:
            with mock.patch.dict(os.environ, {}, clear=False):
                os.environ.pop("ZH_VERIFY_AUDIT_COMMIT", None)
                with self.assertRaisesRegex(
                    SHARED.AuditInputError,
                    "parent is not a real directory",
                ):
                    SHARED.load_review_input(self.repo, "docs/review.md")
        finally:
            (self.repo / "docs").unlink()
            real_docs.rename(self.repo / "docs")

    def test_unbound_mode_rejects_missing_fifo_and_lstat_open_swap(self):
        missing = self.repo / "docs/missing.md"
        fifo = self.repo / "docs/review.fifo"
        os.mkfifo(fifo)
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("ZH_VERIFY_AUDIT_COMMIT", None)
            with self.assertRaisesRegex(
                SHARED.AuditInputError, "cannot be inspected"
            ):
                SHARED.load_review_input(self.repo, "docs/missing.md")
            with self.assertRaisesRegex(
                SHARED.AuditInputError, "not a regular file"
            ):
                SHARED.load_review_input(self.repo, "docs/review.fifo")

            replacement = self.repo / "docs/replacement.md"
            replacement.write_text("REPLACEMENT\n", encoding="utf-8")
            inspected = self.repo / "docs/inspected.md"
            real_open = SHARED.os.open

            def swap_before_open(path, flags):
                self.ledger.replace(inspected)
                replacement.replace(self.ledger)
                return real_open(path, flags)

            with mock.patch.object(
                SHARED.os, "open", side_effect=swap_before_open
            ):
                with self.assertRaisesRegex(
                    SHARED.AuditInputError,
                    "changed between inspection and open",
                ):
                    SHARED.load_review_input(self.repo, "docs/review.md")

    def test_bound_metadata_freezes_validated_commit(self):
        with mock.patch.dict(
            os.environ,
            {"ZH_VERIFY_AUDIT_COMMIT": self.good},
            clear=False,
        ):
            loaded = SHARED.load_review_input(
                self.repo, "docs/review.md"
            )
            os.environ["ZH_VERIFY_AUDIT_COMMIT"] = "0" * 40
            metadata = SHARED.review_input_metadata(loaded)
        self.assertEqual(self.good, loaded.audit_commit)
        self.assertEqual(self.good, metadata["audit_commit"])

    def test_snapshot_bound_discovery_and_content_ignore_worktree_changes(self):
        inputs = self.repo / "inputs"
        inputs.mkdir()
        first = inputs / "first.txt"
        second = inputs / "second.txt"
        first.write_text("FIRST\n", encoding="utf-8")
        second.write_text("SECOND\n", encoding="utf-8")
        commit = self._commit_all("snapshot inputs")

        snapshot = SHARED.AuditSnapshot(self.repo, commit)
        discovered = snapshot.glob("inputs", "*.txt")
        self.assertEqual(
            ["first.txt", "second.txt"],
            [path.name for path in discovered],
        )

        first.write_text("MUTATED\n", encoding="utf-8")
        second.unlink()
        second.symlink_to(self.repo / "outside.txt")
        (inputs / "later.txt").write_text("LATER\n", encoding="utf-8")

        self.assertEqual(discovered, snapshot.glob("inputs", "*.txt"))
        self.assertEqual("FIRST\n", snapshot.text("inputs/first.txt"))
        self.assertEqual("SECOND\n", snapshot.text("inputs/second.txt"))
        self.assertNotIn(
            "inputs/later.txt",
            {
                item["path"]
                for item in snapshot.input_manifest()["inputs"]
            },
        )

    def test_bound_snapshot_rejects_transient_worktree_substitution_during_blob_read(self):
        requested = threading.Event()
        substituted = threading.Event()
        blob_read = threading.Event()
        restored = threading.Event()
        attacker_errors: list[BaseException] = []
        original_path = self.repo / "docs/review.original"
        replacement_path = self.repo / "docs/review.replacement"
        replacement_path.write_text("TRANSIENT ATTACK\n", encoding="utf-8")

        def attacker():
            try:
                if not requested.wait(5):
                    raise RuntimeError("bound read was not reached")
                self.ledger.replace(original_path)
                replacement_path.replace(self.ledger)
                substituted.set()
                if not blob_read.wait(5):
                    raise RuntimeError("bound Git blob read did not finish")
                self.ledger.replace(replacement_path)
                original_path.replace(self.ledger)
                restored.set()
            except BaseException as error:  # surfaced in the main test thread
                attacker_errors.append(error)
                substituted.set()
                restored.set()

        real_git = SHARED._run_git_bytes

        def gated_git(repo, *args):
            if args[:2] != ("cat-file", "blob"):
                return real_git(repo, *args)
            requested.set()
            if not substituted.wait(5):
                raise RuntimeError("transient substitution did not occur")
            try:
                return real_git(repo, *args)
            finally:
                blob_read.set()
                if not restored.wait(5):
                    raise RuntimeError("transient substitution was not restored")

        thread = threading.Thread(target=attacker, daemon=True)
        thread.start()
        snapshot = SHARED.AuditSnapshot(self.repo, self.good)
        with mock.patch.object(
            SHARED, "_run_git_bytes", side_effect=gated_git
        ):
            self.assertEqual("GOOD\n", snapshot.text("docs/review.md"))
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual([], attacker_errors)
        self.assertEqual("GOOD\n", self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(
            "TRANSIENT ATTACK\n",
            replacement_path.read_text(encoding="utf-8"),
        )

    def test_unbound_snapshot_rejects_concurrent_inode_swap_even_after_restore(self):
        requested = threading.Event()
        substituted = threading.Event()
        opened = threading.Event()
        restored = threading.Event()
        attacker_errors: list[BaseException] = []
        original_path = self.repo / "docs/review.original"
        replacement_path = self.repo / "docs/review.replacement"
        replacement_path.write_text("TRANSIENT ATTACK\n", encoding="utf-8")
        real_open = SHARED.os.open

        def attacker():
            try:
                if not requested.wait(5):
                    raise RuntimeError("unbound open was not reached")
                self.ledger.replace(original_path)
                replacement_path.replace(self.ledger)
                substituted.set()
                if not opened.wait(5):
                    raise RuntimeError("replacement inode was not opened")
                self.ledger.replace(replacement_path)
                original_path.replace(self.ledger)
                restored.set()
            except BaseException as error:  # surfaced in the main test thread
                attacker_errors.append(error)
                substituted.set()
                restored.set()

        def gated_open(path, flags):
            requested.set()
            if not substituted.wait(5):
                raise RuntimeError("transient substitution did not occur")
            fd = real_open(path, flags)
            opened.set()
            if not restored.wait(5):
                os.close(fd)
                raise RuntimeError("transient substitution was not restored")
            return fd

        thread = threading.Thread(target=attacker, daemon=True)
        thread.start()
        with (
            mock.patch.dict(os.environ, {}, clear=False),
            mock.patch.object(SHARED.os, "open", side_effect=gated_open),
            self.assertRaisesRegex(
                SHARED.AuditInputError,
                "changed between inspection and open",
            ),
        ):
            os.environ.pop("ZH_VERIFY_AUDIT_COMMIT", None)
            SHARED.AuditSnapshot(self.repo, None).read("docs/review.md")
        thread.join(timeout=5)
        self.assertFalse(thread.is_alive())
        self.assertEqual([], attacker_errors)
        self.assertEqual("GOOD\n", self.ledger.read_text(encoding="utf-8"))
        self.assertEqual(
            "TRANSIENT ATTACK\n",
            replacement_path.read_text(encoding="utf-8"),
        )

    def test_snapshot_reads_each_unique_git_blob_once(self):
        inputs = self.repo / "inputs"
        inputs.mkdir()
        (inputs / "one.txt").write_text("SAME\n", encoding="utf-8")
        (inputs / "two.txt").write_text("SAME\n", encoding="utf-8")
        commit = self._commit_all("duplicate blobs")
        snapshot = SHARED.AuditSnapshot(self.repo, commit)

        calls = []
        original = SHARED._run_git_bytes

        def recording_git(repo, *args):
            if args[:2] == ("cat-file", "blob"):
                calls.append(args[2])
            return original(repo, *args)

        with mock.patch.object(
            SHARED, "_run_git_bytes", side_effect=recording_git
        ):
            snapshot.glob("inputs", "*.txt")
            snapshot.text("inputs/one.txt")
            snapshot.text("inputs/two.txt")
        self.assertEqual(1, len(calls))

    def test_load_review_input_reuses_the_active_invocation_snapshot(self):
        calls = []
        original = SHARED._run_git_bytes

        def recording_git(repo, *args):
            if args[:2] == ("cat-file", "blob"):
                calls.append(args[2])
            return original(repo, *args)

        with (
            mock.patch.dict(
                os.environ,
                {"ZH_VERIFY_AUDIT_COMMIT": self.good},
                clear=False,
            ),
            mock.patch.object(
                SHARED, "_run_git_bytes", side_effect=recording_git
            ),
            SHARED.audit_snapshot_scope(self.repo) as snapshot,
        ):
            first = SHARED.load_review_input(
                self.repo, "docs/review.md"
            )
            second = SHARED.load_review_input(
                self.repo, "docs/review.md"
            )
            self.assertIs(first, second)
            self.assertIs(first, snapshot.read("docs/review.md"))
        self.assertEqual(1, len(calls))

    def test_bound_discovery_rejects_nonmatching_symlink_and_gitlink(self):
        inputs = self.repo / "inputs"
        inputs.mkdir()
        (inputs / "good.txt").write_text("GOOD\n", encoding="utf-8")
        nonmatching_link = inputs / "ignored.bin"
        nonmatching_link.symlink_to("good.txt")
        symlink_commit = self._commit_all("symlink in discovery")
        with self.assertRaisesRegex(
            SHARED.AuditInputError, "non-regular entry"
        ):
            SHARED.AuditSnapshot(
                self.repo, symlink_commit
            ).glob("inputs", "*.txt")

        nonmatching_link.unlink()
        self._commit_all("remove symlink")
        subprocess.run(
            [
                "git", "-C", str(self.repo), "update-index",
                "--add", "--cacheinfo",
                f"160000,{self.good},inputs/ignored.gitlink",
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-qm", "gitlink input"],
            check=True,
        )
        gitlink_commit = self._head()
        with self.assertRaisesRegex(
            SHARED.AuditInputError, "non-regular entry"
        ):
            SHARED.AuditSnapshot(
                self.repo, gitlink_commit
            ).glob("inputs", "*.txt", recursive=True)

    def test_bound_recursive_discovery_rejects_symlinked_directory(self):
        inputs = self.repo / "inputs"
        inputs.mkdir()
        (inputs / "good.txt").write_text("GOOD\n", encoding="utf-8")
        (inputs / "linked-directory").symlink_to(
            self.repo / "docs", target_is_directory=True
        )
        commit = self._commit_all("symlinked discovery directory")
        with self.assertRaisesRegex(
            SHARED.AuditInputError, "non-regular entry"
        ):
            SHARED.AuditSnapshot(self.repo, commit).glob(
                "inputs", "*.txt", recursive=True
            )

    def test_bound_and_unbound_manifests_are_path_normalized_and_comparable(self):
        inputs = self.repo / "inputs"
        nested = inputs / "nested"
        nested.mkdir(parents=True)
        (inputs / "a.txt").write_text("A\n", encoding="utf-8")
        (nested / "b.txt").write_text("B\n", encoding="utf-8")
        commit = self._commit_all("manifest inputs")

        bound = SHARED.AuditSnapshot(self.repo, commit)
        unbound = SHARED.AuditSnapshot(self.repo, None)
        for snapshot in (bound, unbound):
            snapshot.glob("inputs", "*.txt", recursive=True)

        self.assertEqual(bound.input_manifest(), unbound.input_manifest())
        self.assertEqual(
            bound.input_manifest_sha256(),
            unbound.input_manifest_sha256(),
        )
        encoded = SHARED.json.dumps(
            bound.input_manifest(), ensure_ascii=False, sort_keys=True
        )
        self.assertNotIn(str(self.repo), encoded)
        self.assertEqual(
            sorted(
                item["path"]
                for item in bound.input_manifest()["inputs"]
            ),
            [
                item["path"]
                for item in bound.input_manifest()["inputs"]
            ],
        )

    def test_external_inputs_are_cached_but_excluded_from_manifest(self):
        external = Path(self.temp.name) / "external.txt"
        external.write_text("BEFORE\n", encoding="utf-8")
        snapshot = SHARED.AuditSnapshot(self.repo, None)
        loaded = snapshot.read(external, allow_external_unbound=True)
        external.write_text("AFTER\n", encoding="utf-8")

        self.assertIs(
            loaded,
            snapshot.read(external, allow_external_unbound=True),
        )
        self.assertEqual("BEFORE\n", snapshot.text(
            external, allow_external_unbound=True
        ))
        self.assertEqual([], snapshot.input_manifest()["inputs"])

    def test_external_file_and_directory_symlinks_fail_closed(self):
        external_root = Path(self.temp.name) / "external"
        external_root.mkdir()
        target = external_root / "target.txt"
        target.write_text("TARGET\n", encoding="utf-8")
        file_link = external_root / "file-link.txt"
        file_link.symlink_to(target)
        real_directory = external_root / "real-directory"
        real_directory.mkdir()
        (real_directory / "input.txt").write_text(
            "INPUT\n", encoding="utf-8"
        )
        directory_link = external_root / "directory-link"
        directory_link.symlink_to(real_directory, target_is_directory=True)
        snapshot = SHARED.AuditSnapshot(self.repo, None)

        with self.assertRaisesRegex(
            SHARED.AuditInputError, "not a regular file"
        ):
            snapshot.read(file_link, allow_external_unbound=True)
        with self.assertRaisesRegex(
            SHARED.AuditInputError, "directory is not real"
        ):
            snapshot.glob(
                directory_link,
                "*.txt",
                allow_external_unbound=True,
            )
        with self.assertRaisesRegex(
            SHARED.AuditInputError, "parent is not a real directory"
        ):
            snapshot.read(
                directory_link / "input.txt",
                allow_external_unbound=True,
            )

    def test_all_six_consumers_use_loaded_bytes_after_backing_path_replacement(self):
        def assert_frozen_result(result, loaded):
            self.assertEqual(loaded.audit_commit, result["audit_commit"])
            self.assertEqual(loaded.logical_path, result["logical_path"])
            self.assertEqual(loaded.sha256, result["input_sha256"])
            self.assertEqual(
                loaded.sha256, result["review_results_sha256"]
            )

        character_row = {
            "category": "fixture",
            "identity": "fixture:CHARACTER",
            "lifecycle": "current",
        }
        character_payload = {
            "count": 1,
            "glossary_sha256": "b" * 64,
            "inventory_sha256": "c" * 64,
            "rows": [character_row],
        }
        character_text = CHARACTER.render_review_results(
            character_payload,
            {
                character_row["identity"]: {
                    "terminal_conclusion": "keep",
                    "reviewer_rationale": "fixture evidence remains exact",
                },
            },
        )
        character_input = self._load_then_replace(character_text)
        character_result = CHARACTER.review_coverage(
            character_payload, character_input
        )
        self.assertTrue(character_result["coverage_equal"])
        assert_frozen_result(character_result, character_input)

        god_row = {
            "identity": "GOD_FIXTURE",
            "lifecycle": "current",
            "name": "fixture",
        }
        god_payload = {
            "count": 1,
            "glossary_sha256": "d" * 64,
            "inventory_sha256": "e" * 64,
            "parents": [god_row],
        }
        god_text = GOD.render_review_results(
            god_payload,
            {
                god_row["identity"]: {
                    "terminal_conclusion": "keep",
                    "reviewer_rationale": "fixture evidence remains exact",
                },
            },
        )
        god_input = self._load_then_replace(god_text)
        god_result = GOD.review_coverage(god_payload, god_input)
        self.assertTrue(god_result["coverage_equal"])
        assert_frozen_result(god_result, god_input)

        species_row = {
            "category": "species",
            "identity": "species:SP_FIXTURE",
            "lifecycle": "current",
        }
        species_payload = {
            "count": 1,
            "glossary_sha256": "f" * 64,
            "inventory_sha256": "1" * 64,
            "rows": [species_row],
        }
        species_text = SPECIES.render_review_results(
            species_payload,
            {
                species_row["identity"]: {
                    "terminal_conclusion": "keep",
                    "reviewer_rationale": "fixture evidence remains exact",
                },
            },
        )
        species_input = self._load_then_replace(species_text)
        species_result = SPECIES.review_coverage(
            species_payload, species_input
        )
        self.assertTrue(species_result["coverage_equal"])
        assert_frozen_result(species_result, species_input)

        item_source_row = {
            "identity": "item-description:fixture",
            "category": "item-description",
            "lifecycle": "current",
            "english_source": "fixture",
            "_pre_review_chinese": "样例",
            "current_chinese": "样例",
            "producer": "fixture producer",
            "consumer": "fixture consumer",
            "input": "fixture.cc",
            "_metadata": {
                "category": "item-description",
                "description_key": "fixture",
            },
            "_conclusion": "keep",
        }
        item_v2_decision = {
            "identity": item_source_row["identity"],
            "lifecycle": "current",
            "english_source": "fixture",
            "pre_review_chinese": "样例",
            "current_chinese": "样例",
            "adopted_english": "fixture",
            "adopted_chinese": "样例",
            "producer": "fixture producer",
            "consumer": "fixture consumer",
            "metadata": item_source_row["_metadata"],
            "input": "fixture.cc",
            "source_files": [],
            "terminal_conclusion": "keep",
            "semantic_reason": "direct production evidence",
            "reentry_trigger": "not applicable",
        }
        with tempfile.TemporaryDirectory(
            dir=ITEM.ROOT / ".claude"
        ) as item_source_directory:
            item_source_path = Path(item_source_directory)
            (item_source_path / "source.txt").write_text(
                "", encoding="utf-8"
            )
            item_rows = ITEM.v3_decision_cards(
                [item_source_row],
                [item_v2_decision],
                source_directory=item_source_path,
                snapshot=SHARED.AuditSnapshot(ITEM.ROOT, None),
            )
        item_payload = {
            "baseline": "2" * 40,
            "count": 1,
            "decision_inventory_sha256": ITEM.v3_decision_digest(item_rows),
            "glossary_sha256": "3" * 64,
            "rows": item_rows,
        }
        item_text = ITEM.render_review_results_v3(item_payload, item_rows)
        item_input = self._load_then_replace(item_text)
        parsed_item_rows = ITEM.parse_review_results_v3(item_input)
        item_header = ITEM.parse_review_header_v3(item_input)
        item_violations = ITEM.review_violations_v3(
            item_payload["rows"],
            parsed_item_rows,
            item_payload,
            item_header,
            item_input,
        )
        self.assertFalse(any(item_violations.values()), item_violations)
        item_metadata = SHARED.review_input_metadata(item_input)
        self.assertEqual(item_input.audit_commit, item_metadata["audit_commit"])
        self.assertEqual(item_input.logical_path, item_metadata["logical_path"])
        self.assertEqual(item_input.sha256, item_metadata["input_sha256"])

        baseline = "5" * 40
        monster_text = f"- 基线：`{baseline}`\n"
        monster_input = self._load_then_replace(monster_text)
        with (
            mock.patch.object(MONSTER, "_resolve_commit", return_value=baseline),
            mock.patch.object(
                MONSTER,
                "render_review_results",
                return_value=monster_text,
            ),
        ):
            monster_result = MONSTER.review_coverage(
                {"rows": []}, monster_input, baseline
            )
        self.assertTrue(monster_result["coverage_equal"])
        assert_frozen_result(monster_result, monster_input)

        digest = "6" * 64
        world_payload = {
            "rows": [],
            "inventory_sha256": digest,
        }
        world_text = WORLD.render_review_results(
            world_payload,
            {},
            allow_test_fixture_subset=True,
        )
        world_input = self._load_then_replace(world_text)
        world_result = WORLD.review_coverage(
            world_payload,
            world_input,
            allow_test_fixture_subset=True,
        )
        self.assertTrue(world_result["coverage_equal"])
        assert_frozen_result(world_result, world_input)


if __name__ == "__main__":
    unittest.main()
