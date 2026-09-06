# worktree-policy-v1

All repository worktrees must be created from the repository root with a
relative path below `.worktrees/`:

```bash
git worktree add .worktrees/<name> <branch>
```

- Do not use absolute targets, `~`, `../`, or `.claude/worktrees/`.
- A linked worktree owns its checked-out branch. Do not push, merge, update-ref,
  or otherwise move a different target branch from inside it.
- Keep the repository's designated integration/base branch unowned by linked
  worktrees so the primary checkout can switch back to it at any time. Never
  check that branch out when creating or repurposing a linked worktree; use a
  task branch or detached HEAD instead.
- Commit candidate changes in the candidate worktree. Prepare and review that
  immutable commit, then merge the approved OID from the target checkout.
- Never use `git reset --hard` as routine development synchronization.

Dedicated detached build worktrees are the only exception to the reset rule.
Their helper scripts may reset them to the main checkout's exact HEAD only
after refusing a dirty worktree. Manual operation must reproduce the same
clean-tree guard documented in `docs/build-workflow.md`.

Before merging, both target and candidate worktrees must be clean. Do not
discard unrelated work to achieve this; use a suitable checkout when necessary.
Merge review follows `.agents/policies/review-contract.md`. Ordinary review
does not require a clean or committed worktree.

Reuse an appropriate existing checkout. Create a worktree when isolation is
needed, not for every task. Remove only an authorized task-owned worktree or
branch whose work is delivered and which nobody is using. Keep shared caches
and dedicated build worktrees; repository-wide cleanup is not routine closure.
