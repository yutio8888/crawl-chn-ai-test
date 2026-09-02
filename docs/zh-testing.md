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

A newly created linked worktree has empty directories for recorded contrib
submodules. Before verification on a candidate, initialize its exact gitlinks
and confirm that the superproject remains clean:

```bash
git submodule update --init --recursive
git status --porcelain=v1 --untracked-files=all
```

Submodule initialization is environment preparation, not candidate content.

## Domain Review and Merge

Review is a human-readable domain-review phase, separate from the development
verification above:

1. commit the candidate and require a clean worktree;
2. run the single matching `verify_zh.sh` development profile
   (`translation`, `code`, or `ci`);
3. route reviewers with
   `python3 .claude/scripts/classify_reviewers.py --base <target> --head <candidate>`
   and dispatch only the routed domain reviewers;
4. reviewers record Blocker / Needs Fix / Suggestion findings plus a Ready or
   Changes Requested conclusion as plain text in the PR/issue;
5. existing GitHub Actions CI (`.github/workflows/ci.yml`) must pass;
6. merge from the target checkout.

The complete review contract is `.agents/policies/review-contract.md`. There is
no separate final evidence gate, immutable bundle, readiness object, or local
merge authorization. Expired one-time recovery records remain available in the
non-authorizing [review recovery archive](review-recovery-history.md).

## CI

The current CI definition is `.github/workflows/ci.yml`; it is authoritative
for job names and commands. Agent documentation should link to it instead of
copying job inventories that drift.

The tooling suite and combined static gate run on both Ubuntu and macOS. The
macOS lane deliberately uses the system `/bin/bash` contract, so generic
verification scripts must remain compatible with Bash 3.2 and BSD userland.
The tooling suite reads the candidate `.claude/scripts/tests/run_all.sh` entry
from the exact candidate commit's Git blob, while preserving its
candidate-worktree path as `$0` so it discovers the candidate tests, and fixes
`PYTHONSAFEPATH=1` and `ZH_TOOLING_TEST_JOBS=2`.
Python 3, Node.js, `tree-sitter`, `tree-sitter-cpp`, and PyYAML are installed
explicitly in CI; GNU `timeout`, `flock`, `grep -P`, and GNU `script` are not
generic-tooling prerequisites. Target-only Windows, Android, and Tiles helpers
may retain dependencies documented by their target build workflow.

The exact Python version is defined once by the root `.python-version` file.
Local tooling commands should run through a version manager that honors it (or
otherwise verify `python3 --version` matches it); CI's setup-python steps read
the same file.
