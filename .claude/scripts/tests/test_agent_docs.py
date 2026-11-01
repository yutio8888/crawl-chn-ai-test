#!/usr/bin/env python3

import copy
import json
import os
import tempfile
import tomllib
from pathlib import Path
import re
import shlex
import subprocess
import unittest
import yaml


ROOT = Path(__file__).resolve().parents[3]

ENTRY_POINTS = [
    ROOT / "AGENTS.md",
    ROOT / "CODEX.md",
    ROOT / "DSH.md",
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
    ROOT / "docs/android-architecture.md",
    ROOT / "docs/dual-agent-workflow.md",
    ROOT / "docs/issue-tracking.md",
    ROOT / "docs/translation-architecture.md",
    ROOT / "docs/zh-testing.md",
]

ARCHIVES = [
    ROOT / "docs/review-recovery-history.md",
]

REFERENCES = [
    ROOT / "docs/README.md",
]

DOCS_TO_LINT = (ENTRY_POINTS + AUTHORITIES + ARCHIVES + REFERENCES
                + [ROOT / "README.md"])

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
                   for path in ENTRY_POINTS + AUTHORITIES + ARCHIVES + REFERENCES
                   if not path.is_file()]
        self.assertEqual([], missing)

    def test_entry_points_remain_thin(self) -> None:
        limits = {
            "AGENTS.md": 220,
            "CODEX.md": 100,
            "DSH.md": 100,
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

    def test_dsh_adapter_is_reference_driven_and_explicitly_experimental(self) -> None:
        text = " ".join((ROOT / "DSH.md").read_text().split())
        for fragment in (
            "experimental, documentation-level adapter",
            "docs/agent-routing.md",
            ".agents/skills/<name>/SKILL.md",
            "context_resolve.sh",
            "sole-writer",
            "not a registered native role",
            "self-check is not an independent approval",
            "translation assets are written sequentially by their single owner",
            "run_in_background: true",
            "authorized escalation path",
            "do not themselves provide resource isolation",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)
        self.assertIn("| DSH | `DSH.md`", (ROOT / "AGENTS.md").read_text())
        self.assertIn("`DSH.md`", (ROOT / ".agents/README.md").read_text())
        self.assertIn("dsh/<topic>", (ROOT / "docs/dual-agent-workflow.md").read_text())
        self.assertIn("dsh/<topic>", (ROOT / "AGENTS.md").read_text())
        self.assertIn("DSH.md", (ROOT / "README.md").read_text())
        self.assertIn(
            '"DSH.md",',
            (ROOT / ".claude/scripts/check_path_portability.py").read_text(),
        )

    def test_pi_runtime_configuration_is_native_and_guarded(self) -> None:
        settings = json.loads((ROOT / ".pi/settings.json").read_text())
        for key in ("defaultProvider", "defaultModel"):
            self.assertIsInstance(settings[key], str)
            self.assertTrue(settings[key].strip())
        for path in (ROOT / ".codex/agents").glob("*.toml"):
            config = tomllib.loads(path.read_text())
            self.assertEqual(path.stem, config["name"])
            self.assertTrue(config["developer_instructions"].strip())
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
        self.assertIn("classify_reviewers.py", text)
        self.assertNotIn("review_prepare.sh", text)
        self.assertNotIn("review_final_gate.sh", text)
        self.assertNotIn('Agent(subagent_type=', text)
        self.assertNotIn('task(subagent_type=', text)

    def test_batch_translation_review_skill_is_shared_with_pi(self) -> None:
        skill = ROOT / ".agents/skills/batch-translation-review/SKILL.md"
        text = skill.read_text()
        self.assertIn("$dcss-translation-context", text)
        self.assertIn("exactly one evidence card", text)
        self.assertIn("inventory and reviewed identity sets are equal", text)
        self.assertIn("classify_reviewers.py", text)
        self.assertIn("docs/decisions.md", text)
        self.assertNotIn("review_prepare.sh", text)
        self.assertNotIn("review_final_gate.sh", text)

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

    def test_legacy_issue_repository_is_not_a_live_dependency(self) -> None:
        paths = (
            ROOT / "README.md",
            ROOT / "docs/issue-tracking.md",
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

    def test_release_notes_describe_trunk_save_directory(self) -> None:
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        step = next(step for step in workflow["jobs"]["release_draft"]["steps"]
                    if "release-notes.md" in step.get("run", "")
                    and "# DCSS" in step["run"])
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            for tag in ("0.35-trunk-001", "0.34.1-zh5-1-001"):
                env = dict(os.environ, GITHUB_REF_NAME=tag,
                           GITHUB_SHA="a" * 40, RUNNER_TEMP=directory)
                subprocess.run(["bash", "-eu", "-c", step["run"]],
                               env=env, check=True, capture_output=True)
                notes = (Path(directory) / "release-notes.md").read_text()
                windows = next(line for line in notes.splitlines()
                               if line.startswith("- Windows Tiles："))
                if "trunk" in tag:
                    self.assertIn(r"%APPDATA%\crawl-trunk", windows)
                    self.assertNotIn("便携", windows)
                else:
                    self.assertEqual("- Windows Tiles：便携 ZIP，解压后运行 `crawl.exe`。",
                                     windows)

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

        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        jobs = workflow["jobs"]
        self.assertEqual({}, workflow["permissions"])
        for job_id, job in jobs.items():
            expected_permissions = {
                "contents": "write" if job_id == "release_draft" else "read",
            }
            if job_id == "local_builds":
                expected_permissions.update({"statuses": "read", "pull-requests": "read"})
            self.assertEqual(
                expected_permissions,
                job["permissions"],
            )
        required_names = {
            "ZH Tooling Tests (${{ matrix.os }})",
            "ZH CI Gate (static + data, no make, ${{ matrix.os }})",
            "ZH Runtime Catch2 ([zh-translation] + [message-overlay])",
            "ZH Help Runtime Tests (Issue 52)", "Code Linting",
            "Linux Console (GCC)", "Windows Tiles (MinGW64 cross-compile)",
            "Android (buildTest)",
        }
        self.assertTrue(required_names <= {job["name"] for job in jobs.values()})
        release = jobs["release_draft"]
        self.assertEqual({
            "zh_tooling_tests", "zh_ci_gate", "zh_runtime_catch2",
            "zh_runtime_full", "zh_help_runtime", "linting",
            "build_macos_tiles", "build_windows_tiles", "build_android",

        }, set(release["needs"]))
        self.assertEqual({
            "windows-tiles", "macos-tiles-app", "android-release-apk",

        }, {
            step["with"]["name"] for step in release["steps"]
            if step.get("uses", "").startswith("actions/download-artifact@")
        })
        release_run = "\n".join(step.get("run", "") for step in release["steps"])
        self.assertIn("verify_release_artifacts.py", release_run)
        self.assertIn("--draft --verify-tag", release_run)
        self.assertIn("Expected 5 release assets", release_run)
        self.assertNotIn("gh release upload", release_run)
        self.assertNotIn("gh release edit", release_run)
        # PyYAML's YAML 1.1 loader represents the unquoted `on` key as True.
        triggers = workflow[True]
        self.assertIn("0.34.1-zh[0-9]*-[0-9]*-[0-9][0-9][0-9]",
                      triggers["push"]["tags"])

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

    def test_local_build_lookup_preserves_release_dependency_chain(self) -> None:
        workflow = yaml.safe_load((ROOT / ".github/workflows/ci.yml").read_text())
        jobs = workflow["jobs"]
        # A skipped ancestor would propagate to the default success() guard
        # on release_draft even when intermediate builds explicitly continue.
        self.assertNotIn("if", jobs["local_builds"])
        for platform, job_id in (("linux", "build_linux_console"),
                                 ("windows", "build_windows_tiles"),
                                 ("android", "build_android")):
            self.assertEqual("local_builds", jobs[job_id]["needs"])
            self.assertEqual(
                "${{ !cancelled() && needs.local_builds.outputs."
                + platform + " != 'true' }}", jobs[job_id]["if"])

    def test_android_debug_and_release_apks_are_fail_closed(self) -> None:
        def assert_contract(config: dict) -> None:
            jobs = config["jobs"]
            android = jobs["build_android"]
            self.assertEqual("Android (buildTest)", android["name"])

            steps = android["steps"]
            step_by_name = {
                step.get("name"): (index, step)
                for index, step in enumerate(steps)
                if step.get("name")
            }
            test_require_index, test_require = step_by_name[
                "Require Android test signing secrets"
            ]
            test_sign_index, test_sign = step_by_name[
                "Sign Android debug APK for test updates"
            ]
            test_upload_index, test_upload = step_by_name[
                "Upload Android test APK"
            ]
            pr_upload_index, pr_upload = step_by_name[
                "Upload Android PR debug APK"
            ]
            prepare = next(step for step in steps
                           if step.get("name") == "Prepare Android build")
            make_line = next(line for line in prepare["run"].replace("\\\n", " ").splitlines()
                             if line.startswith("make "))
            # Preserve trunk application identity across generated build files.
            self.assertTrue({
                'ANDROID_APPLICATION_ID=$ANDROID_APPLICATION_ID',
                'ANDROID_APP_NAME=$ANDROID_APP_NAME',
            } <= set(shlex.split(make_line)))
            build_index = next(
                index
                for index, step in enumerate(steps)
                if ":app:assembleDebug" in step.get("run", "")
            )
            validate_index = next(
                index
                for index, step in enumerate(steps)
                if "check_android_pcre_apk.sh" in step.get("run", "")
            )
            self.assertLess(test_require_index, build_index)
            self.assertLess(build_index, validate_index)
            self.assertLess(validate_index, test_sign_index)
            self.assertLess(test_sign_index, test_upload_index)
            for step in (test_require, test_sign):
                self.assertFalse(step.get("continue-on-error", False))
                self.assertIn("set -euo pipefail", step["run"])
            self.assertLess(validate_index, pr_upload_index)

            non_pr = "${{ github.event_name != 'pull_request' }}"
            self.assertEqual(non_pr, test_require["if"])
            self.assertEqual(non_pr, test_sign["if"])
            self.assertEqual(non_pr, test_upload["if"])
            self.assertEqual(
                "${{ github.event_name == 'pull_request' }}",
                pr_upload["if"],
            )
            for secret in (
                "ANDROID_TEST_KEYSTORE_BASE64",
                "ANDROID_TEST_KEYSTORE_PASS",
                "ANDROID_TEST_KEY_ALIAS",
            ):
                self.assertIn(
                    f"missing GitHub Actions secret {secret}",
                    test_require["run"],
                )
                secret_reference = "${{ secrets.%s }}" % secret
                self.assertEqual(
                    secret_reference,
                    test_require["env"][secret],
                )
                self.assertEqual(
                    secret_reference,
                    test_sign["env"][secret],
                )
            self.assertNotIn("base64 --decode", test_require["run"])
            self.assertIn("umask 077", test_sign["run"])
            self.assertIn("base64 --decode", test_sign["run"])
            self.assertIn("trap 'rm -f \"$keystore\"' EXIT", test_sign["run"])
            self.assertIn('--ks "$keystore"', test_sign["run"])
            self.assertIn('"$zipalign" -p -f 4', test_sign["run"])
            self.assertIn('"$apksigner" sign', test_sign["run"])
            self.assertIn(
                "--ks-pass env:ANDROID_TEST_STORE_PASSWORD",
                test_sign["run"],
            )
            self.assertIn(
                "--key-pass env:ANDROID_TEST_PRIVATE_KEY_PASSWORD",
                test_sign["run"],
            )
            self.assertIn(
                '[[ "$cert_digest" == "$ANDROID_TEST_CERT_SHA256" ]]',
                test_sign["run"],
            )
            self.assertRegex(
                android["env"]["ANDROID_TEST_CERT_SHA256"],
                r"^[0-9a-f]{64}$",
            )
            self.assertNotIn("--ks-pass pass:", test_sign["run"])
            self.assertNotIn("--key-pass pass:", test_sign["run"])

            test_upload_with = test_upload["with"]
            self.assertEqual("android-debug-apk", test_upload_with["name"])
            self.assertEqual(
                "crawl-ref/source/android-project/app/build/outputs/apk/"
                "debug/app-debug.apk",
                test_upload_with["path"],
            )
            self.assertEqual("error", test_upload_with["if-no-files-found"])
            pr_upload_with = pr_upload["with"]
            self.assertEqual("android-pr-debug-apk", pr_upload_with["name"])
            self.assertEqual(
                "crawl-ref/source/android-project/app/build/outputs/apk/"
                "buildTest/app-buildTest.apk",
                pr_upload_with["path"],
            )
            self.assertEqual("error", pr_upload_with["if-no-files-found"])

            release_steps = {
                step.get("name"): (index, step)
                for index, step in enumerate(steps)
                if step.get("name")
            }
            require_index, require = release_steps[
                "Require Android release signing secrets"
            ]
            sign_index, sign = release_steps[
                "Build and sign Android release APK"
            ]
            release_validate_index, release_validate = release_steps[
                "Validate release APK PCRE linkage for every Android ABI"
            ]
            release_upload_index, release_upload = release_steps[
                "Upload Android release APK"
            ]
            self.assertLess(require_index, sign_index)
            self.assertLess(sign_index, release_validate_index)
            self.assertLess(release_validate_index, release_upload_index)
            for step in (require, sign, release_validate, release_upload):
                self.assertFalse(step.get("continue-on-error", False))
                if "run" in step:
                    self.assertIn("set -euo pipefail", step["run"])
                self.assertEqual(
                    "${{ (startsWith(github.ref, 'refs/tags/0.34.1-zh') || "
                    "(startsWith(github.ref, 'refs/tags/') && "
                    "contains(github.ref_name, '-trunk-'))) }}",
                    step["if"],
                )

            require_run = require["run"]
            self.assertIn("^0\\.34\\.1-zh[1-9][0-9]*-", require_run)
            self.assertIn("base64 --decode", require_run)
            for secret in (
                "ANDROID_KEYSTORE_BASE64",
                "ANDROID_KEYSTORE_PASS",
                "ANDROID_KEY_ALIAS",
            ):
                self.assertIn(
                    f"missing GitHub Actions secret {secret}", require_run
                )
            sign_run = sign["run"]
            self.assertIn("gradle :app:assembleRelease", sign_run)
            self.assertIn("app-release-unsigned.apk", sign_run)
            self.assertIn(
                "stone_soup-${GITHUB_REF_NAME}-android.apk", sign_run
            )
            self.assertIn('"$zipalign" -p -f 4', sign_run)
            self.assertIn('"$apksigner" sign', sign_run)
            self.assertIn("--ks-pass env:ANDROID_STORE_PASSWORD", sign_run)
            self.assertIn(
                "--key-pass env:ANDROID_PRIVATE_KEY_PASSWORD", sign_run
            )
            self.assertIn(
                '${ANDROID_KEY_PASS:-$ANDROID_KEYSTORE_PASS}', sign_run
            )
            self.assertIn(
                '"$apksigner" verify --verbose --print-certs', sign_run
            )
            self.assertNotIn("--ks-pass pass:", sign_run)
            self.assertNotIn("--key-pass pass:", sign_run)

            release_upload_with = release_upload["with"]
            self.assertEqual(
                "android-release-apk", release_upload_with["name"]
            )
            self.assertEqual(
                "stone_soup-${{ github.ref_name }}-android.apk",
                release_upload_with["path"],
            )
            self.assertEqual(
                "error", release_upload_with["if-no-files-found"]
            )

            release = jobs["release_draft"]
            self.assertIn("build_android", release["needs"])
            release_download = next(
                step
                for step in release["steps"]
                if step.get("name") == "Download Android package"
            )
            self.assertEqual(
                "android-release-apk", release_download["with"]["name"]
            )
            release_gate = next(
                step
                for step in release["steps"]
                if step.get("name")
                == "Validate closed-world release artifact set"
            )
            self.assertIn("--apksigner", release_gate["run"])

        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/ci.yml").read_text()
        )
        assert_contract(workflow)

        wrong_identity = copy.deepcopy(workflow)
        prepare = next(step for step in wrong_identity["jobs"]["build_android"]["steps"]
                       if step.get("name") == "Prepare Android build")
        prepare["run"] = prepare["run"].replace(
            'ANDROID_APPLICATION_ID="$ANDROID_APPLICATION_ID"', '')
        with self.assertRaises(AssertionError):
            assert_contract(wrong_identity)

        wrong_path = copy.deepcopy(workflow)
        android_steps = wrong_path["jobs"]["build_android"]["steps"]
        upload = next(
            step
            for step in android_steps
            if step.get("name") == "Upload Android test APK"
        )
        upload["with"]["path"] += ".missing"
        with self.assertRaises(AssertionError):
            assert_contract(wrong_path)

        unpinned_test_key = copy.deepcopy(workflow)
        test_sign = next(
            step
            for step in unpinned_test_key["jobs"]["build_android"]["steps"]
            if step.get("name")
            == "Sign Android debug APK for test updates"
        )
        test_sign["run"] = test_sign["run"].replace(
            '[[ "$cert_digest" == "$ANDROID_TEST_CERT_SHA256" ]]', ""
        )
        with self.assertRaises(AssertionError):
            assert_contract(unpinned_test_key)

        unsigned = copy.deepcopy(workflow)
        release_sign = next(
            step
            for step in unsigned["jobs"]["build_android"]["steps"]
            if step.get("name") == "Build and sign Android release APK"
        )
        release_sign["run"] = release_sign["run"].replace(
            "--ks-pass env:ANDROID_STORE_PASSWORD", ""
        )
        with self.assertRaises(AssertionError):
            assert_contract(unsigned)

    def test_zh_static_tooling_matrix_is_release_scoped(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        jobs = yaml.safe_load(workflow)["jobs"]
        # Execute only the JavaScript-compatible expression subset used by these
        # matrices. GitHub CI remains the authoritative expression evaluator.
        cases = [
            ("refs/pull/184/merge", ["ubuntu-latest"]),
            ("refs/heads/chn-trunk", ["ubuntu-latest"]),
            ("refs/heads/topic-trunk-test", ["ubuntu-latest"]),
            ("refs/tags/ci-probe", ["ubuntu-latest"]),
            ("refs/tags/0.34.1-zh5-1-013", ["ubuntu-latest", "macos-latest"]),
            ("refs/tags/0.35.0-trunk-013", ["ubuntu-latest", "macos-latest"]),
        ]
        evaluate = r"""
const vm = require('vm'), fs = require('fs');
const input = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = input.cases.map(([ref]) => vm.runInNewContext(input.expression, {
    github: {ref, ref_name: ref.replace(/^refs\/(tags|heads)\//, '')},
    startsWith: (s, p) => s.toLowerCase().startsWith(p.toLowerCase()),
    contains: (s, p) => s.toLowerCase().includes(p.toLowerCase()),
    fromJSON: JSON.parse,
}, {timeout: 1000}));
process.stdout.write(JSON.stringify(results));
"""

        def assert_matrix(matrix):
            match = re.fullmatch(r"\$\{\{\s*(.*?)\s*\}\}", matrix, re.S)
            self.assertIsNotNone(match)
            result = subprocess.run(
                ["node", "-e", evaluate],
                input=json.dumps({"expression": match.group(1), "cases": cases}),
                text=True, capture_output=True, check=True,
            )
            self.assertEqual(json.loads(result.stdout), [os for _, os in cases])

        for job_name in ("zh_tooling_tests", "zh_ci_gate"):
            with self.subTest(job=job_name):
                assert_matrix(jobs[job_name]["strategy"]["matrix"]["os"])
        # Both former unconditional matrices must fail the routing contract.
        for os in (["ubuntu-latest"], ["ubuntu-latest", "macos-latest"]):
            with self.subTest(unconditional=os), self.assertRaises(AssertionError):
                assert_matrix("${{ fromJSON('" + json.dumps(os) + "') }}")

        for script, variable in (("tests/run_all.sh", "SCRIPTS_ROOT"),
                                 ("verify_zh.sh", "SCRIPT_DIR")):
            self.assertIn(
                'export PYTHONPATH="${%s}${PYTHONPATH:+:$PYTHONPATH}"' % variable,
                (ROOT / ".claude/scripts" / script).read_text(),
            )

    def test_ci_has_no_proof_binding_or_control_sha(self) -> None:
        workflow = (ROOT / ".github/workflows/ci.yml").read_text()
        for retired in ("control_sha", "trusted_control",
                        "Prepare trusted verification control checkout",
                        "Build trusted target luac"):
            self.assertNotIn(retired, workflow)

    def test_readme_avoids_volatile_counts_and_legacy_font_contract(self) -> None:
        text = (ROOT / "README.md").read_text()
        for pattern in (r"~30,", r"30,452", r"~93%", r"\*\*活跃开发分支\*\*"):
            self.assertIsNone(re.search(pattern, text))
        self.assertNotIn("必须保留 DejaVu Sans Mono", text)

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

    # ------------------------------------------------------------------
    # Python version single source of truth (.python-version + ci.yml)
    # ------------------------------------------------------------------
    def test_python_version_single_source_of_truth(self) -> None:
        workflow = yaml.safe_load(
            (ROOT / ".github/workflows/ci.yml").read_text()
        )

        def mappings(node):
            """Yield every mapping in the parsed workflow document."""
            if isinstance(node, dict):
                yield node
                for value in node.values():
                    yield from mappings(value)
            elif isinstance(node, list):
                for item in node:
                    yield from mappings(item)

        self.assertEqual(
            [],
            [m for m in mappings(workflow) if "python-version" in m],
            "inline `python-version:` inputs are forbidden; "
            "use python-version-file: .python-version",
        )

        python_command = re.compile(
            r"^(?:sudo\s+)?(?:python3?|[\w./-]+\.py)\b"
        )
        for job_name, job in workflow["jobs"].items():
            steps = job.get("steps") or []
            commands = [
                line.strip()
                for step in steps
                for line in (step.get("run") or "").splitlines()
                if line.strip()
            ]
            setup = [
                step for step in steps
                if step.get("uses", "").startswith("actions/setup-python@")
            ]
            if any(python_command.match(line) for line in commands):
                with self.subTest(job=job_name, contract="one setup-python step"):
                    self.assertEqual(
                        1,
                        len(setup),
                        f"job '{job_name}' directly invokes Python "
                        f"({commands!r}) but has "
                        f"{len(setup)} setup-python step(s)",
                    )
            for step in setup:
                with self.subTest(
                    job=job_name,
                    step=step.get("name") or step.get("uses"),
                    contract="version-file only, no inline version",
                ):
                    self.assertEqual(
                        {"python-version-file": ".python-version"},
                        step.get("with"),
                        f"setup-python step in '{job_name}' must set exactly "
                        "python-version-file: .python-version",
                    )


if __name__ == "__main__":
    unittest.main()
