---
name: translation-reviewer
description: 5-layer systematic review of DCSS Chinese translation commits. Protocol/display separation, completeness, consistency, content quality, database integrity.
argument-hint: [commit-ish or leave empty for current diff]
---

Review the specified Chinese translation changes using the 15-point framework defined in `.claude/agents/translation-reviewer.md`.

Start with automated checks:
1. `check_consistency.sh --all`
2. `scan_untranslated.sh --layer1 --summary`
3. `scan_untranslated.sh --layer3 --summary`

Then manually verify each finding against actual source code. Classify as P0 (functional/visibility) or P1 (quality). Report with issue references, file:line, root cause, and fix suggestions.
