# Pi Runtime Adapter

> Status: **runtime adapter**. Read the shared `AGENTS.md` first.

This file contains only Pi-specific invocation syntax. Shared policies,
routing, build instructions, and review contracts remain authoritative
elsewhere.

## Agents

Project roles are native `pi-subagents` agents under `.pi/agents/`. Discover
the live names before dispatch:

```typescript
subagent({ action: "list" })
```

Dispatch one role with a complete task contract:

```typescript
subagent({
  agent: "crawl-coder",
  task: "<complete task and current context_resolve.sh output>",
  async: true
})
```

Use `zh-translator`, `crawl-coder`, `translation-reviewer`,
`zh-code-reviewer`, and `ocr` according to `docs/agent-routing.md`. Use the
built-in `scout` for read-only exploration. Keep one writer for each owned
path; parallelize analysis and review, not overlapping edits.

`pi-subagents` must be installed in the user's Pi environment. Agent model and
tool assignments are authoritative in `.pi/agents/`; do not copy them into
prose.

## Skills

Pi discovers the shared skills under `.agents/skills/`. Load them on demand:

```text
/skill:dcss-translation-context <task>
/skill:translation-pipeline <task>
/skill:batch-translation-review <task>
```

For every applicable dispatch, run `context_resolve.sh` in the current
worktree first and pass its complete output to the child.

For an enumerable full-category audit, load `batch-translation-review`. Use
`scout` only for read-only evidence discovery and keep one sequential
`zh-translator` writer. Do not create a Pi-only copy of the shared Skill.

## Translation Pipeline

Load the shared `translation-pipeline` Skill and execute it with ordinary Pi
role dispatches; do not restate its phases in this adapter.

## Worktrees

Do not use `pi-subagents` `worktree: true`; its native placement does not meet
this repository's relative-path contract and the project extension blocks it.
Use the project tool instead:

1. Call `project_worktree` with `action: "create"`, a one-component `name`,
   and optionally a new `pi/<topic>` branch. Omit `branch` for detached HEAD.
2. Pass the returned absolute `cwd` to `subagent(...)` without `worktree: true`.
3. Commit or intentionally discard the child changes, then call
   `project_worktree` with `action: "remove"`. Removal refuses dirty or active
   worktrees and retains any task branch.

`project_worktree` discovers the primary checkout, executes Git there with a
relative `.worktrees/<name>` target, and supports `list` for recovery. The
bash guard in `.pi/extensions/enforce-worktree-path.ts` blocks direct
agent-issued Git worktree lifecycle commands; use `project_worktree` instead.

## Commands and Extensions

- `/goal <goal>` expands the project prompt template for end-to-end work.
- Run `/reload` after changing project agents, skills, prompts, or extensions.

## Active Configuration

Shared generated policies target `.pi/agents/` and `.codex/agents/`.
`.claude/scripts/` remains the runtime-neutral project toolchain despite its
historical directory name; it is not part of a runtime adapter.
