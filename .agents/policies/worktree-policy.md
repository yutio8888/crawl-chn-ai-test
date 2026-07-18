# worktree-policy-v1

All repository worktrees must be created from the repository root with a
relative path below `.worktrees/`:

```bash
git worktree add .worktrees/<name> <branch>
```

- Do not use absolute targets, `~`, `../`, or `.claude/worktrees/`.
- Do not bypass `.opencode/plugin/enforce-worktree-path.js`.
- A linked worktree owns its checked-out branch. Do not push, merge, update-ref,
  or otherwise move a different target branch from inside it.
- Commit candidate changes in the candidate worktree. Prepare and review that
  immutable commit, then merge the approved OID from the target checkout.
- Never use `git reset --hard` as routine development synchronization.

Dedicated detached build worktrees are the only exception to the reset rule.
Their helper scripts may reset them to the main checkout's exact HEAD only
after refusing a dirty worktree. Manual operation must reproduce the same
clean-tree guard documented in `docs/build-workflow.md`.

Before merging, both target and candidate worktrees must be clean. Translation
candidates additionally follow the schema-v4 process in
`.agents/policies/review-contract.md`.
