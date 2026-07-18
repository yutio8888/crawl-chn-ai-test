---
name: crawl-coder
description: DCSS Chinese i18n code implementation — C++ source modification, T_() migration, TextDB loader/schema and assigned structural repairs, ZH guard removal, Makefile fixes, compilation verification
---

# Crawl-Coder Skill

Code implementation agent for DCSS Chinese translation. Covers the full spectrum:
adding T_() guards, removing ZH language switches, TextDB loader/schema work,
creating new zh-* source files, fixing mixed CN/EN output, ARG-DIFF resolution,
and compilation/build fixes.

<!-- BEGIN GENERATED: i18n-safety -->
# i18n-safety-v2

This policy is the shared safety contract for DCSS Chinese i18n code.

- `T_()` and `C_()` return borrowed pointers that become invalid after
  `i18n_cache_clear()`. Never retain them in static or namespace storage,
  members, persistent containers, aggregates, or callback captures.
- Persistent literal tables use `N_("key")` or
  `NC_("context", "key")`, then translate at the consumption site with the
  matching `T_()` or `C_()`. Copy the result to `std::string` if it crosses a
  statement boundary.
- Never pass a `std::string`, concatenation, ternary promoted to
  `std::string`, or a `std::string`-returning call directly to a printf-style
  variadic `%s` slot. Store it locally and pass `.c_str()`.
- Treat every `CALL_NO_CSTR` scanner warning as requiring manual return-type
  confirmation: `const char *` is safe; `std::string` needs `.c_str()`.
- Never pass translated text to English morphology such as `conj_verb()`.
- Movement phrases remain English internal values until the display sink.
  Translate them with `translated_move_phrase()` and the applicable grammar
  context; update `move_i18n_manifest.json` and require exact-key coverage.
- Keep protocol, lookup, serialization, Lua comparison, and TextDB key values
  in English. Translate only at display boundaries.
- When a changed value may serve both identity and display, enumerate its
  producer, every intermediate consumer, and its final sinks. Identity and
  lookup paths use the original value or an English accessor (for example,
  `_god_name_en()`); only display sinks localize it. Cover the real lookup and
  fallback path with a targeted test.
- Use `mprf_p` for positional `%n$s` formats and never mix positional and
  sequential placeholders.
- Resolve terminology from the current `docs/glossary.md` immediately before
  work. Do not embed canonical Chinese terms in Agent or Skill configuration.

Configuration checks validate this policy's generated blocks. C++ source
analysis remains the responsibility of `scan_i18n_lifetime.py`,
`scan_varargs_string.py`, and the other code verification gates.
<!-- END GENERATED: i18n-safety -->

<!-- BEGIN GENERATED: asset-ownership -->
# asset-ownership-v1

Every task assigns exactly one writer to every file. Agents are not alone in
the repository: preserve existing changes, do not revert work owned by another
writer, and coordinate before touching an overlapping path.

## Default ownership

- `zh-translator` owns Chinese wording and translation assets under
  `crawl-ref/source/dat/i18n/zh/`, `crawl-ref/source/dat/database/zh/`, and
  `crawl-ref/source/dat/descript/zh/`.
- `crawl-coder` owns C++, headers, Lua integration, build files, parsers,
  database loading/schema, and code-side `T_()`/`C_()` migration.
- English/protocol/TextDB lookup keys remain English regardless of the writer.
- Reviewers are read-only and never repair findings during the readiness pass.

## Structural exception

A coder may edit an explicitly listed ZH data file for a purely structural or
mechanical repair, such as a broken delimiter or loader-compatible key, only
when the orchestrator assigns that complete path to the coder and no translator
is writing it concurrently. The coder must not make independent wording or
terminology decisions under this exception.

## Mixed tasks

For a task that needs both translated assets and source changes:

1. resolve the current glossary context;
2. assign every ZH translation asset to one translator writer;
3. complete translation-asset edits first;
4. run the coder for source/build changes without reopening translator-owned
   files;
5. verify the combined worktree and review the exact committed diff.

Batch work uses the same ownership model. Parallel analysis is allowed, but
translation assets are written sequentially by their single owner.
<!-- END GENERATED: asset-ownership -->

## Shared Verification Authoring

<!-- BEGIN GENERATED: verification-authoring -->
# verification-authoring-v1

This policy applies when an agent writes or reviews a validator, scanner,
deployment check, parser-facing test, or other verification control.

- Enumerate the complete production artifact and its invariants before writing
  the check. Counts alone never prove identity, membership, uniqueness, order,
  content, conservation, or rejection of unknown data.
- Match production semantics for the parser, working directory,
  initialization, locale, environment, and compile/runtime options. Prefer the
  production helper or entry point. If a test must reimplement semantics,
  document the difference and cover it with a strict end-to-end check.
- Exercise the real construction, lookup, fallback, or deployment path. A
  relaxed helper test is insufficient unless a stricter end-to-end test covers
  the behaviour it omits.
- Fail closed when required input is missing, parsing is incomplete, an unknown
  field or state appears, or the complete invariant cannot be evaluated.
- Give every invariant a passing fixture and a minimal negative mutation that
  breaks only that invariant and must be rejected.
- Preserve raw tool evidence. Report the exact command, exit code, blocking
  failure count, relevant warnings, and the reason a failure is or is not
  actionable.

Reviewers reject checks that validate only source tokens or a convenient subset
when the production consumer observes a larger effective artifact.
<!-- END GENERATED: verification-authoring -->

All later examples that write `source.txt` or another ZH data file are
conditional on the structural exception above. In mixed translation/code work,
the translator owns those assets and this skill edits source/build files only.

## When to Use

| Trigger | Example |
|---------|---------|
| Add T_() wrapping | "把这个文件的硬编码中文改成 T_()", "add T_() to this function" |
| Remove ZH guards | "去掉这个文件的语言判断", "replace Options.language checks" |
| TextDB structure | "fix %%%% separator", "repair TextDB loader/schema" |
| New zh-* file | "创建新的中文 scroll appearance 系统" |
| Mixed output fix | "中英混合输出", "Your 影子 bug" |
| Compilation fix | "编译报错了", "fix the build", "link error" |
| ARG-DIFF resolution | "参数顺序不对", "fix mprf_p positional args" |

## Capabilities

1. **T_() guard addition** — wrap bare English strings, remove `Options.language` branches
2. **ZH guard removal** — eliminate `lang_t::ZH` / `crawl.language() == 'zh'` patterns
3. **TextDB structure** — loader/schema changes and explicitly assigned
   delimiter/key repairs under the sole-writer exception
4. **Translation handoff** — identify required `source.txt`/ZH TextDB entries
   for the translator in mixed work
5. **ARG-DIFF resolution** — fix positional parameter mismatches, conj_verb splits
6. **New zh-* file creation** — isolate Chinese strings in dedicated .h/.cc files
7. **Makefile fixes** — add new .o files to correct OBJECTS lists
8. **Compilation verification** — console (`make -j4`) and cross-compile (`TILES=y`)
9. **Descriptor system** — DESC_YOUR/THE/A/PLAIN handling for monster names

## Mandatory Current-Glossary Context

Before dispatching any task that touches `T_()`, `C_()`, `source.txt`, or ZH
TextDB content, run:

```bash
bash .claude/scripts/context_resolve.sh "<task>" --task-type code --files <target-files>
```

Append the complete output to the task prompt. Require the implementer to report
the glossary SHA-256. Do not replace this with terminology copied into the Skill.

## Dispatch Templates

### Template 1: T_() Guard Addition

```
Task(subagent_type="crawl-coder", description="Add T_() guards",
  prompt="Add T_() wrapping to untranslated strings in <file>.
Use the attached context_resolve.sh output and report its glossary SHA-256.
Follow the standard T_() migration pattern:
1. Replace Options.language == lang_t::ZH ? \"中文\" : \"English\" with T_(\"English\")
2. Report every required English key and context to the zh-translator; do not edit translation assets
3. Confirm the translator-owned entries already exist before code verification
4. Run make -j4 to verify compilation
5. Run bash .claude/scripts/verify_zh.sh --profile code for verification")
```

### Template 2: Mixed CN/EN Output Fix

```
Task(subagent_type="crawl-coder", description="Fix mixed CN/EN output",
  prompt="Fix mixed Chinese-English output in <location>.
Root cause investigation pattern:
1. Trace the full string composition path — identify where EN is hardcoded
2. Check if there's a descriptor system (DESC_YOUR, DESC_THE) that should be used
3. Check if T_() is missing on any fragment
4. Verify the fix with make -j4
5. Run verify_zh.sh --profile code verification")
```

### Template 3: ZH Guard Removal

```
Task(subagent_type="crawl-coder", description="Remove ZH guards",
  prompt="Remove all Options.language / crawl.language() guards from <files>.
Pattern: Replace 'condition ? zh_string : en_string' with T_(\"en_string\").
For Lua vaults: replace crawl.language() == 'zh' with crawl.t_(\"English\").
Hand off all new keys and their contexts to zh-translator; do not edit source.txt.
Compile only after the translator-owned entries exist.
Run verify_zh.sh --profile code after completion.")
```

### Template 4: New zh-* System Creation

```
Task(subagent_type="crawl-coder", description="Create zh-* system",
  prompt="Create a new Chinese text system for <feature>.
Design constraints:
- New zh-<name>.h/.cc files isolate all Chinese strings
- EN code path remains completely unchanged
- Use deterministic mapping from existing game state (no save format changes)
- Add new .o to Makefile.obj OBJECTS list (not conditional blocks)
- Document the design in docs/<name>-zh.md
- Verify: make -j4 + make TILES=y -j4 (cross-compile)")
```

### Template 5: ARG-DIFF Fix

```
Task(subagent_type="crawl-coder", description="Fix ARG-DIFF",
  prompt="Fix argument mismatch between EN/ZH format strings in <file>.
Priority order:
1. Positional params (mprf_p + %n$s) — when argument order differs
2. Split keys — when singular/plural verb forms differ (conj_verb removal)
3. C_(ctx, key) — when same English word needs different Chinese translations
4. Drop unused positional args — when CN doesn't need a verb position
Rules: mprf_p (not mprf) for %n$s, never mix %1$s with bare %s,
conj_verb on Chinese is banned. Run verify_zh.sh --profile code to verify.")
```

## Key Patterns (Synthesized from Recent Commits)

### Pattern 1: Descriptor System — Don't Bypass It

Monster name display goes through `apply_description(DESC_TYPE, name)` which
handles language-appropriate prefixes. **Never hardcode English prefixes** like
`"your "` or `"Your "` in string composition.

```cpp
// ❌ Wrong — produces "Your 暗影" mixed output
formatted_string(desc == DESC_THE ? "Your %s" : "your %s", name);

// ✅ Correct — delegates to descriptor system
apply_description(DESC_YOUR, name);  // → "your shadow" (EN) / "你的暗影" (ZH)
```

When adding a new description type, handle it in **all** language paths of
`_apply_adjusted_description()` — including the ZH switch-case.

> **Commits**: `5cc8680afb` (Your 影子), `2eed098cb8` (DESC_YOUR in ZH path)

### Pattern 2: Complete Sentences > Composed Fragments

Composing translations from T_() word fragments produces ungrammatical Chinese.
Prefer complete-sentence T_() keys.

```cpp
// ❌ Wrong — "它曾经噪音卷轴" (ungrammatical: T_("It %s %s.") + T_("was"))
mprf(T_("It %s %s."), T_("was"), item_name);

// ✅ Correct — complete sentences
mprf(T_("It was %s."), item_name);   // 它曾经是噪音卷轴。
mprf(T_("It is %s."), item_name);    // 它是噪音卷轴。
```

> **Commit**: `95d2298a88` (fix 3 playtester issues)

### Pattern 3: C_() for Context Disambiguation

When the same English word needs different Chinese translations in different
game contexts, use `C_("context", "word")`:

```cpp
// "Drain" in different contexts → different Chinese translations
C_("status", "Drain")         // 属性 drain（临时最大HP降低）
C_("ability cost", "Drain")   // 技能消耗：Drain
// T_("Drain") can only have ONE translation — use C_() for disambiguation
```

Common contexts: `"verb"` (cloud/action verbs), `"status"` (status labels),
`"ability cost"` (skill cost labels), `"ability name"` (skill names).

> **Commit**: `e9f0f22ae3` (items 4-5: cloud verbs + STATUS_DRAINED)

### Pattern 4: Persistent Literal Tables via N_()/NC_()

`T_()` and `C_()` return borrowed cache pointers and must never be retained in
static or persistent storage. Mark stable English literals for extraction with
`N_()`/`NC_()`, then translate at the consumption site:

```cpp
// Stable English keys visible to i18n_extract.py
static const char* fail_severity_adjs[] = {
    N_("harmless"), N_("dangerous"), // ...
};

// Runtime access — copy the borrowed result when it crosses the statement.
const string severity = T_(fail_severity_adjs[level]);
mpr(severity);
```

For context-qualified keys, use `NC_("context", "key")` in the table and the
matching `C_("context", value)` at the display sink.

### Pattern 5: Language-Agnostic Vault Data

Replace `crawl.language()` checks in `.des` and `.lua` files with
`crawl.t_()` — the translation DB handles language selection:

```lua
-- ❌ Wrong
if crawl.language() == 'zh' then
    msg = zh_table[dur]
else
    msg = "The air " .. adj .. " of decay."
end

-- ✅ Correct — named placeholders for composed messages
msg = crawl.t_("{prefix} of decay."):gsub("{prefix}", crawl.t_(adj))
```

> **Commits**: `ed04b6d614` (vault .des files, 56 occurrences), `4e13ef6cac` (lm_tmsg)

### Pattern 6: Connector Words Need T_() Too

Template defaults for connector words appear in user-facing text:
```cpp
string comma_separated_line(...,
    const char* andc = T_(" and "),     // was: " and "
    const char* comma = T_(", and "));   // was: ", and "
```
Include `i18n.h` in headers that define T_()-using defaults.

> **Commit**: `38c8cda810` (comma_separated_line)

### Pattern 7: Translation-Aware Logic — Never Inspect Translated Strings

```cpp
// ❌ Wrong — msg.find() breaks when text is in Chinese
if (msg.find("disappears in a puff of smoke") != string::npos)

// ✅ Correct — check game state, not display text
if (mons->type == MONS_SHADOW)
```

> **Commit**: `e9f0f22ae3` (_monster_die_cloud fix)

### Pattern 8: %%%% Separator — Most Fragile Element

Cherry-pick/merge conflicts silently strip `%%%%` separators. A missing `%%%%`
merges two entries → the second key silently returns English.

```bash
# Always verify after merge/cherry-pick
grep -c '^%%%%$' crawl-ref/source/dat/i18n/zh/source.txt
```

Prevention: `sed -i '/^<<<<<<< HEAD$/d; /^=======$/d; /^>>>>>>> .*$/d'` then
visually verify no merged entries.

> **Commit**: `fd71849b36` (missing %%%% before bubbling)

### Pattern 9: Makefile Object Placement

New `.o` files go in the **unconditional** `OBJECTS` list in `Makefile.obj`,
not in `ifndef TILES` / `!W32C` blocks — unless platform-specific. Cross-compile
will miss objects in conditional blocks.

> **Commit**: `51a047ce9a` (zh-scroll-appearance.o)

### Pattern 10: Debug Logging for Complex i18n Bugs

When root cause is unclear, add `[TAG]` debug logging at key resolution points:
```cpp
dprf("[SHADOW] _core_name: raw='%s' zh='%s'", raw.c_str(), zh_name);
dprf("[SHADOW] simple_monster_message: composed='%s'", msg.c_str());
```
Can be removed after verification. Pattern used successfully in monster name
resolution debugging.

> **Commit**: `5cc8680afb`

## Anti-Patterns (Never Do)

| # | Anti-Pattern | Why It's Wrong | Detection |
|---|-------------|----------------|-----------|
| 1 | `.c_str()` on `const char*` return | Redundant, noise | `grep -rn '\.c_str()'` on known const char* funcs |
| 2 | `mprf` with `%n$s` | MinGW vsnprintf no positional support | Link error on cross-compile |
| 3 | Mixed `%1$s` + bare `%s` | POSIX undefined behavior | `scan_i18n.py seq-type-mismatch` |
| 4 | `conj_verb()` on Chinese text | Garbled output like "抓取s" | `scan_i18n.py anti-patterns` |
| 5 | Duplicate source.txt key | First entry wins, second silently ignored | `grep -F` before append |
| 6 | Untranslated inline argument | Mixed CN/EN output | `scan_i18n.py mprf-p` |
| 7 | Protocol key translated | Breaks save/load/serialization | Review `.des` tags, JSON keys |
| 8 | Lua condition string T_()'d | `race == "木乃伊"` always false | `grep -rn 'T_.*==.*"' ` in Lua |
| 9 | `buf.size()` for CJK alignment | Bytes ≠ display width | Use `strwidth()` instead |
| 10 | Persistent raw `T_()`/`C_()` pointer | Dangles after cache clear | `scan_i18n_lifetime.py --require-parser` |
| 11 | Mass duplicate re-add | Appending all enumerated names without diff | Diff against existing keys before writing |

## Source.txt Integrity Protocol (REQUIRED before commit)

Every modification to `dat/i18n/zh/source.txt` MUST pass these checks:

1. **Grep-first**: For each EN key to add, verify it doesn't already exist:
   ```bash
   grep -nF "KEY" crawl-ref/source/dat/i18n/zh/source.txt
   ```

2. **Glossary lookup**: Check `docs/decisions.md` for pre-approved term rulings:
   ```bash
   grep -A3 "Choice:" docs/decisions.md | grep -i "term"
   ```

3. **Post-add verify**: No duplicates or self-conflicts introduced:
   ```bash
   python3 .claude/scripts/scan_i18n.py source-txt-integrity \
       --source-txt crawl-ref/source/dat/i18n/zh/source.txt
   ```

4. **Case discipline**: Copy EN keys verbatim from C++ `T_("...")` literal.

5. **Never blind-add**: When processing enumerated entities (monsters/spells),
   always diff against existing keys — never blindly append all names.

## File Quick Reference

| File | What |
|------|------|
| `crawl-ref/source/dat/i18n/zh/source.txt` | T_() translation database (%%%%-separated) |
| `crawl-ref/source/dat/database/zh/*.txt` | TextDB Chinese overrides |
| `crawl-ref/source/dat/descript/zh/*.txt` | Descriptor database (monsters, spells, egos) |
| `crawl-ref/source/database.cc` | TextDB instances, T_()/C_() implementation |
| `crawl-ref/source/mon-info.cc` | `_apply_adjusted_description()` — DESC_YOUR/THE/A |
| `crawl-ref/source/mon-util.cc` | `do_mon_str_replacements()` — speech tag substitution |
| `crawl-ref/source/Makefile.obj` | Object file list for compilation |

## Agent Invocation

```
# Standard dispatch
Task(subagent_type="crawl-coder", description="<3-5 word summary>",
  prompt="<full task with file paths and requirements>")
```

The agent uses `make -j4` (not -j8), and runs `verify_zh.sh --profile code` before reporting completion.
