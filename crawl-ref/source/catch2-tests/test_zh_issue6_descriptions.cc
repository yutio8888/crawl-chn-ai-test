#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "describe.h"
#include "i18n.h"
#include "jobs.h"
#include "mon-info.h"
#include "mon-util.h"
#include "options.h"
#include "player.h"
#include "positional_format.h"
#include "religion.h"
#include "species.h"
#include "spl-util.h"
#include "state.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "unwind.h"

namespace
{
string issue6_monster_description(monster_type type)
{
    init_monsters();
    init_spell_descs();
    unwind_var<bool> game_started(crawl_state.game_started, false);
    unwind_var<god_type> religion(you.religion, GOD_NO_GOD);
    monster_info mi(type);
    describe_info info;
    bool has_stats = false;
    get_monster_db_desc(mi, info, has_stats);
    REQUIRE(has_stats);
    return info.body.str();
}
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 6 monster descriptions preserve complete sentences",
                 "[zh-translation][issue6][descriptions]")
{
    // Exercise the real description producer, including pronouns, list
    // assembly, and newlines, rather than only looking up individual keys.
    const string jelly = issue6_monster_description(MONS_ROYAL_JELLY);
    CHECK(jelly.find("受伤或死亡时会释放多种史莱姆，"
                    "数量与受到的伤害成正比。\n") != string::npos);
    CHECK(jelly.find("被变形时会释放所有史莱姆。\n") != string::npos);
    CHECK(jelly.find("近战攻击时会额外造成1d5点酸伤害。\n")
          != string::npos);
    CHECK(jelly.find("是无定形的，免疫缠绕。\n") != string::npos);

    const string shadow = issue6_monster_description(MONS_SHADOWGHAST);
    CHECK(shadow.find("隐形时移动速度更快。\n") != string::npos);
    CHECK(shadow.find("是无实体的，免疫缠绕。\n") != string::npos);

    const string beast = issue6_monster_description(MONS_MUTANT_BEAST);
    CHECK(beast.find("它长着一组剧毒的尾巴") != string::npos);
    CHECK(beast.find(C_("mutant beast facets", ", it")) != string::npos);
    CHECK(beast.find(C_("mutant beast facets", ", and it")) != string::npos);
}

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: Issue 6 monster descriptions keep English grammar",
                 "[zh-translation][issue6][descriptions]")
{
    const string jelly = issue6_monster_description(MONS_ROYAL_JELLY);
    CHECK(jelly.find("It will release varied jellies when damaged or killed, "
                    "with the number of jellies proportional to the amount "
                    "of damage.\n") != string::npos);
    CHECK(jelly.find("It will release all of its jellies when polymorphed.\n")
          != string::npos);
    CHECK(jelly.find(" 1d5 acid damage when struck in melee.\n")
          != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 6 ghost descriptions retain slot order and identity",
                 "[zh-translation][issue6][descriptions]")
{
    init_monsters();
    monster_info ghost(MONS_PLAYER_GHOST);
    ghost.mname = "Issue6";
    ghost.i_ghost.title = "FrozenTitle";
    const string rank = T_("journeyman");
    const string species_name = species::name(ghost.i_ghost.species);
    const string job = get_job_name(ghost.i_ghost.job);
    const string expected = "Issue6（FrozenTitle，" + rank + species_name + job;

    CHECK(get_ghost_description(ghost, false) == expected + "）");
    CHECK(get_ghost_description(ghost, true) == expected + "）");
    ghost.i_ghost.religion = GOD_ZIN;
    CHECK(get_ghost_description(ghost, false)
          == expected + "，信仰" + god_name(GOD_ZIN) + "）");
    CHECK(ghost.mname == "Issue6");
    CHECK(ghost.i_ghost.title == "FrozenTitle");
    CHECK(ghost.i_ghost.religion == GOD_ZIN);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 6 migrated formats preserve argument and join contracts",
                 "[zh-translation][issue6][formats]")
{
    // The spore message has seven string slots. Stealth was not displayed in
    // this branch before migration and no longer occupies an unused slot.
    CHECK(make_stringf_p(C_("spore attack",
                           "%1$s %2$s at %3$s%4$s%5$s%6$s%7$s"),
                         "A", "V", "D", "C", "N", "W", "!")
          == "A向DVCNW!");
    CHECK(make_stringf_p(C_("monster description",
                           "%1$s is susceptible to %2$s.\n"), "P", "R")
          == "P易受R影响。\n");
    CHECK(make_stringf(C_("monster description",
                         "Despite %s appearance, it can open doors.\n"), "P")
          == "尽管外表P，但它能开门。\n");
    CHECK(make_stringf(C_("attack prompt", "fire in %s direction"), "M")
          == "向M的方向");
    CHECK(string(C_("attack prompt", "your ally ")) == "你的盟友");
    CHECK(string(C_("attack prompt", "your "))
          + C_("attack prompt", "ally ") == "你的盟友");

    const vector<string> gods = { "A", "B", "C" };
    CHECK(comma_separated_line(gods.begin(), gods.end(),
                               C_("god wrath list", " and "),
                               C_("god wrath list", ", ")) == "A、B和C");
    CHECK(string(T_("  [<w>J</w>/<w>Enter</w>]: join"))
          == "  [<w>J</w>/<w>回车</w>]: 皈依");
    CHECK(make_stringf(T_("%s suddenly %s%s!"), "M",
                       C_("xom enchantment", "starts "), "E")
          == "M突然开始了E！");
    CHECK(make_stringf(T_("%s suddenly %s%s!"), "M",
                       C_("xom enchantment", "looks "), "E")
          == "M突然看起来了E！");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: Issue 6 context formats fall back to their English keys",
                 "[zh-translation][issue6][textdb]")
{
    // Reconcile the real TextDB layer so this reaches the missing-context
    // fallback while retaining ZH as the requested display language.
    Options.lang_name = "zz-no-textdb";
    databaseSystemInit();
    CHECK(make_stringf_p(C_("spore attack",
                           "%1$s %2$s at %3$s%4$s%5$s%6$s%7$s"),
                         "A", "V", "D", "C", "N", "W", "!")
          == "A V at DCNW!");
    CHECK(make_stringf_p(C_("ghost description",
                           "%1$s the %2$s, %3$s %4$s %5$s of %6$s"),
                         "A", "T", "R", "S", "J", "G")
          == "A the T, R S J of G");
    CHECK(make_stringf(C_("attack prompt", "fire in %s direction"), "M")
          == "fire in M direction");
    CHECK(string(C_("xom enchantment", "starts ")) == "starts ");
    CHECK(string(C_("xom enchantment", "looks ")) == "looks ");
    CHECK(string(T_("  [<w>J</w>/<w>Enter</w>]: join"))
          == "  [<w>J</w>/<w>Enter</w>]: join");
}
