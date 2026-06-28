---
name: zh-code-reviewer
description: 5-layer systematic code review of DCSS Chinese translation changes. Checks protocol/display separation, T_() migration issues, consistency, and database integrity. Distinct from translation text quality review.
argument-hint: [commit-ish or leave empty for current diff]
---

Review the specified Chinese translation code changes using the 15-point framework defined in `.claude/agents/zh-code-reviewer.md`.

Start with automated checks:
1. `check_consistency.sh --all`
2. `scan_untranslated.sh --layer1 --summary`
3. `scan_untranslated.sh --layer3 --summary`

Then manually verify each finding against actual source code. Classify as P0 (functional/visibility) or P1 (quality). Report with issue references, file:line, root cause, and fix suggestions.
