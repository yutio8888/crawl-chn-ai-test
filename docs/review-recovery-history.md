# Historical Review Recovery Records

> Status: **archival and non-authorizing**. Active review policy lives in
> `.agents/policies/review-contract.md`; current operator guidance lives in
> `docs/zh-testing.md`.

This file preserves expired exception text and former operational notes that
were removed from always-loaded Agent policy. Nothing below authorizes a new
candidate, retry, descendant, target update, or evidence migration.

## Archived exception text from review-contract-v5

The following exception sections are preserved from the former active policy.
Every exception is expired or consumed as stated in its own status field.

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

## Archived operational notes from docs/zh-testing.md

The following detailed narrative accompanied those recovery events. It is
retained for forensic context only and is not current workflow guidance.

By default, every new authorization uses schema-v4 bundles with routing-v2,
findings-v2, readiness-v3, and verification-v5. Routing-v1/readiness-v2
objects in the v4 directory and schema-v3 bundles are historical read-only
evidence and never authorize merge.

The review contract retains three historical recovery exceptions so their
boundaries remain auditable, but none is active. The bootstrap exception
expired when exact S
`a49c41fdcba16acc34023ae29ac81e3b3a62f14f` and exact C
`8aae77c60a5e537e76c7b252c6a311fade4264c2` were installed. The rootfix
exception expired when exact F2
`c7768fde48ea4f08e2363a67f211702d2ba27ca7` was installed over exact P2
`99b887d5c7462874c2b10937333e9f475a9343d4`. The ledger-seed exception was
consumed when exact P3
`2e43e04884348b54879944b77d0af8ebf7636dc0` was installed. None authorizes a
retry, descendant or different target. All later edges use the normal
routing-v2, findings-v2, readiness-v3, and verification-v5 workflow.

The separately owner-governed `DCSS-ZH-ROOTFIX-2026-07-29` exception addresses
one later candidate-root regression in the trusted monster-name test. The
repository owner separately installed P
`0abfe2b3d60d18d6dc3bca7f8079a44bb4a002e0` over Base C
`8aae77c60a5e537e76c7b252c6a311fade4264c2`. The first repair F
`8363639529e650b0c3444614b6978e4d196be7ea` then produced immutable failed
attempt `attempt-1785368942683452000-38040-767b84d22f70` in bundle
`e3b2347a71dc716c4c664543449d42197dc3960f00e297e65485515d321649c3`.
The wrapper exposed its absolute-path argument to `unittest.main()` and did not
install candidate code as the interpreter's real `sys.modules["__main__"]`, so
that attempt did not execute the intended suite. F and all of its formal
evidence remain immutable No-Go forensic records and cannot be retried,
migrated or reused.

Corrective policy candidate P2 was one commit whose parent was exactly P.
Both Base-C-to-P and P-to-P2 had the same exact 16-path manifest, and
Base-C-to-P2 contained no additional path. P2 normalizes `sys.argv`, installs
a real candidate `__main__` module before executing the retained blob, and adds
an end-to-end subprocess regression. P2 was not self-authorizing: the owner
separately approved its exact committed OID, manifest, independent review,
focused gate and bundle regressions, and exact-bound P-to-P2 code profile
before explicitly installing that exact OID. The external owner record binds
its issuer/format, protected ref and current P,
exact P2, exception/protocol version, manifest and binary-diff hashes, glossary,
reviewer result and test/profile results, and authorizes P-to-P2 only rather
than any descendant.
After installation, the exception permitted only the one-commit `P2 → F2`
edge whose sole changed path was
`.claude/scripts/tests/test_monster_name_ssot.py`.

The target-P2 classifier, schema-v4 bundle, findings-v2 and readiness-v3 remain
mandatory. The dedicated `review_rootfix_gate.py` proves both 16-path policy
edges, their cumulative path boundary and the one-path F2 boundary, reads only
the committed test blob from F2, proves all other F2 objects identical to P2,
runs the focused cross-root regression and one
exact-bound full-scope code profile, then writes canonical digest-bound
write-once evidence under `zh-review-evidence/rootfix-v1/`. Its `check`
subcommand is the read-only merge-time validator. Only
`ROOTFIX_MERGEABLE` authorized that exact fast-forward; the exception is now
expired and cannot authorize another edge.

P2 and F2 must be distinct linked worktrees from the same physical Git common
directory, and F2 must appear with its exact HEAD in P2's own worktree inventory.
The gate, `review_bundle.py`, `i18n_shared.py`, verification contract and
verifier must be byte-equal to their P2 Git blobs. With replacement objects
disabled, the gate loads and compiles both Python helpers from the exact P2 Git
blobs in the checkout containing the installed gate; `--target-repo` cannot
select code before validation. It retains the P2 contract bytes and executes
the retained P2 verifier source rather than reopening its pathname. All gate,
metadata, artifact,
marker and approval reads are no-follow, single-link, inode-bound single
reads which also compare size, mtime and ctime before/open/after so same-inode,
same-size mutation during a multi-chunk read fails closed; the focused input
is read once from the exact F2 Git blob, copied into
the attempt, SHA-256 checked and supplied through an anonymous child input.
One held evidence-root/attempts-directory descriptor pair and the first
inventory bind both directory identities plus the presence and inode of
`running.json` and `approval.json`. A later disappearance, replacement or
whole-directory swap fails closed.
Before any repository import, the source-invoked gate selects an unpredictable,
absent private bytecode-cache prefix outside the checkout and disables writes;
the focused child and full profile receive separate attempt-private prefixes.
Ignored checkout `__pycache__` objects and modified working-copy module
sources therefore cannot become trusted input.
Every failed, interrupted or passing attempt records and digests its complete
directory-and-file inventory, including empty directories; unknown, unsafe or
changed objects and hard-linked artifacts fail closed. A retired marker outside
the attempt binds the exact attempt digest, so a coherent artifact plus
internal-inventory rewrite cannot establish a new accepted digest. Before a
retry executes, the complete validated attempt inventory is frozen as a lower
bound: every pre-existing attempt ID and digest must remain unchanged after
the execution, even when the retry fails or is interrupted. Failed and
interrupted attempts require the exact raw file set implied by their durably
started commands. Without a profile command they forbid all profile output;
with one they require one exact terminal metadata run and its exact known
tree, metadata-bound report and semantic wrapper. Incomplete output remains
unpublished staging. The parent-captured focused and profile logs retain their
writer FDs through fsync and snapshot; sealing requires the same inode, size,
digest and bytes at the evidence pathname. The inner signal handler remains
active until the snapshot is fsynced and entered into the writer-seal map and,
after child exit, through profile metadata validation. A focused-phase signal
still publishes exact interrupted evidence. A signal after the profile
metadata establishes a pass, fail or interrupted terminal preserves that exact
terminal; invalid metadata leaves unpublished staging.
Post-execution archive, evidence,
history and marker-conservation checks run before either a normal return or an
exception/signal rethrow. Canonical-byte comparison makes JSON numeric and
Boolean types distinct in approval and artifact bindings. Attempt inventories
also bind empty directories plus every file's mtime/ctime generation, keep
child directory descriptors through the complete recursive walk, re-stat all
read files, and require stable directory size/mtime/ctime before returning.
An object injected after `scandir` or an in-place post-read rewrite therefore
fails closed.

The full code profile metadata validator binds schema and the retained
contract, `profile=code`, `scope=full`, P2/F2/Git-diff/diff-SHA-256/glossary,
run ID and worktree, exact JSON integer and Boolean types, risk and runtime
fields, every required phase and the exact artifact sizes and SHA-256s. It
validates metadata, phases and artifacts from the same attempt snapshot;
missing, extra, skipped, failed or drifted output is rejected. Passing
attempts require exact profile directories/files, the wrapper log, candidate
input, both raw phase logs and both process records. Metadata must equal the
retained verifier's deterministic sorted/indented UTF-8 JSON; duplicate keys
at any depth fail closed. The report parser binds its structured timestamp,
run ID, scope, risk, Base/Head, diff, glossary, ordered phase results and exact
terminal summary to metadata. An exact post-summary HEAD/glossary drift footer
is accepted only with the production ordering and a metadata failure count one
greater than that earlier summary. Wrapper paths must equal the lexical absolute
paths under the attempt's original staging output root, not merely share a
filename suffix. The parent-captured `code-profile.log` is also parsed: a
complete pass/fail stdout must exactly bind the same run ID, report, metadata,
wrapper paths and failure count; interrupted or unexpected output may only be
a byte prefix of that production stdout.

The gate uses a bundle-bound running marker and supervised child process groups
with signal forwarding. Each child waits on a release pipe until a durable
attempt-local record binds its phase, command digest, PID, PGID, process-start
token and boot identity. Stale recovery rejects a live recorded group even
after a Darwin or Linux gate parent was killed. A signal received while that
record is being written is retained before the blocked child is released or
killed. On `SIGINT`, `SIGTERM` or
`SIGHUP`, it first sends the whole focused or profile process group
cleanup-safe `SIGINT`, then after
bounded grace the original termination signal and finally `SIGKILL`; evidence
retains the initiating signal identity. This lets Python temporary fixture
contexts unwind while still preserving exact interruption evidence. It
preserves interrupted attempts instead of silently deleting them, and an
interruption during metadata handoff, post-validation, sealing or retirement
keeps the already established pass/fail/interrupted terminal only when outcome,
exit, signal, commands and metadata path all match it. Once a terminal is
established, the complete seal, publication and marker-retirement critical
section masks catchable signals until the attempt and marker are durably
published and revalidated and the held directories are closed, then rethrows
the original signum. A secondary sealing or retirement error may not replace
that signum, nor may a second signal delivered while restoring the mask; if
sealing fails before publication, marker plus staging remain for explicit
recovery. If the attempt directory was published but marker retirement did not
produce its external digest seal, all objects remain fail-closed and that
incomplete boundary is intentionally not reusable. An uncatchable
interruption requires explicit
`--recover-stale` before validated bundle-local staging or exact bounded
regular `running.json`/`approval.json` atomic-write residue can be recovered.
If a catchable signal lands after profile execution but before metadata
establishes an exact profile terminal, the marker/staging boundary is
retained for recovery and the exact signum is rethrown; a secondary sealing
error may not replace it. A non-signal validation failure before publication
also retains that boundary and is not converted into a generic failed attempt.
Post-wait process-group cleanup also compares the retained boot and
process-start identity before any `SIGKILL`; PID reuse produces No-Go without
signalling the unrelated group.
The gate never unlinks such residue or performs check-then-unlink cleanup of
an unpublished temporary: it keeps the validated descriptor open, uses a
no-replace atomic move into
`zh-review-evidence/rootfix-recovered-v1/<bundle-id>/`, and retains the object
under an exact name binding its source form, writer identity, content SHA-256
and recovery identity. Both `run` and read-only `check` fail closed on an
unknown, unsafe, hard-linked, digest-drifted or otherwise malformed archive
object; `check` does not create an absent archive, and a non-empty set of
required seals cannot validate against an archive that disappeared. The
complete first-inventory
bytes, size, digest and inode remain the required baseline before, throughout
and after archive validation, so same-inode content drift is rejected. A
read-to-move regular-file or symlink replacement is retained in that archive
and rejected. The bound staging tree is also moved without replacement and
accepted only under an exact name binding its complete directory-and-file tree
digest; a staging pathname replacement is retained and rejected. Every object
moved by the current invocation remains required by path, inode, size and
digest before and after staging archival. Long-term
retention between invocations is owner-governed; a conforming gate never
deletes the archive. Staging names
must use the exact generated operation-ID grammar: a marker may bind at most
its one directory, and markerless recovery permits at most one valid residue.
Malformed, multiple or unsafe objects fail closed without deletion, and all
clean-tree checks still apply. A new run after immutable failed evidence
requires `--retry-failed`. If a unique passing attempt and its exact
digest-bound retired marker were durably published before `approval.json`
could be written, the next run deterministically completes that approval
without rerunning or deleting the attempt. A published attempt whose marker
was not durably retired has no external digest authority and remains No-Go.

`running.json` is never removed by pathname unlink. Normal attempt publication
and explicit stale recovery both re-read the canonical marker, keep its
pre-read inode and validated descriptor bound, require a positive integer PID
and non-empty process-start and boot identifiers, and use the same no-replace
move into the retained bundle archive. Its exact archive name binds the
operation ID, marker content SHA-256, exact attempt SHA-256 (or explicit
`none`) and recovery identity; a regular-file or symlink replacement is
retained and rejected in both paths. Recovery binds the evidence root,
attempts directory, marker, approval and atomic residue from one first
inventory, and retires and revalidates a valid dead marker before and after
archiving its bound staging residue. Every published attempt must have exactly
one valid retired marker with the same operation ID and digest before pass
reuse, approval or `check`. `run` and `check` independently
re-resolve the archive path at every post-verification and approval boundary,
so an archive absent at startup but created during a long run cannot be hidden
by a cached absence.

The abandoned C2 bundle has no reusable formal attempt: three ledgers lack
strict evidence blocks and their three required inventory artifacts were never
produced. C2 readiness and bundle objects did not migrate. After F2 landed, the
contextual parser, approved R content and required strict ledgers were rebuilt
as a new candidate with new mixed review and a complete normal
verification-v5 final gate. The rootfix exception is permanently expired.

F2 cannot safely authorize that ledger rebuild directly: its
character-mechanics, god and species/background renderers replace the visible
review cards with hash-only strict evidence, while its item and world
renderers omit required development and migration history. The separate
`DCSS-ZH-LEDGER-SEED-2026-07-30` exception permitted only one exact,
externally owner-authorized F2-to-P3 policy installation. P3 changes the five
target-side auditors, their focused tests, the canonical review contract and
its synchronized reviewer copies; it does not change any ledger, translation
asset, glossary, decision file or normal review gate.

Before P3 was installed, the external canonical owner permit bound the
protected ref and exact F2/P3 OIDs, protocol and semantic scope, complete
24-path manifest and digest, binary diff digest, glossary, F2-trusted routing
digest and reviewer set, focused and exact-bound verification results, and an
independent zero-finding review. It authorizes only that exact fast-forward,
never a descendant. P3 became useful only as the trusted target for the next
normal routing-v2 candidate, whose fully rendered ledgers must then pass the
P3 whole-document assertions and the complete ordinary v5 evidence chain.

The review profile includes a required, independent `review-ledgers` phase.
It executes the target checkout's trusted character, god, item, monster,
species/background, and world auditors against the validated candidate root.
Each resulting inventory JSON is an individually required verification-v5
artifact. The phase is unconditional: dependency or glossary drift must fail
even when the corresponding ledger is absent from the prepared diff.

For an exact-bound review, all six auditors share one `AuditSnapshot` identified
by `ZH_VERIFY_AUDIT_ROOT` and the full `ZH_VERIFY_AUDIT_COMMIT`. The snapshot
loads the exact Git tree once, performs discovery from that tree, and reads
each unique regular-file blob at most once. Production inventory content and
membership therefore do not come from mutable worktree paths. Unbound
development fixtures use no-follow descriptor reads with inode identity checks
and reject a path substituted between inspection and open. Focused tests cover
both transient worktree substitution during a bound blob read and a concurrent
swap restored before the unbound caller resumes. The verifier also requires
the exact clean candidate at the end of a bound run. Monster-ledger historical
inputs derive their Git paths lexically below the validated candidate root and
require the exact declared baseline manifest, so a mutable leaf cannot select
another blob from the same commit. World-inventory provenance that refers to
target-side scripts uses a second snapshot bound by `ZH_VERIFY_CONTROL_ROOT`
and `ZH_VERIFY_CONTROL_COMMIT`, so those hashes also come from the exact trusted
control commit rather than its mutable checkout.
Candidate-versus-control routing uses normalized lexical paths below the
already validated roots; it never resolves a mutable input leaf to choose the
snapshot. The world artifact also requires its observed control manifest to
equal the declared target-side control input set exactly.

Every schema-v4 bundle publishes `.bundle.lock` during initial creation.
Only the invocation that atomically creates the new bundle directory may
create that lock, using exclusive creation. A prepare rerun and every later
exclusive writer must open the existing lock read/write; they do not repair a
missing lock. Status, validation and merge-time readers open it with `O_RDONLY`
and `LOCK_SH`; they never create it, and a missing or replaced lock is invalid
evidence. This allows the complete evidence tree to be mounted read-only
without weakening writer serialization. Lockless schema-v3 bundles may be
inspected only as historical, non-authorizing evidence and remain byte-for-byte
untouched.

<!-- End of archived operational notes. -->
