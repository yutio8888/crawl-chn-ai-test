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

## Borrowed Translation Lifetime (Mandatory for Code)

`T_()` and `C_()` return borrowed `const char*` pointers into the i18n cache.
They are valid only until `i18n_cache_clear()`, not for the process lifetime.

- Never store their raw return values in function-static or namespace objects,
  members, persistent containers, or callback captures.
- C++ literal tables later consumed through dynamic `T_()` / `C_()` use
  `N_("key")` / `NC_("context", "key")` when no dedicated data-source audit
  covers them. These literal-only markers return stable English text while
  keeping keys visible to `i18n_extract.py`. Translate at the use site with
  matching `T_()` / `C_()`, and copy to `std::string` whenever the value
  crosses a statement or is passed to a printf-style variadic `%s` slot.
- If the same English key needs a different translation in this context, use
  `C_()` and add the context-qualified TextDB entry; do not overwrite the
  unqualified translation.
- Do not send a translated value to English morphology such as `conj_verb()`.

For every C++ task touching `T_()`/`C_()`, run the lifetime gate:

```bash
python3 .claude/scripts/scan_i18n_lifetime.py crawl-ref/source/ --require-parser
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
  --source-txt crawl-ref/source/dat/i18n/zh/source.txt
```

## Verify

Run the profile matching the work:

```bash
bash .claude/scripts/verify_zh.sh --profile translation
bash .claude/scripts/verify_zh.sh --profile code
bash .claude/scripts/verify_zh.sh --profile review
```

The verification includes export freshness and changed exact-key terminology.
Use `GLOSSARY_DIFF_BASE=<revision>` when the comparison base is not `HEAD`.
