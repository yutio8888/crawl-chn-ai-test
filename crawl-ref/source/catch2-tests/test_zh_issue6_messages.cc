#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "acquire.h"
#include "branch.h"
#include "flang-t.h"
#include "i18n.h"
#include "item-prop.h"
#include "items.h"
#include "lang-fake.h"
#include "libutil.h"
#include "mon-info.h"
#include "mon-util.h"
#include "options.h"
#include "place.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "unwind.h"

#include <utility>

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: item origin keeps its pronoun and place across locales",
                 "[zh-translation][issue6][item-messages]")
{
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.quantity = 1;
    item.orig_place = level_id(BRANCH_DUNGEON, 1);
    item.orig_monnum = -AQ_SCROLL;

    REQUIRE(origin_describable(item));
    const string chinese = origin_desc(item);
    CHECK(chinese.find("它") != string::npos);
    CHECK(chinese.find(" it ") == string::npos);
    CHECK(prep_branch_level_name(item.orig_place).find("在") == 0);
    {
        EnTranslationFixture english_mode;
        const string english = origin_desc(item);
        CHECK(english.find(" it ") != string::npos);
        CHECK(english.find("它") == string::npos);
        CHECK(prep_branch_level_name(item.orig_place)
              == "on level 1 of the Dungeon");
    }
    CHECK(origin_desc(item) == chinese);
    CHECK(item.orig_place == level_id(BRANCH_DUNGEON, 1));
    CHECK(item.orig_monnum == -AQ_SCROLL);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: hydra head display keeps words and decimal boundaries",
                 "[zh-translation][issue6][monster-info]")
{
    init_monsters();
    monster_info hydra(MONS_HYDRA);
    for (const auto &row : {std::make_pair(1, "（一头）"),
                            std::make_pair(10, "（十头）"),
                            std::make_pair(11, "（11头）"),
                            std::make_pair(20, "（20头）")})
    {
        hydra.num_heads = row.first;
        const string chinese = hydra.common_name();
        CHECK(chinese.find(row.second) != string::npos);
        {
            EnTranslationFixture english_mode;
            CHECK(hydra.common_name().find("-headed hydra") != string::npos);
            CHECK(hydra.common_name().find("头") == string::npos);
        }
        CHECK(hydra.common_name() == chinese);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: starting display templates preserve parameter order",
                 "[zh-translation][issue6][start-notes]")
{
    CHECK(make_stringf(C_("game start", "<yellow>%s, %s the %s %s.</yellow>"),
                       "欢迎", "Ada", "人类", "战士")
          == "<yellow>欢迎，Ada（人类 战士）。</yellow>");
    CHECK(make_stringf(C_("game start", "%s set off with %s%s%s."),
                       "Ada", "甲", "乙", "丙") == "Ada携带甲乙丙出发了。");
    CHECK(make_stringf(C_("game start", "%s set off with %s%s%s."),
                       "Ada", "", "", "") == "Ada携带出发了。");
    CHECK(make_stringf(C_("game start", "%s the %s %s began the quest for the Orb."),
                       "Ada", "人类", "战士")
          == "Ada（人类 战士）开始了寻找宝珠的征程。");
    CHECK(string(C_("monster notice list", "and")) == "和");
    CHECK(string(T_(", ")) == "、");
    CHECK(string(T_(".")) == "。");

    EnTranslationFixture english_mode;
    CHECK(make_stringf(C_("game start", "<yellow>%s, %s the %s %s.</yellow>"),
                       "Welcome", "Ada", "Human", "Fighter")
          == "<yellow>Welcome, Ada the Human Fighter.</yellow>");
    CHECK(make_stringf(C_("game start", "%s set off with %s%s%s."),
                       "Ada", "A", "B", "C") == "Ada set off with ABC.");
    CHECK(make_stringf(C_("game start", "%s the %s %s began the quest for the Orb."),
                       "Ada", "Human", "Fighter")
          == "Ada the Human Fighter began the quest for the Orb.");
    CHECK(string(C_("monster notice list", "and")) == "and");
    CHECK(string(T_(".")) == ".");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: wide pseudo-language maps Unicode independently of locale",
                 "[zh-translation][issue6][wide-language]")
{
    unwind_var<vector<flang_entry>> restore_fake_langs(Options.fake_langs);
    Options.fake_langs = {{flang_t::wide, 0}};
    const string input = " A~\n\t中文";
    const string expected = "　Ａ～\n\t中文";
    CHECK(filtered_lang(input) == expected);
    EnTranslationFixture english_mode;
    CHECK(filtered_lang(input) == expected);
}
