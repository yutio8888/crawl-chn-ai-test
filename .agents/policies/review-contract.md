# review-contract-v2

All translation-related reviewers use one finding model:

- **Blocker**: runtime/functional failure, undefined behaviour, protocol or
  lookup corruption, structural data damage, compilation failure, or an
  incomplete/interrupted required verification.
- **Needs Fix**: a definite semantic, terminology, accuracy, completeness, or
  language error without runtime corruption.
- **Suggestion**: a non-required style preference.

Verdicts are derived mechanically:

- **Go**: `blocker == 0` and `needs_fix == 0`.
- **Conditional Go**: `blocker == 0` and `needs_fix > 0`, with explicit,
  verifiable conditions.
- **No-Go**: `blocker > 0`, or required verification did not complete.

Reviewer ownership is deliberately non-overlapping:

- `zh-code-reviewer` owns runtime safety, protocol/display separation,
  extraction and key coverage, format arguments, TextDB structure, borrowed
  translation lifetime, variadic calls, movement phrase routing, English
  morphology, compilation, and manual triage of scanner warnings.
- `translation-reviewer` owns EN/ZH semantic parity, current-glossary choices
  in context, facts and numbers, completeness, natural Chinese, terminology
  consistency, and character voice. It does not re-review implementation
  mechanics except to report a code defect it directly encounters.

Both reviewers must resolve the current glossary and report its SHA-256. They
must preserve and link raw verification output, then interpret every relevant
failure or warning against the target diff. Raw results may not be hidden or
rewritten; attaching a log is not a substitute for analysis.

Every finding includes an identifier, severity, exact file and line, evidence,
impact, and a concrete fix. Translation findings also include the EN source and
current ZH text. The final report includes finding counts, verdict, raw log
path, review scope, and glossary SHA-256.

Merge-time reviews additionally emit a schema-v2 record through
`record_review.sh`. The record includes a unique `review_id`, verification
`run_id`, immutable `base`, `head`, and binary `diff_hash`, glossary SHA-256,
raw log path (and metadata path when the run belongs to another worktree), and
non-empty `conditions` for Conditional Go. A verdict is not merge evidence
until `review_at_merge.sh --record-verdict ... <review-id>` validates that
record against a completed `status=pass` run.
