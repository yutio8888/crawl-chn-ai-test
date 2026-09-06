# Cross-Runtime Collaboration — Pi, Codex, and DSH

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
- DSH-authored branches use `dsh/<topic>` by default; see `DSH.md` for the
  experimental compatibility contract.

Branch naming does not replace commit review or attribution.

### State lives in durable shared artifacts

Runtime-private memory is not a cross-runtime handoff mechanism. Record the
following in the shared authority that owns it:

- issue-specific analysis, status, acceptance criteria, and handoffs in the
  GitHub Issue described by `docs/issue-tracking.md`;
- implementation, exact commit range, code review, and CI evidence in the
  linked pull request; and
- only cross-issue orchestration constraints in `.claude/ORCHESTRATION_STATE.md`.

For an authorized cross-session handoff, the receiving runtime must be able to
reconstruct the task from those artifacts. Ordinary local work does not require
creating or posting a handoff. Existing user authority governs remote comments.

### Worktrees are shared infrastructure

All runtimes follow `.agents/policies/worktree-policy.md`. Pi has an
additional extension guard; Codex and DSH must follow the same relative
`.worktrees/<name>` rule without relying on Pi's guard.

### Authorship is truthful

- Pi, Codex, and DSH use a declared runtime identity when required; otherwise they
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

The implementing runtime uses assigned file ownership and completes the agreed
endpoint. It reports results and verification locally, or to the existing
GitHub Issue/PR when that remote action is authorized. Routine implementation
details within scope do not require another handoff approval.

### Implementation → review

Ordinary review can inspect files or an uncommitted diff. For merge review,
record the clean candidate branch and commit range; route domains with
`classify_reviewers.py` over that range. Merge requires applicable verification
bound with `--base`/`--head` (or valid reused evidence), completed domain review,
and applicable GitHub Actions CI. Role selection does not mandate a subagent
or repeat whole-project verification.
