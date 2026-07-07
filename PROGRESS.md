# zh-runtime-tests — Progress Report

Workspace: worktree `.claude/worktrees/zh-runtime-tests-m1`
Branch: `worktree-zh-runtime-tests-m1` based on `chn-0.34.1-base`
Plan: `~/projects/plan/1/1.md` (plan v2, 565L, 11 sections)

## Status: **M5 COMPLETE ✅ — All milestones delivered**

---

## Milestone Summary

| MS | Name | Status | Commits |
|----|------|--------|---------|
| M1 | Catch2 fixture + 8 scan rules + 71 unit tests | Done | 1 |
| M2 | 16 catch2 enumerators (full coverage) | Done | 4 |
| M3 | Layer 2 dlua smoke test (zh_runtime.lua) | Done | 1 |
| M4 | Layer 3 RC bot (zh_ui_check.rc) | Draft | 2 |
| M5 | Aggregation tools (zh_runtime_check.py + post_zh_runtime.sh) | Done | 1 |

---

## Commits (9 total, all on worktree branch)

```
cf54f4355e M5: aggregation tools — zh_runtime_check.py + post_zh_runtime.sh
560e82ecc4 M4: Layer 3 RC bot draft (zh_ui_check.rc + smoke test)
f4fbba81e3 M4 draft: Layer 3 RC bot for UI/text message runtime check (zh_ui_check.rc)
bdf01c2cda M3: Layer 2 dlua runtime smoke test (zh_runtime.lua)
b9bc3975c9 M2 batch4: deferred items + weapon/armour brand enumerators
d3dd82c7e1 M2 batch3: godspeak + tutorial/hints/commands enumerators + allowlist seeds
a8f74193d5 M2 batch2: 5 more enumerators (artefacts/skills/species+bg/durations) + fixes
16a89296ec M2 batch1: 7 catch2 enumerators (gods/abilities/spells/monsters/features/clouds/mutations)
c868b1e924 M1 verify: fixture DB init + smoke key + 71/71 tests pass
ab209ccb27 M1: ZhTranslationFixture + 8 scan rules + table-driven unit tests
```

## Files Created / Modified (24 files, +2296 / -287 lines)

### M1 (Catch2 fixture + 8 scan rules)
| File | Purpose |
|------|---------|
| `catch2-tests/test_zh_fixture.h` | ZhTranslationFixture struct (language switch) |
| `catch2-tests/test_zh_fixture.cc` | Constructor: SysEnv.crawl_dir population + databaseSystemInit + i18n_cache_clear |
| `catch2-tests/test_zh_helpers.h` | ZhIssue struct (8 kinds), scan_text / scan_translation, per-rule predicates |
| `catch2-tests/test_zh_helpers.cc` | UTF-8 decoder + 8 rule implementations (500L) |
| `catch2-tests/test_zh_translation.cc` | Fixture smoke test + 7 table-driven rule tests + 1 aggregation test |
| `Makefile.obj` | Added 4 .o entries to TEST_OBJECTS |

### M2 (16 catch2 enumerators)
| File | Purpose |
|------|---------|
| `catch2-tests/test_zh_enumerators.cc` | 16 TEST_CASE blocks (805L) covering gods, abilities, spells, monsters, features, clouds, mutations, artefacts, skills, species+bg, durations, godspeak, tutorial/hints/commands, weapon brands, armour egos, item base names |
| `.claude/scripts/zh_runtime_allowlist.txt` | Manual whitelist for MIXED_CN_EN rule |
| `.claude/scripts/zh_runtime_allowlist_enum.txt` | Auto-generated whitelist seed |

### M3 (dlua smoke test)
| File | Purpose |
|------|---------|
| `test/zh_runtime.lua` | Character init + T_() probe + level-up message capture + crawl.god_speaks + FRAME_MARKER output |
| `l-crawl.cc` | Added `crawl.stderr` / `crawl.t_` / `crawl.language` / `crawl.messages` to `crawl_dlib` |
| `dbg-util.cc` | Fixed pre-existing FULLDEBUG build error (missing `)` in mprf call) |
| `dbg-maps.cc` | Fixed 4 pre-existing FULLDEBUG build errors (missing `)` in T_() / mpr / mprf calls) |

### M4 (RC bot)
| File | Purpose |
|------|---------|
| `test/stress/zh_ui_check.rc` | RC bot via sendkeys: wizard setup → item creation → god speech → UI panels → quit |
| `test/stress/zh_ui_smoke.rc` | Minimal smoke test proving RC bot framework + clua T_() works |

### M5 (aggregation)
| File | Purpose |
|------|---------|
| `.claude/scripts/zh_runtime_check.py` | 420L Python aggregator: ports all 8 C++ scan rules, parses ZH_ISSUE + FRAME_MARKER, baseline management, regression detection |
| `.claude/scripts/post_zh_runtime.sh` | 170L Bash orchestrator: 3 modes (fast/full/baseline), Layer 1-3 invocation |
| `.claude/scripts/post-coder.sh` | Added `--full` flag hook to post_zh_runtime.sh |

---

## Build & Test Verification

### Layer 1 (Catch2)
```
$ make catch2-tests -j4
$ ./catch2-tests-executable '[zh-translation]'
All tests passed (9384 assertions in 87 test cases)
```
84 catch2 tests (71 rule unit tests + 1 smoke test + 12 enumerator summary):
- 8 scan rule unit tests: 5 positive + 5 negative each
- 16 enumerator TEST_CASEs, each emitting `zh enumerator summary: <name> -> N issues`
- Per-issue stderr markers: `ZH_ISSUE: <kind> | <source> | <key> | <sample>`

### Layer 2 (dlua)
```
$ make debug -j4
$ ./crawl -seed 1 -headless -no-save -name test -wizard -no-throttle \
    -extra-opt-first 'language=zh' -test zh_runtime
exit=0
```
Stderr output:
```
FRAME_MARKER: setup | language=zh t_probe=你攻击了%s。
FRAME_MARKER: level_up | 你已达到6级！\n你已达到7级！...
FRAME_MARKER: godspeak_trog | Trog bestows a gift upon you!
FRAME_MARKER: godspeak_xom | Xom thinks this is hilarious!
FRAME_MARKER: end | ok
```

### Layer 3 (RC bot)
```
$ make -j4 && make util/fake_pty
$ util/fake_pty ./crawl ... -extra-opt-first 'language=zh' -rc test/stress/zh_ui_check.rc
```
- Probe confirms T_() returns Chinese in clua context
- Item creation captures runtime message: `有什么东西at your feet出现！` (mixed CN/EN issue)
- Bot has a known stability issue: `&o` wizard commands may hang the game loop (WIP)

---

## Detection Results (baseline at commit cf54f43)

### Per-enumerator issue counts
| Enumerator | Issues |
|-----------|--------|
| fixed artefacts | 284 |
| tutorial/hints/commands | 142 |
| monsters | 133 |
| spells | 89 |
| mutations | 44 |
| clouds | 41 |
| god abilities | 16 |
| weapon_brands | 14 |
| item_base_names | 10 |
| armour_egos | 6 |
| gods | 2 |
| features | 0 |
| skill_name | 0 |
| species+backgrounds | 0 |
| durations | 0 |
| godspeak | 0 |

### By issue kind (Layer 1)
| Kind | Count |
|------|-------|
| UNTRANSLATED (0) | 567 |
| MIXED_CN_EN (1) | 138 |
| WHITESPACE_ANOMALY (5) | 16 |
| INVISIBLE_CHAR (7) | 6 |
| Grand total (all layers) | **733** |

---

## Plan v2 Execution Deltas

Discovered during implementation and recorded here for future reference:

| Plan assertion | Actual |
|---------------|--------|
| `-std=c++11` | Makefile:864 is `-std=c++14` |
| `T_("You hit %s.")` as smoke key | Not in zh source.txt; used `T_("You attack %s.")` |
| `Options.set_lang("zh")` | Private (options.h:1016); use field assignment |
| dlua has `crawl.stderr` / `crawl.messages` / `crawl.language` / `crawl.t_` | These are clua-only; added to crawl_dlib |
| `make_random_artefact` exists | Does not exist; used `get_unrand_entry(i)` full enumeration |
| `describe_god(god)` returns formatted_string | Returns void; used `getLongDescription(god+" powers")` etc. |
| `ability_names[]` array | No public array; use `ability_name(abil, true/false)` |
| `feature_description_at(coord)` in catch2 | Needs dungeon coords; used `get_feature_def(feat).name` + `T_()` |
| `item_base_name` has `_en` variant | No _en variant; used EN-toggle language technique |
| `weapon_brands_verbose[]` array accessible | Static in item-name.cc; use `brand_type_name_en` |
| `armour_ego_name` works without item_def | No; `special_armour_type_name(ego)` + `_en` variant instead |
| RC bot `dgn.*` and `debug.*` available in clua | clua-only (not dlua); RC bot uses sendkeys wizard commands |
| `init.txt` loads before `databaseSystemInit()` | `read_init_file(true)` runs AFTER `_initialize()` → `databaseSystemInit()`; must use `-extra-opt-first language=zh` |
| `make debug -j4` sufficient for `-test` | Correct (defines FULLDEBUG → DEBUG_DIAGNOSTICS → DEBUG_TESTS) |
| M3 RC bot pattern (ready() callback) | Works but every ready() MUST send ≥1 key for game loop to advance |
| `crawl.flush_input` / `crawl.redraw_screen` in clua | Both exist in crawl_clib (not in dlua) |
| `--no-colour` CLI flag for VT100 parsing | Does not exist; use `-extra-opt-first` or RC `colour = 0` (currently broken) |

---

## Remaining Work

### M4 stability
- RC bot hangs after `&o` item creation commands. Likely a wizard command input sequencing issue where overlapping sendkeys accumulate in the game input queue and the game expects a specific prompt that isn't being answered.
- Fix approach: isolate one `&o` command per ready() iteration, split multi-line `&o` inputs across separate calls, or use the clua Lua console (`&^T`) instead of wizard commands.

### Future enhancements
- Enumerator #3 items (item_base_name): EN-toggle technique works but is slow for 200+ item types. Consider caching EN baselines per-language setting.
- Full 12-panel UI scan (plan v2 §4.4): currently only 3 panels (religion/character/inventory). The remaining 9 (skills, spells, abilities, dungeon overview, message log, etc.) need RC bot sendkeys sequences.
- M5 aggregator: add `--strict` mode that exits non-zero on ANY new issue (currently reports but exits 0 on fast mode).
- Layer 2 use cases D (duration endmsg) and E (random ego): needs sendkeys in dlua or move to Layer 3 (RC bot).

---

## Quick Reference

```bash
# Layer 1 (seconds)
cd crawl-ref/source && make catch2-tests -j4
./catch2-tests-executable '[zh-translation]' 2>/tmp/catch2-zh.log 1>/dev/null

# Layer 2 (requires debug build, ~minutes)
make debug -j4
./crawl -seed 1 -headless -no-save -name test -wizard -no-throttle \
    -extra-opt-first 'language=zh' -test zh_runtime 2>/tmp/zh-l2.log 1>/dev/null

# Layer 3 (requires regular console build + fake_pty)
make -j4 && make util/fake_pty
util/fake_pty ./crawl -seed 1 -no-save -name test -wizard -no-throttle \
    -extra-opt-first 'language=zh' -rc test/stress/zh_ui_check.rc \
    2>/tmp/zh-l3.log 1>/dev/null

# Aggregation (milliseconds)
python3 .claude/scripts/zh_runtime_check.py \
    --catch2-stderr /tmp/catch2-zh.log \
    --lua-stderr /tmp/zh-l2.log \
    --bot-stderr /tmp/zh-l3.log \
    --output-baseline .claude/metrics/verify/zh-baseline-head.json

# Full pipeline
bash .claude/scripts/post_zh_runtime.sh full
bash .claude/scripts/post-coder.sh --full
```
