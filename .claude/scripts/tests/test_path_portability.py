#!/usr/bin/env python3

from pathlib import Path
import os
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]
CHECKER = ROOT / ".claude/scripts/check_path_portability.py"


class PathPortabilityTests(unittest.TestCase):
    def run_checker(self, root: Path, *paths: str) -> subprocess.CompletedProcess[str]:
        command = ["python3", str(CHECKER), "--root", str(root)]
        for path in paths:
            command.extend(("--path", path))
        return subprocess.run(command, text=True, capture_output=True)

    def test_repository_passes(self) -> None:
        result = self.run_checker(ROOT)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Path portability check passed", result.stdout)

    def test_machine_specific_paths_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "bad.md"
            path.write_text(
                "clone=/home/example/projects/crawl\n"
                "mount=/mnt/x/crawl-release\n"
                "drive=E:\\\\crawl-game\n"
                "issue=~/projects/issues\n",
                encoding="utf-8",
            )
            result = self.run_checker(root, "bad.md")
            self.assertEqual(1, result.returncode)
            self.assertIn("user-home absolute path", result.stderr)
            self.assertIn("WSL drive mount", result.stderr)
            self.assertIn("Windows drive path", result.stderr)
            self.assertIn("home-relative project layout", result.stderr)

    def test_portable_and_system_paths_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "good.md"
            path.write_text(
                "repo=docs/glossary.md\n"
                "artifacts=.artifacts/windows-tiles\n"
                "issues=${DCSS_ISSUES_DIR:-../issues}\n"
                "sdk=${ANDROID_SDK_ROOT:-$HOME/Android}\n"
                "null=/dev/null\n",
                encoding="utf-8",
            )
            result = self.run_checker(root, "good.md")
            self.assertEqual(0, result.returncode, result.stderr)

    def test_ignored_runtime_state_is_not_treated_as_maintained_source(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "-q", str(root)], check=True,
                text=True, capture_output=True,
            )
            (root / ".gitignore").write_text(".opencode/goals/\n", encoding="utf-8")
            state = root / ".opencode/goals/state.json"
            state.parent.mkdir(parents=True)
            state.write_text(
                '{"checkout":"/home/example/projects/private"}\n', encoding="utf-8"
            )
            result = self.run_checker(root)
            self.assertEqual(0, result.returncode, result.stderr)

    def test_context_resolver_is_cwd_independent_and_reports_relative_source(self) -> None:
        script = ROOT / ".claude/scripts/context_resolve.sh"
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    "bash",
                    str(script),
                    "portable path audit",
                    "--task-type",
                    "general",
                    "--files",
                    "docs/glossary.md",
                ],
                cwd=directory,
                text=True,
                capture_output=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Source: `docs/glossary.md`", result.stdout)
        self.assertNotIn(str(ROOT), result.stdout)

    def test_edit_vault_search_is_cwd_independent(self) -> None:
        script = (ROOT / "crawl-ref/source/util/edit_vault").read_text()
        self.assertIn('SOURCE_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)', script)
        self.assertIn('cd "$SOURCE_DIR" || exit 1', script)
        self.assertIn("grep -rHn --include='*.des'", script)
        self.assertIn('"NAME: *$1$" dat', script)

    def test_deployment_defaults_are_repository_relative(self) -> None:
        windows = (ROOT / ".claude/scripts/deploy.sh").read_text()
        android = (ROOT / ".claude/scripts/deploy-android.sh").read_text()
        self.assertIn("DCSS_WINDOWS_DEPLOY_DIR:-$DEPLOY_ROOT/windows-tiles", windows)
        self.assertIn("DCSS_ANDROID_DEPLOY_DIR:-$DEPLOY_ROOT/android", android)
        self.assertNotIn("/mnt/", windows)
        self.assertNotIn("/mnt/", android)
        for script in (windows, android):
            self.assertIn('source "$SCRIPT_DIR/lib/path_utils.sh"', script)
            self.assertIn(
                'dcss_load_repo_path_config "$REPO_ROOT" "${DCSS_PATH_CONFIG:-}"',
                script,
            )
            self.assertIn('DEPLOY_ROOT="${DCSS_DEPLOY_ROOT:-.artifacts}"', script)
            self.assertIn(
                'TARGET="$(dcss_resolve_repo_path "$REPO_ROOT" "$TARGET_INPUT")"',
                script,
            )

    def test_shared_resolver_anchors_relative_paths_at_repository_root(self) -> None:
        library = ROOT / ".claude/scripts/lib/path_utils.sh"
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory) / "clone"
            command = 'source "$1"; dcss_resolve_repo_path "$2" "$3"'
            relative = subprocess.run(
                [
                    "bash", "-c", command, "bash", str(library), str(repo_root),
                    ".artifacts/windows-tiles",
                ],
                text=True,
                capture_output=True,
            )
            absolute = subprocess.run(
                [
                    "bash", "-c", command, "bash", str(library), str(repo_root),
                    "/external/deploy",
                ],
                text=True,
                capture_output=True,
            )
        self.assertEqual(0, relative.returncode, relative.stderr)
        self.assertEqual(
            f"{repo_root}/.artifacts/windows-tiles\n", relative.stdout
        )
        self.assertEqual(0, absolute.returncode, absolute.stderr)
        self.assertEqual("/external/deploy\n", absolute.stdout)

    def test_local_path_config_is_literal_and_environment_wins(self) -> None:
        library = ROOT / ".claude/scripts/lib/path_utils.sh"
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory) / "clone"
            repo_root.mkdir()
            config = repo_root / "paths.conf"
            config.write_text(
                "DCSS_DEPLOY_ROOT=../mounted/releases\n"
                "DCSS_WINDOWS_DEPLOY_DIR=../game files\n",
                encoding="utf-8",
            )
            command = (
                'source "$1"; dcss_load_repo_path_config "$2" "$3"; '
                'printf "%s|%s\\n" "$DCSS_DEPLOY_ROOT" "$DCSS_WINDOWS_DEPLOY_DIR"'
            )
            loaded = subprocess.run(
                ["bash", "-c", command, "bash", str(library), str(repo_root),
                 str(config)],
                text=True,
                capture_output=True,
            )
            environment = os.environ.copy()
            environment["DCSS_DEPLOY_ROOT"] = "../environment-root"
            overridden = subprocess.run(
                ["bash", "-c", command, "bash", str(library), str(repo_root),
                 str(config)],
                env=environment,
                text=True,
                capture_output=True,
            )
        self.assertEqual(0, loaded.returncode, loaded.stderr)
        self.assertEqual("../mounted/releases|../game files\n", loaded.stdout)
        self.assertEqual(0, overridden.returncode, overridden.stderr)
        self.assertEqual("../environment-root|../game files\n", overridden.stdout)

    def test_local_path_config_rejects_unknown_keys_and_missing_explicit_file(self) -> None:
        library = ROOT / ".claude/scripts/lib/path_utils.sh"
        with tempfile.TemporaryDirectory() as directory:
            repo_root = Path(directory) / "clone"
            repo_root.mkdir()
            config = repo_root / "bad.conf"
            config.write_text("UNSUPPORTED_PATH=somewhere\n", encoding="utf-8")
            command = 'source "$1"; dcss_load_repo_path_config "$2" "$3"'
            unknown = subprocess.run(
                ["bash", "-c", command, "bash", str(library), str(repo_root),
                 str(config)],
                text=True,
                capture_output=True,
            )
            missing = subprocess.run(
                ["bash", "-c", command, "bash", str(library), str(repo_root),
                 "missing.conf"],
                text=True,
                capture_output=True,
            )
        self.assertEqual(2, unknown.returncode)
        self.assertIn("unsupported path config key", unknown.stderr)
        self.assertEqual(2, missing.returncode)
        self.assertIn("explicit path config not found", missing.stderr)


if __name__ == "__main__":
    unittest.main()
