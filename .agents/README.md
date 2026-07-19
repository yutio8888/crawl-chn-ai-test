# Agent Configuration Authority Map

> Status: **canonical maintenance guide**.

The repository supports multiple agent runtimes. A single source of truth is
defined per concern; no one monolithic file is authoritative for everything.

## Layers

1. `AGENTS.md` is the short, runtime-neutral entry point and always-visible
   safety summary.
2. `.agents/policies/` contains normative shared policy bodies.
3. `.agents/skills/` contains shared repository-scoped skills discovered by
   Pi and Codex.
4. `docs/` contains stable architecture and operational reference material.
5. `.pi/APPEND_SYSTEM.md`, `CODEX.md`, `CLAUDE.md`, and
   `.opencode/RUNTIME.md` are thin syntax adapters.
6. `.pi/agents/`, `.codex/agents/`, `.opencode/agents/`, and `.claude/agents/`
   contain runtime-specific role prompts. Shared policy blocks in those files
   are generated copies.
7. Scripts and runtime configuration are authoritative for command-line
   options, model selection, counts, current branches, and other volatile data.

## Canonical Policy Sources

| Policy | Source | Generated targets |
|---|---|---|
| i18n safety | `.agents/policies/i18n-safety.md` | coder and code-reviewer prompts/skills |
| review contract | `.agents/policies/review-contract.md` | code/translation reviewer prompts/skills |
| asset ownership | `.agents/policies/asset-ownership.md` | coder/translator prompts and runtime pipeline skills |
| verification authoring | `.agents/policies/verification-authoring.md` | coder and code-reviewer prompts/skills |
| translation integrity | `.agents/policies/translation-integrity.md` | translator prompts and translation-pipeline skills |
| worktree policy | `.agents/policies/worktree-policy.md` | referenced by every runtime entry point; OpenCode and Pi add hard runtime guards |
| path portability | `.agents/policies/path-portability.md` | referenced by the shared entry point and enforced by a repository checker |

Generated blocks use `<!-- BEGIN GENERATED: name -->` and
`<!-- END GENERATED: name -->`. Update the canonical policy, then run:

```bash
python3 .claude/scripts/sync_agent_policies.py --write
python3 .claude/scripts/sync_agent_policies.py --check
```

Never edit generated blocks directly.

## Stable References

| Concern | Source |
|---|---|
| Role routing | `docs/agent-routing.md` |
| Build/deployment | `docs/build-workflow.md` |
| Translation design | `docs/translation-architecture.md` |
| CJK tiles design | `docs/cjk-tiles-architecture.md` |
| Verification | `docs/zh-testing.md`, `.claude/scripts/TOOLCHAIN.md` |
| Cross-runtime handoff | `docs/dual-agent-workflow.md` |
| Issue files | `docs/issue-tracking.md` |
| Path portability | `.agents/policies/path-portability.md` |

## Change Rules

- Do not put model names, file counts, test counts, current branch lists, or CI
  job names into runtime adapters unless a machine check owns the value.
- A policy change updates its canonical source and regenerated targets in the
  same commit.
- A command-line documentation change must be checked against the script's
  current `--help` output.
- A compatibility tree may be removed only after its synchronizer targets,
  tests, loaders, and documentation references are removed in the same change.
- Duplicated workflow DSL files must remain byte-identical until an explicit
  hosted runner contract chooses one canonical location.
- Documentation links and forbidden standalone workflow invocations are checked
  by `.claude/scripts/tests/test_agent_docs.py`.
- Machine-specific paths in maintained documentation, configuration, and
  project scripts are rejected by `.claude/scripts/check_path_portability.py`.
