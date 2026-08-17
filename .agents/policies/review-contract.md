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

The exported terminal type must be installed. After correcting a terminal-only
failure, use the same prefix with `--retry-failed`; this initializes ncurses and
does not bypass any final-gate phase. Environment diagnosis lives in
`docs/zh-testing.md`.

The final gate uses the target checkout's trusted control-plane, holds a
bundle-specific lock, and creates a new attempt only when no valid pass exists.
Initial schema-v4 bundle creation publishes `.bundle.lock`. Later writers must
open that existing lock read/write; status, validation, final-check and
merge-time readers must open it read-only with a shared lock. They must not
create or repair it. A missing or replaced schema-v4 lock is invalid evidence.
Lockless schema-v3 records may be inspected only as historical,
non-authorizing evidence and must remain byte-for-byte untouched. Failed,
interrupted, abandoned, incomplete, or tampered attempts never approve a
merge. A valid pass is reused and never rerun for the same bundle.

The review profile always runs the independent required `review-ledgers`
phase. Trusted auditor code comes from the target checkout while the validated
candidate root supplies the read-only data. All six strict inventories
(character, god, item, monster, species/background, and world) run regardless
of the changed-file set. Verification-v5 metadata binds each inventory
artifact individually; missing ledger input, incomplete parsing, stale facts,
or an unknown state fails closed.

For an exact-bound review, those auditors must share one snapshot of the full
candidate commit. Input discovery comes from that exact Git tree, each unique
regular-file blob is read at most once, and the inventory artifact binds the
normalized input/discovery manifest. Any target-side control files included as
inventory provenance must use a separate snapshot bound to the exact trusted
control commit. Mutable worktree paths are not production inventory input.
Unbound development reads must use no-follow descriptors and verify the opened
inode matches the inspected inode. Directed tests must prove that a transient
bound-worktree substitution is not accepted and that a concurrent unbound path
swap is rejected even when the original pathname is restored before the caller
resumes.

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

## External CI substitution

A resource-constrained control plane may substitute a bound GitHub Actions run
for some final-gate phases, but only through an explicit, fail-closed option:

`TERM=xterm-256color bash .claude/scripts/review_final_gate.sh <candidate> <target> --github-actions-run <run-id>`

External CI replaces CI *proof* only. It never replaces reviewer readiness,
strict review ledgers, the final approval decision, or the read-only merge
gate: `review-ledgers` always runs locally, every routed reviewer must already
be Ready, and the approval is still sealed from the same immutable attempt
digest. The trusted contract section in
`.claude/scripts/data/review_verification_contract_v5.json` is the single
source of truth for the repository, workflow path, allowed events, required
jobs, externalizable phases, and proof artifact name; it is protected by the
control-plane hash. The caller may name an optional `--github-repository` only
if it equals the contract value; the contract repository can never be
overridden. A caller-supplied proof JSON is never accepted: the proof is
generated at gate time by the contract-listed control-plane helper
(`.claude/scripts/fetch_github_ci_proof.py`) through the real `gh` API for the
exact run id.

The proof is bound to every identity the gate controls and fails closed on any
mismatch: the contract repository (including the run's `repository` and
`head_repository`), the exact candidate `head_sha` (pull-request merge-ref
results are never accepted; only the contract's allowed workflow-dispatch
control path is valid), the workflow path
`.github/workflows/ci.yml`, the workflow blob identity at the candidate head
with no drift against the target/base blob, the recorded workflow blob SHA-1
and SHA-256 identities, a completed run (whose aggregate conclusion is
recorded but need not be success), and every contract-required job id with
`completed`/`success` conclusion. Optional or
skipped jobs never become required. The canonical proof records the run URL/id,
event, head branch/SHA, workflow blob identity, target-control SHA, API response digests, the
required job list, and each job's id/conclusion, and is stored as the attempt artifact
`github-actions-proof.json`. The workflow's externalized jobs must execute the
verification scripts from a detached checkout of that target-control SHA, while
reading the candidate checkout only as data; the evaluated required-job names
must end with ` @ <target-head>` so the target binding is independently visible
in the GitHub API snapshot. The schema-v4/v5 metadata marks every replaced
phase `source=github-actions` while every other phase still runs locally.
Phases the contract does not list as externalizable may never carry that
source. The attempt digest, final approval, and `review_at_merge.sh` re-verify
the proof exactly as the gate did; a missing, forged, drifted, or malformed
proof never approves a merge. Local default behaviour is unchanged: without
`--github-actions-run` the gate runs every contract phase itself.

## Historical recovery records

Expired one-time recovery exceptions are not active policy and are not copied
into runtime Agent prompts. Their original text and the former detailed
operational notes are preserved in the
[review recovery archive](../../docs/review-recovery-history.md). Nothing in
that archive authorizes a new candidate, retry, descendant, or target.
