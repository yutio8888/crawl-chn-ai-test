# DSH Runtime Adapter — Compatibility Contract v1

> Status: **experimental, documentation-level adapter**. Shared policy remains
> in [AGENTS.md](AGENTS.md) and [.agents/README.md](.agents/README.md).

## Activation and Scope

Read `AGENTS.md`, then this file when the active runtime is DSH, regardless of
which model supplies the session. Do not load another runtime's adapter.
This file is a repository convention, not a claim that DSH automatically loads
`DSH.md`. If shared instructions were not loaded, explicitly ask the session to
read `AGENTS.md` and `DSH.md` before work. Use `pwd` and Git state to confirm the
checkout; the harness installation directory is not the project directory.

This version reuses shared policies, skills, scripts, and handoff artifacts.
It does not install plugins, register native roles, copy generated prompts,
change model/provider settings, or replace Pi/Codex configuration. The missing
DSH adapter is addressed with one file rather than a new configuration tree.

## Capability and Tool Mapping

The active session's tool schemas and higher-priority instructions are the
source of truth; this table applies only when those tools are exposed.

| Repository operation | DSH mapping |
|---|---|
| Inspect files and search | `read`, `glob`, `grep`; `read_image` for images |
| Modify files | Read first; `edit` for targeted changes, `write` for new files |
| Run scripts and Git | `bash`; supply `workdir` per call; inspect exit status |
| Load a shared skill | `skill` with its exact catalog name |
| Delegate bounded work | `subagent` with a self-contained task |
| Delegate inherited context | `subagent_fork`; still state role and file ownership |
| Continue a direct child | `send_message` with its returned agent id |
| Start background work | `bash` / delegation tools: `run_in_background: true` |
| Track shell jobs | `job_output` / `job_kill` with the returned job id |
| Track multi-step work | `todo_write` |
| Confirm a decision | `ask_user_question` |

Do not translate Codex/Pi invocation syntax literally. In shared skill text,
`$dcss-translation-context` means load `dcss-translation-context` via `skill`;
other skill names map the same way. If a skill is absent from the catalog,
read its existing `.agents/skills/<name>/SKILL.md` and follow it inline; report
missing capabilities rather than inventing a DSH-only copy or skipping a gate.

## Roles and Delegation

Use [docs/agent-routing.md](docs/agent-routing.md) and its linked canonical
policies. Generic DSH subagents do not automatically load `.pi/agents/` or
`.codex/agents/`, and a role label is not a registered native role.
If no specialized role exists, follow the shared role contract inline or
explicitly supply it to a generic child. A dispatch must include:

- role, objective, acceptance criteria, non-goals, and exact checkout;
- `AGENTS.md`, `DSH.md`, routing and applicable canonical policy references;
- allowed files, sole-writer assignment, dependencies, and read-only limits;
- complete fresh `context_resolve.sh` output for applicable tasks;
- verification required, candidate range for review, and expected report.

Read-only explorer/reviewer assignments are behavioral constraints, not a claim
of tool-level sandbox enforcement. Never delegate to escape session permissions.
Use independent reviewers for required domain review; self-check is not an
independent approval. If unavailable, report the gap and leave merge pending.

Default independent delegations to background execution; do useful independent
work while they run. Collect completion evidence before dependent work. Keep
agent ids separate from job ids and follow each tool's result-delivery contract.
Do not assume children have isolated worktrees. Analysis may run in parallel,
but translation assets are written sequentially by their single owner per
`.agents/policies/asset-ownership.md`; for other paths assign disjoint writes
or run sequentially.

## Execution, Safety, and Completion

- Honor the active file sandbox and approval policy. A denial is not permission
  to retry via another tool; use only the runtime's authorized escalation path.
- Follow [.agents/policies/worktree-policy.md](.agents/policies/worktree-policy.md).
  Pi's extension guard is not present merely because DSH reads this repository.
- New DSH-owned branches default to `dsh/<topic>` unless the user says otherwise;
  do not rename an existing branch or infer authorship from the model provider.
  Follow the runtime identity policy; omit undeclared co-author trailers.
- Use existing verification and resource-isolation commands from `AGENTS.md`.
  DSH background jobs do not themselves provide resource isolation.
- Use goal tools for long-running same-session objectives, not routine tasks.
  `workflow` requires an explicit workflow or large-orchestration request;
  `ralph` requires an explicit Ralph/fresh-agent iteration request.
  These tools do not replace verification, domain review, or CI evidence.
- Follow [docs/dual-agent-workflow.md](docs/dual-agent-workflow.md) for handoff.
  DSH session goals, todos, and child memory are not cross-runtime authority.
- Report changed paths, executed checks, failures and unverified requirements.
  Preserve the glossary SHA-256 for tasks requiring terminology context.

## Trial Acceptance

A trial session must demonstrate entry loading, shared skill loading (or its
explicit fallback), scoped role dispatch (or inline fallback), and an existing
matching verification command. A parallel trial must also demonstrate sole
writer ownership and completion collection. Record observed results in the
normal issue/PR; passing documentation tests alone does not prove runtime
loading, permission enforcement, or end-to-end translation compatibility.
