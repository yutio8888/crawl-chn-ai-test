---
name: dcss-translation-context
description: Load the current DCSS Chinese glossary and route the matching terminology, safety, ownership, and review policies. Use whenever work touches T_(), C_(), zh/source.txt, ZH TextDB files, translated game text, docs/glossary.md, or a DCSS Chinese translation review.
---

# DCSS Translation Context

Use `docs/glossary.md` from the current worktree as the only terminology data
source. Do not rely on remembered terms or copy glossary rows into this Skill.

## Resolve Current Context

From the repository root, choose the task type and run:

```bash
bash .claude/scripts/context_resolve.sh "<task description>" \
  --task-type <translate|code|review> --files <target-files>
```

Read and apply the complete output before editing or reviewing. Keep the emitted
glossary SHA-256 and include it in the final report. If `docs/glossary.md`
changes during the task, rerun the command before continuing.

For an ambiguous term, query it instead of guessing:

```bash
python3 .claude/scripts/glossary_query.py --term "<English term>"
```

Multiple target forms are alternatives only when their comments fit the
current context. Record a new translation decision in `docs/glossary.md` and
regenerate `docs/glossary.utf8` with the project exporter.

## Apply Only the Matching Policies

- Translation writing: read `../../policies/translation-integrity.md` and
  `../../policies/asset-ownership.md`.
- C++ or i18n implementation: read `../../policies/i18n-safety.md` and
  `../../policies/asset-ownership.md`. Also read
  `../../policies/verification-authoring.md` when changing a validator or
  scanner.
- Review: read `../../policies/review-contract.md` and the matching translation
  or implementation policy.

Do not load unrelated policy bodies into the task context.

## Verify

Run the single profile matching the work:

```bash
bash .claude/scripts/verify_zh.sh --profile translation
bash .claude/scripts/verify_zh.sh --profile code
```

For a clean committed candidate, route domain review with
`classify_reviewers.py` and merge after GitHub Actions CI passes.
