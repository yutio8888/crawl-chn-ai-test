#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[3]

ENTRY_POINTS = [
    ROOT / "AGENTS.md",
    ROOT / "CODEX.md",
    ROOT / "CLAUDE.md",
    ROOT / ".opencode/RUNTIME.md",
]

AUTHORITIES = [
    ROOT / ".agents/README.md",
    ROOT / ".agents/policies/i18n-safety.md",
    ROOT / ".agents/policies/asset-ownership.md",
    ROOT / ".agents/policies/review-contract.md",
    ROOT / ".agents/policies/worktree-policy.md",
    ROOT / "docs/agent-routing.md",
    ROOT / "docs/build-workflow.md",
    ROOT / "docs/cjk-tiles-architecture.md",
    ROOT / "docs/dual-agent-workflow.md",
    ROOT / "docs/issue-tracking.md",
    ROOT / "docs/translation-architecture.md",
    ROOT / "docs/zh-testing.md",
]

DOCS_TO_LINT = ENTRY_POINTS + AUTHORITIES

STALE_PATTERNS = {
    r"28 project tool scripts": "hard-coded obsolete script count",
    r"gpt-5\.5": "hard-coded obsolete model",
    r"worktree-cjk-tiles-fix": "obsolete branch inventory",
    r"KNOWN_ISSUES_ZH\.md": "missing historical status document",
    r"Review \(3-way parallel\)": "obsolete fixed reviewer count",
    r"Run via `bash`[^\n]*OpenCode has no `Workflow`":
        "workflow DSL described as a shell program",
}

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class AgentDocumentationTests(unittest.TestCase):
    def test_authoritative_files_exist(self) -> None:
        missing = [path.relative_to(ROOT).as_posix()
                   for path in ENTRY_POINTS + AUTHORITIES if not path.is_file()]
        self.assertEqual([], missing)

    def test_entry_points_remain_thin(self) -> None:
        limits = {
            "AGENTS.md": 220,
            "CODEX.md": 100,
            "CLAUDE.md": 100,
            ".opencode/RUNTIME.md": 100,
        }
        for path in ENTRY_POINTS:
            with self.subTest(path=path.relative_to(ROOT)):
                lines = len(path.read_text().splitlines())
                self.assertLessEqual(lines, limits[path.relative_to(ROOT).as_posix()])

    def test_volatile_or_obsolete_facts_are_absent(self) -> None:
        for path in DOCS_TO_LINT:
            text = path.read_text()
            for pattern, reason in STALE_PATTERNS.items():
                with self.subTest(path=path.relative_to(ROOT), reason=reason):
                    self.assertIsNone(re.search(pattern, text), reason)

    def test_runtime_adapters_do_not_duplicate_model_assignments(self) -> None:
        model_pattern = re.compile(r"(?:gpt-|deepseek|openrouter/)", re.IGNORECASE)
        for path in ENTRY_POINTS:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(model_pattern.search(path.read_text()))

    def test_workflow_dsl_is_not_shown_as_an_executable_command(self) -> None:
        command = re.compile(
            r"(?m)^\s*(?:\$\s*)?(?:node|bash)\s+"
            r"\.(?:opencode|claude)/workflows/"
        )
        for path in DOCS_TO_LINT:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(command.search(path.read_text()))

    def test_opencode_pipeline_uses_opencode_fallback_syntax(self) -> None:
        path = ROOT / ".opencode/skills/translation-pipeline/SKILL.md"
        text = path.read_text()
        self.assertIn('task(subagent_type="general"', text)
        self.assertNotIn('Agent(subagent_type="general"', text)
        self.assertIn(".opencode/workflows/*.js", text)

    def test_codex_does_not_claim_other_runtime_authorship(self) -> None:
        text = (ROOT / "CODEX.md").read_text()
        self.assertNotIn("Co-Authored-By: opencode", text)
        self.assertNotIn("Co-Authored-By: Claude", text)

    def test_workflow_compatibility_copies_are_identical(self) -> None:
        for name in ("translation-fix-pipeline.js",
                     "translation-batch-pipeline.js"):
            with self.subTest(workflow=name):
                opencode = (ROOT / ".opencode/workflows" / name).read_bytes()
                claude = (ROOT / ".claude/workflows" / name).read_bytes()
                self.assertEqual(opencode, claude)

    def test_relative_markdown_links_resolve(self) -> None:
        for path in DOCS_TO_LINT:
            for raw_target in MARKDOWN_LINK.findall(path.read_text()):
                target = raw_target.strip().strip("<>")
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                target = target.split("#", 1)[0]
                if not target:
                    continue
                resolved = (path.parent / target).resolve()
                with self.subTest(path=path.relative_to(ROOT), target=target):
                    self.assertTrue(resolved.exists(), f"missing link target: {resolved}")

    def test_runtime_driver_has_read_only_help(self) -> None:
        script = ROOT / ".claude/scripts/post_zh_runtime.sh"
        result = subprocess.run(
            ["bash", str(script), "--help"], cwd=ROOT,
            text=True, capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("help-baseline", result.stdout)


if __name__ == "__main__":
    unittest.main()
