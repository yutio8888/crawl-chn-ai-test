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
3. `git merge <worktree-branch>` (or `git reset --hard <worktree-branch>` for fast-forward)
4. Resolve any conflicts in the main repository
5. `git reset --hard HEAD` to sync index and working tree

This ensures the main repository's index and working tree stay in sync with
the branch reference, avoiding the stale-index problem caused by `update-ref`.


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

Workflow phases: Analyze → Plan → Review Plan (gate) → Execute (code+translate parallel) → Review (3-way parallel) → Cross-validate → Report.

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


## Pre-Commit Code Review (MANDATORY)

**Before any `git commit` that touches `crawl-ref/source/`, you MUST run code
review. This is non-negotiable — the same way you must compile before committing.**

### Scope

Trigger when the staged diff includes any of:
- `crawl-ref/source/*.cc`, `*.h` — C++ source
- `crawl-ref/source/dat/i18n/zh/*.txt` — T_() translation data
- `crawl-ref/source/dat/descript/zh/*.txt` — description database
- `crawl-ref/source/dat/database/zh/*.txt` — TextDB entries

Skip for: merge commits, `.claude/` only, `~/projects/issues/` only, or `CLAUDE.md` only.

### Workflow

```
0.5 bash .claude/scripts/check_checkpoint.sh
    → If stale (exit 2/3), update ORCHESTRATION_STATE.md first
1. git diff --cached                    # Get staged changes
2. Agent(zh-code-reviewer,              # Spawn code review
     prompt="review the staged diff for this commit:
              $(git diff --cached)")
3. Wait for verdict
4. Record review metrics (see Review Metrics Logging below)
```

### Verdict Action

| Verdict | Action |
|---------|--------|
| **Go** | Proceed with `git commit` |
| **Conditional Go** | Fix 🟡 issues if quick (<2 min), otherwise note them and proceed |
| **No-Go** | Fix 🔴 blockers → `make -j8` verify → re-review → repeat from step 1 |

### Review Metrics Logging

After each code review (step 4 in the workflow), record the results to establish
a quality baseline for future optimization validation:

```bash
bash .claude/scripts/record_review.sh '{
  "date": "'"$(date -Iseconds)"'",
  "agent_type": "zh-code-reviewer",
  "task_summary": "Pre-commit review of <summary>",
  "findings": {"blocker": N, "needs_fix": N, "suggestion": N},
  "fix_iterations": N,
  "verdict": "Go|Conditional Go|No-Go",
  "trigger": "pre-commit",
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

**Important**: Always compile with `-j8` (8 parallel jobs). The WSL environment has
limited resources; using more than 8 cores may cause system instability.

### WSL Console Build (for debugging)
```bash
cd crawl-ref/source
echo 'language = zh' > init.txt
make -j8
# Output: crawl-ref/source/crawl
```

### Windows Tiles Cross-Compile (for tiles testing)
```bash
cd crawl-ref/source
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8
# Output: crawl-ref/source/crawl.exe
```

### Output Paths
- WSL console binary: `crawl-ref/source/crawl`
- Windows tiles binary: `~/outputs/crawl-test/crawl.exe` (copy from `crawl-ref/source/crawl.exe` after build)
- Windows game directory: `D:\crawl-game\` (copy exe + dat/ + contrib/fonts/)
- Font files at runtime: `contrib/fonts/DejaVuSans.ttf`, `DejaVuSansMono.ttf`, `SarasaMonoSC-Regular.ttf`

### Deploy to Windows (after cross-compile)
```bash
cp crawl-ref/source/crawl.exe ~/outputs/crawl-test/crawl.exe
cp crawl-ref/source/crawl.exe /mnt/d/crawl-game/crawl.exe
cp -r crawl-ref/source/dat/* /mnt/d/crawl-game/dat/
cp crawl-ref/source/contrib/fonts/SarasaMonoSC-Regular.ttf /mnt/d/crawl-game/contrib/fonts/
```
Note: the game must be closed before copying to `D:\crawl-game\` (file in use error otherwise).

### Required Fonts
- `contrib/fonts/DejaVuSans.ttf` (~720KB) — proportional font
- `contrib/fonts/DejaVuSansMono.ttf` (~330KB) — primary monospace font (layout metrics)
- `contrib/fonts/SarasaMonoSC-Regular.ttf` (~25MB) — CJK fallback font (must obtain separately)

### Prebuilt Contrib Libraries
Cross-compilation requires prebuilt MinGW libraries at:
`crawl-ref/source/contrib/install/x86_64-w64-mingw32/lib/`
(SDL2, SDL2-image, freetype, libpng, zlib, lua, sqlite, pcre)

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

## Known Anti-Patterns (DO NOT REPEAT)

1. **NEVER translate protocol keys** — JSON keys, `.des` tags, file format identifiers must remain English
2. **NEVER call `conj_verb()` on Chinese strings** — produces garbled output like `"抓取s"`
3. **NEVER change `.name` fields used as DB lookup keys** — use `zh_ability_map` for display names instead
4. **NEVER mix CN/EN in the same format string** — produces mixed-language output; use `T_()` on ALL text fragments
5. **NEVER assume argument order is the same in both languages** — Chinese grammar often swaps subject/object positions
6. **NEVER change `god_name()` return value for DB lookups** — use `_god_name_en()` for database keys
7. **NEVER use `buf.size()` for CJK alignment** — use `strwidth()` for display-width-aware padding
8. **NEVER add `T_()` to a runtime variable without a source.txt entry** —
   `T_(variable)` is invisible to `i18n_extract.py`; always run
   `audit_data_i18n.py` after changes to data-driven files
   (`duration-data.h`, `dat/mons/*.yaml`, `feature-data.h`, `.lua`)
9. **NEVER assemble UI text by concatenating bare English fragments** —
   `desc += " (if damage dealt)"`, `text << "Looks like "`, etc. produce
   untranslatable text. Use `T_()` with complete sentences or make_stringf
   templates. Run `scan_string_concat.py` to detect existing violations.

## Translation Decision Registry

Before translating any entity name (god, monster, spell, item, skill):
1. Read `docs/decisions.md` — the Single Source of Truth for naming decisions
2. If the entity already appears in DECISIONS.md, follow the existing ruling
3. If you make a NEW naming decision, record it in DECISIONS.md

Before submitting any review touching entity names:
  bash .claude/scripts/check_consistency.sh

### Pre-session Checklist

1. Read `~/projects/issues/INDEX.md` → understand issue landscape
2. Read `docs/decisions.md` → know existing rulings
3. Check checkpoint: `bash .claude/scripts/check_checkpoint.sh`
   → If it warns (exit 2/3), update `.claude/ORCHESTRATION_STATE.md` before starting new work
4. If modifying files under `crawl-ref/source/`, run `check_consistency.sh --rulings`

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

**Aggregated verification**: Instead of running individual checks, use the post-agent
aggregation scripts that capture all output to `.claude/metrics/verify/`:

```bash
bash .claude/scripts/post-coder.sh       # After code changes (T_() + mprf-p + arg-mismatch + seq-type-mismatch + format-malformed + anti-patterns + string-concat + smoke)
bash .claude/scripts/post-translator.sh  # After translation (terms + format + @keyword@)
bash .claude/scripts/post-reviewer.sh    # After review (all consistency + cross-file terms)
```

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

### Multi-Agent Parallel Development Pattern

When distributing work across multiple agents, follow this pattern to avoid
chaos and merge conflicts:

```
1. SPAN: Launch N agents simultaneously, each with `isolation: worktree`
         Each agent works on different files (no overlap)
2. WAIT:  All agents complete and commit in their own worktrees
3. CONSOLIDATE: Create a `consolidate-*` worktree from chn-0.34.1-base
                Cherry-pick ALL agent commits into it
                Resolve source.txt conflicts (see below)
4. VERIFY: make -j4 in the consolidate worktree, fix any compilation errors
5. MERGE:   Fast-forward merge consolidate worktree into chn-0.34.1-base
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
| `mprf` with positional params | `mprf(T_("%1$s..."), ...)` | Use `mprf_p` — MinGW vsnprintf doesn't support `%n$s` |
| Untranslated inline args | `T_("You %s %s."), verb, "... the rest"` | Wrap ALL text fragments: `T_(", but do no damage")` |
| Duplicate source.txt keys | Agent adds key that already exists | Agent must `grep` source.txt before adding |
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
