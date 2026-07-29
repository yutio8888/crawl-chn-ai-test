#!/usr/bin/env python3
"""Focused fail-closed tests for the one-edge rootfix bootstrap gate."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import os
import py_compile
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "review_rootfix_gate.py"
SPEC = importlib.util.spec_from_file_location("review_rootfix_gate", SCRIPT)
GATE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(GATE)


class RootfixGateTests(unittest.TestCase):
    def test_repository_imports_use_private_empty_pycache_namespace(
        self,
    ) -> None:
        prefix = GATE.PRIVATE_PYCACHE_PREFIX
        self.assertTrue(sys.dont_write_bytecode)
        self.assertEqual(os.fspath(prefix), sys.pycache_prefix)
        self.assertFalse(prefix.exists())
        self.assertNotEqual(SCRIPT.parents[2], prefix.parent)

        i18n_shared = sys.modules.get("i18n_shared")
        self.assertIsNotNone(i18n_shared)
        for module in (GATE.rb, i18n_shared):
            with self.subTest(module=module.__name__):
                cached = Path(module.__cached__)
                self.assertEqual(
                    os.fspath(prefix),
                    os.path.commonpath(
                        (os.fspath(prefix), os.fspath(cached))
                    ),
                )
                self.assertNotEqual(
                    SCRIPT.parent / "__pycache__",
                    cached.parent,
                )

    def test_ignored_checkout_pyc_cannot_supply_review_bundle(self) -> None:
        probe = "\n".join(
            (
                "import importlib.util",
                "import json",
                "import sys",
                "from pathlib import Path",
                "path = Path(sys.argv[1])",
                "spec = importlib.util.spec_from_file_location('gate', path)",
                "gate = importlib.util.module_from_spec(spec)",
                "spec.loader.exec_module(gate)",
                "print(json.dumps({",
                "    'malicious': getattr(gate.rb, 'MALICIOUS', False),",
                "    'cached': gate.rb.__cached__,",
                "    'prefix': str(gate.PRIVATE_PYCACHE_PREFIX),",
                "    'prefix_exists': gate.PRIVATE_PYCACHE_PREFIX.exists(),",
                "}))",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / ".claude" / "scripts"
            scripts.mkdir(parents=True)
            for name in (
                SCRIPT.name,
                "review_bundle.py",
                "i18n_shared.py",
                "verify_zh.sh",
            ):
                shutil.copy2(SCRIPT.parent / name, scripts / name)
            contract = scripts / "data" / (
                "review_verification_contract_v5.json"
            )
            contract.parent.mkdir()
            shutil.copy2(
                SCRIPT.parents[2] / GATE.PROFILE_CONTRACT_PATH,
                contract,
            )

            poison = scripts / "poison.py"
            poison.write_text("MALICIOUS = True\n")
            active_prefix = sys.pycache_prefix
            try:
                sys.pycache_prefix = None
                cached = Path(
                    importlib.util.cache_from_source(
                        os.fspath(scripts / "review_bundle.py")
                    )
                )
            finally:
                sys.pycache_prefix = active_prefix
            cached.parent.mkdir(parents=True)
            py_compile.compile(
                os.fspath(poison),
                cfile=os.fspath(cached),
                doraise=True,
                invalidation_mode=(
                    py_compile.PycInvalidationMode.UNCHECKED_HASH
                ),
            )
            poison.unlink()

            environment = dict(os.environ)
            environment.pop("PYTHONPYCACHEPREFIX", None)
            environment["PYTHONDONTWRITEBYTECODE"] = "1"
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    probe,
                    os.fspath(scripts / SCRIPT.name),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["malicious"])
            self.assertFalse(payload["prefix_exists"])
            self.assertEqual(
                payload["prefix"],
                os.path.commonpath(
                    (payload["prefix"], payload["cached"])
                ),
            )

    def test_policy_manifest_is_sorted_unique_and_complete(self) -> None:
        self.assertEqual(
            tuple(sorted(set(GATE.POLICY_MANIFEST))),
            GATE.POLICY_MANIFEST,
        )
        self.assertEqual(16, len(GATE.POLICY_MANIFEST))
        self.assertIn(
            ".claude/scripts/review_rootfix_gate.py",
            GATE.POLICY_MANIFEST,
        )
        self.assertIn(
            ".claude/scripts/tests/test_review_rootfix_gate.py",
            GATE.POLICY_MANIFEST,
        )
        rendered = "".join(f"{path}\n" for path in GATE.POLICY_MANIFEST)
        self.assertEqual(
            hashlib.sha256(rendered.encode()).hexdigest(),
            GATE.POLICY_MANIFEST_SHA256,
        )

    def test_single_parent_rejects_merge_and_wrong_identity(self) -> None:
        with mock.patch.object(
            GATE, "_git_text", return_value="a" * 40 + " " + "b" * 40
        ):
            self.assertEqual(
                "b" * 40,
                GATE._single_parent(Path("."), "a" * 40, "P"),
            )
        for value in (
            "a" * 40,
            "a" * 40 + " " + "b" * 40 + " " + "c" * 40,
            "c" * 40 + " " + "b" * 40,
        ):
            with self.subTest(value=value), mock.patch.object(
                GATE, "_git_text", return_value=value
            ):
                with self.assertRaises(GATE.RootfixError):
                    GATE._single_parent(Path("."), "a" * 40, "P")

    def test_trusted_gate_must_execute_from_target_p_blobs(self) -> None:
        target = SCRIPT.parents[2]
        gate_bytes = SCRIPT.read_bytes()
        bundle_bytes = (SCRIPT.parent / "review_bundle.py").read_bytes()
        shared_bytes = (SCRIPT.parent / "i18n_shared.py").read_bytes()
        contract_bytes = (
            target / GATE.PROFILE_CONTRACT_PATH
        ).read_bytes()
        verifier_bytes = (target / GATE.VERIFIER_PATH).read_bytes()
        with mock.patch.object(
            GATE, "_TRUSTED_POLICY_HEAD", "a" * 40
        ), mock.patch.object(
            GATE.rb,
            "read_regular_git_blob",
            side_effect=[
                ("100644", gate_bytes),
                ("100644", bundle_bytes),
                ("100644", shared_bytes),
                ("100644", contract_bytes),
                ("100755", verifier_bytes),
            ],
        ):
            GATE._validate_trusted_gate(Path("."), target, "a" * 40)
        with mock.patch.object(
            GATE, "_TRUSTED_POLICY_HEAD", "a" * 40
        ):
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_trusted_gate(
                    Path("."),
                    target / "not-the-target",
                    "a" * 40,
                )

    def test_candidate_must_share_target_common_dir_and_worktree_inventory(
        self,
    ) -> None:
        head = "b" * 40
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target"
            candidate = root / "candidate"
            common = root / "common"
            other_common = root / "other-common"
            for path in (target, candidate, common, other_common):
                path.mkdir()

            with mock.patch.object(
                GATE.rb,
                "git_common_dir",
                side_effect=[common, other_common],
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError, "share one Git common directory"
                ):
                    GATE._validate_linked_worktree(target, candidate, head)

            with mock.patch.object(
                GATE.rb,
                "git_common_dir",
                side_effect=[common, common],
            ), mock.patch.object(
                GATE,
                "_worktree_records",
                return_value=[
                    {"worktree": str(target), "HEAD": "a" * 40}
                ],
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError, "not uniquely listed"
                ):
                    GATE._validate_linked_worktree(target, candidate, head)

            with mock.patch.object(
                GATE.rb,
                "git_common_dir",
                side_effect=[common, common],
            ), mock.patch.object(
                GATE,
                "_worktree_records",
                return_value=[
                    {"worktree": str(candidate), "HEAD": head}
                ],
            ):
                GATE._validate_linked_worktree(target, candidate, head)

    def test_worktree_parser_rejects_incomplete_and_duplicate_fields(self) -> None:
        valid = (
            b"worktree /repo/target\0HEAD " + b"a" * 40
            + b"\0branch refs/heads/target\0\0"
        )
        with mock.patch.object(GATE, "_git", return_value=valid):
            records = GATE._worktree_records(Path("."))
            self.assertEqual("/repo/target", records[0]["worktree"])
        for raw in (
            b"worktree /repo/target\0\0",
            b"worktree /one\0worktree /two\0HEAD " + b"a" * 40 + b"\0\0",
            b"\xff\0HEAD " + b"a" * 40 + b"\0\0",
        ):
            with self.subTest(raw=raw), mock.patch.object(
                GATE, "_git", return_value=raw
            ):
                with self.assertRaises(GATE.RootfixError):
                    GATE._worktree_records(Path("."))

    def test_changed_paths_reject_noncanonical_order(self) -> None:
        with mock.patch.object(
            GATE, "_git", return_value=b"a\0b\0"
        ):
            self.assertEqual(
                ("a", "b"), GATE._changed_paths(Path("."), "a", "b")
            )
        for value in (b"b\0a\0", b"a\0a\0", b"\xff\0"):
            with self.subTest(value=value), mock.patch.object(
                GATE, "_git", return_value=value
            ):
                with self.assertRaises(GATE.RootfixError):
                    GATE._changed_paths(Path("."), "a", "b")

    def test_policy_modes_preserve_existing_and_fix_new_files(self) -> None:
        def valid_entry(repo, commit, path):
            if commit == GATE.BASE_C and path in GATE.NEW_POLICY_PATHS:
                return None
            return ("100644", "blob", "a" * 40)

        with mock.patch.object(GATE, "_tree_entry", side_effect=valid_entry):
            GATE._validate_policy_modes(Path("."), "b" * 40)

        def changed_mode(repo, commit, path):
            if commit == GATE.BASE_C and path in GATE.NEW_POLICY_PATHS:
                return None
            if commit != GATE.BASE_C and path == GATE.POLICY_MANIFEST[0]:
                return ("100755", "blob", "b" * 40)
            return ("100644", "blob", "a" * 40)

        with mock.patch.object(GATE, "_tree_entry", side_effect=changed_mode):
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_policy_modes(Path("."), "b" * 40)

        def preexisting_new(repo, commit, path):
            return ("100644", "blob", "a" * 40)

        with mock.patch.object(GATE, "_tree_entry", side_effect=preexisting_new):
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_policy_modes(Path("."), "b" * 40)

    def test_candidate_test_accepts_only_exact_one_line_replacement(self) -> None:
        policy = b"before\n" + GATE.OLD_FIXTURE_PARENT + b"\nafter\n"
        candidate = b"before\n" + GATE.NEW_FIXTURE_PARENT + b"\nafter\n"
        with mock.patch.object(
            GATE.rb,
            "read_regular_git_blob",
            side_effect=[("100644", policy), ("100644", candidate)],
        ):
            record, blob = GATE._candidate_test_record(
                Path("."), "a" * 40, "b" * 40
            )
        self.assertEqual(GATE.TEST_PATH, record["path"])
        self.assertEqual(1, record["replacement_count"])
        self.assertEqual(
            hashlib.sha256(candidate).hexdigest(),
            record["candidate_blob_sha256"],
        )
        self.assertEqual(candidate, blob)

    def test_candidate_test_rejects_extra_edit_mode_and_ambiguous_source(self) -> None:
        valid_policy = b"x\n" + GATE.OLD_FIXTURE_PARENT + b"\n"
        valid_candidate = b"x\n" + GATE.NEW_FIXTURE_PARENT + b"\n"
        cases = (
            (("100644", valid_policy), ("100755", valid_candidate)),
            (("100644", valid_policy), ("100644", valid_candidate + b"extra")),
            (
                ("100644", valid_policy + GATE.OLD_FIXTURE_PARENT),
                ("100644", valid_candidate),
            ),
            (
                ("100644", valid_policy + GATE.NEW_FIXTURE_PARENT),
                ("100644", valid_candidate),
            ),
        )
        for policy, candidate in cases:
            with self.subTest(policy=policy, candidate=candidate), mock.patch.object(
                GATE.rb,
                "read_regular_git_blob",
                side_effect=[policy, candidate],
            ):
                with self.assertRaises(GATE.RootfixError):
                    GATE._candidate_test_record(
                        Path("."), "a" * 40, "b" * 40
                    )

    def status(self) -> dict:
        return {
            "target_head": "a" * 40,
            "candidate_head": "b" * 40,
            "bundle_id": "c" * 64,
            "bundle_sha256": "d" * 64,
            "diff_sha256": "e" * 64,
            "glossary_sha256": "f" * 64,
            "routing_sha256": "0" * 64,
            "routing_files": [GATE.TEST_PATH],
            "required_reviewers": [GATE.REVIEWER],
            "ready_reviewers": [GATE.REVIEWER],
            "ready": True,
            "readiness_sha256": {GATE.REVIEWER: "1" * 64},
            "finding_counts": {
                GATE.REVIEWER: {
                    "blocker": 0,
                    "needs_fix": 0,
                    "suggestion": 0,
                }
            },
            "attempts": [],
            "passing_attempt": None,
            "approved": False,
            "approval": None,
            "legacy_read_only": False,
            "state": "FINAL_GATE_REQUIRED",
            "_rootfix_profile_diff_hash": "9" * 40,
            "_rootfix_candidate_blob_sha256": hashlib.sha256(
                b"pass\n"
            ).hexdigest(),
        }

    def candidate_test_record(self) -> dict:
        return {
            "path": GATE.TEST_PATH,
            "mode": "100644",
            "policy_blob_sha256": "2" * 64,
            "candidate_blob_sha256": hashlib.sha256(
                b"pass\n"
            ).hexdigest(),
            "replacement_count": 1,
        }

    def recovery_archive(
        self,
        parent: Path,
        status: dict,
    ) -> Path:
        archive = (
            parent
            / GATE.RECOVERY_ARCHIVE_PART
            / status["bundle_id"]
        )
        archive.mkdir(parents=True)
        return archive

    def write_retired_marker(
        self,
        archive: Path,
        status: dict,
        attempt_id: str,
        *,
        attempt_sha256: str | None = None,
        updates: dict | None = None,
    ) -> Path:
        marker = GATE._running_marker_payload(
            status,
            attempt_id,
            f".staging-{attempt_id}",
        )
        if updates:
            marker.update(updates)
        data = GATE.rb.canonical_json_bytes(marker)
        digest = hashlib.sha256(data).hexdigest()
        path = archive / (
            f"retired-running-{attempt_id}-"
            f"{attempt_sha256 or 'none'}-{digest}-"
            "123-0123456789abcdef.json"
        )
        path.write_bytes(data)
        return path

    def write_process_record(
        self,
        path: Path,
        status: dict,
        attempt_id: str,
        phase: str,
        command: list[str],
    ) -> None:
        record = {
            "schema": GATE.PROCESS_SCHEMA,
            "exception_id": GATE.EXCEPTION_ID,
            "bundle_id": status["bundle_id"],
            "attempt_id": attempt_id,
            "phase": phase,
            "pid": 99999999,
            "pgid": 99999999,
            "proc_start": "dead",
            "boot_id": "test-boot",
            "command_sha256": hashlib.sha256(
                GATE.rb.canonical_json_bytes(command)
            ).hexdigest(),
            "started_ns": "1700000000000000000",
        }
        (path / GATE.PROCESS_RECORD_NAMES[phase]).write_bytes(
            GATE.rb.canonical_json_bytes(record)
        )

    def write_profile_metadata(
        self,
        run: Path,
        status: dict,
        *,
        worktree: Path | None = None,
        profile_status: str = "pass",
        wrapper_run: Path | None = None,
    ) -> dict:
        run.mkdir(parents=True, exist_ok=True)
        phase_ids = (
            "policy-sync",
            "source-db-static",
            "code-static",
            "message-overlay-static",
        )
        phase_results = [
            {
                "id": phase,
                "required": True,
                "status": (
                    "fail"
                    if profile_status != "pass" and index == 0
                    else "pass"
                ),
                "exit_code": (
                    1
                    if profile_status != "pass" and index == 0
                    else 0
                ),
            }
            for index, phase in enumerate(phase_ids)
        ]
        failures = 0 if profile_status == "pass" else 1
        verify_parts = [
            "=== verify_zh.sh --profile code @ "
            "2026-07-29T00:00:00+08:00 ===\n",
            f"Run ID: {run.name}\n",
            "Scope: full\n",
            "Risk: cpp_i18n=0 cjk_runtime=0 zh_test_runtime=0 "
            "message_overlay=0 explicit_full=0\n",
            f"Base: {status['target_head']}\n",
            f"Head: {status['candidate_head']}\n",
            f"Diff hash: {status['_rootfix_profile_diff_hash']}\n",
            f"Diff SHA-256: {status['diff_sha256']}\n",
            f"Glossary SHA-256: {status['glossary_sha256']}\n\n",
        ]
        for phase, (_, label) in zip(
            phase_results, GATE.PROFILE_PHASE_LABELS
        ):
            verify_parts.append(f"=== {label} ===\n")
            verify_parts.append(
                "RESULT: PASS\n\n"
                if phase["status"] == "pass"
                else f"RESULT: FAIL (exit {phase['exit_code']})\n\n"
            )
        verify_parts.extend(
            (
                f"Summary: {failures} blocking failure(s)\n",
                "=== verify_zh.sh complete ===\n",
            )
        )
        verify = "".join(verify_parts).encode("utf-8")
        inventory = b"{}\n"
        (run / "verify.log").write_bytes(verify)
        (run / "item-name-inventory.json").write_bytes(inventory)
        (run / "phases.tsv").write_text(
            "".join(
                f"{phase['id']}\t1\t{phase['status']}\t"
                f"{phase['exit_code']}\n"
                for phase in phase_results
            )
        )
        metadata = {
            "schema_version": 3,
            "verification_contract": GATE.rb.VERIFICATION_CONTRACT,
            "run_id": run.name,
            "status": profile_status,
            "profile": "code",
            "scope": "full",
            "base": status["target_head"],
            "head": status["candidate_head"],
            "diff_hash": "9" * 40,
            "diff_sha256": status["diff_sha256"],
            "glossary_sha256": status["glossary_sha256"],
            "routing_sha256": None,
            "control_plane_sha256": None,
            "risk_cpp_i18n": False,
            "risk_cjk_runtime": False,
            "risk_zh_test_runtime": False,
            "risk_message_overlay": False,
            "runtime_mode": "none",
            "phases": phase_results,
            "artifacts": [
                {
                    "path": "verify.log",
                    "size": len(verify),
                    "sha256": hashlib.sha256(verify).hexdigest(),
                },
                {
                    "path": "item-name-inventory.json",
                    "size": len(inventory),
                    "sha256": hashlib.sha256(inventory).hexdigest(),
                },
            ],
            "worktree": str(
                (worktree or Path("/private/tmp/rootfix-candidate")).resolve()
            ),
            "started_at": "2026-07-29T00:00:00+08:00",
            "completed_at": "2026-07-29T00:01:00+08:00",
            "failures": failures,
        }
        (run / "metadata.json").write_text(
            json.dumps(
                metadata,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        wrapper_run = wrapper_run or run
        (run.parent / f"verify-code-{run.name}.log").write_text(
            f"run_id={run.name}\n"
            "profile=code\n"
            f"status={profile_status}\n"
            f"failures={failures}\n"
            "started_at=2026-07-29T00:00:00+08:00\n"
            "completed_at=2026-07-29T00:01:00+08:00\n"
            f"report={wrapper_run / 'verify.log'}\n"
            f"metadata={wrapper_run / 'metadata.json'}\n"
            f"Summary: {failures} blocking failure(s)\n"
            "=== verify_zh.sh complete ===\n"
        )
        return metadata

    def profile_process_log(
        self,
        run: Path,
        metadata: dict,
        *,
        wrapper_run: Path | None = None,
    ) -> bytes:
        wrapper_run = wrapper_run or run
        wrapper = (
            wrapper_run.parent
            / f"verify-code-{metadata['run_id']}.log"
        )
        return (
            "\n"
            "=== verify-zh --profile code ===\n"
            f"Run ID: {metadata['run_id']}\n"
            f"Report: {wrapper_run / 'verify.log'}\n"
            f"Metadata: {wrapper_run / 'metadata.json'}\n"
            f"Wrapper: {wrapper}\n"
            f"Failures: {metadata['failures']}\n"
            "\n"
        ).encode("utf-8")

    def write_attempt(
        self,
        path: Path,
        status: dict,
        *,
        outcome: str,
        exit_code: int,
        interrupted_signal=None,
        worktree: Path | None = None,
    ) -> str:
        path.mkdir()
        commands = {}
        metadata_path = None
        if outcome == "pass":
            commands = GATE._expected_commands(status)
            (path / "candidate-test.log").write_text("PASS\n")
            (path / "candidate-test.py").write_text("pass\n")
            run = path / "profile-output" / "run"
            wrapper_run = (
                path.parent
                / f".staging-{path.name}"
                / "profile-output"
                / "run"
            )
            metadata = self.write_profile_metadata(
                run,
                status,
                worktree=worktree,
                wrapper_run=wrapper_run,
            )
            (path / "code-profile.log").write_bytes(
                self.profile_process_log(
                    run,
                    metadata,
                    wrapper_run=wrapper_run,
                )
            )
            metadata_path = "run/metadata.json"
        else:
            commands = {
                "candidate_test": GATE._expected_commands(status)[
                    "candidate_test"
                ]
            }
            (path / "candidate-test.py").write_text("pass\n")
            (path / "candidate-test.log").write_text("FAIL\n")
        for phase, command in commands.items():
            self.write_process_record(
                path, status, path.name, phase, command
            )
        GATE._write_attempt_artifacts(path, commands, metadata_path)
        (path / "completion.json").write_bytes(
            GATE.rb.canonical_json_bytes(
                GATE._completion(
                    outcome,
                    exit_code,
                    interrupted_signal,
                )
            )
        )
        return GATE._attempt_digest(path)

    def complete_mock_attempt_run(
        self,
        stage,
        candidate_top: Path,
        status: dict,
        _candidate_test_blob: bytes,
        commands: dict[str, list[str]],
        artifact_seals: dict[str, GATE.FileSnapshot],
    ):
        stage_path = (
            stage.path
            if isinstance(stage, GATE.DirectoryHandle)
            else Path(stage)
        )
        attempt_id = stage_path.name.removeprefix(".staging-")
        commands.update(GATE._expected_commands(status))
        for phase, command in commands.items():
            self.write_process_record(
                stage_path,
                status,
                attempt_id,
                phase,
                command,
            )
        (stage_path / "candidate-test.py").write_bytes(b"pass\n")
        (stage_path / "candidate-test.log").write_text("PASS\n")
        run = stage_path / "profile-output" / "run"
        metadata = self.write_profile_metadata(
            run,
            status,
            worktree=candidate_top,
        )
        (stage_path / "code-profile.log").write_bytes(
            self.profile_process_log(run, metadata)
        )
        for name in ("candidate-test.log", "code-profile.log"):
            artifact_seals[name] = GATE._read_regular_snapshot(
                stage_path / name, "test raw log"
            )
        return 0, "run/metadata.json", None

    def test_bundle_status_requires_exact_v5_readiness_boundary(self) -> None:
        GATE._validate_bundle_status(self.status())
        mutations = (
            ("routing_files", []),
            ("required_reviewers", []),
            ("ready_reviewers", []),
            ("ready", False),
            ("attempts", [{}]),
            ("approved", True),
            ("state", "MERGEABLE"),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                status = self.status()
                status[field] = value
                with self.assertRaises(GATE.RootfixError):
                    GATE._validate_bundle_status(status)
        for severity in ("blocker", "needs_fix"):
            with self.subTest(severity=severity):
                status = self.status()
                status["finding_counts"][GATE.REVIEWER][severity] = 1
                with self.assertRaises(GATE.RootfixError):
                    GATE._validate_bundle_status(status)

    def test_profile_metadata_is_bound_to_exact_candidate(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "profile-output"
            run = output / "run"
            metadata = self.write_profile_metadata(run, status)
            relative, loaded = GATE._profile_metadata(output, status)
            self.assertEqual("run/metadata.json", relative)
            self.assertEqual(metadata, loaded)
            for field, value in (
                ("head", "9" * 40),
                ("diff_hash", "8" * 40),
                ("status", "fail"),
                ("failures", 1),
                ("failures", False),
                ("schema_version", 2),
                ("schema_version", True),
                ("risk_cpp_i18n", 0),
                ("scope", "changed"),
                ("verification_contract", "wrong-contract"),
                ("run_id", "wrong-run"),
                ("phases", []),
                ("artifacts", []),
            ):
                with self.subTest(field=field):
                    changed = dict(metadata)
                    changed[field] = value
                    (run / "metadata.json").write_text(json.dumps(changed))
                    with self.assertRaises(GATE.RootfixError):
                        GATE._profile_metadata(output, status)
            for field, value in (
                ("required", 1),
                ("exit_code", False),
            ):
                with self.subTest(phase_field=field):
                    changed = json.loads(json.dumps(metadata))
                    changed["phases"][0][field] = value
                    (run / "metadata.json").write_text(
                        json.dumps(changed)
                    )
                    with self.assertRaises(GATE.RootfixError):
                        GATE._profile_metadata(output, status)
            for mutation in ("required-phase", "artifact-missing", "artifact-digest"):
                with self.subTest(mutation=mutation):
                    (run / "metadata.json").write_text(json.dumps(metadata))
                    inventory_path = run / "item-name-inventory.json"
                    inventory_path.write_bytes(b"{}\n")
                    if mutation == "required-phase":
                        changed = json.loads(json.dumps(metadata))
                        changed["phases"][2]["status"] = "skip"
                        (run / "metadata.json").write_text(
                            json.dumps(changed)
                        )
                    elif mutation == "artifact-missing":
                        inventory_path.unlink()
                    else:
                        inventory_path.write_bytes(b'{"drift":true}\n')
                    with self.assertRaises(GATE.RootfixError):
                        GATE._profile_metadata(output, status)

    def test_profile_report_and_wrapper_bind_exact_semantics(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "profile-output"
            run = output / "run"
            metadata = self.write_profile_metadata(run, status)
            report = run / "verify.log"
            forged = report.read_text().replace(
                f"Base: {status['target_head']}",
                f"Base: {'8' * 40}",
            ).replace(
                "Summary: 0 blocking failure(s)",
                "Summary: 999 blocking failure(s)",
            )
            report.write_text(forged)
            changed = json.loads(json.dumps(metadata))
            report_artifact = changed["artifacts"][0]
            report_bytes = report.read_bytes()
            report_artifact["size"] = len(report_bytes)
            report_artifact["sha256"] = hashlib.sha256(
                report_bytes
            ).hexdigest()
            (run / "metadata.json").write_text(
                json.dumps(
                    changed,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "report .* binding"
            ):
                GATE._profile_metadata(output, status)

            self.write_profile_metadata(run, status)
            wrapper = output / "verify-code-run.log"
            wrapper.write_text(
                wrapper.read_text().replace(
                    f"report={run / 'verify.log'}",
                    "report=/attacker/elsewhere/profile-output/"
                    "run/verify.log",
                )
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "wrapper path binding"
            ):
                GATE._profile_metadata(output, status)

    def test_profile_metadata_rejects_duplicate_keys_at_any_depth(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "profile-output"
            run = output / "run"
            self.write_profile_metadata(run, status)
            metadata_path = run / "metadata.json"
            original = metadata_path.read_text()
            mutations = (
                original.replace(
                    "{\n",
                    '{\n  "status": "fail",\n',
                    1,
                ),
                original.replace(
                    '    {\n      "path": "verify.log",',
                    '    {\n      "path": "forged",\n'
                    '      "path": "verify.log",',
                    1,
                ),
            )
            for index, mutation in enumerate(mutations):
                with self.subTest(index=index):
                    metadata_path.write_text(mutation)
                    with self.assertRaisesRegex(
                        GATE.RootfixError,
                        "unambiguous strict UTF-8 JSON",
                    ):
                        GATE._profile_metadata(output, status)
                    metadata_path.write_text(original)

    def test_profile_report_binds_legitimate_post_summary_drift(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "profile-output"
            run = output / "run"
            metadata = self.write_profile_metadata(
                run,
                status,
                profile_status="fail",
            )
            report = run / "verify.log"
            report.write_text(
                report.read_text().replace(
                    "Summary: 1 blocking failure(s)\n"
                    "=== verify_zh.sh complete ===\n",
                    "Summary: 0 blocking failure(s)\n"
                    "=== verify_zh.sh complete ===\n"
                    "ERROR: worktree HEAD changed during verification: "
                    f"{status['candidate_head']} -> {'7' * 40}\n",
                )
            )
            report_bytes = report.read_bytes()
            metadata["artifacts"][0]["size"] = len(report_bytes)
            metadata["artifacts"][0]["sha256"] = hashlib.sha256(
                report_bytes
            ).hexdigest()
            (run / "metadata.json").write_text(
                json.dumps(
                    metadata,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            GATE._profile_metadata(
                output,
                status,
                expected_status="fail",
            )

            report.write_text(
                report.read_text().replace(
                    f"{status['candidate_head']} -> {'7' * 40}",
                    f"{'6' * 40} -> {'7' * 40}",
                )
            )
            report_bytes = report.read_bytes()
            metadata["artifacts"][0]["size"] = len(report_bytes)
            metadata["artifacts"][0]["sha256"] = hashlib.sha256(
                report_bytes
            ).hexdigest()
            (run / "metadata.json").write_text(
                json.dumps(
                    metadata,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "drift footer binding"
            ):
                GATE._profile_metadata(
                    output,
                    status,
                    expected_status="fail",
                )

    def test_profile_raw_log_binds_run_paths_and_failure_count(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            attempt_id = (
                "attempt-1700000000000000954-1001-eeeeeeeeeeee"
            )
            attempt = Path(tmp) / attempt_id
            self.write_attempt(
                attempt,
                status,
                outcome="pass",
                exit_code=0,
            )
            raw = attempt / "code-profile.log"
            raw.write_text(
                "\n"
                "=== verify-zh --profile code ===\n"
                "Run ID: DIFFERENT-RUN\n"
                "Report: /different/verify.log\n"
                "Metadata: /different/metadata.json\n"
                "Wrapper: /different/wrapper.log\n"
                "Failures: 73\n"
                "\n"
            )
            (attempt / "artifacts.json").unlink()
            GATE._write_attempt_artifacts(
                attempt,
                GATE._expected_commands(status),
                "run/metadata.json",
            )
            digest = GATE._attempt_digest(attempt)
            with self.assertRaisesRegex(
                GATE.RootfixError, "raw log semantic binding"
            ):
                GATE._validate_attempt(
                    attempt,
                    digest,
                    status,
                )

    def test_security_sensitive_reads_use_no_follow_single_read_helper(
        self,
    ) -> None:
        target = SCRIPT.parents[2]
        with mock.patch.object(
            GATE, "_TRUSTED_POLICY_HEAD", "a" * 40
        ), mock.patch.object(
            GATE,
            "_read_regular_bytes",
            side_effect=GATE.RootfixError("inode changed"),
        ):
            with self.assertRaisesRegex(GATE.RootfixError, "inode changed"):
                GATE._validate_trusted_gate(Path("."), target, "a" * 40)

        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "artifact.log"
            artifact.write_text("data")
            with mock.patch.object(
                GATE,
                "_read_regular_at",
                side_effect=GATE.RootfixError("inode changed"),
            ):
                with self.assertRaisesRegex(GATE.RootfixError, "inode changed"):
                    GATE._artifact_inventory(root)

            run = root / "run"
            run.mkdir()
            (run / "metadata.json").write_text("{}")
            with mock.patch.object(
                GATE,
                "_read_regular_at",
                side_effect=GATE.RootfixError("inode changed"),
            ):
                with self.assertRaisesRegex(GATE.RootfixError, "inode changed"):
                    GATE._profile_metadata(root, status)

    def test_directory_inventories_reject_post_enumeration_objects(
        self,
    ) -> None:
        status = self.status()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "artifacts"
            root.mkdir()
            (root / "known").write_text("known")
            original_read = GATE._read_regular_at
            injected = False

            def inject_artifact(*args, **kwargs):
                nonlocal injected
                snapshot = original_read(*args, **kwargs)
                if not injected:
                    injected = True
                    (root / "unknown-after-enumeration").write_text(
                        "unknown"
                    )
                return snapshot

            with mock.patch.object(
                GATE, "_read_regular_at", side_effect=inject_artifact
            ), self.assertRaisesRegex(
                GATE.RootfixError, "contents changed during enumeration"
            ):
                GATE._artifact_snapshot(root)
            self.assertTrue(
                (root / "unknown-after-enumeration").exists()
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "evidence"
            (root / "attempts").mkdir(parents=True)
            attempt_id = (
                "attempt-1700000000000000950-997-aaaaaaaaaaaa"
            )
            marker = GATE._running_marker_payload(
                status,
                attempt_id,
                f".staging-{attempt_id}",
            )
            (root / GATE.RUNNING_NAME).write_bytes(
                GATE.rb.canonical_json_bytes(marker)
            )
            original_read = GATE._read_regular_at

            def inject_evidence(*args, **kwargs):
                snapshot = original_read(*args, **kwargs)
                (root / "unknown-after-enumeration").write_text(
                    "unknown"
                )
                return snapshot

            with mock.patch.object(
                GATE, "_read_regular_at", side_effect=inject_evidence
            ), self.assertRaisesRegex(
                GATE.RootfixError, "contents changed during enumeration"
            ):
                GATE._validate_evidence_objects(root, status)

        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000951-998-bbbbbbbbbbbb"
            )
            self.write_retired_marker(
                archive,
                status,
                attempt_id,
            )
            original_validate = GATE._validate_archived_running_marker

            def inject_archive(*args, **kwargs):
                result = original_validate(*args, **kwargs)
                (archive / "unknown-after-enumeration").write_text(
                    "unknown"
                )
                return result

            with mock.patch.object(
                GATE,
                "_validate_archived_running_marker",
                side_effect=inject_archive,
            ), self.assertRaisesRegex(
                GATE.RootfixError, "contents changed during enumeration"
            ):
                GATE._validate_recovery_archive(archive, status)

        with tempfile.TemporaryDirectory() as tmp:
            attempts = Path(tmp) / "attempts"
            attempts.mkdir()
            attempt_id = (
                "attempt-1700000000000000952-999-cccccccccccc"
            )
            attempt = attempts / attempt_id
            self.write_attempt(
                attempt,
                status,
                outcome="pass",
                exit_code=0,
            )
            original_validate = GATE._validate_attempt

            def inject_attempt(*args, **kwargs):
                result = original_validate(*args, **kwargs)
                (attempts / "unknown-after-enumeration").mkdir()
                return result

            with mock.patch.object(
                GATE, "_validate_attempt", side_effect=inject_attempt
            ), self.assertRaisesRegex(
                GATE.RootfixError, "contents changed during enumeration"
            ):
                GATE._published_attempts(attempts, status)

    def test_artifact_snapshot_rejects_post_read_in_place_rewrite(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = root / "first"
            second = root / "second"
            first.write_bytes(b"first")
            second.write_bytes(b"second")
            original_read = GATE._read_regular_at
            injected = False

            def rewrite_after_read(*args, **kwargs):
                nonlocal injected
                snapshot = original_read(*args, **kwargs)
                if not injected:
                    injected = True
                    first.write_bytes(b"FIRST")
                return snapshot

            with mock.patch.object(
                GATE, "_read_regular_at", side_effect=rewrite_after_read
            ), self.assertRaisesRegex(
                GATE.RootfixError, "artifact changed after reading"
            ):
                GATE._artifact_snapshot(root)
            self.assertEqual(b"FIRST", first.read_bytes())

    def test_post_wait_cleanup_refuses_reused_pid_without_signal(
        self,
    ) -> None:
        record = {
            "pid": 12345,
            "pgid": 12345,
            "proc_start": "original-token",
            "boot_id": "current-boot",
        }
        with mock.patch.object(
            GATE, "_process_group_exists", return_value=True
        ), mock.patch.object(
            GATE.rb, "_boot_id", return_value="current-boot"
        ), mock.patch.object(
            GATE.rb, "_proc_start_token", return_value="reused-token"
        ), mock.patch.object(os, "killpg") as killpg:
            with self.assertRaisesRegex(
                GATE.RootfixError, "PID was reused"
            ):
                GATE._terminate_surviving_process_group(record)
        killpg.assert_not_called()

    def test_post_wait_cleanup_refuses_unreadable_live_pid_identity(
        self,
    ) -> None:
        record = {
            "pid": 12345,
            "pgid": 12345,
            "proc_start": "original-token",
            "boot_id": "current-boot",
        }
        with mock.patch.object(
            GATE, "_process_group_exists", return_value=True
        ), mock.patch.object(
            GATE.rb, "_boot_id", return_value="current-boot"
        ), mock.patch.object(
            GATE.rb, "_proc_start_token", return_value=None
        ), mock.patch.object(
            os, "kill", return_value=None
        ), mock.patch.object(os, "killpg") as killpg:
            with self.assertRaisesRegex(
                GATE.RootfixError, "identity cannot be proven"
            ):
                GATE._terminate_surviving_process_group(record)
        killpg.assert_not_called()

    def test_approval_payload_binds_readiness_and_attempt(self) -> None:
        status = self.status()
        candidate_test = {
            "path": GATE.TEST_PATH,
            "mode": "100644",
            "policy_blob_sha256": "2" * 64,
            "candidate_blob_sha256": "3" * 64,
            "replacement_count": 1,
        }
        approval = GATE._approval_payload(
            status,
            candidate_test,
            [{"attempt_id": "attempt-fixed", "sha256": "4" * 64}],
            "attempt-fixed",
            "4" * 64,
        )
        self.assertEqual(GATE.APPROVAL_FIELDS, frozenset(approval))
        self.assertEqual(status["readiness_sha256"][GATE.REVIEWER],
                         approval["readiness"][0]["sha256"])
        self.assertEqual("4" * 64, approval["attempt_sha256"])
        self.assertNotIn("created_ns", approval)

    def test_successful_attempt_preserves_logs_metadata_and_exact_commands(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            attempt_id = (
                "attempt-1700000000000000000-700-0123456789ab"
            )
            stage = Path(tmp) / f".staging-{attempt_id}"
            stage.mkdir()
            candidate = Path(tmp) / "candidate"
            candidate.mkdir()
            (candidate / Path(GATE.TEST_PATH).parent).mkdir(parents=True)

            candidate_blob = b"print('committed test')\n"
            status["_rootfix_candidate_blob_sha256"] = hashlib.sha256(
                candidate_blob
            ).hexdigest()

            def fake_run(
                command,
                cwd,
                output,
                environment,
                *,
                stdin_path=None,
                stdin_bytes=None,
                stage=None,
                status=None,
                attempt_id=None,
                phase=None,
                evidence_command=None,
                output_seals=None,
                deferred_signals=None,
                after_snapshot=None,
            ):
                stage_path = (
                    stage.path
                    if isinstance(stage, GATE.DirectoryHandle)
                    else Path(stage)
                )
                self.write_process_record(
                    stage_path,
                    status,
                    attempt_id,
                    phase,
                    evidence_command,
                )
                self.assertEqual(candidate, cwd)
                if output.name == "candidate-test.log":
                    output.write_text("PASS\n", encoding="utf-8")
                    self.assertIsNone(stdin_path)
                    self.assertEqual(candidate_blob, stdin_bytes)
                    self.assertEqual(
                        candidate / GATE.TEST_PATH,
                        Path(command[-1]),
                    )
                    self.assertEqual(
                        stage_path / ".candidate-pycache",
                        Path(environment["PYTHONPYCACHEPREFIX"]),
                    )
                    self.assertFalse(
                        Path(environment["PYTHONPYCACHEPREFIX"]).exists()
                    )
                if output.name == "code-profile.log":
                    self.assertEqual(
                        stage_path / ".profile-pycache",
                        Path(environment["PYTHONPYCACHEPREFIX"]),
                    )
                    self.assertFalse(
                        Path(environment["PYTHONPYCACHEPREFIX"]).exists()
                    )
                    run = stage_path / "profile-output" / "run"
                    metadata = self.write_profile_metadata(
                        run, status, worktree=candidate
                    )
                    output.write_bytes(
                        self.profile_process_log(run, metadata)
                    )
                if output_seals is not None:
                    output_seals[output.name] = (
                        GATE._read_regular_snapshot(
                            output, "test raw log"
                        )
                    )
                if after_snapshot is not None:
                    after_snapshot(0, None)
                return 0, None

            commands = {}
            with mock.patch.object(GATE, "_run_process", side_effect=fake_run):
                rc, metadata_path, interrupted = GATE._run_attempt(
                    stage, candidate, status, candidate_blob, commands
                )
            self.assertEqual(0, rc)
            self.assertEqual("run/metadata.json", metadata_path)
            self.assertIsNone(interrupted)
            self.assertEqual(
                [],
                list((candidate / Path(GATE.TEST_PATH).parent).iterdir()),
            )
            GATE._write_attempt_artifacts(stage, commands, metadata_path)
            GATE.rb.atomic_write_once(
                stage / "completion.json",
                GATE.rb.canonical_json_bytes(GATE._completion("pass", 0)),
            )
            digest = GATE._attempt_digest(stage)
            GATE._validate_attempt(stage, digest, status)
            artifacts = json.loads((stage / "artifacts.json").read_text())
            self.assertEqual(
                [
                    "python3",
                    f"{status['candidate_head']}:{GATE.TEST_PATH}",
                ],
                artifacts["commands"]["candidate_test"],
            )
            self.assertTrue((stage / "candidate-test.py").is_file())
            candidate_log = next(
                record
                for record in artifacts["artifacts"]
                if record["path"] == "candidate-test.log"
            )
            self.assertEqual(
                hashlib.sha256(b"PASS\n").hexdigest(),
                candidate_log["sha256"],
            )
            self.assertEqual(5, candidate_log["size"])
            self.assertRegex(candidate_log["mtime_ns"], r"^[0-9]+$")
            self.assertRegex(candidate_log["ctime_ns"], r"^[0-9]+$")
            (stage / "unexpected-empty-directory").mkdir()
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_attempt(stage, digest, status)
            with self.assertRaisesRegex(
                GATE.RootfixError,
                "directory inventory is not exact|"
                "unknown rootfix attempt directory",
            ):
                GATE._validate_attempt(
                    stage,
                    GATE._attempt_digest(stage),
                    status,
                )

    def test_failed_attempt_inventory_is_digest_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            attempts = Path(tmp)
            failed_id = (
                "attempt-1700000000000000200-720-aaaaaaaaaaaa"
            )
            failed = attempts / failed_id
            failed.mkdir()
            GATE._write_attempt_artifacts(failed, {}, None)
            completion = GATE._completion("fail", 7)
            (failed / "completion.json").write_bytes(
                GATE.rb.canonical_json_bytes(completion)
            )
            records, passing = GATE._published_attempts(
                attempts, self.status()
            )
            self.assertEqual(failed_id, records[0]["attempt_id"])
            self.assertEqual(
                GATE._attempt_digest(failed), records[0]["sha256"]
            )
            self.assertIsNone(passing)
            old_digest = records[0]["sha256"]
            (failed / "unregistered-empty-directory").mkdir()
            self.assertNotEqual(old_digest, GATE._attempt_digest(failed))
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_attempt(failed, old_digest, self.status())
            with self.assertRaisesRegex(
                GATE.RootfixError,
                "profile output without a profile command",
            ):
                GATE._validate_attempt(
                    failed,
                    GATE._attempt_digest(failed),
                    self.status(),
                )
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_all_attempts(
                    attempts,
                    [{"attempt_id": failed_id, "sha256": "0" * 64}],
                    "attempt-pass",
                    "1" * 64,
                    self.status(),
                )
            unexpected = attempts / "unexpected"
            unexpected.mkdir()
            with self.assertRaises(GATE.RootfixError):
                GATE._attempt_paths(attempts)

    def test_attempt_digest_rejects_symlinks_and_binds_empty_directories(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            attempt = Path(tmp) / "attempt"
            attempt.mkdir()
            (attempt / "log").write_text("data")
            before = GATE._attempt_digest(attempt)
            (attempt / "empty").mkdir()
            self.assertNotEqual(before, GATE._attempt_digest(attempt))
            link = attempt / "link"
            try:
                link.symlink_to(attempt / "log")
            except (OSError, NotImplementedError):
                self.skipTest("symlinks are unavailable")
            with self.assertRaises(GATE.RootfixError):
                GATE._attempt_digest(attempt)

    def test_published_attempt_uses_one_file_snapshot_for_digest_and_validation(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            attempts = Path(tmp)
            failed_id = (
                "attempt-1700000000000000201-721-bbbbbbbbbbbb"
            )
            self.write_attempt(
                attempts / failed_id,
                status,
                outcome="fail",
                exit_code=7,
            )
            original = GATE._artifact_snapshot
            with mock.patch.object(
                GATE,
                "_artifact_snapshot",
                wraps=original,
            ) as snapshot:
                records, passing = GATE._published_attempts(
                    attempts, status
                )
            self.assertEqual(1, snapshot.call_count)
            self.assertEqual(failed_id, records[0]["attempt_id"])
            self.assertIsNone(passing)

    def test_keyboard_interrupt_publishes_interrupted_attempt(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000100-700-aaaaaaaaaaaa"
            )
            with mock.patch.object(
                GATE, "_attempt_id", return_value=attempt_id
            ), mock.patch.object(
                GATE,
                "_run_attempt",
                side_effect=KeyboardInterrupt,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    GATE._execute_attempt(
                        root,
                        attempts,
                        root,
                        status,
                        b"test",
                        lambda: archive,
                        lambda: None,
                    )
            self.assertFalse((root / GATE.RUNNING_NAME).exists())
            self.assertEqual(
                1,
                len(GATE._validate_recovery_archive(archive, status)),
            )
            records, passing = GATE._published_attempts(attempts, status)
            self.assertEqual(1, len(records))
            self.assertIsNone(passing)
            completion = json.loads(
                (
                    attempts
                    / attempt_id
                    / "completion.json"
                ).read_text()
            )
            self.assertEqual("interrupted", completion["outcome"])
            self.assertEqual(signal.SIGINT, completion["interrupted_signal"])
            self.assertEqual(128 + signal.SIGINT, completion["exit_code"])

    def test_interrupt_during_passing_seal_preserves_passing_terminal(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000101-701-bbbbbbbbbbbb"
            )

            def successful_run(
                stage,
                _candidate_top,
                current_status,
                _candidate_test_blob,
                commands,
                artifact_seals,
            ):
                stage_path = (
                    stage.path
                    if isinstance(stage, GATE.DirectoryHandle)
                    else Path(stage)
                )
                commands.update(GATE._expected_commands(current_status))
                for phase, command in commands.items():
                    self.write_process_record(
                        stage_path,
                        current_status,
                        attempt_id,
                        phase,
                        command,
                )
                (stage_path / "candidate-test.py").write_text("pass\n")
                (stage_path / "candidate-test.log").write_text("PASS\n")
                run = stage_path / "profile-output" / "run"
                metadata = self.write_profile_metadata(
                    run, current_status, worktree=_candidate_top
                )
                (stage_path / "code-profile.log").write_bytes(
                    self.profile_process_log(run, metadata)
                )
                for name in ("candidate-test.log", "code-profile.log"):
                    artifact_seals[name] = GATE._read_regular_snapshot(
                        stage_path / name, "test raw log"
                    )
                return 0, "run/metadata.json", None

            original_write = GATE._atomic_write_once_at
            interrupted = False

            def interrupt_first_completion(directory, name, data):
                nonlocal interrupted
                if name == "completion.json" and not interrupted:
                    interrupted = True
                    raise KeyboardInterrupt
                return original_write(directory, name, data)

            with mock.patch.object(
                GATE, "_attempt_id", return_value=attempt_id
            ), mock.patch.object(
                GATE, "_run_attempt", side_effect=successful_run
            ), mock.patch.object(
                GATE,
                "_atomic_write_once_at",
                side_effect=interrupt_first_completion,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    GATE._execute_attempt(
                        root,
                        attempts,
                        root,
                        status,
                        b"test",
                        lambda: archive,
                        lambda: None,
                    )
            self.assertTrue(interrupted)
            self.assertFalse((root / GATE.RUNNING_NAME).exists())
            self.assertEqual(
                1,
                len(GATE._validate_recovery_archive(archive, status)),
            )
            records, passing = GATE._published_attempts(attempts, status)
            self.assertEqual(1, len(records))
            self.assertIsNotNone(passing)
            self.assertEqual("pass", passing["outcome"])
            self.assertEqual(0, passing["exit_code"])

    def test_supervised_signal_result_is_preserved_as_interrupted(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000102-702-cccccccccccc"
            )
            with mock.patch.object(
                GATE, "_attempt_id", return_value=attempt_id
            ), mock.patch.object(
                GATE,
                "_run_attempt",
                return_value=(128 + signal.SIGTERM, None, signal.SIGTERM),
            ):
                with self.assertRaises(
                    GATE.RootfixSignalInterrupt
                ) as raised:
                    GATE._execute_attempt(
                        root,
                        attempts,
                        root,
                        status,
                        b"test",
                        lambda: archive,
                        lambda: self.fail(
                            "post validation must not run"
                        ),
                    )
            self.assertEqual(signal.SIGTERM, raised.exception.signum)
            self.assertEqual(
                1,
                len(GATE._validate_recovery_archive(archive, status)),
            )
            records, _ = GATE._published_attempts(attempts, status)
            record = GATE._validate_attempt(
                attempts / attempt_id,
                records[0]["sha256"],
                status,
            )
            self.assertEqual("interrupted", record["outcome"])

    def test_candidate_wrapper_unwinds_fixture_on_forwarded_sigterm(
        self,
    ) -> None:
        candidate_blob = (
            b"from pathlib import Path\n"
            b"import tempfile\n"
            b"import time\n"
            b"root = Path(__file__).resolve().parents[3]\n"
            b"with tempfile.TemporaryDirectory(dir=root / '.claude') as fixture:\n"
            b"    print(fixture, flush=True)\n"
            b"    time.sleep(30)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            test_path = candidate / GATE.TEST_PATH
            test_path.parent.mkdir(parents=True)
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    GATE._candidate_test_wrapper(),
                    str(test_path),
                ],
                cwd=candidate,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            assert process.stdin is not None
            assert process.stdout is not None
            process.stdin.write(candidate_blob)
            process.stdin.close()
            fixture = Path(
                process.stdout.readline().decode("utf-8").strip()
            )
            self.assertTrue(fixture.is_dir())
            os.kill(process.pid, signal.SIGTERM)
            process.wait(timeout=10)
            process.stdout.read()
            process.stdout.close()
            stderr = process.stderr.read() if process.stderr else b""
            if process.stderr:
                process.stderr.close()
            self.assertNotEqual(0, process.returncode, stderr.decode())
            self.assertFalse(fixture.exists())

    def test_run_process_forwards_signal_to_child_process_group(self) -> None:
        helper = "\n".join(
            (
                "import importlib.util",
                "import json",
                "import sys",
                "from pathlib import Path",
                "p = Path(sys.argv[1])",
                "s = importlib.util.spec_from_file_location('g', p)",
                "g = importlib.util.module_from_spec(s)",
                "s.loader.exec_module(g)",
                "root = Path(sys.argv[2])",
                "command = [sys.argv[3], '-c', sys.argv[4], sys.argv[5]]",
                "rc, sig = g._run_process(",
                "    command,",
                "    root,",
                "    root / 'out',",
                "    g.rb._trusted_child_environment(),",
                ")",
                "print(json.dumps([rc, sig]))",
            )
        )
        child = "\n".join(
            (
                "import sys",
                "import tempfile",
                "import time",
                "from pathlib import Path",
                "parent = Path(sys.argv[1])",
                "with tempfile.TemporaryDirectory(dir=parent) as fixture:",
                "    print(fixture, flush=True)",
                "    time.sleep(30)",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixtures = root / "fixtures"
            fixtures.mkdir()
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    helper,
                    str(SCRIPT),
                    str(root),
                    sys.executable,
                    child,
                    str(fixtures),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.monotonic() + 10
            while (
                not any(fixtures.iterdir())
                and process.poll() is None
                and time.monotonic() < deadline
            ):
                time.sleep(0.05)
            self.assertIsNone(process.poll())
            self.assertEqual(1, len(list(fixtures.iterdir())))
            os.kill(process.pid, signal.SIGTERM)
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(0, process.returncode, stderr)
            self.assertEqual(
                [128 + signal.SIGTERM, signal.SIGTERM],
                json.loads(stdout),
            )
            self.assertEqual([], list(fixtures.iterdir()))

    def test_stale_marker_and_staging_require_explicit_recovery(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            operation = (
                "attempt-1700000000000000001-123-0123456789ab"
            )
            stage = attempts / f".staging-{operation}"
            stage.mkdir()
            marker = GATE._running_marker_payload(
                status, operation, stage.name
            )
            marker["pid"] = 99999999
            marker["proc_start"] = "dead"
            (root / GATE.RUNNING_NAME).write_bytes(
                GATE.rb.canonical_json_bytes(marker)
            )
            with mock.patch.object(
                GATE.rb, "_running_marker_live", return_value=False
            ):
                with self.assertRaises(GATE.StaleRootfixError):
                    GATE._require_no_stale_state(root, attempts, status)
                GATE._recover_stale(
                    root,
                    attempts,
                    status,
                    recovery_archive=archive,
                )
            self.assertFalse(stage.exists())
            self.assertFalse((root / GATE.RUNNING_NAME).exists())
            retired = GATE._validate_recovery_archive(
                archive, status
            )
            self.assertEqual(2, len(retired))
            self.assertEqual(
                1,
                sum(
                    path.name.startswith("retired-running-")
                    for path in retired
                ),
            )
            self.assertEqual(
                1,
                sum(
                    path.name.startswith("retired-staging-")
                    for path in retired
                ),
            )

    def test_stale_marker_replacement_is_retained_and_rejected(
        self,
    ) -> None:
        status = self.status()
        for replacement in ("regular", "symlink"):
            with (
                self.subTest(replacement=replacement),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                root.mkdir()
                attempts = root / "attempts"
                attempts.mkdir()
                archive = self.recovery_archive(container, status)
                operation = (
                    "attempt-1700000000000000200-800-"
                    "dddddddddddd"
                )
                stage = attempts / f".staging-{operation}"
                stage.mkdir()
                marker = GATE._running_marker_payload(
                    status, operation, stage.name
                )
                marker["pid"] = 99999999
                marker["proc_start"] = "dead"
                marker_path = root / GATE.RUNNING_NAME
                marker_path.write_bytes(
                    GATE.rb.canonical_json_bytes(marker)
                )
                real_rename = GATE.rb._atomic_rename_noreplace
                replaced = False

                def replace_marker(source, target):
                    nonlocal replaced
                    if Path(source) == marker_path and not replaced:
                        replaced = True
                        marker_path.unlink()
                        if replacement == "regular":
                            marker_path.write_text(
                                "unknown replacement"
                            )
                        else:
                            marker_path.symlink_to(attempts)
                    return real_rename(Path(source), Path(target))

                with mock.patch.object(
                    GATE.rb,
                    "_running_marker_live",
                    return_value=False,
                ), mock.patch.object(
                    GATE.rb,
                    "_atomic_rename_noreplace",
                    side_effect=replace_marker,
                ):
                    with self.assertRaisesRegex(
                        GATE.RootfixError,
                        "changed during archival",
                    ):
                        GATE._recover_stale(
                            root,
                            attempts,
                            status,
                            recovery_archive=archive,
                        )
                self.assertTrue(replaced)
                self.assertFalse(marker_path.exists())
                self.assertTrue(stage.exists())
                retained = list(archive.iterdir())
                self.assertEqual(1, len(retained))
                if replacement == "regular":
                    self.assertEqual(
                        "unknown replacement",
                        retained[0].read_text(),
                    )
                else:
                    self.assertTrue(retained[0].is_symlink())
                    self.assertEqual(
                        attempts.resolve(), retained[0].resolve()
                    )
                with self.assertRaises(GATE.RootfixError):
                    GATE._validate_recovery_archive(
                        archive, status
                    )

    def test_normal_marker_replacement_is_retained_and_rejected(
        self,
    ) -> None:
        status = self.status()
        for index, replacement in enumerate(("regular", "symlink")):
            with (
                self.subTest(replacement=replacement),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                root.mkdir()
                attempts = root / "attempts"
                attempts.mkdir()
                archive = self.recovery_archive(container, status)
                operation = (
                    f"attempt-17000000000000003{index}-"
                    f"81{index}-eeeeeeeeeee{index}"
                )
                marker_path = root / GATE.RUNNING_NAME
                real_rename = GATE.rb._atomic_rename_noreplace
                replaced = False

                def replace_marker(source, target):
                    nonlocal replaced
                    if Path(source) == marker_path and not replaced:
                        replaced = True
                        marker_path.unlink()
                        if replacement == "regular":
                            marker_path.write_text(
                                "unknown replacement"
                            )
                        else:
                            marker_path.symlink_to(attempts)
                    return real_rename(Path(source), Path(target))

                with mock.patch.object(
                    GATE, "_attempt_id", return_value=operation
                ), mock.patch.object(
                    GATE,
                    "_run_attempt",
                    return_value=(7, None, None),
                ), mock.patch.object(
                    GATE.rb,
                    "_atomic_rename_noreplace",
                    side_effect=replace_marker,
                ):
                    with self.assertRaisesRegex(
                        GATE.RootfixError,
                        "changed during archival",
                    ):
                        GATE._execute_attempt(
                            root,
                            attempts,
                            root,
                            status,
                            b"test",
                            lambda: archive,
                            lambda: self.fail(
                                "post validation must not run"
                            ),
                        )
                self.assertTrue(replaced)
                self.assertFalse(marker_path.exists())
                self.assertTrue((attempts / operation).is_dir())
                retained = list(archive.iterdir())
                self.assertEqual(1, len(retained))
                if replacement == "regular":
                    self.assertEqual(
                        "unknown replacement",
                        retained[0].read_text(),
                    )
                else:
                    self.assertTrue(retained[0].is_symlink())
                    self.assertEqual(
                        attempts.resolve(), retained[0].resolve()
                    )
                with self.assertRaises(GATE.RootfixError):
                    GATE._validate_recovery_archive(
                        archive, status
                    )

    def test_identical_marker_replacement_after_read_is_rejected(
        self,
    ) -> None:
        status = self.status()
        for stale in (False, True):
            with (
                self.subTest(stale=stale),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                root.mkdir()
                attempts = root / "attempts"
                attempts.mkdir()
                archive = self.recovery_archive(container, status)
                operation = (
                    "attempt-1700000000000000350-835-"
                    f"{'a' if stale else 'b'}bbbbbbbbbbb"
                )
                stage = attempts / f".staging-{operation}"
                if stale:
                    stage.mkdir()
                marker = GATE._running_marker_payload(
                    status, operation, stage.name
                )
                marker["pid"] = 99999999
                marker["proc_start"] = "dead"
                marker_path = root / GATE.RUNNING_NAME
                marker_path.write_bytes(
                    GATE.rb.canonical_json_bytes(marker)
                )
                original_inode = os.lstat(marker_path).st_ino
                real_load = GATE._canonical_snapshot_object
                replaced = False

                def replace_after_read(data, label):
                    nonlocal replaced
                    loaded = real_load(data, label)
                    if (
                        label == "rootfix running marker"
                        and not replaced
                    ):
                        replaced = True
                        marker_path.unlink()
                        marker_path.write_bytes(data)
                    return loaded

                with mock.patch.object(
                    GATE,
                    "_canonical_snapshot_object",
                    side_effect=replace_after_read,
                ), mock.patch.object(
                    GATE.rb,
                    "_running_marker_live",
                    return_value=False,
                ):
                    with self.assertRaisesRegex(
                        GATE.RootfixError,
                        "changed before archival|identity changed|"
                        "presence or identity changed|"
                        "contents changed during enumeration",
                    ):
                        if stale:
                            GATE._recover_stale(
                                root,
                                attempts,
                                status,
                                recovery_archive=archive,
                            )
                        else:
                            GATE._archive_validated_running_marker(
                                root,
                                archive,
                                status,
                                marker,
                            )
                self.assertTrue(replaced)
                self.assertTrue(marker_path.exists())
                self.assertNotEqual(
                    original_inode, os.lstat(marker_path).st_ino
                )
                self.assertEqual([], list(archive.iterdir()))
                if stale:
                    self.assertTrue(stage.exists())

    def test_run_recovery_binds_initial_marker_presence(self) -> None:
        status = self.status()
        candidate_test = self.candidate_test_record()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(container, status)
            operation = (
                "attempt-1700000000000000352-837-cccccccccccc"
            )
            stage = attempts / f".staging-{operation}"
            stage.mkdir()
            marker = GATE._running_marker_payload(
                status, operation, stage.name
            )
            marker["pid"] = 99999999
            marker["proc_start"] = "dead"
            marker_path = root / GATE.RUNNING_NAME
            marker_path.write_bytes(
                GATE.rb.canonical_json_bytes(marker)
            )
            bundle_path = container / "bundle"
            bundle_path.mkdir()
            real_recover = GATE._recover_stale
            removed = False

            def remove_before_recovery(*args, **kwargs):
                nonlocal removed
                marker_path.unlink()
                removed = True
                return real_recover(*args, **kwargs)

            with mock.patch.object(
                GATE.rb, "_resolve_bundle_path", return_value=bundle_path
            ), mock.patch.object(
                GATE.rb,
                "bundle_lock",
                return_value=contextlib.nullcontext(),
            ), mock.patch.object(
                GATE.rb, "_validate_bundle_locked", return_value=status
            ), mock.patch.object(
                GATE,
                "_validate_topology",
                return_value=(
                    container / "target",
                    container / "candidate",
                    candidate_test,
                    b"candidate",
                ),
            ), mock.patch.object(
                GATE, "_evidence_path", return_value=root
            ), mock.patch.object(
                GATE, "_recovery_archive_path", return_value=archive
            ), mock.patch.object(
                GATE,
                "_recover_stale",
                side_effect=remove_before_recovery,
            ), mock.patch.object(
                GATE, "_execute_attempt"
            ) as execute:
                with self.assertRaisesRegex(
                    GATE.RootfixError,
                    "presence or identity changed",
                ):
                    GATE.run_gate(
                        container / "candidate",
                        container / "target",
                        status["bundle_id"],
                        recover_stale=True,
                    )
            self.assertTrue(removed)
            execute.assert_not_called()
            self.assertFalse(marker_path.exists())
            self.assertTrue(stage.exists())

    def test_first_inventory_binds_approval_presence_and_identity(
        self,
    ) -> None:
        status = self.status()
        for mutation in ("remove", "replace"):
            with (
                self.subTest(mutation=mutation),
                tempfile.TemporaryDirectory() as tmp,
            ):
                root = Path(tmp) / "root"
                (root / "attempts").mkdir(parents=True)
                approval = root / GATE.APPROVAL_NAME
                approval.write_bytes(
                    GATE.rb.canonical_json_bytes({"observed": True})
                )
                context = GATE._open_evidence_context(
                    root,
                    create_attempts=False,
                    require_attempts=True,
                )
                try:
                    initial = GATE._validate_evidence_objects(context)
                    original = approval.read_bytes()
                    approval.unlink()
                    if mutation == "replace":
                        approval.write_bytes(original)
                    current = GATE._validate_evidence_objects(context)
                    with self.assertRaisesRegex(
                        GATE.RootfixError,
                        "approval presence or identity changed",
                    ):
                        GATE._validate_inventory_identity(
                            initial, current
                        )
                finally:
                    context.close()

    def test_markerless_staging_requires_valid_unique_operation_id(
        self,
    ) -> None:
        status = self.status()
        cases = (
            (
                (".staging-attempt-?",),
                GATE.RootfixError,
                False,
            ),
            (
                (".staging-attempt-prefix-only",),
                GATE.RootfixError,
                False,
            ),
            (
                (
                    (
                        ".staging-attempt-1700000000000000002-"
                        "124-1123456789ab"
                    ),
                    (
                        ".staging-attempt-1700000000000000003-"
                        "125-2123456789ab"
                    ),
                ),
                GATE.StaleRootfixError,
                False,
            ),
            (
                (
                    (
                        ".staging-attempt-1700000000000000004-"
                        "126-3123456789ab"
                    ),
                ),
                None,
                True,
            ),
        )
        for names, expected_error, removed in cases:
            with self.subTest(names=names), tempfile.TemporaryDirectory() as tmp:
                container = Path(tmp)
                root = container / "active"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                archive = self.recovery_archive(container, status)
                paths = []
                for name in names:
                    path = attempts / name
                    path.mkdir()
                    (path / "preserved.txt").write_text("data")
                    paths.append(path)
                if expected_error is None:
                    GATE._recover_stale(
                        root,
                        attempts,
                        status,
                        recovery_archive=archive,
                    )
                else:
                    with self.assertRaises(expected_error):
                        GATE._recover_stale(root, attempts, status)
                self.assertEqual(
                    [not removed] * len(paths),
                    [path.exists() for path in paths],
                )
                if removed:
                    archived = GATE._validate_recovery_archive(
                        archive, status
                    )
                    self.assertEqual(1, len(archived))
                    self.assertEqual(
                        "data",
                        (archived[0] / "preserved.txt").read_text(),
                    )

    def test_live_marker_cannot_be_recovered(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempts = root / "attempts"
            attempts.mkdir()
            operation = (
                "attempt-1700000000000000005-127-4123456789ab"
            )
            stage = attempts / f".staging-{operation}"
            stage.mkdir()
            (root / GATE.RUNNING_NAME).write_bytes(
                GATE.rb.canonical_json_bytes(
                    GATE._running_marker_payload(
                        status, operation, stage.name
                    )
                )
            )
            atomic_temp = (
                root / ".tmp-approval.json-123-0123456789abcdef"
            )
            atomic_temp.write_text("partial approval")
            with mock.patch.object(
                GATE.rb, "_running_marker_live", return_value=True
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError, "may not be recovered"
                ):
                    GATE._recover_stale(root, attempts, status)
            self.assertTrue(stage.exists())
            self.assertTrue((root / GATE.RUNNING_NAME).exists())
            self.assertTrue(atomic_temp.exists())

    def test_root_atomic_temps_require_explicit_recovery(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            atomic_temps = [
                root / ".tmp-running.json-123-0123456789abcdef",
                root / ".tmp-approval.json-456-fedcba9876543210",
                root
                / (
                    ".recover-approval.json-789-0011223344556677-"
                    "321-8899aabbccddeeff"
                ),
            ]
            for path in atomic_temps:
                path.write_text("interrupted atomic write")

            with self.assertRaises(GATE.StaleRootfixError):
                GATE._validate_evidence_objects(root)
            with self.assertRaises(GATE.StaleRootfixError):
                GATE._require_no_stale_state(root, attempts, status)
            discovered = GATE._validate_evidence_objects(
                root, allow_atomic_temps=True
            )
            self.assertEqual(
                sorted(atomic_temps),
                sorted(item.path for item in discovered.atomic_temps),
            )

            with mock.patch.object(
                GATE,
                "_read_regular_at",
                side_effect=GATE.RootfixError("inode changed"),
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError, "inode changed"
                ):
                    GATE._recover_stale(
                        root,
                        attempts,
                        status,
                        discovered.atomic_temps,
                        archive,
                    )
            self.assertTrue(all(path.exists() for path in atomic_temps))

            with mock.patch.object(
                GATE.os,
                "unlink",
                side_effect=AssertionError(
                    "root atomic recovery must not unlink"
                ),
            ):
                GATE._recover_stale(
                    root,
                    attempts,
                    status,
                    discovered.atomic_temps,
                    archive,
                )
            self.assertFalse(any(path.exists() for path in atomic_temps))
            self.assertEqual(
                (), GATE._validate_evidence_objects(root).atomic_temps
            )
            archived = GATE._validate_recovery_archive(
                archive, status
            )
            self.assertEqual(3, len(archived))
            self.assertEqual(
                sorted(
                    (
                        "interrupted atomic write",
                        "interrupted atomic write",
                        "interrupted atomic write",
                    )
                ),
                sorted(path.read_text() for path in archived),
            )

            malformed = (
                root / ".tmp-approval.json-0-0123456789abcdef"
            )
            malformed.write_text("not an exact atomic temp")
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_evidence_objects(
                    root, allow_atomic_temps=True
                )
            malformed.unlink()

            oversized = (
                root / ".tmp-approval.json-789-0011223344556677"
            )
            with oversized.open("wb") as stream:
                stream.truncate(1024 * 1024 + 1)
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_evidence_objects(
                    root, allow_atomic_temps=True
                )
            oversized.unlink()

            unsafe = (
                root / ".tmp-running.json-987-8899aabbccddeeff"
            )
            try:
                unsafe.symlink_to(root / "attempts")
            except (OSError, NotImplementedError):
                return
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_evidence_objects(
                    root, allow_atomic_temps=True
                )

    def test_atomic_temp_replacement_is_archived_and_rejected(self) -> None:
        status = self.status()
        for replacement in ("regular", "symlink"):
            with (
                self.subTest(replacement=replacement),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                root.mkdir()
                attempts = root / "attempts"
                attempts.mkdir()
                archive = self.recovery_archive(container, status)
                atomic_temp = (
                    root
                    / ".tmp-approval.json-123-0123456789abcdef"
                )
                atomic_temp.write_text("validated inode")
                discovered = GATE._validate_evidence_objects(
                    root, allow_atomic_temps=True
                )
                real_rename = GATE.rb._atomic_rename_noreplace
                replaced = False

                def replace_after_read(source, target):
                    nonlocal replaced
                    if Path(source) == atomic_temp and not replaced:
                        replaced = True
                        atomic_temp.unlink()
                        if replacement == "regular":
                            atomic_temp.write_text("replacement inode")
                        else:
                            atomic_temp.symlink_to(attempts)
                    return real_rename(Path(source), Path(target))

                with mock.patch.object(
                    GATE.rb,
                    "_atomic_rename_noreplace",
                    side_effect=replace_after_read,
                ):
                    with self.assertRaisesRegex(
                        GATE.RootfixError, "changed during archival"
                    ):
                        GATE._recover_stale(
                            root,
                            attempts,
                            status,
                            discovered.atomic_temps,
                            archive,
                        )
                self.assertTrue(replaced)
                self.assertFalse(atomic_temp.exists())
                retained = list(archive.iterdir())
                self.assertEqual(1, len(retained))
                if replacement == "regular":
                    self.assertEqual(
                        "replacement inode",
                        retained[0].read_text(),
                    )
                else:
                    self.assertTrue(retained[0].is_symlink())
                    self.assertEqual(
                        attempts.resolve(), retained[0].resolve()
                    )
                with self.assertRaises(GATE.RootfixError):
                    GATE._validate_recovery_archive(
                        archive, status
                    )

    def test_interrupted_atomic_archival_is_retained_and_revalidated(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            atomic_temp = (
                root / ".tmp-running.json-123-0123456789abcdef"
            )
            atomic_temp.write_text("interrupted recovery")
            discovered = GATE._validate_evidence_objects(
                root, allow_atomic_temps=True
            )
            real_lstat = os.lstat
            interrupted = False

            def interrupt_after_isolation(path):
                nonlocal interrupted
                if (
                    Path(path).parent == archive
                    and not interrupted
                ):
                    interrupted = True
                    raise KeyboardInterrupt
                return real_lstat(path)

            with mock.patch.object(
                GATE.os,
                "lstat",
                side_effect=interrupt_after_isolation,
            ):
                with self.assertRaises(KeyboardInterrupt):
                    GATE._recover_stale(
                        root,
                        attempts,
                        status,
                        discovered.atomic_temps,
                        archive,
                    )
            self.assertTrue(interrupted)
            self.assertFalse(atomic_temp.exists())
            archived = GATE._validate_recovery_archive(
                archive, status
            )
            self.assertEqual(1, len(archived))
            self.assertEqual(
                "interrupted recovery", archived[0].read_text()
            )
            GATE._recover_stale(
                root,
                attempts,
                status,
                [],
                archive,
            )
            self.assertTrue(archived[0].exists())
            self.assertEqual(
                (), GATE._validate_evidence_objects(root).atomic_temps
            )

    def test_archived_atomic_replacement_is_retained_and_rejected(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            atomic_temp = (
                root / ".tmp-running.json-123-0123456789abcdef"
            )
            atomic_temp.write_text("validated inode")
            discovered = GATE._validate_evidence_objects(
                root, allow_atomic_temps=True
            )
            real_read = GATE._read_regular_snapshot
            replaced = False

            def replace_archived_path(path, label, **kwargs):
                nonlocal replaced
                path = Path(path)
                if path.parent == archive and not replaced:
                    replaced = True
                    path.unlink()
                    path.write_text("replacement after archival")
                return real_read(path, label, **kwargs)

            with mock.patch.object(
                GATE,
                "_read_regular_snapshot",
                side_effect=replace_archived_path,
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError,
                    "identity, size or link count|changed while reading|content digest is invalid",
                ):
                    GATE._recover_stale(
                        root,
                        attempts,
                        status,
                        discovered.atomic_temps,
                        archive,
                    )
            self.assertTrue(replaced)
            self.assertFalse(atomic_temp.exists())
            retained = list(archive.iterdir())
            self.assertEqual(1, len(retained))
            self.assertEqual(
                "replacement after archival", retained[0].read_text()
            )
            with self.assertRaisesRegex(
                GATE.RootfixError,
                "identity, size or link count|changed while reading|content digest is invalid",
            ):
                GATE._validate_recovery_archive(
                    archive, status
                )

    def test_identical_post_move_archive_replacement_is_rejected(
        self,
    ) -> None:
        status = self.status()
        for kind in ("atomic", "marker"):
            with (
                self.subTest(kind=kind),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                root.mkdir()
                (root / "attempts").mkdir()
                archive = self.recovery_archive(container, status)
                replaced = False
                if kind == "atomic":
                    source = (
                        root
                        / ".tmp-running.json-123-0123456789abcdef"
                    )
                    source.write_text("byte-identical replacement")
                    original_validator = (
                        GATE._validate_archived_root_atomic
                    )

                    def replace_atomic(path, expected_identity=None):
                        nonlocal replaced
                        data = Path(path).read_bytes()
                        Path(path).unlink()
                        Path(path).write_bytes(data)
                        replaced = True
                        return original_validator(
                            Path(path), expected_identity
                        )

                    patcher = mock.patch.object(
                        GATE,
                        "_validate_archived_root_atomic",
                        side_effect=replace_atomic,
                    )
                    archive_call = lambda: (
                        GATE._archive_validated_root_atomic(
                            source, archive
                        )
                    )
                else:
                    operation = (
                        "attempt-1700000000000000360-836-"
                        "dddddddddddd"
                    )
                    marker = GATE._running_marker_payload(
                        status,
                        operation,
                        f".staging-{operation}",
                    )
                    source = root / GATE.RUNNING_NAME
                    source.write_bytes(
                        GATE.rb.canonical_json_bytes(marker)
                    )
                    original_validator = (
                        GATE._validate_archived_running_marker
                    )

                    def replace_marker(
                        path, current_status, expected_identity=None
                    ):
                        nonlocal replaced
                        data = Path(path).read_bytes()
                        Path(path).unlink()
                        Path(path).write_bytes(data)
                        replaced = True
                        return original_validator(
                            Path(path),
                            current_status,
                            expected_identity,
                        )

                    patcher = mock.patch.object(
                        GATE,
                        "_validate_archived_running_marker",
                        side_effect=replace_marker,
                    )
                    archive_call = lambda: (
                        GATE._archive_validated_running_marker(
                            root, archive, status, marker
                        )
                    )
                with patcher:
                    with self.assertRaisesRegex(
                        GATE.RootfixError, "identity"
                    ):
                        archive_call()
                self.assertTrue(replaced)
                self.assertFalse(source.exists())
                retained = list(archive.iterdir())
                self.assertEqual(1, len(retained))
                self.assertEqual(
                    b"byte-identical replacement"
                    if kind == "atomic"
                    else GATE.rb.canonical_json_bytes(marker),
                    retained[0].read_bytes(),
                )

    def test_recovery_archive_inventory_and_digest_fail_closed(
        self,
    ) -> None:
        status = self.status()
        cases = ("unknown", "directory", "symlink", "hardlink")
        for case in cases:
            with (
                self.subTest(case=case),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                archive = self.recovery_archive(container, status)
                data = b"preserved residue"
                digest = hashlib.sha256(data).hexdigest()
                name = (
                    "recovered-tmp-running.json-123-"
                    f"0123456789abcdef-{digest}-"
                    "456-fedcba9876543210"
                )
                archived = archive / name
                if case == "unknown":
                    archived.write_bytes(data)
                    (archive / "unknown").write_text("unknown")
                elif case == "directory":
                    archived.mkdir()
                elif case == "symlink":
                    try:
                        archived.symlink_to(container)
                    except (OSError, NotImplementedError):
                        continue
                else:
                    archived.write_bytes(data)
                    os.link(archived, container / "external-link")
                with self.assertRaises(GATE.RootfixError):
                    GATE._validate_recovery_archive(
                        archive, status
                    )

        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            archive = self.recovery_archive(container, status)
            data = b"preserved residue"
            digest = hashlib.sha256(data).hexdigest()
            archived = archive / (
                "recovered-recover-approval.json-123-"
                f"0123456789abcdef-{digest}-"
                "456-fedcba9876543210"
            )
            archived.write_bytes(data)
            self.assertEqual(
                [archived],
                GATE._validate_recovery_archive(
                    archive, status
                ),
            )
            archived.write_bytes(b"tampered")
            with self.assertRaisesRegex(
                GATE.RootfixError, "content digest is invalid"
            ):
                GATE._validate_recovery_archive(
                    archive, status
                )

    def test_archived_marker_rejects_invalid_static_field_types(
        self,
    ) -> None:
        status = self.status()
        operation = (
            "attempt-1700000000000000370-838-eeeeeeeeeeee"
        )
        cases = (
            ("pid", "not-an-integer", "pid"),
            ("pid", True, "pid"),
            ("pid", 0, "pid"),
            ("proc_start", [], "process token"),
            ("proc_start", "", "process token"),
            ("boot_id", {}, "boot id"),
            ("boot_id", "", "boot id"),
        )
        for field, value, error in cases:
            with (
                self.subTest(field=field, value=value),
                tempfile.TemporaryDirectory() as tmp,
            ):
                archive = self.recovery_archive(
                    Path(tmp), status
                )
                self.write_retired_marker(
                    archive,
                    status,
                    operation,
                    updates={field: value},
                )
                with self.assertRaisesRegex(
                    GATE.RootfixError, error
                ):
                    GATE._validate_recovery_archive(
                        archive, status
                    )

    def test_attempt_marker_conservation_rejects_missing_and_duplicate(
        self,
    ) -> None:
        status = self.status()
        operation = (
            "attempt-1700000000000000371-839-ffffffffffff"
        )
        records = [
            {"attempt_id": operation, "sha256": "a" * 64}
        ]
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.recovery_archive(Path(tmp), status)
            with self.assertRaisesRegex(
                GATE.RootfixError, "lacks exactly one"
            ):
                GATE._validate_attempt_marker_conservation(
                    records, []
                )
            first = self.write_retired_marker(
                archive,
                status,
                operation,
                attempt_sha256="a" * 64,
            )
            second = archive / first.name.replace(
                "123-0123456789abcdef.json",
                "124-fedcba9876543210.json",
            )
            second.write_bytes(first.read_bytes())
            archive_objects = GATE._validate_recovery_archive(
                archive, status
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "duplicate"
            ):
                GATE._validate_attempt_marker_conservation(
                    records, archive_objects
                )

    def test_stale_marker_rejects_conflicting_staging_inventory(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            attempts = root / "attempts"
            attempts.mkdir()
            operation = (
                "attempt-1700000000000000006-128-5123456789ab"
            )
            expected = attempts / f".staging-{operation}"
            extra = attempts / (
                ".staging-attempt-1700000000000000007-"
                "129-6123456789ab"
            )
            expected.mkdir()
            extra.mkdir()
            (root / GATE.RUNNING_NAME).write_bytes(
                GATE.rb.canonical_json_bytes(
                    GATE._running_marker_payload(
                        status, operation, expected.name
                    )
                )
            )
            with mock.patch.object(
                GATE.rb, "_running_marker_live", return_value=False
            ):
                with self.assertRaisesRegex(
                    GATE.StaleRootfixError, "conflicts"
                ):
                    GATE._recover_stale(root, attempts, status)
            self.assertTrue(expected.exists())
            self.assertTrue(extra.exists())

    def test_unique_passing_attempt_completes_approval_after_write_failure(
        self,
    ) -> None:
        status = self.status()
        candidate_test = self.candidate_test_record()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(container, status)
            failed_id = (
                "attempt-1700000000000000400-840-aaaaaaaaaaaa"
            )
            passing_id = (
                "attempt-1700000000000000401-841-bbbbbbbbbbbb"
            )
            failed = attempts / failed_id
            passing_path = attempts / passing_id
            failed_sha256 = self.write_attempt(
                failed,
                status,
                outcome="fail",
                exit_code=7,
            )
            passing_sha256 = self.write_attempt(
                passing_path,
                status,
                outcome="pass",
                exit_code=0,
            )
            self.write_retired_marker(
                archive,
                status,
                failed_id,
                attempt_sha256=failed_sha256,
            )
            self.write_retired_marker(
                archive,
                status,
                passing_id,
                attempt_sha256=passing_sha256,
            )
            archive_objects = GATE._validate_recovery_archive(
                archive, status
            )
            records, passing = GATE._published_attempts(attempts, status)
            self.assertIsNotNone(passing)
            with mock.patch.object(
                GATE,
                "_atomic_write_once_at",
                side_effect=OSError("approval write failed"),
            ):
                with self.assertRaisesRegex(OSError, "approval write failed"):
                    GATE._publish_approval_from_passing(
                        root,
                        status,
                        candidate_test,
                        records,
                        passing,
                    )
            self.assertFalse((root / GATE.APPROVAL_NAME).exists())
            GATE._publish_approval_from_passing(
                root,
                status,
                candidate_test,
                records,
                passing,
            )
            first_bytes = (root / GATE.APPROVAL_NAME).read_bytes()
            result = GATE._validate_approval(
                root, status, candidate_test, archive_objects
            )
            self.assertEqual("ROOTFIX_MERGEABLE", result["state"])
            self.assertEqual(
                first_bytes,
                GATE.rb.canonical_json_bytes(
                    GATE._approval_payload(
                        status,
                        candidate_test,
                        records,
                        passing["attempt_id"],
                        passing["sha256"],
                    )
                ),
            )
            (failed / "unregistered-empty-directory").mkdir()
            with self.assertRaises(GATE.RootfixError):
                GATE._validate_approval(
                    root, status, candidate_test, archive_objects
                )

    def test_missing_marker_retirement_cannot_resume_passing_attempt(
        self,
    ) -> None:
        status = self.status()
        candidate_test = self.candidate_test_record()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            root.mkdir()
            attempts = root / "attempts"
            attempts.mkdir()
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000410-850-dddddddddddd"
            )

            def successful_run(
                stage,
                _candidate_top,
                current_status,
                _candidate_test_blob,
                commands,
                artifact_seals,
            ):
                stage_path = (
                    stage.path
                    if isinstance(stage, GATE.DirectoryHandle)
                    else Path(stage)
                )
                commands.update(
                    GATE._expected_commands(current_status)
                )
                for phase, command in commands.items():
                    self.write_process_record(
                        stage_path,
                        current_status,
                        attempt_id,
                        phase,
                        command,
                )
                (stage_path / "candidate-test.py").write_text("pass\n")
                (stage_path / "candidate-test.log").write_text("PASS\n")
                run = stage_path / "profile-output" / "run"
                metadata = self.write_profile_metadata(
                    run,
                    current_status,
                    worktree=_candidate_top,
                )
                (stage_path / "code-profile.log").write_bytes(
                    self.profile_process_log(run, metadata)
                )
                for name in ("candidate-test.log", "code-profile.log"):
                    artifact_seals[name] = GATE._read_regular_snapshot(
                        stage_path / name, "test raw log"
                    )
                return 0, "run/metadata.json", None

            real_archive_marker = (
                GATE._archive_validated_running_marker
            )

            def disappear_before_retirement(*args, **kwargs):
                (root / GATE.RUNNING_NAME).unlink()
                return real_archive_marker(*args, **kwargs)

            with mock.patch.object(
                GATE, "_attempt_id", return_value=attempt_id
            ), mock.patch.object(
                GATE, "_run_attempt", side_effect=successful_run
            ), mock.patch.object(
                GATE,
                "_archive_validated_running_marker",
                side_effect=disappear_before_retirement,
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError, "disappeared"
                ):
                    GATE._execute_attempt(
                        root,
                        attempts,
                        root,
                        status,
                        b"candidate",
                        lambda: archive,
                        lambda: None,
                    )
            records, passing = GATE._published_attempts(
                attempts, status
            )
            self.assertEqual(1, len(records))
            self.assertIsNotNone(passing)
            self.assertEqual([], list(archive.iterdir()))

            bundle_path = container / "bundle"
            bundle_path.mkdir()
            with mock.patch.object(
                GATE.rb, "_resolve_bundle_path", return_value=bundle_path
            ), mock.patch.object(
                GATE.rb,
                "bundle_lock",
                return_value=contextlib.nullcontext(),
            ), mock.patch.object(
                GATE.rb, "_validate_bundle_locked", return_value=status
            ), mock.patch.object(
                GATE,
                "_validate_topology",
                return_value=(
                    container / "target",
                    container / "candidate",
                    candidate_test,
                    b"candidate",
                ),
            ), mock.patch.object(
                GATE, "_evidence_path", return_value=root
            ), mock.patch.object(
                GATE, "_recovery_archive_path", return_value=archive
            ), mock.patch.object(
                GATE, "_execute_attempt"
            ) as execute, mock.patch.object(
                GATE, "_publish_approval_from_passing"
            ) as publish:
                with self.assertRaisesRegex(
                    GATE.RootfixError,
                    "lacks an external digest seal|lacks exactly one retired",
                ):
                    GATE.run_gate(
                        container / "candidate",
                        container / "target",
                        status["bundle_id"],
                    )
            execute.assert_not_called()
            publish.assert_not_called()
            self.assertFalse((root / GATE.APPROVAL_NAME).exists())

    def test_published_attempt_without_retirement_seal_cannot_recover(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000411-851-eeeeeeeeeeee"
            )
            attempt = attempts / attempt_id
            self.write_attempt(
                attempt,
                status,
                outcome="pass",
                exit_code=0,
            )
            marker = GATE._running_marker_payload(
                status,
                attempt_id,
                f".staging-{attempt_id}",
            )
            marker["pid"] = 99999999
            marker["proc_start"] = "dead"
            (root / GATE.RUNNING_NAME).write_bytes(
                GATE.rb.canonical_json_bytes(marker)
            )
            with mock.patch.object(
                GATE.rb, "_running_marker_live", return_value=False
            ):
                with self.assertRaisesRegex(
                    GATE.StaleRootfixError,
                    "lacks a durable external digest seal",
                ):
                    GATE._recover_stale(
                        root,
                        attempts,
                        status,
                        recovery_archive=archive,
                    )
            self.assertTrue(attempt.exists())
            self.assertTrue((root / GATE.RUNNING_NAME).exists())
            self.assertEqual([], list(archive.iterdir()))

    def test_run_gate_reuses_unique_passing_attempt_without_retry(self) -> None:
        status = self.status()
        candidate_test = self.candidate_test_record()
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / "candidate"
            target = Path(tmp) / "target"
            candidate.mkdir()
            target.mkdir()
            root = Path(tmp) / "rootfix"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(Path(tmp), status)
            attempt_id = (
                "attempt-1700000000000000402-842-cccccccccccc"
            )
            attempt_sha256 = self.write_attempt(
                attempts / attempt_id,
                status,
                outcome="pass",
                exit_code=0,
                worktree=candidate,
            )
            self.write_retired_marker(
                archive,
                status,
                attempt_id,
                attempt_sha256=attempt_sha256,
            )
            approval_temp = (
                root / ".tmp-approval.json-123-0123456789abcdef"
            )
            approval_temp.write_text("interrupted approval")
            bundle_path = Path(tmp) / "bundle"
            bundle_path.mkdir()
            with mock.patch.object(
                GATE.rb, "_resolve_bundle_path", return_value=bundle_path
            ), mock.patch.object(
                GATE.rb,
                "bundle_lock",
                return_value=contextlib.nullcontext(),
            ), mock.patch.object(
                GATE.rb, "_validate_bundle_locked", return_value=status
            ), mock.patch.object(
                GATE,
                "_validate_topology",
                return_value=(
                    target,
                    candidate,
                    candidate_test,
                    b"candidate",
                ),
            ), mock.patch.object(
                GATE, "_evidence_path", return_value=root
            ), mock.patch.object(
                GATE, "_recovery_archive_path", return_value=archive
            ), mock.patch.object(
                GATE, "_execute_attempt"
            ) as execute:
                result = GATE.run_gate(
                    candidate,
                    target,
                    status["bundle_id"],
                    recover_stale=True,
                )
            execute.assert_not_called()
            self.assertFalse(approval_temp.exists())
            self.assertEqual(
                2,
                len(
                    GATE._validate_recovery_archive(
                        archive, status
                    )
                ),
            )
            self.assertEqual("ROOTFIX_MERGEABLE", result["state"])

    def test_run_gate_re_resolves_archive_after_long_attempt(
        self,
    ) -> None:
        status = self.status()
        candidate_test = self.candidate_test_record()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "rootfix"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = (
                container
                / GATE.RECOVERY_ARCHIVE_PART
                / status["bundle_id"]
            )
            bundle_path = container / "bundle"
            bundle_path.mkdir()

            def resolve_archive(_repo, _bundle_id, *, create):
                if create:
                    archive.mkdir(parents=True, exist_ok=True)
                    return archive
                return archive if archive.exists() else None

            def inject_archive(*_arguments):
                archive.mkdir(parents=True)
                (archive / "unknown").write_text(
                    "created during long attempt"
                )
                return attempts / "unused", "0" * 64, 0, None

            with mock.patch.object(
                GATE.rb, "_resolve_bundle_path", return_value=bundle_path
            ), mock.patch.object(
                GATE.rb,
                "bundle_lock",
                return_value=contextlib.nullcontext(),
            ), mock.patch.object(
                GATE.rb, "_validate_bundle_locked", return_value=status
            ), mock.patch.object(
                GATE,
                "_validate_topology",
                return_value=(
                    container / "target",
                    container / "candidate",
                    candidate_test,
                    b"candidate",
                ),
            ), mock.patch.object(
                GATE, "_evidence_path", return_value=root
            ), mock.patch.object(
                GATE,
                "_recovery_archive_path",
                side_effect=resolve_archive,
            ), mock.patch.object(
                GATE,
                "_execute_attempt",
                side_effect=inject_archive,
            ), mock.patch.object(
                GATE, "_publish_approval_from_passing"
            ) as publish:
                with self.assertRaisesRegex(
                    GATE.RootfixError,
                    "unexpected rootfix recovery archive object",
                ):
                    GATE.run_gate(
                        container / "candidate",
                        container / "target",
                        status["bundle_id"],
                    )
            publish.assert_not_called()
            self.assertFalse((root / GATE.APPROVAL_NAME).exists())
            self.assertEqual(
                "created during long attempt",
                (archive / "unknown").read_text(),
            )

    def test_nonpassing_retry_still_checks_preexisting_history(self) -> None:
        cases = (
            ("fail", 7, None),
            (
                "interrupted",
                128 + signal.SIGTERM,
                signal.SIGTERM,
            ),
        )
        for index, (outcome, exit_code, interrupted_signal) in enumerate(
            cases, 1
        ):
            with (
                self.subTest(outcome=outcome),
                tempfile.TemporaryDirectory() as tmp,
            ):
                status = self.status()
                candidate_test = self.candidate_test_record()
                container = Path(tmp)
                candidate = container / "candidate"
                target = container / "target"
                candidate.mkdir()
                target.mkdir()
                root = container / "rootfix"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                archive = self.recovery_archive(container, status)
                old_attempt_id = (
                    f"attempt-170000000000000040{index}-"
                    f"84{index}-{index:012x}"
                )
                old_attempt = attempts / old_attempt_id
                old_sha256 = self.write_attempt(
                    old_attempt,
                    status,
                    outcome="fail",
                    exit_code=1,
                    worktree=candidate,
                )
                old_marker = self.write_retired_marker(
                    archive,
                    status,
                    old_attempt_id,
                    attempt_sha256=old_sha256,
                )
                new_attempt_id = (
                    f"attempt-170000000000000041{index}-"
                    f"85{index}-{index + 10:012x}"
                )

                def replace_history(*_arguments):
                    shutil.rmtree(old_attempt)
                    old_marker.unlink()
                    new_attempt = attempts / new_attempt_id
                    new_sha256 = self.write_attempt(
                        new_attempt,
                        status,
                        outcome=outcome,
                        exit_code=exit_code,
                        interrupted_signal=interrupted_signal,
                        worktree=candidate,
                    )
                    new_marker = self.write_retired_marker(
                        archive,
                        status,
                        new_attempt_id,
                        attempt_sha256=new_sha256,
                    )
                    snapshot = GATE._read_regular_snapshot(
                        new_marker,
                        "test retired running marker",
                    )
                    seal = GATE.ArchiveSeal(
                        new_marker,
                        snapshot.dev,
                        snapshot.ino,
                        snapshot.size,
                        snapshot.sha256,
                        "running",
                    )
                    return new_attempt, new_sha256, exit_code, seal

                bundle_path = container / "bundle"
                bundle_path.mkdir()
                with mock.patch.object(
                    GATE.rb,
                    "_resolve_bundle_path",
                    return_value=bundle_path,
                ), mock.patch.object(
                    GATE.rb,
                    "bundle_lock",
                    return_value=contextlib.nullcontext(),
                ), mock.patch.object(
                    GATE.rb,
                    "_validate_bundle_locked",
                    return_value=status,
                ), mock.patch.object(
                    GATE,
                    "_validate_topology",
                    return_value=(
                        target,
                        candidate,
                        candidate_test,
                        b"candidate",
                    ),
                ), mock.patch.object(
                    GATE, "_evidence_path", return_value=root
                ), mock.patch.object(
                    GATE,
                    "_recovery_archive_path",
                    return_value=archive,
                ), mock.patch.object(
                    GATE,
                    "_execute_attempt",
                    side_effect=replace_history,
                ), mock.patch.object(
                    GATE, "_publish_approval_from_passing"
                ) as publish:
                    with self.assertRaisesRegex(
                        GATE.RootfixError,
                        "pre-existing rootfix attempt history",
                    ):
                        GATE.run_gate(
                            candidate,
                            target,
                            status["bundle_id"],
                            retry_failed=True,
                        )
                publish.assert_not_called()
                self.assertFalse(
                    (root / GATE.APPROVAL_NAME).exists()
                )

    def test_attempt_and_approval_hardlinks_fail_closed(self) -> None:
        status = self.status()
        cases = (
            ("fail", 7, None),
            ("interrupted", 128 + signal.SIGINT, signal.SIGINT),
            ("pass", 0, None),
        )
        for index, (outcome, exit_code, interrupted_signal) in enumerate(
            cases, 1
        ):
            for link_kind in ("external", "internal"):
                with (
                    self.subTest(outcome=outcome, link_kind=link_kind),
                    tempfile.TemporaryDirectory() as tmp,
                ):
                    container = Path(tmp)
                    attempt_id = (
                        f"attempt-17000000000000005{index}0-"
                        f"9{index}0-{index:012x}"
                    )
                    (container / "attempts").mkdir()
                    attempt = container / "attempts" / attempt_id
                    self.write_attempt(
                        attempt,
                        status,
                        outcome=outcome,
                        exit_code=exit_code,
                        interrupted_signal=interrupted_signal,
                    )
                    target = (
                        attempt
                        / (
                            "profile-output/run/metadata.json"
                            if outcome == "pass"
                            else "candidate-test.log"
                        )
                    )
                    link = (
                        container / "external-hardlink"
                        if link_kind == "external"
                        else attempt / "internal-hardlink"
                    )
                    os.link(target, link)
                    with self.assertRaisesRegex(
                        GATE.RootfixError, "link count"
                    ):
                        GATE._validate_attempt(
                            attempt,
                            None,
                            status,
                        )

        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000599-999-ffffffffffff"
            )
            attempt_sha256 = self.write_attempt(
                attempts / attempt_id,
                status,
                outcome="pass",
                exit_code=0,
            )
            self.write_retired_marker(
                archive,
                status,
                attempt_id,
                attempt_sha256=attempt_sha256,
            )
            archive_objects = GATE._validate_recovery_archive(
                archive, status
            )
            records, passing = GATE._published_attempts(
                attempts,
                status,
                expected_sha256_by_id={
                    attempt_id: attempt_sha256
                },
            )
            assert passing is not None
            approval = GATE._publish_approval_from_passing(
                root,
                status,
                self.candidate_test_record(),
                records,
                passing,
            )
            os.link(approval.path, container / "approval-hardlink")
            with self.assertRaisesRegex(
                GATE.RootfixError, "link count"
            ):
                GATE._validate_approval(
                    root,
                    status,
                    self.candidate_test_record(),
                    archive_objects,
                )

    def test_external_attempt_digest_seal_rejects_coherent_drift(
        self,
    ) -> None:
        status = self.status()
        cases = (
            ("fail", 7, None),
            ("interrupted", 128 + signal.SIGTERM, signal.SIGTERM),
            ("pass", 0, None),
        )
        for index, (outcome, exit_code, interrupted_signal) in enumerate(
            cases, 1
        ):
            with (
                self.subTest(outcome=outcome),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                attempts = container / "attempts"
                attempts.mkdir()
                archive = self.recovery_archive(container, status)
                attempt_id = (
                    f"attempt-17000000000000006{index}0-"
                    f"8{index}0-{index:012x}"
                )
                attempt = attempts / attempt_id
                original_sha256 = self.write_attempt(
                    attempt,
                    status,
                    outcome=outcome,
                    exit_code=exit_code,
                    interrupted_signal=interrupted_signal,
                )
                self.write_retired_marker(
                    archive,
                    status,
                    attempt_id,
                    attempt_sha256=original_sha256,
                )
                log = attempt / "candidate-test.log"
                log.write_text("coherently changed after publication\n")
                inventory_path = attempt / "artifacts.json"
                inventory = json.loads(inventory_path.read_text())
                data = log.read_bytes()
                for record in inventory["artifacts"]:
                    if record["path"] == "candidate-test.log":
                        record["size"] = len(data)
                        record["sha256"] = hashlib.sha256(data).hexdigest()
                inventory_path.write_bytes(
                    GATE.rb.canonical_json_bytes(inventory)
                )
                self.assertNotEqual(
                    original_sha256, GATE._attempt_digest(attempt)
                )
                archive_objects = GATE._validate_recovery_archive(
                    archive, status
                )
                with self.assertRaisesRegex(
                    GATE.RootfixError, "digest mismatch"
                ):
                    GATE._published_attempts(
                        attempts,
                        status,
                        expected_sha256_by_id=(
                            GATE._sealed_attempt_digests(
                                archive_objects
                            )
                        ),
                    )

    def test_recovery_requires_just_archived_object_until_cleanup_boundary(
        self,
    ) -> None:
        status = self.status()
        for kind in ("marker", "atomic"):
            with (
                self.subTest(kind=kind),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                archive = self.recovery_archive(container, status)
                stage = None
                if kind == "marker":
                    operation = (
                        "attempt-1700000000000000700-970-"
                        "aaaaaaaaaaaa"
                    )
                    stage = attempts / f".staging-{operation}"
                    stage.mkdir()
                    marker = GATE._running_marker_payload(
                        status, operation, stage.name
                    )
                    marker["pid"] = 99999999
                    marker["proc_start"] = "dead"
                    (root / GATE.RUNNING_NAME).write_bytes(
                        GATE.rb.canonical_json_bytes(marker)
                    )
                else:
                    (
                        root
                        / ".tmp-approval.json-123-0123456789abcdef"
                    ).write_text("atomic residue")
                real_validate = GATE._validate_recovery_archive
                deleted = False

                def delete_required(
                    current_archive,
                    current_status,
                    required=(),
                ):
                    nonlocal deleted
                    if required and not deleted:
                        required[0].path.unlink()
                        deleted = True
                    return real_validate(
                        current_archive,
                        current_status,
                        required,
                    )

                with mock.patch.object(
                    GATE.rb,
                    "_running_marker_live",
                    return_value=False,
                ), mock.patch.object(
                    GATE,
                    "_validate_recovery_archive",
                    side_effect=delete_required,
                ):
                    with self.assertRaisesRegex(
                        GATE.RootfixError, "disappeared"
                    ):
                        GATE._recover_stale(
                            root,
                            attempts,
                            status,
                            recovery_archive=archive,
                        )
                self.assertTrue(deleted)
                if stage is not None:
                    self.assertFalse(stage.exists())
                    retained_staging = [
                        path
                        for path in archive.iterdir()
                        if path.name.startswith("retired-staging-")
                    ]
                    self.assertEqual(1, len(retained_staging))

    def test_attempts_directory_identity_is_bound_from_first_inventory(
        self,
    ) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            context = GATE._open_evidence_context(
                root,
                create_attempts=False,
                require_attempts=True,
            )
            try:
                inventory = GATE._validate_evidence_objects(
                    context, status
                )
                displaced = container / "displaced-attempts"
                attempts.rename(displaced)
                attempts.mkdir()
                with self.assertRaisesRegex(
                    GATE.RootfixError,
                    "attempts.*identity changed|identity changed",
                ):
                    GATE._require_no_stale_state(
                        context,
                        context.attempts,
                        status,
                        inventory,
                    )
            finally:
                context.close()

    def test_sigkill_recovery_refuses_live_recorded_child_group(
        self,
    ) -> None:
        if sys.platform != "darwin":
            self.skipTest("Darwin parent-death recovery boundary")
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(container, status)
            operation = (
                "attempt-1700000000000000800-980-bbbbbbbbbbbb"
            )
            stage = attempts / f".staging-{operation}"
            stage.mkdir()
            status_path = container / "status.json"
            status_path.write_text(json.dumps(status))
            ready = container / "child-ready"
            child = "\n".join(
                (
                    "import os",
                    "import sys",
                    "import time",
                    "from pathlib import Path",
                    "Path(sys.argv[1]).write_text(str(os.getpid()))",
                    "time.sleep(30)",
                )
            )
            helper = "\n".join(
                (
                    "import importlib.util",
                    "import json",
                    "import sys",
                    "from pathlib import Path",
                    "spec = importlib.util.spec_from_file_location('g', sys.argv[1])",
                    "g = importlib.util.module_from_spec(spec)",
                    "spec.loader.exec_module(g)",
                    "root = Path(sys.argv[2])",
                    "stage = Path(sys.argv[3])",
                    "status = json.loads(Path(sys.argv[4]).read_text())",
                    "sys.stdin.buffer.read(1)",
                    "g._run_process(",
                    "    [sys.executable, '-c', sys.argv[6], sys.argv[5]],",
                    "    root,",
                    "    stage / 'child.log',",
                    "    g.rb._trusted_child_environment(),",
                    "    stage=stage,",
                    "    status=status,",
                    "    attempt_id=sys.argv[7],",
                    "    phase='candidate_test',",
                    ")",
                )
            )
            process = subprocess.Popen(
                [
                    sys.executable,
                    "-c",
                    helper,
                    str(SCRIPT),
                    str(root),
                    str(stage),
                    str(status_path),
                    str(ready),
                    child,
                    operation,
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            record = None
            try:
                marker = GATE._running_marker_payload(
                    status, operation, stage.name
                )
                marker["pid"] = process.pid
                marker["proc_start"] = (
                    GATE.rb._proc_start_token(process.pid)
                    or "unavailable"
                )
                marker["boot_id"] = (
                    GATE.rb._boot_id() or "unavailable"
                )
                (root / GATE.RUNNING_NAME).write_bytes(
                    GATE.rb.canonical_json_bytes(marker)
                )
                assert process.stdin is not None
                process.stdin.write(b"R")
                process.stdin.close()
                deadline = time.monotonic() + 10
                record_path = (
                    stage
                    / GATE.PROCESS_RECORD_NAMES["candidate_test"]
                )
                while (
                    (not ready.exists() or not record_path.exists())
                    and process.poll() is None
                    and time.monotonic() < deadline
                ):
                    time.sleep(0.05)
                self.assertTrue(ready.exists())
                self.assertTrue(record_path.exists())
                record = json.loads(record_path.read_text())
                os.kill(process.pid, signal.SIGKILL)
                process.wait(timeout=10)
                self.assertTrue(GATE._process_record_live(record))
                with self.assertRaisesRegex(
                    GATE.StaleRootfixError,
                    "live rootfix candidate_test process group",
                ):
                    GATE._recover_stale(
                        root,
                        attempts,
                        status,
                        recovery_archive=archive,
                    )
                self.assertTrue(stage.exists())
                self.assertTrue((root / GATE.RUNNING_NAME).exists())
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                if record is not None:
                    try:
                        os.killpg(record["pgid"], signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                if process.stdout is not None:
                    process.stdout.close()
                if process.stderr is not None:
                    process.stderr.close()

    def test_run_parser_exposes_explicit_stale_recovery(self) -> None:
        args = GATE.parse_args(
            [
                "run",
                "--repo",
                ".",
                "--target-repo",
                ".",
                "--bundle",
                "bundle",
                "--recover-stale",
            ]
        )
        self.assertTrue(args.recover_stale)

    def test_read_only_evidence_lookup_does_not_create_namespace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            common = Path(tmp)
            with mock.patch.object(
                GATE.rb, "git_common_dir", return_value=common
            ):
                with self.assertRaises(GATE.RootfixError):
                    GATE._evidence_path(
                        Path("."), "a" * 64, create=False
                    )
                self.assertIsNone(
                    GATE._recovery_archive_path(
                        Path("."), "a" * 64, create=False
                    )
                )
            self.assertFalse((common / "zh-review-evidence").exists())

    def test_committed_candidate_blob_is_executed_and_evidence_bound(
        self,
    ) -> None:
        status = self.status()
        committed = b"raise SystemExit(7)\n"
        status["_rootfix_candidate_blob_sha256"] = hashlib.sha256(
            committed
        ).hexdigest()
        attempt_id = (
            "attempt-1700000000000000800-980-aaaaaaaaaaaa"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / f".staging-{attempt_id}"
            stage.mkdir()
            candidate = root / "candidate"
            candidate_test = candidate / GATE.TEST_PATH
            candidate_test.parent.mkdir(parents=True)
            candidate_test.write_text("raise SystemExit(0)\n")
            commands: dict[str, list[str]] = {}
            rc, metadata_path, interrupted = GATE._run_attempt(
                stage,
                candidate,
                status,
                committed,
                commands,
            )
            self.assertEqual(7, rc)
            self.assertIsNone(metadata_path)
            self.assertIsNone(interrupted)
            self.assertEqual(committed, (stage / "candidate-test.py").read_bytes())

            # Even a coherently re-inventoried replacement cannot become the
            # committed F input after execution.
            (stage / "candidate-test.py").write_text(
                "raise SystemExit(0)\n"
            )
            GATE._write_attempt_artifacts(stage, commands, None)
            (stage / "completion.json").write_bytes(
                GATE.rb.canonical_json_bytes(
                    GATE._completion("fail", 7)
                )
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "committed F blob"
            ):
                GATE._validate_attempt(
                    stage,
                    GATE._attempt_digest(stage),
                    status,
                )

    def test_code_profile_executes_trusted_verifier_blob(self) -> None:
        status = self.status()
        attempt_id = (
            "attempt-1700000000000000801-981-bbbbbbbbbbbb"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / f".staging-{attempt_id}"
            stage.mkdir()
            candidate = root / "candidate"
            verifier = candidate / GATE.VERIFIER_PATH
            verifier.parent.mkdir(parents=True)
            verifier.write_text("#!/bin/bash\nexit 0\n")
            candidate_test = candidate / GATE.TEST_PATH
            candidate_test.parent.mkdir(parents=True)
            candidate_test.write_text("raise SystemExit(99)\n")
            commands: dict[str, list[str]] = {}
            trusted = dict(GATE._TRUSTED_SOURCE_BLOBS)
            trusted[GATE.VERIFIER_PATH] = b"exit 7\n"
            with mock.patch.object(
                GATE, "_TRUSTED_SOURCE_BLOBS", trusted
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError,
                    "exactly one metadata",
                ):
                    GATE._run_attempt(
                        stage,
                        candidate,
                        status,
                        b"pass\n",
                        commands,
                    )
            self.assertEqual(
                GATE._expected_commands(status),
                commands,
            )
            self.assertTrue((stage / "profile-output").is_dir())
            self.assertTrue((stage / "code-profile.log").is_file())

    def test_passing_attempt_requires_exact_profile_and_raw_inventory(
        self,
    ) -> None:
        status = self.status()
        mutations = (
            "extra-profile-file",
            "extra-profile-directory",
            "missing-wrapper-log",
            "missing-candidate-input",
            "missing-candidate-log",
            "missing-profile-log",
        )
        for index, mutation in enumerate(mutations, 1):
            with (
                self.subTest(mutation=mutation),
                tempfile.TemporaryDirectory() as tmp,
            ):
                attempt_id = (
                    f"attempt-170000000000000081{index}-"
                    f"98{index}-{index:012x}"
                )
                attempt = Path(tmp) / attempt_id
                self.write_attempt(
                    attempt,
                    status,
                    outcome="pass",
                    exit_code=0,
                )
                if mutation == "extra-profile-file":
                    (
                        attempt / "profile-output" / "run" / "unknown"
                    ).write_text("unknown")
                elif mutation == "extra-profile-directory":
                    (
                        attempt
                        / "profile-output"
                        / "run"
                        / "unknown-empty"
                    ).mkdir()
                elif mutation == "missing-wrapper-log":
                    (
                        attempt / "profile-output" / "verify-code-run.log"
                    ).unlink()
                elif mutation == "missing-candidate-input":
                    (attempt / "candidate-test.py").unlink()
                elif mutation == "missing-candidate-log":
                    (attempt / "candidate-test.log").unlink()
                else:
                    (attempt / "code-profile.log").unlink()
                (attempt / "artifacts.json").unlink()
                GATE._write_attempt_artifacts(
                    attempt,
                    GATE._expected_commands(status),
                    "run/metadata.json",
                )
                with self.assertRaises(GATE.RootfixError):
                    GATE._validate_attempt(
                        attempt,
                        GATE._attempt_digest(attempt),
                        status,
                    )

    def test_staging_path_replacement_is_retained_and_rejected(
        self,
    ) -> None:
        status = self.status()
        attempt_id = (
            "attempt-1700000000000000820-990-cccccccccccc"
        )
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            attempts_path = container / "attempts"
            attempts_path.mkdir()
            archive = self.recovery_archive(container, status)
            stage_name = f".staging-{attempt_id}"
            stage_path = attempts_path / stage_name
            stage_path.mkdir()
            (stage_path / "original").write_text("original")
            attempts = GATE._open_directory_path(
                attempts_path, "test attempts"
            )
            stage = GATE._open_child_directory(
                attempts, stage_name, "test staging"
            )
            original_rename = GATE._atomic_rename_noreplace_at
            displaced = attempts_path / "displaced-original"

            def replace_before_rename(
                source_directory,
                source_name,
                target_directory,
                target_name,
            ):
                (source_directory.path / source_name).rename(displaced)
                replacement = source_directory.path / source_name
                replacement.mkdir()
                (replacement / "victim").write_text(
                    "must not be deleted"
                )
                return original_rename(
                    source_directory,
                    source_name,
                    target_directory,
                    target_name,
                )

            try:
                with mock.patch.object(
                    GATE,
                    "_atomic_rename_noreplace_at",
                    side_effect=replace_before_rename,
                ):
                    with self.assertRaises(GATE.RootfixError):
                        GATE._archive_validated_staging(
                            stage,
                            attempts,
                            archive,
                            status,
                            attempt_id,
                        )
            finally:
                stage.close()
                attempts.close()
            self.assertEqual(
                "original", (displaced / "original").read_text()
            )
            retired = list(archive.iterdir())
            self.assertEqual(1, len(retired))
            self.assertEqual(
                "must not be deleted",
                (retired[0] / "victim").read_text(),
            )

    def test_root_atomic_same_inode_content_drift_is_rejected(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "attempts").mkdir()
            residue = (
                root / ".tmp-running.json-123-0123456789abcdef"
            )
            residue.write_bytes(b"first")
            inventory = GATE._validate_evidence_objects(
                root, status, allow_atomic_temps=True
            )
            self.assertEqual(1, len(inventory.atomic_temps))
            original_inode = residue.stat().st_ino
            residue.write_bytes(b"other")
            self.assertEqual(original_inode, residue.stat().st_ino)
            with self.assertRaisesRegex(
                GATE.RootfixError, "changed after first inventory"
            ):
                GATE._open_validated_root_atomic(
                    residue, inventory.atomic_temps[0]
                )

    def test_atomic_write_failure_never_unlinks_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = GATE._open_directory_path(
                root, "test atomic directory"
            )
            observed: dict[str, Path] = {}

            def replace_and_fail(
                source_directory,
                source_name,
                _target_directory,
                _target_name,
            ):
                original = root / f"{source_name}.original"
                (root / source_name).rename(original)
                replacement = root / source_name
                replacement.write_text("replacement")
                observed["original"] = original
                observed["replacement"] = replacement
                raise OSError("forced publication failure")

            try:
                with mock.patch.object(
                    GATE,
                    "_atomic_rename_noreplace_at",
                    side_effect=replace_and_fail,
                ):
                    with self.assertRaises(OSError):
                        GATE._atomic_write_once_at(
                            directory,
                            "approval.json",
                            b"original",
                        )
            finally:
                directory.close()
            self.assertEqual(
                b"original", observed["original"].read_bytes()
            )
            self.assertEqual(
                "replacement", observed["replacement"].read_text()
            )

    def test_signal_during_process_record_write_is_durable_and_classified(
        self,
    ) -> None:
        status = self.status()
        attempt_id = (
            "attempt-1700000000000000830-991-dddddddddddd"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stage = root / f".staging-{attempt_id}"
            stage.mkdir()
            original_write = GATE._atomic_write_once_at
            signalled = False

            def signal_while_recording(directory, name, data):
                nonlocal signalled
                if (
                    name
                    == GATE.PROCESS_RECORD_NAMES["candidate_test"]
                    and not signalled
                ):
                    signalled = True
                    os.kill(os.getpid(), signal.SIGTERM)
                return original_write(directory, name, data)

            with mock.patch.object(
                GATE,
                "_atomic_write_once_at",
                side_effect=signal_while_recording,
            ):
                rc, interrupted = GATE._run_process(
                    [
                        sys.executable,
                        "-c",
                        "import time; time.sleep(30)",
                    ],
                    root,
                    stage / "child.log",
                    GATE.rb._trusted_child_environment(),
                    stage=stage,
                    status=status,
                    attempt_id=attempt_id,
                    phase="candidate_test",
                    evidence_command=GATE._expected_commands(status)[
                        "candidate_test"
                    ],
                )
            self.assertTrue(signalled)
            self.assertEqual(128 + signal.SIGTERM, rc)
            self.assertEqual(signal.SIGTERM, interrupted)
            records = GATE._load_stage_process_records(
                stage, status, attempt_id
            )
            self.assertEqual({"candidate_test"}, set(records))
            self.assertFalse(
                GATE._process_record_live(records["candidate_test"])
            )

    def test_signal_during_writer_snapshot_is_sealed_and_rethrown(
        self,
    ) -> None:
        status = self.status()
        attempt_id = (
            "attempt-1700000000000000953-1000-dddddddddddd"
        )
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            candidate = container / "candidate"
            candidate.mkdir()
            archive = self.recovery_archive(container, status)
            original_snapshot = GATE._snapshot_writer_stream
            signalled = False

            def signal_while_snapshotting(*args, **kwargs):
                nonlocal signalled
                if not signalled:
                    signalled = True
                    os.kill(os.getpid(), signal.SIGTERM)
                return original_snapshot(*args, **kwargs)

            with mock.patch.object(
                GATE, "_attempt_id", return_value=attempt_id
            ), mock.patch.object(
                GATE,
                "_snapshot_writer_stream",
                side_effect=signal_while_snapshotting,
            ):
                with self.assertRaises(
                    GATE.RootfixSignalInterrupt
                ) as raised:
                    GATE._execute_attempt(
                        root,
                        attempts,
                        candidate,
                        status,
                        b"pass\n",
                        lambda: archive,
                        lambda: self.fail(
                            "post validation must not run"
                        ),
                    )
            self.assertTrue(signalled)
            self.assertEqual(signal.SIGTERM, raised.exception.signum)
            self.assertFalse((root / GATE.RUNNING_NAME).exists())
            archive_objects = GATE._validate_recovery_archive(
                archive, status
            )
            records, passing = GATE._published_attempts(
                attempts,
                status,
                candidate,
                GATE._sealed_attempt_digests(archive_objects),
            )
            self.assertEqual(1, len(records))
            self.assertIsNone(passing)
            attempt = GATE._validate_attempt(
                attempts / attempt_id,
                records[0]["sha256"],
                status,
                candidate,
            )
            self.assertEqual("interrupted", attempt["outcome"])
            self.assertEqual(
                signal.SIGTERM, attempt["interrupted_signal"]
            )

    def test_post_wait_signal_is_deferred_through_snapshot_callback(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "child.log"
            seals: dict[str, GATE.FileSnapshot] = {}
            deferred: list[int] = []
            callback_calls: list[tuple[int, int | None]] = []

            def after_snapshot(
                return_code: int,
                interrupted_signal: int | None,
            ) -> None:
                callback_calls.append(
                    (return_code, interrupted_signal)
                )
                os.kill(os.getpid(), signal.SIGTERM)

            rc, interrupted = GATE._run_process(
                [sys.executable, "-c", "print('complete')"],
                root,
                output,
                GATE.rb._trusted_child_environment(),
                output_seals=seals,
                deferred_signals=deferred,
                after_snapshot=after_snapshot,
            )
            self.assertEqual(0, rc)
            self.assertIsNone(interrupted)
            self.assertEqual([(0, None)], callback_calls)
            self.assertEqual([signal.SIGTERM], deferred)
            self.assertEqual({"child.log"}, set(seals))
            self.assertEqual(b"complete\n", seals["child.log"].data)

    def test_profile_handoff_signals_preserve_exact_interrupt(
        self,
    ) -> None:
        status = self.status()
        for index, boundary in enumerate(("handoff", "post-validate"), 1):
            with (
                self.subTest(boundary=boundary),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                candidate = container / "candidate"
                candidate.mkdir()
                archive = self.recovery_archive(container, status)
                attempt_id = (
                    f"attempt-170000000000000095{4 + index}-"
                    f"{1001 + index}-{index:012x}"
                )

                def run_profile(*args, **kwargs):
                    result = self.complete_mock_attempt_run(
                        *args, **kwargs
                    )
                    if boundary == "handoff":
                        os.kill(os.getpid(), signal.SIGTERM)
                    return result

                def post_validate():
                    if boundary == "post-validate":
                        os.kill(os.getpid(), signal.SIGTERM)
                    else:
                        self.fail(
                            "handoff signal must precede post validation"
                        )

                with mock.patch.object(
                    GATE, "_attempt_id", return_value=attempt_id
                ), mock.patch.object(
                    GATE, "_run_attempt", side_effect=run_profile
                ):
                    with self.assertRaises(
                        GATE.RootfixSignalInterrupt
                    ) as raised:
                        GATE._execute_attempt(
                            root,
                            attempts,
                            candidate,
                            status,
                            b"pass\n",
                            (
                                (
                                    lambda: self.fail(
                                        "unterminated staging must not "
                                        "retire marker"
                                    )
                                )
                                if boundary == "handoff"
                                else (lambda: archive)
                            ),
                            post_validate,
                        )
                self.assertEqual(
                    signal.SIGTERM, raised.exception.signum
                )
                if boundary == "handoff":
                    self.assertTrue(
                        (root / GATE.RUNNING_NAME).is_file()
                    )
                    self.assertTrue(
                        (
                            attempts / f".staging-{attempt_id}"
                        ).is_dir()
                    )
                    self.assertFalse(
                        (attempts / attempt_id).exists()
                    )
                else:
                    self.assertFalse(
                        (root / GATE.RUNNING_NAME).exists()
                    )
                    records, passing = GATE._published_attempts(
                        attempts,
                        status,
                        candidate,
                        GATE._sealed_attempt_digests(
                            GATE._validate_recovery_archive(
                                archive, status
                            )
                        ),
                    )
                    self.assertEqual(1, len(records))
                    self.assertIsNotNone(passing)
                    self.assertEqual("pass", passing["outcome"])

    def test_established_profile_terminal_survives_signal_and_seal_error(
        self,
    ) -> None:
        status = self.status()
        for index, seal_error in enumerate((False, True), 1):
            with (
                self.subTest(seal_error=seal_error),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                candidate = container / "candidate"
                candidate.mkdir()
                archive = self.recovery_archive(container, status)
                attempt_id = (
                    f"attempt-170000000000000096{index}-"
                    f"{1010 + index}-{index:012x}"
                )

                def established_run(*args, **kwargs):
                    self.complete_mock_attempt_run(*args, **kwargs)
                    raise GATE.RootfixEstablishedTerminalInterrupt(
                        signal.SIGTERM,
                        ("pass", 0, "run/metadata.json", None),
                    )

                seal_patch = (
                    mock.patch.object(
                        GATE,
                        "_seal_stage",
                        side_effect=GATE.RootfixError(
                            "injected seal failure"
                        ),
                    )
                    if seal_error
                    else contextlib.nullcontext()
                )
                with mock.patch.object(
                    GATE, "_attempt_id", return_value=attempt_id
                ), mock.patch.object(
                    GATE, "_run_attempt", side_effect=established_run
                ), seal_patch:
                    with self.assertRaises(
                        GATE.RootfixSignalInterrupt
                    ) as raised:
                        GATE._execute_attempt(
                            root,
                            attempts,
                            candidate,
                            status,
                            b"pass\n",
                            (
                                (
                                    lambda: self.fail(
                                        "failed seal must not retire marker"
                                    )
                                )
                                if seal_error
                                else (lambda: archive)
                            ),
                            lambda: self.fail(
                                "established interrupt must bypass "
                                "post validation"
                            ),
                        )
                self.assertEqual(
                    signal.SIGTERM, raised.exception.signum
                )
                if seal_error:
                    self.assertTrue(
                        (root / GATE.RUNNING_NAME).is_file()
                    )
                    self.assertTrue(
                        (
                            attempts / f".staging-{attempt_id}"
                        ).is_dir()
                    )
                    self.assertFalse(
                        (attempts / attempt_id).exists()
                    )
                else:
                    self.assertFalse(
                        (root / GATE.RUNNING_NAME).exists()
                    )
                    records, passing = GATE._published_attempts(
                        attempts,
                        status,
                        candidate,
                        GATE._sealed_attempt_digests(
                            GATE._validate_recovery_archive(
                                archive, status
                            )
                        ),
                    )
                    self.assertEqual(1, len(records))
                    self.assertIsNotNone(passing)
                    self.assertEqual("pass", passing["outcome"])

    def test_profile_post_validation_failure_retains_staging(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            candidate = container / "candidate"
            candidate.mkdir()
            attempt_id = (
                "attempt-1700000000000000963-1013-cccccccccccc"
            )
            with mock.patch.object(
                GATE, "_attempt_id", return_value=attempt_id
            ), mock.patch.object(
                GATE,
                "_run_attempt",
                side_effect=self.complete_mock_attempt_run,
            ), self.assertRaisesRegex(
                GATE.RootfixError, "post-validation drift"
            ):
                GATE._execute_attempt(
                    root,
                    attempts,
                    candidate,
                    status,
                    b"pass\n",
                    lambda: self.fail(
                        "unvalidated staging must not retire marker"
                    ),
                    lambda: (_ for _ in ()).throw(
                        GATE.RootfixError("post-validation drift")
                    ),
                )
            self.assertTrue((root / GATE.RUNNING_NAME).is_file())
            self.assertTrue(
                (attempts / f".staging-{attempt_id}").is_dir()
            )
            self.assertFalse((attempts / attempt_id).exists())

    def test_post_publish_errors_cannot_replace_returned_interrupt(
        self,
    ) -> None:
        status = self.status()
        for index, validation_error in enumerate((False, True), 1):
            with (
                self.subTest(validation_error=validation_error),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                candidate = container / "candidate"
                candidate.mkdir()
                archive = self.recovery_archive(container, status)
                attempt_id = (
                    f"attempt-170000000000000096{6 + index}-"
                    f"{1016 + index}-{index:012x}"
                )

                def interrupted_run(*args, **kwargs):
                    result = self.complete_mock_attempt_run(
                        *args, **kwargs
                    )
                    stage_arg = args[0]
                    candidate_arg = args[1]
                    status_arg = args[2]
                    seals_arg = args[5]
                    stage_path = (
                        stage_arg.path
                        if isinstance(stage_arg, GATE.DirectoryHandle)
                        else Path(stage_arg)
                    )
                    run = stage_path / "profile-output" / "run"
                    metadata = self.write_profile_metadata(
                        run,
                        status_arg,
                        worktree=candidate_arg,
                        profile_status="interrupted",
                    )
                    log = stage_path / "code-profile.log"
                    log.write_bytes(
                        self.profile_process_log(run, metadata)
                    )
                    seals_arg["code-profile.log"] = (
                        GATE._read_regular_snapshot(
                            log, "test interrupted raw log"
                        )
                    )
                    return (
                        128 + signal.SIGTERM,
                        result[1],
                        signal.SIGTERM,
                    )

                original_seal = GATE._seal_stage

                def publish_then_fail(*args, **kwargs):
                    original_seal(*args, **kwargs)
                    raise GATE.RootfixError(
                        "injected post-publish failure"
                    )

                original_validate = GATE._validate_attempt
                validate_calls = 0

                def validate_after_publish(*args, **kwargs):
                    nonlocal validate_calls
                    validate_calls += 1
                    if validation_error and validate_calls == 2:
                        raise GATE.RootfixError(
                            "injected published validation failure"
                        )
                    return original_validate(*args, **kwargs)

                with mock.patch.object(
                    GATE, "_attempt_id", return_value=attempt_id
                ), mock.patch.object(
                    GATE, "_run_attempt", side_effect=interrupted_run
                ), mock.patch.object(
                    GATE, "_seal_stage", side_effect=publish_then_fail
                ), mock.patch.object(
                    GATE,
                    "_validate_attempt",
                    side_effect=validate_after_publish,
                ):
                    with self.assertRaises(
                        GATE.RootfixSignalInterrupt
                    ) as raised:
                        GATE._execute_attempt(
                            root,
                            attempts,
                            candidate,
                            status,
                            b"pass\n",
                            (
                                (lambda: archive)
                                if not validation_error
                                else (
                                    lambda: self.fail(
                                        "unvalidated publication must "
                                        "retain marker"
                                    )
                                )
                            ),
                            lambda: self.fail(
                                "interrupted terminal must bypass "
                                "post validation"
                            ),
                        )
                self.assertEqual(
                    signal.SIGTERM, raised.exception.signum
                )
                self.assertTrue((attempts / attempt_id).is_dir())
                if validation_error:
                    self.assertTrue(
                        (root / GATE.RUNNING_NAME).is_file()
                    )
                else:
                    self.assertFalse(
                        (root / GATE.RUNNING_NAME).exists()
                    )

    def test_signal_mask_restore_cannot_replace_primary_interrupt(
        self,
    ) -> None:
        status = self.status()
        for index, boundary in enumerate(
            ("exception-handoff", "returned-interrupted"), 1
        ):
            with (
                self.subTest(boundary=boundary),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                candidate = container / "candidate"
                candidate.mkdir()
                archive = self.recovery_archive(container, status)
                attempt_id = (
                    f"attempt-170000000000000096{3 + index}-"
                    f"{1013 + index}-{index:012x}"
                )

                def established_run(*args, **kwargs):
                    result = self.complete_mock_attempt_run(
                        *args, **kwargs
                    )
                    if boundary == "exception-handoff":
                        raise GATE.RootfixEstablishedTerminalInterrupt(
                            signal.SIGTERM,
                            ("pass", 0, "run/metadata.json", None),
                        )
                    stage_arg = args[0]
                    candidate_arg = args[1]
                    status_arg = args[2]
                    seals_arg = args[5]
                    stage_path = (
                        stage_arg.path
                        if isinstance(stage_arg, GATE.DirectoryHandle)
                        else Path(stage_arg)
                    )
                    run = stage_path / "profile-output" / "run"
                    metadata = self.write_profile_metadata(
                        run,
                        status_arg,
                        worktree=candidate_arg,
                        profile_status="interrupted",
                    )
                    log = stage_path / "code-profile.log"
                    log.write_bytes(
                        self.profile_process_log(run, metadata)
                    )
                    seals_arg["code-profile.log"] = (
                        GATE._read_regular_snapshot(
                            log, "test interrupted raw log"
                        )
                    )
                    return (
                        128 + signal.SIGTERM,
                        result[1],
                        signal.SIGTERM,
                    )

                mask_calls: list[int] = []

                def mask_with_secondary(signals_how, _signals):
                    mask_calls.append(signals_how)
                    if signals_how == signal.SIG_SETMASK:
                        raise GATE.RootfixSignalInterrupt(
                            signal.SIGHUP
                        )
                    return set()

                with mock.patch.object(
                    GATE, "_attempt_id", return_value=attempt_id
                ), mock.patch.object(
                    GATE, "_run_attempt", side_effect=established_run
                ), mock.patch.object(
                    signal,
                    "pthread_sigmask",
                    side_effect=mask_with_secondary,
                ):
                    with self.assertRaises(
                        GATE.RootfixSignalInterrupt
                    ) as raised:
                        GATE._execute_attempt(
                            root,
                            attempts,
                            candidate,
                            status,
                            b"pass\n",
                            lambda: archive,
                            lambda: self.fail(
                                "interrupt must bypass post validation"
                            ),
                        )
                self.assertEqual(
                    signal.SIGTERM, raised.exception.signum
                )
                self.assertEqual(
                    [signal.SIG_BLOCK, signal.SIG_SETMASK],
                    mask_calls,
                )
                self.assertFalse(
                    (root / GATE.RUNNING_NAME).exists()
                )
                records, passing = GATE._published_attempts(
                    attempts,
                    status,
                    candidate,
                    GATE._sealed_attempt_digests(
                        GATE._validate_recovery_archive(
                            archive, status
                        )
                    ),
                )
                self.assertEqual(1, len(records))
                if boundary == "exception-handoff":
                    self.assertIsNotNone(passing)
                    self.assertEqual("pass", passing["outcome"])
                else:
                    self.assertIsNone(passing)
                    attempt = GATE._validate_attempt(
                        attempts / attempt_id,
                        records[0]["sha256"],
                        status,
                        candidate,
                    )
                    self.assertEqual(
                        "interrupted", attempt["outcome"]
                    )
                    self.assertEqual(
                        signal.SIGTERM,
                        attempt["interrupted_signal"],
                    )

    def test_repository_modules_and_contract_load_from_exact_git_blobs(
        self,
    ) -> None:
        helper = "\n".join(
            (
                "import importlib.util",
                "import json",
                "import sys",
                "from pathlib import Path",
                "spec = importlib.util.spec_from_file_location(",
                "    'gate_probe', Path(sys.argv[1]))",
                "gate = importlib.util.module_from_spec(spec)",
                "spec.loader.exec_module(gate)",
                "gate._load_trusted_repository_modules(Path(sys.argv[2]))",
                "print(json.dumps({",
                "    'bundle': gate.rb.VALUE,",
                "    'shared': gate.rb.SHARED,",
                "    'verifier': gate._TRUSTED_SOURCE_BLOBS[gate.VERIFIER_PATH].decode(),",
                "    'contract': gate._TRUSTED_SOURCE_BLOBS[gate.PROFILE_CONTRACT_PATH].decode(),",
                "}))",
            )
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            scripts = repo / ".claude" / "scripts"
            contract = scripts / "data" / (
                "review_verification_contract_v5.json"
            )
            contract.parent.mkdir(parents=True)
            (scripts / "i18n_shared.py").write_text(
                "VALUE = 'trusted-shared'\n"
            )
            (scripts / "review_bundle.py").write_text(
                "import i18n_shared\n"
                "VALUE = 'trusted-bundle'\n"
                "SHARED = i18n_shared.VALUE\n"
            )
            (scripts / "verify_zh.sh").write_text("trusted-verifier\n")
            contract.write_text("trusted-contract\n")
            subprocess.run(
                ["git", "init", "-q", os.fspath(repo)],
                check=True,
            )
            subprocess.run(
                ["git", "-C", os.fspath(repo), "add", "."],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    os.fspath(repo),
                    "-c",
                    "user.name=Rootfix Test",
                    "-c",
                    "user.email=rootfix@example.invalid",
                    "commit",
                    "-qm",
                    "trusted",
                ],
                check=True,
            )
            (scripts / "i18n_shared.py").write_text(
                "VALUE = 'poisoned-shared'\n"
            )
            (scripts / "review_bundle.py").write_text(
                "VALUE = 'poisoned-bundle'\nSHARED = 'poisoned'\n"
            )
            (scripts / "verify_zh.sh").write_text("poisoned-verifier\n")
            contract.write_text("poisoned-contract\n")
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    helper,
                    os.fspath(SCRIPT),
                    os.fspath(repo),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual("trusted-bundle", payload["bundle"])
            self.assertEqual("trusted-shared", payload["shared"])
            self.assertEqual("trusted-verifier\n", payload["verifier"])
            self.assertEqual("trusted-contract\n", payload["contract"])

    def test_seal_rejects_every_established_terminal_substitution(
        self,
    ) -> None:
        status = self.status()
        established = {
            "outcome": "pass",
            "exit_code": 0,
            "signal": None,
            "commands": GATE._expected_commands(status),
            "metadata": "run/metadata.json",
        }
        mutations = (
            ("outcome", "fail"),
            ("exit_code", 7),
            ("signal", signal.SIGTERM),
            (
                "commands",
                {
                    "candidate_test": GATE._expected_commands(status)[
                        "candidate_test"
                    ]
                },
            ),
            ("metadata", "other/metadata.json"),
        )
        for index, (field, value) in enumerate(mutations, 1):
            with (
                self.subTest(field=field),
                tempfile.TemporaryDirectory() as tmp,
            ):
                attempt_id = (
                    f"attempt-170000000000000084{index}-"
                    f"99{index}-{index:012x}"
                )
                attempts = Path(tmp) / "attempts"
                attempts.mkdir()
                stage = attempts / f".staging-{attempt_id}"
                fixture = attempts / attempt_id
                self.write_attempt(
                    fixture,
                    status,
                    outcome="pass",
                    exit_code=0,
                )
                fixture.rename(stage)
                terminal = dict(established)
                terminal[field] = value
                with self.assertRaisesRegex(
                    GATE.RootfixError, "established terminal"
                ):
                    GATE._seal_stage(
                        stage,
                        attempts,
                        attempt_id,
                        status,
                        terminal["commands"],
                        terminal["metadata"],
                        terminal["outcome"],
                        terminal["exit_code"],
                        terminal["signal"],
                    )
                self.assertTrue(stage.is_dir())
                self.assertFalse((attempts / attempt_id).exists())

    def test_exception_retry_audits_history_before_rethrow(self) -> None:
        status = self.status()
        candidate_test = self.candidate_test_record()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            candidate = container / "candidate"
            target = container / "target"
            candidate.mkdir()
            target.mkdir()
            root = container / "rootfix"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(container, status)
            old_id = "attempt-1700000000000000900-990-aaaaaaaaaaaa"
            old = attempts / old_id
            old_sha256 = self.write_attempt(
                old,
                status,
                outcome="fail",
                exit_code=7,
                worktree=candidate,
            )
            old_marker = self.write_retired_marker(
                archive,
                status,
                old_id,
                attempt_sha256=old_sha256,
            )
            bundle_path = container / "bundle"
            bundle_path.mkdir()

            def delete_history_then_interrupt(*_arguments):
                shutil.rmtree(old)
                old_marker.unlink()
                raise KeyboardInterrupt

            with mock.patch.object(
                GATE.rb, "_resolve_bundle_path", return_value=bundle_path
            ), mock.patch.object(
                GATE.rb,
                "bundle_lock",
                return_value=contextlib.nullcontext(),
            ), mock.patch.object(
                GATE.rb, "_validate_bundle_locked", return_value=status
            ), mock.patch.object(
                GATE,
                "_validate_topology",
                return_value=(
                    target,
                    candidate,
                    candidate_test,
                    b"pass\n",
                ),
            ), mock.patch.object(
                GATE, "_evidence_path", return_value=root
            ), mock.patch.object(
                GATE, "_recovery_archive_path", return_value=archive
            ), mock.patch.object(
                GATE,
                "_execute_attempt",
                side_effect=delete_history_then_interrupt,
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError,
                    "pre-existing rootfix attempt history",
                ):
                    GATE.run_gate(
                        candidate,
                        target,
                        status["bundle_id"],
                        retry_failed=True,
                    )

    def test_gate_boundary_signals_retire_published_attempt(self) -> None:
        status = self.status()
        for index, boundary in enumerate(("seal", "retire"), 1):
            with (
                self.subTest(boundary=boundary),
                tempfile.TemporaryDirectory() as tmp,
            ):
                container = Path(tmp)
                root = container / "root"
                attempts = root / "attempts"
                attempts.mkdir(parents=True)
                candidate = container / "candidate"
                candidate.mkdir()
                archive = self.recovery_archive(container, status)
                attempt_id = (
                    f"attempt-170000000000000091{index}-"
                    f"99{index}-{index:012x}"
                )
                target_name = (
                    "_seal_stage"
                    if boundary == "seal"
                    else "_archive_validated_running_marker"
                )
                original = getattr(GATE, target_name)
                sent = False

                def signal_once(*args, **kwargs):
                    nonlocal sent
                    if not sent:
                        sent = True
                        os.kill(os.getpid(), signal.SIGTERM)
                    return original(*args, **kwargs)

                with mock.patch.object(
                    GATE, "_attempt_id", return_value=attempt_id
                ), mock.patch.object(
                    GATE,
                    "_run_attempt",
                    side_effect=self.complete_mock_attempt_run,
                ), mock.patch.object(
                    GATE, target_name, side_effect=signal_once
                ):
                    with self.assertRaises(
                        GATE.RootfixSignalInterrupt
                    ) as raised:
                        GATE._execute_attempt(
                            root,
                            attempts,
                            candidate,
                            status,
                            b"pass\n",
                            lambda: archive,
                            lambda: None,
                        )
                self.assertEqual(signal.SIGTERM, raised.exception.signum)
                self.assertTrue(sent)
                self.assertFalse((root / GATE.RUNNING_NAME).exists())
                self.assertEqual([], list(attempts.glob(".staging-*")))
                archive_objects = GATE._validate_recovery_archive(
                    archive, status
                )
                records, passing = GATE._published_attempts(
                    attempts,
                    status,
                    candidate,
                    GATE._sealed_attempt_digests(archive_objects),
                )
                self.assertEqual(1, len(records))
                self.assertIsNotNone(passing)

    def test_json_integer_fields_reject_boolean_aliases(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            failed = (
                container
                / "attempt-1700000000000000920-992-aaaaaaaaaaaa"
            )
            self.write_attempt(
                failed,
                status,
                outcome="fail",
                exit_code=7,
            )
            log = failed / "candidate-test.log"
            log.write_bytes(b"X")
            inventory_path = failed / "artifacts.json"
            inventory = json.loads(inventory_path.read_text())
            for record in inventory["artifacts"]:
                if record["path"] == "candidate-test.log":
                    record["size"] = True
                    record["sha256"] = hashlib.sha256(b"X").hexdigest()
            inventory_path.write_bytes(
                GATE.rb.canonical_json_bytes(inventory)
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "artifact inventory mismatch"
            ):
                GATE._validate_attempt(failed, None, status)

        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            root = container / "root"
            attempts = root / "attempts"
            attempts.mkdir(parents=True)
            archive = self.recovery_archive(container, status)
            attempt_id = (
                "attempt-1700000000000000921-993-bbbbbbbbbbbb"
            )
            attempt_sha256 = self.write_attempt(
                attempts / attempt_id,
                status,
                outcome="pass",
                exit_code=0,
            )
            self.write_retired_marker(
                archive,
                status,
                attempt_id,
                attempt_sha256=attempt_sha256,
            )
            archive_objects = GATE._validate_recovery_archive(
                archive, status
            )
            records, passing = GATE._published_attempts(
                attempts,
                status,
                expected_sha256_by_id=(
                    GATE._sealed_attempt_digests(archive_objects)
                ),
            )
            assert passing is not None
            approval = GATE._publish_approval_from_passing(
                root,
                status,
                self.candidate_test_record(),
                records,
                passing,
            )
            payload = json.loads(approval.data)
            payload["candidate_test"]["replacement_count"] = True
            approval.path.unlink()
            approval.path.write_bytes(
                GATE.rb.canonical_json_bytes(payload)
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "identity binding"
            ):
                GATE._validate_approval(
                    root,
                    status,
                    self.candidate_test_record(),
                    archive_objects,
                )

    def test_failed_profile_inventory_is_exact_or_unpublished(self) -> None:
        status = self.status()
        with tempfile.TemporaryDirectory() as tmp:
            container = Path(tmp)
            attempt_id = (
                "attempt-1700000000000000930-994-aaaaaaaaaaaa"
            )
            attempt = container / attempt_id
            attempt.mkdir()
            commands = GATE._expected_commands(status)
            (attempt / "candidate-test.py").write_bytes(b"pass\n")
            (attempt / "candidate-test.log").write_text("PASS\n")
            for phase, command in commands.items():
                self.write_process_record(
                    attempt, status, attempt_id, phase, command
                )
            run = attempt / "profile-output" / "run"
            wrapper_run = (
                attempt.parent
                / f".staging-{attempt.name}"
                / "profile-output"
                / "run"
            )
            metadata = self.write_profile_metadata(
                run,
                status,
                profile_status="fail",
                wrapper_run=wrapper_run,
            )
            (attempt / "code-profile.log").write_bytes(
                self.profile_process_log(
                    run,
                    metadata,
                    wrapper_run=wrapper_run,
                )
            )
            GATE._write_attempt_artifacts(
                attempt, commands, "run/metadata.json"
            )
            (attempt / "completion.json").write_bytes(
                GATE.rb.canonical_json_bytes(
                    GATE._completion("fail", 1)
                )
            )
            GATE._validate_attempt(attempt, None, status)

            (attempt / "profile-output" / "unknown-empty").mkdir()
            (attempt / "artifacts.json").unlink()
            GATE._write_attempt_artifacts(
                attempt, commands, "run/metadata.json"
            )
            with self.assertRaisesRegex(
                GATE.RootfixError,
                "profile directory inventory is not exact",
            ):
                GATE._validate_attempt(attempt, None, status)

        with tempfile.TemporaryDirectory() as tmp:
            attempt_id = (
                "attempt-1700000000000000931-995-bbbbbbbbbbbb"
            )
            attempt = Path(tmp) / attempt_id
            attempt.mkdir()
            commands = GATE._expected_commands(status)
            (attempt / "candidate-test.py").write_bytes(b"pass\n")
            (attempt / "candidate-test.log").write_text("PASS\n")
            (attempt / "code-profile.log").write_text("FAIL\n")
            for phase, command in commands.items():
                self.write_process_record(
                    attempt, status, attempt_id, phase, command
                )
            GATE._write_attempt_artifacts(attempt, commands, None)
            (attempt / "completion.json").write_bytes(
                GATE.rb.canonical_json_bytes(
                    GATE._completion("fail", 1)
                )
            )
            with self.assertRaisesRegex(
                GATE.RootfixError, "profile metadata path is missing"
            ):
                GATE._validate_attempt(attempt, None, status)

    def test_raw_log_writer_fd_rejects_path_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "raw.log"
            displaced = root / "writer.log"
            mutation_error: list[BaseException] = []

            def replace_output() -> None:
                try:
                    deadline = time.monotonic() + 5
                    while time.monotonic() < deadline:
                        if output.exists() and b"ORIGINAL" in output.read_bytes():
                            break
                        time.sleep(0.01)
                    else:
                        raise AssertionError("writer output was not observed")
                    os.replace(output, displaced)
                    output.write_bytes(b"FORGED\n")
                except BaseException as error:
                    mutation_error.append(error)

            attacker = threading.Thread(target=replace_output)
            attacker.start()
            seals: dict[str, GATE.FileSnapshot] = {}
            with self.assertRaisesRegex(
                GATE.RootfixError,
                "writer descriptor no longer names",
            ):
                GATE._run_process(
                    [
                        sys.executable,
                        "-c",
                        (
                            "import time\n"
                            "print('ORIGINAL', flush=True)\n"
                            "time.sleep(0.25)\n"
                            "print('TAIL', flush=True)\n"
                        ),
                    ],
                    root,
                    output,
                    GATE.rb._trusted_child_environment(),
                    output_seals=seals,
                )
            attacker.join(timeout=5)
            self.assertFalse(attacker.is_alive())
            self.assertEqual([], mutation_error)
            self.assertEqual({}, seals)
            self.assertEqual(b"FORGED\n", output.read_bytes())
            self.assertIn(b"ORIGINAL", displaced.read_bytes())

    def test_single_read_rejects_same_inode_same_size_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "large.bin"
            path.write_bytes(b"A" * (2 * 1024 * 1024))
            real_read = GATE.os.read
            mutated = False

            def mutate_after_first_chunk(fd, size):
                nonlocal mutated
                data = real_read(fd, size)
                if data and not mutated:
                    mutated = True
                    time.sleep(0.002)
                    with path.open("r+b", buffering=0) as stream:
                        stream.write(b"B" * (2 * 1024 * 1024))
                        os.fsync(stream.fileno())
                return data

            with mock.patch.object(
                GATE.os, "read", side_effect=mutate_after_first_chunk
            ):
                with self.assertRaisesRegex(
                    GATE.RootfixError, "changed while reading"
                ):
                    GATE._read_regular_snapshot(
                        path, "same-inode mutation"
                    )
            self.assertTrue(mutated)
            self.assertEqual(
                b"B" * (2 * 1024 * 1024), path.read_bytes()
            )

    def test_required_recovery_archive_cannot_disappear(self) -> None:
        status = self.status()
        seal = GATE.ArchiveSeal(
            Path("/private/tmp/missing-rootfix-archive/object"),
            1,
            2,
            3,
            "a" * 64,
            "running",
        )
        with self.assertRaisesRegex(
            GATE.RootfixError, "recovery archive disappeared"
        ):
            GATE._validate_recovery_archive(None, status, [seal])
        self.assertEqual(
            [], GATE._validate_recovery_archive(None, status)
        )

    def test_policy_text_keeps_p_and_f_no_go_and_records_c2_state(self) -> None:
        policy = (
            SCRIPT.parents[2] / ".agents/policies/review-contract.md"
        ).read_text(encoding="utf-8")
        for fragment in (
            "P^ == 8aae77c60a5e537e76c7b252c6a311fade4264c2",
            "F^ == <approved-full-P-OID>",
            "P is not Go",
            "F remains No-Go",
            "did not publish a formal attempt",
            "C2 readiness, bundle objects, logs and any",
            "The sole candidate-sourced control input",
            "ROOTFIX_MERGEABLE",
            "same physical Git common directory",
            "single-read file descriptors",
            "read the exact P blobs",
            "`i18n_shared.py`",
            "executes the retained",
            "Ignored checkout `__pycache__` objects",
            "every relative directory and regular file",
            "bundle-bound `running.json`",
            "`--recover-stale`",
            "exact atomic temporary fails as stale",
            "never unlinks the atomic residue",
            "`zh-review-evidence/rootfix-recovered-v1/<bundle-id>/`",
            "content-digest validation",
            "`check` does not create an absent",
            "owner-governed forensic retention",
            "regular-file or symlink replacement",
            "also never unlinks `running.json`",
            "generated retired-marker name binds",
            "positive-integer PID",
            "Every published attempt must map to exactly one",
            "pre-execution inventory",
            "freezes the evidence-root, attempts-directory",
            "cannot consume either staging object",
            "same-inode, same-size",
            "mtime and ctime",
            "absent bundle archive",
            "canonical-byte comparison",
            "terminal metadata run",
            "writer descriptors",
            "both when it returns and when it throws",
            "critical section temporarily masks",
            "never performs a check-then-unlink cleanup",
            "complete directory-and-file tree digest",
            "absence observed at startup",
            "never cached across a long-running verification",
            "cleanup-safe `SIGINT`",
            "whole focused-child or full-profile process group",
            "initiating signal",
            "resumes that same",
            "operation-ID grammar",
            "grammar. With a marker",
            "accepts at most one valid staging residue",
            "next `run` deterministically",
            "same approval from that sealed attempt",
            "separate supervised process group",
            "PGID, process-start token and boot identity",
            "exact published-attempt SHA-256",
            "has no durable external digest authority",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, policy)
        self.assertNotIn(
            "replace the impossible normal\nverification-v5 final approval",
            policy,
        )

    def test_main_fails_closed_with_canonical_no_go(self) -> None:
        output = mock.Mock()
        output.buffer = io.BytesIO()
        with mock.patch.object(
            GATE, "_load_trusted_repository_modules"
        ) as load, mock.patch.object(
            GATE, "check_gate", side_effect=GATE.RootfixError("rejected")
        ), mock.patch.object(GATE.sys, "stdout", output):
            rc = GATE.main([
                "check",
                "--repo", ".",
                "--target-repo", ".",
                "--bundle", "x",
            ])
        load.assert_called_once_with(GATE.SCRIPT_DIR.parents[1])
        self.assertEqual(2, rc)
        payload = json.loads(output.buffer.getvalue())
        self.assertEqual("ROOTFIX_NO_GO", payload["state"])
        self.assertFalse(payload["approved"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
