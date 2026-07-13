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
| `.claude/scripts/*.sh,*.py` | 28 project tool scripts (post-coder, post-translator, classify_review, scan_varargs_string, etc.) | OpenCode loads via `bash` — paths still work |
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

### Workflows → hosted runner only; otherwise use task fallback

OpenCode has no `Workflow({...})` tool. These `.js` files depend on host-injected
`args`, `agent()`, `parallel()`, `phase()`, and `log()` and are not standalone
Node.js programs. Do not execute them with plain `node`.

```bash
# ❌ CLAUDE.md (Claude Code)
# Workflow({scriptPath: ".claude/workflows/translation-fix-pipeline.js", args: {issues: [...]}})

# ✅ Without an explicit hosted workflow runner
# Load translation-pipeline, then dispatch its documented phases with task(...).
# Keep source.txt and zh TextDB files under one zh-translator writer.
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
# → follows the hosted runner when available, otherwise the documented task fallback
```

Pipeline phases: Analyze → Plan → Review Plan (gate) → Execute (translator owns translation assets, then coder edits code) → Review (3-way parallel) → Cross-validate → Report.

### Batch Pipeline → hosted runner or task fallback
For multiple issues, use a runtime-provided workflow runner only when one is
explicitly available. Otherwise reproduce the documented phases with `task(...)`;
do not invoke `.opencode/workflows/*.js` with plain Node.js.

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

## Worktree Placement Policy (ENFORCED)

**All git worktrees MUST be created inside `.worktrees/` at the repo root, using
a relative path:**

```bash
git worktree add .worktrees/<name> <branch>
```

Rules:
- Path MUST start with `.worktrees/` (repo-internal).
- MUST be relative — no absolute paths, no `~`, no `../` escaping the repo.
- `git config --global worktree.useRelativePaths true` is already set.

This is **hard-enforced** by the auto-loaded plugin
`.opencode/plugin/enforce-worktree-path.js`, which intercepts `bash` tool calls
and blocks any `git worktree add` whose target is not a compliant
`.worktrees/<name>` relative path. Non-compliant commands raise an error and do
not execute. Do not attempt to bypass it (e.g. `cd` elsewhere then add) — keep
worktrees inside the repo so cleanup, relative paths, and WSL access stay
consistent.

Legacy `.claude/worktrees/` is deprecated and now empty; do not create new
worktrees there.

## Codex Collaboration (when to hand off)

This repo is worked by two AI engines. See `docs/dual-agent-workflow.md` for the
full matrix. Quick guidance for OpenCode sessions:

**Keep in OpenCode** (our strengths): batch `T_()` / `%%%%` translation, routine
C++ `T_()` migration, Makefile fixes, multi-issue batch pipelines, script-verifiable
patterned work, anything parallelizable across subagents.

**Suggest handing to Codex** (deep single-thread reasoning): CJK render /
char-width / advance / font-fallback bugs, hidden crashes / UB / call-chain root
cause, large architectural refactor design. When a task clearly fits this
profile, tell the user "this is a good Codex task" rather than grinding on it
with flash-tier reasoning.

**Handoff is via disk, not memory.** Codex CANNOT read OpenCode's persistent
memory (`system/handoff.md`). To hand work to Codex, write the plan / branch /
commit range to `.claude/ORCHESTRATION_STATE.md` or `~/projects/issues/<N>/`.

**Branch ownership:** Codex uses `codex/<topic>`; OpenCode uses `<topic>` or
`consolidate-*`. Use the trailer for the engine that actually authored the
change; Codex must not claim OpenCode authorship.

## Commit Message Convention

Commits created by OpenCode or Claude Code MUST end with the matching trailer:

```
Co-Authored-By: opencode <noreply@opencode.ai>
```

or (if you are still committing via Claude Code):

```
Co-Authored-By: Claude <noreply@anthropic.com>
```

Pick whichever matches the tool that actually generated the change. Other
runtimes must follow their own repository policy and must not falsely use one
of these identities. The repo history is mixed; both listed forms are acceptable.

## Default init.txt Configuration

`crawl-ref/source/init.txt` (gitignored — user-local config) must contain:

```ini
language = zh
# Unified Maple Mono NF CN for all tile fonts
tile_font_crt_file = dat/tiles/MapleMono-NF-CN-Regular.ttf
tile_font_msg_file = dat/tiles/MapleMono-NF-CN-Regular.ttf
tile_font_stat_file = dat/tiles/MapleMono-NF-CN-Regular.ttf
tile_font_tip_file = dat/tiles/MapleMono-NF-CN-Regular.ttf
tile_font_lbl_file = dat/tiles/MapleMono-NF-CN-Regular.ttf
```

Fonts must be deployed to `dat/tiles/` (not `contrib/fonts/`).
This file must be copied alongside `crawl.exe` and data files on every deployment.

## Build Workflow: Multi Worktree + ccache

See `docs/build-workflow.md` for full documentation.

Console and tiles builds use **separate worktrees** to keep `.o` files isolated:

| Worktree | Target | Helper script |
|----------|--------|--------------|
| **Main** (`crawl/`) | WSL Console | `bash crawl-ref/source/util/build-console.sh` |
| `.worktrees/mingw-tiles` | Windows Tiles | `bash crawl-ref/source/util/build-tiles.sh` |
| `.worktrees/android-tiles` | Android APK | `bash crawl-ref/source/util/build-android.sh` |

When `ccache` is installed, the project Makefile automatically wraps `GCC` and
`GXX` with it; no `CC`/`CXX` or `PATH` override is required.

## Windows Tiles Deployment

```bash
# Use deploy.sh (recommended — syncs mingw-tiles worktree, builds, deploys)
bash .claude/scripts/deploy.sh [target_dir]

# Or manually (from mingw-tiles worktree):
cd .worktrees/mingw-tiles/crawl-ref/source
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8
TARGET=/mnt/d/crawl-release
cp -f crawl.exe "$TARGET/"
cp -r dat/* "$TARGET/dat/"
cp -f contrib/fonts/*.ttf "$TARGET/dat/tiles/"
cp -f init.txt "$TARGET/"
```

## Android Deployment

```bash
# Use deploy-android.sh (recommended — syncs android-tiles worktree, builds, deploys)
bash .claude/scripts/deploy-android.sh [target_dir] [--release]

# Or manually (from android-tiles worktree):
cd .worktrees/android-tiles/crawl-ref/source
make ANDROID=$(date +%Y%m%d) TILES=y android -j8
cd android-project
ANDROID_SDK_ROOT=$HOME/Android gradle :app:assembleBuildTest
# APK at: app/build/outputs/apk/buildTest/app-buildTest-unsigned.apk
```

Android build requires Android SDK + NDK (see `crawl-ref/docs/develop/android.txt`).
Default variant is `buildTest` (arm64-v8a only); use `--release` for all ABIs.

Key files to always deploy:
| File | Purpose |
|------|---------|
| `crawl.exe` | Cross-compiled Windows tiles binary |
| `dat/` | Full data directory (descriptions, tiles, database, etc.) |
| `dat/tiles/*.ttf` | Font files (Maple Mono for CJK, DejaVu Sans as fallback) |
| `init.txt` | Language + font configuration |

## Critical C++ Anti-Pattern: std::string in variadic `%s` (Issue #42 UB)

**NEVER pass a `std::string` (or a `std::string`-producing expression) as a
`%s` argument to a printf-style variadic function** (`make_stringf`, `mprf`,
`mprf_p`, `die`, `cprintf`, ...). These are C variadic functions:
`va_arg(ap, const char*)` reads the first 8 bytes of the `std::string` object
(its SSO buffer / data pointer) as a `char*` → **runtime garbage / control
characters**. `-Wformat` does NOT reliably catch this for class temporaries.

Watch especially for:
- Ternaries: `cond ? string(a) + " " : ""` promotes **BOTH** branches to
  `std::string` (the bug that produced the garbled "请仅输入%s%s。" prompt).
- Runtime concatenation: `make_stringf("%s", a + b)`.
- Function calls returning `std::string`: `make_stringf("%s", foo())` where
  `foo()` returns `std::string`.

**Fix:** build a `std::string` local first, then pass `.c_str()`; `T_()`
already returns `const char*` so it needs no wrapping.

**Enforced gate:** `.claude/scripts/scan_varargs_string.py` (tree-sitter AST)
is wired into `post-coder.sh` (and `verify_zh.sh --profile code`) as **blocking**. Run it after any C++ edit
touching these calls:

```bash
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/          # HIGH only (blocking)
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/ --include-warn  # + advisory
```

HIGH rules (`STRING_CTOR` / `CONCAT` / `TERNARY`) block; `CALL_NO_CSTR` is a
WARN — verify the callee returns `const char*` (safe) vs `std::string` (needs
`.c_str()`). Full write-up: `CLAUDE.md` "Variadic-String UB Scanner" +
`.claude/scripts/TOOLCHAIN.md`.

## Simplified Verification: `verify_zh.sh --profile`

**Agents should NOT run a dozen individual scripts.** A single command replaces
the three post-* scripts:

| Change type | Command |
|------------|---------|
| Translation / data files | `bash .claude/scripts/verify_zh.sh --profile translation` |
| C++ / i18n code | `bash .claude/scripts/verify_zh.sh --profile code` |
| Pre-merge review | `bash .claude/scripts/verify_zh.sh --profile review` |
| CI gate | `bash .claude/scripts/verify_zh.sh --profile ci` |

**Agent post-task template:**
```
翻译 source.txt：
1. 修改
2. bash .claude/scripts/verify_zh.sh --profile translation
3. 若失败，只修复报告中列出的条目
4. 报告命令、退出码、失败项数
```

```
C++ i18n 改动：
1. 修改
2. bash .claude/scripts/verify_zh.sh --profile code
3. 必要时编译目标
4. 报告命令、退出码、失败项数
```

**Hard rule for translator agents:**
```
将 \n、\t、\r、%%%%、%N$s、<tag>、@keyword@ 视为不可翻译 token。
输出前必须逐字保留；不得为了中文自然性删除它们。
```

The report (written to `.claude/metrics/verify/`) aggregates results from
`core-static` checks (always blocking) plus domain-specific checks per profile.
All three `post-*.sh` scripts remain available as backward-compatible aliases.

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
