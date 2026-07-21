# GitHub Issue Tracking

GitHub Issues in `yutio8888/crawl-chn-ai-test` are the single source of truth
for problems, current status, acceptance criteria, priority, assignee, and
milestone:

<https://github.com/yutio8888/crawl-chn-ai-test/issues>

Use explicit repository selection in automation and agent commands. Do not
infer the tracker from a local remote named `origin`:

```bash
gh issue view <number> --repo yutio8888/crawl-chn-ai-test
gh issue create --repo yutio8888/crawl-chn-ai-test
gh issue comment <number> --repo yutio8888/crawl-chn-ai-test
```

## Information Boundaries

| Information | Authority |
|---|---|
| Problem, status, acceptance criteria, priority, owner | GitHub Issue |
| Implementation, code review, and CI evidence | Pull request |
| Durable architecture, terminology, and decisions | Repository documentation |
| Pre-cutover analysis, plans, and reviews | Read-only legacy archive |

The legacy issue repository was frozen on 2026-07-21. It is historical
evidence only and must not receive new files, numbers, status updates, or
handoffs. Its public archive is intended to live at:

<https://github.com/yutio8888/crawl-chn-issues-archive>

## Issue Lifecycle

- `Open` means that further action is still required.
- `Closed` means that no remaining action is owned by that issue.
- Use labels only for type, priority, and the small set of actionable workflow
  states configured in GitHub.
- Use assignees for ownership and milestones for a release or implementation
  batch.
- Use `Refs #<number>` while implementation or evidence remains incomplete.
- Use `Fixes #<number>` or `Closes #<number>` only when merging to the default
  branch fully satisfies the issue acceptance criteria.

Do not reproduce legacy status names such as `implemented`, `approved`, or
`resolved_with_followup` as labels. Record the completion reason and final
evidence in the closing comment and linked pull request.

## Issue Content

Keep the current problem, reproduction, acceptance criteria, explicit
non-goals, implementation ownership, and required verification in the issue
body. Put investigation updates, decisions, and cross-session handoffs in
comments. Exact candidate review and CI evidence belong on the pull request.

A handoff comment records the branch/worktree, exact commit range, file
ownership, completed verification, and remaining work. Private runtime memory
is not a handoff artifact.

## Legacy References

Migrated issues use the `legacy-migrated` label and include both the legacy ID
and an immutable archive link. Do not try to preserve the old number or
creation timestamp. Historical citations in `docs/` continue to point to the
archived source commit rather than being rewritten as new GitHub issue IDs.
