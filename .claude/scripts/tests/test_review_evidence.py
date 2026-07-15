#!/usr/bin/env python3
"""Black-box tests for review records, migration, and immutable evidence."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1]


class ReviewEvidenceTests(unittest.TestCase):
    def run_cmd(self, *args: str, cwd: Path, check: bool = False):
        return subprocess.run(
            args, cwd=cwd, text=True, capture_output=True, check=check
        )

    def test_record_review_writes_one_compact_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = {
                "date": "2026-07-15T00:00:00+08:00",
                "agent_type": "zh-code-reviewer",
                "task_summary": "unit test",
                "findings": {"blocker": 0, "needs_fix": 0, "suggestion": 1},
                "fix_iterations": 0,
                "verdict": "Go",
                "trigger": "pre-commit",
            }
            result = self.run_cmd(
                "bash", str(SCRIPTS / "record_review.sh"),
                json.dumps(entry, ensure_ascii=False, indent=2), cwd=root
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            lines = (root / ".claude/metrics/review-log.jsonl").read_text().splitlines()
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0])["schema_version"], 2)

    def test_merge_record_requires_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry = {
                "date": "2026-07-15T00:00:00+08:00",
                "agent_type": "zh-code-reviewer",
                "task_summary": "missing evidence",
                "findings": {"blocker": 0, "needs_fix": 0, "suggestion": 0},
                "fix_iterations": 0,
                "verdict": "Go",
                "trigger": "merge-time",
            }
            result = self.run_cmd(
                "bash", str(SCRIPTS / "record_review.sh"), json.dumps(entry),
                cwd=Path(tmp)
            )
            self.assertNotEqual(result.returncode, 0)

    def test_duplicate_review_id_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = {
                "schema_version": 2,
                "review_id": "same-id",
                "date": "2026-07-15T00:00:00+08:00",
                "agent_type": "zh-code-reviewer",
                "task_summary": "unit test",
                "findings": {"blocker": 0, "needs_fix": 0, "suggestion": 0},
                "fix_iterations": 0,
                "verdict": "Go",
                "trigger": "pre-commit",
            }
            first = self.run_cmd(
                "bash", str(SCRIPTS / "record_review.sh"), json.dumps(entry), cwd=root
            )
            second = self.run_cmd(
                "bash", str(SCRIPTS / "record_review.sh"), json.dumps(entry), cwd=root
            )
            self.assertEqual(first.returncode, 0)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(len((root / ".claude/metrics/review-log.jsonl").read_text().splitlines()), 1)

    def test_migration_preserves_raw_and_canonicalises(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review-log.jsonl"
            path.write_text(
                '{"agent_type":"test"}\n{\n"agent_type":"zh-code-reviewer",'
                '"date":"d"\n}\n', encoding="utf-8"
            )
            result = self.run_cmd(
                "python3", str(SCRIPTS / "migrate_review_log_v2.py"), str(path),
                cwd=Path(tmp)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(path.with_name(path.name + ".v1.raw").is_file())
            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(lines), 1)
            record = json.loads(lines[0])
            self.assertTrue(record["legacy"])
            self.assertEqual(record["schema_version"], 1)

    def test_validator_accepts_matching_passed_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_id = "run-1"
            run_dir = root / ".claude/metrics/verify" / run_id
            run_dir.mkdir(parents=True)
            raw_log = run_dir / "reviewer.log"
            raw_log.write_text("review passed\n", encoding="utf-8")
            raw_hash = hashlib.sha256(raw_log.read_bytes()).hexdigest()
            metadata = {
                "status": "pass",
                "base": "base",
                "head": "head",
                "diff_hash": "diff",
                "glossary_sha256": "glossary",
            }
            (run_dir / "metadata.json").write_text(json.dumps(metadata))
            record = {
                "schema_version": 2,
                "review_id": "review-1",
                "run_id": run_id,
                "trigger": "merge-time",
                "base": "base",
                "head": "head",
                "diff_hash": "diff",
                "glossary_sha256": "glossary",
                "raw_log": str(raw_log.relative_to(root)),
                "raw_log_sha256": raw_hash,
                "findings": {"blocker": 0, "needs_fix": 0, "suggestion": 0},
                "verdict": "Go",
            }
            log = root / "review-log.jsonl"
            log.write_text(json.dumps(record) + "\n")
            result = self.run_cmd(
                "python3", str(SCRIPTS / "validate_review_evidence.py"),
                "--log", str(log.relative_to(root)),
                "--review-id", "review-1", "--base", "base",
                "--head", "head", "--diff-hash", "diff",
                "--verdict", "go", cwd=root
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(json.loads(result.stdout)["run_id"], run_id)

            mismatch = self.run_cmd(
                "python3", str(SCRIPTS / "validate_review_evidence.py"),
                "--log", str(log.relative_to(root)),
                "--review-id", "review-1", "--base", "wrong",
                "--head", "head", "--diff-hash", "diff",
                "--verdict", "go", cwd=root
            )
            self.assertNotEqual(mismatch.returncode, 0)

    def test_merge_gate_records_only_matching_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            scripts = root / ".claude/scripts"
            scripts.mkdir(parents=True)
            for name in ("review_at_merge.sh", "validate_review_evidence.py"):
                (scripts / name).write_bytes((SCRIPTS / name).read_bytes())
            (scripts / "classify_review.sh").write_text(
                '#!/bin/bash\necho \'{"level":"RED","reason":"test","summary":"test"}\'\nexit 2\n'
            )
            (scripts / "verify_zh.sh").write_text("#!/bin/bash\nexit 0\n")
            for path in scripts.iterdir():
                path.chmod(0o755)
            self.run_cmd("git", "init", "-q", cwd=root, check=True)
            self.run_cmd("git", "config", "user.email", "test@example.invalid", cwd=root, check=True)
            self.run_cmd("git", "config", "user.name", "test", cwd=root, check=True)
            self.run_cmd("git", "add", ".claude/scripts", cwd=root, check=True)
            self.run_cmd("git", "commit", "-qm", "base", cwd=root, check=True)
            self.run_cmd("git", "branch", "-m", "target", cwd=root, check=True)
            self.run_cmd("git", "branch", "candidate", cwd=root, check=True)
            self.run_cmd(
                "git", "worktree", "add", "-q", ".worktrees/candidate", "candidate",
                cwd=root, check=True
            )
            candidate = root / ".worktrees/candidate"
            (candidate / "change.txt").write_text("candidate\n")
            self.run_cmd("git", "add", "change.txt", cwd=candidate, check=True)
            self.run_cmd("git", "commit", "-qm", "candidate", cwd=candidate, check=True)

            base = self.run_cmd("git", "rev-parse", "target", cwd=root, check=True).stdout.strip()
            head = self.run_cmd("git", "rev-parse", "candidate", cwd=root, check=True).stdout.strip()
            diff = subprocess.run(
                "git diff --binary target..candidate | git hash-object --stdin",
                cwd=root, shell=True, text=True, capture_output=True, check=True
            ).stdout.strip()
            run_id = "run-merge"
            run_dir = root / ".claude/metrics/verify" / run_id
            run_dir.mkdir(parents=True)
            raw_log = run_dir / "reviewer.log"
            raw_log.write_text("pass\n")
            (run_dir / "metadata.json").write_text(json.dumps({
                "status": "pass", "base": base, "head": head,
                "diff_hash": diff, "glossary_sha256": "a" * 64,
            }))
            review_log = root / ".claude/metrics/review-log.jsonl"
            review_log.write_text(json.dumps({
                "schema_version": 2, "review_id": "review-merge",
                "run_id": run_id, "trigger": "merge-time", "base": base,
                "head": head, "diff_hash": diff, "glossary_sha256": "a" * 64,
                "raw_log": str(raw_log.relative_to(root)),
                "findings": {"blocker": 0, "needs_fix": 0, "suggestion": 0},
                "verdict": "Go",
            }) + "\n")

            missing = self.run_cmd(
                "bash", ".claude/scripts/review_at_merge.sh", "candidate", "target",
                "--record-verdict", "go", cwd=root
            )
            self.assertNotEqual(missing.returncode, 0)
            accepted = self.run_cmd(
                "bash", ".claude/scripts/review_at_merge.sh", "candidate", "target",
                "--record-verdict", "go", "review-merge", "unit test", cwd=root
            )
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            verdicts = list((root / ".claude/metrics/review-verdicts").glob("*.verdict"))
            self.assertEqual(len(verdicts), 1)
            verdict_text = verdicts[0].read_text()
            self.assertIn("review_id=review-merge", verdict_text)
            self.assertIn("glossary_sha256=" + "a" * 64, verdict_text)
            self.assertIn("review_record_sha256=", verdict_text)
            self.assertIn("raw_log_sha256=", verdict_text)

            gated = self.run_cmd(
                "bash", ".claude/scripts/review_at_merge.sh", "candidate", "target",
                cwd=root
            )
            self.assertEqual(gated.returncode, 0, gated.stdout + gated.stderr)

            raw_log.write_text("tampered\n")
            tampered = self.run_cmd(
                "bash", ".claude/scripts/review_at_merge.sh", "candidate", "target",
                cwd=root
            )
            self.assertEqual(tampered.returncode, 2)

            raw_log.write_text("pass\n")
            changed_record = json.loads(review_log.read_text())
            changed_record["findings"]["suggestion"] = 1
            review_log.write_text(json.dumps(changed_record) + "\n")
            changed = self.run_cmd(
                "bash", ".claude/scripts/review_at_merge.sh", "candidate", "target",
                cwd=root
            )
            self.assertEqual(changed.returncode, 2)


if __name__ == "__main__":
    unittest.main()
