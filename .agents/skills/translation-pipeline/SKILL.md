---
name: translation-pipeline
description: Run the end-to-end DCSS Chinese translation bug workflow with repository reuse, frozen acceptance criteria, single-writer asset ownership, mechanically routed review, and existing final evidence. Use for reported untranslated text, translation errors, protocol leaks, TextDB gaps, or mixed translation-and-code fixes that span analysis through review.
---

# DCSS Translation Pipeline

Use this Skill for an end-to-end translation bug. For a simple wording edit,
route directly to the matching writer or reviewer in `docs/agent-routing.md`.

## Load Context and Investigate

1. Load `$dcss-translation-context` and preserve its complete resolver output.
2. Locate the displayed English text and trace its producer, transformations,
   identity consumers, display sink, and fallback path.
3. Inspect the existing scanners, fixtures, tests, and matching
   `verify_zh.sh` profile before proposing changes.
4. Classify the issue with `docs/translation-architecture.md`.

## Freeze the Smallest Sufficient Plan

Record observable acceptance criteria and explicit non-goals. Prefer extending
existing scripts, tests, and verification entry points.

For any new module, schema, persistent state, or directory, identify the
observed failure, why the existing mechanism is insufficient, and why the
simplest alternative is not viable. Without all three, omit the mechanism.

Review the plan once in this order:

1. scope and simplification;
2. coverage inside the acceptance criteria;
3. implementability against real files and commands;
4. internal consistency.

Classify plan issues as `core_gap`, `implementation_gap`, `out_of_scope`, or
`design_induced`. Resolve them by delete, reuse, narrow, then add. Do not expand
the plan for an out-of-scope theoretical risk. If new infrastructure or a
material scope expansion is required, stop and return the decision to the user.

## Execute with Existing Ownership

Follow `.agents/policies/asset-ownership.md` and
`.agents/policies/translation-integrity.md`:

1. assign one writer to every file;
2. complete translator-owned assets first;
3. execute code changes without reopening translator-owned files;
4. run the single matching development profile;
5. commit the candidate and leave its worktree clean.

## Review and Domain Review

Follow `.agents/policies/review-contract.md` and `docs/agent-routing.md`.
Commit the candidate and leave its worktree clean, route reviewers with
`classify_reviewers.py`, and dispatch only the routed domain reviewers.
Reviewers inspect the complete diff; plan non-goals do not excuse defects the
diff introduces.

Merge requires the matching development profile, the routed domain review,
and existing GitHub Actions CI. Do not invent alternative readiness, merge,
lease, recovery, clock, reflog, or persistent-state protocols.

Report changed files, EN-to-ZH decisions, glossary SHA-256, development
verification, reviewer conclusion (Ready or Changes Requested), and merge
status.
