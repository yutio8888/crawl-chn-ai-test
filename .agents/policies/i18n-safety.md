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
  key values in English. A serialized display snapshot may use the current
  display language only when every consumer is display-only and no gameplay,
  protocol, lookup, or comparison path reuses it. Such snapshots are
  language-locked: changing the UI language does not retroactively retranslate
  existing records.
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
