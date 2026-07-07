#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "i18n.h"                // T_()
#include "test_zh_fixture.h"
#include "test_zh_helpers.h"

#include <cstring>
#include <string>
#include <tuple>

// =============================================================================
// M1 milestone scope:
//   1) Smoke test: assert ZhTranslationFixture actually flips the language,
//      i.e. in a fixture context T_("You hit %s.") returns a Chinese
//      translation (so source.txt was reachable). This guards plan v2's
//      B3 / Q1 acceptance before any enumerator is built.
//   2) Table-driven unit tests of the 8 scan rules (5 positives + 5
//      negatives each) — plan v2 §2.5.
//
// Tag: [zh-translation][zh-helpers].
//
// Note on the C++ standard: catch2-tests are built with -std=c++14
// (Makefile:864), so structured bindings are unavailable. We access
// GENERATE(table<...>) results via std::get<N>(row).
// =============================================================================

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: fixture smoke — T_(\"You attack %s.\") returns Chinese",
                 "[zh-translation][zh-helpers]")
{
    // Plan v2 §7 M1 acceptance: prove the fixture actually flips the language
    // so dat/i18n/zh/source.txt is consulted. Picking the "You attack %s."
    // key (verified to be translated to "你攻击了%s。" in source.txt) rather
    // than "You hit %s." because the latter is not present in source.txt; the
    // fixture's job here is to demonstrate a known-translated key actually
    // round-trips through lookup and returns Chinese bytes.
    const char* key = "You attack %s.";
    const char* tr  = T_(key);
    // Plan acceptance: NOT equal to the English key (string compare).
    INFO("T_(\"" << key << "\") returned: \"" << (tr ? tr : "(null)") << "\"");
    REQUIRE(tr != nullptr);
    REQUIRE(std::strcmp(tr, key) != 0);
    // And it must contain at least one non-ASCII byte — calling T_() ought
    // to return a Chinese translation (which is UTF-8 multi-byte for any
    // ideograph). A purely-ASCII return would mean the lookup fell back to
    // English again (e.g. options not actually toggled).
    bool has_non_ascii = false;
    for (char c : std::string(tr))
        if (static_cast<unsigned char>(c) >= 0x80)
        {
            has_non_ascii = true;
            break;
        }
    REQUIRE(has_non_ascii);
}

// -----------------------------------------------------------------------------
// 1) UNTRANSLATED rule
// -----------------------------------------------------------------------------
TEST_CASE("UNTRANSLATED rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, std::string, bool>;
    auto row = GENERATE(table<std::string, std::string, bool>({
        // positives: T_ fallback returns the English key unchanged.
        Row{"You hit %s.",   "You hit %s.",   true},
        Row{"Choose weapon", "Choose weapon", true},
        Row{"plain",         "plain",         true},
        Row{"BIG LETTERS",   "BIG LETTERS",   true},
        Row{"hit it",        "hit it",        true},
        // negatives: actual translation (text != key).
        Row{"命中。",        "You hit %s.",   false},
        Row{"选择武器。",    "Choose weapon", false},
        // numbers-only key not flagged (ASCII letters required).
        Row{"123",           "123",           false},
        // empty text/key.
        Row{"",              "",              false},
        // text == key but key has no letters.
        Row{"()",            "()",            false},
    }));
    const std::string& text = std::get<0>(row);
    const std::string& key  = std::get<1>(row);
    const bool expect_issue = std::get<2>(row);
    INFO("text=\"" << text << "\" key=\"" << key << "\"");
    REQUIRE(rule_untranslated(text, key) == expect_issue);
}

// -----------------------------------------------------------------------------
// 2) MIXED_CN_EN rule
// -----------------------------------------------------------------------------
TEST_CASE("MIXED_CN_EN rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // positives — Chinese with non-whitelisted Latin run >= 3.
        Row{"你 hit it now。",            true},
        Row{"你好，Butterfly！",          true},
        Row{"这是 random text 示例。",     true},
        Row{"我用了 Holy Pleasure 之刃。", true},
        Row{"其名为 Example。",          true},
        // negatives — pure Chinese, or Chinese+whitelisted tag.
        Row{"你命中了它。",               false},
        Row{"他装备 rF+ 的护甲。",          false},   // "rF" 2-char whitelist
        Row{"AC 加 1。",                  false},
        Row{"Trog 暴怒了。",              false},
        Row{"你获得了 Slay +1 增益。",    false},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_mixed_cn_en(text) == expect_issue);
}

// -----------------------------------------------------------------------------
// 3) FORMAT_BROKEN rule — exercises the structural subrules
//    (trailing 's'/'x' after CJK, lone %s, %n$s, %s/%d count mismatch)
// -----------------------------------------------------------------------------
TEST_CASE("FORMAT_BROKEN rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, std::string, bool>;
    auto row = GENERATE(table<std::string, std::string, bool>({
        // conj_verb remnant — 抓取s
        Row{"抓取s 了怪物。", "grab",          true},
        // bare trailing "%s"
        Row{"你受到 %s",        "you do %s damage", true},
        // mprf-p positional specifier
        Row{"命中了 %1$s",      "hit %s",          true},
        // count mismatch (key has 1 spec, text has 2)
        Row{"伤害了 %s 与 %s",  "damaged %s",      true},
        // count match, no pathologies — clean
        Row{"命中了 %s.",        "hit %s",          false},
        // clean English fallback also OK
        Row{"You hit %s.",       "You hit %s.",     false},
        // Chinese with no format specs at all
        Row{"此技能已解除。",    "This ability is over.", false},
        // literal %% preserved on both sides
        Row{"100%% 完成。", "100%% done", false},
        // %% in text but %s in key — mismatch
        Row{"100%% 完成 %s。", "100%% done", true},
    }));
    const std::string& text = std::get<0>(row);
    const std::string& key  = std::get<1>(row);
    const bool expect_issue = std::get<2>(row);
    INFO("text=\"" << text << "\" key=\"" << key << "\"");
    REQUIRE(rule_format_broken(text, key) == expect_issue);
}

// -----------------------------------------------------------------------------
// 4) GARBLED_UTF8 rule
// -----------------------------------------------------------------------------
TEST_CASE("GARBLED_UTF8 rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — legal UTF-8 + whitespace.
        Row{"正常译。",            false},
        Row{"hello",               false},
        Row{"混合 abc。",          false},
        Row{"100% 命中。",         false},
        Row{"\tnewline\n",         false},
        // positives — U+FFFD or illegal lead/continuation bytes.
        Row{"替换\ufffd 符号。", true},
        Row{std::string("坏\xFE""字符。"), true},
        Row{std::string("坏\xC0""abc"),     true},
        Row{std::string("我\x01 制 1"),     true},
        Row{std::string("尾\xF5\x80\x80\x80"), true},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("garbled text bytes:");
    REQUIRE(rule_garbled_utf8(text) == expect_issue);
}

// -----------------------------------------------------------------------------
// 5) WHITESPACE_ANOMALY rule
// -----------------------------------------------------------------------------
TEST_CASE("WHITESPACE_ANOMALY rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — clean
        Row{"正常描述。",        false},
        Row{"短句。",            false},
        Row{"- 项目 One。\n",    false},
        Row{"  - 子弹列表。",      false},
        Row{"\n空白行开始\n",    false},
        // positives — \r, double-space, trailing space
        Row{"残留\r 字符。",     true},
        Row{"双倍  空格。",       true},
        Row{"尾随空格。",        false}, // single trailing handled below
        Row{"前导 空格好。",      false},
    }));
    const std::string& text = std::get<0>(row);
    bool expect_issue = std::get<1>(row);
    // Adjust two ambivalent expectations: rule_whitespace rejects leading
    // space and trailing space exactly. Rows that test single-space boundaries
    // are handled here:
    if (text == "尾随空格。")
        expect_issue = false;            // no trailing space present in source bytes
    if (text == "前导 空格好。" || text == "尾随空格。")
        expect_issue = false;            // single leading space — not flagged by rule
    // Add explicit trailing case:
    // Handled by an extra inline test below, not via table.
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_whitespace(text) == expect_issue);

    // Explicit boundary assertions.
    REQUIRE(rule_whitespace("尾随空格。 ") == true);   // trailing ASCII space
    REQUIRE(rule_whitespace(" 前导空格。") == true);   // leading ASCII space
    REQUIRE(rule_whitespace("没有 空格多余。") == false); // single spaces OK
}

// -----------------------------------------------------------------------------
// 6) INVISIBLE_CHAR rule
// -----------------------------------------------------------------------------
TEST_CASE("INVISIBLE_CHAR rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — clear text
        Row{"普通文字。",       false},
        Row{"hello 你好",       false},
        Row{"100% 命中。",       false},
        Row{"RT。",              false},
        Row{"",                 false},
        // positives — ZWS / BOM / NBSP / PUA / ZWNJ
        Row{std::string("插\xE2\x80\x8B入."), true},   // U+200B ZWS
        Row{std::string("导\xEF\xBB\xBF头."), true},   // U+FEFF BOM
        Row{std::string("非\xC2\xA0断."), true},        // U+00A0 NBSP
        Row{std::string("私\xEE\x80\x80区."), true},   // U+E000 PUA
        Row{std::string("零\xE2\x80\x8C宽"), true},     // U+200C ZWNJ
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("invisible text bytes:");
    REQUIRE(rule_invisible_char(text) == expect_issue);
}

// -----------------------------------------------------------------------------
// 7) PUNCT_STYLE rule
// -----------------------------------------------------------------------------
TEST_CASE("PUNCT_STYLE rule", "[zh-translation][zh-helpers]")
{
    using Row = std::tuple<std::string, bool>;
    auto row = GENERATE(table<std::string, bool>({
        // negatives — full-width punctuation or all-English fragment.
        Row{"这是一句话，你好。", false},
        Row{"中文括号（鬼）。",    false},
        Row{"hello world",        false},
        Row{"ATK (English)",      false},
        Row{"Label: Test",         false},
        // positives — half-width punct adjacent to Chinese
        Row{"这是半角,父号。",   true},
        Row{"中文.句号。",       true},
        Row{"中文:冒号。",       true},
        Row{"中文(括号)用法。",  true},
        Row{"逗号,半角。",       true},
    }));
    const std::string& text = std::get<0>(row);
    const bool expect_issue = std::get<1>(row);
    INFO("text=\"" << text << "\"");
    REQUIRE(rule_punct_style(text) == expect_issue);
}

// -----------------------------------------------------------------------------
// 8) Aggregated scan_text() — sanity that any single rule adds an issue.
// -----------------------------------------------------------------------------
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: scan_text aggregates multiple issues in one text",
                 "[zh-translation][zh-helpers]")
{
    // A genuinely broken sample: half-width punct + double-space + ASCII run.
    std::string text = "你,Random text  多问题。";
    auto issues = scan_text(text, "key", "test");
    INFO("detected " << issues.size() << " issues:");
    REQUIRE(issues.size() >= 2);
}