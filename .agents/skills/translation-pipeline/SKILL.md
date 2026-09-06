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
