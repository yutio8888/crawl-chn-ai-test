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
- dlua translation/database smoke tests;
- RC bot UI and gameplay workflows;
- aggregation against version-controlled baselines.

Use `.claude/scripts/post_zh_runtime.sh --help` and
`.claude/scripts/TOOLCHAIN.md` for current modes and artifact locations. Avoid
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

Reviewers never run `verify_zh.sh --profile review` themselves. The complete
security contract is `.agents/policies/review-contract.md`. New authorization
uses schema-v4 bundles with schema-v2 atomic readiness; schema-v3 bundles are
historical read-only evidence.

## CI

The current CI definition is `.github/workflows/ci.yml`; it is authoritative
for job names and commands. Agent documentation should link to it instead of
copying job inventories that drift.
