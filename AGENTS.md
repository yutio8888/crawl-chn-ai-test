# AGENTS.md — Shared Agent Entry Point

> Status: **canonical shared instructions**. This file is intentionally
> runtime-neutral. Runtime-specific tool syntax belongs in `CODEX.md`,
> `CLAUDE.md`, or `.opencode/RUNTIME.md`.

This repository contains the DCSS Chinese translation, i18n tooling, and CJK
tiles work. Read this file first in every agent runtime. For the source-of-truth
map and maintenance rules, see `.agents/README.md`.

## Runtime Adapter

After this file, read only the adapter for the active runtime:

| Runtime | Adapter |
|---|---|
| OpenCode | `.opencode/RUNTIME.md` |
| Codex | `CODEX.md` |
| Claude Code | `CLAUDE.md` |

Adapters translate tool syntax only. They must not weaken the shared policies
in this file or `.agents/policies/`.

## Canonical Sources

| Concern | Authority |
|---|---|
| Runtime roles and task routing | `docs/agent-routing.md` |
| Translation terminology | `docs/glossary.md` |
| i18n safety | `.agents/policies/i18n-safety.md` |
| Translation-asset ownership | `.agents/policies/asset-ownership.md` |
| Review findings and final evidence | `.agents/policies/review-contract.md` |
| Worktree placement and branch safety | `.agents/policies/worktree-policy.md` |
| Translation architecture | `docs/translation-architecture.md` |
| CJK tiles architecture | `docs/cjk-tiles-architecture.md` |
| Build and deployment | `docs/build-workflow.md` |
| ZH testing and verification | `docs/zh-testing.md` and `.claude/scripts/TOOLCHAIN.md` |
| Cross-runtime collaboration | `docs/dual-agent-workflow.md` |
| Issue tracking | `docs/issue-tracking.md` |

Do not copy model assignments, script counts, branch lists, test counts, or
other volatile state into prose. Read the corresponding configuration, Git
state, script `--help`, or CI workflow instead.

## Mandatory Terminology Context

For every translation, i18n implementation, or translation review task, resolve
terminology from the current worktree immediately before dispatch or editing:

```bash
bash .claude/scripts/context_resolve.sh "<task>" \
  --task-type <translate|code|review> --files <target-files>
```

Pass the complete output to every applicable agent. Preserve the emitted
`docs/glossary.md` SHA-256 in the final report. If the glossary changes, rerun
the resolver before continuing. Never embed a fixed canonical terminology list
in an Agent, Skill, workflow, or runtime adapter.

## Task Routing

Use the project role when the active runtime exposes it. If that role is not
available, follow the same contract inline. Full boundaries and examples are in
`docs/agent-routing.md`.

| Task | Role |
|---|---|
| Translate or revise Chinese game text | `zh-translator` |
| C++, Lua, build, TextDB loader/schema, or code-side `T_()` work | `crawl-coder` |
| Translation wording, terminology, completeness, or voice review | `translation-reviewer` |
| i18n implementation, protocol/display, format, or database review | `zh-code-reviewer` |
| Verbatim text extraction from a screenshot or image | `ocr` |
| Read-only code search | runtime read-only explorer |
| End-to-end translation bug | `translation-pipeline` skill or its documented fallback |

Translation assets have one writer per task. By default, `zh-translator` owns
`dat/i18n/zh/`, `dat/database/zh/`, and `dat/descript/zh/`; `crawl-coder` owns
source and build files. A coder may receive an explicitly scoped structural
repair in a ZH data file only when it is the sole writer for that path. Mixed
tasks execute translation-asset edits first and code edits second. See
`.agents/policies/asset-ownership.md`.

## Workflow Execution

Files under `.opencode/workflows/` and `.claude/workflows/` use a hosted DSL
with injected `args`, `agent()`, `parallel()`, `phase()`, and `log()` globals.
They are not standalone shell or Node.js programs.

- Use them only when the active runtime explicitly exposes a compatible hosted
  workflow runner.
- Never run them with `bash`, `node`, or another ordinary interpreter.
- Without a runner, load `translation-pipeline` and reproduce its documented
  phases with the runtime's normal agent tools.
- Keep every ZH translation asset under one writer throughout the fallback.

## Worktrees and Branches

All new worktrees must use a relative path inside the repository:

```bash
git worktree add .worktrees/<name> <branch>
```

Never create a worktree under an absolute path, `~`, `../`, or the deprecated
`.claude/worktrees/`. OpenCode additionally enforces this with
`.opencode/plugin/enforce-worktree-path.js`. Follow the complete shared policy
in `.agents/policies/worktree-policy.md`.

Do not move another branch ref from inside a linked worktree. Commit in the
candidate worktree, prepare and review the immutable candidate, then merge the
approved commit from the target checkout. Dedicated detached build worktrees
may be reset only through their guarded helper scripts or after the documented
clean-tree check in `docs/build-workflow.md`.

## Verification

Use the single matching development profile; do not run a dozen individual
scripts or serially run every profile against one immutable candidate.

| Change | Command |
|---|---|
| Translation or ZH data | `bash .claude/scripts/verify_zh.sh --profile translation` |
| C++ or i18n code | `bash .claude/scripts/verify_zh.sh --profile code` |
| Combined static CI preflight | `bash .claude/scripts/verify_zh.sh --profile ci` |
| Final evidence | `bash .claude/scripts/review_final_gate.sh <candidate> <target>` |
| Merge-time validation | `bash .claude/scripts/review_at_merge.sh <candidate> <target>` |

The `review` profile is final-gate internal. Reviewers do not run it during
readiness. Prepare the exact committed, clean boundary with
`review_prepare.sh`, dispatch only mechanically routed reviewers, record their
readiness, and let `review_final_gate.sh` own the single final run. See
`.agents/policies/review-contract.md`.

Use at most eight build jobs. Agents compiling alongside other work should use
`-j4`, and concurrent agents must not start overlapping compile storms.

## Commit Attribution

Authorship must match the runtime that actually produced the change:

- OpenCode-authored commits use
  `Co-Authored-By: opencode <noreply@opencode.ai>`.
- Claude Code-authored commits use
  `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Other runtimes must follow their own declared identity policy and must not
  claim OpenCode or Claude authorship. If no trailer is required, omit it rather
  than inventing or borrowing an identity.

Branch names are an ownership signal: Codex uses `codex/<topic>`; OpenCode uses
`<topic>` or `consolidate-*` unless the user requests another name.

## Configuration Maintenance

Shared policy bodies live only in `.agents/policies/`. Generated copies inside
runtime Agent and Skill files are maintained by:

```bash
python3 .claude/scripts/sync_agent_policies.py --check
python3 .claude/scripts/sync_agent_policies.py --write
```

Do not edit generated blocks directly. Do not delete `.claude/agents/` or
`.claude/skills/` as “legacy” while they remain synchronization and test
targets. Before changing or removing a compatibility tree, update the source
map, synchronizer, tests, and every runtime reference in the same change.
