#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include <fstream>
#include <iterator>
#include <map>
#include <set>
#include <tuple>
#include <utility>

#include "ability.h"
#include "areas.h"
#include "beam.h"
#include "chardump.h"
#include "colour.h"
#include "branch.h"
#include "dgn-overview.h"
#include "dungeon.h"
#include "env.h"
#include "describe.h"
#include "files.h"
#include "hiscores.h"
#include "item-prop.h"
#include "item-name.h"
#include "items.h"
#include "i18n.h"
#include "losglobal.h"
#include "mon-info.h"
#include "mon-death.h"
#include "monster.h"
#include "mon-util.h"
#include "mon-place.h"
#include "mutation.h"
#include "notes.h"
#include "options.h"
#include "output.h"
#include "player.h"
#include "player-equip.h"
#include "religion.h"
#include "spl-cast.h"
#include "spl-util.h"
#include "state.h"
#include "syscalls.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "travel.h"
#include "unicode.h"
#include "unwind.h"

// The overview has no public snapshot API; preserve its existing discovery
// table while preparing a fixture with an undiscovered Temple.
extern map<branch_type, set<level_id>> stair_level;

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


TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 157 staff and armour comparisons preserve bilingual delays",
                 "[zh-translation][issue149][issue157][descriptions]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_properties();
    init_monsters();
    init_spell_descs();
    unwind_var<player> restore_player(you);
    unwind_var<bool> started(crawl_state.game_started, false);
    unwind_var<bool> saving(crawl_state.need_save, true);
    for (int scenario : {0, 1, 2})
    {
        INFO("scenario=" << scenario);
        string english_numbers;
        for (lang_t language : {lang_t::EN, lang_t::ZH})
        {
            TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
            issue149_player();
            you.base_stats[STAT_STR] = you.base_stats[STAT_DEX] = 10;
            if (scenario != 0)
            {
                item_def& weapon = you.inv[0];
                weapon.base_type = OBJ_WEAPONS;
                weapon.sub_type = scenario == 1 ? WPN_LONG_SWORD : WPN_LONGBOW;
                weapon.quantity = 1;
                weapon.flags = ISFLAG_IDENTIFIED;
                weapon.pos = ITEM_IN_INVENTORY;
                weapon.link = 0;
                you.equipment.add(weapon, SLOT_WEAPON);
                you.equipment.update();
                REQUIRE(you.weapon() == &weapon);
            }
            item_def candidate;
            candidate.base_type = scenario == 2 ? OBJ_ARMOUR : OBJ_STAVES;
            candidate.sub_type = scenario == 2 ? ARM_ROBE : STAFF_CONJURATION;
            candidate.quantity = 1;
            candidate.flags = ISFLAG_IDENTIFIED;
            const player_stats before = you.calc_stats(100);
            const string description = get_item_description(candidate);
            INFO(description);
            const string prefix = language == lang_t::EN ? "Your attack delay would " : "你的攻击延迟";
            const size_t begin = description.find(prefix);
            REQUIRE(begin != string::npos);
            const string line = description.substr(begin, description.find('\n', begin) - begin);
            if (language == lang_t::EN)
            {
                CHECK(line.find(scenario == 0 ? "increase" : scenario == 1 ? "decrease" : "remain unchanged") != string::npos);
                if (scenario != 2)
                {
                    const size_t numbers = line.find('(');
                    REQUIRE(numbers != string::npos);
                    english_numbers = line.substr(numbers, line.find(')', numbers) - numbers + 1);
                    if (scenario == 0)
                        CHECK(english_numbers == "(1.0 -> 1.2)");
                }
            }
            else
            {
                CHECK(line.find("Your attack delay") == string::npos);
                CHECK(line.find(scenario == 0 ? "增加" : scenario == 1 ? "减少" : "不变") != string::npos);
                if (scenario != 2)
                    CHECK(line.find(english_numbers) != string::npos);
            }
            CHECK(you.calc_stats(100).delay == before.delay);
            CHECK(candidate.sub_type == (scenario == 2 ? ARM_ROBE : STAFF_CONJURATION));
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 157 frost death localizes morgue without changing kaux",
                 "[zh-translation][issue149][issue157][morgue][protocol]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_monsters();
    init_properties();
    unwind_var<player> restore_player(you);
    unwind_var<vector<string>> order(Options.dump_order, {"hiscore"});
    unwind_var<string> directory(Options.morgue_dir, ".");
    unwind_var<bool> updating(crawl_state.updating_scores, true);
    unwind_var<bool> saving(crawl_state.need_save, false);
    issue149_player();
    // Match the normal level initialization and the existing real-score
    // fixture: an uninitialized zero map ID indexes a nonexistent vault.
    const coord_def player_position = you.pos();
    const unsigned old_map_id = env.level_map_ids(player_position);
    unwinder restore_map_id([player_position, old_map_id]() {
        env.level_map_ids(player_position) = old_map_id;
    });
    env.level_map_ids(player_position) = INVALID_MAP_INDEX;
    you.your_name = "Issue157";
    you.hp = 0;
    const string filename = "catch2-issue157-death-" + to_string(getpid());
    unwinder cleanup([filename]() {
        unlink_u((filename + ".txt").c_str());
        unlink_u((filename + ".lst").c_str());
    });
    // Lowercase names are raw beam identities. Uppercase kaux is the separate
    // historic protocol for an already assembled shooting sentence.
    for (const char* cause : {"puff of frost", "unknown legacy beam"})
    {
        scorefile_entry entry(2, MID_NOBODY, KILLED_BY_BEAM, cause, true,
                              "Blorkula the Orcula");
        entry.init(1600000000);
        const string raw = entry.raw_string();
        REQUIRE_FALSE(raw.empty());
        REQUIRE(entry.get_fields().str_field("kaux") == cause);
        for (lang_t language : {lang_t::ZH, lang_t::EN})
        {
            TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
            scorefile_entry saved;
            REQUIRE(saved.parse(raw));
            const string verbose = saved.death_description(scorefile_entry::DDV_VERBOSE);
            INFO(verbose);
            const string display_cause = language == lang_t::ZH ? T_(cause) : cause;
            CHECK(verbose.find(display_cause) != string::npos);
            if (language == lang_t::ZH && string(cause) == "puff of frost")
                CHECK(verbose.find(cause) == string::npos);
            REQUIRE(dump_char(filename, true, false, &saved));
            ifstream file(filename + ".txt");
            REQUIRE(file.good());
            const string dump((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
            INFO(dump);
            CHECK(dump.find(display_cause) != string::npos);
            if (language == lang_t::ZH && string(cause) == "puff of frost")
                CHECK(dump.find(cause) == string::npos);
            CHECK(saved.get_fields().str_field("kaux") == cause);
            CHECK(saved.raw_string() == raw);
            CHECK(saved.death_description(scorefile_entry::DDV_LOGVERBOSE).find(cause) != string::npos);
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 154 and 155 named monsters assemble display grammar once",
                 "[zh-translation][issue149][issue154][issue155][monsters]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_monsters();
    init_properties();
    init_spell_descs();
    unwind_var<player> restore_player(you);
    unwind_var<bool> saving(crawl_state.need_save, false);
    issue149_player();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (monster_type type : {MONS_ANCESTOR, MONS_ANCESTOR_KNIGHT,
                                  MONS_ANCESTOR_ELEMENTALIST, MONS_ANCESTOR_HEXER})
        {
            monster_info ancestor(type);
            ancestor.mname = "Xochitl";
            ancestor.props[MON_GENDER_KEY] = GENDER_NEUTRAL;
            const string name = ancestor.full_name();
            CHECK(name.find("Xochitl") != string::npos);
            CHECK(name.find(ancestor.common_name()) != string::npos);
            CHECK((name.find(" the ") != string::npos) == (language == lang_t::EN));
            CHECK(string(ancestor.pronoun(PRONOUN_SUBJECTIVE)) == (language == lang_t::ZH ? "它" : "they"));
            CHECK(ancestor.pronoun_plurality() == (language == lang_t::EN));
            CHECK(ancestor.props[MON_GENDER_KEY].get_int() == GENDER_NEUTRAL);
            CHECK(ancestor.mname == "Xochitl");
            monster actual;
            actual.type = type;
            actual.props[MON_GENDER_KEY] = GENDER_NEUTRAL;
            CHECK(actual.pronoun(PRONOUN_SUBJECTIVE, true) == ancestor.pronoun(PRONOUN_SUBJECTIVE));
            CHECK(actual.pronoun_plurality(true) == (language == lang_t::EN));
        }
        for (monster_type type : {MONS_PLAYER_GHOST, MONS_PLAYER_ILLUSION})
        {
            monster_info ghost(type);
            ghost.mname = "SpecialOrigin";
            const string displayed = ghost.full_name();
            CHECK(displayed.find("的的") == string::npos);
            CHECK(displayed == (language == lang_t::ZH
                ? string("SpecialOrigin的") + (type == MONS_PLAYER_GHOST ? "鬼魂" : "幻象")
                : string("SpecialOrigin's ") + (type == MONS_PLAYER_GHOST ? "ghost" : "illusion")));
            CHECK(ghost.mname == "SpecialOrigin");
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 155 every panlord body adjective fits its full template",
                 "[zh-translation][issue149][issue155][descriptions]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_monsters();
    init_properties();
    init_spell_descs();
    unwind_var<player> restore_player(you);
    unwind_var<bool> saving(crawl_state.need_save, false);
    unwind_var<bool> started(crawl_state.game_started, false);
    issue149_player();
    const set<string> expected = {"armoured", "vast, spindly", "fat", "obese",
        "muscular", "spiked", "splotchy", "slender", "tentacled", "emaciated",
        "bug-like", "skeletal", "mantis", "slithering"};
    set<string> covered;
    for (int n = 0; n < 160; ++n)
    {
        const string name = n == 0 ? "Ugrogiot" : "Issue155Panlord" + to_string(n);
        for (bool flying : {false, true})
        {
            monster_info demon(MONS_PANDEMONIUM_LORD);
            demon.mname = name;
            demon.ghost_colour = ETC_RANDOM;
            demon.mb.set(MB_AIRBORNE, flying);
            for (lang_t language : {lang_t::EN, lang_t::ZH})
            {
                TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
                describe_info description;
                bool has_stats = false;
                get_monster_db_desc(demon, description, has_stats);
                const string text = description.body.str();
                INFO(name << " flying=" << flying << ": " << text);
                CHECK(text.find(name) != string::npos);
                CHECK(text.find("的的") == string::npos);
                if (language == lang_t::EN)
                {
                    bool found = false;
                    for (const string& adjective : expected)
                        if (text.find(adjective + " body") != string::npos)
                        {
                            covered.insert(adjective);
                            found = true;
                        }
                    CHECK(found);
                }
                else
                    for (const string& adjective : expected)
                        CHECK(text.find(adjective + "的躯体") == string::npos);
                CHECK(demon.mname == name);
            }
        }
    }
    CHECK(covered == expected);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 156 named corpse creation keeps English identities",
                 "[zh-translation][issue149][issue156][items][protocol]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_monsters();
    init_properties();
    unwind_var<player> restore_player(you);
    issue149_player();
    for (monster_type type : {MONS_ROBIN, MONS_JESSICA, MONS_ENCHANTRESS})
    {
        monster dead;
        dead.type = type;
        dead.set_position(coord_def(20, 21));
        unwind_var<dungeon_feature_type> floor(env.grid(dead.pos()), DNGN_FLOOR);
        item_def* corpse = place_corpse_or_gold(dead, true);
        REQUIRE(corpse != nullptr);
        const int index = corpse->index();
        unwinder cleanup([index]() { destroy_item(index); });
        const string identity = mons_type_name_en(type, DESC_PLAIN);
        REQUIRE(get_corpse_name(*corpse) == identity);
        for (lang_t language : {lang_t::ZH, lang_t::EN})
        {
            TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
            for (int form : {CORPSE_BODY, CORPSE_SKELETON})
            {
                corpse->sub_type = form;
                const string displayed = corpse->name(DESC_PLAIN);
                INFO(displayed);
                CHECK((displayed.find(" of ") != string::npos) == (language == lang_t::EN));
                const string translated_name = language == lang_t::ZH
                    ? type == MONS_ENCHANTRESS ? T_("Enchantress") : mons_type_name(type, DESC_PLAIN)
                    : identity;
                CHECK(displayed.find(translated_name) != string::npos);
                if (language == lang_t::ZH && type == MONS_ENCHANTRESS)
                    CHECK(displayed.find("the ") == string::npos);
                CHECK(get_corpse_name(*corpse) == identity);
                CHECK(corpse->orig_monnum == type);
            }
        }
        // Purchasing or acquiring an item can replace orig_monnum with a
        // non-monster source. It must not be used to resolve a custom name.
        {
            TranslationFixture chinese(lang_t::ZH, "zh");
            corpse->orig_monnum = -IT_SRC_SHOP;
            corpse->props[CORPSE_NAME_KEY] = "the CustomName";
            CHECK(corpse->name(DESC_PLAIN).find("the CustomName") != string::npos);
            CHECK(get_corpse_name(*corpse) == "the CustomName");
            CHECK(corpse->orig_monnum == -IT_SRC_SHOP);
        }
        // A historic localized snapshot and a custom name have no lookup key.
        for (const string& legacy : {string("旧名字"), string("CustomName")})
        {
            corpse->props[CORPSE_NAME_KEY] = legacy;
            CHECK(corpse->name(DESC_PLAIN).find(legacy) != string::npos);
            CHECK(get_corpse_name(*corpse) == legacy);
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 carried stash and unexplored temple localize display labels",
                 "[zh-translation][issue149][stash][overview]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_monsters();
    init_properties();
    unwind_var<player> restore_player(you);
    unwind_var<branch_type> root(root_branch, BRANCH_DUNGEON);
    unwind_var<int> depth(brdepth[BRANCH_DUNGEON], 15);
    unwind_var<int> temple_depth(brdepth[BRANCH_TEMPLE], 1);
    unwind_var<game_type> game(crawl_state.type, GAME_TYPE_NORMAL);
    unwind_var<TravelCache> explored(travel_cache, TravelCache());
    unwind_var<map<branch_type, set<level_id>>> discovered(stair_level, {});
    issue149_player();
    you.where_are_you = BRANCH_DUNGEON;
    you.depth = 5;
    // A real D:5 arrival has a travel record for the stairs back to D:4.
    // Unseen branch ranges are conditional on that explored-level cache.
    stair_info arrival;
    arrival.position = you.pos();
    arrival.grid = DNGN_STONE_STAIRS_UP_I;
    arrival.destination = level_pos(level_id(BRANCH_DUNGEON, 4), you.pos());
    arrival.guessed_pos = false;
    travel_cache.get_level_info(level_id::current()).get_stairs().push_back(arrival);
    REQUIRE(find_deepest_explored(level_id(BRANCH_DUNGEON, 0)) == level_id::current());
    item_def& dagger = you.inv[0];
    dagger.base_type = OBJ_WEAPONS;
    dagger.sub_type = WPN_DAGGER;
    dagger.quantity = 1;
    dagger.flags = ISFLAG_IDENTIFIED;
    dagger.pos = ITEM_IN_INVENTORY;
    dagger.link = 0;
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const string displayed = Stash::stash_item_name(dagger);
        CHECK(displayed.find(dagger.name(DESC_INVENTORY_EQUIP)) != string::npos);
        CHECK((displayed.find("[carried] ") != string::npos) == (language == lang_t::EN));
        CHECK(dagger.link == 0);
        CHECK(dagger.pos == ITEM_IN_INVENTORY);
        for (bool onscreen : {false, true})
        {
            const string overview = overview_description_string(onscreen);
            INFO(overview);
            CHECK(overview.find("(5/15)") != string::npos);
            CHECK(overview.find(language == lang_t::ZH ? "神殿" : "Temple") != string::npos);
            CHECK((overview.find("Temple:") != string::npos) == (language == lang_t::EN));
            CHECK(overview.find(":4-7") != string::npos);
            CHECK(string(branches[BRANCH_TEMPLE].abbrevname) == "Temple");
            CHECK(string(branches[BRANCH_DUNGEON].abbrevname) == "D");
        }
    }
}


TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 149 ancestor and neutral monsters localize actual lists and dumps",
                 "[zh-translation][issue149][issue154][monsters][morgue]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_properties();
    init_monsters();
    init_spell_descs();
    unwind_var<player> restore_player(you);
    unwind_var<bool> started(crawl_state.game_started, false);
    unwind_var<bool> testing(crawl_state.test, true);
    unwind_var<vector<string>> order(Options.dump_order, {"monlist"});
    unwind_var<string> directory(Options.morgue_dir, ".");
    const mid_t old_last_mid = you.last_mid;
    const int old_max_mon_index = env.max_mon_index;
    const auto old_mid_cache = env.mid_cache;
    vector<tuple<coord_def, dungeon_feature_type, unsigned short, uint32_t>> cells;
    vector<monster*> monsters;
    issue149_player();
    you.last_mid = old_last_mid;
    you.on_current_level = true;
    you.current_vision = LOS_DEFAULT_RANGE;
    you.wizard_vision = true;
    // Match the existing lit-floor monster consumer fixture. Preserve every
    // grid cell and allocator identity that this test changes.
    unwinder restore_world([&]() {
        for (monster* mon : monsters)
            mon->reset();
        env.mid_cache = old_mid_cache;
        env.max_mon_index = old_max_mon_index;
        for (const auto& cell : cells)
        {
            env.grid(get<0>(cell)) = get<1>(cell);
            env.mgrid(get<0>(cell)) = get<2>(cell);
            env.level_map_ids(get<0>(cell)) = get<3>(cell);
        }
        invalidate_los();
        invalidate_agrid();
    });
    for (int x = 12; x <= 28; ++x)
        for (int y = 12; y <= 28; ++y)
        {
            const coord_def pos(x, y);
            cells.emplace_back(pos, env.grid(pos), env.mgrid(pos), env.level_map_ids(pos));
            env.grid(pos) = DNGN_FLOOR;
            env.mgrid(pos) = NON_MONSTER;
            env.level_map_ids(pos) = INVALID_MAP_INDEX;
        }
    invalidate_los();
    invalidate_agrid();
    for (int which : {0, 1})
    {
        monster* mon = get_free_monster();
        REQUIRE(mon != nullptr);
        monsters.push_back(mon);
        mon->type = which == 0 ? MONS_ANCESTOR_HEXER : MONS_GOBLIN;
        mon->mname = which == 0 ? "Xochitl" : "";
        mon->props["issue149_identity"] = "English identity";
        mon->set_hit_dice(1);
        mon->hit_points = mon->max_hit_points = 30;
        mon->speed = 10;
        mon->base_attitude = which == 0 ? ATT_FRIENDLY : ATT_NEUTRAL;
        mon->behaviour = BEH_SEEK;
        mon->foe = MHITYOU;
        mon->set_position(coord_def(20 + which, 21));
        mon->set_new_monster_id();
        env.mgrid(mon->pos()) = mon->mindex();
    }
    const string filename = "catch2-issue149-monlist-" + to_string(getpid());
    unwinder cleanup([filename]() {
        unlink_u((filename + ".txt").c_str());
        unlink_u((filename + ".lst").c_str());
    });
    const scorefile_entry death;
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (bool past : {false, true})
        {
            const string listed = mpr_monster_list(past);
            INFO(listed);
            CHECK(listed.find(language == lang_t::ZH ? "友善" : "friendly") != string::npos);
            CHECK(listed.find(language == lang_t::ZH ? "中立" : "neutral") != string::npos);
            CHECK(listed.find(language == lang_t::ZH ? "诅咒师Xochitl" : "Xochitl the hexer") != string::npos);
            if (language == lang_t::ZH)
            {
                CHECK(listed.find("friendly") == string::npos);
                CHECK(listed.find("neutral") == string::npos);
            }
            REQUIRE(dump_char(filename, true, false, past ? &death : nullptr));
            ifstream file(filename + ".txt");
            REQUIRE(file.good());
            const string dump((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
            INFO(dump);
            CHECK(dump.find(listed) != string::npos);
            CHECK(monsters[0]->base_attitude == ATT_FRIENDLY);
            CHECK(monsters[1]->base_attitude == ATT_NEUTRAL);
            CHECK(monsters[0]->mname == "Xochitl");
            CHECK(monsters[0]->type == MONS_ANCESTOR_HEXER);
            CHECK(monsters[0]->props["issue149_identity"].get_string() == "English identity");
            CHECK(monsters[1]->props["issue149_identity"].get_string() == "English identity");
            CHECK(monsters[1]->mname.empty());
            CHECK(monsters[1]->type == MONS_GOBLIN);
            CHECK(mons_type_name_en(monsters[0]->type, DESC_PLAIN) == "hexer");
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Issue 154 ancestor life descriptions agree across actual consumers",
                 "[zh-translation][issue149][issue154][abilities][mutations][morgue]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([saved_locale]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    init_properties();
    init_monsters();
    init_spell_descs();
    init_mut_index();
    unwind_var<player> restore_player(you);
    unwind_var<vector<string>> order(Options.dump_order, {"mutations"});
    unwind_var<string> directory(Options.morgue_dir, ".");
    issue149_player();
    you.religion = GOD_HEPLIAKLQANA;
    you.raw_piety = 80;
    you.props[HEPLIAKLQANA_ALLY_NAME_KEY] = "Xochitl";
    you.props[HEPLIAKLQANA_ALLY_TYPE_KEY] = MONS_ANCESTOR_HEXER;
    // The dump includes the mutation section only for a mutated player; use
    // the ordinary innate caster mutation of the reported deep elf character.
    you.species = SP_DEEP_ELF;
    you.mutation[MUT_INNATE_CASTER] = you.innate_mutation[MUT_INNATE_CASTER] = 1;
    REQUIRE(you.has_any_mutations());
    const string filename = "catch2-issue154-life-" + to_string(getpid());
    unwinder cleanup([filename]() {
        unlink_u((filename + ".txt").c_str());
        unlink_u((filename + ".lst").c_str());
    });
    const string english_life = "Your life essence is reduced to manifest your ancestor. (-10% HP)";
    const string chinese_life = "你的生命精华因显现先祖而减少。（-10% 生命值）";
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const string life = language == lang_t::ZH ? chinese_life : english_life;
        const string mutations = describe_muts_for_chardump(false);
        INFO(mutations);
        CHECK(mutations.find(life) != string::npos);
        REQUIRE(dump_char(filename, true));
        ifstream file(filename + ".txt");
        REQUIRE(file.good());
        const string dump((istreambuf_iterator<char>(file)), istreambuf_iterator<char>());
        INFO(dump);
        CHECK(dump.find(life) != string::npos);
        if (language == lang_t::ZH)
        {
            CHECK(mutations.find(english_life) == string::npos);
            CHECK(dump.find(english_life) == string::npos);
        }
        const string menu = ability_name(ABIL_HEPLIAKLQANA_TYPE_HEXER, false);
        CHECK(menu == (language == lang_t::ZH ? "先祖生命：诅咒师" : "Ancestor Life: Hexer"));
        CHECK(ability_name(ABIL_HEPLIAKLQANA_TYPE_HEXER, true) == "Ancestor Life: Hexer");
        const string details = get_ability_desc(ABIL_HEPLIAKLQANA_TYPE_HEXER, false);
        INFO(details);
        CHECK(details.find(language == lang_t::ZH
            ? "回想起你的先祖是个诅咒师，一个刀法迅捷、擅长施展削弱性法术的狡猾贼人。"
            : "Remembers your ancestor as a hexer") != string::npos);
        const string type_name = language == lang_t::ZH
            ? mons_type_name(MONS_ANCESTOR_HEXER, DESC_PLAIN)
            : mons_type_name_en(MONS_ANCESTOR_HEXER, DESC_A);
        const string confirmation = make_stringf(
            T_("Are you sure you want to remember your ancestor as %s?"), type_name.c_str());
        CHECK(confirmation == (language == lang_t::ZH
            ? "你确定要记住你的先祖作为诅咒师吗？"
            : "Are you sure you want to remember your ancestor as a hexer?"));
        monster_info ancestor(MONS_ANCESTOR_HEXER);
        ancestor.mname = "Xochitl";
        CHECK(ancestor.full_name() == (language == lang_t::ZH ? "诅咒师Xochitl" : "Xochitl the hexer"));
        const string identity = mons_type_name_en(MONS_ANCESTOR_HEXER, DESC_A);
        const Note note(NOTE_ANCESTOR_TYPE, 0, 0, identity);
        const string displayed_note = note.describe(false, false);
        INFO(displayed_note);
        CHECK(displayed_note.find(language == lang_t::ZH ? "诅咒师" : "a hexer") != string::npos);
        CHECK(note.name == "a hexer");
        CHECK(identity == "a hexer");
        CHECK(you.props[HEPLIAKLQANA_ALLY_NAME_KEY].get_string() == "Xochitl");
        CHECK(you.props[HEPLIAKLQANA_ALLY_TYPE_KEY].get_int() == MONS_ANCESTOR_HEXER);
        CHECK(you.raw_piety == 80);
    }
}
