# Cross-Runtime Collaboration — Pi and Codex

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

- Pi-authored branches use `pi/<topic>` by default.
- Codex-authored branches use `codex/<topic>` by default.

Branch naming does not replace commit review or attribution.

### State lives in durable shared artifacts

Runtime-private memory is not a cross-runtime handoff mechanism. Record the
following in the shared authority that owns it:

- issue-specific analysis, status, acceptance criteria, and handoffs in the
  GitHub Issue described by `docs/issue-tracking.md`;
- implementation, exact commit range, code review, and CI evidence in the
  linked pull request; and
- only cross-issue orchestration constraints in `.claude/ORCHESTRATION_STATE.md`.

A handoff is incomplete until the receiving runtime can reconstruct the task
from these durable artifacts without relying on conversation memory.

### Worktrees are shared infrastructure

Both runtimes follow `.agents/policies/worktree-policy.md`. Pi has an
additional extension guard, while Codex obeys the same relative
`.worktrees/<name>` rule through its shell behavior.

### Authorship is truthful

- Pi and Codex use a declared runtime identity when required; otherwise they
  omit the co-author trailer rather than borrowing another identity.

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
resulting commit plus verification evidence back to the same GitHub Issue and
linked pull request.

### Implementation → review

The implementer records the clean candidate branch and commit range. For
translation-related changes, the target checkout runs `review_prepare.sh`; the
prepared bundle's routing decides which reviewers are required. Informal
cross-runtime review cannot replace schema-v4 readiness or final evidence.
