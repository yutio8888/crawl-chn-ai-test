#!/usr/bin/env python3
"""Black-box checks for the read-only schema-v4 merge gate."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


sys.dont_write_bytecode = True
SOURCE_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_NAMES = (
    "review_at_merge.sh",
    "review_bundle.py",
    "review_prepare.sh",
    "classify_reviewers.py",
)
SPEC = importlib.util.spec_from_file_location(
    "review_bundle_contract_test", SOURCE_ROOT / ".claude/scripts/review_bundle.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ReviewAtMergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.repo = Path(self.temporary.name) / "repo"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.email", "merge-gate@example.invalid")
        self.git("config", "user.name", "Merge Gate Test")
        scripts = self.repo / ".claude/scripts"
        scripts.mkdir(parents=True)
        for name in SCRIPT_NAMES:
            shutil.copy2(SOURCE_ROOT / ".claude/scripts" / name, scripts / name)
        glossary = self.repo / "docs/glossary.md"
        glossary.parent.mkdir(parents=True)
        glossary.write_text("# test glossary\n", encoding="utf-8")
        (self.repo / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
        (self.repo / "base.txt").write_text("base\n", encoding="utf-8")
        self.git("add", ".")
        self.git("commit", "-qm", "base")
        self.git("branch", "-m", "target")
        self.git("branch", "candidate")
        self.git("worktree", "add", "-q", ".worktrees/candidate", "candidate")
        self.candidate = self.repo / ".worktrees/candidate"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str, cwd: Path | None = None) -> str:
        return subprocess.check_output(
            ["git", *args], cwd=cwd or self.repo, text=True
        ).strip()

    def commit_candidate(self, relative: str, text: str) -> str:
        path = self.candidate / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        self.git("add", relative, cwd=self.candidate)
        self.git("commit", "-qm", "candidate change", cwd=self.candidate)
        return self.git("rev-parse", "HEAD", cwd=self.candidate)

    def run_gate(self, **extra_environment: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.update(extra_environment)
        return subprocess.run(
            ["/bin/bash", ".claude/scripts/review_at_merge.sh", "candidate", "target"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def run_prepare(self, **extra_environment: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env.update(extra_environment)
        return subprocess.run(
            ["/bin/bash", ".claude/scripts/review_prepare.sh", "candidate", "target"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    @staticmethod
    def evidence_snapshot(path: Path) -> dict[str, tuple[str, bytes]]:
        result: dict[str, tuple[str, bytes]] = {}
        for item in sorted(path.rglob("*")):
            relative = item.relative_to(path).as_posix()
            if item.is_symlink():
                result[relative] = ("symlink", os.readlink(item).encode())
            elif item.is_dir():
                result[relative] = ("directory", b"")
            else:
                result[relative] = ("file", item.read_bytes())
        return result

    def test_unrouted_change_still_requires_final_evidence(self) -> None:
        self.commit_candidate("notes/review-note.txt", "documentation only\n")
        evidence = self.repo / ".git/zh-review-evidence"
        self.assertFalse(evidence.exists())
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 11, proc.stdout + proc.stderr)
        self.assertIn('"state":"FINAL_GATE_REQUIRED"', proc.stdout)
        self.assertFalse(evidence.exists(), "read-only gate created evidence")

    def test_routed_change_without_bundle_requires_final_gate_read_only(self) -> None:
        self.commit_candidate("crawl-ref/source/review-test.cc", "// test\n")
        evidence = self.repo / ".git/zh-review-evidence"
        proc = self.run_gate()
        self.assertEqual(proc.returncode, 11, proc.stdout + proc.stderr)
        self.assertIn('"state":"FINAL_GATE_REQUIRED"', proc.stdout)
        self.assertFalse(evidence.exists(), "missing-bundle status created evidence")

    def test_existing_evidence_is_byte_for_byte_unchanged(self) -> None:
        self.commit_candidate("crawl-ref/source/review-test.cc", "// test\n")
        glossary_sha256 = hashlib.sha256(
            (self.candidate / "docs/glossary.md").read_bytes()
        ).hexdigest()
        created = MODULE.create_bundle(
            self.candidate,
            "target",
            "HEAD",
            glossary_sha256,
            self.repo / ".claude/scripts/classify_reviewers.py",
        )
        evidence = Path(created["bundle_path"]).parents[1]
        before = self.evidence_snapshot(evidence)
        proc = self.run_gate()
        after = self.evidence_snapshot(evidence)
        self.assertEqual(proc.returncode, MODULE.READINESS_REQUIRED, proc.stdout + proc.stderr)
        self.assertIn('"state":"READINESS_REQUIRED"', proc.stdout)
        self.assertEqual(before, after, "read-only merge gate changed existing evidence")

    def test_prepare_creates_exact_bundle_before_review(self) -> None:
        head = self.commit_candidate("crawl-ref/source/review-test.cc", "// test\n")
        proc = self.run_prepare()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["candidate_head"], head)
        self.assertEqual(result["routing"]["reviewers"], ["zh-code-reviewer"])
        self.assertTrue(Path(result["bundle_path"]).is_dir())
        self.assertEqual(result["state"], "READINESS_REQUIRED")

    def test_prepare_rejects_dirty_candidate_before_evidence_write(self) -> None:
        self.commit_candidate("crawl-ref/source/review-test.cc", "// test\n")
        (self.candidate / "dirty.txt").write_text("dirty\n", encoding="utf-8")
        proc = self.run_prepare()
        self.assertEqual(proc.returncode, MODULE.STALE_EVIDENCE, proc.stdout + proc.stderr)
        self.assertIn("candidate worktree is dirty", proc.stderr)
        self.assertFalse((self.repo / ".git/zh-review-evidence").exists())

    def test_gate_scrubs_path_and_git_repository_overrides(self) -> None:
        self.commit_candidate("notes/environment-test.txt", "safe\n")
        proc = self.run_gate(PATH="/tmp/unsafe-path", GIT_DIR="/tmp/not-the-repo")
        self.assertEqual(proc.returncode, 11, proc.stdout + proc.stderr)
        self.assertIn('"state":"FINAL_GATE_REQUIRED"', proc.stdout)

    def test_merge_gate_contains_no_verification_invocation(self) -> None:
        text = (SOURCE_ROOT / ".claude/scripts/review_at_merge.sh").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("--profile review", text)
        self.assertNotIn("verify_zh.sh", text)

    def test_repository_contract_matches_bundle_core(self) -> None:
        contract_path = (
            SOURCE_ROOT
            / ".claude/scripts/data/review_verification_contract_v5.json"
        )
        contract = MODULE._parse_contract(contract_path.read_bytes())
        self.assertIn(MODULE.TRUSTED_CLASSIFIER_PATH, contract["control_plane_files"])
        self.assertIn(".claude/scripts/verify_zh.sh", contract["control_plane_files"])
        self.assertIn(".claude/scripts/review_prepare.sh", contract["control_plane_files"])
        self.assertIn(
            "review-ledgers",
            [phase["id"] for phase in contract["phase_plan"]],
        )
        self.assertEqual(6, len(contract["required_artifacts"]))
        self.assertEqual(
            [phase["id"] for phase in contract["phase_plan"]][-1],
            "zh-runtime-catch2",
        )


if __name__ == "__main__":
    unittest.main()
