---
name: translation-reviewer
description: Review DCSS Chinese translation semantics and language quality, distinct from implementation mechanics.
argument-hint: "[commit-ish or leave empty for current diff]"
---

# translation-reviewer Skill

Use `.claude/agents/translation-reviewer.md` for content-quality review.

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

## Temporary owner-authorized recovery bootstrap exception

**Exception ID:** `DCSS-ZH-BOOTSTRAP-2026-07-29`
**Authority:** repository owner and sole project-policy administrator
**Effective date:** 2026-07-29
**Installed S:** `a49c41fdcba16acc34023ae29ac81e3b3a62f14f`
**Installed C:** `8aae77c60a5e537e76c7b252c6a311fade4264c2`
**Status:** expired permanently when the exact installed C above was
fast-forwarded into the dedicated recovery target; no further edge is
authorized

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

This exception expired immediately and permanently when the exact installed C
OID `8aae77c60a5e537e76c7b252c6a311fade4264c2` was fast-forwarded into the
dedicated recovery target.

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

## Temporary owner-authorized candidate-root test repair

**Exception ID:** `DCSS-ZH-ROOTFIX-2026-07-29`
**Authority:** repository owner and sole project-policy administrator
**Base C:** `8aae77c60a5e537e76c7b252c6a311fade4264c2`
**Installed P:** `0abfe2b3d60d18d6dc3bca7f8079a44bb4a002e0`
**Installed P2:** `99b887d5c7462874c2b10937333e9f475a9343d4`
**Installed F2:** `c7768fde48ea4f08e2363a67f211702d2ba27ca7`
**Failed F:** `8363639529e650b0c3444614b6978e4d196be7ea`
**Status:** expired permanently when the exact installed F2 above was
fast-forwarded into the dedicated recovery target; the former `P2 → F2`
authorization cannot be retried or reused

This exception repairs one target-trusted regression test which writes its
mutable fixture beneath the target checkout while its auditor is correctly
bound to the candidate checkout. The resulting cross-root rejection prevents
every normal verification-v5 successor of C from authorizing the repair that
would make the test candidate-root safe.

P was separately owner-authorized and installed. Its first repair candidate F
was formally attempted under bundle
`e3b2347a71dc716c4c664543449d42197dc3960f00e297e65485515d321649c3`,
producing immutable failed attempt
`attempt-1785368942683452000-38040-767b84d22f70`. The committed candidate
test was invoked with the gate wrapper's own absolute path argument still in
`sys.argv` and with candidate code detached from the interpreter's real
`sys.modules["__main__"]`. The failed attempt is retained for forensic history.
It did not run the intended test suite and cannot authorize F.

P is not Go evidence for F merely because it contains the exception. F remains
No-Go permanently, and its bundle, readiness, logs, failed attempt and retired
marker must not be deleted, rewritten, migrated, retried, or reused for F2.
The dedicated recovery target must not move again until P2 has been separately
authorized and installed and the dedicated gate has produced and revalidated
a complete immutable approval for a newly committed F2.

### Installed P and corrective policy candidate P2

The installed P remains the exact one-commit policy boundary whose parent is
Base C:

`P^ == 8aae77c60a5e537e76c7b252c6a311fade4264c2`

P2 is a new, unique, one-commit correction whose exact parent must be the
installed P:

`P2^ == 0abfe2b3d60d18d6dc3bca7f8079a44bb4a002e0`

Both the historical Base-C-to-P edge and the corrective P-to-P2 edge must have
the same complete changed-path set, computed with rename detection disabled:

- `.agents/policies/review-contract.md`
- `.claude/agents/translation-reviewer.md`
- `.claude/agents/zh-code-reviewer.md`
- `.claude/scripts/review_rootfix_gate.py`
- `.claude/scripts/tests/test_review_rootfix_gate.py`
- `.claude/skills/translation-reviewer.md`
- `.claude/skills/zh-code-reviewer.md`
- `.codex/agents/translation-reviewer.toml`
- `.codex/agents/zh-code-reviewer.toml`
- `.opencode/agents/translation-reviewer.md`
- `.opencode/agents/zh-code-reviewer.md`
- `.opencode/skills/translation-reviewer/SKILL.md`
- `.opencode/skills/zh-code-reviewer/SKILL.md`
- `.pi/agents/translation-reviewer.md`
- `.pi/agents/zh-code-reviewer.md`
- `docs/zh-testing.md`

Every path outside this manifest must have identical path existence, mode,
object type, and object OID in Base C, P and P2. P2 must contain only the
candidate-wrapper correction, its end-to-end subprocess and lineage
regressions, this canonical policy update, its synchronized generated copies,
and the matching `docs/zh-testing.md` update. The wrapper must normalize
`sys.argv` to the candidate test path and install a real candidate
`sys.modules["__main__"]` module before executing the committed blob.

Nothing written in P2 authorizes, ratifies, or retrospectively validates its
own installation. Before the dedicated recovery target moves from P to P2,
the repository owner must separately record the exact full OID of P2, approve
the complete manifest above, verify clean P and P2 checkouts plus the exact
Base-C-to-P-to-P2 ancestry, require the focused rootfix-gate tests and existing
review-bundle regressions to pass, require one clean exact-bound code profile
for P to P2, and require independent `zh-code-reviewer` findings of zero
Blocker and zero Needs Fix. The external owner record must identify its permit
format and issuer, bind the protected ref and its current exact P OID, the exact
P2 OID, exception/protocol version, 16-path count and manifest SHA-256, binary
diff SHA-256, glossary SHA-256, reviewer set and result, and focused,
review-bundle and code-profile results. It must authorize only the exact
fast-forward from P to P2, never a P2 descendant. The owner must then explicitly
authorize only that exact policy installation. An ordinary candidate,
reviewer, branch name, prose file inside the candidate, or automation run
cannot perform that governance action. Any protected-ref state or P2 content
change invalidates its OID, hashes, review and owner authorization.

### Repair candidate F2 boundary

After P2 has been installed, F2 must be one clean commit with exactly one
parent:

`F2^ == <approved-full-P2-OID>`

Its complete changed-path set, computed with rename detection disabled, must be
exactly:

- `.claude/scripts/tests/test_monster_name_ssot.py`

The existing file mode must be preserved. Every path outside this one-file
manifest must have identical path existence, mode, object type, and object OID
in P2 and F2.

The only semantic change permitted in F2 is to create the mutable review
fixture beneath the auditor's resolved candidate root, replacing
`REPO_ROOT / ".claude"` with `audit.ROOT / ".claude"` as the explicit
`TemporaryDirectory` parent. F2 must not change production auditors, verifier
code, review schemas, policies, translation assets, glossaries, decisions, or
review ledgers.

### Dedicated mechanically verified P2 to F2 gate

The normal target-P2 `review_prepare.sh` must first create a new schema-v4 bundle
for the exact P2 and F2 OIDs. Its routing-v2 scope must be the single F2 path and
its reviewer set must be exactly one `zh-code-reviewer`. That reviewer must
review the complete frozen path and return findings-v2 with zero Blocker and
zero Needs Fix before readiness-v3 is recorded.

No normal verification-v5 attempt or final approval may exist in this bundle.
The rootfix gate rejects legacy evidence, incomplete readiness, a different
scope or reviewer, any normal attempt, or any normal approval. It recomputes
the exact parent topology, both complete Base-C-to-P and P-to-P2 16-path
manifests, their cumulative no-extra-path boundary, and the complete
P2-to-F2 one-path manifest, both file modes and both test blobs.
The clean F2 checkout must be a linked worktree listed by the clean P2 target's
own `git worktree list --porcelain -z` inventory, and both checkouts must
resolve to the same physical Git common directory. An independent clone,
unlisted checkout, mismatched worktree HEAD, or external evidence namespace is
rejected.
The executable gate, `review_bundle.py`, `i18n_shared.py`, verification
contract and `verify_zh.sh` must themselves be regular files in the clean P2
target and byte-equal their P2 Git blobs. Before loading repository code, the
gate uses a sanitized Git environment with replacement objects disabled to
read the exact P2 blobs from the checkout containing the installed gate for
`review_bundle.py`, `i18n_shared.py`, the verification contract and
`verify_zh.sh`; a caller-supplied target path cannot select pre-validation
code. It compiles both Python modules from those bytes in isolated module
objects, parses the retained contract bytes, and executes the retained
verifier source rather than reopening the verifier pathname. Gate blobs,
profile metadata, artifact files and every other
path-sensitive evidence read use no-follow, inode-identity-checked,
single-read file descriptors and require link count one; an object replacement
or hard link during open or read fails closed. The focused committed input is
read from the exact F2 Git blob, retained once, and supplied to the child
through an anonymous input file; its attempt-local copy must have the same
SHA-256.
The gate retains descriptors for the evidence root and its `attempts/`
directory from the first inventory through the terminal boundary. That first
inventory also binds the presence, bytes and inode identity of `running.json`
and `approval.json`. Disappearance, appearance, replacement or whole-directory
substitution after that observation is No-Go; an observed approval cannot be
treated as an interrupted absent approval and regenerated.
Before its first repository import, the source-invoked gate selects an
unpredictable, initially absent private bytecode-cache namespace outside the
checkout and disables bytecode writes. The focused child and the full profile
subtree receive distinct attempt-private cache prefixes and the same write
prohibition. Ignored checkout `__pycache__` objects and modified working-copy
Python sources therefore cannot supply the gate's trusted imports or either
verification phase.

The sole candidate-sourced control input is the committed F2 blob at
`.claude/scripts/tests/test_monster_name_ssot.py`. The gate proves that blob is
exactly the P2 blob with one replacement of `REPO_ROOT / ".claude"` by
`audit.ROOT / ".claude"`, then executes that F2 entry point with audit root and
audit commit bound to F2. The wrapper supplies only the test path in
`sys.argv`, creates and registers a real candidate `__main__` module, and
executes the retained blob in that module. Every imported auditor, helper,
verifier, classifier, policy, production input and other tree object remains
P2-trusted: the one-path tree proof mechanically establishes byte-for-byte
P2/F2 identity outside the test blob.

After the focused cross-root test passes, the gate runs the retained P2
`verify_zh.sh` source exactly once as
`--profile code --base P2 --head F2 --scope full` with F2 as its clean worktree.
The verifier pathname cannot replace the source being executed, and every
dependency except the approved test blob has already been proven identical to
P2. Metadata must be schema-v3, status `pass`, with zero failures and exact P2,
F2, Git diff-hash, diff SHA-256 and glossary bindings. Boolean and integer
fields require their exact JSON types; Python's bool/int subtype relationship
cannot satisfy them. The gate also requires the retained P2
verification-contract version, `profile=code`,
`scope=full`, the run-directory ID and candidate worktree, all risk and runtime
fields, the exact required phase sequence and successful phase records, and
the exact artifact inventory, sizes and SHA-256 values. Metadata, phases and
artifacts are checked from the same single-read attempt snapshot; missing,
extra, skipped, failed or digest-drifted objects fail closed. A passing
attempt's `profile-output/` directory and file sets are exact, including the
wrapper log, and its candidate input, both raw phase logs and both process
records are mandatory.

Run the installed P2 gate from the clean P2 target checkout:

```text
python3 .claude/scripts/review_rootfix_gate.py run \
  --repo <clean-F2-worktree> --target-repo <clean-P2-target> \
  --bundle <exact-schema-v4-bundle-id>
```

After an immutable failed attempt, a new execution additionally requires
`--retry-failed`. After a demonstrably stale running marker, staging residue,
or exact root-level atomic temporary left by `running.json` or `approval.json`,
recovery additionally requires `--recover-stale`; neither option weakens any
OID, topology, routing, readiness, blob, inventory, or clean-tree binding.
Without that flag, an exact atomic temporary fails as stale. With it, the gate
never unlinks the atomic residue. It holds the no-follow,
inode-identity-checked descriptor open and uses a no-replace atomic move into
the bundle-bound sibling archive
`zh-review-evidence/rootfix-recovered-v1/<bundle-id>/`. The exact generated
archive name binds the original temporary form, writer identity, content
SHA-256 and recovery identity. The complete bytes, size, digest and inode from
the first evidence inventory remain the required baseline; the no-follow
single read also binds the pre-open and post-read size, mtime and ctime, so a
same-inode, same-size write during a multi-chunk read is rejected. The moved
inode is checked against the open
descriptor before, throughout and after content validation; a later pathname
read may not establish a new baseline. The archive is then fully enumerated
with exact-name, single-link, size and content-digest validation.
Every object moved by the current recovery invocation returns an inode, size
and digest seal which remains required before and after staging archival and at
the invocation's next evidence boundary. A just-moved object cannot disappear
or be replaced while recovery still succeeds; a non-empty required-seal set
with an absent bundle archive is an immediate No-Go rather than an empty
inventory.
Both `run` and read-only
`check` validate any existing archive; `check` does not create an absent
archive. Archived objects remain outside the active approval root for
owner-governed forensic retention, and a conforming gate invocation never
removes them. The gate mechanically conserves objects it moved for the
duration of that invocation; long-term archive retention between invocations
remains an owner-governed filesystem responsibility. An
interruption after the move therefore resumes by validating the retained
archive object, not by deleting it. A regular-file or symlink replacement
after the read is retained in the archive and rejected; its identity or digest
cannot satisfy the generated name. Malformed names, unknown objects,
unrecognized directories, symlinks, special objects, hard links, oversized
files and content drift fail closed. The sole accepted archive directories
are exact retired-staging names whose complete directory-and-file tree digest
matches their names.

The gate also never unlinks `running.json`. After a normal attempt is
published, or while a demonstrably dead marker is recovered, it re-reads and
validates the exact canonical marker, including positive-integer PID and
non-empty process-start and boot identifiers. Its pre-read inode, size and
single-link state remain the baseline while the descriptor is opened and held,
and the pathname is retired with the same no-replace move into the bundle
archive. The
generated retired-marker name binds the exact operation ID, marker content
SHA-256, exact published-attempt SHA-256 (or explicit `none` when no attempt
was published), and recovery identity. Both normal retirement and stale recovery
compare the moved inode with the descriptor before, throughout and after
content validation and retain plus reject a regular-file, symlink or other
replacement. Every archive validation boundary independently
re-resolves the physical bundle archive path; an absence observed at startup
is never cached across a long-running verification or approval publication.
Every published attempt must map to exactly one valid retired marker with the
same operation ID and attempt digest at pass reuse, approval validation and
read-only `check`; duplicate, missing, orphaned or mismatched conservation
records fail closed. Recovery may not derive a new digest seal from a
published attempt still accompanied by an unretired marker: that crash window
has no durable external digest authority and remains No-Go.

The gate preserves every failed run under the Git common directory at
`zh-review-evidence/rootfix-v1/<bundle-id>/attempts/`. A successful run writes
one canonical, write-once `approval.json` beside that directory. The approval
schema binds the exception ID, Base C, P2 and F2 OIDs, bundle/diff/glossary/
routing digests, readiness-v3 digest, frozen policy-manifest digest, both test
blob digests, the complete failed-and-passing attempt inventory, and the
passing attempt digest. The gate's compiled-in P OID and lineage proof bind
the intervening exact Base-C-to-P-to-P2 chain. The gate emits the approval
SHA-256; unknown objects, non-canonical JSON, digest drift, an unsafe path or a
changed attempt fail closed. Exact JSON types are part of the binding:
canonical-byte comparison prevents a Boolean from satisfying an expected
integer through language-level container equality.

Every published attempt, including failed and interrupted attempts, contains a
canonical inventory of every relative directory and regular file. Its digest
also enumerates both directories and files and binds each file's kernel
modification/change generation, so adding an empty directory or rewriting a
file changes the digest. Every recursive enumeration binds each held
directory's size, mtime and ctime before the scan and after all descendants,
then re-stats every read file by its held parent descriptor. Symlinks, special
objects, an inventory omission, an unrecorded object, a hard-linked artifact
or approval, or any post-publication mutation is rejected. The digest in the
retired marker is outside the attempt
directory and fixes the authority used on every later validation; coherently
rewriting both an artifact and the attempt's internal inventory cannot create
a new accepted digest. Passing attempts additionally require the exact
profile-output directories and files plus every raw input, log and process
record. Failed and interrupted attempts with no durable profile command forbid
all profile-output objects; after the profile command starts, publication
requires one exact terminal metadata run, its exact known directory/file tree,
metadata-bound report, semantic wrapper and no additional or omitted object.
Profile metadata must use the retained verifier's deterministic sorted,
indented UTF-8 JSON serialization; duplicate keys at any depth and non-standard
JSON constants fail closed. The report's timestamp, run ID, scope, risk,
Base/Head, both diff identities, glossary, ordered phase headers/results and
terminal summary are parsed and bound to that metadata. If the retained
verifier appends a post-summary HEAD or glossary drift footer,
the gate accepts only its exact production form and requires the final failure
count to equal the report summary plus that one drift failure. The wrapper's
report and metadata lines must equal the exact lexical absolute paths under the
attempt's original `.staging-<attempt-id>/profile-output/<run-id>/` output
root; a suffix match or an external lookalike path is insufficient.
The parent-captured `code-profile.log` must equal the production stdout for a
complete pass/fail run and bind the same run ID, report, metadata, wrapper
paths and blocking-failure count. An interrupted or unexpected-exit run may
retain only a byte prefix of that stdout; a present structured field may never
contradict the metadata or original staging root.
An incomplete partial profile remains unpublished staging for explicit
recovery. The two parent-captured raw phase logs are opened read/write once,
fsynced and snapshotted through their writer descriptors; sealing requires the
same inode, size, digest and bytes at the final evidence pathname. The inner
signal-forwarding handler remains installed until that writer snapshot is
fsynced and registered in the attempt seal set. After the child has reached a
terminal, that handler also remains installed through the profile metadata
handoff: a signal is deferred until the raw-log seal and metadata validation
either establish the exact profile terminal or fail closed. A focused-phase
signal becomes exact interrupted evidence; a signal after a validated profile
terminal preserves that pass, fail or interrupted terminal rather than losing
the raw-log seal or inventing a different completion.
Immediately
before a retry executes, the gate freezes
the complete validated published-attempt inventory. Every entry in that
pre-execution inventory, with the same attempt ID and digest, must remain in
the post-execution inventory, including when the retry fails or is interrupted;
a concurrent deletion or rewrite cannot be hidden by publishing a new attempt.
The archive, evidence inventory, pre-existing-attempt lower bound and
attempt/retired-marker conservation checks run after the execution callback
both when it returns and when it throws; only after those checks pass may the
original exception or interruption be rethrown.

The gate holds the normal bundle lock, writes a bundle-bound `running.json`
marker before execution, and starts each child behind a release pipe in a
separate supervised process group. Before releasing the child to execute, it
durably writes an attempt-local process record binding the phase, logical
command digest, PID, PGID, process-start token and boot identity. Recovery
refuses a live recorded process group even after the gate parent was killed;
this is the Darwin and Linux parent-death boundary. After the child leader is
reaped, cleanup may signal a surviving recorded group only when the current
boot and any reused leader PID still match the retained identity; a different
process-start token fails closed without signalling that group. A catchable
signal arriving
while the process record is being written is recorded before release; the
blocked child is killed or released and signalled only after that record has
reached its durable boundary. The gate records an
initiating `SIGINT`, `SIGTERM`, or `SIGHUP`. It immediately sends
the whole focused-child or full-profile process group a cleanup-safe `SIGINT`
so Python `TemporaryDirectory` contexts can unwind. After bounded grace it
sends the original `SIGTERM` or `SIGHUP`, then `SIGKILL` if the group remains
unresponsive. Attempt evidence normalizes the exit and interrupted-signal
fields to the initiating signal rather than the cleanup signal. The focused
Python child additionally converts catchable signals into an exception-safe
unwind. The same initiating-signal handler remains active across attempt
creation and execution. Once a terminal is established, the complete
seal-to-publication-to-marker-retirement critical section temporarily masks
those catchable signals, durably publishes the attempt, archives and
revalidates the marker, closes its held directories, then restores the mask
and rethrows the original signal with its exact signum; no catchable signal can
strand a published attempt on the unsealed side of marker retirement. A
secondary signal delivered while restoring that mask cannot replace the first
initiating signum. The gate
never silently deletes
unpublished staging after an
exception. Interrupted execution is published as an immutable interrupted
attempt when possible. If a signal arrives after the profile command has
started but before metadata establishes an exact profile terminal,
the gate retains marker plus staging for explicit recovery and rethrows the
exact signum; it must not invent an interrupted completion over that tree or
allow a secondary sealing error to replace the signal. Once verification has
established a pass, fail, or interrupted profile terminal, an interruption
during the metadata handoff, post-validation, sealing or marker retirement
resumes that same terminal. The published outcome, exit code, signal, commands
and metadata path must all equal the established terminal instead of creating
a contradictory completion marker. A failure before attempt publication must
leave the marker/staging boundary recoverable and must not replace the
initiating signal. Once the attempt directory has been atomically published,
a retirement failure preserves every object and the initiating signal but does
not authorize recovery to derive the missing external digest seal; only the
complete attempt-plus-retired-marker boundary is reusable. A non-signal
validation failure before terminal publication likewise retains marker plus
staging and is never rewritten as a generic failed attempt. An
uncatchable termination leaves the running marker and any staging or atomic
temporary for explicit stale recovery; all candidate and target clean-tree
constraints are rechecked before evidence can be reused. Stale cleanup
requires an explicit `--recover-stale`, rejects a live owner, and archives
rather than deletes the exact validated bundle-local staging tree, safe atomic
temporaries and dead running marker described above. Atomic write-once
publication retains its open temporary descriptor through publication and
never performs a check-then-unlink cleanup after failure; any unpublished
temporary or pathname replacement remains available for explicit recovery.
The recovery entry freezes the evidence-root, attempts-directory, marker,
approval and atomic-residue identities from one initial inventory; an observed
object may not disappear, appear or be replaced before the recovery re-read.
A validated dead marker and every exact atomic residue are retained and
revalidated in the archive before and after the bound staging directory is
atomically moved into that archive. Its held directory descriptor, inode and
complete tree digest must still identify the moved object, so a pathname
replacement is retained and rejected rather than deleted. Failed retirement
cannot consume either staging object.
Normal completion retires its validated marker through that same retained
archive path. A staging name must contain the gate's exact generated
operation-ID grammar. With a marker, zero or one staging directory is allowed
and any present directory must equal the marker binding; without a marker,
recovery accepts at most one valid staging residue. Malformed, conflicting or
multiple residues fail closed without deletion. If the unique passing attempt
and its exact digest-bound retired marker were both durably published but
approval writing was interrupted or failed, the next `run` deterministically
writes the same approval from that sealed attempt instead of rejecting or
rerunning it. A published attempt lacking that retirement seal is not
recoverable by this exception.

Immediately before landing, run the read-only check:

```text
python3 .claude/scripts/review_rootfix_gate.py check \
  --repo <clean-F2-worktree> --target-repo <clean-P2-target> \
  --bundle <exact-schema-v4-bundle-id>
```

Only `ROOTFIX_MERGEABLE` with exit code zero authorizes the repository owner to
fast-forward the dedicated recovery target from the exact P2 OID to the exact
F2 OID printed by the checker. The check does not create or repair evidence.
Normal final-attempt, final-approval and merge-authorization JSON must not be
fabricated.

This exception does not authorize deletion, rewriting, migration, or reuse of
any existing evidence. It does not authorize a non-fast-forward update,
replacement of `chn-0.34.1-base`, a push, release, or deployment.

### C2 and successor recovery state

The abandoned C2 candidate
`9eb928eb31b1618ddd95dfdf2259e0227b74526d` and bundle
`1cdadc600224cc7bd9b3f2116272871ab46c59d9c57ef0f72813a3412d6f3527`
do not authorize any later edge. Its character-mechanics, god and
species/background ledgers lack strict evidence blocks, so their three
required inventory artifacts were never produced. The invalid final-gate run
did not publish a formal attempt. C2 readiness, bundle objects, logs and any
other evidence must not be copied, migrated or reused.

After F2 landed, the contextual parser change was rebuilt on F2 together with
the approved R content changes and every required strict review ledger as a new
committed candidate. That successor used a new bundle, mechanically routed
code and translation review, new readiness and a complete normal
verification-v5 final gate. No C2, F, or pre-F2 identity or evidence was
carried forward.

### Expiration

This corrected exception activated only after the separately authorized
installation of exact P2
`99b887d5c7462874c2b10937333e9f475a9343d4` and expired immediately and
permanently when exact F2
`c7768fde48ea4f08e2363a67f211702d2ba27ca7` was fast-forwarded into the
dedicated recovery target. It cannot authorize F, an amended F2, a retry for
another edge, or any content change. Every successor of F2 must use
routing-v2, findings-v2, readiness-v3, verification-v5, the normal final gate,
and the normal merge-time validator.

## Temporary owner-authorized whole-document ledger seed

**Exception ID:** `DCSS-ZH-LEDGER-SEED-2026-07-30`
**Authority:** repository owner and sole project-policy administrator
**Installed F2:** `c7768fde48ea4f08e2363a67f211702d2ba27ca7`
**Installed P3:** `2e43e04884348b54879944b77d0af8ebf7636dc0`
**Status:** consumed permanently by installation of the exact P3 above under
its separate external owner permit; no retry, descendant or other target is
authorized

This exception exists because the F2-trusted character-mechanics, god and
species/background auditors require a strict evidence block but their
canonical renderers replace the complete human-readable review cards with
hash-only triples. The F2-trusted item and world renderers likewise omit
required development and inventory-migration history. A normal F2 final gate
therefore cannot both preserve those reviewed statements and accept a
candidate that installs their target-side whole-document validation.

The exception authorizes only the policy installation described below. It does
not authorize a content candidate, a review ledger, a translation change, a
normal final-gate approval, or any descendant of P3.

### Exact P3 topology and path boundary

P3 must be one clean commit with exactly one parent:

`P3^ == c7768fde48ea4f08e2363a67f211702d2ba27ca7`

Its complete changed-path set, computed with rename detection disabled, must be
exactly:

- `.agents/policies/review-contract.md`
- `.claude/agents/translation-reviewer.md`
- `.claude/agents/zh-code-reviewer.md`
- `.claude/scripts/audit_character_mechanics_inventory.py`
- `.claude/scripts/audit_god_inventory.py`
- `.claude/scripts/audit_item_name_inventory.py`
- `.claude/scripts/audit_species_background_inventory.py`
- `.claude/scripts/audit_world_inventory.py`
- `.claude/scripts/tests/test_audit_character_mechanics_inventory.py`
- `.claude/scripts/tests/test_audit_god_inventory.py`
- `.claude/scripts/tests/test_audit_item_name_inventory.py`
- `.claude/scripts/tests/test_audit_species_background_inventory.py`
- `.claude/scripts/tests/test_audit_world_inventory.py`
- `.claude/skills/translation-reviewer.md`
- `.claude/skills/zh-code-reviewer.md`
- `.codex/agents/translation-reviewer.toml`
- `.codex/agents/zh-code-reviewer.toml`
- `.opencode/agents/translation-reviewer.md`
- `.opencode/agents/zh-code-reviewer.md`
- `.opencode/skills/translation-reviewer/SKILL.md`
- `.opencode/skills/zh-code-reviewer/SKILL.md`
- `.pi/agents/translation-reviewer.md`
- `.pi/agents/zh-code-reviewer.md`
- `docs/zh-testing.md`

Existing file modes must be preserved. Every path outside this manifest must
have identical path existence, mode, object type and object OID in F2 and P3.
The generated reviewer Agent and Skill copies may change only through
`sync_agent_policies.py` from this canonical policy.

P3 may install only deterministic whole-document rendering and validation for
the five affected ledgers, focused negative-mutation regressions, this
canonical exception, its synchronized generated copies and the matching
testing documentation. It must preserve complete visible identity, English and
Chinese, production-fact, reviewer-decision and rationale evidence. It must
also preserve the item producer/consumer evidence, all four exact development
report paths and statuses, their failure/pass reruns and non-overwrite
statement. The world inventory history, complete 20-member old-only proof,
761-to-788-to-789 membership proof and deferral history must likewise be
canonical rendered sections. A missing, altered, duplicated, reordered or
extra managed section must fail closed.

P3 must not modify any review ledger, translation asset, glossary, decision
file, classifier, bundle schema, final gate, merge validator, verifier or
inventory source. It must not silently assign a terminal conclusion to a new
identity. Its migration writer may carry forward a complete, parseable
reviewer decision and rationale from an existing ledger, but cannot invent one
when the source evidence is absent or ambiguous.

### Separate external owner permit

Nothing committed in P3 authorizes or retrospectively validates its own
installation. Before the protected target moves, the repository owner must
issue one external permit in canonical
`dcss-zh-owner-permit-v1` key-value form. The permit must bind:

- issuer identity and permit format version;
- this exception ID and `review-contract-v5`;
- the protected ref identity and its current exact F2 OID;
- the exact P3 OID and the explicit semantic scope
  `target-side-whole-document-ledger-seed-v1`;
- the exact 24-path count, normalized sorted manifest SHA-256 and binary diff
  SHA-256;
- the candidate glossary SHA-256;
- target-F2 routing schema, routing digest, classification and the complete
  reviewer set;
- focused auditor-test, policy-sync and exact-bound code-profile results;
- an independent review of the complete frozen scope with zero Blocker and
  zero Needs Fix.

Every bound value must be recomputed with F2-trusted Git and routing controls
before installation. The permit must state that it authorizes only an
`ff-only` update of the named protected ref from exact F2 to exact P3 and does
not authorize a P3 descendant. A changed OID, path, mode, object type, manifest
hash, diff, glossary, routing result, reviewer result, test result or protected
ref state invalidates the permit and requires a newly built P3 and a new
external permit. A candidate file, local branch name, ordinary readiness
record or automation run is not the owner permit.

### Consumption and successor boundary

The exact permitted P3
`2e43e04884348b54879944b77d0af8ebf7636dc0` consumed this exception
immediately and permanently when it was installed. The exception cannot be
reused for an amended P3, another target ref, a retry, a ledger rewrite or any
later candidate. The expired bootstrap and rootfix exceptions remain expired
and cannot provide an alternative F2 migration entry.

P3 only makes its control plane available as trusted target-side code. It does
not prove that code against a production ledger candidate. The first successor
must be a newly committed normal routing-v2 candidate reviewed under the
complete mechanically routed reviewer set. Its ledgers must be generated by
the P3 renderers and pass P3-trusted whole-document audits, readiness-v3,
verification-v5, the normal final gate and the normal merge-time validator.
No C2, C11 or pre-P3 bundle, readiness, attempt, approval or merge
authorization may be copied, converted or reused.
<!-- END GENERATED: review-contract -->

Resolve current terminology, compare the exact committed EN/ZH diff in context,
and inspect existing development/targeted evidence. Do not run the review
profile. Report exact EN/ZH evidence, finding counts, mechanically derived
readiness, immutable bundle id, and glossary hash.
