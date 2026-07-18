# translation-integrity-v1

This policy applies to writers and pipelines that create or update Chinese
translation assets.

- Preserve every source clause, condition, cause, exception, number,
  restriction, and gameplay consequence. Sentence-length, tone, and fluency
  guidance may change expression but never remove a proposition.
- Never silently compress content to fit a UI. Use a context-specific
  translation key or fix the layout when the complete meaning does not fit.
- Before adding an entry, search the complete target asset for the exact,
  case-sensitive literal key. Update an owned existing entry deliberately;
  never blindly append an enumerated batch or rely on later duplicate-key
  override behaviour.
- Treat `\n`, `\t`, `\r`, `%%%%`, positional and sequential format
  placeholders, markup tags, `@keyword@`, sentinels, and data-language syntax as
  immutable tokens. Preserve each token byte-for-byte and preserve its required
  multiplicity; reorder only when the format's documented positional grammar
  permits it.
- Run the translation profile after writing assets. Preserve its raw report and
  explain every relevant failure or warning instead of reporting only a
  pass/fail summary.

Layout preferences and style targets are subordinate to semantic and structural
integrity.
