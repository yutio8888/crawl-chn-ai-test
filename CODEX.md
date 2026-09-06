# CODEX.md — Codex Runtime Adapter

> Status: **runtime adapter**. Shared project rules live in `AGENTS.md` and
> `.agents/`; this file only maps them to Codex capabilities.

Read `AGENTS.md` first. Do not reinterpret this adapter as a second source of
translation, review, build, or worktree policy.

## Tools and Roles

- Use the runtime's configured project agents (`crawl-coder`, `zh-translator`,
  `zh-code-reviewer`, and `translation-reviewer`) when collaboration tools are
  available and delegation is allowed by the active session.
- If a configured role is unavailable, apply its contract inline; do not read
  another runtime's prompt and pretend an unavailable tool exists.
- Use repository skills exposed by Codex when their task trigger applies.
  Reuse current context already loaded by the session or role.

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

Use `.agents/policies/review-contract.md` for ordinary versus merge review.
Role routing selects expertise; it does not require delegation or all i18n
checks for a governance-only diff. Task completion and existing authorization
follow `AGENTS.md`.

Use a Codex identity only when the active runtime or user has declared one;
otherwise omit the co-author trailer. For an authorized cross-session handoff,
issue-specific state belongs in the existing Issue/PR described by
`docs/issue-tracking.md`; only cross-issue constraints belong in
`.claude/ORCHESTRATION_STATE.md`.
