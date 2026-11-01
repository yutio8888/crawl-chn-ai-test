# Chinese Translation Architecture

## Lookup Model

Display translation flows through `T_("English")` or contextual
`C_("context", "English")` into the Chinese i18n TextDB. If no Chinese entry
exists, the English key is returned. Call sites should not add language guards
around ordinary display translation.

`T_()` and `C_()` return borrowed pointers whose safety rules are canonical in
`.agents/policies/i18n-safety.md`.

## Translation Paths

### Type I — literal source keys

```cpp
mprf(T_("You hit %s."), mon_name);
```

Literal keys are visible to `i18n_extract.py` and are the preferred path.

### Type II — translated wrappers

Functions such as name/title helpers may translate their underlying English
data internally. Callers must know whether a wrapper returns translated display
text, an English key, `const char *`, or `std::string`; do not guess when adding
`.c_str()` or performing protocol comparisons.

### Type III — runtime variable keys

Data tables may enter `T_(variable)` or `C_(context, variable)`. The literal
extractor cannot see these keys unless they use `N_()`/`NC_()` markers or have a
specialized data-source audit. Run `audit_data_i18n.py` and keep the translation
entry in the same change.

### Type IV — TextDB descriptions

Long descriptions live in `%%%%`-separated databases under
`crawl-ref/source/dat/database/zh/` and
`crawl-ref/source/dat/descript/zh/`. Lookup keys remain English; only display
values are translated. Preserve separators, format placeholders, control characters,
`@keyword@` markers, and embedded template syntax exactly.

### Type V — protocol, internal values, and display snapshots

Serialization identities, Lua/JSON comparison keys, `.des` tags, enum
identifiers, and TextDB lookup keys stay English. Translate only at a display
boundary. Three audited `Note::name` cases are language-locked display snapshots:
`NOTE_MESSAGE` created by `crawl.take_note`, `NOTE_HP_CHANGE` created in
`ouch()` from `scorefile_entry::death_description(DDV_TERSE)`, and `NOTE_DEATH`
from its `DDV_NORMAL` death display (`DDV_VERBOSE` in wizard simulation). They are not
retranslated after a language change. The exceptions do not cover other note
types or fields. Their complete consumer boundary is:

| Stage | Consumer | Contract |
|---|---|---|
| Message producer | `l-crawl.cc::crawl_take_note` | Constructs `NOTE_MESSAGE`; the complete template and string arguments translate together or the whole message remains English |
| Injury producer | `ouch()` | Constructs `NOTE_HP_CHANGE` from the current injury display; known beam/event causes translate at the display gate, unknown names remain verbatim |
| Death producer | `ouch()` | Constructs `NOTE_DEATH` from the normal death display or wizard verbose simulation; the separate literal wizard-revival note is unchanged |
| Persistence | `Note::save` / `Note::load` | Round-trips `Note::name` without interpreting it |
| Display | `Note::describe`, notes UI, chardump/morgue | Emits the stored snapshot |
| Injury selection | `_is_noteworthy`, `is_noteworthy_hp` | Reads numeric HP, maximum HP and turns, never the name |
| Death selection | `_is_noteworthy` | Always accepts `NOTE_DEATH`, without inspecting its name |
| Excluded logic | milestone handling, xlog, Lua comparisons, lookup, gameplay | Does not consume these snapshots' names; `check_milestone` handles only `NOTE_DUNGEON_LEVEL_CHANGE` |

The injury exception documents an existing display snapshot: its source already
localized monster/weapon names and compact injury labels. It permits completing
known beam names without making `scorefile_entry` raw fields or log output
localized. Saved historical snapshots retain their original text.
Death snapshots already used localized descriptions before this audit. Extended
xlog `tmsg`/`vmsg` and death milestones instead use `short_kill_message` /
`long_kill_message`, which scope their generation to English and restore the UI
language afterward; the saved note is not their input.

The protocol-facing Lua bindings `you.race()`,
`you.species()`, `you.genus()`, `you.class()`, and `you.monster()` therefore
produce canonical English identities (using raw or `_en` accessors); callers
may still apply their existing lowercase/pluralisation conventions.

## Context and Extraction

- Use `C_()` when one English key needs a context-specific translation.
- Persistent literal tables later consumed by dynamic translation use
  literal-only `N_()` or `NC_()` when no specialized audit owns the source.
- Never persist the pointer returned by `T_()`/`C_()`; copy it to
  `std::string` if ownership must cross a statement or cache generation.
- Never feed translated text into English morphology such as `conj_verb()`.
  Display verbs pass the original English key and context to
  `actor::verb_for_display()` or `conjugate_verb_for_display()`: ZH returns
  the complete translated form, while English (including a missing ZH entry)
  conjugates only the English key.
- Game C/C++ source contains no Chinese display literals. Chinese display
  text lives in the translation assets; the remaining production CJK
  occurrences are protocol/parse values frozen by
  `.claude/scripts/cjk_inventory.json` and checked by
  `scan_i18n.py cjk-inventory` (see `.claude/scripts/TOOLCHAIN.md`).
- Movement phrases remain English internal values until
  `translated_move_phrase()` applies the correct grammar context at display.

## Data Ownership

Chinese wording and ZH data assets default to the translator role. Source,
loader/schema, and code-side translation boundaries default to the coder role.
The normative single-writer rules are in
`.agents/policies/asset-ownership.md`.

## Terminology and Verification

`docs/glossary.md` is the only terminology source. Generate focused context
with `context_resolve.sh` before work. The `scan_i18n.py anti-patterns` gate
function-qualifies these five Lua identity producers and includes positive and
negative accessor fixtures. Use the matching development profile in
`verify_zh.sh`; detailed scanners and exit codes are documented in
`.claude/scripts/TOOLCHAIN.md`.
