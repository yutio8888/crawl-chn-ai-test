#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include <fstream>
#include <iterator>
#include <utility>

#include "beam.h"
#include "chardump.h"
#include "describe.h"
#include "files.h"
#include "hiscores.h"
#include "item-prop.h"
#include "items.h"
#include "i18n.h"
#include "mon-info.h"
#include "mon-util.h"
#include "notes.h"
#include "options.h"
#include "player.h"
#include "religion.h"
#include "spl-cast.h"
#include "spl-util.h"
#include "state.h"
#include "syscalls.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "unicode.h"
#include "unwind.h"

namespace
{
void issue149_player()
{
    you = player();
    you.species = SP_HUMAN;
    you.set_position(coord_def(20, 20));
    you.hp = you.hp_max = 28;
    you.experience_level = 12;
    you.base_stats[STAT_INT] = 25;
}
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 weapon description separates numeric fields",
                 "[zh-translation][issue149][descriptions]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    unwind_var<bool> game_started(crawl_state.game_started, false);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        issue149_player();
        item_def dagger;
        dagger.base_type = OBJ_WEAPONS;
        dagger.sub_type = WPN_DAGGER;
        dagger.quantity = 1;
        dagger.flags = ISFLAG_IDENTIFIED;
        const string description = get_item_description(dagger);
        if (language == lang_t::ZH)
        {
            CHECK(description.find("伤害: 4  基础攻击延迟") != string::npos);
            CHECK(description.find("这 武器") == string::npos);
            CHECK(description.find("短刃") != string::npos);
        }
        else
        {
            CHECK(description.find("Base damage: 4  Base attack delay: 1.0")
                  != string::npos);
            CHECK(description.find("This weapon falls into the 'Short Blades'")
                  != string::npos);
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 surviving damage notes do not claim death",
                 "[zh-translation][issue149][notes]")
{
    init_monsters();
    unwind_var<player> restore_player(you);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        issue149_player();
        you.hp = 1;
        for (kill_method_type cause : {KILLED_BY_MONSTER, KILLED_BY_HEADBUTT,
                                       KILLED_BY_ROLLING, KILLED_BY_SPINES})
        {
            INFO("cause=" << cause);
            scorefile_entry entry(5, MID_NOBODY, cause, "+0 spear", true, "Robin");
            const string source = entry.death_description(scorefile_entry::DDV_TERSE);
            const Note injury(NOTE_HP_CHANGE, 1, 28, source);
            const string displayed = injury.describe(false, false);
            CHECK(displayed.find("1/28") != string::npos);
            CHECK(displayed.find("5") != string::npos);
            CHECK(displayed.find(language == lang_t::ZH ? "罗宾" : "Robin")
                  != string::npos);
            CHECK(source.find("杀死") == string::npos);
            CHECK(source.find("击杀") == string::npos);
            CHECK(source.find("压死") == string::npos);
            if (language == lang_t::ZH && cause == KILLED_BY_MONSTER)
            {
                const string death = entry.death_description(scorefile_entry::DDV_ONELINE);
                CHECK(death.find("杀死") != string::npos);
            }
        }
        Note defeated(NOTE_DEFEAT_MONSTER, 0, 0, "Robin", "killed");
        CHECK(defeated.describe(false, false)
              == (language == lang_t::ZH ? "击杀Robin" : "Killed Robin"));
        CHECK(defeated.name == "Robin");
        CHECK(defeated.desc == "killed");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 monster display distinguishes attack and remembered state",
                 "[zh-translation][issue149][monsters]")
{
    init_monsters();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (bool with_object : {false, true})
        {
            CHECK(mon_attack_name(AT_GORE, with_object)
                  == (language == lang_t::ZH ? "顶撞" : "gore"));
        }
        monster_info remembered(MONS_SHADOWGHAST);
        remembered.mb.set(MB_REMEMBERED_INVIS);
        const auto attributes = remembered.attributes();
        const string flag = language == lang_t::ZH ? "曾在此处" : "remembered";
        CHECK(find(attributes.begin(), attributes.end(), flag) != attributes.end());
        if (language == lang_t::ZH)
        {
            CHECK(find(attributes.begin(), attributes.end(), "remembered")
                  == attributes.end());
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 hit chance describes chance with a complete sentence",
                 "[zh-translation][issue149][descriptions]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        issue149_player();
        item_def staff;
        staff.base_type = OBJ_STAVES;
        staff.sub_type = STAFF_CONJURATION;
        staff.quantity = 1;
        staff.flags = ISFLAG_IDENTIFIED;
        ostringstream displayed;
        describe_hit_chance(97, displayed, &staff, true);
        const string text = displayed.str();
        CHECK(text.find("97%") != string::npos);
        CHECK(text.find(language == lang_t::ZH ? "咒法法杖" : "staff of conjuration")
              != string::npos);
        CHECK(text.find(language == lang_t::ZH ? "命中率" : "% to hit")
              != string::npos);
        CHECK(text.find("命中用你的") == string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 151 ordinary item origins localize complete sentences",
                 "[zh-translation][issue149][issue151][descriptions]")
{
    init_monsters();
    init_properties();
    unwind_var<player> restore_player(you);
    unwind_var<bool> game_started(crawl_state.game_started, false);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        issue149_player();
        item_def item;
        item.base_type = OBJ_WEAPONS;
        item.sub_type = WPN_DAGGER;
        item.quantity = 1;
        item.flags = ISFLAG_IDENTIFIED;
        item.orig_place = level_id(BRANCH_DUNGEON, 3);
        for (monster_type monster : {MONS_GOBLIN, MONS_ROBIN, MONS_ENCHANTRESS,
                                     MONS_PLAYER_GHOST,
                                     MONS_PANDEMONIUM_LORD})
        {
            INFO("monster=" << monster);
            item.orig_monnum = monster;
            REQUIRE(origin_describable(item));
            string name = language == lang_t::ZH
                          ? mons_type_name(monster, DESC_PLAIN)
                          : mons_type_name_en(monster, DESC_A);
            if (language == lang_t::ZH && monster == MONS_PLAYER_GHOST)
                name = T_("player ghost");
            else if (language == lang_t::ZH && monster == MONS_PANDEMONIUM_LORD)
                name = T_("pandemonium lord");
            else if (language == lang_t::ZH && monster == MONS_ENCHANTRESS)
                name = "妖术女王";
            const string expected = language == lang_t::ZH
                ? "在地牢第3层你从" + name + "身上拿走了它"
                : "You took it off " + name + " on level 3 of the Dungeon";
            CHECK(origin_desc(item) == expected);
            // The actual description consumer adds one sentence terminator.
            const string description = get_item_description(item);
            CHECK(description.find(expected + ".") != string::npos);
            CHECK(description.find(expected + "..") == string::npos);
            if (language == lang_t::ZH)
            {
                CHECK(description.find(" off ") == string::npos);
                CHECK(origin_desc(item).find("a ") == string::npos);
                CHECK(origin_desc(item).find("an ") == string::npos);
                CHECK(origin_desc(item).find("the ") == string::npos);
            }
            CHECK(item.orig_monnum == monster);
            CHECK(item.orig_place == level_id(BRANCH_DUNGEON, 3));
            CHECK(mons_type_name_en(monster, DESC_PLAIN).find("罗宾")
                  == string::npos);
            if (monster == MONS_ENCHANTRESS)
                CHECK(mons_type_name_en(monster, DESC_PLAIN) == "the Enchantress");
        }
        item.orig_monnum = 0;
        CHECK(origin_desc(item) == (language == lang_t::ZH
              ? "在地牢第3层你找到了它"
              : "You found it on level 3 of the Dungeon"));
        CHECK(item.orig_monnum == 0);
        CHECK(item.orig_place == level_id(BRANCH_DUNGEON, 3));
        item.quantity = 2;
        CHECK_FALSE(origin_describable(item));
        CHECK(origin_desc(item).empty());
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 religion dumps retain attitude and English tense",
                 "[zh-translation][issue149][morgue]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() {
        setlocale(LC_CTYPE, saved_locale.c_str());
    });
    REQUIRE(ensure_utf8_ctype());
    unwind_var<player> restore_player(you);
    unwind_var<vector<string>> order(Options.dump_order, {"religion"});
    unwind_var<string> directory(Options.morgue_dir, ".");
    unwind_var<bool> updating(crawl_state.updating_scores);
    unwind_var<bool> saving(crawl_state.need_save);
    const string name = "catch2-issue149-religion-" + to_string(getpid());
    unwinder cleanup([name]() {
        unlink_u((name + ".txt").c_str());
        unlink_u((name + ".lst").c_str());
    });
    const scorefile_entry death;
    const vector<pair<int, const char *>> ranks = {
        {0, "noncommittal"},
        {100, "aware of your devotion"},
        {500, "pleased with you"},
        {1000, "most pleased with you"},
        {5000, "greatly pleased with you"},
        {10000, "extremely pleased with you"},
        {50000, "exalted by your worship"}
    };
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (bool dead : {false, true})
        {
            INFO("dead=" << dead);
            crawl_state.updating_scores = dead;
            crawl_state.need_save = !dead;
            for (const auto &rank : ranks)
            {
                INFO("gold=" << rank.first);
                issue149_player();
                you.religion = GOD_GOZAG;
                you.gold = rank.first;
                REQUIRE(dump_char(name, true, false, dead ? &death : nullptr));
                ifstream file(name + ".txt");
                REQUIRE(file.good());
                const string dump((istreambuf_iterator<char>(file)),
                                  istreambuf_iterator<char>());
                const string expected = language == lang_t::ZH
                    ? string(dead ? "哥萨戈当时" : "哥萨戈") + T_(rank.second) + "。"
                    : string(dead ? "Gozag was " : "Gozag is ") + rank.second + ".";
                INFO("expected=" << expected << "; dump=" << dump);
                CHECK(dump.find(expected + "\n") != string::npos);
                CHECK(dump.find("原为") == string::npos);
                CHECK(you.religion == GOD_GOZAG);
                CHECK(you.gold == rank.first);
                CHECK(string(_god_name_en(you.religion)) == "Gozag");
            }
            issue149_player();
            you.religion = GOD_XOM;
            you.raw_piety = 100;
            you.gift_timeout = 10;
            REQUIRE(dump_char(name, true, false, dead ? &death : nullptr));
            ifstream file(name + ".txt");
            REQUIRE(file.good());
            const string dump((istreambuf_iterator<char>(file)),
                              istreambuf_iterator<char>());
            INFO("Xom dump=" << dump);
            CHECK(dump.find(language == lang_t::ZH
                            ? dead ? "你曾是佐姆的玩具。\n" : "你是佐姆的玩具。\n"
                            : dead ? "You were a toy of Xom.\n" : "You are a toy of Xom.\n")
                  != string::npos);
            CHECK(dump.find("柯苏特") == string::npos);
            CHECK(you.religion == GOD_XOM);
            CHECK(string(_god_name_en(you.religion)) == "Xom");
        }
        // Wizard numeric/text summaries still use the generic, separate key.
        CHECK(string(T_("%s was %s."))
              == (language == lang_t::ZH ? "%s原为%s。" : "%s was %s."));
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 spell dump retains composite damage and failure rate",
                 "[zh-translation][issue149][morgue]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() {
        setlocale(LC_CTYPE, saved_locale.c_str());
    });
    REQUIRE(ensure_utf8_ctype());
    init_spell_descs();
    init_zap_index();
    init_properties();
    unwind_var<player> restore_player(you);
    unwind_var<vector<string>> order(Options.dump_order, {"spells"});
    unwind_var<string> directory(Options.morgue_dir, ".");
    const string name = "catch2-issue149-dump-" + to_string(getpid());
    unwinder cleanup([name]() {
        unlink_u((name + ".txt").c_str());
        unlink_u((name + ".lst").c_str());
    });
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (bool memorised : {false, true})
        {
            INFO("memorised=" << memorised);
            issue149_player();
            you.spell_library.set(SPELL_ISKENDERUNS_MYSTIC_BLAST);
            if (memorised)
                REQUIRE(add_spell_to_memory(SPELL_ISKENDERUNS_MYSTIC_BLAST));
            const string damage = spell_damage_string(SPELL_ISKENDERUNS_MYSTIC_BLAST);
            REQUIRE(damage.find('(') != string::npos);
            REQUIRE(damage.find(')') != string::npos);
            const string failure = failure_rate_to_string(raw_spell_fail(SPELL_ISKENDERUNS_MYSTIC_BLAST));
            REQUIRE(dump_char(name, true));
            ifstream file(name + ".txt");
            REQUIRE(file.good());
            const string dump((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
            INFO("damage=" << damage << "; dump=" << dump);
            const size_t pos = dump.find(damage);
            REQUIRE(pos != string::npos);
            const size_t end = dump.find('\n', pos);
            const string tail = dump.substr(pos + damage.size(), end - pos - damage.size());
            REQUIRE_FALSE(tail.empty());
            CHECK(tail.front() == ' ');
            CHECK(tail.find(failure) != string::npos);
        }
    }
}
