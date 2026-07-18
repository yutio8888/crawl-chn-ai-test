# OpenCode Runtime Adapter

> Status: **runtime adapter**. Read the shared `AGENTS.md` first.

This file contains only OpenCode-specific tool syntax. Shared policies,
routing, build instructions, and review contracts must not be duplicated here.

## Agents

Dispatch project agents with `task`:

```python
task(
  subagent_type="zh-translator",
  description="Translate <target>",
  prompt="<complete task and current context_resolve.sh output>"
)
```

Project-defined types are stored in `.opencode/agents/`. Use the built-in
lowercase `explore` type for read-only searches. Use `general` only when no
specialized role matches. Model assignments are authoritative in the agent
front matter and `.opencode/opencode.json`; do not copy them into prose.

## Skills

Load OpenCode skills with:

```python
skill(name="translation-pipeline")
```

Skill packages live under `.opencode/skills/<name>/SKILL.md`. The shared
terminology and safety policy remains `.agents/skills/dcss-translation-context/`
for Codex and `.agents/policies/` for generated cross-runtime blocks.

## Workflow DSL

OpenCode does not provide a normal `Workflow({...})` call in every runtime.
The files under `.opencode/workflows/` require host-injected DSL globals and
cannot run under ordinary Node.js or a shell.

- If the current host explicitly exposes a compatible workflow runner, pass it
  the required target root, target branch, candidate branch, and issue args.
- Otherwise load `translation-pipeline` and dispatch its phases with `task`.
- Never use `node .opencode/workflows/...` or `bash .opencode/workflows/...`.

## Plugins and Worktrees

`.opencode/plugin/enforce-worktree-path.js` rejects non-relative
`git worktree add` targets outside `.worktrees/`. This is an additional runtime
guard, not a replacement for `.agents/policies/worktree-policy.md`.

The project configuration in `.opencode/opencode.json` also enables the goal
plugin. Treat plugin state and agent models as configuration data, not
documentation that should be mirrored in `AGENTS.md`.

## Compatibility Trees

`.claude/agents/` and `.claude/skills/` are not OpenCode-native, but they remain
supported synchronization/test targets for Claude Code compatibility. Do not
delete them merely because OpenCode does not load them.
