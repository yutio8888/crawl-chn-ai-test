#!/usr/bin/env python3

from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[3]

ENTRY_POINTS = [
    ROOT / "AGENTS.md",
    ROOT / "CODEX.md",
    ROOT / ".pi/APPEND_SYSTEM.md",
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

ARCHIVES = [
    ROOT / "docs/review-recovery-history.md",
]

DOCS_TO_LINT = ENTRY_POINTS + AUTHORITIES + ARCHIVES + [ROOT / "README.md"]

STALE_PATTERNS = {
    r"28 project tool scripts": "hard-coded obsolete script count",
    r"gpt-5\.5": "hard-coded obsolete model",
    r"worktree-cjk-tiles-fix": "obsolete branch inventory",
    r"KNOWN_ISSUES_ZH\.md": "missing historical status document",
    r"Review \(3-way parallel\)": "obsolete fixed reviewer count",
    r"\bOpenCode\b": "retired runtime adapter",
    r"\bClaude Code\b": "retired runtime adapter",
    r"/home/yutio888": "clone-specific absolute path",
}

MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


class AgentDocumentationTests(unittest.TestCase):
    def test_documented_files_exist(self) -> None:
        missing = [path.relative_to(ROOT).as_posix()
                   for path in ENTRY_POINTS + AUTHORITIES + ARCHIVES
                   if not path.is_file()]
        self.assertEqual([], missing)

    def test_entry_points_remain_thin(self) -> None:
        limits = {
            "AGENTS.md": 220,
            "CODEX.md": 100,
            ".pi/APPEND_SYSTEM.md": 100,
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

    def test_batch_translation_review_skill_is_shared_with_pi(self) -> None:
        skill = ROOT / ".agents/skills/batch-translation-review/SKILL.md"
        text = skill.read_text()
        self.assertIn("$dcss-translation-context", text)
        self.assertIn("exactly one evidence card", text)
        self.assertIn("inventory and reviewed identity sets are equal", text)
        self.assertIn("review_prepare.sh", text)
        self.assertIn("review_final_gate.sh", text)

        adapter = (ROOT / ".pi/APPEND_SYSTEM.md").read_text()
        self.assertIn("/skill:batch-translation-review <task>", adapter)
        self.assertIn("Do not create", adapter)
        self.assertIn("Pi-only copy of the shared Skill", adapter)

        routing = (ROOT / "docs/agent-routing.md").read_text()
        self.assertIn("## Batch Translation Review", routing)
        self.assertIn("`batch-translation-review` skill", routing)
        self.assertIn(
            "| Complete enumerable translation-category or series audit |",
            (ROOT / "AGENTS.md").read_text(),
        )
        self.assertIn(
            "| Complete enumerable translation audit |",
            (ROOT / ".agents/README.md").read_text(),
        )

    def test_plan_review_enforces_minimal_sufficient_design(self) -> None:
        path = ROOT / ".agents/skills/translation-pipeline/SKILL.md"
        text = path.read_text()
        required_fragments = (
            "observable acceptance criteria",
            "explicit non-goals",
            "observed failure",
            "existing mechanism is insufficient",
            "simplest alternative is not viable",
            "design_induced",
            "delete, reuse, narrow, then add",
        )
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_retired_runtime_adapters_are_absent(self) -> None:
        for path in (
            ROOT / "CLAUDE.md",
            ROOT / ".opencode",
            ROOT / ".claude/agents",
            ROOT / ".claude/skills",
            ROOT / ".claude/workflows",
            ROOT / "tools/pi-subagent",
            ROOT / "tools/pi-subagent-guard.mjs",
        ):
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(path.exists())
        self.assertNotIn("External Pi Worker", (ROOT / "CODEX.md").read_text())
        active_config = "\n".join(
            path.read_text()
            for root in (ROOT / ".pi", ROOT / ".codex")
            for path in root.rglob("*")
            if path.is_file() and path.suffix in {".md", ".toml", ".json"}
        )
        self.assertNotIn("opencode-go", active_config.lower())

    def test_legacy_issue_repository_is_not_a_live_dependency(self) -> None:
        paths = (
            ROOT / "README.md",
            ROOT / "docs/issue-tracking.md",
            ROOT / "docs/known-issues-zh.md",
            ROOT / "docs/dual-agent-workflow.md",
            ROOT / ".claude/ORCHESTRATION_STATE.md",
            ROOT / ".agents/skills/translation-pipeline/SKILL.md",
        )
        forbidden = ("DCSS_ISSUES_DIR", "issueFile", "../issues")
        for path in paths:
            text = path.read_text()
            for fragment in forbidden:
                with self.subTest(path=path.relative_to(ROOT), fragment=fragment):
                    self.assertNotIn(fragment, text)

    def test_translation_assets_use_full_repository_paths(self) -> None:
        paths = [
            ROOT / "AGENTS.md",
            ROOT / "docs/translation-architecture.md",
            ROOT / ".agents/policies/asset-ownership.md",
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
        self.assertIn(
            "'0.34.1-zh[0-9]+-[0-9]+-[0-9][0-9][0-9]'",
            workflow,
        )
        self.assertNotIn("'0.34.1-zh*-*-???'", workflow)
        self.assertIn("package-windows-tiles", workflow)
        self.assertIn("name: windows-tiles", workflow)
        self.assertIn("stone_soup-*-tiles-win32.zip", workflow)
        self.assertIn("mac-app-tiles-dmg", workflow)
        self.assertIn("crawl-ref/source/mac-app-zips/*.dmg", workflow)
        self.assertIn("!crawl-ref/source/mac-app-zips/latest.dmg", workflow)
        self.assertIn("release_draft:", workflow)
        self.assertIn("Create verified draft release", workflow)
        self.assertIn("verify_release_artifacts.py", workflow)
        self.assertIn("--draft --verify-tag", workflow)
        self.assertIn("Create draft release once", workflow)
        self.assertIn("Expected 4 release assets", workflow)
        self.assertNotIn("Download Linux package", workflow)
        self.assertNotIn("name: linux-console", workflow)
        self.assertIn("Download macOS package", workflow)
        self.assertIn("name: macos-tiles-app", workflow)
        self.assertIn("中文桌面正式版", workflow)
        self.assertIn("macOS Tiles：ad-hoc 签名 DMG", workflow)
        self.assertIn("xattr -dr com.apple.quarantine", workflow)
        self.assertEqual(7, workflow.count("name: Ensure version info"))
        self.assertEqual(
            7,
            workflow.count(
                "run: bash .claude/scripts/ensure_version_info.sh"
            ),
        )
        self.assertNotIn(
            "git describe 2>/dev/null > crawl-ref/source/util/release_ver",
            workflow,
        )
        release_draft = workflow.split("  release_draft:\n", 1)[1]
        self.assertIn("runs-on: macos-latest", release_draft)
        self.assertNotIn("mapfile", release_draft)
        release_needs = release_draft.split("    permissions:\n", 1)[0]
        self.assertNotIn("- build_linux_console", release_needs)
        self.assertIn("- build_macos_tiles", release_needs)
        self.assertNotIn("gh release upload", workflow)
        self.assertNotIn("gh release edit", workflow)

        make_dry_run = subprocess.run(
            [
                "make",
                "-n",
                "-j1",
                "-C",
                str(ROOT / "crawl-ref/source/mac"),
                "-f",
                "Makefile.app-bundle",
                "tiles-dmg",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        codesign_commands = "\n".join(
            line
            for line in make_dry_run.stdout.splitlines()
            if "codesign" in line
        )
        self.assertIn(
            "codesign --force --deep --sign - --timestamp=none",
            codesign_commands,
        )
        self.assertIn("Dungeon Crawl Stone Soup - Tiles.app", codesign_commands)
        self.assertNotIn(r"Dungeon\ Crawl\ Stone\ Soup", codesign_commands)

    def test_zh_static_tooling_runs_on_linux_and_macos(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        tooling = workflow.split("  zh_tooling_tests:\n", 1)[1].split(
            "\n  zh_ci_gate:", 1
        )[0]
        gate = workflow.split("  zh_ci_gate:\n", 1)[1].split(
            "\n  zh_runtime_catch2:", 1
        )[0]
        for job in (tooling, gate):
            self.assertIn("os: [ubuntu-latest, macos-latest]", job)
            self.assertIn("runs-on: ${{ matrix.os }}", job)
            self.assertIn("uses: actions/setup-python@v4", job)
        self.assertIn("uses: actions/setup-node@v4", tooling)
        self.assertIn(
            "run: /bin/bash .claude/scripts/tests/run_all.sh", tooling
        )
        self.assertIn(
            "run: /bin/bash .claude/scripts/verify_zh.sh --profile ci", gate
        )

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
