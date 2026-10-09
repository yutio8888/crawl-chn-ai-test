#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include <fstream>
#include <iterator>

#include "beam.h"
#include "chardump.h"
#include "describe.h"
#include "files.h"
#include "hiscores.h"
#include "item-prop.h"
#include "i18n.h"
#include "mon-info.h"
#include "mon-util.h"
#include "notes.h"
#include "options.h"
#include "player.h"
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
