# AGENTS.md — Shared Agent Entry Point

> Status: **canonical shared instructions**. This file is intentionally
> runtime-neutral. Runtime-specific tool syntax belongs in
> `.pi/APPEND_SYSTEM.md`, `CODEX.md`, or `DSH.md`.

This repository contains the DCSS Chinese translation, i18n tooling, and CJK
tiles work. Read this file first in every agent runtime. For the source-of-truth
map and maintenance rules, see `.agents/README.md`.

## Runtime Adapter

After this file, read only the adapter for the active runtime:

| Runtime | Adapter |
|---|---|
| Pi | `.pi/APPEND_SYSTEM.md` |
| Codex | `CODEX.md` |
| DSH | `DSH.md` (experimental compatibility contract) |

Adapters translate tool syntax only. They must not weaken the shared policies
in this file or `.agents/policies/`.

The source map below is a lookup index, not a reading checklist. Read only the
sections needed for the active task. Reuse already loaded, unchanged context;
locating files does not require first reading architecture or terminology docs.
Session instructions and existing user authorization govern permissions.

## Canonical Sources

| Concern | Authority |
|---|---|
| Runtime roles and task routing | `docs/agent-routing.md` |
| Translation terminology | `docs/glossary.md` |
| i18n safety | `.agents/policies/i18n-safety.md` |
| Translation-asset ownership | `.agents/policies/asset-ownership.md` |
| Review findings and domain review | `.agents/policies/review-contract.md` |
| Worktree placement and branch safety | `.agents/policies/worktree-policy.md` |
| Portable repository and external paths | `.agents/policies/path-portability.md` |
| Translation architecture | `docs/translation-architecture.md` |
| CJK tiles architecture | `docs/cjk-tiles-architecture.md` |
| Build and deployment | `docs/build-workflow.md` |
| ZH testing and verification | `docs/zh-testing.md` and `.claude/scripts/TOOLCHAIN.md` |
| Cross-runtime collaboration | `docs/dual-agent-workflow.md` |
| Issue tracking | `docs/issue-tracking.md` |

Do not copy model assignments, script counts, branch lists, test counts, or
other volatile state into prose. Read the corresponding configuration, Git
state, script `--help`, or CI workflow instead.

## Minimal Sufficient Design

- Optimize for the fewest new concepts needed to satisfy confirmed acceptance
  criteria.
- Before planning, identify acceptance criteria, explicit non-goals, and
  existing repository mechanisms that can be extended.
- Prefer modifying an existing script, test, Skill, or verification entry
  point.
- Choose routine implementation details, helper files, and directories within
  the accepted scope autonomously. Explain material design choices briefly.
- Reviewer findings do not automatically expand task scope. Resolve them by
  deleting, reusing, or narrowing before adding mechanisms.
- Escalate an unapproved external dependency, persistent mechanism, material
  scope expansion, or product tradeoff requiring user input. Existing approval
  remains valid; continue independent authorized work while a decision is pending.

## Mandatory Terminology Context

Before making translation or terminology judgments, resolve relevant terms
from the current worktree (initial file discovery can happen first):

```bash
bash .claude/scripts/context_resolve.sh "<task>" \
  --task-type <translate|code|review> --files <target-files>
```

Share that output with agents making the same judgments and reuse it within
the task. Refresh when the file scope or relevant glossary context changes;
refresh the digest for final translation evidence after any glossary change.
Preserve its SHA-256 in formal translation reports. Pure tooling, structural,
or governance work does not require terminology or a glossary hash unless it
makes a terminology decision. Never embed a fixed terminology list in prompts.

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
| Complete enumerable translation-category or series audit | `batch-translation-review` skill |

Translation assets have one writer per task. By default, `zh-translator` owns
`crawl-ref/source/dat/i18n/zh/`, `crawl-ref/source/dat/database/zh/`, and
`crawl-ref/source/dat/descript/zh/`; `crawl-coder` owns source and build files.
A coder may receive an explicitly scoped structural
repair in a ZH data file only when it is the sole writer for that path. Mixed
tasks follow dependency order, with assets updated by their owner as interfaces
settle. See
`.agents/policies/asset-ownership.md`.

## Worktrees and Branches

All new worktrees must use a relative path inside the repository:

```bash
git worktree add .worktrees/<name> <branch>
```

Never create a worktree under an absolute path, `~`, `../`, or the deprecated
`.claude/worktrees/`. Pi additionally enforces this with
`.pi/extensions/enforce-worktree-path.ts`. Follow the complete shared policy in
`.agents/policies/worktree-policy.md`.

Repository documentation and script defaults must not embed clone-specific
home directories, drive letters, or mount points. Use repository-root-relative
paths and documented environment variables as defined by
`.agents/policies/path-portability.md`.

Do not move another branch ref from inside a linked worktree. Commit in the
candidate worktree, then merge the commit that passed verification, domain
review, and CI from the target checkout. Dedicated detached build worktrees
may be reset only through their guarded helper scripts or after the documented
clean-tree check in `docs/build-workflow.md`.

## Verification

Use the single matching development profile; do not run a dozen individual
scripts or serially run every profile against one candidate.

| Change | Command |
|---|---|
| Read-only review | Inspect the requested scope and existing evidence; no automatic build |
| Governance/docs/tooling | Focused existing checks; `code` profile for verification-tool changes |
| Translation or ZH data | `bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile translation` |
| C++ or i18n code | `bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile code` |
| Combined static CI preflight | `bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile ci` |

For committed candidates, append `--base <base> --head <candidate>` to the
matching profile: unbound changed scope covers only uncommitted work. Route
merge review with `classify_reviewers.py` and merge only after applicable
GitHub Actions CI passes. Ordinary review accepts files or a worktree diff.
See `docs/zh-testing.md` and `.agents/policies/review-contract.md`.

Use at most eight build jobs. Agents compiling alongside other work should use
`-j4`, and concurrent agents must not start overlapping compile storms.

## Resource Isolation

Heavy Python tests, `unittest discover`, and `verify_zh.sh` profiles run
inside the Paseo daemon cgroup by default and can exhaust its memory/CPU
budget, severing the outer connection. Launch them through the isolation
wrapper instead of a bare `python3` or `bash`:

```bash
bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_monspeak_inventory.py
bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile translation
```

The wrapper starts a transient service in `paseo-workers.slice` with
`MemoryHigh`/`MemoryMax`/`CPUWeight`/`CPUQuota` limits when a user-level
systemd session and the slice exist; otherwise it falls back to a direct
`exec` so CI and non-systemd environments stay portable. `fork`/`nohup`/
`setsid`/`start_new_session` cannot escape the parent cgroup and must not be
used for this purpose. Per-command limits do not cap concurrent workers; for
`run_all.sh`-style concurrency set an aggregate cap on the slice via a
machine-local user drop-in. See `.claude/scripts/TOOLCHAIN.md` for overrides.

## Commit Attribution

Authorship must match the runtime that actually produced the change. Follow the
active runtime's declared identity policy; if no trailer is required, omit it
rather than inventing or borrowing an identity.

Branch names are an ownership signal: Pi uses `pi/<topic>`, Codex uses
`codex/<topic>`, and DSH uses `dsh/<topic>` unless the user requests another name.

## Task Completion and Cleanup

- Use the user's requested endpoint: review report, implemented change, merge,
  or release. Skills do not add Git actions or external publication authority.
- Review-only work is complete with findings, evidence, and any coverage gaps.
- Implementation is complete when acceptance criteria are met, relevant checks
  pass, introduced blocking defects are resolved, the final diff is inspected,
  and already-authorized delivery steps are done. Do not ask again for existing
  approval or stop at an offer to finish those steps.
- Reuse valid verification. Repeat or broaden it only for new changes, failures,
  or unresolved evidence gaps. Report genuine blockers without claiming success;
  continue work that does not depend on the missing input.
- Remove only this task's disposable temporary artifacts. Do not clean others'
  files to satisfy a clean-tree gate. Branch/worktree removal requires known
  ownership, delivered work, no active user, and authorization; retain shared
  caches and dedicated build worktrees. Do not clean the whole repository.
- Write PR/Issue comments only when authorized; use existing issue/PR records
  for cross-session handoff, not an extra local status system.

## Configuration Maintenance

Shared policy bodies live only in `.agents/policies/`. Generated copies inside
Pi and Codex Agent files follow the maintenance procedure in
`.agents/README.md`. Do not edit generated blocks directly. Before changing or
removing a compatibility tree, update the source map, synchronizer, tests, and
every runtime reference in the same change.
