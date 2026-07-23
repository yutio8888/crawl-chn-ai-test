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
    ROOT / ".pi/APPEND_SYSTEM.md",
    ROOT / ".opencode/RUNTIME.md",
]

AUTHORITIES = [
    ROOT / ".agents/README.md",
    ROOT / ".agents/policies/i18n-safety.md",
    ROOT / ".agents/policies/asset-ownership.md",
    ROOT / ".agents/policies/path-portability.md",
    ROOT / ".agents/policies/review-contract.md",
    ROOT / ".agents/policies/translation-integrity.md",
    ROOT / ".agents/policies/verification-authoring.md",
    ROOT / ".agents/policies/worktree-policy.md",
    ROOT / "docs/agent-routing.md",
    ROOT / "docs/build-workflow.md",
    ROOT / "docs/cjk-tiles-architecture.md",
    ROOT / "docs/dual-agent-workflow.md",
    ROOT / "docs/issue-tracking.md",
    ROOT / "docs/translation-architecture.md",
    ROOT / "docs/zh-testing.md",
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
            ".pi/APPEND_SYSTEM.md": 100,
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

    def test_pi_runtime_configuration_is_native_and_guarded(self) -> None:
        settings = (ROOT / ".pi/settings.json").read_text()
        self.assertIn('"defaultProvider": "openai-codex"', settings)
        self.assertIn('"defaultModel": "gpt-5.6-sol"', settings)
        self.assertTrue((ROOT / ".pi/prompts/goal.md").is_file())
        guard = (ROOT / ".pi/extensions/enforce-worktree-path.ts").read_text()
        self.assertIn('pi.on("tool_call"', guard)
        self.assertIn('name: "project_worktree"', guard)
        adapter = (ROOT / ".pi/APPEND_SYSTEM.md").read_text()
        self.assertIn("Do not use `pi-subagents` `worktree: true`", adapter)
        self.assertIn("project_worktree", adapter)
        self.assertIn("returned absolute `cwd`", adapter)
        self.assertIn(".pi-subagents/", (ROOT / ".gitignore").read_text())
        expected_agents = {
            "crawl-coder", "ocr", "reviewer", "scout",
            "translation-reviewer", "worker", "zh-code-reviewer",
            "zh-translator",
        }
        self.assertEqual(
            expected_agents,
            {path.stem for path in (ROOT / ".pi/agents").glob("*.md")},
        )

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

    def test_codex_pipeline_skill_is_present_and_reference_driven(self) -> None:
        path = ROOT / ".agents/skills/translation-pipeline/SKILL.md"
        text = path.read_text()
        self.assertIn("$dcss-translation-context", text)
        self.assertIn(".agents/policies/asset-ownership.md", text)
        self.assertIn(".agents/policies/translation-integrity.md", text)
        self.assertIn(".agents/policies/review-contract.md", text)
        self.assertIn("docs/agent-routing.md", text)
        self.assertIn("review_prepare.sh", text)
        self.assertIn("review_final_gate.sh", text)
        self.assertNotIn('Agent(subagent_type=', text)
        self.assertNotIn('task(subagent_type=', text)
        self.assertNotIn("node .claude/workflows/", text)

    def test_plan_review_enforces_minimal_sufficient_design(self) -> None:
        required_fragments = (
            "acceptanceCriteria",
            "nonGoals",
            "design_induced",
            "preferredAction",
            "delete, reuse, and narrow",
            "reviewer suggestions are not commands",
        )
        for name in ("translation-fix-pipeline.js",
                     "translation-batch-pipeline.js"):
            text = (ROOT / ".claude/workflows" / name).read_text()
            for fragment in required_fragments:
                with self.subTest(workflow=name, fragment=fragment):
                    self.assertIn(fragment, text)
            self.assertNotIn("Address EVERY issue", text)
            self.assertNotIn("Address ALL review issues", text)
            self.assertNotIn("Were ALL previous issues addressed", text)
            self.assertNotIn("scope_expansion_required", text)
            self.assertNotIn("newMechanisms", text)

        for path in (
            ROOT / ".claude/skills/translation-pipeline.md",
            ROOT / ".opencode/skills/translation-pipeline/SKILL.md",
        ):
            text = path.read_text()
            with self.subTest(skill=path.relative_to(ROOT)):
                self.assertIn("最小充分方案边界", text)
                self.assertIn("验收标准和明确非目标", text)
                self.assertIn("design_induced", text)
                self.assertIn("删除、复用、缩小、新增", text)
                self.assertIn("`rejected`", text)

    def test_codex_does_not_claim_other_runtime_authorship(self) -> None:
        text = (ROOT / "CODEX.md").read_text()
        self.assertNotIn("Co-Authored-By: opencode", text)
        self.assertNotIn("Co-Authored-By: Claude", text)

    def test_legacy_issue_repository_is_not_a_live_dependency(self) -> None:
        paths = (
            ROOT / "README.md",
            ROOT / "docs/issue-tracking.md",
            ROOT / "docs/known-issues-zh.md",
            ROOT / "docs/dual-agent-workflow.md",
            ROOT / ".claude/ORCHESTRATION_STATE.md",
            ROOT / ".claude/skills/translation-pipeline.md",
            ROOT / ".opencode/skills/translation-pipeline/SKILL.md",
            ROOT / ".claude/workflows/translation-fix-pipeline.js",
            ROOT / ".claude/workflows/translation-batch-pipeline.js",
            ROOT / ".opencode/workflows/translation-fix-pipeline.js",
            ROOT / ".opencode/workflows/translation-batch-pipeline.js",
        )
        forbidden = ("DCSS_ISSUES_DIR", "issueFile", "../issues")
        for path in paths:
            text = path.read_text()
            for fragment in forbidden:
                with self.subTest(path=path.relative_to(ROOT), fragment=fragment):
                    self.assertNotIn(fragment, text)

    def test_workflow_compatibility_copies_are_identical(self) -> None:
        for name in ("translation-fix-pipeline.js",
                     "translation-batch-pipeline.js"):
            with self.subTest(workflow=name):
                opencode = (ROOT / ".opencode/workflows" / name).read_bytes()
                claude = (ROOT / ".claude/workflows" / name).read_bytes()
                self.assertEqual(opencode, claude)

    def test_workflows_fail_closed_on_invalid_structured_findings(self) -> None:
        required_fragments = (
            "maxItems: 200",
            "maximum: 10000000",
            "id is invalid or duplicated",
            "file is not a normalized relative path",
            "glossary SHA-256 does not match the bundle",
            "validateReviewFindings(kind, result, reviewBoundary.glossary_sha256)",
        )
        for name in (
            "translation-fix-pipeline.js",
            "translation-batch-pipeline.js",
        ):
            text = (ROOT / ".claude/workflows" / name).read_text()
            for fragment in required_fragments:
                with self.subTest(workflow=name, fragment=fragment):
                    self.assertIn(fragment, text)

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
            *ROOT.glob(".pi/agents/*.md"),
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
            ROOT / ".pi/agents/crawl-coder.md",
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
        font = ROOT / "crawl-ref/source/dat/tiles/MapleMono-NF-CN-Regular.ttf"
        self.assertTrue(font.is_file())
        self.assertGreater(font.stat().st_size, 0)
        self.assertNotIn(
            "crawl-ref/source/dat/tiles/MapleMono-NF-CN-Regular.ttf",
            (ROOT / ".gitignore").read_text(),
        )

        initfile = (ROOT / "crawl-ref/source/initfile.cc").read_text()
        self.assertIn("Options.apply_distribution_defaults();", initfile)
        self.assertIn('language_option = "zh";', initfile)
        self.assertIn("ASSERT(set_lang(language_option.c_str()));", initfile)
        self.assertEqual(5, initfile.count(
            '"dat/tiles/MapleMono-NF-CN-Regular.ttf", true)'
        ))
        self.assertIn(
            "new IntGameOption(SIMPLE_NAME(tile_window_width), 1280,", initfile
        )
        self.assertIn(
            "new IntGameOption(SIMPLE_NAME(tile_window_height), 800,", initfile
        )
        self.assertIn(
            "new IntGameOption(SIMPLE_NAME(tile_window_ratio), 0,", initfile
        )
        self.assertIn("SCREENMODE_WINDOW", initfile)

        deploy = (ROOT / ".claude/scripts/deploy.sh").read_text()
        self.assertIn("FONT_SOURCE", deploy)
        self.assertIn(
            'cmp -s "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"', deploy
        )
        self.assertIn('if [ -s "$LOCAL_INIT" ]; then', deploy)
        self.assertIn('rm -f "$TARGET/init.txt"', deploy)
        self.assertNotIn("VERSIONED_INIT", deploy)
        self.assertNotIn("validate_chinese_init", deploy)

        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        self.assertIn("package-windows-tiles", workflow)
        self.assertIn("name: windows-tiles", workflow)
        self.assertIn("stone_soup-*-tiles-win32.zip", workflow)
        self.assertIn("!crawl-ref/source/mac-app-zips/latest.zip", workflow)
        self.assertIn("release_draft:", workflow)
        self.assertIn("Create verified draft release", workflow)
        self.assertIn("verify_release_artifacts.py", workflow)
        self.assertIn("--draft --verify-tag", workflow)
        self.assertIn("Create draft release once", workflow)
        self.assertIn("Expected 3 release assets", workflow)
        self.assertNotIn("Download Linux package", workflow)
        self.assertNotIn("name: linux-console", workflow)
        self.assertNotIn("Download macOS package", workflow)
        self.assertIn("name: macos-tiles-app", workflow)
        self.assertIn("首个中文 Windows 正式版", workflow)
        self.assertIn("macOS Tiles：仅保留 CI 编译产物", workflow)
        release_draft = workflow.split("  release_draft:\n", 1)[1]
        release_needs = release_draft.split("    permissions:\n", 1)[0]
        self.assertNotIn("- build_linux_console", release_needs)
        self.assertNotIn("- build_macos_tiles", release_needs)
        self.assertNotIn("gh release upload", workflow)
        self.assertNotIn("gh release edit", workflow)

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
