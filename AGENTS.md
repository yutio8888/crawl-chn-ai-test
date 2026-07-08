# AGENTS.md — OpenCode-Specific Instructions

> **OpenCode overlay for the DCSS Chinese translation project.**
> For shared project knowledge (build, branches, translation system, CJK tiles,
> testing pipeline, issue tracking, agent commit discipline), see `CLAUDE.md`.
> OpenCode loads `AGENTS.md` first; if absent, it falls back to `CLAUDE.md`.

## OpenCode Runtime Layout

This repo carries two parallel config trees from a Claude Code → OpenCode migration:

| Tree | Purpose | Loaded by OpenCode? |
|------|---------|---------------------|
| `.opencode/` | **OpenCode-native** agents/skills/workflows/config | ✅ Yes |
| `.claude/`  | Legacy Claude Code infrastructure | ⚠️ Partial |

### What lives in each (current state)

| Path | Role | Notes |
|------|------|-------|
| `.opencode/agents/*.md` | 5 subagents: `crawl-coder`, `ocr`, `translation-reviewer`, `zh-code-reviewer`, `zh-translator` | OpenCode syntax (`mode: subagent`, `model: deepseek/...`, `permission:`) |
| `.opencode/skills/<name>/SKILL.md` | 4 skills (one file per skill in its own directory) | OpenCode loads `<name>/SKILL.md` |
| `.opencode/workflows/*.js` | 2 workflow scripts | Run via `bash` — OpenCode has no `Workflow` tool |
| `.opencode/opencode.json` | Project-level config | Set `explore.model = deepseek/deepseek-v4-flash` |
| `.claude/scripts/*.sh,*.py` | 27 project tool scripts (post-coder, post-translator, classify_review, etc.) | OpenCode loads via `bash` — paths still work |
| `.claude/workflows/*.js` | Duplicate of `.opencode/workflows/` | Safe to keep as redundancy; can be deleted if not returning to Claude Code |
| `.claude/agents/`, `.claude/skills/` | Claude Code-format legacy files (use `model: inherit`, `tools: Read, Write,...`) | **Not loaded by OpenCode** (syntax/structure incompatible) — safe to delete |
| `.claude/ORCHESTRATION_STATE.md`, `.claude/analysis/`, `.claude/metrics/`, `.claude/worktrees/` | Project state, analysis, metrics, worktree bookkeeping | OpenCode reads as files (no special loading) |

### Agent model assignments (current)

| Agent | Model | Source |
|-------|-------|--------|
| `crawl-coder` | `deepseek/deepseek-v4-flash` | `.opencode/agents/crawl-coder.md` |
| `translation-reviewer` | `deepseek/deepseek-v4-flash` | `.opencode/agents/translation-reviewer.md` |
| `zh-translator` | `deepseek/deepseek-v4-flash` | `.opencode/agents/zh-translator.md` |
| `zh-code-reviewer` | `deepseek/deepseek-v4-pro` | `.opencode/agents/zh-code-reviewer.md` (intentionally v4-pro, not v4-flash) |
| `ocr` | `openrouter/qwen/qwen3-vl-8b-instruct` | `.opencode/agents/ocr.md` |
| `explore` (built-in) | `deepseek/deepseek-v4-flash` | `.opencode/opencode.json` |

## OpenCode Tool Surface (the syntax differences)

`CLAUDE.md` was written for Claude Code and uses Claude Code dispatch syntax.
**Replace those syntaxes when invoking tools in OpenCode:**

### Subagents → use `task`, not `Agent`

```python
# ❌ CLAUDE.md (Claude Code) — does NOT work in OpenCode
# Agent(subagent_type="zh-translator", description="...", prompt="...")

# ✅ OpenCode
task(
  subagent_type="zh-translator",  # or "crawl-coder" | "translation-reviewer" | "zh-code-reviewer" | "ocr" | "explore" | "general"
  description="Translate <target>",
  prompt="<full task>\n\n## Terminology Context\n${CONTEXT}"
)
```

Available built-in subagent types in OpenCode: `general`, `explore` (lowercase!),
`scout`. Project-defined subagents: `crawl-coder`, `ocr`, `translation-reviewer`,
`zh-code-reviewer`, `zh-translator`.

### Skills → use `skill(name=...)`, not `Skill("...")`

```python
# ❌ CLAUDE.md (Claude Code)
# Skill("translation-pipeline")

# ✅ OpenCode
skill(name="translation-pipeline")  # loads .opencode/skills/translation-pipeline/SKILL.md
```

Available skills: `crawl-coder`, `translation-pipeline`, `translation-reviewer`,
`zh-code-reviewer`.

### Workflows → no `Workflow` tool exists; invoke via `bash`

OpenCode has no `Workflow({...})` tool. Workflows are `.js` scripts that must be
executed through `bash`:

```bash
# ❌ CLAUDE.md (Claude Code)
# Workflow({scriptPath: ".claude/workflows/translation-fix-pipeline.js", args: {issues: [...]}})

# ✅ OpenCode
node .opencode/workflows/translation-fix-pipeline.js '<json args>'
# or for batch:
node .opencode/workflows/translation-batch-pipeline.js '<json args>'
```

The scripts are identical in both `.opencode/workflows/` and `.claude/workflows/`.

### Built-in `explore` agent (read-only code search)

`explore` is a **built-in OpenCode subagent**, not a project file. No
`.opencode/agents/explore.md` exists. Configuration goes in `opencode.json`:

```json
{ "agent": { "explore": { "model": "deepseek/deepseek-v4-flash" } } }
```

To invoke:
```python
task(subagent_type="explore", description="Find <target>",
     prompt="<search task>")
```

`explore` cannot edit files (read-only by design). For write-capable multi-step
work, use `general` instead.

## Agent Auto-Routing (OpenCode syntax)

When the user's request matches a scenario, **delegate to the specified agent**
via the `task` tool. Do NOT handle these tasks inline.

### Translation → `zh-translator`
| Trigger | Example |
|---------|---------|
| Translate text / files | "翻译这个文件", "translate these god descriptions" |
| Add T_() entries | "把这些字符串加到 source.txt" |
| Convert hardcoded ZH to T_() | "把这个文件的硬编码中文改成 T_() 形式" |
| Batch i18n operations | "批量翻译这批 %%%%% 条目" |

```python
CONTEXT=$(bash .claude/scripts/context_resolve.sh "<task>" --files <target-files> 2>/dev/null)
task(subagent_type="zh-translator", description="Translate <target>",
     prompt="<full translation task>\n\n## Terminology Context\n${CONTEXT}")
```

### Code Implementation → `crawl-coder`
| Trigger | Example |
|---------|---------|
| C++ source modification | "修一下这个 bug", "把这个函数迁移到 T_()" |
| T_() migration (code side) | "把这个文件迁移到 T_()" |
| TextDB / .txt data files | "更新 zh/source.txt", "fix %%%% separators" |
| Compilation / build fixes | "编译报错了帮我修", "fix the build" |

```python
task(subagent_type="crawl-coder", description="Implement <change>",
     prompt="<full implementation task with file paths and requirements>")
```

### Code Review → `zh-code-reviewer`
| Trigger | Example |
|---------|---------|
| Code review | "帮我 review 这个 commit", "审查代码改动" |
| T_() migration review | "检查 T_() 迁移是否正确" |
| Protocol/display audit | "检查有没有 protocol 泄露" |
| Database integrity | "检查 TextDB 完整性", "verify %%%% parity" |
| Translation bug investigation | "这个翻译 bug 根因是什么" |

```python
task(subagent_type="zh-code-reviewer", description="Review <scope>",
     prompt="<review scope: commit hash, file list, or diff>")
```

### Translation Quality Review → `translation-reviewer`
| Trigger | Example |
|---------|---------|
| Translation quality | "审查翻译质量", "review translation content" |
| Terminology consistency | "检查神名一致性" |
| Content accuracy | "对比中英文内容是否一致" |
| Character voice | "角色语气对不对" |

```python
task(subagent_type="translation-reviewer", description="Review <scope>",
     prompt="<review scope: commit hash, file list, or diff>")
```

### Full Pipeline → `translation-pipeline` skill
| Trigger | Example |
|---------|---------|
| "有个翻译问题" | "神名翻译不一致，帮我看看" |
| "translation bug" | "There's a bug in the Chinese UI text" |
| "这里没翻译" | "XX还是显示英文" |
| New issue from scratch | "帮我处理 Issue #N" |

```python
skill(name="translation-pipeline")
# → internally invokes .opencode/workflows/translation-fix-pipeline.js via node/bash
```

Pipeline phases: Analyze → Plan → Review Plan (gate) → Execute (code+translate parallel) → Review (3-way parallel) → Cross-validate → Report.

### Batch Pipeline → run workflow script directly
For multiple issues at once, run the batch pipeline script via `bash`:

```bash
node .opencode/workflows/translation-batch-pipeline.js \
  '{"issues": [{"description": "..."}, ...]}'
```

Key differences from single-issue pipeline: shared worktree, phase-batched processing, parallel analysis with merged root causes and unified glossary, sequential execution to avoid source.txt merge conflicts.

### Code Exploration → `explore` (built-in)
| Trigger | Example |
|---------|---------|
| Search / find in codebase | "查找所有未翻译的 mprf", "where is spell_title defined" |

```python
task(subagent_type="explore", description="Find <target>", prompt="<search task>")
```

### Fallback
- Simple git ops, quick questions, planning → handle inline.
- Multi-step complex tasks spanning categories → break into steps, dispatch each.

## Commit Message Convention

All commits MUST end with one of:

```
Co-Authored-By: opencode <noreply@opencode.ai>
```

or (if you are still committing via Claude Code):

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

Pick whichever matches the tool that actually generated the change. The repo
history is mixed; both forms are acceptable.

## Pointer to CLAUDE.md (for shared knowledge)

The following topics are documented in `CLAUDE.md` and **not duplicated here**
(OpenCode loads CLAUDE.md as a fallback only if AGENTS.md is absent, so explicit
pointer matters for the in-context awareness):

- **Worktree branch discipline** — see `CLAUDE.md` "Worktree Branch Discipline"
- **Risk-tiered code review** — see `CLAUDE.md` "Code Review Strategy" + the
  `review_at_merge.sh` / `classify_review.sh` scripts
- **Build commands** (WSL console, Windows tiles cross-compile, deploy) — see
  `CLAUDE.md` "Build Requirements & Commands"
- **CJK tiles architecture** (3 layers) — see `CLAUDE.md` "CJK Tiles Support
  Architecture"
- **Translation system architecture** (Type I-V translation patterns) — see
  `CLAUDE.md` "Translation System Architecture"
- **Current branch status** — see `CLAUDE.md` "Current Branch Status"
- **Testing** (manual + 3-layer pipeline + M5 aggregator) — see `CLAUDE.md`
  "Testing"
- **Verification checklist per commit** — see `CLAUDE.md` "Verification Checklist"
- **Translation toolchain** (pre-commit CI scripts) — see `CLAUDE.md`
  "Translation Toolchain"
- **Agent commit discipline** (cherry-pick, concurrency limits) — see
  `CLAUDE.md` "Agent Commit Discipline"
- **Multi-agent parallel development pattern** — see `CLAUDE.md` "Multi-Agent
  Parallel Development Pattern"
- **Issue tracking** (`~/projects/issues/INDEX.md`, file naming, auto-commit) —
  see `CLAUDE.md` "Issue Tracking"

Read `CLAUDE.md` on first invocation of this project, or when you encounter a
topic from the list above and need the canonical reference.
