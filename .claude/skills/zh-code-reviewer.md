---
name: zh-code-reviewer
description: 5-layer systematic code review of DCSS Chinese translation changes. Checks protocol/display separation, T_() migration issues, consistency, and database integrity. Distinct from translation text quality review.
argument-hint: [commit-ish or leave empty for current diff]
---

Review the specified Chinese translation code changes using the 5-layer framework defined in `.opencode/agents/zh-code-reviewer.md`.

Start with automated checks:
1. Run `bash .claude/scripts/post-reviewer.sh` and report the raw log path
2. Do NOT summarize, filter, or interpret script output — the orchestrator reads raw logs directly

Then manually verify each finding against actual source code. Classify as:
- 🔴 Blocker (functional impact or mechanical error)
- 🟡 Needs fix (content inaccuracy or language error)
- 🟢 Suggestion (style preference)

Every finding must include: exact line reference, EN original, current ZH text, problem description, and suggested fix.

Report format:
```
## Summary
| Layer | 🔴 | 🟡 | 🟢 |
|-------|----|----|-----|
| ... | N | N | N |
| **Total** | **N** | **N** | **N** |

## Findings
### 🔴/<emoji> <Issue>
- **Line**: N
- **Problem**: <description>
- **Fix**: <suggestion>

## Verdict: Go / Conditional Go / No-Go
```
