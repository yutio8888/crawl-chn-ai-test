---
name: zh-code-reviewer
description: Review DCSS Chinese i18n implementation mechanics and runtime safety, distinct from translation wording quality.
---

# zh-code-reviewer Skill

Use `.opencode/agents/zh-code-reviewer.md` for code/i18n implementation review.

<!-- BEGIN GENERATED: review-contract -->
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
<!-- END GENERATED: review-contract -->

<!-- BEGIN GENERATED: i18n-safety -->
# i18n-safety-v2

This policy is the shared safety contract for DCSS Chinese i18n code.

- `T_()` and `C_()` return borrowed pointers that become invalid after
  `i18n_cache_clear()`. Never retain them in static or namespace storage,
  members, persistent containers, aggregates, or callback captures.
- Persistent literal tables use `N_("key")` or
  `NC_("context", "key")`, then translate at the consumption site with the
  matching `T_()` or `C_()`. Copy the result to `std::string` if it crosses a
  statement boundary.
- Never pass a `std::string`, concatenation, ternary promoted to
  `std::string`, or a `std::string`-returning call directly to a printf-style
  variadic `%s` slot. Store it locally and pass `.c_str()`.
- Treat every `CALL_NO_CSTR` scanner warning as requiring manual return-type
  confirmation: `const char *` is safe; `std::string` needs `.c_str()`.
- Never pass translated text to English morphology such as `conj_verb()`.
- Movement phrases remain English internal values until the display sink.
  Translate them with `translated_move_phrase()` and the applicable grammar
  context; update `move_i18n_manifest.json` and require exact-key coverage.
- Keep protocol, lookup, serialization, Lua comparison, and TextDB key values
  in English. Translate only at display boundaries.
- Use `mprf_p` for positional `%n$s` formats and never mix positional and
  sequential placeholders.
- Resolve terminology from the current `docs/glossary.md` immediately before
  work. Do not embed canonical Chinese terms in Agent or Skill configuration.

Configuration checks validate this policy's generated blocks. C++ source
analysis remains the responsibility of `scan_i18n_lifetime.py`,
`scan_varargs_string.py`, and the other code verification gates.
<!-- END GENERATED: i18n-safety -->

Resolve current terminology, inspect the exact diff, run the review profile,
preserve its raw log, and explain every relevant failure or warning. Report
file/line evidence, finding counts, derived verdict, log path, and glossary hash.
