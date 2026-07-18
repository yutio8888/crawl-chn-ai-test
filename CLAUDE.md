# CLAUDE.md — Claude Code Runtime Adapter

> Status: **runtime adapter**. Shared project rules live in `AGENTS.md` and
> `.agents/`; this file only maps them to Claude Code tools.

Read `AGENTS.md` first. Project architecture, safety rules, build commands,
testing, issue tracking, and review evidence are intentionally not duplicated
here.

## Runtime Mapping

- Dispatch project roles with the Claude Code Agent tool when it is available:
  `crawl-coder`, `zh-translator`, `zh-code-reviewer`, and
  `translation-reviewer`.
- Use the read-only Explore role for code search.
- Load the applicable Claude Code skill when the runtime exposes it. The
  compatibility files under `.claude/skills/` remain generated-policy targets;
  do not delete them without updating the synchronizer and tests.
- Use a hosted Workflow tool only when it is explicitly available and accepts
  the repository DSL. Never run `.claude/workflows/*.js` with `node` or `bash`.
- Without a hosted runner, reproduce the `translation-pipeline` phases with
  normal Agent calls and maintain one writer for every translation asset.

## Mandatory Context

Before every translation, i18n implementation, or review dispatch, run:

```bash
bash .claude/scripts/context_resolve.sh "<task>" \
  --task-type <translate|code|review> --files <target-files>
```

Pass the complete output to the Agent and require the glossary SHA-256 in its
result. Follow `docs/agent-routing.md` for role selection and ownership.

## Worktrees, Review, and Commits

- Worktrees must be relative `.worktrees/<name>` paths.
- Follow `.agents/policies/worktree-policy.md`; do not move target refs from a
  linked candidate worktree.
- Translation-related review follows `.agents/policies/review-contract.md`.
- Claude Code-authored commits end with:

```text
Co-Authored-By: Claude <noreply@anthropic.com>
```

Do not use that trailer for work authored by another runtime.

## Shared References

- Authority map: `.agents/README.md`
- Translation architecture: `docs/translation-architecture.md`
- CJK tiles architecture: `docs/cjk-tiles-architecture.md`
- Build and deployment: `docs/build-workflow.md`
- Verification: `docs/zh-testing.md` and `.claude/scripts/TOOLCHAIN.md`
- Cross-runtime handoff: `docs/dual-agent-workflow.md`
- Issue tracking: `docs/issue-tracking.md`
