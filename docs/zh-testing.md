# Chinese Translation Verification

## Development Profiles

Use focused existing checks during development, then one profile matching the
coherent change when it affects translation, game code, or verification tools:

```bash
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile translation
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile code
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile ci
```

`translation` and `code` default to changed scope. Without a bound range, they
inspect only changes relative to HEAD, including untracked files. A clean
worktree does not mean the last commit has been verified. For a committed
candidate, use the matching profile with an explicit range, for example:

```bash
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh \
  --profile code --base <base> --head <candidate>
```

The bound candidate must be checked out and clean. Do not discard unrelated
work to meet that condition. Reuse earlier verification if the tested content
and relevant dependencies are unchanged; record the scope covered by the evidence.

| Task | Local verification |
|---|---|
| Read-only review | Inspect scope and existing logs; targeted checks only to resolve concrete uncertainty |
| Policy/docs only | Existing documentation, configuration, and sync checks; no game build |
| Verification tooling | Relevant regression tests and `code` profile |
| Translated assets | `translation` profile, preserving global key/structure integrity |
| C++/i18n | `code` profile and affected target/runtime checks selected by risk |
| Mixed assets and code | `code` profile plus focused translation checks; use `ci` instead when combined full static preflight is needed, with runtime checks separately if required |

Known governance-only changes skip game static and overlay phases in local
changed mode. Relevant source/data and validator dependencies retain global
integrity checks; overlay dependencies select the heavy overlay suite. Unknown
paths are conservative. `ci` and full scope retain their full static coverage.
Skipping unrelated phases does not verify the changed tool: run its focused
tests. Read current options from `verify_zh.sh --help`.

The miscname exact-candidate integration test needs committed inputs. A dirty,
unbound changed run explicitly skips that case while exercising its fixture
regressions; bound and CI/full runs retain the clean-candidate check. Report
the skip as unavailable candidate evidence, not a successful integration run.

Agents that write or review verification controls follow
`.agents/policies/verification-authoring.md` for coverage proportional to the
tool's claimed guarantees, realistic fixtures, and blocking versus advisory
behavior. No new end-to-end test is needed when existing coverage is sufficient.

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
submodules. Before a build or a check that needs contrib dependencies,
initialize its exact gitlinks and confirm the superproject remains clean:

```bash
git submodule update --init --recursive
git status --porcelain=v1 --untracked-files=all
```

Submodule initialization is environment preparation, not candidate content.

## Domain Review and Merge

Ordinary review accepts existing files or uncommitted changes and reports
findings plus Validation Gaps. It does not require a build, commit, or remote
comment. For an authorized merge:

1. commit the candidate and require a clean worktree;
2. verify the matching profile with `--base <base> --head <candidate>`, or reuse
   valid evidence for unchanged content and dependencies;
3. route reviewers with
   `python3 .claude/scripts/classify_reviewers.py --base <target> --head <candidate>`
   and apply the routed domains, inline when delegation is unavailable or unnecessary;
4. reviewers report findings, Validation Gaps, and Ready or Changes Requested;
   post to the PR/issue only when authorized;
5. applicable GitHub Actions CI (`.github/workflows/ci.yml`) must pass; use the
   existing PR or manual workflow, since a task branch alone does not trigger CI;
6. merge from the target checkout.

The complete review contract is `.agents/policies/review-contract.md`. There is
no separate final evidence gate, immutable bundle, readiness object, or local
merge authorization. Expired one-time recovery records remain available in the
non-authorizing [review recovery archive](review-recovery-history.md).

Verification is not restarted solely because the task advances to review or
delivery. New changes, failures, or missing evidence justify additional checks.
Task completion and cleanup follow `AGENTS.md`; do not apply release gates to
ordinary development.

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
