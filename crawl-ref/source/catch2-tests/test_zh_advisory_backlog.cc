#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "delay.h"
#include "transform.h"
#include "item-prop.h"
#include "format.h"
#include "i18n.h"
#include "item-def.h"
#include "message.h"
#include "mutation.h"
#include "player.h"
#include "spl-book.h"
#include "spl-cast.h"
#include "stringutil.h"
#include "syscalls.h"
#include "unicode.h"
#include "unwind.h"

#include "test_zh_fixture.h"

namespace
{
struct scoped_display_locale
{
    string saved = setlocale(LC_CTYPE, nullptr);
    scoped_display_locale()
    {
#if defined(UNIX) && !defined(__ANDROID__)
        REQUIRE(ensure_utf8_ctype());
#endif
    }
    ~scoped_display_locale() { setlocale(LC_CTYPE, saved.c_str()); }
};

void require_utf8(const string& text)
{
    for (const char* s = text.c_str(); *s; )
    {
        char32_t c;
        const int bytes = utf8towc(&c, s);
        REQUIRE(bytes > 0);
        REQUIRE(c != 0xFFFD);
        s += bytes;
    }
}
}

TEST_CASE("spell search headings retain complete Chinese codepoints",
          "[zh-translation][advisory-backlog]")
{
    scoped_display_locale locale;
    TranslationFixture language(lang_t::ZH, "zh");
    string regression = "a";
    for (int i = 0; i < 16; ++i)
        regression += "界";
    CHECK(regression.size() == 49);
    CHECK(spell_search_description(regression, 47)
          == "匹配：<w>" + regression + "</w>");

    string long_name;
    for (int i = 0; i < 40; ++i)
        long_name += "界";
    for (int width : {22, 28, 47})
    {
        const string text = spell_search_description(long_name, width);
        CAPTURE(width, text);
        require_utf8(text);
        CHECK(ends_with(text, "..</w>"));
        const string plain = formatted_string::parse_string(text).tostring();
        CHECK(strwidth(plain) <= width + strwidth("匹配："));
    }

    const string escaped = spell_search_description("<界>", 22);
    CHECK(escaped == "匹配：<w><<界></w>");
    CHECK(formatted_string::parse_string(escaped).tostring() == "匹配：<界>");
}

TEST_CASE("spell search keeps the English heading and precision contract",
          "[zh-translation][advisory-backlog]")
{
    TranslationFixture language(lang_t::EN, nullptr);
    CHECK(spell_search_description("fire", 47) == "Matches: <w>fire</w>");
    const string long_name(60, 'a');
    for (int width : {22, 28, 47})
    {
        CHECK(spell_search_description(long_name, width)
              == "Matches: <w>" + string(width - 2, 'a') + "..</w>");
    }
    // Escaping and byte precision have the same order as the old EN path.
    CHECK(spell_search_description(string(30, '<'), 22)
          == "Matches: <w>" + string(20, '<') + "..</w>");
}

TEST_CASE("equipment interruptions keep verb and object separate",
          "[zh-translation][advisory-backlog]")
{
    init_mut_index();
    unwind_var<player> restore_player(you);
    for (lang_t lang : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture language(lang, lang == lang_t::ZH ? "zh" : nullptr);
        for (int kind : {0, 1, 2})
        {
            you = player();
            you.species = SP_HUMAN;
            item_def item;
            item.quantity = 1;
            item.base_type = kind == 0 ? OBJ_WEAPONS
                : kind == 1 ? OBJ_ARMOUR : OBJ_JEWELLERY;
            if (kind == 0)
                item.sub_type = WPN_LONG_SWORD;
            else if (kind == 1)
                item.sub_type = ARM_ROBE;
            else
                item.sub_type = AMU_REGENERATION;
            string text;
            {
                msg::tee capture(text);
                EquipOffDelay delay(1, item);
                REQUIRE(delay.try_interrupt(true));
            }
            const string expected = lang == lang_t::ZH
                ? (kind == 0 ? "你停止了收起武器。"
                   : kind == 1 ? "你停止了脱下护甲。" : "你停止了摘下项链。")
                : (kind == 0 ? "You stop unwielding your weapon."
                   : kind == 1 ? "You stop removing your armour."
                               : "You stop removing your amulet.");
            CAPTURE(lang, kind, text);
            CHECK(text.find(expected) != string::npos);
        }
    }
}

TEST_CASE("Equipment completion uses whole clauses for each equipment action",
          "[zh-translation][r22][equipment-completion]")
{
    init_mut_index();
    init_properties();
    unwind_var<player> restore_player(you);
    const char * const on_en[] = {"wielding", "attuning to", "putting on",
                                 "putting on", "haunting", "fusing with"};
    const char * const off_en[] = {"unwielding", "parting from", "removing",
                                  "removing", "removing yourself from", "unfusing"};
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (int kind = 0; kind < 6; ++kind)
        {
            you = player();
            you.species = SP_HUMAN;
            if (kind == 1)
                you.mutation[MUT_SLOW_WIELD] = 1;
            if (kind == 4)
                you.mutation[MUT_FORMLESS] = 1;
            if (kind == 5)
                you.form = transformation::fortress_crab;
            item_def item;
            item.quantity = 1;
            item.flags = ISFLAG_IDENTIFIED;
            item.base_type = kind < 2 ? OBJ_WEAPONS
                : kind == 3 ? OBJ_JEWELLERY : OBJ_ARMOUR;
            item.sub_type = kind < 2 ? static_cast<int>(WPN_LONG_SWORD)
                : kind == 3 ? static_cast<int>(AMU_REGENERATION)
                            : static_cast<int>(ARM_ROBE);
            const equipment_slot slot = kind < 2 ? SLOT_WEAPON
                : kind == 3 ? SLOT_AMULET : SLOT_BODY_ARMOUR;
            const string name = item.name(DESC_YOUR);
            const string on_zh[] = {"你已握持" + name + "。", "你已与" + name + "完成调谐。",
                "你已穿上" + name + "。", "你已戴上" + name + "。",
                "你已附身于" + name + "。", "你已与" + name + "融合。"};
            const string off_zh[] = {"你已收起" + name + "。", "你已解除与" + name + "的调谐。",
                "你已脱下" + name + "。", "你已摘下" + name + "。",
                "你已从" + name + "中脱离。", "你已解除与" + name + "的融合。"};
            EquipOnDelay on(1, item, slot);
            EquipOffDelay off(1, item);
            CAPTURE(language, kind, name);
            CHECK(on.completion_message() == (language == lang_t::ZH ? on_zh[kind]
                : make_stringf("You finish %s %s.", on_en[kind], name.c_str())));
            CHECK(off.completion_message() == (language == lang_t::ZH ? off_zh[kind]
                : make_stringf("You finish %s %s.", off_en[kind], name.c_str())));
        }
    }
}
