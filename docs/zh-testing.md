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
coverage from a parser-only check. Use `.claude/scripts/post_zh_runtime.sh
--help` and `.claude/scripts/TOOLCHAIN.md` for current modes and artifact
locations. Avoid
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
security contract is `.agents/policies/review-contract.md`. New authorization
uses schema-v4 bundles with schema-v2 atomic readiness; schema-v3 bundles are
historical read-only evidence.

## CI

The current CI definition is `.github/workflows/ci.yml`; it is authoritative
for job names and commands. Agent documentation should link to it instead of
copying job inventories that drift.
