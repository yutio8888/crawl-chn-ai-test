# Okapi headless QA adapter

`source_to_xliff.py` converts the project's `source.txt` TextDB format to
bilingual XLIFF 1.2. `run_qa.sh` compiles and runs `OkapiQaRunner` without
starting Rainbow or CheckMate. The runner feeds XLIFF through
`RawDocumentToFilterEventsStep` and `QualityCheckStep`, then writes an XML
report. Terminology is checked separately by `check_terms.py`; Okapi's
SimpleTB terminology step is deliberately disabled. Okapi's C-style printf
pattern is also disabled because the project has a separate formatter-token
checker.

Known TextDB key namespaces such as `status|Fire` are exported as the visible
source `Fire`; the namespace is retained in the XLIFF note as `key-prefix`.
Other pipe-separated UI strings are preserved unchanged.

Example:

```bash
python3 tools/okapi/source_to_xliff.py \
  crawl-ref/source/dat/i18n/zh/source.txt /tmp/dcss-source.xlf

bash tools/okapi/run_qa.sh \
  /tmp/dcss-source.xlf /tmp/dcss-qa.xml \
  docs/glossary.utf8
```

This produces `/tmp/dcss-qa.xml` for Okapi structural checks and
`/tmp/dcss-qa.terms.json` for project-aware terminology checks. The first two
glossary columns are source and target; target alternatives may be separated
by `/`, for example `施法 / 施放 / 咏唱`. The third column can contain
`domain=...` and `context=...` metadata. Use `--domain` directly with
`check_terms.py` for a domain-specific run. This tool does not rewrite TextDB
files and does not replace the project's existing control-token/database-key
checks.
