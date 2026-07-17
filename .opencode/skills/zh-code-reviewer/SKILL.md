---
name: zh-code-reviewer
description: Review DCSS Chinese i18n implementation mechanics and runtime safety, distinct from translation wording quality.
---

# zh-code-reviewer Skill

Use `.opencode/agents/zh-code-reviewer.md` for code/i18n implementation review.

<!-- BEGIN GENERATED: review-contract -->
# review-contract-v3

Translation-related review separates domain review from expensive final
verification. A reviewer never runs `verify_zh.sh --profile review` during the
readiness pass; that profile is executed once by `review_final_gate.sh` after
all required reviewers are ready.

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

Resolve current terminology, inspect the exact committed diff and existing
development/targeted logs, and explain every relevant failure or warning. Do
not run the review profile. Report file/line evidence, finding counts,
mechanically derived readiness, immutable bundle id, and glossary hash.
