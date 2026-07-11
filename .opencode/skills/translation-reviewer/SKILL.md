---
name: translation-reviewer
description: 5-layer systematic review of DCSS Chinese translation commits. Protocol/display separation, completeness, consistency, content quality, database integrity.
---

Review the specified Chinese translation changes using the 15-point framework defined in `.opencode/agents/translation-reviewer.md`.

Start with automated checks:
1. Run `bash .claude/scripts/verify_zh.sh --profile review` and report the raw log path
2. Do NOT summarize, filter, or interpret script output — the orchestrator reads raw logs directly

Then manually verify each finding against actual source code. Classify as:
- P0 (functional/visibility impact) — must block commit
- P1 (quality impact) — flag but do not block

Report with issue references, file:line, root cause, and fix suggestions.
Final verdict: Go / Conditional Go / No-Go.
