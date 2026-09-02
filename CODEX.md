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
  another runtime's prompt and pretend an unavailable tool exists.
- Use repository skills exposed by Codex. For translation/i18n work, load
  `dcss-translation-context` before editing or review.
- Use `apply_patch` for manual file edits and preserve unrelated worktree
  changes.

Codex-native role prompts live in `.codex/agents/*.toml`. Shared generated
policy blocks inside them come from `.agents/policies/`.

## Translation Pipeline

For an end-to-end translation issue, load the shared `translation-pipeline`
Skill and execute it with Codex's normal collaboration tools. Do not reproduce
its phases in this adapter.

## Worktrees and Branches

Codex shell calls follow `.agents/policies/worktree-policy.md`: create only
relative `.worktrees/<name>` worktrees and use `codex/<topic>` branches by
default. Dedicated detached build worktrees remain governed by
`docs/build-workflow.md`.

## Review and Merge

Code-review answers use findings-first format with exact file/line evidence.
For translation candidates, route domain review with `classify_reviewers.py`
per `.agents/policies/review-contract.md`; merge requires the matching
verification profile, domain review, and GitHub Actions CI.

Use a Codex identity only when the active runtime or user has declared one;
otherwise omit the co-author trailer. Cross-runtime handoff state belongs in
`.claude/ORCHESTRATION_STATE.md` or the issue repository described by
`docs/issue-tracking.md`.
