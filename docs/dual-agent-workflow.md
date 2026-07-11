# Dual-Agent Workflow — Codex × OpenCode

Authoritative division of labor for this repo. Both tools read this file:
OpenCode via `instructions`/AGENTS.md pointer, Codex via CODEX.md pointer.

> One-line model: **OpenCode is the high-throughput pipeline; Codex is the
> deep-reasoning consultant.** Not primary/secondary — a two-speed engine.

## 1. Engine Profiles

| | OpenCode | Codex |
|---|---|---|
| Models | deepseek flash / pro | gpt-5.5 + `reasoning_effort` |
| Concurrency | many subagents in parallel | single-thread deep reasoning |
| Strengths | volume, patterned work, script-verifiable, orchestratable | cross-file global reasoning, hard root-cause, architecture tradeoffs |
| Unique | `task` parallelism, `workflow` scripts, plugin hard-guards, persistent memory | high reasoning budget, adversarial review |
| Role | pipeline workshop | staff engineer / consultant |

## 2. Task Routing Matrix

| Task | Owner | Rationale |
|---|---|---|
| Batch `T_()` entries, `%%%%` description-body translation | OpenCode `zh-translator` (flash) | high volume, cheap, parallelizable |
| Routine C++ `T_()` migration, Makefile fixes | OpenCode `crawl-coder` | patterned, script-verifiable |
| CJK render / char-width / advance / font-fallback bugs | **Codex** | needs cross-file reasoning over font metrics |
| Hidden crashes / UB / call-chain root cause | **Codex** | global reasoning |
| Large architectural refactor | Codex **designs** → OpenCode **executes** | complementary |
| Merge-gate final review | Codex (adversarial) + OpenCode `zh-code-reviewer` | two independent passes |
| Multi-issue batch | OpenCode `batch-pipeline` | shared worktree, sequential source.txt |

Fallback: simple git ops / quick questions / planning → whichever tool the user
is already in, handled inline.

## 3. Collaboration Glue (this is what makes it work)

1. **Branch naming = ownership.**
   - Codex-authored: `codex/<topic>`
   - OpenCode-authored: `<topic>` or `consolidate-*`
   - Makes merge provenance obvious and keeps the two engines from stepping on
     each other's branches.

2. **Cross-tool state lives on disk, not in memory.**
   OpenCode's persistent memory (`system/handoff.md`) is **invisible to Codex**.
   Any handoff between the two tools MUST be written to a shared on-disk file:
   - `.claude/ORCHESTRATION_STATE.md` — active plan / who-owns-what
   - `~/projects/issues/<N>/` — issue tracking (independent git repo)
   Rule of thumb: if Codex needs to know it, it does NOT go in OpenCode memory.

3. **Worktrees: always `.worktrees/<name>` (relative).**
   - OpenCode: hard-enforced by `.opencode/plugin/enforce-worktree-path.js`.
   - Codex: NOT covered by that plugin — enforced only by convention in
     `CODEX.md`. Codex must self-discipline here.

4. **Commit attribution:** both tools use
   `Co-Authored-By: opencode <noreply@opencode.ai>` (see CODEX.md / AGENTS.md).

## 4. Ideal Day Loop

```
issue (~/projects/issues/)
   │
   ├─[simple / high-volume]→ OpenCode full flow
   │     explore → translation-pipeline → zh-code-reviewer
   │     → consolidate-* worktree → merge
   │
   └─[hard / architectural]→ Codex deep reasoning designs plan
         (writes plan to .claude/ORCHESTRATION_STATE.md)
            │
            ├→ OpenCode executes plan in parallel (.worktrees/)
            │
            ├→ Codex adversarial review ─────────┐
            │                                     ├→ dual sign-off → merge
            └→ OpenCode zh-code-reviewer ─────────┘
```

## 5. Handoff Protocol (Codex ⇄ OpenCode)

**Codex → OpenCode** (design handed to execution):
1. Codex writes plan + file list + risks to `.claude/ORCHESTRATION_STATE.md`.
2. Codex creates/points to `codex/<topic>` branch or a `.worktrees/<name>`.
3. OpenCode reads the state file, executes in `.worktrees/`, runs post-coder /
   audit scripts, commits.

**OpenCode → Codex** (execution handed to review):
1. OpenCode records worktree branch + commit range in the state file.
2. Codex runs `.claude/scripts/classify_review.sh <target>..<branch>` then an
   adversarial read.
3. Merge only after both a Codex pass and an OpenCode `zh-code-reviewer` pass.

## 6. Anti-Patterns

- Using Codex for bulk patterned translation (waste of reasoning budget).
- Using OpenCode flash for subtle font-metric / call-chain root cause (misses it).
- Relying on OpenCode memory to hand off to Codex (Codex can't see it).
- Creating worktrees outside `.worktrees/` from Codex (breaks the shared layout).
- Both tools editing `source.txt` on different branches concurrently (merge hell —
  serialize through one worktree).
