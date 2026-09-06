---
name: dcss-translation-context
description: Resolve current DCSS Chinese terminology and applicable i18n policies for translated wording, T_()/C_() changes, or ZH TextDB work. Pure tooling or governance work needs only its relevant policy, not terminology lookup.
---

# DCSS Translation Context

Locate affected files before loading context. Use current `docs/glossary.md`
for terminology decisions, not remembered mappings or a copied prompt glossary.

## Resolve and reuse relevant context

When making translation or terminology judgments, run from the repository root:

```bash
bash .claude/scripts/context_resolve.sh "<task description>" \
  --task-type <translate|code|review> --files <target-files>
```

Apply the relevant returned terms in context. Share the output with writers or
reviewers making the same judgments; do not rerun it merely for each dispatch
or edit. Refresh for a changed file scope or relevant terminology/decision.
After any glossary change, refresh the digest used for final translation
evidence; formal translation reports include its SHA-256. Pure structural,
tooling, or governance work does not need a glossary hash.

Use `--terminology yes` when judgment needs terms that automatic detection
cannot recognize; use `--terminology no` for purely structural work. For an
ambiguous term, use `python3 .claude/scripts/glossary_query.py --term "<term>"`.
Alternative target forms apply only where their comments fit. Record new
terminology decisions in the owned glossary/decision files and regenerate
`docs/glossary.utf8` with the existing exporter when the glossary changes.

## Load only applicable policy

- Translation writing: `../../policies/translation-integrity.md` and
  `../../policies/asset-ownership.md`.
- i18n implementation: `../../policies/i18n-safety.md` and ownership.
- Validator/scanner changes: `../../policies/verification-authoring.md`.
- Review: `../../policies/review-contract.md` and the affected domain's policy.

Read only missing relevant sections; generated policy already present in an
active role is sufficient when unchanged. This Skill is context preparation,
not a command to build, commit, or merge. Writers choose checks using
`docs/zh-testing.md`; reviewers inspect existing evidence and report gaps.
