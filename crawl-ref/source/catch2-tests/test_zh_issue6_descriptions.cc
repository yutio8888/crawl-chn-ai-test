#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "beam.h"
#include "database.h"
#include "describe.h"
#include "describe-spells.h"
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
#include "syscalls.h"
#include "test_zh_fixture.h"
#include "unwind.h"
#include "xom.h"
#include "unicode.h"

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
    CHECK(jelly.find("受伤或死亡时会释放多种果冻怪，"
                    "数量与受到的伤害成正比。\n") != string::npos);
    CHECK(jelly.find("被变形时会释放所有果冻怪。\n") != string::npos);
    CHECK(jelly.find("被近战击中时会造成1d5点酸伤害。\n")
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
    CHECK(make_stringf_p(C_("monster description",
                         "Despite %1$s appearance, %2$s can open doors.\n"), "它的", "它")
          == "尽管它的外表如此，它仍能开门。\n");
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
    // The live consumer now takes complete typed predicates, rather than
    // combining aspect-bearing flag labels with a second starts/looks verb.
    for (const auto effect : { ENCH_REGENERATION, ENCH_HASTE })
    {
        const string predicate = xom_enchantment_predicate(effect);
        REQUIRE(predicate == (effect == ENCH_REGENERATION
                              ? "开始再生" : "看起来迅捷了"));
        CHECK(make_stringf(T_("%s suddenly %s!"), "M", predicate.c_str())
              == "M突然" + predicate + "！");
    }

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

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: xv poison maxima qualify poison rather than paralysis",
                 "[zh-translation][issue147][descriptions]")
{
    for (const auto type : {MONS_HORNET, MONS_FORMLESS_JELLYFISH})
    {
        CAPTURE(type);
        const string description = issue6_monster_description(type);
        const monster_info mi(type);
        const attack_flavour flavour = type == MONS_HORNET
            ? AF_POISON_PARALYSE : AF_MINIPARA;
        const string expected = make_stringf("Poison (max %d) and %s",
            flavour_damage(flavour, mi.hd, false),
            type == MONS_HORNET ? "paralysis/slowing" : "momentary paralysis");
        CHECK(description.find(expected) != string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: xv poison maxima preserve complete translated formats",
                 "[zh-translation][issue147][descriptions]")
{
    for (const auto type : {MONS_HORNET, MONS_FORMLESS_JELLYFISH})
    {
        CAPTURE(type);
        const string description = issue6_monster_description(type);
        const monster_info mi(type);
        const attack_flavour flavour = type == MONS_HORNET
            ? AF_POISON_PARALYSE : AF_MINIPARA;
        const string maximum = make_stringf(T_(" (max %d%s)"),
            flavour_damage(flavour, mi.hd, false), "");
        const string expected = make_stringf(type == MONS_HORNET
            ? T_("Poison%s and paralysis/slowing")
            : T_("Poison%s and momentary paralysis"), maximum.c_str());
        CHECK(description.find(expected) != string::npos);
    }
}


TEST_CASE_METHOD(ZhTranslationFixture,
                 "playtest round4: real door descriptions preserve monster pronouns",
                 "[zh-translation][playtest-round4][descriptions]")
{
    init_monsters();
    init_spell_descs();
    unwind_var<bool> game_started(crawl_state.game_started, false);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (monster_type type : {MONS_ERICA, MONS_AIZUL, MONS_UGLY_THING})
        {
            monster_info mi(type);
            describe_info description;
            bool stats = false;
            get_monster_db_desc(mi, description, stats);
            const string text = description.body.str();
            INFO(text);
            const string subject = mi.pronoun(PRONOUN_SUBJECTIVE);
            const string possessive = mi.pronoun(PRONOUN_POSSESSIVE);
            const string expected = language == lang_t::ZH
                ? "尽管" + possessive + "外表如此，" + subject + "仍能开门。"
                : "Despite " + possessive + " appearance, " + subject + " can open doors.";
            CHECK(text.find(expected) != string::npos);
            if (language == lang_t::ZH && type == MONS_ERICA)
            {
                CHECK(subject == "她");
                CHECK(text.find("它仍能开门") == string::npos);
            }
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "playtest round4 related: invisible monster descriptions preserve facts and pronouns",
                 "[zh-translation][playtest-round4-related][descriptions]")
{
    init_monsters();
    init_spell_descs();
    unwind_var<bool> game_started(crawl_state.game_started, false);
    for (lang_t language : {lang_t::ZH, lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (monster_type type : {MONS_ERICA, MONS_AIZUL, MONS_UGLY_THING})
        {
            for (auto flag : {MB_KNOWN_INVIS, MB_REMEMBERED_INVIS})
            {
                monster_info mi(type);
                const string identity = mi.db_name();
                mi.mb.set(flag);
                describe_info description;
                bool stats = false;
                get_monster_db_desc(mi, description, stats);
                const string text = description.body.str();
                INFO(text);
                if (language == lang_t::ZH)
                {
                    CHECK(text.find("你目前看不到" + string(mi.pronoun(PRONOUN_OBJECTIVE)))
                          != string::npos);
                    CHECK(text.find("currently invisible") == string::npos);
                    if (flag == MB_KNOWN_INVIS)
                    {
                        CHECK(text.find("推断出了") != string::npos);
                        CHECK(text.find("当前生命值和状态") != string::npos);
                        CHECK(text.find("命中率") != string::npos);
                        CHECK(text.find("防御能力都会降低") != string::npos);
                        CHECK(text.find("最后一次看到") == string::npos);
                    }
                    else
                    {
                        CHECK(text.find("真实位置") != string::npos);
                        CHECK(text.find("最后一次看到" + string(mi.pronoun(PRONOUN_SUBJECTIVE)))
                              != string::npos);
                        CHECK(text.find("命中率") == string::npos);
                    }
                }
                else if (flag == MB_KNOWN_INVIS)
                {
                    CHECK(text.find("you have merely inferred ") != string::npos);
                    CHECK(text.find("current health and status is unknown to you") != string::npos);
                    CHECK(text.find(" attacks is reduced. </magenta>") != string::npos);
                }
                else
                {
                    CHECK(text.find(" true position is unknown, but ") != string::npos);
                    CHECK(text.find(" was last observed here.</magenta>") != string::npos);
                }
                CHECK(mi.db_name() == identity);
                CHECK(mi.is(flag));
            }
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "playtest round4 related: crystal spear name budgets use columns and localized fallback",
                 "[zh-translation][playtest-round4-related][spellset]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_monsters();
    init_spell_descs();
    init_zap_index();
    unwind_var<bool> game_started(crawl_state.game_started, false);
    monster_info mi(MONS_DEEP_ELF_ANNIHILATOR);
    spellbook_contents book;
    book.spells = {SPELL_LEHUDIBS_CRYSTAL_SPEAR};
    for (lang_t language : {lang_t::ZH, lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        formatted_string description;
        describe_spellset({book}, nullptr, description, &mi);
        const string text = description.tostring();
        INFO(text);
        if (language == lang_t::ZH)
        {
            CHECK(text.find("勒胡迪布之水晶矛") != string::npos);
            CHECK(text.find("Crystal Spear") == string::npos);
            CHECK(string(T_("Crystal Spear")) == "水晶矛");
        }
        else
            CHECK(text.find("Crystal Spear") != string::npos);
        CHECK(book.spells == vector<spell_type>{SPELL_LEHUDIBS_CRYSTAL_SPEAR});
    }

    TranslationFixture mode(lang_t::ZH, "zh");
    // A deliberately large spell-HD fixture makes the damage field consume
    // enough columns to exercise the short-name branch in the real renderer.
    mi.hd = 1000000;
    const int name_budget = 30
                           - strwidth(spell_effect_string(book.spells[0], &mi))
                           - 3 - 1; // range and separator
    REQUIRE(name_budget < strwidth(spell_title(book.spells[0])));
    REQUIRE(name_budget >= strwidth(T_("Crystal Spear")));
    formatted_string compact_description;
    describe_spellset({book}, nullptr, compact_description, &mi);
    const string compact_text = compact_description.tostring();
    INFO(compact_text);
    CHECK(compact_text.find("水晶矛") != string::npos);
    CHECK(compact_text.find("勒胡迪布之水晶矛") == string::npos);
    CHECK(compact_text.find("Crystal Spear") == string::npos);
}
