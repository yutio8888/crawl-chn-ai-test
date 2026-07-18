#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess
import tempfile
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
    ROOT / ".agents/policies/path-portability.md",
    ROOT / ".agents/policies/review-contract.md",
    ROOT / ".agents/policies/worktree-policy.md",
    ROOT / "docs/agent-routing.md",
    ROOT / "docs/build-workflow.md",
    ROOT / "docs/cjk-tiles-architecture.md",
    ROOT / "docs/dual-agent-workflow.md",
    ROOT / "docs/issue-tracking.md",
    ROOT / "docs/translation-architecture.md",
    ROOT / "docs/zh-testing.md",
    ROOT / "crawl-ref/source/init.zh.txt",
]

DOCS_TO_LINT = ENTRY_POINTS + AUTHORITIES + [ROOT / "README.md"]

STALE_PATTERNS = {
    r"28 project tool scripts": "hard-coded obsolete script count",
    r"gpt-5\.5": "hard-coded obsolete model",
    r"worktree-cjk-tiles-fix": "obsolete branch inventory",
    r"KNOWN_ISSUES_ZH\.md": "missing historical status document",
    r"Review \(3-way parallel\)": "obsolete fixed reviewer count",
    r"Run via `bash`[^\n]*OpenCode has no `Workflow`":
        "workflow DSL described as a shell program",
    r"/home/yutio888": "clone-specific absolute path",
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

    def test_workflows_enforce_translation_first_and_profile_success(self) -> None:
        for tree in (".claude", ".opencode"):
            batch = (ROOT / tree / "workflows/translation-batch-pipeline.js").read_text()
            execute = batch.split("phase('Execute Sequential')", 1)[1].split(
                "phase('Prepare Review Bundle')", 1)[0]
            with self.subTest(tree=tree):
                translation_pass, code_pass = execute.split("// Pass 2:", 1)
                self.assertIn("// Pass 1:", translation_pass)
                self.assertNotIn("agentType: 'crawl-coder'", translation_pass)
                self.assertNotIn("agentType: 'zh-translator'", code_pass)
                self.assertLess(
                    execute.index("agentType: 'zh-translator'"),
                    execute.index("agentType: 'crawl-coder'"),
                )
                self.assertIn("translation_execution_failed", execute)
                self.assertIn("code_execution_failed", execute)
                self.assertIn("verificationStatus", batch)
                self.assertNotIn("mprf_p for positional %s", batch)

            single = (ROOT / tree / "workflows/translation-fix-pipeline.js").read_text()
            self.assertIn("translation_execution_failed", single)
            self.assertIn("code_execution_failed", single)
            self.assertNotIn("mprf_p for positional %s", single)

    def test_translation_assets_use_full_repository_paths(self) -> None:
        paths = [
            ROOT / "AGENTS.md",
            ROOT / "docs/translation-architecture.md",
            ROOT / ".agents/policies/asset-ownership.md",
            *ROOT.glob(".claude/agents/*.md"),
            *ROOT.glob(".claude/skills/*.md"),
            *ROOT.glob(".opencode/agents/*.md"),
            *ROOT.glob(".opencode/skills/*/SKILL.md"),
            *ROOT.glob(".codex/agents/*.toml"),
        ]
        for path in paths:
            text = path.read_text()
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("`dat/database/zh/`", text)
                self.assertNotIn("`dat/descript/zh/`", text)

    def test_coder_templates_handoff_translation_assets(self) -> None:
        paths = [
            ROOT / ".claude/agents/crawl-coder.md",
            ROOT / ".claude/skills/crawl-coder.md",
            ROOT / ".opencode/agents/crawl-coder.md",
            ROOT / ".opencode/skills/crawl-coder/SKILL.md",
            ROOT / ".codex/agents/crawl-coder.toml",
        ]
        forbidden = (
            "append to zh/source.txt",
            "Add corresponding entries to crawl-ref/source/dat/i18n/zh/source.txt",
            "Add all new keys to source.txt",
            "T_() + source.txt entry in same commit",
        )
        for path in paths:
            text = path.read_text()
            with self.subTest(path=path.relative_to(ROOT)):
                for phrase in forbidden:
                    self.assertNotIn(phrase, text)
                self.assertIn("zh-translator", text)

    def test_chinese_deploy_contract_is_fail_closed(self) -> None:
        template = (ROOT / "crawl-ref/source/init.zh.txt").read_text()
        self.assertIn("language = zh", template)
        self.assertIn("language := language", template)
        for role in ("crt", "msg", "stat", "tip", "lbl"):
            self.assertIn(f"tile_font_{role}_file := tile_font_{role}_file", template)
            self.assertIn(
                f"tile_font_{role}_file = dat/tiles/MapleMono-NF-CN-Regular.ttf",
                template,
            )

        deploy = (ROOT / ".claude/scripts/deploy.sh").read_text()
        self.assertIn("validate_chinese_init", deploy)
        self.assertIn("effective_init_value", deploy)
        self.assertIn("VERSIONED_INIT", deploy)
        self.assertIn('cat "$VERSIONED_INIT" >> "$DEPLOY_INIT"', deploy)
        self.assertIn("FONT_SOURCE", deploy)
        self.assertIn('cmp -s "$INIT_SOURCE" "$TARGET/init.txt"', deploy)
        self.assertIn(
            'cmp -s "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"', deploy
        )
        self.assertNotIn("init.txt not found in either worktree. Skipping", deploy)
        self.assertNotIn("cp contrib/fonts/*.ttf", deploy)

        script = ROOT / ".claude/scripts/deploy.sh"
        template_without_alias_resets = "\n".join(
            line for line in template.splitlines() if ":=" not in line
        ) + "\n"
        cases = {
            "canonical": (template, 0),
            "later_language_override": (template + "\nlanguage = en\n", 1),
            "later_font_override": (
                template
                + "\ntile_font_msg_file = dat/tiles/DejaVuSansMono.ttf\n",
                1,
            ),
            "last_assignment_wins": ("language = en\n" + template, 0),
            "language_alias_without_reset": (
                "language := fake_lang\n" + template_without_alias_resets,
                1,
            ),
            "font_alias_without_reset": (
                "tile_font_msg_file := other_font\n"
                + template_without_alias_resets,
                1,
            ),
            "canonical_resets_local_alias": (
                "language := fake_lang\n"
                "tile_font_msg_file := other_font\n"
                + template,
                0,
            ),
        }
        for name, (contents, expected) in cases.items():
            with self.subTest(case=name), tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8"
            ) as handle:
                handle.write(contents)
                handle.flush()
                result = subprocess.run(
                    ["bash", str(script), "--validate-init", handle.name],
                    cwd=ROOT, text=True, capture_output=True,
                )
                self.assertEqual(expected, result.returncode, result.stderr)

    def test_readme_avoids_volatile_counts_and_legacy_font_contract(self) -> None:
        text = (ROOT / "README.md").read_text()
        for pattern in (r"~30,", r"30,452", r"~93%", r"\*\*活跃开发分支\*\*"):
            self.assertIsNone(re.search(pattern, text))
        self.assertNotIn("必须保留 DejaVu Sans Mono", text)
        historical = (ROOT / "docs/cjk-tiles-support.md").read_text()
        self.assertIn("历史实现记录", historical[:500])

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
