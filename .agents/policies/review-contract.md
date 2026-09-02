# review-contract-v6

Domain review is a human-readable review phase routed by
`classify_reviewers.py`, with merge gated by the matching development profile
and existing GitHub Actions CI. There is no immutable bundle, readiness
object, digest-bound approval, lock, attempt/retry state, local merge
authorization, or `.git/zh-review-evidence` directory.

## Finding model

- **Blocker**: runtime/functional failure, undefined behaviour, protocol or
  lookup corruption, structural data damage, compilation failure, failure to
  review the complete diff, an unmet confirmed acceptance criterion within
  that diff, or an interrupted required verification.
- **Needs Fix**: a definite semantic, terminology, accuracy, completeness, or
  language error without runtime corruption.
- **Suggestion**: a non-required style preference.

## Conclusion

- **Ready**: `blocker == 0` and `needs_fix == 0`.
- **Changes Requested**: a Blocker or Needs Fix exists, or the reviewer could
  not complete the assigned scope.

Suggestions do not block. There is no Conditional Go. Plan non-goals do not
excuse defects introduced by the diff under review. When proposing a
resolution, prefer deleting unnecessary design, reusing repository
mechanisms, and narrowing the commitment, in that order.

## Reviewer ownership

- `zh-code-reviewer` owns runtime safety, protocol/display separation,
  extraction and key coverage, format arguments, TextDB structure, borrowed
  translation lifetime, variadic calls, movement phrase routing, English
  morphology, compilation, and scanner warning triage.
- `translation-reviewer` owns EN/ZH semantic parity, current-glossary choices
  in context, facts and numbers, completeness, natural Chinese, terminology
  consistency, and character voice. It reports implementation defects it
  encounters but does not duplicate the code reviewer's primary scope.

For mixed changes, each reviewer stays within that ownership and inspects the
shared context/fallback boundary only where the two domains meet. Neither
reviewer reruns whole-project verification suites during readiness.
`docs/*-review-results.md` ledgers classify as mixed and require both
reviewers.

## Reviewer output

Reviewers record their findings as plain human-readable text in the PR or
issue. No structured JSON, digest, signature, or evidence directory is
required. Each record includes at least:

- the reviewer role;
- findings classified as Blocker / Needs Fix / Suggestion;
- for each finding, the file, line, evidence, impact, and a concrete
  suggested fix when applicable;
- a final conclusion of Ready or Changes Requested.

Translation-reviewer findings cite the English source and the current Chinese
text when useful.

## Orchestration

- Review starts only after the candidate changes are committed and the
  worktree is clean.
- The reviewer set comes from
  `classify_reviewers.py --base <target> --head <candidate>` (or an explicit
  `--files` list); never hard-code a fixed reviewer count.
- Development verification uses exactly one matching profile
  (`translation`, `code`, or `ci`); do not serially run all three profiles
  against the same candidate.
- Existing GitHub Actions CI must pass before merge.
- There is no immutable bundle ID and no digest-bound readiness.
