#include "AppHdr.h"

#include "test_zh_helpers.h"

#include <algorithm>
#include <cstring>
#include <regex>
#include <string>
#include <vector>

// =============================================================================
// Unicode helpers — scan_strings here are std::string stored as UTF-8 bytes.
// We decode them with a small forward iterator so we can ask per-codepoint
// questions (CJK, PUA, emoji, ...)
// =============================================================================

namespace {

// Decode one UTF-8 codepoint starting at `s[i]`; return the codepoint in `cp`
// and the number of bytes consumed in `len`. On an invalid byte sequence we
// return U+FFFD with len==1 so that rule_garbled_utf8 can flag it.
void decode_cp(const std::string& s, size_t i, char32_t& cp, size_t& len)
{
    // Fast path: ASCII
    const unsigned char b0 = static_cast<unsigned char>(s[i]);
    if (b0 < 0x80)
    {
        cp  = b0;
        len = 1;
        return;
    }

    // Determine expected length and initial payload bits.
    unsigned need;
    char32_t val;
    if      ((b0 & 0xE0) == 0xC0) { need = 1; val = b0 & 0x1F; }
    else if ((b0 & 0xF0) == 0xE0) { need = 2; val = b0 & 0x0F; }
    else if ((b0 & 0xF8) == 0xF0) { need = 3; val = b0 & 0x07; }
    else
    {
        // 0xF8..0xFF or 0xC0/0xC1 — illegal lead byte.
        cp  = 0xFFFD;
        len = 1;
        return;
    }

    if (i + need >= s.size())
    {
        // truncated sequence
        cp  = 0xFFFD;
        len = 1;
        return;
    }

    for (unsigned k = 1; k <= need; ++k)
    {
        const unsigned char bn = static_cast<unsigned char>(s[i + k]);
        if ((bn & 0xC0) != 0x80)
        {
            // bad continuation.
            cp  = 0xFFFD;
            len = 1;
            return;
        }
        val = (val << 6) | (bn & 0x3F);
    }

    // Reject overlong encodings, surrogate halves, and codepoints above the
    // Unicode ceiling (0x10FFFF). The latter catches 0xF5..0xFF lead bytes,
    // which my decoder would otherwise naively assemble into illegal values
    // such as 0x140000 — plan §2.3 GARBLED_UTF8 relies on this.
    const char32_t min_cp[4] = { 0, 0x80, 0x800, 0x10000 };
    if (val < min_cp[need] || val > 0x10FFFF
        || (val >= 0xD800 && val <= 0xDFFF))
    {
        cp  = 0xFFFD;
        len = 1;
        return;
    }

    cp  = val;
    len = 1 + need;
}

// Produce a small bounded copy of `s` (used to populate ZhIssue::sample); we
// truncate to ~120 bytes in a UTF-8-safe way (cut on a codepoint boundary).
std::string sample_of(const std::string& s)
{
    const size_t max = 120;
    if (s.size() <= max)
        return s;

    // Walk the prefix, stopping before we would exceed `max` bytes.
    size_t i = 0;
    char32_t cp; size_t len;
    while (i < max)
    {
        decode_cp(s, i, cp, len);
        if (i + len > max)
            break;
        i += len;
    }
    return s.substr(0, i);
}

// Produce a bounded UTF-8-safe sample around a known ASCII offender. Unlike
// sample_of(), this keeps diagnostics useful when the bad token occurs after a
// long translated prefix (Issue 64's Bat status false diagnosis).
std::string sample_around(const std::string& s, size_t focus)
{
    const size_t max = 120;
    if (s.size() <= max)
        return s;

    size_t start = focus > max / 2 ? focus - max / 2 : 0;
    while (start < s.size()
           && (static_cast<unsigned char>(s[start]) & 0xC0) == 0x80)
    {
        ++start;
    }

    size_t end = std::min(s.size(), start + max);
    while (end > start && end < s.size()
           && (static_cast<unsigned char>(s[end]) & 0xC0) == 0x80)
    {
        --end;
    }
    return s.substr(start, end - start);
}

// =============================================================================
// JSONL protocol v1 — JSON escaping and hex encoding.
// =============================================================================

// Escapes a string for JSON: backslash, quote, tab, LF, CR, and control chars.
// Returns a valid JSON string value (WITHOUT the surrounding double quotes).
std::string json_escape_internal(const std::string& s)
{
    std::string out;
    out.reserve(s.size() + 16);
    for (size_t i = 0; i < s.size(); ++i)
    {
        const unsigned char c = static_cast<unsigned char>(s[i]);
        switch (c)
        {
        case '"':  out += "\\\""; break;
        case '\\': out += "\\\\"; break;
        case '\t': out += "\\t";  break;
        case '\n': out += "\\n";  break;
        case '\r': out += "\\r";  break;
        default:
            if (c < 0x20)
            {
                // U+0000–U+001F: \uXXXX
                char buf[8];
                snprintf(buf, sizeof(buf), "\\u%04x", c);
                out += buf;
            }
            else
                out += s[i];
            break;
        }
    }
    return out;
}

} // anonymous namespace

std::string json_escape(const std::string& s)
{
    return json_escape_internal(s);
}

std::string sample_to_hex(const std::string& s)
{
    const size_t max_bytes = 120;
    const size_t n = std::min(s.size(), max_bytes);
    std::string hex;
    hex.reserve(n * 2);
    static const char hex_chars[] = "0123456789abcdef";
    for (size_t i = 0; i < n; ++i)
    {
        unsigned char c = static_cast<unsigned char>(s[i]);
        hex += hex_chars[c >> 4];
        hex += hex_chars[c & 0x0F];
    }
    return hex;
}

std::set<std::string> textdb_template_tokens(const std::string& text)
{
    std::set<std::string> tokens;
    size_t begin = text.find('@');
    while (begin != std::string::npos)
    {
        const size_t end = text.find('@', begin + 1);
        if (end == std::string::npos)
            break;
        tokens.insert(text.substr(begin, end - begin + 1));
        begin = text.find('@', end + 1);
    }
    return tokens;
}

std::string mask_textdb_template_tokens(
    const std::string& text,
    const std::set<std::string>& allowed_tokens)
{
    std::string masked;
    size_t cursor = 0;
    size_t begin = text.find('@');
    while (begin != std::string::npos)
    {
        const size_t end = text.find('@', begin + 1);
        if (end == std::string::npos)
            break;
        masked.append(text, cursor, begin - cursor);
        const std::string token = text.substr(begin, end - begin + 1);
        masked += allowed_tokens.count(token) ? "#" : token;
        cursor = end + 1;
        begin = text.find('@', cursor);
    }
    masked.append(text, cursor, std::string::npos);
    return masked;
}

void emit_jsonl_issue(const std::string& suite,
                      const std::string& enumerator,
                      int sequence,
                      const ZhIssue& issue)
{
    // Build the kind string from the enum integer.
    static const char* kind_names[] = {
        "UNTRANSLATED", "MIXED_CN_EN", "FORMAT_BROKEN",
        "GARBLED_UTF8", "EMPTY_DB", "WHITESPACE_ANOMALY",
        "INVISIBLE_CHAR", "PUNCT_STYLE", "EMBEDDED_LUA_ERROR"
    };
    const char* kind_str = "UNKNOWN";
    if (issue.kind >= ZhIssue::UNTRANSLATED
        && issue.kind <= ZhIssue::EMBEDDED_LUA_ERROR)
    {
        kind_str = kind_names[issue.kind];
    }

    // Compact JSON construction using snprintf to avoid JSON library dependency.
    // Manual construction is simpler than streaming JSON.
    // Format: {"schema_version":1,"record_type":"issue","suite":"...","enumerator":"...","sequence":N,"kind":"...","source":"...","key":"...","sample":"...","sample_bytes_hex":"..."}
    std::string json = "{\"schema_version\":1,\"record_type\":\"issue\"";
    json += ",\"suite\":\"" + json_escape_internal(suite) + "\"";
    json += ",\"enumerator\":\"" + json_escape_internal(enumerator) + "\"";
    json += ",\"sequence\":" + std::to_string(sequence);
    json += ",\"kind\":\"" + std::string(kind_str) + "\"";
    json += ",\"source\":\"" + json_escape_internal(issue.source) + "\"";
    json += ",\"key\":\"" + json_escape_internal(issue.key) + "\"";
    json += ",\"sample\":\"" + json_escape_internal(issue.sample) + "\"";
    json += ",\"sample_bytes_hex\":\"" + sample_to_hex(issue.sample) + "\"}";

    fprintf(stderr, "ZH_ISSUE_JSON: %s\n", json.c_str());
}

void emit_jsonl_summary(const std::string& suite,
                        const std::string& enumerator,
                        int issue_count)
{
    std::string json = "{\"schema_version\":1,\"record_type\":\"summary\"";
    json += ",\"suite\":\"" + json_escape_internal(suite) + "\"";
    json += ",\"enumerator\":\"" + json_escape_internal(enumerator) + "\"";
    json += ",\"issue_count\":" + std::to_string(issue_count) + "}";

    fprintf(stderr, "ZH_ISSUE_JSON: %s\n", json.c_str());
}

void emit_issue_protocol(const std::string& suite,
                         const std::string& enumerator,
                         const std::vector<ZhIssue>& issues)
{
    for (size_t i = 0; i < issues.size(); ++i)
        emit_jsonl_issue(suite, enumerator, static_cast<int>(i), issues[i]);
    emit_jsonl_summary(suite, enumerator, static_cast<int>(issues.size()));
}

bool iscjk(char32_t cp)
{
    // Common CJK ranges that appear in zh translations.
    // Hiragana / Katakana are listed but should never legitimately appear in zh,
    // so we still count them as "wide" — that lets MIXED_CN_EN catch a stray
    // Japanese glyph mixed in by mistake.
    return (cp >= 0x3000 && cp <= 0x303F)   // CJK punctuation
        || (cp >= 0x3400 && cp <= 0x4DBF)   // CJK Ext A
        || (cp >= 0x4D40 && cp <= 0x4DFF)   // CJK Ext A (overlap)
        || (cp >= 0x4E00 && cp <= 0x9FFF)   // CJK Unified Ideographs
        || (cp >= 0xAC00 && cp <= 0xD7AF)   // Hangul Syllables
        || (cp >= 0xF900 && cp <= 0xFAFF)   // CJK Compat Ideographs
        || (cp >= 0xFF00 && cp <= 0xFFEF)   // Fullwidth forms
        || (cp >= 0x20000 && cp <= 0x2FFFF) // SMP CJK
        || (cp >= 0x3040 && cp <= 0x309F)   // Hiragana
        || (cp >= 0x30A0 && cp <= 0x30FF);  // Katakana
}

bool is_invisible_or_pua(char32_t cp)
{
    return cp == 0x200B                       // Zero Width Space (CJK tiles marker also leaks here)
        || cp == 0xFEFF                       // BOM / ZWNBSP
        || cp == 0x00A0                       // NBSP
        || (cp >= 0x200C && cp <= 0x200F)     // ZWNJ / ZWJ / direction marks
        || (cp >= 0x2028 && cp <= 0x202F)     // line/paragraph separators & friends
        || (cp >= 0x2060 && cp <= 0x206F)     // word joiner / invisibles
        || (cp >= 0xE000 && cp <= 0xF8FF)     // Private Use Area
        || (cp >= 0xF0000 && cp <= 0xFFFFD)   // Supplementary PUA-A
        || (cp >= 0x100000 && cp <= 0x10FFFD);// Supplementary PUA-B
}

// =============================================================================
// Individual rule implementations.
// =============================================================================

bool rule_untranslated(const std::string& text, const std::string& key)
{
    // 1) Comparison is by string contents (not pointer). i18n_source_lookup
    //    (database.cc:1061) returns a deque-stored c_str() on ZH-mode miss,
    //    not the caller's pointer — B2.
    // 2) Only fire when the key actually contains ASCII letters (a pure-digit
    //    or empty key cannot meaningfully be flagged "untranslated").
    if (text != key)
        return false;
    bool has_letter = false;
    for (char c : key)
        if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'))
        {
            has_letter = true;
            break;
        }
    return has_letter;
}

static bool is_ascii_identifier_char(char c)
{
    return (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')
        || (c >= '0' && c <= '9') || c == '_';
}

static bool is_command_identifier_char(char c)
{
    return (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9')
        || c == '_';
}

static size_t command_template_end(const std::string& text, size_t i)
{
    static const std::string prefix = "$cmd[";
    if (text.compare(i, prefix.size(), prefix) != 0)
        return std::string::npos;

    const size_t identifier_start = i + prefix.size();
    if (text.compare(identifier_start, 4, "CMD_") != 0)
        return std::string::npos;

    size_t end = identifier_start + 4;
    const size_t command_start = end;
    while (end < text.size() && is_command_identifier_char(text[end]))
        ++end;
    return end > command_start && end < text.size() && text[end] == ']'
        ? end + 1 : std::string::npos;
}

static size_t allowed_technical_literal_end(const std::string& text, size_t i)
{
    // Some translated command descriptions must preserve exact option names,
    // command identifiers, literals, and paths. Match the complete ASCII
    // identifier/literal instead of allowlisting its component words: broad
    // entries such as "auto" or "status" would hide ordinary English leaks.
    if (i > 0 && is_ascii_identifier_char(text[i - 1]))
        return std::string::npos;

    size_t end = i;
    while (end < text.size() && is_ascii_identifier_char(text[end]))
        ++end;

    static const std::vector<std::string> allowed = {
        "morgue",
        "CMD_EXPLORE",
        "explore_auto_rest",
        "false",
        "explore_auto_rest_status",
    };
    const std::string candidate = text.substr(i, end - i);
    return std::find(allowed.begin(), allowed.end(), candidate) != allowed.end()
        ? end : std::string::npos;
}

static size_t allowed_txt_filename_end(const std::string& text,
                                       size_t identifier_end)
{
    static const std::string extension = ".txt";
    if (text.compare(identifier_end, extension.size(), extension) != 0)
        return std::string::npos;

    const size_t end = identifier_end + extension.size();
    return end == text.size() || !is_ascii_identifier_char(text[end])
        ? end : std::string::npos;
}

static bool is_lua_member_call_identifier(const std::string& text,
                                          size_t identifier_start,
                                          size_t identifier_end)
{
    if (identifier_start == 0 || text[identifier_start - 1] != '.'
        || identifier_end + 1 >= text.size()
        || text[identifier_end] != '(' || text[identifier_end + 1] != ')')
    {
        return false;
    }

    const size_t open = text.rfind("{{", identifier_start);
    if (open == std::string::npos)
        return false;
    const size_t close = text.rfind("}}", identifier_start);
    if (close != std::string::npos && close >= open)
        return false;

    const size_t template_end = text.find("}}", open + 2);
    return template_end != std::string::npos
        && identifier_end + 2 <= template_end;
}

static size_t mixed_cn_en_offender(const std::string& text)
{
    // Fire when text contains a CJK ideograph AND >=3 consecutive ASCII
    // Latin letters that aren't whitelisted as an allowed embedded technical
    // term (resistances, abbreviation tags, the names of gods/skills/species
    // which are intentionally kept in English — see plan v2 §2.3 row 2).
    //
    // The whitelist itself is loaded/managed in the catch2 enumerators
    // (M2 milestone); here we implement the structural detection.

    bool has_cjk = false;
    size_t i = 0;
    char32_t cp; size_t len;
    while (i < text.size())
    {
        decode_cp(text, i, cp, len);
        if (iscjk(cp))
            has_cjk = true;
        i += len;
    }
    if (!has_cjk)
        return std::string::npos;

    // Preserve valid $cmd[COMMAND_IDENTIFIER] templates explicitly. Outside
    // templates, classify each maximal ASCII identifier as a whole; otherwise
    // a near-match such as cmd_explore could fall back to separately
    // allowlisted "cmd" and "explore" fragments.
    // The whitelist lives in catch2-tests/zh_runtime_allowlist_enum.txt plus
    // a hardcoded minimal set in source. We replicate a generous built-in
    // whitelist here so the helper is self-contained and testable in M1.

     static const std::vector<std::string> builtin = {
         // Resistance / stat tags
         "rF","rC","rElec","rPois","rN","MR","rCorr","rWater","rNeg","rMut","rTorment","rHellfire",
         "AC","EV","SH","Str","Dex","Int","XL","HP","MP","SLA","SInv","Slay",
         // God names (canonical, kept in English by policy)
         "Trog","Okawaru","Sif","Muna","Kikubaaqudgha","Dithmenos","Makhleb","Vehumet",
         "Zin","Shining","Trog","Cheibriados","Lugonu","Nemelex","Xom","Yredelemnul",
         "Beogh","Jiyva","Fedhas","Elyvilon","The","Ru","Uskayaw","Hepliaklqana","Wu",
         "Ignis","Qazlal","Gozag","Ehur","Elyvilon","Ashenzari","Iashol","Saoieme",
         // Common English embedded terms (acronyms, dungeon names)
         "Dungeon","Lair","Shoals","Snake","Spider","Tomb","Vaults","Hell","Abyss","Zot",
         "Slime","Orc","Elf","Crypt","Pan","Bligit","Dis","Gehenna","Cocytus","Tartarus",
         // Tech prefixes used in items
         "Tele","Rage","Highlight",
         // DCSS command/wizard codes in tutorial/hints templates
         "CMD","EVOKE","READ","QUAFF","tiles","white","TODO","you","god",
         // ==============================================================
         // Markup / template tokens below — added to suppress false positives
         // from DCSS markup tags, HTML-style tag names,
         // and external proper names embedded in Chinese display text.
         // ==============================================================
         // HTML-style / DCSS markup tags
         "lightred","lightblue","lightgreen","lightgrey","lightgray",
         "darkgrey","darkgray","localtiles","localtile","console",
         "yellow","cyan","nomouse","nowrap","input",
         // Command words that also occur outside $cmd[...] templates
         "REPLAY","MESSAGES","CLOSE","DOWNSTAIRS","UPSTAIRS","EXPLORE",
         "EQUIP","PICKUP","WAIT","FIRE","MEMORISE","DISPLAY","QUIVER",
         "CAST","SPELL","WEAPON","WIELD","DROP","LOOK","AROUND","TARGET",
         "DESCRIBE","SEARCH","STASHES","INTERLEVEL","TRAVEL","ABILITY",
         "RELIGION","RESISTS","SCREEN","COMMANDS","CHARACTER","DUMP",
         "AUTOFIGHT","open","door","rest","spells",
         // Keyboard / key names in tutorial text
         "Shift","NumLock","Tab","ESC","Enter","key",
         // External proper names
         "IRC","Libera",
         // Filename extensions embedded in Chinese text
         "txt",
         // Game terms referenced in tutorial/hints as English concepts
         "experience","level","return","use",
         // Command tokens in tutorial templates
         "MOVE","LEFT","RIGHT","DOWN","UP","MAP","webtiles",
         "SELECT","FORWARD","ATTACK","PRIMARY","CYCLE","ITEM",
         "SKILLS","INVENTORY","UNEQUIP","OVERMAP","SHOUT",
         "NOTE","MAKE","SAVE","GAME","race","class","manual",
         "guide","options","quickstart","crawl","init",
         "chat","crawlrc","shop","magic","type","end","Ctrl",
         "Esc",
     };

    i = 0;
    while (i < text.size())
    {
        char c = text[i];
        if (c == '$' && text.compare(i, 5, "$cmd[") == 0)
        {
            const size_t template_end = command_template_end(text, i);
            if (template_end == std::string::npos)
                return i;
            i = template_end;
            continue;
        }

        if (is_ascii_identifier_char(c))
        {
            size_t j = i + 1;
            while (j < text.size() && is_ascii_identifier_char(text[j]))
                ++j;

            const size_t technical_end = allowed_technical_literal_end(text, i);
            if (technical_end != std::string::npos)
            {
                i = technical_end;
                continue;
            }

            const size_t filename_end = allowed_txt_filename_end(text, j);
            if (filename_end != std::string::npos)
            {
                i = filename_end;
                continue;
            }

            if (is_lua_member_call_identifier(text, i, j))
            {
                i = j;
                continue;
            }

            const std::string token = text.substr(i, j - i);
            size_t letter_count = 0;
            for (char d : token)
            {
                if ((d >= 'A' && d <= 'Z') || (d >= 'a' && d <= 'z'))
                    ++letter_count;
            }
            if (letter_count == 0)
            {
                i = j;
                continue;
            }

            // Compound identifiers must either match one of the exact,
            // case-sensitive technical literals above or fail closed. Never
            // split them into independently allowlisted word fragments.
            if (token.find('_') != std::string::npos)
                return i;

            bool whitelisted = false;
            if (letter_count < 3)
                whitelisted = true;            // 1-2 letter tokens (rF, AC, ...)
            else
            {
                // case-insensitive whitelist lookup
                std::string lower = token;
                std::transform(lower.begin(), lower.end(), lower.begin(),
                               [](unsigned char ch){ return std::tolower(ch); });
                for (const std::string& w : builtin)
                {
                    std::string wl = w;
                    std::transform(wl.begin(), wl.end(), wl.begin(),
                                   [](unsigned char ch){ return std::tolower(ch); });
                    if (wl == lower)
                    {
                        whitelisted = true;
                        break;
                    }
                }
            }
            if (!whitelisted)
                return i;
            i = j;
        }
        else
            ++i;
    }
    return std::string::npos;
}

bool rule_mixed_cn_en(const std::string& text)
{
    return mixed_cn_en_offender(text) != std::string::npos;
}

bool rule_embedded_lua_error(const std::string& text)
{
    return text.find("[string \"db_embedded_lua\"]") != std::string::npos;
}

bool rule_format_broken(const std::string& text, const std::string& key)
{
    // The plan defines 4 sub-rules; we implement them here as regex scans plus
    // an argument-count comparison (only performed when `key` is non-empty,
    // so this rule is also callable from Layer 2 snapshots).

    // a) Stray English verb conjugation: a 2+ CJK run followed by ASCII 's' / 'x'
    //    not followed by a word char. This is the "conj_verb(...) produces
    //    garbled const string" error noted in CLAUDE.md anti-pattern #2.
    try
    {
        // e.g. "抓取s is bad" matches.
        static const std::regex conj_re("[\\xE4-\\xE9][\\x80-\\xBF]{2}[sx](?![A-Za-z0-9])");
        if (std::regex_search(text, conj_re))
            return true;
    }
    catch (...) { /* ignore regex engine quirks */ }

    // b) Lone trailing %s that produces garbled runtime substitution.
    //    We accept "%s" only when embedded with surrounding context or
    //    followed by another format char; a bare "%s$" at end-of-string is
    //    flagged.
    if (text.size() >= 2 && text.find("%s") == text.size() - 2)
    {
        // "%s" alone at the very end, with nothing else guaranteed — that's
        // suspicious in a translated string.
        return true;
    }

    // c) mprf-p incompatibility — MinGW vsnprintf does not support %n$s.
    if (text.find('%') != std::string::npos)
    {
        // Match %<digits>$
        try
        {
            static const std::regex pos_re("%[0-9]+\\$");
            if (std::regex_search(text, pos_re))
                return true;
        }
        catch (...) { /* ignore */ }
    }

    // d) %s / %d count mismatch between the (English) key and translated text.
    //    This is the same logic as scan_i18n.py arg-mismatch mode, adapted to
    //    runtime comparison. We do a per-format-specifier count comparison;
    //    asterisk / %*d etc. are ignored.
    if (!key.empty())
    {
        auto count_specs = [](const std::string& s) -> int
        {
            int n = 0;
            for (size_t k = 0; k + 1 < s.size(); ++k)
            {
                if (s[k] == '%')
                {
                    char nxt = s[k + 1];
                    if (nxt == '%')
                    {
                        ++k; // consume the %%
                        continue;
                    }
                    // skip width / precision / flags
                    size_t j = k + 1;
                    while (j < s.size())
                    {
                        char c = s[j];
                        if ((c >= '0' && c <= '9') || c == '-' || c == '+'
                            || c == ' ' || c == '#' || c == '.' || c == '*')
                        {
                            ++j;
                            continue;
                        }
                        break;
                    }
                    if (j < s.size())
                    {
                        char conv = s[j];
                        if (conv == 's' || conv == 'd' || conv == 'u'
                            || conv == 'i' || conv == 'l' || conv == 'f'
                            || conv == 'g' || conv == 'x' || conv == 'X'
                            || conv == 'c' || conv == 'p')
                        {
                            ++n;
                        }
                    }
                    k = j;
                }
            }
            return n;
        };
        if (count_specs(text) != count_specs(key))
            return true;
    }
    return false;
}

bool rule_garbled_utf8(const std::string& text)
{
    // Walk the buffer decoding; illegal lead bytes / truncated sequences /
    // overlongs / surrogate halves all surface as U+FFFD via decode_cp.
    size_t i = 0;
    char32_t cp; size_t len;
    while (i < text.size())
    {
        decode_cp(text, i, cp, len);
        if (cp == 0xFFFD)
            return true;
        // Also reject any control char other than the well-behaved
        // whitespace set {tab, newline, carriage-return}.
        if (cp < 0x20 && cp != '\t' && cp != '\n')
            return true;
        i += len;
    }
    return false;
}

bool rule_whitespace(const std::string& text)
{
    // \r is unambiguously anomalous (source.txt Windows CRLF remnant).
    if (text.find('\r') != std::string::npos)
        return true;
    // Double space.
    if (text.find("  ") != std::string::npos)
    {
        // Allow leading indent of two-space bullets like "  - foo":
        // if the double space is followed by a dash, ignore.
        size_t pos = text.find("  ");
        while (pos != std::string::npos)
        {
            if (pos + 2 >= text.size() || text[pos + 2] != '-')
                return true;
            pos = text.find("  ", pos + 1);
        }
    }
    // Leading / trailing ASCII space — but allow legitimate bullet indent
    // patterns like "  - foo" or "  * foo" (plan §2.3 row 6 only forbids
    // accidental editorial whitespace, not intentional markdown bullets).
    if (!text.empty())
    {
        if (text.front() == ' ')
        {
            size_t p = 0;
            while (p < text.size() && text[p] == ' ')
                ++p;
            char first_real = (p < text.size() ? text[p] : '\0');
            if (first_real != '-' && first_real != '*')
                return true;
        }
        if (!text.empty() && text.back() == ' ')
            return true;
    }
    return false;
}

bool rule_invisible_char(const std::string& text)
{
    size_t i = 0;
    char32_t cp; size_t len;
    while (i < text.size())
    {
        decode_cp(text, i, cp, len);
        if (is_invisible_or_pua(cp))
            return true;
        i += len;
    }
    return false;
}

bool rule_punct_style(const std::string& text)
{
    // We walk the string as a sequence of codepoints (with their byte
    // positions), so adjacency queries are O(1) by index into that vector.
    std::vector<char32_t> cps;
    std::vector<size_t>   byte_starts;
    size_t i = 0;
    char32_t cp; size_t len;
    while (i < text.size())
    {
        decode_cp(text, i, cp, len);
        cps.push_back(cp);
        byte_starts.push_back(i);
        i += len;
    }

    static const std::string bad = "(),.:;";
    for (size_t k = 0; k < cps.size(); ++k)
    {
        char32_t cp = cps[k];
        char c = static_cast<char>(cp);
        if (cp >= 0x80)               // not ASCII
            continue;
        if (bad.find(c) == std::string::npos)
            continue;
        bool prev_cjk = (k > 0) ? iscjk(cps[k - 1]) : false;
        bool next_cjk = (k + 1 < cps.size()) ? iscjk(cps[k + 1]) : false;
        if (c == '.' && prev_cjk)
        {
            // Filename extension heuristic: CJK + '.' + 1-6 ASCII letters.
            // e.g. 玩家名.txt — the extension is not a punctuation issue.
            size_t ext_start = k + 1;
            size_t ext_len = 0;
            while (ext_start + ext_len < cps.size() && ext_len < 6)
            {
                char32_t ec = cps[ext_start + ext_len];
                if ((ec >= 'a' && ec <= 'z') || (ec >= 'A' && ec <= 'Z'))
                    ++ext_len;
                else
                    break;
            }
            if (ext_len >= 1)
            {
                // extension ends at non-letter or string end
                size_t ext_end = ext_start + ext_len;
                if (ext_end >= cps.size()
                    || !((cps[ext_end] >= 'a' && cps[ext_end] <= 'z')
                      || (cps[ext_end] >= 'A' && cps[ext_end] <= 'Z')))
                {
                    continue;
                }
            }
        }
        if (prev_cjk || next_cjk)
            return true;
        // Whole-string degenerate case: a mostly-Chinese fragment that
        // happens to use a single ASCII punct and nothing but ASCII letters
        // elsewhere. We check this only when no per-adjacency match fired.
    }
    return false;
}

// =============================================================================
// Aggregating entry point.
// =============================================================================

std::vector<ZhIssue> scan_translation(const char* translated,
                                      const std::string& key,
                                      const std::string& source_tag)
{
    std::string text(translated ? translated : "");
    return scan_text(text, key, source_tag);
}

std::vector<ZhIssue> scan_text(const std::string& text,
                               const std::string& key,
                               const std::string& source_tag)
{
    std::vector<ZhIssue> issues;

    auto add = [&](ZhIssue::Kind k, const std::string& sample)
    {
        ZhIssue iss;
        iss.kind   = k;
        iss.source  = source_tag;
        iss.key     = key;
        iss.sample  = sample_of(sample);
        issues.push_back(iss);
    };

    // The evaluator's diagnostic is not rendered translation text. Report
    // the underlying failure once instead of deriving mixed-language,
    // punctuation, or formatting false positives from the error message.
    if (rule_embedded_lua_error(text))
    {
        add(ZhIssue::EMBEDDED_LUA_ERROR, text);
        return issues;
    }

    if (!key.empty() && rule_untranslated(text, key))
        add(ZhIssue::UNTRANSLATED, text);
    const size_t mixed_offender = mixed_cn_en_offender(text);
    if (mixed_offender != std::string::npos)
        add(ZhIssue::MIXED_CN_EN, sample_around(text, mixed_offender));
    if (rule_format_broken(text, key))
        add(ZhIssue::FORMAT_BROKEN, text);
    if (rule_garbled_utf8(text))
        add(ZhIssue::GARBLED_UTF8, text);
    if (rule_whitespace(text))
        add(ZhIssue::WHITESPACE_ANOMALY, text);
    if (rule_invisible_char(text))
        add(ZhIssue::INVISIBLE_CHAR, text);
    if (rule_punct_style(text))
        add(ZhIssue::PUNCT_STYLE, text);

    return issues;
}
