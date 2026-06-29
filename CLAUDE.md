# CLAUDE.md — Dungeon Crawl Stone Soup Chinese Translation + CJK Tiles

This file guides ongoing Chinese (zh) translation work and CJK tiles rendering
support for DCSS.

| Branch | Role | Based on |
|--------|------|----------|
| `chn-0.34.1-base` | **Active dev branch** | `chinese-translation-0.34.1` |
| `chinese-translation-0.34.1` | Stable integration target | `0.34.1` stable tag |
| `worktree-cjk-tiles-fix` | CJK tiles original dev | `master` |

## ⚠️ Worktree Branch Discipline

Each worktree operates on its own isolated branch. **Do NOT push, merge, or
update-ref directly from a worktree to other branches.** Doing so causes
`git update-ref` to move the branch pointer without updating the main
repository's index and working tree, leading to false "staged changes".

**Correct procedure after committing in a worktree:**
1. `cd ~/projects/crawl` (the main repository)
2. `git checkout <target-branch>` (e.g. `chinese-translation-0.34.1` or `chn-0.34.1-base`)
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
Agent(subagent_type="zh-translator", description="Translate <target>",
  prompt="<full translation task with file paths and context>")
```

### Code Implementation → `crawl-coder` agent

| Trigger | Example |
|---------|---------|
| C++ source modification | "修一下这个 bug", "把这个函数加上 language guard" |
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

### Full Pipeline → `translation-pipeline` workflow

For complex issues requiring the full document → analyze → translate → review →
execute cycle:

| Trigger | Example |
|---------|---------|
| "有个翻译问题" | "神名翻译不一致，帮我看看" |
| "translation bug" | "There's a bug in the Chinese UI text" |
| New issue from scratch | "帮我处理 Issue #N" |

```
Skill("translation-pipeline", args={problem: "<description>"})
```

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
1. git diff --cached                    # Get staged changes
2. Agent(zh-code-reviewer,              # Spawn code review
     prompt="review the staged diff for this commit:
              $(git diff --cached)")
3. Wait for verdict
```

### Verdict Action

| Verdict | Action |
|---------|--------|
| **Go** | Proceed with `git commit` |
| **Conditional Go** | Fix 🟡 issues if quick (<2 min), otherwise note them and proceed |
| **No-Go** | Fix 🔴 blockers → `make -j8` verify → re-review → repeat from step 1 |

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

### Layer 1: Descript Database (`dat/descript/zh/*.txt`)

Format: `%%%%`-separated entries with `key\n\ndescription` blocks.
Spell keys must match `spell_title() + " spell"` — update keys when translating spell names.

### Layer 2: Hardcoded Source Strings

Three patterns:
- **Pattern A**: Direct replacement (most common) — Chinese strings replace English
- **Pattern B**: Runtime language check — used for species/job names
- **Pattern C**: Format string adjustment — Chinese grammar differs (了 particle, adverb position, no conjugation)

## Common Translation Rules

- No verb conjugation — remove `conj_verb()` calls
- Add 了 after verbs for completed actions
- Adverbs BEFORE verbs in Chinese
- No articles (the/a/an), no plural forms
- Format specifiers must match argument count after rearrangement

## Current Branch Status

### `chn-0.34.1-base` (active dev, current)
Based on `chinese-translation-0.34.1`. Active translation work happens here.
Cherry-picked commits land on `chinese-translation-0.34.1` after verification.

### `chinese-translation-0.34.1` (stable integration)
Based on `0.34.1` stable tag. Merged 96 translation commits from
`worktree-cjk-tiles-fix`. ~1635+ Chinese strings across ~96 .cc files.
18 merge conflicts resolved. Both WSL console and Windows tiles compile.

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

## Language Guard Design

### English Mode Goal: 基本可用 (Basically Usable)

The current branch hardcodes many strings as Chinese without `Options.language` guards.
The goal for English mode is **basic usability**: no crashes, readable UI, core operations
functional. Perfect bilingual parity is a long-term goal (no hard deadline).

### Translation Data Classification Framework

All translated strings fall into one of four types:

| Type | Description | Correct Approach |
|------|-------------|-----------------|
| **I — Static Display Data** | Names, descriptions from DB | Method B: Chinese data + English fallback for DB lookups |
| **II — Dynamic Format Strings** | `mprf()` messages with `%s` | Method A: `Options.language` guard at each call site |
| **III — Helper Function Returns** | `held_status()`, `charge_desc()` | Must be language-aware — return value used by callers |
| **IV — Internal/Protocol Data** | JSON keys, `.des` tags, Lua API | Must always be English regardless of language setting |

### Known Anti-Patterns (DO NOT REPEAT)

1. **NEVER translate protocol keys** — JSON keys, `.des` tags, file format identifiers must remain English
2. **NEVER call `conj_verb()` on Chinese strings** — produces garbled output like `"抓取s"`
3. **NEVER change `.name` fields used as DB lookup keys** — use `zh_ability_map` for display names instead
4. **NEVER mix CN/EN in the same format string without a language guard** — produces mixed-language output
5. **NEVER assume argument order is the same in both languages** — Chinese grammar often swaps subject/object positions
6. **NEVER change `god_name()` return value for DB lookups** — use `_god_name_en()` for database keys
7. **NEVER use `buf.size()` for CJK alignment** — use `strwidth()` for display-width-aware padding

### Translation Decision Registry

Before translating any entity name (god, monster, spell, item, skill):
1. Read `docs/decisions.md` — the Single Source of Truth for naming decisions
2. If the entity already appears in DECISIONS.md, follow the existing ruling
3. If you make a NEW naming decision, record it in DECISIONS.md

Before submitting any review touching entity names:
  bash .claude/scripts/check_consistency.sh

### Pre-session Checklist

1. Read `~/projects/issues/INDEX.md` → understand issue landscape
2. Read `docs/decisions.md` → know existing rulings
3. If modifying files under `crawl-ref/source/`, run `check_consistency.sh --rulings`

### Verification Checklist (Per Commit)

```
1. make clean && make -j8                    # Console build passes (0 errors)
2. make -j8 TILES=y                          # Tiles build passes (if touching tiles code)
3. grep to confirm target functions          # No missed guards
4. git diff self-review                      # Only intended lines changed
5. EN mode: launch and confirm no crash      # Required for Phase 0-1
6. EN mode: play 10 min                      # Required for Phase 2+
```

## Agent Commit Discipline

**Before committing** any Agent-authored changes to crawl-ref:

1. **Verify the dev branch compiles**: `make clean && make -j8` in the main
   repository on the active dev branch (`chn-0.34.1-base`). If compilation fails,
   diagnose and fix before committing — never commit code that breaks the build.
2. **Prefer cherry-pick over merge**: When moving individual commits between
   branches (e.g. from a worktree branch to `chn-0.34.1-base`, or from
   `chn-0.34.1-base` to `chinese-translation-0.34.1`), use `git cherry-pick`
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
