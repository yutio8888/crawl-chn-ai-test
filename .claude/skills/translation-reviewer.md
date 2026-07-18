---
name: translation-reviewer
description: Review DCSS Chinese translation semantics and language quality, distinct from implementation mechanics.
argument-hint: "[commit-ish or leave empty for current diff]"
---

# translation-reviewer Skill

Use `.claude/agents/translation-reviewer.md` for content-quality review.

<!-- BEGIN GENERATED: review-contract -->
# review-contract-v4

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
  lookup corruption, structural data damage, compilation failure, incomplete
  scope, or an interrupted required verification.
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
digest, reviewer role, reviewed scope, and the complete structured findings
array. Any ref, diff,
glossary, or routing change invalidates the record.

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

The final evidence approver inspects the published verification artifacts and
records a final Go bound to the verification digest, routing digest, and every
required readiness digest. `review_at_merge.sh` is a read-only validator: it
does not build, test, create, repair, or update evidence.

Historical schema-v1/v2 log records and schema-v3 bundles remain read-only
metrics only. New merge authorization is written exclusively as a schema-v4
bundle with schema-v2 readiness. Old records are never upgraded, appended to,
or converted into a schema-v4 Go.
<!-- END GENERATED: review-contract -->

Resolve current terminology, compare the exact committed EN/ZH diff in context,
and inspect existing development/targeted evidence. Do not run the review
profile. Report exact EN/ZH evidence, finding counts, mechanically derived
readiness, immutable bundle id, and glossary hash.
