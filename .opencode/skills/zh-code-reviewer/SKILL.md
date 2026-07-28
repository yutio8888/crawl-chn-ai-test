---
name: zh-code-reviewer
description: Review DCSS Chinese i18n implementation mechanics and runtime safety, distinct from translation wording quality.
---

# zh-code-reviewer Skill

Use `.opencode/agents/zh-code-reviewer.md` for code/i18n implementation review.

<!-- BEGIN GENERATED: review-contract -->
# review-contract-v5

Translation-related review separates domain review from expensive final
verification. A reviewer never runs `verify_zh.sh --profile review` during the
readiness pass; that profile is executed once by `review_final_gate.sh` after
all required reviewers are ready.

## Cost-aware orchestration

Development feedback uses targeted tests and only the profile that matches the
current edit. Do not serially run `translation`, `code`, and `ci` against the
same immutable mixed candidate: when one combined static preflight is useful,
run `ci` once. These development profiles are not schema-v4 final evidence.

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
  lookup corruption, structural data damage, compilation failure, failure to
  review the complete prepared diff, an unmet confirmed acceptance criterion
  within that diff, or an interrupted required verification.
- **Needs Fix**: a definite semantic, terminology, accuracy, completeness, or
  language error without runtime corruption.
- **Suggestion**: a non-required style preference.

Readiness is derived mechanically:

- **Ready for Final Gate**: `blocker == 0` and `needs_fix == 0`.
- **Changes Requested**: `blocker == 0` and `needs_fix > 0`.
- **No-Go**: `blocker > 0` or the reviewer could not complete the exact scope.

Suggestions do not block readiness. Schema-v4 merge authorization has no
Conditional Go: a definite fix is completed before final verification, while
deployment or release conditions are outside the immutable code-review proof.

Plan non-goals do not excuse defects introduced by the prepared diff. Reviewers
inspect the complete immutable diff for real runtime, semantic, structural, and
verification defects. A theoretical risk outside the task acceptance criteria
is non-blocking unless the prepared diff creates or materially worsens it.

When proposing a resolution, prefer deleting unnecessary design, reusing
repository mechanisms, and narrowing the commitment, in that order. Add a new
mechanism only when those options are insufficient.

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

The mechanically generated routing-v2 record for the immutable
target/candidate range is authoritative. It uses normalized, sorted, unique
paths and a one-to-one classified-file record whose category and reviewer set
are recomputed before any evidence is accepted. Root-level
`docs/*-review-results.md` ledgers are mixed changes and always require both
reviewers. Mixed changes require both readiness records; a final evidence
approver cannot replace a missing domain readiness record.

## Immutable readiness

Before review, the candidate changes must be committed and its worktree must be
clean. From the clean target checkout, the orchestrator runs
`review_prepare.sh <candidate> <target>` and gives every reviewer that exact
bundle ID and range; a reviewer returns No-Go if this immutable boundary is
missing or mismatched. The target checkout must remain clean through the final
gate. Each readiness record binds the exact
target head, candidate head, binary diff SHA-256, glossary SHA-256, routing
digest, reviewer role, reviewed scope, and the complete structured findings
array. Findings-v2 and readiness-v3 both carry `reviewed_scope`, which must
equal the complete `routing.files` array item for item and in order; a missing,
partial, extended, reordered, duplicated, absolute, or traversing scope is
rejected. Any ref, diff, glossary, or routing change invalidates the record.

Every finding is persisted inside the reviewer's atomic readiness object and
cites a unique id, severity, exact file and line, evidence, impact, and a
concrete fix. Translation-reviewer findings also include the English source and
current Chinese text. The tool derives severity counts and readiness from this
array; callers never supply either value independently. Reviewer identity in
local evidence is an audit declaration, not a cryptographic signature.

## Final evidence

After every required reviewer returns Ready, the orchestrator runs:

`TERM=xterm-256color bash .claude/scripts/review_final_gate.sh <candidate> <target>`

The explicit `TERM` assignment is required for headless or automated runs. A
shell may expose a non-exported fallback such as `TERM=dumb` to interactive
expansion while leaving `TERM` absent from `printenv` and therefore absent from
the final gate's sanitized Python child environment. Ncurses then treats the
terminal type as `unknown`, Crawl exits with code 1, and the `zh-smoke` phase
fails even though the candidate is unrelated to terminal handling. Supplying a
known installed terminal type is environment initialization, not a verification
bypass; all final-gate phases still run and bind the same immutable candidate.
Use the same prefix with `--retry-failed` after correcting this environment.

The final gate uses the target checkout's trusted control-plane, holds a
bundle-specific lock, and creates a new attempt only when no valid pass exists.
Failed, interrupted, abandoned, incomplete, or tampered attempts never approve
a merge. A valid pass is reused and never rerun for the same bundle.

The review profile always runs the independent required `review-ledgers`
phase. Trusted auditor code comes from the target checkout while the validated
candidate root supplies the read-only data. All six strict inventories
(character, god, item, monster, species/background, and world) run regardless
of the changed-file set. Verification-v5 metadata binds each inventory
artifact individually; missing ledger input, incomplete parsing, stale facts,
or an unknown state fails closed.

The final evidence approver inspects the published verification artifacts and
records a final Go bound to the verification digest, routing digest, and every
required readiness digest. `review_at_merge.sh` is a read-only validator: it
does not build, test, create, repair, or update evidence.

Historical schema-v1/v2 log records and schema-v3 bundles remain read-only
metrics only. Routing-v1/readiness-v2 objects found in the v4 directory are
also legacy read-only, including bundles that already contain approval. They
cannot accept new readiness or final evidence and never authorize merge.
New merge authorization is written exclusively as a schema-v4 bundle with
routing-v2, findings-v2, readiness-v3, and verification-v5. Old records are
never upgraded, appended to, copied, or converted into a new Go.

## Temporary owner-authorized recovery bootstrap exception

**Exception ID:** `DCSS-ZH-BOOTSTRAP-2026-07-29`
**Authority:** repository owner and sole project-policy administrator
**Effective date:** 2026-07-29
**Status:** active only until the approved control candidate C is merged

This section is a narrow administrative exception to the legacy read-only
restriction above. It exists only to bootstrap a new continuously authorized
recovery lineage when no already-authorized verification-v5 target can approve
the first control-plane repair.

The exception authorizes new target-era routing-v1, findings-v1,
readiness-v2, and verification-v4 evidence only for these two consecutive
edges:

1. `fa0144cb3729e2fdae70e070946fe89f0b6cec15 → S`
2. the exact approved full OID of S `→ C`

Here, S and C mean the unique final committed candidates selected under the
conditions below. Their full target and candidate OIDs must be recorded in
their newly prepared bundles and in the owner-maintained recovery record.
Changing either candidate invalidates all readiness, final evidence, and
merge-time authorization produced for its previous OID.

### Stage S boundary

S must be a clean committed descendant of
`fa0144cb3729e2fdae70e070946fe89f0b6cec15`. Its complete changed-path set,
computed with rename detection disabled, must be exactly:

- `.claude/scripts/check_consistency.sh`
- `.claude/scripts/tests/test_check_consistency.sh`
- `.claude/scripts/classify_reviewers.py`
- `.claude/scripts/tests/test_classify_reviewers.py`
- `.claude/scripts/verify_zh.sh`
- `.claude/scripts/tests/test_verify_zh.sh`

The existing file modes must be preserved. For every path outside this
six-file set, the target and S trees must have identical path existence, mode,
object type, and object OID. S must not modify review schemas, ledgers,
translation assets, glossary or decision files, policies, runtime agent files,
or any other repository path.

S may contain only the minimum target-root/candidate-root binding, reviewer
routing coverage, rename-preserving changed-file discovery, and their focused
tests described by the approved recovery design.

### Stage C boundary

C must be a clean committed descendant of the exact approved full OID of S.
Before `review_prepare.sh` is run, the repository owner must approve one
normalized, sorted, unique control-plane manifest for C.

The complete `S..C` changed-path set, computed with rename detection disabled,
must equal that manifest exactly. Every path outside the manifest must have
identical path existence, mode, object type, and object OID in S and C.

C is code/control-plane only. It must not change Chinese translation assets,
`docs/glossary.md`, `docs/glossary.utf8`, `docs/decisions.md`, or any root
translation-review ledger. C must install the routing-v2, findings-v2,
readiness-v3, verification-v5, immutable candidate-input, and fail-closed
control plane required for the later content candidate R.

### Required evidence for both edges

For each exceptional edge:

- The target and candidate must be identified by complete Git commit OIDs.
- The target checkout and candidate worktree must be clean.
- The target must be an ancestor of the candidate.
- The glossary SHA-256 resolved from the candidate worktree must be recorded.
- Focused tests and the single exact-bound code development profile must pass
  before formal readiness is recorded.
- The target checkout's own trusted classifier, verifier, final gate, and
  merge-time validator must be used.
- The mechanically routed reviewer set must be exactly one
  `zh-code-reviewer`.
- Because readiness-v2 has no mechanical `reviewed_scope`, the reviewer must
  explicitly declare that every entry in the complete frozen ordered path
  manifest was reviewed. A partial, reordered, extended, duplicated, absolute,
  or traversing scope is No-Go.
- Every routing, readiness, verification, final-approval, and merge-time object
  must be newly produced for that exact edge.
- No historical bundle, readiness, attempt, artifact, approval, or merge
  authorization may be copied, appended to, converted, migrated, or reused.
- A candidate OID, diff, routing, glossary, reviewer set, or frozen-manifest
  change invalidates the complete evidence set and requires a new preparation
  and review.
- Landing is permitted only as an `ff-only` update to the dedicated recovery
  target using the exact candidate OID printed by the merge-time validator.

This exception does not authorize deletion or rewriting of failed evidence. It
does not authorize a non-fast-forward replacement of
`chn-0.34.1-base`, a push, a release, or deployment.

### Expiration

This exception expires immediately and permanently when the approved full OID
of C is merged into the dedicated recovery target.

After expiration:

- all routing-v1, findings-v1, readiness-v2, and verification-v4 objects return
  to legacy read-only status;
- they cannot authorize any additional edge, retry, amended candidate, or
  unrelated merge;
- `C → R` and every later candidate must use routing-v2, findings-v2,
  readiness-v3, verification-v5, the normal final gate, and the normal
  merge-time validator;
- this section remains only as the historical record of the repository owner's
  bounded bootstrap authorization.
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
- Keep protocol, lookup, serialization identities, Lua comparison, and TextDB
  key values in English. The sole localized serialization exception is
  `Note::name` on `NOTE_MESSAGE` records created through `crawl.take_note`:
  consumer tracing proves that value is a display-only snapshot, not an
  identity. It may use the current display language only when the complete
  template and every string parameter translate; otherwise the whole note
  remains English. This snapshot is language-locked, so changing the UI
  language does not retroactively retranslate it. Do not extend the exception
  to other note types or fields without a new consumer audit and policy change.
- When a changed value may serve both identity and display, enumerate its
  producer, every intermediate consumer, and its final sinks. Identity and
  lookup paths use the original value or an English accessor (for example,
  `_god_name_en()`); only display sinks localize it. Cover the real lookup and
  fallback path with a targeted test.
- Use `mprf_p` for positional `%n$s` formats and never mix positional and
  sequential placeholders.
- Resolve terminology from the current `docs/glossary.md` immediately before
  work. Do not embed canonical Chinese terms in Agent or Skill configuration.

Configuration checks validate this policy's generated blocks. C++ source
analysis remains the responsibility of `scan_i18n_lifetime.py`,
`scan_varargs_string.py`, and the other code verification gates.
<!-- END GENERATED: i18n-safety -->

## Shared Verification Authoring

<!-- BEGIN GENERATED: verification-authoring -->
# verification-authoring-v1

This policy applies when an agent writes or reviews a validator, scanner,
deployment check, parser-facing test, or other verification control.

- Enumerate the complete production artifact and its invariants before writing
  the check. Counts alone never prove identity, membership, uniqueness, order,
  content, conservation, or rejection of unknown data.
- Match production semantics for the parser, working directory,
  initialization, locale, environment, and compile/runtime options. Prefer the
  production helper or entry point. If a test must reimplement semantics,
  document the difference and cover it with a strict end-to-end check.
- Exercise the real construction, lookup, fallback, or deployment path. A
  relaxed helper test is insufficient unless a stricter end-to-end test covers
  the behaviour it omits.
- Fail closed when required input is missing, parsing is incomplete, an unknown
  field or state appears, or the complete invariant cannot be evaluated. Expose
  the failure through the validator's existing interface, normally a non-zero
  exit or an existing structured unresolved result. This requirement does not
  introduce a new result protocol, parser, persistent state, distributed
  coordination, recovery mechanism, or general compiler.
- Give every invariant a passing fixture and a minimal negative mutation that
  breaks only that invariant and must be rejected.
- Preserve raw tool evidence. Report the exact command, exit code, blocking
  failure count, relevant warnings, and the reason a failure is or is not
  actionable.

Reviewers reject checks that validate only source tokens or a convenient subset
when the production consumer observes a larger effective artifact.
<!-- END GENERATED: verification-authoring -->

Resolve current terminology, inspect the exact committed diff and existing
development/targeted logs, and explain every relevant failure or warning. Do
not run the review profile. Report file/line evidence, finding counts,
mechanically derived readiness, immutable bundle id, and glossary hash.
