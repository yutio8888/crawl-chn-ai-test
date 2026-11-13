#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "god-abil.h"
#include "item-prop.h"
#include "message.h"
#include "options.h"
#include "player.h"
#include "potion.h"
#include "random.h"
#include "shopping.h"
#include "status.h"
#include "syscalls.h"
#include "unwind.h"

#include "test_zh_fixture.h"

namespace
{
struct merchant_case
{
    shop_type type;
    gender_type gender;
    const char* suffix;
    const char* english;
    const char* chinese;
};

const merchant_case merchant_cases[] = {
    {SHOP_JEWELLERY, GENDER_MALE, "Shop",
     "Ada Vale invites you to visit his Jewellery Shop.",
     "Ada Vale邀请你访问他的首饰店铺。"},
    {SHOP_JEWELLERY, GENDER_FEMALE, "Boutique",
     "Ada Vale invites you to visit her Jewellery Boutique.",
     "Ada Vale邀请你访问她的首饰精品店。"},
    {SHOP_JEWELLERY, GENDER_NEUTRAL, "",
     "Ada Vale invites you to visit their Jewellery.",
     "Ada Vale邀请你访问他的首饰。"},
    {SHOP_BOOK, GENDER_MALE, "",
     "Ada Vale invites you to visit his Book.",
     "Ada Vale邀请你访问他的书籍。"},
    {SHOP_BOOK, GENDER_FEMALE, "Shop",
     "Ada Vale invites you to visit her Book Shop.",
     "Ada Vale邀请你访问她的书籍店铺。"},
    {SHOP_BOOK, GENDER_NEUTRAL, "Boutique",
     "Ada Vale invites you to visit their Book Boutique.",
     "Ada Vale邀请你访问他的书籍精品店。"},
};

struct scoped_merchant_locale
{
    string saved = setlocale(LC_CTYPE, nullptr);
    scoped_merchant_locale()
    {
#if defined(UNIX) && !defined(__ANDROID__)
        REQUIRE(ensure_utf8_ctype());
#endif
    }
    ~scoped_merchant_locale() { setlocale(LC_CTYPE, saved.c_str()); }
};
}

TEST_CASE("Gozag merchant invitations preserve English and join Chinese shop fragments",
          "[zh-translation][r15][gozag-shop]")
{
    scoped_merchant_locale locale;
    unwind_var<bool> condense(Options.msg_condense_repeats, false);
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto& row : merchant_cases)
        {
            shop_struct shop;
            shop.type = row.type;
            shop.shop_name = "Ada Vale";
            shop.shop_type_name = "Saved specialty";
            shop.shop_suffix_name = row.suffix;
            const auto state = rng::current_generator().get_state();
            const auto count = rng::current_generator().get_count();
            msgwin_temporary_mode temporary;
            unwinder clear([]() { msgwin_clear_temporary(); });
            msg::tee observed;
            gozag_announce_shop(shop, row.gender);
            const string expected = language == lang_t::ZH
                ? row.chinese : row.english;
            CAPTURE(language, row.type, row.gender, row.suffix);
            CHECK(observed.get_store() == "<lightgrey>" + expected + "\n");
            CHECK(shop.shop_name == "Ada Vale");
            CHECK(shop.shop_type_name == "Saved specialty");
            CHECK(shop.shop_suffix_name == row.suffix);
            CHECK(rng::current_generator().get_state() == state);
            CHECK(rng::current_generator().get_count() == count);
        }
    }
}

TEST_CASE("attraction potion intensity follows its duration in both languages",
          "[zh-translation][r15][potion-intensity]")
{
    scoped_merchant_locale locale;
    init_properties();
    init_duration_index();
    unwind_var<player> restore_player(you);
    unwind_var<bool> condense(Options.msg_condense_repeats, false);
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    for (bool repeat : {false, true})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        you = player();
        you.species = SP_HUMAN;
        you.duration[DUR_ATTRACTIVE] = repeat ? 10 : 0;
        msgwin_temporary_mode temporary;
        unwinder clear([]() { msgwin_clear_temporary(); });
        msg::tee observed;
        REQUIRE(get_potion_effect(POT_ATTRACTION)->effect());
        const string expected = language == lang_t::ZH
            ? (repeat ? "你感到对怪物更加有吸引力了。" : "你感到对怪物有吸引力了。")
            : (repeat ? "You feel more attractive to monsters." : "You feel attractive to monsters.");
        CAPTURE(language, repeat);
        CHECK(observed.get_store() == "<lightblue>" + expected + "\n");
        CHECK(you.duration[DUR_ATTRACTIVE] > (repeat ? 10 : 0));
    }
}
