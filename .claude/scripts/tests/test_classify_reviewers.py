#!/usr/bin/env python3
"""Tests for mechanical reviewer routing."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "classify_reviewers.py"
REPO = SCRIPT.parents[2]
SPEC = importlib.util.spec_from_file_location("classify_reviewers", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)


class ReviewerRoutingTests(unittest.TestCase):
    def assert_route(self, files, classification, reviewers):
        result = MODULE.classify_files(files)
        self.assertEqual(result["classification"], classification)
        self.assertEqual(result["reviewers"], reviewers)

    def test_pure_code_routes_code_reviewer(self):
        self.assert_route(
            ["crawl-ref/source/melee-attack.cc", ".claude/scripts/tool.py"],
            "code", ["zh-code-reviewer"],
        )

    def test_pure_translation_routes_translation_reviewer(self):
        self.assert_route(
            ["crawl-ref/source/dat/i18n/zh/source.txt", "docs/glossary.md"],
            "translation", ["translation-reviewer"],
        )

    def test_mixed_routes_both_reviewers(self):
        self.assert_route(
            ["crawl-ref/source/player.cc", "crawl-ref/source/dat/descript/zh/items.txt"],
            "mixed", ["zh-code-reviewer", "translation-reviewer"],
        )

    def test_localized_overlay_fragments_route_both_reviewers(self):
        for path in (
            ".claude/data/message-overlay/monspell.json",
            ".claude/data/message-overlay/monspell/batch-a.json",
        ):
            with self.subTest(path=path):
                self.assert_route(
                    [path], "mixed",
                    ["zh-code-reviewer", "translation-reviewer"],
                )

    def test_unknown_source_file_fails_safe_to_code(self):
        self.assert_route(
            ["crawl-ref/source/dat/mystery/runtime.asset"],
            "code", ["zh-code-reviewer"],
        )

    def test_empty_diff_routes_no_reviewers(self):
        self.assert_route([], "none", [])

    def test_policy_infrastructure_requires_code_review(self):
        self.assert_route(
            [".opencode/workflows/translation-fix-pipeline.js"],
            "code", ["zh-code-reviewer"],
        )

    def test_explicit_absolute_and_parent_paths_fail_closed(self):
        for path in ("/tmp/source.txt", "../source.txt", "docs/../CLAUDE.md", "C:/repo/file.cc"):
            with self.subTest(path=path):
                proc = subprocess.run(
                    ["python3", str(SCRIPT), "--files", path],
                    text=True, capture_output=True,
                )
                self.assertEqual(proc.returncode, 2)
                self.assertIn("ERROR:", proc.stderr)

    def test_base_head_cli_emits_machine_readable_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            target = repo / "crawl-ref/source/dat/i18n/zh/source.txt"
            target.parent.mkdir(parents=True)
            target.write_text("old\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "base"], check=True)
            base = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
            target.write_text("new\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repo), "commit", "-qam", "head"], check=True)
            head = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()

            proc = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo), "--base", base, "--head", head],
                text=True, capture_output=True, check=True,
            )
            result = json.loads(proc.stdout)
            self.assertEqual(result["classification"], "translation")
            self.assertEqual(result["reviewers"], ["translation-reviewer"])
            self.assertEqual(result["source"], {"type": "git", "base": base, "head": head})

            empty = subprocess.run(
                ["python3", str(SCRIPT), "--repo", str(repo), "--base", head, "--head", head],
                text=True, capture_output=True, check=True,
            )
            empty_result = json.loads(empty.stdout)
            self.assertEqual(empty_result["classification"], "none")
            self.assertEqual(empty_result["reviewers"], [])

    def test_workflows_and_fallback_consume_shared_result(self):
        workflow_dir = REPO / ".opencode/workflows"
        legacy_workflow_dir = REPO / ".claude/workflows"
        for name in ("translation-fix-pipeline.js", "translation-batch-pipeline.js"):
            text = (workflow_dir / name).read_text(encoding="utf-8")
            legacy_text = (legacy_workflow_dir / name).read_text(encoding="utf-8")
            self.assertEqual(legacy_text, text, name + " workflow copies diverged")
            self.assertNotIn("args?.reviewRouting", text, name)
            self.assertIn("args?.targetRoot", text, name)
            self.assertIn("args?.targetBranch", text, name)
            self.assertIn("args?.candidateBranch", text, name)
            self.assertIn("review_prepare.sh", text, name)
            self.assertIn("review_boundary_arguments_required", text, name)
            self.assertIn("const REVIEW_ROUTING = reviewBoundary.routing", text, name)
            self.assertIn("REVIEW_ROUTING?.schema_version !== 1", text, name)
            self.assertIn("JSON.stringify(routedReviewers) !== JSON.stringify(expectedReviewers)", text, name)
            self.assertIn("routedReviewers.includes('zh-code-reviewer')", text, name)
            self.assertIn("routedReviewers.includes('translation-reviewer')", text, name)
            self.assertIn("reviewJobs.length ? await parallel(reviewJobs) : []", text, name)
            self.assertIn("review-contract-v4", text, name)
            self.assertIn("Ready for Final Gate", text, name)
            self.assertIn("persist-review-readiness", text, name)
            self.assertIn("run-single-final-gate", text, name)
            self.assertIn("routedReviewers.length === 0", text, name)
            self.assertIn("READINESS_NOT_REQUIRED", text, name)
            self.assertIn("finalGate?.state !== 'MERGEABLE'", text, name)
            self.assertIn("review_final_gate.sh", text, name)
            self.assertNotIn("bash .claude/scripts/verify_zh.sh --profile review", text, name)
            self.assertNotIn("Conditional Go", text, name)
            self.assertNotIn("p0Issues", text, name)
            self.assertNotIn("p1Issues", text, name)
            self.assertNotIn("P0", text, name)
            self.assertNotIn("P1", text, name)
            self.assertNotIn("label: 'terminology'", text, name)
            self.assertNotIn("termCheck", text, name)
            self.assertIn("bash .claude/scripts/check_consistency.sh --rulings", text, name)
            self.assertLess(text.index("commit only"), text.index("phase('Prepare Review Bundle')"), name)
            self.assertLess(text.index("phase('Prepare Review Bundle')"), text.index("phase('Cross-validate')"), name)
            self.assertLess(text.index("phase('Cross-validate')"), text.index("phase('Seal Final Evidence')"), name)

        skill = (REPO / ".opencode/skills/translation-pipeline/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(".claude/scripts/classify_reviewers.py", skill)
        self.assertIn("args.targetRoot", skill)
        self.assertIn("review_prepare.sh", skill)
        self.assertNotIn("args.reviewRouting", skill)
        self.assertIn("只对\n`reviewers`", skill)

    def test_forged_routing_payload_is_rejected_by_workflow_contract(self):
        forged = {"schema_version": 1, "classification": "code", "reviewers": []}
        expected = {
            "none": [],
            "code": ["zh-code-reviewer"],
            "translation": ["translation-reviewer"],
            "mixed": ["zh-code-reviewer", "translation-reviewer"],
        }
        self.assertNotEqual(forged["reviewers"], expected[forged["classification"]])
        for name in ("translation-fix-pipeline.js", "translation-batch-pipeline.js"):
            text = (REPO / ".opencode/workflows" / name).read_text(encoding="utf-8")
            self.assertIn("JSON.stringify(routedReviewers) !== JSON.stringify(expectedReviewers)", text)

    def test_review_context_uses_v3_readiness_contract_and_ownership(self):
        proc = subprocess.run(
            [
                "bash", ".claude/scripts/context_resolve.sh", "review routing",
                "--task-type", "review", "--files", ".opencode/workflows/translation-fix-pipeline.js",
            ],
            cwd=REPO, text=True, capture_output=True, check=True,
        )
        output = proc.stdout
        self.assertIn("review-contract-v4", output)
        self.assertIn("**Blocker**", output)
        self.assertIn("**Needs Fix**", output)
        self.assertIn("**Suggestion**", output)
        self.assertIn("`zh-code-reviewer`", output)
        self.assertIn("`translation-reviewer`", output)
        self.assertIn("Ready for Final Gate", output)
        self.assertIn("review_final_gate.sh", output)
        self.assertNotIn("Conditional Go", output)
        self.assertNotIn("P0", output)
        self.assertNotIn("P1", output)


if __name__ == "__main__":
    unittest.main()
