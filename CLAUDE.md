# CLAUDE.md — Dungeon Crawl Stone Soup Chinese Translation + CJK Tiles

This file guides ongoing Chinese (zh) translation work and CJK tiles rendering
support for DCSS.

| Branch | Role | Based on |
|--------|------|----------|
| `chn-0.34.1-base` | **Active dev branch** | `0.34.1` stable tag (clean rebuild) |
| `chinese-translation-0.34.1` | Legacy branch (retained for reference) | `0.34.1` stable tag → polluted by master merge |
| `worktree-cjk-tiles-fix` | CJK tiles original dev | `master` |

## ⚠️ Worktree Branch Discipline

Each worktree operates on its own isolated branch. **Do NOT push, merge, or
update-ref directly from a worktree to other branches.** Doing so causes
`git update-ref` to move the branch pointer without updating the main
repository's index and working tree, leading to false "staged changes".

**Correct procedure after committing in a worktree:**
1. `cd ~/projects/crawl` (the main repository)
2. `git checkout <target-branch>` (e.g. `chn-0.34.1-base`)
3. **Run merge review gate**: `bash .claude/scripts/review_at_merge.sh <worktree-branch> <target-branch>`
   - See "Worktree Merge Review" below — this classifies the cumulative diff
     and decides whether full review is required before merging.
4. `git merge --ff-only <worktree-branch>` (use an explicit non-FF merge only when intended)
5. Resolve any conflicts in the main repository
6. Verify `git status`; never use `reset --hard` as routine synchronization

This ensures the main repository's index and working tree stay in sync with the
branch reference, avoiding the stale-index problem caused by `update-ref`.
The review gate (step 3) catches high-risk C++/T_() changes before they reach
`chn-0.34.1-base`.


## Agent Auto-Routing

When the user's request matches a scenario below, **delegate to the specified
agent** using the Agent tool. Do NOT handle these tasks inline.

### Translation → `zh-translator` agent

| Trigger | Example |
|---------|---------|
| Translate text / files | "翻译这个文件", "translate these god descriptions" |
| Add T_() entries | "把这些字符串加到 source.txt", "add T_() for this" |
| Convert hardcoded ZH to T_() | "把这个文件的硬编码中文改成 T_() 形式" |
| Batch i18n operations | "批量翻译这批 %%%%% 条目" |

```
# Auto-inject terminology context before dispatch
CONTEXT=$(bash .claude/scripts/context_resolve.sh "<task>" --files <target-files> 2>/dev/null)
Agent(subagent_type="zh-translator", description="Translate <target>",
  prompt="<full translation task>\n\n## Terminology Context\n${CONTEXT}")
```

### Code Implementation → `crawl-coder` agent

| Trigger | Example |
|---------|---------|
| C++ source modification | "修一下这个 bug", "把这个函数迁移到 T_()" |
| T_() migration (code side) | "把这个文件迁移到 T_()", "add T_() guard to mprf calls" |
| TextDB / .txt data files | "更新 zh/source.txt", "fix %%%% separators" |
| Compilation / build fixes | "编译报错了帮我修", "fix the build" |

```
Agent(subagent_type="crawl-coder", description="Implement <change>",
  prompt="<full implementation task with file paths and requirements>")
```

### Code Review → `zh-code-reviewer` agent

Dedicated code review for translation-related source changes. Use this when the
user asks to review code, check correctness, or audit implementation quality.

| Trigger | Example |
|---------|---------|
| Code review | "帮我 review 这个 commit", "审查代码改动" |
| T_() migration review | "检查 T_() 迁移是否正确", "review the T_() changes" |
| Protocol/display audit | "检查有没有 protocol 泄露", "audit display vs protocol separation" |
| Database integrity | "检查 TextDB 完整性", "verify %%%% parity" |
| Translation bug investigation | "这个翻译 bug 根因是什么", "analyze this i18n issue" |

```
Agent(subagent_type="zh-code-reviewer", description="Review <scope>",
  prompt="<review scope: commit hash, file list, or diff>")
```

### Translation Quality Review → `translation-reviewer` agent

Content-level review of Chinese translation quality. Use this for language
quality, terminology consistency, and character voice checks.

| Trigger | Example |
|---------|---------|
| Translation quality | "审查翻译质量", "review translation content" |
| Terminology consistency | "检查神名一致性", "verify terminology across files" |
| Content accuracy | "对比中英文内容是否一致", "check EN/ZH parity" |
| Character voice | "角色语气对不对", "check character voice consistency" |

```
Agent(subagent_type="translation-reviewer", description="Review <scope>",
  prompt="<review scope: commit hash, file list, or diff>")
```

### Full Pipeline → `translation-pipeline` skill + workflow

For complex issues requiring the full analyze → plan → review → execute → verify
cycle, the `translation-pipeline` skill handles structured intake, then invokes
the `translation-fix-pipeline` workflow for deterministic multi-agent orchestration.

| Trigger | Example |
|---------|---------|
| "有个翻译问题" | "神名翻译不一致，帮我看看" |
| "translation bug" | "There's a bug in the Chinese UI text" |
| "这里没翻译" | "XX还是显示英文" |
| New issue from scratch | "帮我处理 Issue #N" |

```
# Skill handles intake → creates issue file → invokes Workflow
Skill("translation-pipeline")
# → Workflow({scriptPath: ".claude/workflows/translation-fix-pipeline.js", args: {...}})
```

Workflow phases: Analyze → Plan → Review Plan (gate) → Execute (translator owns translation assets, then coder edits code) → Review (3-way parallel) → Cross-validate → Report.

### Batch Pipeline → `translation-batch-pipeline` workflow

For multiple issues at once (e.g., a batch of playtester feedback), use the B′ batch
workflow: shared worktree + phase-batched processing. Analyzes all issues in parallel,
merges same-root-cause groups, builds a unified batch glossary, then executes
sequentially to avoid source.txt merge conflicts.

```
Workflow({scriptPath: ".claude/workflows/translation-batch-pipeline.js", args: {issues: [{description: "..."}, ...]}})
```

Key differences from single-issue pipeline:
- **Batch Analyze**: parallel analysis → merge same root causes → unified glossary
- **Execute Sequential**: serial code+translation in shared worktree (no merge conflicts)
- **Aggregate Report**: per-issue status + overall verdict

### Code Exploration → `Explore` agent

| Trigger | Example |
|---------|---------|
| Search / find in codebase | "查找所有未翻译的 mprf", "where is spell_title defined" |

```
Agent(subagent_type="Explore", description="Find <target>",
  prompt="<search task>")
```

### Fallback

Tasks that don't match any agent above (general discussion, planning, simple git
operations, quick questions) → handle inline. Multi-step complex tasks that span
categories → break into steps, dispatch each step to the right agent.


## Code Review Strategy: Risk-Tiered, Merge-Time Gated

**Review happens at worktree merge time, not at every commit.** Per-commit review
on every translation micro-edit is too costly; instead, classify the cumulative
worktree diff and apply the right level of scrutiny before merging into
`chn-0.34.1-base`.

### Risk Classification

Use `classify_review.sh` to categorize a diff:

| Level | Trigger | Treatment |
|-------|---------|-----------|
| 🟢 **GREEN** | Low-risk files outside source and workflow policy | No review — just merge |
| 🟡 **YELLOW** | Only `crawl-ref/source/dat/{i18n,descript,database}/zh/*.txt` | Run `verify_zh.sh --profile translation`; merge if clean |
| 🔴 **RED** | Source code/other source files, workflow policy, verification or build/deploy scripts, core workflow docs | Full reviewer pass plus a head-bound recorded verdict |

```bash
# Classify staged diff (per-commit quick check, advisory)
bash .claude/scripts/classify_review.sh

# Classify a worktree→target range (use at merge time)
bash .claude/scripts/classify_review.sh <target>..<worktree>

# JSON output for tooling
bash .claude/scripts/classify_review.sh <range> --json
```

### Worktree Merge Review (the actual gate)

**Run this in the MAIN repo before merging a worktree branch:**

```bash
cd ~/projects/crawl
git checkout chn-0.34.1-base
bash .claude/scripts/review_at_merge.sh <worktree-branch> chn-0.34.1-base
```

The script:
1. Computes the cumulative diff range `<target>..<worktree-branch>`
2. Classifies via `classify_review.sh`
3. **GREEN** → prints merge command, exit 0
4. **YELLOW** → runs `verify_zh.sh --profile translation`, exit 0/1
5. **RED** → exits 2 until a reviewer returns Go/Conditional Go. Record that
   result with `--record-verdict go|conditional-go`; the record is bound to the
   target head, worktree head, and binary diff hash. Any later change invalidates it.

### Per-Commit Review (Optional, Advisory)

During worktree development, you can still run `classify_review.sh` on staged
changes to get an early warning. **This is advisory only — the actual gate is
at merge time.** No need to dispatch the full `zh-code-reviewer` agent for
every micro-commit; defer that work to the merge point.

If a single commit is large enough to warrant full review on its own (e.g., a
risky T_() migration, a refactor of an enemy attack table), you may invoke
`zh-code-reviewer` directly on `git diff --cached` — but treat this as an
exception, not the default.

### Review Metrics Logging

After each code review (RED path: post-merge verdict, or per-commit exception),
record the results to establish a quality baseline for future optimization
validation:

```bash
bash .claude/scripts/record_review.sh '{
  "date": "'"$(date -Iseconds)"'",
  "agent_type": "zh-code-reviewer",
  "task_summary": "Worktree merge review of <worktree-branch>",
  "findings": {"blocker": N, "needs_fix": N, "suggestion": N},
  "fix_iterations": N,
  "verdict": "Go|Conditional Go|No-Go",
  "trigger": "merge-time",
  "session_id": "<from ORCHESTRATION_STATE.md>"
}'
```

The review metrics log (`.claude/metrics/review-log.jsonl`) establishes a baseline
for quantitatively validating future optimization scripts (Phase B #1 term
validation, #5 anti-pattern detection). Target: ≥30 records before first trend analysis.

### Commit Message Convention

All commits MUST end with:
```
Co-Authored-By: Claude <noreply@anthropic.com>
```

## Build Requirements & Commands

**Important**: Use at most 8 parallel jobs. The WSL environment has limited
resources; unbounded `-j$(nproc)` may cause system instability.

**Full build docs**: `docs/build-workflow.md`

### Architecture: Dual Worktree + ccache

Console and tiles builds use separate worktrees to isolate `.o` files:

| Worktree | Build target | Command |
|----------|-------------|---------|
| **Main** (`crawl/`) | WSL Console | `bash crawl-ref/source/util/build-console.sh` |
| `.worktrees/mingw-tiles` | Windows Tiles | `bash crawl-ref/source/util/build-tiles.sh` |

When `ccache` is installed, the project Makefile automatically wraps `GCC` and
`GXX` with it and caches objects across builds with similar flags.

### WSL Console Build (main worktree)
```bash
cd crawl-ref/source
bash util/build-console.sh
# or manually:
echo 'language = zh' > init.txt
make -j8
# Output: crawl (in source dir)
```

### Windows Tiles Cross-Compile (mingw-tiles worktree)
The worktree is **detached** and must be synced to the main worktree's
current HEAD before building. The helper script does this automatically:

```bash
cd crawl-ref/source
bash util/build-tiles.sh
# or manually:
cd /home/yutio888/projects/crawl
MAIN_HEAD=$(git rev-parse HEAD)
cd .worktrees/mingw-tiles
test -z "$(git status --porcelain --untracked-files=all)" || {
  echo "refusing destructive sync: build worktree is dirty" >&2; exit 1;
}
git reset --hard "$MAIN_HEAD"
cd crawl-ref/source
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8
# Output: crawl.exe (in worktree's source dir)
```

This reset is permitted only in the dedicated detached build worktree after
the clean-tree check. `build-tiles.sh` and `deploy.sh` enforce the same guard.
Never use this reset pattern to synchronize the main development worktree.

### Deploy to Windows (after cross-compile)
```bash
# One-step: sync worktree + cross-compile + copy + clear DB cache
bash .claude/scripts/deploy.sh
# Or specify custom target:
bash .claude/scripts/deploy.sh /mnt/d/crawl-game
```
Note: the game must be closed before copying (file in use error otherwise).

The script automatically clears `saves/db/` to force BerkeleyDB cache
regeneration — this ensures text file changes (zh/*.txt) take effect
even when only the C++ binary was modified.

### Required Fonts
- `contrib/fonts/DejaVuSans.ttf` (~720KB) — proportional font
- `contrib/fonts/DejaVuSansMono.ttf` (~330KB) — primary monospace font (layout metrics)
- `contrib/fonts/SarasaMonoSC-Regular.ttf` (~25MB) — CJK fallback font (must obtain separately)
- `contrib/fonts/MapleMono-NF-CN-Regular.ttf` — unified CJK tile font (see init.txt)

### Prebuilt Contrib Libraries
Cross-compilation requires prebuilt MinGW libraries at:
`crawl-ref/source/contrib/install/x86_64-w64-mingw32/lib/`
(SDL2, SDL2-image, freetype, libpng, zlib, lua, sqlite, pcre)

Different compilers use different `$(ARCH)` paths, so console vs tiles contribs
are naturally isolated (e.g. `x86_64-linux-gnu/` vs `x86_64-w64-mingw32/`).

## CJK Tiles Support Architecture

### Problem
CJK characters are 2x the width of ASCII characters. The tiles engine's
`TextRegion` grid system treats every character as 1 cell wide, causing layout
breakage with Chinese text.

### Solution (3 layers)

**Layer 1 — Grid Cell Counting** (`tilereg-text.cc:addstr_aux()`):
- Uses `wcwidth()` to determine per-character cell width
- CJK chars (width=2) occupy 2 grid cells; the second cell holds `0x200B` (ZWS) marker
- `print_x` advances by actual display width, not character count

**Layer 2 — Rendering** (`fontwrapper-ft.cc:render_textblock()`):
- Skips `0x200B` continuation markers (no render, no advance)
- CJK chars get 2x background width (`m_max_advance.x * wcwidth(ch)`)

**Layer 3 — Font Fallback** (`fontwrapper-ft.cc/h`):
- DejaVu Sans Mono provides all layout metrics (m_max_advance, m_ascender, charsz)
- Sarasa Mono SC loaded as secondary face for CJK glyphs
- `get_glyph_info()` / `load_glyph()` try primary face first, fall back to CJK face
- CJK glyphs use Sarasa's native ascender values (no override — caused floating)
- Atlas cell width doubled to accommodate wider CJK glyphs

## Translation System Architecture

### Overview

All translation flows through `T_("English")` → `i18n_source_lookup()` → `source.txt`.
When no Chinese translation is found, `T_()` returns the English key unchanged —
no `Options.language` guard is needed at call sites. The codebase is language-neutral;
language selection happens entirely at the translation database level.

### Type I — C++ Literal `T_("string")` (primary pattern, ~93%)

```cpp
mprf(T_("You hit %s."), mon_name);    // ← literal key, statically auditable
```

`i18n_extract.py` scans all `.cc`/`.h`/`.lua` files for `T_("...")` and
cross-references with `source.txt`. This is the fully-verified path.

### Type II — Function Wrappers (internal `T_()`, ~5%)

Functions that internally call `T_()` on their return data. Callers are
translation-unaware — they just call `skill_name(sk)` and it's already Chinese.

| Wrapper | Internal T_() pattern | Source data |
|---------|----------------------|-------------|
| `skill_name()` | `T_(_skill_english_name(skill))` | `skills.cc` static array |
| `spell_title()` | `T_(_seekspell(spell)->title)` | `spl-data.h` spell table |
| `item_base_name()` | `T_(Weapon_prop[...].name)` | `item-prop.cc` prop tables |
| `brand_type_name()` | `T_(weapon_brands_verbose[brand])` | `item-name.cc` arrays |
| `jewellery_effect_name()` | `T_("see invisible")` etc. | `item-name.cc` switch |
| `special_armour_type_name()` | `T_("fire resistance")` etc. | `item-name.cc` switch |
| `feature_description_at()` | `T_(get_feature_def(grid).name)` | `feature-data.h` struct |
| `mons_type_name()` | `T_(get_monster_data(mc)->name)` | `dat/mons/*.yaml` |
| `ability_name()` | `T_(ability_names[...])` | `ability.cc` array |

### Type III — Runtime Variable `T_(variable)` (~1%, invisible to static scan)

Strings defined as data arrays and translated at runtime via `T_(variable)`.
`i18n_extract.py` **cannot** detect these — always audit with `audit_data_i18n.py`.

| Source | Definition | Runtime trigger | Count |
|--------|-----------|-----------------|-------|
| Duration expiry/warning | `duration-data.h` struct array | `player-reacts.cc:170-180` → `T_(endmsg)` / `T_(expmsg)` | ~56/39 |
| Monster names | `dat/mons/*.yaml` `name:` | `mon-util.cc:5957` → `T_(en.c_str())` + `zh_monster_name()` map | 667 |
| Feature/dungeon names | `feature-data.h` struct array | `directn.cc:3138` → `T_(get_feature_def(grid).name)` | ~200 |
| Lua UI messages | `dat/clua/*.lua` | `l-crawl.cc` → `crawl.t_("string")` | ~20 |

**Rule**: When adding `T_()` to any of these data sources, always add the
corresponding `source.txt` entry in the same commit. Run `audit_data_i18n.py`
to verify coverage.

### Type IV — TextDB Descriptors (separate `.txt` database files)

Descriptive text stored in `%%%%`-separated key-value files under `dat/descript/zh/`
and `dat/database/zh/`, accessed by C++ lookup functions.

| Domain | DB file | Access function | Key format |
|--------|---------|-----------------|------------|
| Monster descriptions | `zh/monsters.txt` | `getLongDescription()` | Monster name → description |
| Ego/brand descriptions | `zh/egos.txt` | `getEgoString()` | `"flaming (flame) weapon ego"` |
| Spell descriptions | `zh/spells.txt` | `getLongDescription()` | Spell name → description |
| God speech | `zh/godspeak/` | `getMiscString()` | `"Trog":speech` → text |
| Decorative lines | `zh/decorlines.txt` | Lua `{{ }}` template | Lua template blocks |

Keys in these files are **always English** (used as DB lookup keys independent
of display language). Only the value side is translated.

### Type V — Protocol / Internal (never translated)

Identifiers that must remain English regardless of language setting:
- `.des` file tags (`TAG_MAJOR_VERSION`, `BRANCH_ENTRY`)
- JSON / Lua API keys
- Save-file identifiers
- Internal enum-to-string mappings used for serialisation

## Common Translation Rules

- No verb conjugation — remove `conj_verb()` calls
- Add 了 after verbs for completed actions
- Adverbs BEFORE verbs in Chinese
- No articles (the/a/an), no plural forms
- Format specifiers must match argument count after rearrangement

## Current Branch Status

### `chn-0.34.1-base` (active dev, current)
Clean rebuild from `0.34.1` stable tag. Active translation work happens here.
Commits are cherry-picked from worktree branches into this branch.

### `chinese-translation-0.34.1` (legacy, retained for reference)
Originally based on `0.34.1` stable tag, then merged `worktree-cjk-tiles-fix`
(based on `master`), bringing in 558 master gameplay commits. ~1635+ Chinese
strings across ~96 .cc files. Both WSL console and Windows tiles compile.
**Superseded by `chn-0.34.1-base`** — do not use for new work.

### `worktree-cjk-tiles-fix` (original development, master-based)
Based on `master` via `chinese-translation`. Contains the original
96 translation commits. More recent codebase but less stable.

## Key Files Modified for CJK Tiles

| File | Change |
|------|--------|
| `tilereg-text.cc` | `addstr_aux()` CJK grid cell counting, `addstr()` TODO update |
| `fontwrapper-ft.h` | Added `cjk_face`, `cjk_ttf` members |
| `fontwrapper-ft.cc` | Font fallback loading, `get_glyph_info()`/`load_glyph()` CJK face selection, `render_textblock()` ZWS skip + 2x bg, atlas cell enlargement |

## Key Files Modified for Translation (40+ files)

Major categories: game log messages, monster attack verbs (25+), UI panels (Q/W/I/E/!/$/\^), targeting interface, inventory complaints, terrain descriptions, spell names, monster description tables, command help text, species difficulty labels.

## Testing

### Manual testing

```bash
# Console
cd crawl-ref/source && make -j8 && ./crawl

# Windows tiles (cross-compile + deploy — see "Deploy to Windows" section above)
cd crawl-ref/source && make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8
cp crawl.exe ~/outputs/crawl-test/crawl.exe
cp crawl.exe /mnt/d/crawl-game/crawl.exe
cp -r dat/* /mnt/d/crawl-game/dat/
cp contrib/fonts/SarasaMonoSC-Regular.ttf /mnt/d/crawl-game/contrib/fonts/
```

### Automated Translation Regression Tests (three-layer pipeline)

Built per `~/projects/plan/1/1.md` (plan v2). All three layers output parseable
markers (`ZH_ISSUE` / `FRAME_MARKER`) on stderr/stout consumed by the M5
aggregator.

#### Layer 1 — Catch2 Unit Tests (static text scanning)

Builds and runs 16 enumerators that iterate every translatable entity (gods,
abilities, spells, monsters, features, clouds, mutations, artefacts, skills,
species, backgrounds, durations, godspeak, tutorial/hints/commands, weapon
brands, armour egos, item base names). Each enumerator runs 8 scan rules
(UNTRANSLATED, MIXED_CN_EN, FORMAT_BROKEN, GARBLED_UTF8, WHITESPACE_ANOMALY,
INVISIBLE_CHAR, PUNCT_STYLE, EMPTY_DB) on the T_()-wrapped output.

```bash
cd crawl-ref/source && make catch2-tests -j4
./catch2-tests-executable '[zh-translation]' 2>/tmp/catch2-zh.log 1>/dev/null
```

87 test cases, ~9384 assertions. Issues emitted as:
`ZH_ISSUE: <kind> | <source> | <key> | <sample>`

#### Layer 2 — dlua Smoke Test (runtime message capture)

Verifies that `-extra-opt-first language=zh` loads the i18n TextDB before
`databaseSystemInit()` and that `crawl.t_()` returns Chinese at runtime.
Captures level-up messages and `crawl.god_speaks` output via
`crawl.messages()` (exposed to dlua via `crawl_dlib` in `l-crawl.cc`).

```bash
cd crawl-ref/source && make debug -j4       # FULLDEBUG required for -test
./crawl -seed 1 -headless -no-save -name test -wizard -no-throttle \
    -extra-opt-first 'language=zh' -test zh_runtime 2>/tmp/zh-l2.log 1>/dev/null
```

Output: `FRAME_MARKER: <id> | <content>`

#### Layer 3 — RC Bot (clua, interactive UI)

Uses `crawl.sendkeys` to open wizard commands (`&o`, `&G`, `&p`, `&Y`) and
UI panels (`^`, `%`, `I`, `m`, `a`, `O`, `Ctrl-P`). Captures game messages
via `crawl.messages()`.

**Critical**: each `ready()` must send ≥1 key; use "." (wait) as no-op.
Do NOT call `crawl.flush_input()`/`crawl.redraw_screen()` after `&o` commands.
Never combine sendkeys+emit in one `ready()` — split across two iterations.
Skip `M` (spells panel) — crashes when character has no spells.

```bash
cd crawl-ref/source && make -j4 && make util/fake_pty
util/fake_pty ./crawl -seed 1 -no-save -name test -wizard -no-throttle \
    -extra-opt-first 'language=zh' -rc test/stress/zh_ui_check.rc \
    2>/tmp/zh-l3.log 1>/dev/null
```

Output: `FRAME_MARKER: <id> | <content>` (12 markers: probe, items×2, god, 7 panels, done).

#### M5 — Aggregation & Baseline

| Tool | Purpose |
|------|---------|
| `zh_runtime_check.py` | Python port of all 8 C++ scan rules; parses ZH_ISSUE + FRAME_MARKER; generates baseline-<sha>.json; compares against previous baseline (reports regressions + fixes) |
| `post_zh_runtime.sh` | Orchestrates all 3 layers in 3 modes: `fast` (aggregate existing logs), `full` (build+run all layers+aggregate), `baseline` (full + write baseline); returns non-zero on missing markers, runtime regressions, or baseline comparison failures |
| `post-coder.sh --full` | Hook at the end of existing post-coder.sh; runs the static blocking gate first, then triggers `post_zh_runtime.sh full` + `fast` for regression check |

```bash
# Full pipeline
bash .claude/scripts/post_zh_runtime.sh full
bash .claude/scripts/post-coder.sh --full

# Regression check against baseline
python3 .claude/scripts/zh_runtime_check.py \
    --catch2-stderr /tmp/catch2-zh.log \
    --lua-stderr /tmp/zh-l2.log \
    --bot-stderr /tmp/zh-l3.log \
    --baseline .claude/metrics/verify/zh-baseline-<sha>.json
```

Baselines live in `.claude/metrics/verify/zh-baseline-<sha>.json`.
Treat the newest committed baseline file as canonical; do not rely on a
hard-coded issue count in documentation.

### Verification Checklist (Per Commit)

```
1. make -j8                                   # Console build passes (0 errors)
2. make -j8 TILES=y                          # Tiles build passes (if touching tiles code)
3. grep to confirm target functions          # No missed guards
4. git diff self-review                      # Only intended lines changed
5. EN mode: launch and confirm no crash      # Required for Phase 0-1
6. EN mode: play 10 min                      # Required for Phase 2+
7. audit_data_i18n.py check                  # Data-driven source coverage
```

**On-request only** (user must explicitly ask):
```
make catch2-tests -j4                          # Layer 1: 16 enumerators, ~minute build
bash .claude/scripts/post_zh_runtime.sh full   # Layers 1-3 + aggregation, ~minutes
```

### Translation Toolchain

Before committing translation changes, run the pre-commit CI checks:

```bash
# 0. Check checkpoint is current
bash .claude/scripts/check_checkpoint.sh

# 1. T_() key coverage + data-driven sources + mprf_p compatibility + format integrity
python3 .claude/scripts/i18n_extract.py validate crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/audit_data_i18n.py crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py mprf-p crawl-ref/source/ \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py arg-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py seq-type-mismatch \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt && \
python3 .claude/scripts/scan_i18n.py format-malformed \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt
```

**Dynamic context injection**: For focused agent tasks, generate a minimal context
block with only relevant terminology and constraints:
```bash
# Capture context into a variable, include in agent dispatch prompt
CONTEXT=$(bash .claude/scripts/context_resolve.sh "task description" \
    --files <target-files>)
# Then include $CONTEXT in the agent prompt to reduce context bloat.
```

**Aggregated verification**: After code changes, use these scripts to run checks.
`post-coder.sh`, `post-translator.sh`, and `post-reviewer.sh` are blocking gates:
they return non-zero when blocking checks fail and are suitable for CI.
Within `post-coder.sh`, `scan_string_concat.py` and `smoke_test.sh` are currently
warning-only, so they surface in the report without blocking the gate.
Default is fast (seconds); `--full` / `post_zh_runtime.sh` only when explicitly requested
(they trigger compilation and runtime test execution).

```bash
bash .claude/scripts/post-coder.sh       # After code changes (blocking static gate; string-concat + smoke are warning-only)
bash .claude/scripts/post-coder.sh --full # Same as above + catch2 (L1) + dlua (L2) + RC bot (L3) + aggregation
bash .claude/scripts/post-translator.sh  # After translation (terms + format + @keyword@)
bash .claude/scripts/post-reviewer.sh    # After review (all consistency + cross-file terms)
bash .claude/scripts/post_zh_runtime.sh fast  # Runtime regression check from existing logs (seconds)
bash .claude/scripts/post_zh_runtime.sh full  # Build + run all 3 layers + aggregate (minutes)
```

**CI integration**: `.github/workflows/ci.yml` now includes two dedicated jobs:
`ZH Tooling Tests` runs `.claude/scripts/tests/run_all.sh`, and `ZH Static Checks`
runs `bash .claude/scripts/post-coder.sh`.

### String Concatenation Scanner (`scan_string_concat.py`)

Tree-sitter-based scanner that detects bare (untranslated) string literals
embedded in concatenation, stream insertion, `.append()`, and compile-time
adjacent-string expressions — patterns that regex-based tools cannot reliably
see.

```bash
# Full scan (non-blocking, graceful degradation if tree-sitter missing)
python3 .claude/scripts/scan_string_concat.py crawl-ref/source/ --skip-low

# Specific files only
python3 .claude/scripts/scan_string_concat.py \
    --files hiscores.cc,hints.cc --skip-low

# CI enforce mode (exit 2 if tree-sitter unavailable)
python3 .claude/scripts/scan_string_concat.py crawl-ref/source/ \
    --require-parser --skip-low --format json --json-output report.json

# Audit mode (include T_()-wrapped literals too)
python3 .claude/scripts/scan_string_concat.py crawl-ref/source/ --all
```

Detection rules: `+=` compound assignment, `.append()` calls, `<<` stream
insertion, `+` runtime concatenation, and compile-time adjacent strings.
Risk scoring combines variable name, prose content, file/function context,
and CJK presence. Requires `pip3 install tree-sitter tree-sitter-cpp`.

Full toolchain documentation: `.claude/scripts/TOOLCHAIN.md`

### Variadic-String UB Scanner (`scan_varargs_string.py`)

Tree-sitter-based scanner for the **Issue #42 class of undefined behavior**:
passing a `std::string` object (not `const char*`) as a `%s` argument to a
printf-style variadic function (`make_stringf`, `mprf`, `mprf_p`, `die`, ...).

**Why it's UB:** these are C variadic functions. `va_arg(ap, const char*)`
reads the first 8 bytes of the `std::string` object — its SSO buffer / data
pointer — and interprets them as a `char*`. Result: garbage / random control
characters at runtime. The compiler's `-Wformat` does **not** reliably catch
this when the argument is a non-trivial class temporary, so this static gate is
required. (First seen: `describe.cc` water-travel prompt; recurred at
`prompt.cc` yesno prompt "请仅输入%s%s。" and three `describe.cc` monster
descriptions.)

```bash
# Blocking scan (HIGH only) — wired into post-coder.sh
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/

# Include advisory WARN (bare function-call args — verify return type is const char*)
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/ --include-warn

# Specific files / JSON / CI enforce
python3 .claude/scripts/scan_varargs_string.py --files prompt.cc,describe.cc
python3 .claude/scripts/scan_varargs_string.py crawl-ref/source/ --format json --require-parser
```

Rules: `STRING_CTOR` / `CONCAT` / `TERNARY` are **HIGH (blocking)** — definite
`std::string` temporaries in a `%s` slot. `CALL_NO_CSTR` is **WARN** — a bare
function call; verify the callee returns `const char*` (safe) vs `std::string`
(needs `.c_str()`). **Fix:** build a `std::string` local first, then pass
`.c_str()`; for ternaries, remember `cond ? string(a) : ""` promotes BOTH
branches to `std::string`. Requires `pip3 install tree-sitter tree-sitter-cpp`.

## Agent Commit Discipline

**Before committing** any Agent-authored changes to crawl-ref:

1. **Verify the dev branch compiles**: `make -j8` in the main repository on the
   active dev branch (`chn-0.34.1-base`). If compilation fails, diagnose and fix
   before committing — never commit code that breaks the build.
2. **Prefer cherry-pick over merge**: When moving individual commits between
   branches (e.g. from a worktree branch to `chn-0.34.1-base`), use `git cherry-pick`
   rather than `git merge`. Cherry-pick keeps history linear, makes each commit's
   intent clear, and allows reverting individual changes without affecting
   unrelated work.

```bash
# Example: cherry-pick a single commit from worktree branch to dev branch
cd ~/projects/crawl
git checkout chn-0.34.1-base
git cherry-pick <commit-hash>

# Example: cherry-pick a range
git cherry-pick <start-hash>..<end-hash>
```

### Agent Concurrency Limits

The WSL environment has limited CPU and memory. To avoid system instability:

1. **Max 4 agents in parallel**: Never launch more than 4 Agent/Workflow
   subagents concurrently. If a task seems to need more, run them sequentially
   or ask the user to approve the scale.
2. **Agent compile with `-j4`**: When an agent needs to compile crawl-ref (e.g.
   to verify a change), use `make -j4` instead of `make -j8`. This leaves cores
   free for other agents and the main session.
3. **No background compile storms**: If one agent is already compiling, other
   agents must wait for it to finish before starting their own compilation.

### Source.txt Append-Safe Protocol (MANDATORY)

Before adding ANY entry to `dat/i18n/zh/source.txt`:

1. **Grep-first**: Verify the EN key does not already exist:
   ```bash
   grep -nF "§KEY§" crawl-ref/source/dat/i18n/zh/source.txt
   ```
   If the key exists, skip — translation is already covered.

2. **Glossary lookup**: Check `docs/decisions.md` for term rulings:
   ```bash
   grep -A3 "Choice:" docs/decisions.md | grep -i "§word§"
   ```
   Use decisions.md-approved terms (god names, species names, skill names).

3. **Post-add self-check**: Verify no duplicates or self-conflicts:
   ```bash
   python3 .claude/scripts/scan_i18n.py source-txt-integrity \
       --source-txt crawl-ref/source/dat/i18n/zh/source.txt
   ```

4. **Case discipline**: Copy EN keys verbatim from the C++ `T_("...")` literal.
   Do NOT alter case. The runtime handles case-insensitive lookup; the
   source.txt key must match the C++ literal for `i18n_extract.py` to
   cross-reference successfully.

5. **Never re-add all**: When processing enumerated entities (monsters, spells,
   etc.), diff against existing keys before writing. Never blindly append
   all enumerated names.

### Multi-Agent Parallel Development Pattern

When distributing work across multiple agents, follow this pattern to avoid
chaos and merge conflicts:

```
1. SPAN: Launch N agents simultaneously, each with `isolation: worktree`
         Each agent works on different files (no overlap)
2. WAIT:  All agents complete and commit in their own worktrees
3. PREFLIGHT: Run overlap check before consolidation:
              bash .claude/scripts/pre_consolidation_check.sh \
                  chn-0.34.1-base <wt1> <wt2> ...
4. CONSOLIDATE: Create a `consolidate-*` worktree from chn-0.34.1-base
                Cherry-pick ALL agent commits into it
                Resolve source.txt conflicts (see below)
5. VERIFY: Run `.claude/scripts/post-coder.sh` in consolidate worktree;
           make -j4; fix any compilation errors
6. MERGE:   Fast-forward merge consolidate worktree into chn-0.34.1-base
```

**Never cherry-pick agent commits directly to `chn-0.34.1-base`.** Always go
through a consolidation worktree first. This keeps the dev branch clean if
the agent changes need rework.

#### source.txt Merge Conflicts

When multiple agents add entries to `dat/i18n/zh/source.txt`, they always
append to the end, causing conflicts during consolidation. Resolution:

```bash
# All conflicts are append-only — keep both sides
sed -i '/^<<<<<<< HEAD$/d; /^=======$/d; /^>>>>>>> .*$/d' \
    crawl-ref/source/dat/i18n/zh/source.txt
git add crawl-ref/source/dat/i18n/zh/source.txt
git cherry-pick --continue
```

#### Agent-Prone Mistakes (Review Checklist)

When reviewing agent output, check for these common errors:

| Mistake | Example | Fix |
|---------|---------|-----|
| `.c_str()` on `const char*` | `skill_name(sk).c_str()` | Remove `.c_str()` — `skill_name()` returns `const char*` |
| **`std::string` in variadic `%s`** | `make_stringf(T_("%s"), string(x)+" ")` **(UB, Issue #42)** | Pass `const char*`: build a `string` var first, then `.c_str()`. Watch ternaries — `cond ? string(a) : ""` promotes BOTH branches to `std::string` |
| `mprf` with positional params | `mprf(T_("%1$s..."), ...)` | Use `mprf_p` — MinGW vsnprintf doesn't support `%n$s` |
| Untranslated inline args | `T_("You %s %s."), verb, "... the rest"` | Wrap ALL text fragments: `T_(", but do no damage")` |
| Duplicate source.txt keys | Agent adds key that already exists | Agent must `grep` source.txt before adding |
| Mass duplicate re-add | Appending all enumerated names without checking | Diff against existing keys before writing |
| `git add -A` in main repo | Stages worktrees, cache files | Only `git add` specific source files |

## Issue Tracking

All translation issues live under `~/projects/issues/` (independent git repo,
see `~/projects/issues/INDEX.md` for the master issue index and status tracking).

### File Naming Convention

| File | Purpose |
|------|---------|
| `README.md` | Problem description + status |
| `analysis.md` | Root cause analysis |
| `check.md` | Text extraction / code exploration |
| `translate.md` | Translation plan |
| `review.md` | Plan review |
| `review_commit.md` | Commit review |
| `*-plan*.md` | Execution/fix plan |
| `*-adjustment*.md` | Plan adjustments |
| `*_review*.md` | Multi-round / phase reviews |

### Auto-commit Rule

**After writing or modifying any file under `~/projects/issues/`, you MUST commit
before ending the session.** Run:

```bash
cd ~/projects/issues && git add -A && git commit -m "<type>: <brief description>"
```

Commit types:
- `Issue #N:` — numbered issue work (analysis, translation, review, fix)
- `Chore:` — cleanup, organization, file moves
- `Review:` — standalone review documents
- `Docs:` — INDEX.md or README updates

If nothing was changed under issues/, skip the commit.

### Documentation Discipline

1. Before creating a new project-wide tracking document, check if INDEX.md or
   KNOWN_ISSUES_ZH.md already covers that information
2. If a document becomes superseded by a newer system, delete it — don't leave
   it as "sedimentary documentation"
3. When adding a new translation-tracking .md file to the crawl repo, ask:
   "Does this duplicate INDEX.md or KNOWN_ISSUES_ZH.md?"
4. The answer to "how is the translation project going?" must always be
   answerable from a single file: ~/projects/issues/INDEX.md
