# Chinese Translation Verification

## Development Profiles

Use one profile matching the active edit:

```bash
bash .claude/scripts/verify_zh.sh --profile translation
bash .claude/scripts/verify_zh.sh --profile code
bash .claude/scripts/verify_zh.sh --profile ci
```

`translation` and `code` default to changed scope. `ci` is the combined static
gate. Read the current options from `verify_zh.sh --help`; do not duplicate an
exhaustive phase list in agent adapters.

Agents that write or review verification controls follow
`.agents/policies/verification-authoring.md`. It is authoritative for complete
invariant coverage, production-semantic fixtures, fail-closed behaviour, and
negative mutation tests; this document does not duplicate that contract.

The report is written below `.claude/metrics/verify/`. Agents report the exact
command, exit code, blocking failure count, and relevant warnings rather than
only saying that verification “passed”.

## Runtime Evidence

The runtime suite combines:

- Catch2 translation and message-overlay checks;
- dlua translation/database smoke tests, including ZH canonical-English
  identity assertions for the five protocol-facing `you.*` bindings;
- RC bot UI and gameplay workflows;
- aggregation against version-controlled baselines.

The identity runtime case also constructs the named
`heliophobic_arrival_battle_scene` arrival vault through the production Vault
path; it fails if the vault cannot be found or placed, rather than claiming
coverage from a parser-only check. Use `.claude/scripts/post_zh_runtime.sh --help` and `.claude/scripts/TOOLCHAIN.md`
for current modes and artifact locations. Avoid
hard-coded test/assertion/marker counts in prose because the suites evolve.

Expensive suites such as full runtime, help-full, or the tooling test suite run
only when required by the task/release contract and against the final reviewed
candidate. A requested fix creates a new targeted development loop instead of
rerunning all expensive evidence on a rejected candidate.

A newly created linked worktree has empty directories for recorded contrib
submodules. Before preparing an immutable candidate for final review, initialize
its exact gitlinks and confirm that the superproject remains clean:

```bash
git submodule update --init --recursive
git status --porcelain=v1 --untracked-files=all
```

Submodule initialization is environment preparation, not candidate content. If
an immutable final attempt fails only because a recorded build dependency was
not initialized, retain that failed attempt, initialize the exact gitlinks,
reconfirm the candidate OID and clean state, and use the documented
`--retry-failed` path.

## Review Evidence

Review readiness and final verification are separate:

1. commit the candidate and require clean target/candidate worktrees;
2. run `review_prepare.sh <candidate> <target>` from the target checkout;
3. dispatch only reviewers named by the prepared bundle routing;
4. persist each reviewer's complete structured findings; the bundle tool derives
   severity counts and readiness;
5. run `review_final_gate.sh <candidate> <target>` once;
6. immediately before merge, run the read-only
   `review_at_merge.sh <candidate> <target>` and merge the approved OID.

### Headless terminal requirement

Run the final gate from the clean target checkout with an explicitly exported,
installed terminal type:

```bash
TERM=xterm-256color bash .claude/scripts/review_final_gate.sh \
    <candidate> <target>
```

This matters even when `printf '%s\n' "$TERM"` prints `dumb`: some automation
shells create that as a shell-local fallback without exporting it. The final
gate starts its verifier through a sanitized Python environment, so ncurses may
instead receive no `TERM`, report
`ncurses: cannot initialize terminal type ($TERM="unknown")`, and make
`zh-smoke` report `Crawl exited with unexpected code 1`.

Check the exported value and the local terminfo entry rather than relying on
shell expansion:

```bash
printenv TERM
infocmp xterm-256color >/dev/null
TERM=xterm-256color bash .claude/scripts/smoke_test.sh
```

If a final attempt failed only because `TERM` was missing or invalid, keep the
failed evidence and retry through the supported path; do not delete or rewrite
the bundle:

```bash
TERM=xterm-256color bash .claude/scripts/review_final_gate.sh \
    <candidate> <target> --retry-failed
```

An explicit valid `TERM` only permits ncurses startup. It does not skip static
checks, compilation, runtime tests, readiness binding, or evidence sealing.

Reviewers never run `verify_zh.sh --profile review` themselves. The complete
security contract is `.agents/policies/review-contract.md`.

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

## CI

The current CI definition is `.github/workflows/ci.yml`; it is authoritative
for job names and commands. Agent documentation should link to it instead of
copying job inventories that drift.

The tooling suite and combined static gate run on both Ubuntu and macOS. The
macOS lane deliberately uses the system `/bin/bash` contract, so generic
verification scripts must remain compatible with Bash 3.2 and BSD userland.
Python 3, Node.js, `tree-sitter`, `tree-sitter-cpp`, and PyYAML are installed
explicitly in CI; GNU `timeout`, `flock`, `grep -P`, and GNU `script` are not
generic-tooling prerequisites. Target-only Windows, Android, and Tiles helpers
may retain dependencies documented by their target build workflow.
