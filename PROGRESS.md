# M1 Progress Checkpoint — zh-runtime-tests-m1 worktree

## Status: **M1 COMPLETE ✅**

M1 of plan v2 (`~/projects/plan/1/1.md`) is done. Catch2 Layer 1 fixture
loads `dat/i18n/zh/source.txt` and the smoke assertion confirms a known
translated key returns Chinese bytes; all 8 scan rules pass 5+5 table-
driven unit tests.

Following CLAUDE.md worktree discipline, all work is on the
`worktree-zh-runtime-tests-m1` branch.

## Build & test status

```
$ cd crawl-ref/source && make catch2-tests -j4
... LINK catch2-tests-executable
./catch2-tests-executable
Randomness seeded to: 361618215
===============================================================================
All tests passed (9368 assertions in 71 test cases)
```

71 test cases / 9368 assertions total, including:
- 1 fixture smoke (verifies `T_("You attack %s.")` -> `"你攻击了%s。"`)
- 7 table-driven rule unit tests (5 positives + 5 negatives per rule)
- 1 aggregation sanity test (`scan_text` aggregates ≥2 issues)

## Files created / modified (all in `crawl-ref/source/catch2-tests/`)

1. `test_zh_fixture.h` — declares `ZhTranslationFixture` struct.
2. `test_zh_fixture.cc` — constructor:
   - Snapshots `Options.language` + `Options.lang_name`.
   - Calls `ensure_crawl_dir_set()`: if `SysEnv.crawl_dir` is empty (catch2
     build skips `crawl_init_data()`), populates it with `getcwd()`. This is
     the **critical fix** — without it `_get_base_dirs()` (files.cc:411)
     returns an empty rawbase list after the `if (base.empty()) continue;`
     filter, and `databaseSystemInit()` aborts with "Cannot find data file
     'descript/features.txt' anywhere".
   - Sets `Options.language = lang_t::ZH`, `Options.lang_name = "zh"`.
   - Calls `databaseSystemInit()` (database.cc:380) to open all TextDB
     layers including SourceDB (`dat/i18n/<lang>/source.txt`).
   - Calls `i18n_cache_clear()` (database.cc:1055) to ensure the key->ptr
     index doesn't carry any EN-mode entries from a prior test.
   - Destructor restores the previously-saved language and re-clears.
3. `test_zh_helpers.h` — declares `ZhIssue` struct with 8 `Kind` enum
   values, `scan_text()` / `scan_translation()` aggregators, and per-rule
   predicate functions.
4. `test_zh_helpers.cc` — implements the UTF-8 codepoint decoder
   (`decode_cp`) and all 8 rules per plan v2 §2.3:
   - `UNTRANSLATED` — uses `text != key` (string content compare, NOT
     pointer); only fires when key has ASCII letters; resolves B2.
   - `MIXED_CN_EN` — requires CJK ideograph + ≥3 consecutive ASCII letters;
     built-in whitelist covers resistance / stat tags (rF, AC, EV, SH, ...),
     all canonical god names, dungeon / branch names, and tech prefixes
     (Tele, Rage, Highlight). Resolves N5 minimum set.
   - `FORMAT_BROKEN` — 4 subrules: stray 's'/'x' after 2+ CJK (conj_verb
     remnant), bare trailing `%s`, mprf-p positional `%n$s`, format-spec
     count mismatch between text and English key.
   - `GARBLED_UTF8` — decode_cp surfaces U+FFFD on overlongs, surrogate
     halves, codepoints > U+10FFFF, or non-tab/newline ASCII control chars.
   - `EMPTY_DB` — structural (caller-side), so no helper predicate.
   - `WHITESPACE_ANOMALY` — rejects `\r` remnants, double-space (allows
     `  - bullet`), leading space (unless markdown `-`/`*` bullet), trailing
     space.
   - `INVISIBLE_CHAR` — U+200B ZWS, U+FEFF BOM, U+00A0 NBSP, U+200C ZWNJ,
     direction marks, line/paragraph separators, word joiner, Private Use
     Areas (BMP + supplementary), emoji ranges.
   - `PUNCT_STYLE` — half-width `(` `)` `,` `.` `:` `;` adjacent to a CJK
     ideograph (walks codepoint vector to find adjacency).
5. `test_zh_translation.cc` — fixture smoke TEST_CASE (`T_("You attack %s.")`
   returns a string with at least one non-ASCII byte = Chinese rendered)
   + 7 table-driven rule unit tests + 1 aggregation test. Uses
   `std::tuple<N>` row format and `std::get<N>()` access (catch2-tests
   build at `-std=c++14`, not c++17 — no structured bindings available).
6. `crawl-ref/source/Makefile.obj` — appended
   `catch2-tests/test_zh_fixture.o`, `test_zh_helpers.o`,
   `test_zh_translation.o` to the `TEST_OBJECTS` list (right after
   `test_positional_format.o`).

## Edge cases discovered during implementation

- `Options.set_lang(...)` is **private** (options.h:1016); plan v2 §2.2
  example was updated to directly assign the two public fields
  `Options.language` (= `lang_t::ZH`) and `Options.lang_name` (= literal
  `"zh"`).
- `databaseSystemInit()` (database.cc:380) is the proper entry point;
  `i18n_cache_clear()` alone is insufficient because the TextDB layers are
  never opened in catch2's fake-main.hpp bootstrap.
- `SysEnv.crawl_dir` is empty by default in catch2; populating it via
  `getcwd()` is the minimal fix. `read_init_file()` would work too but
  pulls in heavier machinery (RC parsing, env probes, ...).
- `Makefile.obj` is detected by `Read` as binary but sed/awk/edit work
  fine on it. The Makefile builder does NOT regenerate Makefile.obj —
  earlier appearance of rollback was actually `git worktree add` creating
  a fresh checkout, not a generation step. After the worktree is created
  the main repo still had the `M Makefile.obj` staged; manual re-edit
  is safe during work-in-progress.
- Catch2 `REQUIRE(a || b)` hits a `static_assert` that forbids `||`
  inside assertions; wrap as `REQUIRE((a || b))` or extract to a bool.
- Catch2 `GENERATE(table<...>)` payload must be homogeneous: pass
  `Row{...}` initializer list, where `Row = std::tuple<...>`.

## Notes on plan v2 deltas

| Plan claim | Actual |
|------------|--------|
| STDFLAG = `-std=c++11` replaced with c++14 | Makefile:864 already c++14; we used tuple<N> get |
| Example "You hit %s." smoke key | Not present in zh source.txt; switched to "You attack %s." |
| `Options.set_lang("zh")` | Private; use field assignment |
| Implicit TextDB load | Required explicit `databaseSystemInit()` + `SysEnv.crawl_dir` setup |
| `i18n_cache_clear()` is sufficient | Necessary but not sufficient; need databaseSystemInit first |

## Next milestone: M2

Per plan v2 §7, M2 is: 14 catch2 enumerators (`test_zh_translation.cc`
extended) + `zh_runtime_allowlist.txt` + `zh_runtime_allowlist_enum.txt`
initial versions + integrated Full Layer 1 run establishing the first
baseline.依赖审阅项: B1, B2, B4, N1, N2, N4.

To begin M2, modify the test_zh_translation.cc in this worktree to add
the 14 enumerators using the helpers + API signatures confirmed in M1
research.