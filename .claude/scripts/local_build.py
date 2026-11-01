#!/usr/bin/env python3
"""Run the workflow's PR build steps locally and optionally publish exact-SHA statuses."""
from __future__ import annotations

import argparse
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
import fcntl
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone

import yaml

TARGETS = {
    "linux": ("build_linux_console", "linux-console", "linux-console", (
        "Ensure version info", "Build Linux console")),
    "windows": ("build_windows_tiles", "mingw-tiles", "windows-tiles", (
        "Ensure version info", "Build Windows tiles")),
    "android": ("build_android", "android-tiles", "android-buildtest", (
        "Ensure version info", "Prepare Android build",
        "Run Android launcher unit tests", "Build Android arm64 PR APK")),
}
DESCRIPTION = "Equivalent PR build passed for "


class BuildError(RuntimeError):
    pass


def output(args, cwd=None, env=None):
    result = subprocess.run(args, cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        # Arguments/env may contain authentication configuration: don't echo it.
        raise BuildError(f"{Path(args[0]).name} failed (exit {result.returncode})")
    return result.stdout.strip()


def git(root, *args):
    return output(["git", "-C", str(root), *args])


def ignored_sources(root):
    """Reject ignored source overrides; allow only existing generated-source paths."""
    ignore = root / "crawl-ref/.gitignore"
    exact = set(re.findall(r"(?m)^/source/([^*\n]+\.(?:h|cc))$",
                           ignore.read_text() if ignore.exists() else ""))
    for name in git(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").split("\0"):
        path = Path(name)
        prefix = "crawl-ref/source/"
        if not name.startswith(prefix) or path.suffix not in {".h", ".cc", ".cpp", ".mk"}:
            continue
        relative = name[len(prefix):]
        generated = relative in exact or re.fullmatch(
            r"(?:rltiles/tiledef-[a-z]+\.(?:h|cc)|rltiles/status-icon-sizes\.h|"
            r"util/levcomp\.(?:tab\.(?:h|cc)|lex\.cc))", relative)
        # Third-party installed headers and Android native outputs are caches,
        # rather than additional source search paths in the core source tree.
        cached = relative.startswith(("contrib/install/", "android-project/app/.cxx/",
                                      "android-project/app/build/"))
        if (not generated and not cached) or (root / name).is_symlink():
            raise BuildError(f"unrecognized ignored source file: {name}")


@dataclass(frozen=True)
class Snapshot:
    head: str
    submodules: tuple


def snapshot(root):
    if git(root, "status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none"):
        raise BuildError(f"worktree must be clean: {root}")
    ignored_sources(root)
    head = git(root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", head):
        raise BuildError("expected a full 40-character commit SHA")
    submodules = []
    for record in git(root, "ls-files", "--stage", "-z").split("\0"):
        if not record.startswith("160000 "):
            continue
        metadata, name = record.split("\t", 1)
        expected = metadata.split()[1]
        child = root / name
        if git(child, "rev-parse", "--show-toplevel") != str(child.resolve()):
            raise BuildError(f"submodule is not initialized: {name}")
        child_state = snapshot(child)
        if child_state.head != expected:
            raise BuildError(f"submodule checkout differs from gitlink: {name}")
        submodules.append((name, child_state))
    return Snapshot(head, tuple(submodules))


def unchanged(root, expected):
    if snapshot(root) != expected:
        raise BuildError(f"HEAD or submodules changed during build: {root}")


def unique(items, predicate, label):
    found = [item for item in items if predicate(item)]
    if len(found) != 1:
        raise BuildError(f"workflow must contain exactly one {label}")
    return found[0]


def pr_value(value):
    """Resolve only the workflow's supported PR-vs-release environment forms."""
    value = str(value)
    if "${{" not in value:
        return value
    ternary = re.fullmatch(
        r"\$\{\{\s*startsWith\(github.ref, 'refs/tags/0\.34\.1-zh'\)"
        r"\s*&&\s*'[^']*'\s*\|\|\s*'([^']*)'\s*\}\}", value)
    if ternary:
        return ternary.group(1)
    release = "${{ (startsWith(github.ref, 'refs/tags/0.34.1-zh') || (startsWith(github.ref, 'refs/tags/') && contains(github.ref_name, '-trunk-'))) }}"
    if value == release:
        return "false"
    raise BuildError("unsupported workflow expression; cannot prove PR equivalence")


def pr_step_applicable(step):
    condition = step.get("if")
    if condition in (None, "${{ github.event_name == 'pull_request' }}"):
        return True
    if condition == "${{ github.event_name != 'pull_request' }}":
        return False
    if pr_value(condition) == "false":
        return False
    raise BuildError("unsupported workflow step condition")


def workflow_plan(root, target):
    workflow = yaml.safe_load((root / ".github/workflows/ci.yml").read_text())
    job_id, _, _, names = TARGETS[target]
    try:
        job = workflow["jobs"][job_id]
        steps = [unique(job["steps"], lambda s: s.get("name") == name, name)
                 for name in names]
    except (KeyError, TypeError) as exc:
        raise BuildError(f"missing workflow build configuration for {target}") from exc
    # Refuse new PR validations rather than silently skipping part of the job.
    for step in job["steps"]:
        if not pr_step_applicable(step):
            continue
        if "uses" in step:
            action = step["uses"].split("@")[0]
            allowed = {"actions/checkout", "actions/setup-python", "actions/setup-java",
                       "gradle/actions/setup-gradle", "actions/upload-artifact"}
            if action not in allowed:
                raise BuildError(f"uncovered PR workflow action: {action}")
            if action == "actions/setup-python" and step.get("with", {}).get("python-version-file") != ".python-version":
                raise BuildError("Python setup no longer reads .python-version")
            if action == "actions/checkout" and any(key in step.get("with", {}) for key in ("ref", "repository", "path")):
                raise BuildError("checkout must use this candidate at the repository root")
            continue
        if step in steps or step.get("name") == "Install build dependencies":
            continue
        if target == "android" and "sdkmanager\" --sdk_root" in step.get("run", ""):
            continue
        raise BuildError(f"uncovered PR workflow command: {step.get('name', '<unnamed>')}")
    positions = [job["steps"].index(step) for step in steps]
    if positions != sorted(positions):
        raise BuildError("workflow build step order changed")
    env = {key: pr_value(value) for key, value in job.get("env", {}).items()}
    for step in steps:
        if step.get("shell") not in (None, "bash"):
            raise BuildError("selected build step requires an unsupported shell")
        if not isinstance(step.get("run"), str) or "${{" in step["run"]:
            raise BuildError("selected build step must have a directly executable run command")
        if step.get("if") not in (None, "${{ github.event_name == 'pull_request' }}"):
            raise BuildError("unsupported build step condition")
        for value in step.get("env", {}).values():
            pr_value(value)
        directory = Path(step.get("working-directory", "."))
        if directory.is_absolute() or ".." in directory.parts:
            raise BuildError("workflow working-directory must stay inside build worktree")
    return job, steps, env


def clean_environment(head):
    # Do not inherit compiler/build switches, Gradle JVM options, shell startup
    # hooks, or secrets into scripts whose CI configuration we are reproducing.
    allowed = {"PATH", "HOME", "USER", "LOGNAME", "TMPDIR", "LANG", "TERM",
               "JAVA_HOME", "ANDROID_HOME", "ANDROID_SDK_ROOT", "GRADLE_USER_HOME",
               "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS",
               "http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY",
               "ZH_ISOLATE_MEMORY_HIGH", "ZH_ISOLATE_MEMORY_MAX",
               "ZH_ISOLATE_CPU_WEIGHT", "ZH_ISOLATE_CPU_QUOTA"}
    env = {key: value for key, value in os.environ.items()
           if key in allowed or key.startswith("LC_")}
    env.update(GITHUB_EVENT_NAME="pull_request", GITHUB_REF="refs/pull/local/head",
               GITHUB_REF_TYPE="branch", GITHUB_REF_NAME="local-pr", GITHUB_SHA=head,
               GITHUB_RUN_NUMBER="1", ANDROID_VARIANT="buildTest")
    if env.get("JAVA_HOME"):
        env["PATH"] = str(Path(env["JAVA_HOME"]) / "bin") + os.pathsep + env.get("PATH", "")
    return env


def require_tool(name, env):
    path = shutil.which(name, path=env.get("PATH"))
    if not path:
        raise BuildError(f"required tool not found: {name}")
    return path


def python_tools(root, env):
    expected = (root / ".python-version").read_text().strip()
    actual = output([require_tool("python3", env), "--version"], env=env)
    if actual != f"Python {expected}":
        raise BuildError(f"workflow requires Python {expected}; configure PATH for build subprocesses")


def android_tools(root, job, env):
    java_step = unique(job["steps"], lambda s: s.get("uses", "").startswith("actions/setup-java@"), "Java setup")
    gradle_step = unique(job["steps"], lambda s: s.get("uses", "").startswith("gradle/actions/setup-gradle@"), "Gradle setup")
    sdk_step = unique(job["steps"], lambda s: "sdkmanager\" --sdk_root" in s.get("run", ""), "SDK setup")
    java_version = str(java_step["with"]["java-version"])
    gradle_version = str(gradle_step["with"]["gradle-version"])
    java = require_tool("java", env)
    result = subprocess.run([java, "-version"], env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    match = re.search(r'version "(\d+)', result.stdout)
    if result.returncode or not match or match.group(1) != java_version:
        raise BuildError(f"workflow requires Java {java_version}; set JAVA_HOME accordingly")
    sdk = env.get("ANDROID_SDK_ROOT") or env.get("ANDROID_HOME")
    if not sdk:
        raise BuildError("set ANDROID_SDK_ROOT to the installed Android SDK")
    packages = re.findall(r'"((?:platforms|build-tools|ndk);[^"\s]+)"', sdk_step["run"])
    if {p.split(";")[0] for p in packages} != {"platforms", "build-tools", "ndk"}:
        raise BuildError("cannot resolve pinned Android SDK requirements from workflow")
    for package in packages:
        directory = Path(sdk).joinpath(*package.split(";"))
        required = {"platforms": "android.jar", "build-tools": "apksigner", "ndk": "ndk-build"}[package.split(";")[0]]
        if not (directory / required).is_file():
            raise BuildError(f"missing Android SDK package: {package}")
    env["ANDROID_SDK_ROOT"] = sdk
    installed = shutil.which("gradle", path=env.get("PATH"))
    if installed:
        version = output([installed, "--version"], env=env)
        if not re.search(r"(?m)^Gradle " + re.escape(gradle_version) + r"\s*$", version):
            raise BuildError(f"workflow requires Gradle {gradle_version}")
        return installed
    project = root / "crawl-ref/source/android-project"
    properties = (project / "gradle/wrapper/gradle-wrapper.properties").read_text()
    if f"/gradle-{gradle_version}-bin.zip" not in properties or not (project / "gradlew").is_file():
        raise BuildError("tracked Gradle wrapper differs from workflow Gradle version")
    return str(project / "gradlew")


@contextmanager
def build_lock(common, name):
    with (common / f"local-build-{name}.lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise BuildError(f"build worktree already in use: {name}") from exc
        yield


def synchronize(main, head, name):
    destination = main / ".worktrees" / name
    if destination.is_symlink() or destination.resolve() != destination:
        raise BuildError("build worktree path must not be a symlink")
    if destination.exists():
        if (git(destination, "rev-parse", "--show-toplevel") != str(destination)
                or git(destination, "rev-parse", "--path-format=absolute", "--git-common-dir")
                != git(main, "rev-parse", "--path-format=absolute", "--git-common-dir")):
            raise BuildError("destination is not a worktree of this repository")
        attached = subprocess.run(["git", "-C", str(destination), "symbolic-ref", "-q", "HEAD"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if attached.returncode == 0:
            raise BuildError("build worktree must have a detached HEAD")
        snapshot(destination)
        git(destination, "reset", "--hard", head)
    else:
        git(main, "worktree", "add", "--detach", f".worktrees/{name}", head)
    git(destination, "submodule", "update", "--init", "--recursive")
    return destination


def cache_environment(main, target, phase, env):
    profile = {"linux": "console", "windows": "mingw-tiles",
               "android": f"android-tiles/buildTest/{phase}"}[target]
    env = dict(env)
    if shutil.which("ccache", path=env.get("PATH")):
        env.update(CCACHE_DIR=str(main / ".ccache" / profile),
                   CCACHE_TEMPDIR=str(Path(tempfile.gettempdir()) / f"crawl-ccache-{os.getuid()}" / profile),
                   CCACHE_NOREADONLY="1", CCACHE_STATS="1")
        if target == "android":
            env["NDK_CCACHE"] = "ccache"
        Path(env["CCACHE_DIR"]).mkdir(parents=True, exist_ok=True)
        Path(env["CCACHE_TEMPDIR"]).mkdir(parents=True, exist_ok=True)
    return env


def execute_steps(caller, build_root, main, target, steps, env, logs):
    for index, step in enumerate(steps):
        step_env = cache_environment(main, target, "host" if step["name"] == "Prepare Android build" else "ndk", env)
        step_env.update({key: pr_value(value) for key, value in step.get("env", {}).items()})
        directory = build_root / step.get("working-directory", ".")
        if not directory.resolve().is_relative_to(build_root):
            raise BuildError("workflow directory escapes build worktree")
        log = logs / f"{target}-{index + 1}.log"
        print(f"{target}: {step['name']} (log: {log})", flush=True)
        # No xtrace or environment dumping: CI commands can inherit credentials
        # needed by Git without writing them to the build log.
        with log.open("w") as handle:
            handle.write(f"Step: {step['name']}\nWorking-directory: {step.get('working-directory', '.')}\nCommand:\n{step['run']}\n")
            handle.flush()
            # systemd-run starts with the service manager's environment, not
            # subprocess(env=...). Restore the controlled environment *inside*
            # isolation; keep its values out of argv and the persistent log.
            with tempfile.TemporaryDirectory(prefix="local-build-step-") as temporary:
                script = Path(temporary) / "step.sh"
                script.write_text("\n".join(
                    f"export {key}={shlex.quote(value)}" for key, value in step_env.items())
                    + "\n" + step["run"] + "\n")
                script.chmod(0o600)
                bash = require_tool("bash", step_env)
                env_tool = require_tool("env", step_env)
                result = subprocess.run([bash, str(caller / ".claude/scripts/run_isolated.sh"),
                                         env_tool, "-i", bash, "--noprofile", "--norc",
                                         "-e", "-o", "pipefail", str(script)],
                                        cwd=directory, env=step_env,
                                        stdout=handle, stderr=subprocess.STDOUT)
            handle.write(f"\nExit status: {result.returncode}\n")
        if result.returncode:
            raise BuildError(f"{step['name']} failed; see {log}")


def check_artifacts(build_root, job, clear=False):
    """Use the PR upload contract; never accept a stale APK from another build."""
    for step in job["steps"]:
        if not step.get("uses", "").startswith("actions/upload-artifact@") or not pr_step_applicable(step):
            continue
        settings = step.get("with", {})
        if settings.get("if-no-files-found") != "error":
            continue
        patterns = settings.get("path", "").splitlines()
        files = []
        for pattern in patterns:
            path = Path(pattern)
            if not pattern or path.is_absolute() or ".." in path.parts or "${{" in pattern or pattern.startswith("!"):
                raise BuildError("unsupported required PR artifact path")
            for match in build_root.glob(pattern):
                if (match.is_symlink() or not match.is_file() or match.suffix != ".apk"
                        or not match.resolve().is_relative_to(build_root)):
                    raise BuildError("required PR artifact must be a regular APK inside the build worktree")
                files.append(match)
        if clear:
            for path in files:
                path.unlink()
        elif not files:
            raise BuildError("required PR APK was not produced")


def publish(root, head, targets):
    origin = git(root, "remote", "get-url", "origin")
    match = re.fullmatch(r"(?:https://github\.com/|git@github\.com:)([\w.-]+/[\w.-]+?)(?:\.git)?", origin)
    if not match:
        raise BuildError("origin must identify a GitHub repository without embedded credentials")
    repository = match.group(1)
    for target in targets:
        context = "local-build/" + TARGETS[target][2]
        output(["gh", "api", "--method", "POST", f"repos/{repository}/statuses/{head}",
                "-f", "state=success", "-f", f"context={context}",
                "-f", f"description={DESCRIPTION}{head}"], cwd=root)
        print(f"Published {context} for {head}")


def run(root, targets, push=False, publish_status=False):
    before = snapshot(root)
    common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    main = common.parent
    plans = {target: workflow_plan(root, target) for target in targets}
    env = clean_environment(before.head)
    for name in ("bash", "git", "make"):
        require_tool(name, env)
    python_tools(root, env)
    if "linux" in targets:
        for name in ("gcc", "g++"):
            require_tool(name, env)
    if "windows" in targets:
        for name in ("x86_64-w64-mingw32-g++", "x86_64-w64-mingw32-windres"):
            require_tool(name, env)
    target_environments = {target: dict(env, **plans[target][2]) for target in targets}
    gradle = None
    if "android" in targets:
        gradle = android_tools(root, plans["android"][0], target_environments["android"])
    if push:
        branch = git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    if publish_status:
        require_tool("gh", os.environ)
    log_base = root / ".claude/metrics/verify"
    log_base.mkdir(parents=True, exist_ok=True)
    logs = Path(tempfile.mkdtemp(prefix=datetime.now(timezone.utc).strftime("local-build-%Y%m%dT%H%M%SZ-"), dir=log_base))
    with ExitStack() as stack:
        # Lock every selected target before changing either worktree.
        for target in targets:
            stack.enter_context(build_lock(common, TARGETS[target][1]))
        builds = {}
        for target in targets:
            name = TARGETS[target][1]
            if root == main / ".worktrees" / name:
                raise BuildError("candidate must differ from its build worktree")
            destination = synchronize(main, before.head, name)
            state = snapshot(destination)
            if state != before:
                raise BuildError("synchronized build worktree differs from candidate")
            builds[target] = (destination, state)
        unchanged(root, before)
        for target in targets:
            job, steps, _ = plans[target]
            check_artifacts(builds[target][0], job, clear=True)
            target_env = target_environments[target]
            with tempfile.TemporaryDirectory(prefix="local-build-tools-") as temporary:
                if target == "android":
                    wrapper = root / "crawl-ref/source/android-project/gradlew"
                    if gradle == str(wrapper):
                        gradle = str(builds[target][0] / wrapper.relative_to(root))
                    shim = Path(temporary) / "gradle"
                    shim.write_text("#!/bin/sh\nexec " + shlex.quote(gradle) + ' --no-daemon --max-workers=4 "$@"\n')
                    shim.chmod(0o755)
                    target_env["PATH"] = temporary + os.pathsep + target_env["PATH"]
                execute_steps(root, builds[target][0], main, target, steps, target_env, logs)
                check_artifacts(builds[target][0], job)
        unchanged(root, before)
        for destination, state in builds.values():
            unchanged(destination, state)
        if push:
            if git(root, "symbolic-ref", "--quiet", "--short", "HEAD") != branch:
                raise BuildError("current branch changed during build")
            output(["git", "push", "origin", f"{before.head}:refs/heads/{branch}"], cwd=root)
            unchanged(root, before)
        if publish_status:
            publish(root, before.head, targets)
    print(f"Equivalent PR build passed for {before.head}: {', '.join(targets)}")
    return logs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    execute = subparsers.add_parser("run", help="run exact PR build steps from this checkout's workflow")
    execute.add_argument("--target", choices=["linux", "windows", "android", "all"], required=True)
    execute.add_argument("--push", action="store_true", help="push the current branch after all selected builds pass")
    execute.add_argument("--publish", action="store_true", help="publish exact-HEAD success statuses after all selected builds pass")
    args = parser.parse_args()
    try:
        root = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
        targets = list(TARGETS) if args.target == "all" else [args.target]
        run(root, targets, args.push, args.publish)
    except (BuildError, OSError, ValueError, yaml.YAMLError) as exc:
        print(f"local_build: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
