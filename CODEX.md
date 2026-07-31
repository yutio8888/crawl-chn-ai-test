# CODEX.md — Codex Runtime Adapter

> Status: **runtime adapter**. Shared project rules live in `AGENTS.md` and
> `.agents/`; this file only maps them to Codex capabilities.

Read `AGENTS.md` first. Do not reinterpret this adapter as a second source of
translation, review, build, or worktree policy.

## Tools and Roles

- Use the runtime's configured project agents (`crawl-coder`, `zh-translator`,
  `zh-code-reviewer`, and `translation-reviewer`) when collaboration tools are
  available and delegation is allowed by the active session.
- For read-only exploration, prefer `rg`, `rg --files`, and `git grep` or a
  runtime-provided explorer.
- If a configured role is unavailable, apply its contract inline; do not read
  an OpenCode prompt and pretend an unavailable OpenCode tool exists.
- Use repository skills exposed by Codex. For translation/i18n work, load
  `dcss-translation-context` before editing or review.
- Use `apply_patch` for manual file edits and preserve unrelated worktree
  changes.

## External Pi Worker

A constrained repository worker with file-edit capability is available through:

```bash
tools/pi-subagent "<narrow task with explicit writable paths>"
```

- Use it for repository exploration, symbol and call-chain discovery, focused
  failure analysis, diff review, a second opinion, and narrowly scoped file
  implementation.
- Do not delegate architectural decisions, credential handling, publishing,
  Git operations, destructive actions, or ambiguous repository-wide work.
- Before a write task, inspect the worktree, assign exact writable paths, and
  ensure no other writer owns those paths. Give each invocation one bounded
  task and request exact file/line evidence.
- Treat its report and edits as untrusted work. Codex must inspect the resulting
  diff, preserve unrelated changes, and own all testing and final acceptance.
- The wrapper permits read/search/list/edit/write tools. It rejects shell and
  Git tools, paths outside the repository, `.git`, and its ignored runtime-state
  directory.

Codex-native role prompts live in `.codex/agents/*.toml`. Shared generated
policy blocks inside them come from `.agents/policies/`.

## Translation Pipeline

For an end-to-end translation issue, follow the `translation-pipeline` phases:

```text
Analyze → Plan → Review Plan → Execute → Prepare Review Bundle
→ Mechanically Routed Review → Cross-validate → Final Evidence → Report
```

The workflow JavaScript files are hosted DSL sources, not Node.js programs.
Never invoke `node .opencode/workflows/...` or `node .claude/workflows/...`.
When Codex has no compatible hosted runner, use its normal collaboration tools
to reproduce the skill's phases and preserve single-writer ownership.

## Worktrees and Branches

- Create worktrees only as relative `.worktrees/<name>` paths from the repo
  root.
- Use `codex/<topic>` for Codex-authored branches by default.
- The OpenCode path-enforcement plugin does not enforce Codex shell calls;
  follow `.agents/policies/worktree-policy.md` explicitly.
- Do not use destructive synchronization in a development worktree. Dedicated
  detached build worktrees are governed by `docs/build-workflow.md`.

## Review and Merge

Code-review answers use findings-first format with exact file/line evidence.
For translation candidates, use the schema-v4 process in
`.agents/policies/review-contract.md`; do not substitute an informal review for
mechanical routing or final evidence.

Codex must not add OpenCode or Claude attribution to Codex-authored changes.
Use a Codex identity only when the active runtime or user has declared one;
otherwise omit the co-author trailer. Cross-runtime handoff state belongs in
`.claude/ORCHESTRATION_STATE.md` or the issue repository described by
`docs/issue-tracking.md`.
