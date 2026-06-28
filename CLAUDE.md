# CLAUDE.md — Dungeon Crawl Stone Soup Chinese Translation + CJK Tiles

This file guides ongoing Chinese (zh) translation work and CJK tiles rendering
support for DCSS.
Current branch: `chinese-translation-0.34.1` (based on `0.34.1` stable tag).
Sibling branch: `worktree-cjk-tiles-fix` (based on `master`, original development).

## ⚠️ Worktree Branch Discipline

This worktree uses branch `cr0626`. **Do NOT push, merge, or update-ref
directly from this worktree to other branches** (e.g. `chinese-translation-0.34.1`).
Doing so causes `git update-ref` to move the branch pointer without updating
the main repository's index and working tree, leading to false "staged changes".

**Correct procedure after committing in this worktree:**
1. `cd ~/projects/crawl` (the main repository)
2. `git checkout chinese-translation-0.34.1` (or the target branch)
3. `git merge cr0626` (or `git reset --hard cr0626` for fast-forward)
4. Resolve any conflicts in the main repository
5. `git reset --hard HEAD` to sync index and working tree

This ensures the main repository's index and working tree stay in sync with
the branch reference, avoiding the stale-index problem caused by `update-ref`.

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

### `chinese-translation-0.34.1` (current, stable-based)
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
1. make -j8 TILES=y                         # Compiles cleanly
2. grep to confirm target functions          # No missed guards
3. git diff self-review                      # Only intended lines changed
4. EN mode: launch and confirm no crash      # Required for Phase 0-1
5. EN mode: play 10 min                      # Required for Phase 2+
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
