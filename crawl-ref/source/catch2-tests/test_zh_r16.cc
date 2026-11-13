#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "i18n.h"
#include "item-prop.h"
#include "mon-cast.h"
#include "player.h"
#include "status.h"
#include "syscalls.h"
#include "unwind.h"

#include "test_zh_fixture.h"

TEST_CASE("Oblivion Howl adjectives join the final sentence in both languages",
          "[zh-translation][r16][oblivion-howl]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([&]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
#if defined(UNIX) && !defined(__ANDROID__)
    REQUIRE(ensure_utf8_ctype());
#endif
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const bool zh = language == lang_t::ZH;
        // These shared adjectives have other consumers and must stay unchanged.
        CHECK(string(T_("terrible")) == (zh ? "可怕的" : "terrible"));
        CHECK(string(T_("silent")) == (zh ? "无声" : "silent"));
        for (bool silent : {false, true})
        for (bool resisted : {false, true})
        {
            const string effect = zh
                ? (resisted ? "但你抵抗住了。" : "它开始在你的脑海中回响！")
                : (resisted ? "but you resist." : "and it begins to echo in your mind!");
            const string expected = zh
                ? (silent ? "Hound A发出了无声的嚎叫，" : "Hound A发出了可怕的嚎叫，")
                : (silent ? "Hound A unleashes a silent howl, " : "Hound A unleashes a terrible howl, ");
            CAPTURE(language, silent, resisted);
            CHECK(oblivion_howl_message("Hound A", silent, effect) == expected + effect);
        }
    }
}

TEST_CASE("Vertigo display is distinct from Dazed and retains English identities",
          "[zh-translation][r16][vertigo]")
{
    init_properties();
    init_duration_index();
    unwind_var<player> restore_player(you);
    you = player();
    you.duration[DUR_VERTIGO] = 500;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const bool zh = language == lang_t::ZH;
        status_info info;
        REQUIRE(fill_status_info(DUR_VERTIGO, info));
        CHECK(info.light_text == (zh ? "头晕" : "Vertigo"));
        CHECK(info.short_text == (zh ? "头晕" : "vertiginous"));
        CHECK(info.long_text == (zh ? "头晕使你的攻击、施法和闪避更加困难。"
            : "Vertigo is making it harder to attack, cast, and dodge."));
        CHECK(info.db_key == "Vertigo");
        CHECK(info.short_db_key == "vertiginous");
        CHECK(string(duration_name(DUR_VERTIGO)) == "vertigo");
        CHECK(duration_by_name("vertigo") == DUR_VERTIGO);
        CHECK(string(T_("dazed")) == (zh ? "眩晕" : "dazed"));
        CHECK(string(T_("You snap out of the daze."))
              == (zh ? "你从眩晕中清醒过来。" : "You snap out of the daze."));
    }
}
