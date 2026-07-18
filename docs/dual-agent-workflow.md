# Cross-Runtime Collaboration — Codex, OpenCode, and Claude Code

This document defines shared handoff and ownership. Runtime capabilities and
model assignments change over time; read current runtime configuration instead
of treating this document as a model inventory.

## Routing Principles

Choose the runtime and role by the work, not by a permanent claim that one
engine is always “fast” or “deep”:

| Work | Preferred capability |
|---|---|
| High-volume, patterned translation | Translator role with current glossary context and deterministic verification |
| Routine C++ i18n migration | Coder role with compiler/scanner access |
| CJK metrics, hidden UB, or call-chain root cause | Strong cross-file reasoning and focused runtime evidence |
| Translation quality review | Independent translation reviewer |
| i18n implementation review | Independent code reviewer |
| Multi-issue batch | Orchestrator that can enforce one writer per translation asset |

The active session's tools and user instructions determine whether delegation
or parallel work is available. Do not hard-code model versions or concurrency
claims here.

## Collaboration Glue

### Branches identify ownership

- Codex-authored branches use `codex/<topic>` by default.
- OpenCode-authored branches use `<topic>` or `consolidate-*` by default.
- Claude Code uses the branch explicitly assigned by the user or orchestrator.

Branch naming does not replace commit review or attribution.

### State lives on disk

Runtime-private memory is not a cross-runtime handoff mechanism. Record the
following in a shared file:

- active plan, owner, file scope, branch, and commit range in
  `.claude/ORCHESTRATION_STATE.md`; or
- issue-specific analysis and status in the repository described by
  `docs/issue-tracking.md`.

A handoff is incomplete until the receiving runtime can reconstruct the task
from disk without relying on conversation memory.

### Worktrees are shared infrastructure

Every runtime follows `.agents/policies/worktree-policy.md`. OpenCode has an
additional plugin guard, while other runtimes must obey the same relative
`.worktrees/<name>` rule through their shell behavior.

### Authorship is truthful

- OpenCode uses its OpenCode trailer.
- Claude Code uses its Claude trailer.
- Codex and other runtimes do not borrow either identity. They use a declared
  runtime identity when required or omit the co-author trailer.

## Handoff Protocol

### Design or diagnosis → implementation

The handing-off runtime records:

1. objective and non-goals;
2. exact files or modules;
3. root cause and evidence;
4. invariants and risks;
5. branch/worktree and starting commit;
6. required verification.

The implementing runtime confirms file ownership before editing and reports the
resulting commit plus verification evidence back to the same state file.

### Implementation → review

The implementer records the clean candidate branch and commit range. For
translation-related changes, the target checkout runs `review_prepare.sh`; the
prepared bundle's routing decides which reviewers are required. Informal
cross-runtime review cannot replace schema-v3 readiness or final evidence.

## Anti-Patterns

- Routing by stale model names or old assumptions about runtime concurrency.
- Handing off through private memory only.
- Both runtimes editing the same translation asset concurrently.
- Creating worktrees outside `.worktrees/`.
- Claiming another runtime's commit identity.
- Running hosted workflow DSL files with an ordinary Node.js or shell process.
