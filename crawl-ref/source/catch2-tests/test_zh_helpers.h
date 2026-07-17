#pragma once

#include <string>
#include <vector>

// ZhIssue represents a single i18n defect of one of the 8 enumerated kinds.
// It carries optional telemetry about where it came from (the English key
// that produced the offending text and a short file/domain tag) so the
// aggregator (.claude/scripts/zh_runtime_check.py) can produce a readable
// report.
struct ZhIssue
{
    enum Kind
    {
        UNTRANSLATED,        // 1: strcmp(T_(key), key) == 0  (and key has ASCII letters)
        MIXED_CN_EN,         // 2: contains CJK + >=3 consecutive Latin chars (not whitelisted)
        FORMAT_BROKEN,       // 3: stray conjugation / pos %s / mprf_p %n$s / arg-count mismatch
        GARBLED_UTF8,        // 4: illegal UTF-8 bytes / U+FFFD / BOM / control chars
        EMPTY_DB,            // 5: getLongDescription(key) empty when key is expected to exist
        WHITESPACE_ANOMALY,  // 6: \r remnant / double space / leading/trailing whitespace
        INVISIBLE_CHAR,      // 7: U+200B / U+FEFF / U+00A0 / PUA / emoji ranges
        PUNCT_STYLE,         // 8: half-width ( ) , . : ; embedded in Chinese text
    };

    Kind        kind;
    std::string source;     // short domain tag, e.g. "monsters.txt"
    std::string key;        // English key that produced `text`, if known
    std::string sample;     // offending text (truncated for logging)
};

// =============================================================================
// JSONL issue protocol v1 helpers.
//
// Emit ZH_ISSUE_JSON: prefixed protocol records to stderr. The protocol
// replaces the old ZH_ISSUE: plain-text format with one-JSON-object-per-line
// transport. See .claude/scripts/data/zh_issue_protocol_v1.schema.json.
// =============================================================================

// JSON-escape a string for use as a JSON string value.
// Escapes LF/CR/TAB/quotes/backslash/U+0000-001F.
std::string json_escape(const std::string& s);

// Hex-encode the raw bytes of `s` (up to 120 bytes) as lowercase even-digit hex.
std::string sample_to_hex(const std::string& s);

// Emit one JSONL issue record to stderr.
void emit_jsonl_issue(const std::string& suite,
                      const std::string& enumerator,
                      int sequence,
                      const ZhIssue& issue);

// Emit one JSONL summary record to stderr.
void emit_jsonl_summary(const std::string& suite,
                        const std::string& enumerator,
                        int issue_count);

// Convenience: emit all issues (in order) then a summary record.
// Call this once per enumerator after all scanning is done.
void emit_issue_protocol(const std::string& suite,
                         const std::string& enumerator,
                         const std::vector<ZhIssue>& issues);

// scan_text applies all 8 scan rules to `text` (the rendered / translated
// string) given the optional English `key` that produced it. `source_tag` is
// an arbitrary short identifier for grouping the report (e.g. the enumerator
// name or TextDB file). Returns a vector of detected ZhIssue entries (may be
// empty).
//
// `key` may be empty for callers that have only the rendered text (Layer 2
// snapshots, hi-score strings); the UNTRANSLATED rule is skipped in that case.
std::vector<ZhIssue> scan_text(const std::string& text,
                               const std::string& key,
                               const std::string& source_tag);

// Convenience wrapper that scans the result of `T_(key)` for a translation
// lookup, eagerly computing T_(key) via the caller and passing text/key to
// scan_text. (T_() itself requires AppHdr.h + i18n.h and is invoked by the
// caller; this helper keeps the i18n macro out of the helpers TU.)
std::vector<ZhIssue> scan_translation(const char* translated,
                                      const std::string& key,
                                      const std::string& source_tag);

// Helper predicates split out so M1 table-driven unit tests (test_zh_translation.cc)
// can target individual rules without running all 8.
bool rule_untranslated   (const std::string& text, const std::string& key);
bool rule_mixed_cn_en    (const std::string& text);
// True for any error returned by TextDB's embedded-Lua evaluator. This is
// checked independently of the mixed-language rule because an evaluator error
// may contain no CJK text at all.
bool rule_embedded_lua_error(const std::string& text);
bool rule_format_broken  (const std::string& text, const std::string& key);
bool rule_garbled_utf8   (const std::string& text);
bool rule_whitespace     (const std::string& text);
bool rule_invisible_char (const std::string& text);
bool rule_punct_style    (const std::string& text);
// EMPTY_DB is structural (caller knows whether empty is allowed); not a
// pure-text rule, so it is intentionally absent from the helpers.

// True iff character looks like a CJK ideograph, used by mixed_cn_en rule.
bool iscjk(char32_t cp);

// True iff character falls inside Unicode emoji / PUA / symbol ranges
// used by rule_invisible_char (covers U+E000–U+F8FF PUA, U+200B ZWS,
// U+FEFF BOM, U+00A0 NBSP and a few common emoji blocks).
bool is_invisible_or_pua(char32_t cp);
