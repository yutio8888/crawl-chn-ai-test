# Translation Issue Tracking

Translation issues are tracked in an independent repository. From the crawl
repository root, its location is `${DCSS_ISSUES_DIR:-../issues}`; set
`DCSS_ISSUES_DIR` when the repositories are not siblings. Its `INDEX.md` is the
authority for issue status.

## Per-Issue Files

Use only the files needed for the issue:

| File | Purpose |
|---|---|
| `README.md` | Problem, reproduction, and current status |
| `analysis.md` | Root cause and evidence |
| `check.md` | Search/extraction results |
| `translate.md` | Translation plan or wording decisions |
| `review.md` | Plan/content review |
| `review_commit.md` | Exact candidate review |
| `*-plan*.md` | Execution plans |
| `*-adjustment*.md` | Plan revisions |

Do not create a second project-status document inside the crawl repository.
Before adding tracking material, check whether the issue `README.md` or the
external `INDEX.md` already owns it.

## Handoff

Cross-runtime handoffs record the issue number, branch/worktree, exact commit
range, file ownership, remaining work, and required verification. Private
runtime memory is not a handoff artifact.

## Commits

If a task modifies the independent issue repository, commit those changes in
that repository before ending the task, using its current commit convention.
If no issue file changed, do not create an empty issue-tracking commit.
