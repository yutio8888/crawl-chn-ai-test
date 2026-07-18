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

## Shared Safety Policy

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
bash .claude/scripts/review_prepare.sh <candidate> <target>
bash .claude/scripts/review_final_gate.sh <candidate> <target>
```

The verification includes export freshness and changed exact-key terminology.
Use `GLOSSARY_DIFF_BASE=<revision>` when the comparison base is not `HEAD`.
The prepare and final-gate commands are orchestrator-owned. Reviewers inspect
only the exact prepared bundle and never execute the review profile themselves.

## Shared Review Contract

<!-- BEGIN GENERATED: review-contract -->
# review-contract-v3

Translation-related review separates domain review from expensive final
verification. A reviewer never runs `verify_zh.sh --profile review` during the
readiness pass; that profile is executed once by `review_final_gate.sh` after
all required reviewers are ready.

## Cost-aware orchestration

Development feedback uses targeted tests and only the profile that matches the
current edit. Do not serially run `translation`, `code`, and `ci` against the
same immutable mixed candidate: when one combined static preflight is useful,
run `ci` once. These development profiles are not schema-v3 final evidence.

Create the immutable bundle and complete routed domain review before running
expensive independent suites such as `run_all.sh`, `help-full`, or
`post_zh_runtime.sh full`. If the task or release contract requires those
suites, run each once only after all reviewers report Ready, against the exact
candidate OID that will enter the final gate. A reviewer-requested fix creates a
new bundle and uses targeted checks during the next feedback loop; do not spend
full-suite evidence on a candidate already known to need changes.

`review_prepare.sh`, routed readiness, `review_final_gate.sh`, and
`review_at_merge.sh` remain separate security boundaries. Their repeated
identity and clean-worktree checks are intentional and must not be removed as
performance optimizations.

## Finding model

- **Blocker**: runtime/functional failure, undefined behaviour, protocol or
  lookup corruption, structural data damage, compilation failure, incomplete
  scope, or an interrupted required verification.
- **Needs Fix**: a definite semantic, terminology, accuracy, completeness, or
  language error without runtime corruption.
- **Suggestion**: a non-required style preference.

Readiness is derived mechanically:

- **Ready for Final Gate**: `blocker == 0` and `needs_fix == 0`.
- **Changes Requested**: `blocker == 0` and `needs_fix > 0`.
- **No-Go**: `blocker > 0` or the reviewer could not complete the exact scope.

Suggestions do not block readiness. Schema-v3 merge authorization has no
Conditional Go: a definite fix is completed before final verification, while
deployment or release conditions are outside the immutable code-review proof.

## Reviewer ownership

- `zh-code-reviewer` owns runtime safety, protocol/display separation,
  extraction and key coverage, format arguments, TextDB structure, borrowed
  translation lifetime, variadic calls, movement phrase routing, English
  morphology, compilation, and scanner warning triage.
- `translation-reviewer` owns EN/ZH semantic parity, current-glossary choices
  in context, facts and numbers, completeness, natural Chinese, terminology
  consistency, and character voice. It reports implementation defects it
  encounters but does not duplicate the code reviewer's primary scope.

For mixed changes, each reviewer stays within that ownership and inspects the
shared context/fallback boundary only where the two domains meet. Neither
reviewer reruns whole-project verification suites during readiness.

The mechanically generated routing for the immutable target/candidate range is
authoritative. Mixed changes require both readiness records; a final evidence
approver cannot replace a missing domain readiness record.

## Immutable readiness

Before review, the candidate changes must be committed and its worktree must be
clean. From the clean target checkout, the orchestrator runs
`review_prepare.sh <candidate> <target>` and gives every reviewer that exact
bundle ID and range; a reviewer returns No-Go if this immutable boundary is
missing or mismatched. The target checkout must remain clean through the final
gate. Each readiness record binds the exact
target head, candidate head, binary diff SHA-256, glossary SHA-256, routing
digest, reviewer role, reviewed scope, and finding counts. Any ref, diff,
glossary, or routing change invalidates the record.

Every finding cites the exact file and line, evidence, impact, and a concrete
fix. Translation findings also include the English source and current Chinese
text. Reviewer identity in local evidence is an audit declaration, not a
cryptographic signature.

## Final evidence

After every required reviewer returns Ready, the orchestrator runs:

`bash .claude/scripts/review_final_gate.sh <candidate> <target>`

The final gate uses the target checkout's trusted control-plane, holds a
bundle-specific lock, and creates a new attempt only when no valid pass exists.
Failed, interrupted, abandoned, incomplete, or tampered attempts never approve
a merge. A valid pass is reused and never rerun for the same bundle.

The final evidence approver inspects the published verification artifacts and
records a final Go bound to the verification digest, routing digest, and every
required readiness digest. `review_at_merge.sh` is a read-only validator: it
does not build, test, create, repair, or update evidence.

Historical schema-v1/v2 records remain metrics only. New merge authorization
is written exclusively as a schema-v3 review bundle; old Conditional Go records
are never converted into a schema-v3 Go.
<!-- END GENERATED: review-contract -->
