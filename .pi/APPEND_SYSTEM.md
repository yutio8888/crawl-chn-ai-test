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
```

For every applicable dispatch, run `context_resolve.sh` in the current
worktree first and pass its complete output to the child.

## Workflow Fallback

Pi does not execute the hosted DSL files under `.opencode/workflows/` or
`.claude/workflows/`. Load `translation-pipeline` and reproduce its documented
phases with `subagent` chains or ordinary role dispatches. Never execute those
DSL files with Node.js or a shell.

## Commands and Extensions

- `/goal <goal>` expands the project prompt template for end-to-end work.
- `.pi/extensions/enforce-worktree-path.ts` blocks agent-issued
  `git worktree add` commands whose target is outside relative
  `.worktrees/<name>` paths.
- Run `/reload` after changing project agents, skills, prompts, or extensions.

## Compatibility Trees

`.opencode/`, `.claude/`, and `.codex/` remain supported synchronization and
test targets. Pi configuration supplements them; migration does not authorize
deleting another runtime's compatibility tree.
