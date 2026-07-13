---
name: zh-code-reviewer
description: 5-layer systematic code review of DCSS Chinese translation changes. Checks protocol/display separation, T_() migration issues, consistency, and database integrity. Distinct from translation text quality review.
---

Review the specified Chinese translation code changes using the 5-layer framework defined in `.opencode/agents/zh-code-reviewer.md`.

Start with automated checks:
1. Run `bash .claude/scripts/context_resolve.sh "<review scope>" --task-type review --files <target-files>`
2. Use the returned current glossary context and retain its SHA-256
3. Run `bash .claude/scripts/verify_zh.sh --profile review` and report the raw log path
4. Do NOT summarize, filter, or interpret script output — the orchestrator reads raw logs directly

Then manually verify each finding against actual source code. Classify as:
- 🔴 Blocker (functional impact or mechanical error)
- 🟡 Needs fix (content inaccuracy or language error)
- 🟢 Suggestion (style preference)

Every finding must include: exact line reference, EN original, current ZH text, problem description, and suggested fix.
Include the glossary SHA-256 in the final report.

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
