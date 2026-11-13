#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "i18n.h"
#include "item-def.h"
#include "item-name.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "mon-info.h"
#include "mon-util.h"
#include "player.h"
#include "status.h"
#include "syscalls.h"
#include "unwind.h"

#include "test_zh_fixture.h"

namespace
{
struct scoped_name_locale
{
    string saved = setlocale(LC_CTYPE, nullptr);
    scoped_name_locale()
    {
#if defined(UNIX) && !defined(__ANDROID__)
        REQUIRE(ensure_utf8_ctype());
#endif
    }
    ~scoped_name_locale() { setlocale(LC_CTYPE, saved.c_str()); }
};
}

TEST_CASE("resource potion names do not rename ordinary magic",
          "[zh-translation][r11-r12][item-name]")
{
    scoped_name_locale locale;
    init_properties();
    for (lang_t lang : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture language(lang, lang == lang_t::ZH ? "zh" : nullptr);
        const bool zh = lang == lang_t::ZH;
        item_def potion;
        potion.base_type = OBJ_POTIONS;
        potion.sub_type = POT_MAGIC;
        potion.quantity = 1;
        potion.flags |= ISFLAG_IDENTIFIED;
        CHECK(string(potion_type_name(POT_MAGIC)) == (zh ? "法力" : "magic"));
        CHECK(potion.name(DESC_PLAIN) == (zh ? "法力药水" : "potion of magic"));
        CHECK(string(T_("magic")) == (zh ? "魔法" : "magic"));
    }
}

TEST_CASE("Horror and Fear retain distinct production status labels",
          "[zh-translation][r11-r12][status]")
{
    scoped_name_locale locale;
    init_duration_index();
    unwind_var<player> restore_player(you);
    for (lang_t lang : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture language(lang, lang == lang_t::ZH ? "zh" : nullptr);
        const bool zh = lang == lang_t::ZH;
        you = player();
        you.duration[DUR_HORROR] = 1;
        you.props[HORROR_PENALTY_KEY] = HORROR_LVL_EXTREME;
        status_info horror;
        REQUIRE(fill_status_info(DUR_HORROR, horror));
        CHECK(horror.light_text.find(zh ? "惊骇" : "Horr") == 0);
        CHECK(horror.short_text == (zh ? "极度惊骇" : "extremely horrified"));
        CHECK(horror.long_text == (zh ? "你极度惊骇！" : "You are extremely horrified!"));

        you.duration[DUR_AFRAID] = 1;
        status_info fear;
        REQUIRE(fill_status_info(DUR_AFRAID, fear));
        CHECK(fear.light_text == (zh ? "恐惧" : "Fear"));
    }
}

TEST_CASE("named player ghosts and illusions add one possessive",
          "[zh-translation][r11-r12][monster-name]")
{
    scoped_name_locale locale;
    init_monsters();
    for (lang_t lang : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture language(lang, lang == lang_t::ZH ? "zh" : nullptr);
        const bool zh = lang == lang_t::ZH;
        for (const string& owner : {string("Alex"), string("艾达")})
        {
            for (monster_type type : {MONS_PLAYER_GHOST, MONS_PLAYER_ILLUSION})
            {
                monster_info mon(type);
                mon.mname = owner;
                const string suffix = type == MONS_PLAYER_GHOST
                    ? (zh ? "的鬼魂" : "'s ghost")
                    : (zh ? "的幻象" : "'s illusion");
                CHECK(mon.common_name(DESC_PLAIN) == owner + suffix);
                CHECK(mon.mname == owner);
            }
        }
    }
}
