# review-contract-v6

Domain review produces human-readable findings for the requested scope.
`classify_reviewers.py` selects relevant domains, not additional permission,
mandatory subagents, or a requirement to run every i18n check.

## Finding model

- **Blocker**: a demonstrated functional failure, undefined behaviour, protocol
  or lookup corruption, structural data damage, compilation failure, or unmet
  confirmed acceptance criterion introduced by the reviewed change.
- **Needs Fix**: a definite semantic, terminology, accuracy, completeness, or
  language error without runtime corruption.
- **Suggestion**: a non-required style preference; it never blocks acceptance.
- **Validation Gap**: required evidence or assigned coverage could not be
  obtained. State what is missing and why; do not present it as a proven defect.

## Conclusion

- **Ready**: no Blocker or Needs Fix, assigned review complete, and evidence
  required for this review's endpoint is available.
- **Changes Requested**: a Blocker or Needs Fix exists, or required review or
  validation remains incomplete. Distinguish defects from Validation Gaps.

An ordinary audit is delivered when findings and coverage gaps are reported;
it need not claim merge readiness. Report confirmed findings even if another
part is blocked. Plan non-goals do not excuse defects introduced by the diff.
Resolve findings within scope, preferring existing mechanisms and narrow fixes.

## Reviewer ownership

- `zh-code-reviewer` owns runtime safety, protocol/display separation,
  extraction and key coverage, formats, TextDB structure, translation lifetime,
  variadic calls, movement routing, English morphology, compilation, scanner
  triage, and relevant tooling/governance changes.
- `translation-reviewer` owns EN/ZH semantic parity, contextual glossary use,
  facts and numbers, completeness, naturalness, terminology, and character voice.

For mixed changes, each reviewer inspects its domain and the shared boundary
where they meet. `docs/*-review-results.md` ledgers classify as mixed. A role's
checklist applies only to affected behavior; governance review does not require
gameplay tracing or terminology lookup. Reuse the implementer's relevant logs.
Reviewers do not rerun whole-project verification suites; targeted checks are
appropriate to resolve a concrete uncertainty. Reviewers remain read-only and
return fixes to the assigned writer.

## Output and stages

- Ordinary review accepts named files, existing content, staged changes, or a
  worktree diff. State the boundary and any concurrent changes observed; neither
  a commit nor a clean worktree is a prerequisite.
- Merge review binds a clean committed candidate and its complete diff against
  the target. Route with `classify_reviewers.py --base <target> --head <candidate>`;
  ordinary review can use `--files`. Apply domains inline if delegation is
  unavailable or unnecessary; do not claim independent review in that case.
- Report role/scope, classified findings, file/line evidence, impact, suggested
  fixes, validation gaps, and the conclusion. Cite EN/ZH text when useful.
  Return the report locally unless remote posting is authorized. No JSON,
  signature, evidence bundle, or new status artifact is required.
- Development uses one matching profile and focused checks as described in
  `docs/zh-testing.md`. A committed-candidate run includes `--base` and `--head`;
  unbound changed scope covers only uncommitted changes. Reuse evidence when
  tested content and dependencies are unchanged.
- Merge requires applicable GitHub Actions CI and completed domain review.
  Existing user authorization governs committing, posting, and merging. A task
  branch alone does not trigger CI: use the existing PR/manual workflow when
  merge is requested. No separate final evidence gate or local merge protocol
  is required.
