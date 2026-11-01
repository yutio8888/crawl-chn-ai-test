#!/usr/bin/env python3
"""Exercise local build provenance using real temporary Git worktrees.

The fixture isolation wrapper only execs the requested command; cgroup behavior
is covered by run_isolated.sh's own checks. No compiler or network is invoked.
"""
import contextlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_build as lb

ROOT = Path(__file__).resolve().parents[3]


class LocalBuildTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name) / "repository"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("config", "user.name", "Local build test")
        self.git("config", "user.email", "local-build@example.invalid")
        self.git("config", "protocol.file.allow", "always")
        self.write(".gitignore", ".worktrees/\n.ccache/\n.claude/metrics/verify/\n")
        self.write("crawl-ref/.gitignore", "/source/config.h\n/source/util/*.h\n")
        self.write("crawl-ref/source/tracked.h", "original\n")
        self.write(".claude/scripts/run_isolated.sh", '#!/bin/bash\nexec "$@"\n')
        self.workflow = {"jobs": {}}
        for target, (job_id, _, _, names) in lb.TARGETS.items():
            self.workflow["jobs"][job_id] = {"steps": [{"name": name, "run": "true"} for name in names]}
        self.commit_workflow()
        self.git("checkout", "-qb", "feature/local-build")
        original_tool = lb.require_tool
        self.tools = mock.patch.object(lb, "require_tool", side_effect=lambda name, env: "/bin/true" if name in {"x86_64-w64-mingw32-g++", "x86_64-w64-mingw32-windres", "gh", "java"} else original_tool(name, env))
        self.tools.start()
        self.addCleanup(self.tools.stop)
        self.python = mock.patch.object(lb, "python_tools")
        self.python.start()
        self.addCleanup(self.python.stop)
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()
        self.addCleanup(self.quiet.__exit__, None, None, None)

    def git(self, *args, root=None):
        return subprocess.check_output(["git", "-C", str(root or self.repo), *args],
                                       text=True, stderr=subprocess.DEVNULL).strip()

    def write(self, relative, content):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def commit_workflow(self):
        self.write(".github/workflows/ci.yml", yaml.safe_dump(self.workflow))
        self.git("add", ".")
        self.git("commit", "-qm", "fixture")

    def test_current_workflow_commands_and_pr_identity_are_reused(self):
        for target in lb.TARGETS:
            job, steps, env = lb.workflow_plan(ROOT, target)
            self.assertEqual([s["name"] for s in steps], list(lb.TARGETS[target][3]))
            self.assertIn("--fetch-upstream-tags", steps[0]["run"])
            if target == "linux":
                self.assertEqual(steps[1]["run"].strip(), "make -j4 SAVEDIR='~/.crawl-trunk'")
            elif target == "windows":
                self.assertEqual(lb.pr_value(steps[1]["env"]["RELEASE_PACKAGE"]), "false")
                self.assertIn("CROSSHOST=x86_64-w64-mingw32", steps[1]["run"])
            else:
                self.assertEqual(env["ANDROID_APPLICATION_ID"], "org.develz.crawl.trunk")
                self.assertEqual(env["ANDROID_APP_NAME"], "Dungeon Crawl Stone Soup Trunk")
                self.assertIn('NPROC=4', steps[1]["run"])
                self.assertEqual(steps[2]["run"].strip(), "gradle :app:testDebugUnitTest")
                self.assertEqual(steps[3]["run"].strip(), "gradle :app:assembleBuildTest")

    def test_unknown_expression_or_missing_step_fails_closed(self):
        with self.assertRaises(lb.BuildError):
            lb.pr_value("${{ secrets.SOME_SECRET }}")
        self.workflow["jobs"]["build_windows_tiles"]["steps"].pop()
        self.commit_workflow()
        with self.assertRaises(lb.BuildError):
            lb.workflow_plan(self.repo, "windows")

    def test_new_required_pr_command_and_reordered_steps_fail_closed(self):
        for condition in (None, "${{ github.event_name == 'pull_request' }}", "${{ always() }}"):
            with self.subTest(condition=condition):
                new = {"name": "New required validation", "run": "exit 1"}
                if condition:
                    new["if"] = condition
                job = self.workflow["jobs"]["build_windows_tiles"]
                job["steps"].append(new)
                self.commit_workflow()
                with self.assertRaises(lb.BuildError):
                    lb.workflow_plan(self.repo, "windows")
                job["steps"].pop()
        self.workflow["jobs"]["build_windows_tiles"]["steps"].reverse()
        self.commit_workflow()
        with self.assertRaisesRegex(lb.BuildError, "step order"):
            lb.workflow_plan(self.repo, "windows")

    def test_new_pr_validation_action_fails_closed(self):
        job = self.workflow["jobs"]["build_windows_tiles"]
        job["steps"].append({"uses": "example/extra-validation@v1"})
        self.commit_workflow()
        with self.assertRaisesRegex(lb.BuildError, "uncovered PR workflow action"):
            lb.workflow_plan(self.repo, "windows")

    def test_required_apk_glob_rejects_missing_stale_and_symlink_outputs(self):
        job = {"steps": [{"uses": "actions/upload-artifact@v4", "if": "${{ github.event_name == 'pull_request' }}", "with": {"path": "output/*.apk", "if-no-files-found": "error"}}]}
        with self.assertRaisesRegex(lb.BuildError, "not produced"):
            lb.check_artifacts(self.repo, job)
        artifact = self.repo / "output/fixture.apk"
        artifact.parent.mkdir()
        artifact.write_bytes(b"old")
        lb.check_artifacts(self.repo, job, clear=True)
        self.assertFalse(artifact.exists())
        with self.assertRaises(lb.BuildError):
            lb.check_artifacts(self.repo, job)
        artifact.write_bytes(b"current")
        lb.check_artifacts(self.repo, job)
        artifact.unlink()
        artifact.symlink_to(self.repo / "crawl-ref/source/tracked.h")
        with self.assertRaisesRegex(lb.BuildError, "regular APK"):
            lb.check_artifacts(self.repo, job)

    def test_dirty_or_untracked_candidate_never_builds_or_publishes(self):
        for name in ("crawl-ref/source/tracked.h", "crawl-ref/source/rogue.h"):
            with self.subTest(name=name):
                self.write(name, "dirty\n")
                with mock.patch.object(lb, "synchronize") as sync, mock.patch.object(lb, "publish") as publish:
                    with self.assertRaises(lb.BuildError):
                        lb.run(self.repo, ["windows"], publish_status=True)
                    sync.assert_not_called()
                    publish.assert_not_called()
                if name.endswith("rogue.h"):
                    (self.repo / name).unlink()
                else:
                    self.git("checkout", "--", name)

    def test_install_path_marker_is_ignored_without_ignoring_source_overrides(self):
        # Use the production ignore file, not a duplicate of its new rule.
        self.write("crawl-ref/.gitignore", (ROOT / "crawl-ref/.gitignore").read_text())
        self.commit_workflow()
        before = lb.snapshot(self.repo)
        self.write("crawl-ref/source/.install-path-cflags", '-DSAVE_DIR_PATH="fixture"\n')
        self.assertEqual(lb.snapshot(self.repo), before)
        for name in ("crawl-ref/source/.install-path-cflags.h",
                     "crawl-ref/source/nested/.install-path-cflags"):
            with self.subTest(name=name):
                self.write(name, "untracked source or unrelated marker\n")
                with self.assertRaisesRegex(lb.BuildError, "worktree must be clean"):
                    lb.snapshot(self.repo)
                (self.repo / name).unlink()

    def test_unknown_ignored_header_rejected_but_known_generated_header_allowed(self):
        self.write("crawl-ref/source/config.h", "generated\n")
        lb.snapshot(self.repo)
        self.write("crawl-ref/source/util/rogue.h", "override\n")
        with self.assertRaisesRegex(lb.BuildError, "ignored source"):
            lb.snapshot(self.repo)

    def test_success_uses_detached_fixed_worktree_without_moving_main_head(self):
        head = self.git("rev-parse", "HEAD")
        lb.run(self.repo, ["windows"])
        build = self.repo / ".worktrees/mingw-tiles"
        self.assertEqual(self.git("rev-parse", "HEAD", root=build), head)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)
        self.assertEqual(self.git("symbolic-ref", "--short", "HEAD"), "feature/local-build")
        self.assertTrue(list((self.repo / ".claude/metrics/verify").glob("local-build-*/windows-2.log")))

    def test_dirty_build_worktree_or_attached_head_refuses_sync(self):
        head = self.git("rev-parse", "HEAD")
        build = lb.synchronize(self.repo, head, "mingw-tiles")
        (build / "untracked.h").write_text("unsafe\n")
        with self.assertRaises(lb.BuildError):
            lb.synchronize(self.repo, head, "mingw-tiles")
        self.assertTrue((build / "untracked.h").exists())
        (build / "untracked.h").unlink()
        self.git("checkout", "-qb", "build-owned-branch", root=build)
        with self.assertRaisesRegex(lb.BuildError, "detached"):
            lb.synchronize(self.repo, head, "mingw-tiles")

    def test_submodule_checkout_and_dirty_content_are_checked(self):
        child = Path(self.temporary.name) / "child"
        child.mkdir()
        self.git("init", "-q", root=child)
        self.git("config", "user.name", "Child", root=child)
        self.git("config", "user.email", "child@example.invalid", root=child)
        (child / "file").write_text("one\n")
        self.git("add", ".", root=child)
        self.git("commit", "-qm", "one", root=child)
        self.git("-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child), "module")
        self.git("commit", "-qam", "submodule")
        lb.snapshot(self.repo)
        module = self.repo / "module"
        (module / "file").write_text("dirty\n")
        with self.assertRaises(lb.BuildError):
            lb.snapshot(self.repo)
        self.git("checkout", "--", "file", root=module)
        self.git("-c", "user.name=Child", "-c", "user.email=child@example.invalid",
                 "commit", "--allow-empty", "-qm", "different", root=module)
        with self.assertRaises(lb.BuildError):
            lb.snapshot(self.repo)

    def test_failure_of_any_target_does_not_push_or_publish(self):
        self.workflow["jobs"]["build_android"]["steps"][-1]["run"] = "exit 17"
        self.commit_workflow()
        with mock.patch.object(lb, "android_tools", return_value="/bin/true"), mock.patch.object(lb, "publish") as publish, mock.patch.object(lb, "output", wraps=lb.output) as command:
            with self.assertRaisesRegex(lb.BuildError, "failed; see"):
                lb.run(self.repo, ["windows", "android"], push=True, publish_status=True)
            publish.assert_not_called()
            self.assertFalse(any(call.args[0][:2] == ["git", "push"] for call in command.call_args_list))

    def test_post_build_dirty_or_head_change_cannot_publish(self):
        for command in ('echo changed > crawl-ref/source/tracked.h',
                        'git -c user.name=Test -c user.email=test@example.invalid commit --allow-empty -qm changed',
                        'echo override > untracked.h'):
            with self.subTest(command=command):
                build = self.repo / ".worktrees/mingw-tiles"
                if build.exists():
                    self.git("reset", "--hard", self.git("rev-parse", "HEAD"), root=build)
                    for path in (build / "untracked.h",):
                        path.unlink(missing_ok=True)
                self.workflow["jobs"]["build_windows_tiles"]["steps"][-1]["run"] = command
                self.commit_workflow()
                with mock.patch.object(lb, "publish") as publish:
                    with self.assertRaises(lb.BuildError):
                        lb.run(self.repo, ["windows"], publish_status=True)
                    publish.assert_not_called()

    def test_candidate_mutation_during_build_cannot_publish(self):
        def mutate(*args):
            self.write("crawl-ref/source/tracked.h", "changed\n")
        with mock.patch.object(lb, "execute_steps", side_effect=mutate), mock.patch.object(lb, "publish") as publish:
            with self.assertRaises(lb.BuildError):
                lb.run(self.repo, ["windows"], publish_status=True)
            publish.assert_not_called()

    def test_publish_exact_sha_context_and_fixed_description(self):
        self.git("remote", "add", "origin", "https://github.com/example/project.git")
        head = self.git("rev-parse", "HEAD")
        with mock.patch.object(lb, "output", wraps=lb.output) as command:
            command.side_effect = lambda args, **kw: "https://github.com/example/project.git" if args[0] == "git" else "{}"
            lb.publish(self.repo, head, ["windows", "android"])
        posts = [c.args[0] for c in command.call_args_list if c.args[0][0] == "gh"]
        self.assertEqual(len(posts), 2)
        self.assertIn(f"repos/example/project/statuses/{head}", posts[0])
        self.assertIn("context=local-build/windows-tiles", posts[0])
        self.assertIn("context=local-build/android-buildtest", posts[1])
        self.assertIn(f"description={lb.DESCRIPTION}{head}", posts[0])

    def test_missing_compiler_fails_before_worktree_changes(self):
        self.tools.stop()
        with mock.patch.object(lb.shutil, "which", return_value=None), mock.patch.object(lb, "synchronize") as sync:
            with self.assertRaisesRegex(lb.BuildError, "required tool"):
                lb.run(self.repo, ["windows"])
            sync.assert_not_called()

    def test_isolation_restores_controlled_environment_without_logging_values(self):
        self.write(".claude/scripts/run_isolated.sh", '#!/bin/bash\nexec /usr/bin/env -i "$@"\n')
        self.workflow["jobs"]["build_linux_console"]["steps"][-1]["run"] = 'test "$GITHUB_EVENT_NAME" = pull_request; test "$PYTHON_MARKER" = preserved; test -z "${CXXFLAGS:-}"'
        self.commit_workflow()
        # This PATH fixture is passed through the same production export path;
        # fake cgroup transport deliberately discards its incoming environment.
        self.tools.stop()
        env = lb.clean_environment("a" * 40)
        env["PYTHON_MARKER"] = "preserved"
        job, steps, _ = lb.workflow_plan(self.repo, "linux")
        log = Path(self.temporary.name) / "logs"
        log.mkdir()
        lb.execute_steps(self.repo, self.repo, self.repo, "linux", steps, env, log)
        for path in log.glob("*.log"):
            self.assertNotIn("export PYTHON_MARKER", path.read_text())
            self.assertIn("Exit status: 0", path.read_text())

    def test_python_requirement_checks_path_subprocess_instead_of_runner(self):
        self.python.stop()
        self.write(".python-version", "3.13.14\n")
        with mock.patch.object(lb, "require_tool", return_value="/configured/bin/python3"), mock.patch.object(lb, "output", return_value="Python 3.11.2"):
            with self.assertRaisesRegex(lb.BuildError, "Python 3.13.14"):
                lb.python_tools(self.repo, {"PATH": "/configured/bin"})
        with mock.patch.object(lb, "require_tool", return_value="/configured/bin/python3"), mock.patch.object(lb, "output", return_value="Python 3.13.14") as command:
            lb.python_tools(self.repo, {"PATH": "/configured/bin"})
            self.assertEqual(command.call_args.kwargs["env"]["PATH"], "/configured/bin")

    def test_linux_uses_own_detached_worktree_and_console_cache(self):
        with mock.patch.object(lb, "execute_steps", wraps=lb.execute_steps) as execute:
            lb.run(self.repo, ["linux"])
        build = self.repo / ".worktrees/linux-console"
        self.assertTrue(build.exists())
        self.assertEqual(execute.call_args.args[1], build)
        env = lb.cache_environment(self.repo, "linux", "host", {"PATH": os.environ["PATH"]})
        if "CCACHE_DIR" in env:
            self.assertEqual(env["CCACHE_DIR"], str(self.repo / ".ccache/console"))

    def test_android_missing_sdk_is_rejected_before_build(self):
        job, _, _ = lb.workflow_plan(ROOT, "android")
        java = next(s["with"]["java-version"] for s in job["steps"] if s.get("uses", "").startswith("actions/setup-java@"))
        completed = subprocess.CompletedProcess([], 0, f'openjdk version "{java}.0.0"')
        with mock.patch.object(lb.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(lb.BuildError, "ANDROID_SDK_ROOT"):
                lb.android_tools(self.repo, job, {"PATH": os.environ["PATH"]})
        sdk = Path(self.temporary.name) / "sdk"
        with mock.patch.object(lb.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(lb.BuildError, "missing Android SDK package"):
                lb.android_tools(self.repo, job, {"PATH": os.environ["PATH"], "ANDROID_SDK_ROOT": str(sdk)})

    def test_all_targets_finish_before_push_and_publication(self):
        events = []
        head = self.git("rev-parse", "HEAD")
        original = lb.output
        original_execute = lb.execute_steps
        def command(args, **kwargs):
            if args[:2] == ["git", "push"]:
                events.append("push")
                self.assertEqual(args[-1], f"{head}:refs/heads/feature/local-build")
                return ""
            return original(args, **kwargs)
        def execute(*args):
            events.append(args[3])
            return original_execute(*args)
        with mock.patch.object(lb, "android_tools", return_value="/bin/true"), mock.patch.object(lb, "execute_steps", side_effect=execute), mock.patch.object(lb, "output", side_effect=command), mock.patch.object(lb, "publish", side_effect=lambda root, head, targets: events.append("publish")):
            lb.run(self.repo, list(lb.TARGETS), push=True, publish_status=True)
        self.assertEqual(events, ["linux", "windows", "android", "push", "publish"])

    def test_lock_prevents_concurrent_build(self):
        common = self.repo / ".git"
        with lb.build_lock(common, "mingw-tiles"):
            with self.assertRaisesRegex(lb.BuildError, "already in use"):
                lb.run(self.repo, ["windows"])

    def test_build_switches_and_secrets_do_not_enter_build_environment(self):
        with mock.patch.dict(os.environ, {"CXXFLAGS": "-DUNTESTED", "MAKEFLAGS": "-j128", "GH_TOKEN": "secret", "BASH_ENV": "/untrusted", "JAVA_HOME": "/jdk", "ZH_ISOLATE_MEMORY_MAX": "6G", "XDG_RUNTIME_DIR": "/run/user/test", "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/test/bus"}):
            env = lb.clean_environment("a" * 40)
        self.assertEqual(env["GITHUB_EVENT_NAME"], "pull_request")
        self.assertEqual(env["ANDROID_VARIANT"], "buildTest")
        self.assertEqual(env["ZH_ISOLATE_MEMORY_MAX"], "6G")
        self.assertEqual(env["XDG_RUNTIME_DIR"], "/run/user/test")
        self.assertIn("DBUS_SESSION_BUS_ADDRESS", env)
        self.assertTrue(env["PATH"].startswith("/jdk/bin"))
        for key in ("CXXFLAGS", "MAKEFLAGS", "GH_TOKEN", "BASH_ENV"):
            self.assertNotIn(key, env)


if __name__ == "__main__":
    unittest.main()
