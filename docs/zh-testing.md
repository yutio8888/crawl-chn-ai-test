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

### Resource-constrained external CI substitution

When the local machine cannot complete the full final profile, the final gate
may substitute a live, bound GitHub Actions run for the contract-listed
phases. First dispatch `.github/workflows/ci.yml` on the candidate ref with
`control_sha` set to the exact final-gate target SHA; the workflow then runs
its verification scripts from a detached target-control checkout and labels
required jobs with that SHA. For example:

```bash
gh workflow run ci.yml --repo yutio8888/crawl-chn-ai-test \
  --ref <candidate-ref> -f control_sha=<target-sha>
```

Run the final gate from the clean target checkout with an exported terminal
type and the resulting exact run id:

```bash
TERM=xterm-256color bash .claude/scripts/review_final_gate.sh \
    <candidate> <target> --github-actions-run <run-id>
```

Only phases that the trusted contract's `external_ci` section lists as
externalizable are replaced (currently the static policy/source/DB/message
overlay gates and the ZH Catch2 runtime gate).
`review-static`, `review-ledgers`, and the ZH smoke/build phases always run locally
because the CI workflow does not claim to cover them. The external proof still
requires every non-optional CI build, lint, tooling, static, and runtime job
listed by the contract. The CI workflow `.github/workflows/ci.yml` is
authoritative for which jobs exist; optional jobs such as "ZH Runtime Full" or
the release job are never treated as required. `gh` must be installed and
authenticated on the control plane; tests use fake `gh` fixtures and never
contact GitHub.

The proof artifact `github-actions-proof.json` is fetched live through `gh`,
bound to the contract repository, exact candidate HEAD, target-control SHA,
allowed workflow event, workflow path and blob (no target/candidate drift),
canonical API snapshots, and every required job's `completed`/`success`
conclusion, then sealed inside the final attempt
and re-verified by the final approval and `review_at_merge.sh`. A caller can
never supply the proof JSON or override the contract repository. Readiness,
review ledgers, and the final approval are not bypassed; without
`--github-actions-run` the gate is byte-for-byte the default fully local flow.

### Current evidence format and recovery history

Current and legacy evidence semantics are authoritative in
`.agents/policies/review-contract.md`. Expired one-time recovery records remain
available in the non-authorizing
[review recovery archive](review-recovery-history.md).

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

The exact Python version is defined once by the root `.python-version` file.
Local tooling commands should run through a version manager that honors it (or
otherwise verify `python3 --version` matches it); CI's setup-python steps read
the same file.
