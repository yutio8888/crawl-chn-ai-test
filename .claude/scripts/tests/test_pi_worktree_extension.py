#!/usr/bin/env python3

from pathlib import Path
import subprocess
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[3]
MODULE_URI = (ROOT / ".pi/extensions/worktree-policy.mjs").as_uri()


def run_node(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class PiWorktreeExtensionTests(unittest.TestCase):
    def test_pure_policy_helpers(self) -> None:
        script = textwrap.dedent(
            f"""
            import assert from "node:assert/strict";
            import {{
              extractGitWorktreeSegments,
              extractTargetPath,
              isCompliantWorktreeTarget,
              parseWorktreePorcelain,
              relativeWorktreePath,
              validatePiBranch,
              validateWorktreeName,
              worktreeToolCallViolation,
            }} from {MODULE_URI!r};

            assert.equal(relativeWorktreePath("task-1"), ".worktrees/task-1");
            for (const valid of ["a", "task-1", "task_2", "task.3"]) validateWorktreeName(valid);
            for (const invalid of ["", ".", "..", "../x", "a/b", "a\\\\b", "~x", ".hidden"]) {{
              assert.throws(() => validateWorktreeName(invalid));
            }}
            assert.equal(validatePiBranch("pi/task-1"), "pi/task-1");
            for (const invalid of ["task-1", "pi/", "codex/task", "pi/../task"]) {{
              assert.throws(() => validatePiBranch(invalid));
            }}
            assert.equal(isCompliantWorktreeTarget(".worktrees/task"), true);
            for (const invalid of [null, ".worktrees/", ".worktrees/a/b", "/tmp/task", "../task"]) {{
              assert.equal(isCompliantWorktreeTarget(invalid), false);
            }}

            for (const command of [
              "git worktree add -b pi/task .worktrees/task HEAD",
              "(git worktree add --detach .worktrees/task HEAD)",
              "$(git worktree add --detach .worktrees/task HEAD)",
              "`git worktree add --detach .worktrees/task HEAD`",
              "git worktree a''dd --detach .worktrees/task HEAD",
              "git worktree ad\\\\d --detach .worktrees/task HEAD",
              "g''it wo\\\\rktree list",
            ]) {{
              assert.equal(extractGitWorktreeSegments(command).length, 1);
            }}
            const segment = extractGitWorktreeSegments(
              "git worktree add -b pi/task .worktrees/task HEAD"
            )[0];
            assert.equal(extractTargetPath(segment), ".worktrees/task");
            assert.match(
              worktreeToolCallViolation({{
                toolName: "bash",
                input: {{ command: "git worktree add --detach .worktrees/task HEAD" }},
              }}),
              /Blocked direct Git worktree operation/
            );
            assert.match(
              worktreeToolCallViolation({{
                toolName: "subagent",
                input: {{ tasks: [{{ agent: "worker" }}], worktree: true }},
              }}),
              /Blocked pi-subagents worktree:true/
            );
            assert.match(
              worktreeToolCallViolation({{
                toolName: "subagent",
                input: {{ chain: [{{ parallel: [{{ agent: "worker" }}], worktree: true }}] }},
              }}),
              /Blocked pi-subagents worktree:true/
            );
            assert.equal(
              worktreeToolCallViolation({{
                toolName: "subagent",
                input: {{ agent: "worker", cwd: "/repo/.worktrees/task" }},
              }}),
              null
            );

            const records = parseWorktreePorcelain(
              "worktree /repo root\\nHEAD abcdef\\nbranch refs/heads/main\\n\\n" +
              "worktree /repo root/.worktrees/task\\nHEAD 123456\\ndetached\\n"
            );
            assert.equal(records.length, 2);
            assert.equal(records[0].path, "/repo root");
            assert.equal(records[0].branch, "main");
            assert.equal(records[1].detached, true);
            assert.throws(() => parseWorktreePorcelain(""));
            assert.throws(() => parseWorktreePorcelain("HEAD abcdef"));
            """
        )
        result = run_node(script)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_create_list_and_safe_remove_from_linked_checkout(self) -> None:
        script = textwrap.dedent(
            f"""
            import assert from "node:assert/strict";
            import {{ existsSync, mkdtempSync, mkdirSync, realpathSync, rmSync, symlinkSync, writeFileSync }} from "node:fs";
            import os from "node:os";
            import path from "node:path";
            import {{ spawnSync }} from "node:child_process";
            import {{ manageProjectWorktree }} from {MODULE_URI!r};

            const root = mkdtempSync(path.join(os.tmpdir(), "pi-project-worktree-test-"));
            const symlinkRoot = mkdtempSync(path.join(os.tmpdir(), "pi-project-worktree-symlink-test-"));
            const outside = mkdtempSync(path.join(os.tmpdir(), "pi-project-worktree-outside-"));
            const calls = [];
            function git(cwd, args, allowFailure = false) {{
              const result = spawnSync("git", args, {{ cwd, encoding: "utf8" }});
              if (!allowFailure && result.status !== 0) {{
                throw new Error(result.stderr || result.stdout || `git failed: ${{args.join(" ")}}`);
              }}
              return result;
            }}
            const exec = async (command, args, options) => {{
              calls.push({{ command, args: [...args], cwd: options.cwd }});
              const result = spawnSync(command, args, {{ cwd: options.cwd, encoding: "utf8" }});
              return {{ code: result.status ?? 1, stdout: result.stdout ?? "", stderr: result.stderr ?? "" }};
            }};

            try {{
              const canonicalRoot = realpathSync(root);
              git(root, ["init"]);
              git(root, ["config", "user.email", "test@example.invalid"]);
              git(root, ["config", "user.name", "Test"]);
              writeFileSync(path.join(root, "tracked.txt"), "base\\n");
              git(root, ["add", "tracked.txt"]);
              git(root, ["commit", "-m", "base"]);
              const head = git(root, ["rev-parse", "HEAD"]).stdout.trim();

              mkdirSync(path.join(root, ".worktrees"));
              git(root, ["worktree", "add", "--detach", ".worktrees/caller", "HEAD"]);
              const caller = path.join(root, ".worktrees", "caller");
              const context = {{ cwd: caller, exec, signal: undefined }};

              const created = await manageProjectWorktree(
                {{ action: "create", name: "isolated", branch: "pi/isolated" }}, context
              );
              assert.equal(created.cwd, path.join(canonicalRoot, ".worktrees", "isolated"));
              assert.equal(created.worktreePath, ".worktrees/isolated");
              assert.equal(created.head, head);
              const addCall = calls.find((call) => call.args[0] === "worktree" && call.args[1] === "add");
              assert.ok(addCall);
              assert.equal(addCall.cwd, canonicalRoot);
              assert.ok(addCall.args.includes(".worktrees/isolated"));
              assert.equal(addCall.args.some((arg) => path.isAbsolute(arg) && arg.includes("isolated")), false);

              const listed = await manageProjectWorktree({{ action: "list" }}, context);
              assert.equal(listed.mainRoot, canonicalRoot);
              assert.ok(listed.worktrees.some((item) => item.name === "isolated"));

              const removed = await manageProjectWorktree({{ action: "remove", name: "isolated" }}, context);
              assert.equal(removed.retainedBranch, "pi/isolated");
              assert.equal(git(root, ["show-ref", "--verify", "refs/heads/pi/isolated"], true).status, 0);

              const dirty = await manageProjectWorktree(
                {{ action: "create", name: "dirty" }}, context
              );
              writeFileSync(path.join(dirty.cwd, "untracked.txt"), "dirty\\n");
              await assert.rejects(
                manageProjectWorktree({{ action: "remove", name: "dirty" }}, context),
                /must be clean/
              );
              rmSync(path.join(dirty.cwd, "untracked.txt"));
              await manageProjectWorktree({{ action: "remove", name: "dirty" }}, context);
              await assert.rejects(
                manageProjectWorktree({{ action: "remove", name: "caller" }}, context),
                /active Pi session/
              );

              git(symlinkRoot, ["init"]);
              git(symlinkRoot, ["config", "user.email", "test@example.invalid"]);
              git(symlinkRoot, ["config", "user.name", "Test"]);
              writeFileSync(path.join(symlinkRoot, ".gitignore"), ".worktrees\\n");
              writeFileSync(path.join(symlinkRoot, "tracked.txt"), "base\\n");
              git(symlinkRoot, ["add", ".gitignore", "tracked.txt"]);
              git(symlinkRoot, ["commit", "-m", "base"]);
              symlinkSync(outside, path.join(symlinkRoot, ".worktrees"));
              await assert.rejects(
                manageProjectWorktree(
                  {{ action: "create", name: "escape" }},
                  {{ cwd: symlinkRoot, exec, signal: undefined }}
                ),
                /must be a real directory/
              );
              assert.equal(existsSync(path.join(outside, "escape")), false);
            }} finally {{
              rmSync(root, {{ recursive: true, force: true }});
              rmSync(symlinkRoot, {{ recursive: true, force: true }});
              rmSync(outside, {{ recursive: true, force: true }});
            }}
            """
        )
        result = run_node(script)
        self.assertEqual(0, result.returncode, result.stderr)


if __name__ == "__main__":
    unittest.main()
