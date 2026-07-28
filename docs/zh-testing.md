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

The sole temporary exception is
`DCSS-ZH-BOOTSTRAP-2026-07-29`, defined in the review contract. It permits new
target-era routing-v1, findings-v1, readiness-v2, and verification-v4 evidence
only for the consecutive recovery edges:

1. `fa0144cb3729e2fdae70e070946fe89f0b6cec15 → S`
2. the exact approved full OID of S `→ C`

Both edges must satisfy the exception's exact path boundary, complete
reviewer-scope declaration, tree-equivalence, glossary, clean-worktree,
full-OID, new-evidence, final-gate, and merge-time conditions. The tools must
come from each edge's trusted target checkout; a newer candidate or unrelated
checkout must not authorize itself.

The exception expires permanently when the approved C full OID is merged into
the dedicated recovery target. `C → R` and every later edge must use the normal
routing-v2, findings-v2, readiness-v3, and verification-v5 workflow. The
exception does not authorize reuse of old evidence, replacement of
`chn-0.34.1-base`, pushing, releasing, or deployment.

The review profile includes a required, independent `review-ledgers` phase.
It executes the target checkout's trusted character, god, item, monster,
species/background, and world auditors against the validated candidate root.
Each resulting inventory JSON is an individually required verification-v5
artifact. The phase is unconditional: dependency or glossary drift must fail
even when the corresponding ledger is absent from the prepared diff.

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
