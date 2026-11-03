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
- Keep protocol, lookup, serialization identities, Lua comparison, and TextDB
  key values in English. The following audited Note fields are localized
  display snapshots, not identities:
  - `Note::name` on `NOTE_MESSAGE` created through `crawl.take_note` may use
    the current display language only when the complete template and every
    string parameter translate; otherwise the whole note remains English.
  - `NOTE_HP_CHANGE` created in `ouch()` stores the injury display at creation,
    from `death_description(DDV_TERSE)` or the unseen-source damage template.
    Known beam/event causes may translate through the audited display gate;
    unknown names remain verbatim. The underlying score fields, auxiliary
    cause, and xlog remain canonical English.
  - `NOTE_DEATH` created in `ouch()` from `death_description(DDV_NORMAL)`
    (or `DDV_VERBOSE` in wizard death simulation) stores the death display at
    creation. The separate literal wizard-revival note remains unchanged.
    Logging helpers must generate canonical English independently.
  - `NOTE_MESSAGE.name` created by `_djinn_announce_spells()` and
    `_wanderer_note_equipment()` records the complete game-start display,
    including the player's unchanged name and current item/spell labels.
  - `NOTE_ID_ITEM.name` and `.desc` created by `bless_weapon()` record the
    identified item and the complete blessing description with its old item
    label. Both game-start and blessing notes are always noteworthy by type;
    these payloads are not parsed, compared for identity, or used for milestones.
  `Note::save/load` round-trips these snapshots. Their text consumers are
  `Note::describe`, the notes UI, and chardump/morgue. Injury noteworthiness
  uses numeric HP and turn fields, not the name; death notes are always
  noteworthy. These snapshots are language-locked: changing the UI language
  does not retroactively retranslate their payloads. Do not extend these
  exceptions to other note types or fields without a consumer audit and
  policy change.
- `portal_notes[level_pos]` populated from `TroveMarker:overview_note` is a
  separate audited display snapshot. Translate the complete toll frame and
  its display arguments together, or retain the whole English result. Its
  value consumers are overview UI/chardump display, save/load, copying to a
  new position, and removal. The `level_pos` identity and raw marker toll data
  stay unchanged. The snapshot keeps its creation language until the portal
  is observed again. Do not parse historical values or extend this exception
  to other marker properties without auditing their consumers.
- When a changed value may serve both identity and display, enumerate its
  producer, every intermediate consumer, and its final sinks. Identity and
  lookup paths use the original value or an English accessor (for example,
  `_god_name_en()`); only display sinks localize it. Cover the real lookup and
  fallback path with a targeted test.
- Use `mprf_p` for positional `%n$s` formats and never mix positional and
  sequential placeholders.
- When choosing translated terms, use current relevant `docs/glossary.md`
  context as described in the context Skill. Pure structural work does not
  require terminology lookup. Do not embed canonical terms in prompts.

Configuration checks validate this policy's generated blocks. C++ source
analysis remains the responsibility of `scan_i18n_lifetime.py`,
`scan_varargs_string.py`, and the other code verification gates.
