---
name: translation-pipeline
description: Diagnose and fix DCSS Chinese translation bugs spanning text, i18n code, and verification. Use for untranslated output, protocol leaks, TextDB gaps, or mixed translation-and-code fixes; use direct translation or review for a simple wording judgment.
---

# DCSS Translation Pipeline

Use the user's requested endpoint: diagnosis, implementation, or merge. This
Skill does not add commit, remote-posting, merge, or release authorization.
Task completion and cleanup follow `AGENTS.md`.

## Investigate the reported behavior

Locate the text and affected files first. Load `$dcss-translation-context` for
relevant safety rules and, when making terminology judgments, current terms.
Reuse unchanged task context. Trace producers, transformations, identity
consumers, display sinks, and fallback only where the affected value uses them.
Consult relevant sections of `docs/translation-architecture.md` and existing
scanners/tests; do not read the entire toolchain before every change.

For inherited terminology decisions, apply the contextual-evidence section of
`.agents/policies/review-contract.md`: keep mandatory context loaded, establish
the source mechanism and independent meaning first, then assess the old ruling's
applicability. Record the applicability verdict and bounded follow-up in the
existing review/decision flow; do not bypass a user-imposed stage boundary.
For example, `You break out of your daze.` ends `DUR_MESMERISED` and clears
beholders; the word `daze` alone does not make it a Dazed recovery message.

## Implement within the acceptance boundary

Record observable acceptance criteria and explicit non-goals at a level suited
to the task. Reuse existing helpers and checks. Routine helper files, local
implementation choices, and necessary corrections within that boundary do not
require another approval. Escalate only unapproved external dependencies,
persistent mechanisms, material scope expansion, or unresolved product choices;
continue independent authorized work while awaiting input.

Follow `.agents/policies/asset-ownership.md` and
`.agents/policies/translation-integrity.md`. Assign one active writer per file,
implement in dependency order, and let the translator update owned assets when
keys, placeholders, or contexts settle. Validate the combined result with
focused checks and one matching development profile from `docs/zh-testing.md`.

## Terminology consumer checklist

When adding or changing a glossary term, list these bounded consumers in the PR
and give a change/keep reason for each: full names and shared short keys; actual
display consumers; descript and database bodies; dynamic arguments and templates;
test expectations; applicability to each maintained line. Use
`context_resolve.sh`, `glossary_query.py`, and `git grep` to trace the affected
term and its consumers; this does not require a repository-wide review.

For example, D-C-113's `ghost` also reaches `MONS_GHOST`, missed in the first
draft, as well as the player-ghost suffix. D-C-114's `mutation` reaches the
`test_zh_help.cc` expected lookup label, whose stale value surfaced only in CI.

## Review and deliver

Follow `.agents/policies/review-contract.md` and `docs/agent-routing.md`.
Ordinary review accepts files or an uncommitted diff; route applicable domains
with `classify_reviewers.py --files <files>`. Fix introduced defects without
expanding the task for optional suggestions. Reuse valid verification results.

For an authorized merge, prepare a clean committed candidate, verify the exact
range with `--base <base> --head <candidate>`, route merge review over that range,
and use existing GitHub Actions CI. Do not add a separate readiness mechanism.

Report implemented behavior or diagnostic findings, material EN-to-ZH decisions
and glossary SHA-256 when applicable, verification, unresolved gaps, and the
requested delivery status. Complete already-authorized steps without asking
again. Review-only work ends with its evidence report, not a commit or build.
