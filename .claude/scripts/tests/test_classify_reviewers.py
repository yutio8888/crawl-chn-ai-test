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
            [".agents/skills/translation-pipeline/SKILL.md"],
            "code", ["zh-code-reviewer"],
        )

    def test_pi_policy_and_zh_testing_route_only_code_reviewer(self):
        for path in (
            ".pi/agents/translation-reviewer.md",
            "docs/zh-testing.md",
        ):
            with self.subTest(path=path):
                self.assert_route(
                    [path], "code", ["zh-code-reviewer"],
                )

    def test_root_review_result_ledgers_route_both_reviewers_only(self):
        expected = {
            "card-review-results.md",
            "character-mechanics-review-results.md",
            "cloud-review-results.md",
            "command-review-results.md",
            "decorlines-review-results.md",
            "god-review-results.md",
            "graffiti-review-results.md",
            "help-review-results.md",
            "hint-review-results.md",
            "item-extended-review-results.md",
            "miscast-review-results.md",
            "monflee-review-results.md",
            "monspeak-review-results.md",
            "monspell-review-results.md",
            "monster-review-results.md",
            "shout-review-results.md",
            "species-background-review-results.md",
            "spell-name-review-results.md",
            "tutorial-review-results.md",
            "world-review-results.md",
            "wpnnoise-review-results.md",
        }
        ledgers = sorted(REPO.glob("docs/*-review-results.md"))
        self.assertEqual(expected, {path.name for path in ledgers})
        for path in ledgers:
            with self.subTest(path=path.name):
                self.assert_route(
                    [path.relative_to(REPO).as_posix()],
                    "mixed",
                    ["zh-code-reviewer", "translation-reviewer"],
                )
        for path in (
            "docs/nested/character-review-results.md",
            "docs/character-review-results.md.bak",
            "docs/review-plan.md",
            "docs/review-note.md",
        ):
            with self.subTest(nonmatch=path):
                category, _reason = MODULE.classify_file(path)
                self.assertNotEqual("mixed", category)

    def test_explicit_absolute_and_parent_paths_fail_closed(self):
        for path in ("/tmp/source.txt", "../source.txt", "docs/../CODEX.md", "C:/repo/file.cc"):
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

    def test_git_renames_preserve_both_endpoints_and_review_risk(self):
        cases = (
            (
                "crawl-ref/source/review_probe.cc",
                "docs/review_probe",
                "code",
                ["zh-code-reviewer"],
            ),
            (
                "crawl-ref/source/dat/i18n/zh/old.txt",
                "crawl-ref/source/dat/descript/zh/new.txt",
                "translation",
                ["translation-reviewer"],
            ),
            (
                "crawl-ref/source/review_probe.cc",
                "crawl-ref/source/dat/i18n/zh/review_probe.txt",
                "mixed",
                ["zh-code-reviewer", "translation-reviewer"],
            ),
        )
        for old_path, new_path, classification, reviewers in cases:
            with self.subTest(old=old_path, new=new_path):
                with tempfile.TemporaryDirectory() as tmp:
                    repo = Path(tmp)
                    subprocess.run(["git", "init", "-q", str(repo)], check=True)
                    subprocess.run(
                        ["git", "-C", str(repo), "config", "user.email",
                         "test@example.invalid"],
                        check=True,
                    )
                    subprocess.run(
                        ["git", "-C", str(repo), "config", "user.name", "Test"],
                        check=True,
                    )
                    old = repo / old_path
                    old.parent.mkdir(parents=True)
                    old.write_text("rename payload\n", encoding="utf-8")
                    subprocess.run(
                        ["git", "-C", str(repo), "add", "."], check=True
                    )
                    subprocess.run(
                        ["git", "-C", str(repo), "commit", "-qm", "base"],
                        check=True,
                    )
                    base = subprocess.check_output(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"],
                        text=True,
                    ).strip()
                    new = repo / new_path
                    new.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(
                        ["git", "-C", str(repo), "mv", old_path, new_path],
                        check=True,
                    )
                    subprocess.run(
                        ["git", "-C", str(repo), "commit", "-qm", "rename"],
                        check=True,
                    )
                    head = subprocess.check_output(
                        ["git", "-C", str(repo), "rev-parse", "HEAD"],
                        text=True,
                    ).strip()

                    changed = MODULE.git_changed_files(base, head, str(repo))
                    self.assertEqual(sorted((old_path, new_path)), sorted(changed))
                    result = MODULE.classify_files(changed)
                    self.assertEqual(classification, result["classification"])
                    self.assertEqual(reviewers, result["reviewers"])

    def test_review_context_uses_v3_readiness_contract_and_ownership(self):
        proc = subprocess.run(
            [
                "bash", ".claude/scripts/context_resolve.sh", "review routing",
                "--task-type", "review", "--files",
                ".agents/skills/translation-pipeline/SKILL.md",
            ],
            cwd=REPO, text=True, capture_output=True, check=True,
        )
        output = proc.stdout
        self.assertIn("review-contract-v5", output)
        self.assertIn("**Blocker**", output)
        self.assertIn("**Needs Fix**", output)
        self.assertIn("**Suggestion**", output)
        self.assertIn("`zh-code-reviewer`", output)
        self.assertIn("`translation-reviewer`", output)
        self.assertIn("Ready for Final Gate", output)
        self.assertIn("review_final_gate.sh", output)
        self.assertIn(
            "TERM=xterm-256color bash .claude/scripts/review_final_gate.sh",
            output,
        )
        self.assertIn("Only the orchestrator runs the final profile", output)
        self.assertIn("complete prepared diff", output)
        self.assertIn("Plan non-goals do not excuse defects", output)
        self.assertIn("theoretical risk outside the acceptance criteria is non-blocking", output)
        self.assertIn("before adding mechanisms", output)
        self.assertNotIn("Conditional Go", output)
        self.assertNotIn("P0", output)
        self.assertNotIn("P1", output)


if __name__ == "__main__":
    unittest.main()
