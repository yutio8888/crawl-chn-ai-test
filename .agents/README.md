# Agent Configuration Authority Map

> Status: **canonical maintenance guide**.

The repository supports multiple agent runtimes. A single source of truth is
defined per concern; no one monolithic file is authoritative for everything.

## Layers

1. `AGENTS.md` is the short, runtime-neutral entry point and always-visible
   safety summary.
2. `.agents/policies/` contains normative shared policy bodies.
3. `.agents/skills/` contains repository-scoped Codex skills.
4. `docs/` contains stable architecture and operational reference material.
5. `CODEX.md`, `CLAUDE.md`, and `.opencode/RUNTIME.md` are thin syntax adapters.
6. `.codex/agents/`, `.opencode/agents/`, and `.claude/agents/` contain
   runtime-specific role prompts. Shared policy blocks in those files are
   generated copies.
7. Scripts and runtime configuration are authoritative for command-line
   options, model selection, counts, current branches, and other volatile data.

## Canonical Policy Sources

| Policy | Source | Generated targets |
|---|---|---|
| i18n safety | `.agents/policies/i18n-safety.md` | coder and code-reviewer prompts/skills plus the translation-context skill |
| review contract | `.agents/policies/review-contract.md` | code/translation reviewer prompts/skills plus the translation-context skill |
| asset ownership | `.agents/policies/asset-ownership.md` | coder/translator prompts and relevant skills |
| worktree policy | `.agents/policies/worktree-policy.md` | referenced by every runtime entry point; OpenCode adds a hard plugin guard |

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
