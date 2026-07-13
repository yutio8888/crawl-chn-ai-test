---
name: dcss-translation-context
description: Load the current DCSS Chinese glossary and enforce terminology checks for translation, i18n code changes, translation reviews, and terminology decisions. Use whenever work touches T_(), C_(), zh/source.txt, ZH TextDB files, translated game text, or docs/glossary.md.
---

# DCSS Translation Context

Use `docs/glossary.md` from the current worktree as the only terminology data
source. Do not rely on remembered terms or copy glossary rows into this Skill.

## Start Every Applicable Task

From the repository root, choose the task type and run:

```bash
bash .claude/scripts/context_resolve.sh "<task description>" \
  --task-type <translate|code|review> --files <target-files>
```

Read and apply the complete output before editing or reviewing. Keep the emitted
glossary SHA-256 and include it in the final report. If `docs/glossary.md` changes
during the task, rerun the command before continuing.

For an ambiguous term, request it explicitly rather than guessing:

```bash
python3 .claude/scripts/glossary_query.py --term "<English term>"
```

Multiple listed target forms are allowed alternatives only when their comments
fit the current context. A new translation decision belongs in
`docs/glossary.md`; regenerate `docs/glossary.utf8` with the project exporter.

## Verify

Run the profile matching the work:

```bash
bash .claude/scripts/verify_zh.sh --profile translation
bash .claude/scripts/verify_zh.sh --profile code
bash .claude/scripts/verify_zh.sh --profile review
```

The verification includes export freshness and changed exact-key terminology.
Use `GLOSSARY_DIFF_BASE=<revision>` when the comparison base is not `HEAD`.
