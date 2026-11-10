/**
 * @file
 * @brief Regression coverage for the stable-branch trunk backport (core C++).
 *
 * These cases exercise production paths only: catalog lookups consumed by the
 * display sinks, the canonical-identity / localized-display split, legacy
 * already-saved exclusion descriptions, and the death-cause round trip.
 */

#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "areas.h"
#include "beam.h"
#include "branch.h"
#include "cloud.h"
#include "cloud-type.h"
#include "database.h"
#include "dungeon.h"
#include "dgn-overview.h"
#include "english.h"
#include "describe-god.h"
#include "env.h"
#include "exclude.h"
#include "god-wrath.h"
#include "hiscores.h"
#include "losglobal.h"
#include "item-prop.h"
#include "jobs.h"
#include "lang-en-guard.h"
#include "melee-attack.h"
#include "mon-util.h"
#include "mutation.h"
#include "notes.h"
#include "options.h"
#include "positional_format.h"
#include "player.h"
#include "religion.h"
#include "skills.h"
#include "species.h"
#include "state.h"
#include "spl-damage.h"
#include "spl-goditem.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "transform.h"
#include "travel.h"
#include "unwind.h"
#include "view.h"

#include <chrono>
#include <vector>

namespace
{
// Small lit-floor world: enough for exclude LOS/placement and mid lookups,
// mirroring the fixture convention used by the other ZH consumer tests.
struct backport_world
{
    unwind_var<player> saved_player{you};
    unwind_var<bool> saved_test{crawl_state.test, true};
    unwind_var<bool> saved_started{crawl_state.game_started, false};

    backport_world()
    {
        init_properties();
        init_monsters();
        init_spell_descs();
        reset_player();
        for (int x = 15; x <= 30; ++x)
            for (int y = 15; y <= 30; ++y)
            {
                const coord_def p(x, y);
                env.grid(p) = DNGN_FLOOR;
                env.mgrid(p) = NON_MONSTER;
                // dgn_vault_at() indexes level_map_ids: a death path
                // (ouch -> scorefile_entry::init) must not read an
                // uninitialised map id here.
                env.level_map_ids(p) = INVALID_MAP_INDEX;
            }
        you.set_position(coord_def(20, 20));
        invalidate_los();
        invalidate_agrid();
    }

    // Restore a *living* player. `you = player()` leaves hp at 0, which turns
    // any mutation/effect call into a death path.
    void reset_player()
    {
        you = player();
        init_properties();
        you.species = SP_HUMAN;
        you.hp = you.hp_max = 100;
        you.magic_points = you.max_magic_points = 20;
        you.on_current_level = true;
        you.current_vision = LOS_DEFAULT_RANGE;
        you.wizard_vision = true;
        you.set_position(coord_def(20, 20));
        you.mutation.init(0);
        invalidate_los();
        invalidate_agrid();
    }
};
} // namespace

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: chinese number words keep hundred/thousand grouping",
                 "[zh-translation][backport][numbers]")
{
    // A leading ten is bare ("十五"), but a ten following hundreds/thousands
    // keeps its "one" ("一百一十五"), and the finite vocabulary has no
    // ten-thousand grouping word.
    CHECK(number_in_words(15) == "十五");
    CHECK(number_in_words(110) == "一百一十");
    CHECK(number_in_words(115) == "一百一十五");
    CHECK(number_in_words(2010) == "二千零一十");
    CHECK(number_in_words(9999) == "九千九百九十九");
    CHECK(number_in_words(10000) == "10000");
    CHECK(number_in_words(12345) == "12345");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: auxiliary attacks translate at the message sink",
                 "[zh-translation][backport][combat]")
{
    backport_world world;

    REQUIRE(mutate(MUT_FANGS, "backport test"));
    const vector<string> fang_names = get_player_aux_names();
    const string fang_expected = C_("auxiliary attack name", "bite");
    REQUIRE(fang_expected != "bite");   // the assets must carry this context
    CHECK(find(fang_names.begin(), fang_names.end(), fang_expected)
          != fang_names.end());

    // Claws without tentacles form the composite off-hand name; the identity is
    // canonical English and the lookup happens through the catalog context.
    world.reset_player();
    REQUIRE(mutate(MUT_CLAWS, "backport test"));
    const vector<string> claw_names = get_player_aux_names();
    const string claw_expected = C_("auxiliary attack name", "off-hand claw");
    REQUIRE(claw_expected != "off-hand claw");
    CHECK(find(claw_names.begin(), claw_names.end(), claw_expected)
          != claw_names.end());

    // Verb sink: the tail attack is a plain-key lookup today.
    CHECK(string(C_("auxiliary attack name", "tail-slap")) == "尾击");
    CHECK(string(C_("auxiliary attack verb", "punch")) == "拳击");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: draconian scale colour is canonical, sentence is localized",
                 "[zh-translation][backport][species]")
{
    // Identity stays English in every display language.
    CHECK(string(species::scale_type(SP_RED_DRACONIAN)) == "fiery red");
    {
        EnTranslationFixture en;
        CHECK(string(species::scale_type(SP_RED_DRACONIAN)) == "fiery red");
        // English display must stay English.
        CHECK(make_stringf(T_("Your %s scales are hard. (AC +%d)"),
                           T_(species::scale_type(SP_RED_DRACONIAN)), 7)
              == "Your fiery red scales are hard. (AC +7)");
    }

    const string zh = make_stringf(T_("Your %s scales are hard. (AC +%d)"),
                                   T_(species::scale_type(SP_RED_DRACONIAN)),
                                   7);
    CHECK(zh.find("火红色") != string::npos);
    CHECK(zh.find("AC +7") != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: frailty death cause keeps canonical xlog, localizes display",
                 "[zh-translation][backport][death-protocol]")
{
    backport_world world;
    you.your_name = "BackportTester";
    you.birth_time = 1599999900;
    you.last_keypress_time = chrono::system_clock::from_time_t(you.birth_time);
    you.species = SP_HUMAN;
    you.char_class = JOB_MONK;
    you.chr_class_name = get_job_name(you.char_class);
    you.where_are_you = BRANCH_DUNGEON;
    you.depth = 1;

    const string mutation_en = mutation_name_en(MUT_FRAIL);
    const string mutation_display = mutation_name(MUT_FRAIL);
    REQUIRE(!mutation_en.empty());
    REQUIRE(mutation_en != mutation_display);
    {
        ScopedLangEn english;
        CHECK(string(mutation_name(MUT_FRAIL)) == mutation_en);
    }

    const string cause = "gaining the " + mutation_en + " mutation";
    const string expected = make_stringf(T_("gaining the %s mutation"),
                                         mutation_display.c_str());

    scorefile_entry live(0, MID_NOBODY, KILLED_BY_FRAILTY, cause.c_str(), true);
    live.init(1600000000);
    const string serialized = live.raw_string();
    REQUIRE(!serialized.empty());
    CHECK(xlog_fields(serialized).str_field("kaux") == cause);

    scorefile_entry restored;
    REQUIRE(restored.parse(serialized));
    CHECK(xlog_fields(restored.raw_string()).str_field("kaux") == cause);

    const string display =
        restored.death_description(scorefile_entry::DDV_VERBOSE);
    CHECK(display.find(expected) != string::npos);
    {
        const ScopedLangEn english;
        const string en = restored.death_description(
            scorefile_entry::DDV_VERBOSE);
        CHECK(en.find(cause) != string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: orb and fragmentation beam identities render at display",
                 "[zh-translation][backport][beam]")
{
    // Canonical identity is unchanged; only the display helper localizes.
    CHECK(orb_beam_name_display("orb of destruction") == "毁灭法球");
    CHECK(orb_beam_name_display("wavering orb of destruction")
          != "wavering orb of destruction");
    CHECK(orb_beam_name_display("some unknown beam") == "some unknown beam");
    CHECK(fragmentation_name_display("blast of rock fragments")
          != "blast of rock fragments");
    CHECK(fragmentation_name_display("unknown blast") == "unknown blast");

    CHECK(is_known_beam_name("bolt of cold"));
    CHECK(!is_known_beam_name("not a beam"));

    // English display is untouched.
    {
        EnTranslationFixture en;
        CHECK(orb_beam_name_display("orb of destruction") == "orb of destruction");
        CHECK(fragmentation_name_display("blast of rock fragments")
              == "blast of rock fragments");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: cloud exclusions recognise canonical and legacy descriptions",
                 "[zh-translation][backport][exclusions]")
{
    backport_world world;

    // Stable has no freezing-vapour cloud; CLOUD_COLD exercises the same path.
    const cloud_type type = CLOUD_COLD;
    const string canonical = cloud_type_name_en(type, true) + " cloud";
    string legacy;
    {
        const unwind_var<lang_t> chinese(Options.language, lang_t::ZH);
        legacy = make_stringf(T_("%s cloud"),
                              cloud_type_name(type, true).c_str());
    }
    REQUIRE(legacy != canonical);

    CHECK(is_cloud_exclusion(canonical));
    CHECK(is_cloud_exclusion(legacy));
    CHECK(!is_cloud_exclusion("a goblin"));

    // A legacy Chinese monster description renders through the canonical
    // normalisation instead of leaking or being dropped.
    const string legacy_monster = mons_type_name(MONS_GOBLIN, DESC_PLAIN);
    const string canonical_monster = mons_type_name_en(MONS_GOBLIN, DESC_PLAIN);
    CHECK(legacy_monster != canonical_monster);
    CHECK(exclusion_display_name(legacy_monster) == legacy_monster);
    CHECK(exclusion_display_name(canonical_monster) == legacy_monster);
    CHECK(exclusion_display_name("a hand-written exclusion")
          == "a hand-written exclusion");

    const string detected = canonical_monster + " (detected)";
    CHECK(exclusion_display_name(detected) == legacy_monster + T_(" (detected)"));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: unpacifiable sleeping/dormant suffix is localized",
                 "[zh-translation][backport][pacify]")
{
    init_monsters();
    init_properties();

    // Drive the real producer: a living, stationary-free monster that is
    // asleep / dormant reaches the suffix branch of unpacifiable_reason().
    for (const monster_info_flags flag : { MB_SLEEPING, MB_DORMANT })
    {
        monster_info mi(MONS_GOBLIN);
        mi.mb.set(flag);
        const string reason = unpacifiable_reason(mi);
        REQUIRE(!reason.empty());

        const char* en_suffix = flag == MB_SLEEPING ? "asleep" : "dormant";
        const string suffix = T_(en_suffix);
        CHECK(reason.find(suffix) != string::npos);
        // The English literal must not survive once the assets carry it; if
        // the asset is missing, T_() returns the key itself.
        if (suffix != en_suffix)
            CHECK(reason.find(string(" ") + en_suffix + "!") == string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: exclusion summary dedupes legacy Chinese and canonical names",
                 "[zh-translation][backport][exclusions]")
{
    backport_world world;

    const level_id level = level_id::current();
    const string legacy = mons_type_name(MONS_GOBLIN, DESC_PLAIN);
    const string canonical = mons_type_name_en(MONS_GOBLIN, DESC_PLAIN);

    exclude_set excludes;
    excludes.add_exclude(coord_def(20, 20), 2, true, legacy, false);
    excludes.add_exclude(coord_def(24, 20), 2, true, canonical, false);
    REQUIRE(excludes.size() == 2);

    // Storage keeps the canonical summary (and the historical EN prefix), so
    // two descriptions of the same monster become one counted entry.
    const string stored = excludes.get_exclusion_desc(level, false);
    // Storage is canonical English, so the count/plural prefix must be built
    // under the English guard (ZH pluralise() is identity by design).
    string stored_expected;
    {
        const ScopedLangEn english;
        stored_expected = "exclusion: 2 " + pluralise(canonical);
    }
    CHECK(stored == stored_expected);
    CHECK(stored.find(legacy) == string::npos);

    // Display renders the same identity in the current language, unpluralised.
    const string shown = excludes.get_exclusion_desc(level, true);
    CHECK(shown.find(legacy) != string::npos);
    CHECK(shown.find(canonical) == string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: saved ghost titles map the full stable special-title set",
                 "[zh-translation][backport][ghost]")
{
    init_monsters();
    init_properties();

    // Plain skill-table title.
    CHECK(translated_ghost_title("Fighter", SP_HUMAN)
          == string(T_("Fighter")));
    // Article form from older saves (and the La Petite Mort special case).
    CHECK(translated_ghost_title("the Fighter", SP_HUMAN)
          == string(T_("Fighter")));
    CHECK(translated_ghost_title("Petite Mort", SP_HUMAN)
          == string(T_("Petite Mort")));
    // "La Petite Mort" is the English article form of the plain title; ZH
    // keeps no article, so the saved form maps to the bare translated title.
    CHECK(translated_ghost_title("La Petite Mort", SP_HUMAN)
          == string(T_("Petite Mort")));
    // Species-specific specials from skill_title_by_rank().
    for (const char *special : { "Prickly Pangolin", "Hell Knight",
                                 "Rolling Thunder", "Weightless Champion" })
    {
        CHECK(translated_ghost_title(special, SP_HUMAN)
              == string(T_(special)));
    }
    // Conduct titles.
    for (const char *conduct : { "Flawless", "True Ascetic", "Incurious",
                                 "Ruthless", "Miser", "Chaos Fanatic",
                                 "Keeper of the Flame",
                                 "Pinnacle of Evolution" })
    {
        CHECK(translated_ghost_title(conduct, SP_HUMAN)
              == string(T_(conduct)));
    }
    // God titles resolve through the finite divine-title table.
    const string god_title_en = [] {
        const ScopedLangEn en;
        return god_title(GOD_TROG, SP_HUMAN, 200);
    }();
    REQUIRE(!god_title_en.empty());
    CHECK(translated_ghost_title(god_title_en, SP_HUMAN)
          == god_title(GOD_TROG, SP_HUMAN, 200));

    // Unknown or historical snapshots are never guessed at.
    CHECK(translated_ghost_title("BackportTester the Unmapped", SP_HUMAN)
          == "BackportTester the Unmapped");
    CHECK(translated_ghost_title("", SP_HUMAN).empty());

    // English display keeps the canonical title.
    {
        const ScopedLangEn en;
        CHECK(translated_ghost_title("Petite Mort", SP_HUMAN) == "Petite Mort");
        CHECK(translated_ghost_title("Prickly Pangolin", SP_HUMAN)
              == "Prickly Pangolin");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: possessive wrath identity stays canonical and localizes",
                 "[zh-translation][backport][death-protocol]")
{
    // Protocol identity: unchanged by the display language.
    CHECK(string(N_("Trog's wrath")) == "Trog's wrath");
    // Display: mapped through the finite possessive table when the assets
    // carry the template, otherwise the whole canonical string is kept.
    const string possessive = C_("god wrath possessive", "%1$s %2$s");
    const string noun = C_("god wrath noun", "wrath");
    const string expected = (possessive == "%1$s %2$s" || noun == "wrath")
        ? string("Trog's wrath")
        : make_stringf_p(possessive.c_str(),
                         god_name(GOD_TROG, false).c_str(), noun.c_str());
    CHECK(god_wrath_display_name("Trog's wrath") == expected);
    // The "the <noun> of <god>" family is mapped too.
    CHECK(god_wrath_display_name("the fiery rage of Trog")
          != "the fiery rage of Trog");
    CHECK(god_wrath_display_name("an unrelated cause")
          == "an unrelated cause");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: death cause display maps orb identities",
                 "[zh-translation][backport][death-protocol]")
{
    backport_world world;
    you.your_name = "BackportTester";
    you.birth_time = 1599999900;
    you.last_keypress_time = chrono::system_clock::from_time_t(you.birth_time);
    you.species = SP_HUMAN;
    you.char_class = JOB_MONK;
    you.chr_class_name = get_job_name(you.char_class);
    you.where_are_you = BRANCH_DUNGEON;
    you.depth = 1;

    const string cause = "orb of destruction";
    scorefile_entry live(0, MID_NOBODY, KILLED_BY_BEAM, cause.c_str(), true);
    live.init(1600000000);
    const string serialized = live.raw_string();
    REQUIRE(!serialized.empty());
    CHECK(xlog_fields(serialized).str_field("kaux") == cause);

    scorefile_entry restored;
    REQUIRE(restored.parse(serialized));
    const string display =
        restored.death_description(scorefile_entry::DDV_VERBOSE);
    CHECK(display.find("毁灭法球") != string::npos);
    CHECK(xlog_fields(restored.raw_string()).str_field("kaux") == cause);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: projectile display localizes known identities and keeps unknown ones",
                 "[zh-translation][backport][projectile]")
{
    // A known missile root renders in the current language.
    const string arrow = T_("arrow");
    REQUIRE(arrow != "arrow");
    CHECK(projectile_display_name("arrow") == arrow);

    // Stable has no wind-blessed mechanic, so a composite identity is not
    // decomposed: it stays canonical.
    CHECK(projectile_display_name("wind-blessed arrow")
          == "wind-blessed arrow");

    // Unknown identities are never guessed at.
    CHECK(projectile_display_name("unknown projectile")
          == "unknown projectile");

    // English display keeps the canonical string.
    {
        const ScopedLangEn en;
        CHECK(projectile_display_name("wind-blessed arrow")
              == "wind-blessed arrow");
        CHECK(projectile_display_name("arrow") == "arrow");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: xom note renderer re-renders canonical shapes only",
                 "[zh-translation][backport][xom-notes]")
{
    // A real canonical payload round-trips through Note::describe: the
    // renderer translates it and the stored name is left untouched.
    const string canonical_count = "summons 3 friends";
    Note count_note(NOTE_XOM_EFFECT, 100, -1, canonical_count);
    const string expected = string(T_("XOM: ")) + make_stringf(T_("summons %d friends"), 3);
    CHECK(count_note.describe(false, false, true) == expected);
    CHECK(count_note.name == canonical_count);

    // Unknown or historical payloads stay byte-for-byte.
    const string unknown = "divine lightning + x bolts";
    Note unknown_note(NOTE_XOM_EFFECT, 100, -1, unknown);
    CHECK(unknown_note.describe(false, false, true).find(unknown) != string::npos);
    CHECK(unknown_note.name == unknown);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: corrupted level notes render only canonical typed payloads",
                 "[zh-translation][backport][corrupted-level-notes]")
{
    const string canonical = "Corrupted D:7";
    Note note(NOTE_MESSAGE, 0, 0, canonical, "corrupted level");
    note.place = level_id(BRANCH_DUNGEON, 7);

    SECTION("canonical producer note follows the display language")
    {
        const string expected = make_stringf(T_("Corrupted %s"),
                                             note.place.describe(true, true).c_str());
        REQUIRE(expected != canonical);
        CHECK(note.describe(false, false, true) == expected);
        {
            EnTranslationFixture english;
            CHECK(note.describe(false, false, true) == canonical);
        }
        CHECK(note.describe(false, false, true) == expected);
        CHECK(note.name == canonical);
        CHECK(note.desc == "corrupted level");
    }

    SECTION("historical unmarked snapshots remain unchanged")
    {
        note.desc.clear();
        CHECK(note.describe(false, false, true) == canonical);
    }

    SECTION("unknown payloads remain unchanged")
    {
        const string unknown = "Corrupted unknown level";
        note.name = unknown;
        CHECK(note.describe(false, false, true) == unknown);
        CHECK(note.name == unknown);
    }

    SECTION("invalid typed levels remain unchanged")
    {
        note.place.clear();
        CHECK(note.describe(false, false, true) == canonical);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: equipment notice template keeps both slots",
                 "[zh-translation][backport][protocol]")
{
    // Structure check for the catalog template the notice is built from: the
    // subject slot must survive so the code can pass a canonical subject.
    const string equip_template = C_("monster equip", "%1$s %2$s.");
    CHECK(equip_template != "%1$s %2$s.");
    CHECK(equip_template.find("%1$s") != string::npos);
    CHECK(equip_template.find("%2$s") != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: flooded substance catalog resolves to the same text as ooze",
                 "[zh-translation][backport][flood]")
{
    // Structure check only: the display sinks look the stored canonical
    // substance up through this context (plain key today). The producer itself
    // is exercised by the in-game flood messages, not by this case.
    CHECK(string(C_("flood substance", "ooze")) == string(T_("ooze")));
    {
        const ScopedLangEn english;
        CHECK(string(C_("flood substance", "ooze")) == "ooze");
    }
}

// Regression cases adapted from trunk PR #245.
#include "directn.h"
#include "describe.h"
#include "item-name.h"
#include "items.h"
#include "mon-info.h"
#include "monster.h"
#include "player-notices.h"
#include "viewgeom.h"
#include "mutation.h"
#include <sstream>

namespace {
void stage_b_player()
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
                 "stone stack display counts preserve identity and English quantities",
                 "[zh-translation][playtest-004][items]")
{
    init_properties();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (missile_type subtype : {MI_STONE, MI_LARGE_ROCK})
        {
            item_def item;
            item.base_type = OBJ_MISSILES;
            item.sub_type = subtype;
            item.quantity = 1;
            item.flags = ISFLAG_IDENTIFIED;
            const string basename = item.name(DESC_BASENAME);
            const string dbname = item.name(DESC_DBNAME);
            const string qualname = item.name(DESC_QUALNAME);
            item.quantity = 5;
            CHECK(item.name(DESC_DBNAME) == dbname);
            CHECK(item.name(DESC_BASENAME) == basename);
            CHECK(item.name(DESC_QUALNAME) == qualname);
            const string displayed = item.name(DESC_A);
            if (language == lang_t::ZH)
            {
                CHECK(displayed == "5块" + basename);
                CHECK(make_stringf(T_("Found %s."), displayed.c_str())
                      == "发现了5块" + basename + "。");
                CHECK(make_stringf(T_("You see here %s."), displayed.c_str())
                      == "你在这里看到5块" + basename + "。");
                CHECK(item.name(DESC_A, false, false, false, true)
                      == "五块" + basename);
            }
            else
            {
                CHECK(displayed == (subtype == MI_STONE ? "5 stones" : "5 large rocks"));
                CHECK(item.name(DESC_A, false, false, false, true)
                      == (subtype == MI_STONE ? "five stones" : "five large rocks"));
            }
            ScopedLangEn english_identity;
            CHECK(item.name(DESC_DBNAME)
                  == (subtype == MI_STONE ? "stone" : "large rock"));
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "unarmed hit chance describes body parts independently of weapon phrasing",
                 "[zh-translation][playtest-004][descriptions]")
{
    init_properties();
    init_mut_index();
    unwind_var<player> restore_player(you);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (species_type species : {SP_HUMAN, SP_FELID, SP_OCTOPODE})
        {
            stage_b_player();
            you.species = species;
            you.duration[DUR_BLIND] = 1;
            ostringstream displayed;
            describe_hit_chance(73, displayed, nullptr, true, 2);
            const string text = displayed.str();
            CHECK(text.find("73%") != string::npos);
            CHECK(text.find(you.hand_name(true)) != string::npos);
            if (language == lang_t::ZH)
            {
                CHECK(text.find("你用" + you.hand_name(true) + "攻击的命中率") != string::npos);
                CHECK(text.find("使用手") == string::npos);
            }
            else
                CHECK(text.find("% to hit with your ") != string::npos);
        }
    }
}

#ifdef USE_TILE_LOCAL
#include "tilereg-dgn.h"

TEST_CASE_METHOD(ZhTranslationFixture,
                 "local tiles dungeon tooltip translates movement and description actions",
                 "[zh-translation][playtest-004][tiles]")
{
    init_properties();
    unwind_var<player> restore_player(you);
    stage_b_player();
    you.on_current_level = true;
    you.wizard_vision = true;
    you.current_vision = 8;
    you.equipment.update();
    const coord_def target = you.pos() + coord_def(1, 0);
    unwind_var<dungeon_feature_type> restore_floor(env.grid(target), DNGN_FLOOR);
    unwind_var<unsigned short> restore_monster(env.mgrid(target), NON_MONSTER);
    unwind_var<map_cell> restore_map(env.map_knowledge(target), map_cell());
    env.map_knowledge(target).set_feature(DNGN_FLOOR);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        string displayed;
        REQUIRE(tile_dungeon_tip(target, displayed));
        CHECK(displayed == string(T_("[L-Click] Move")) + "\n" + T_("[R-Click] Describe"));
        CHECK(displayed.find(language == lang_t::ZH ? "[左键]" : "[L-Click]") != string::npos);
        if (language == lang_t::ZH)
            CHECK(displayed.find("Describe") == string::npos);
    }
}
#endif

TEST_CASE_METHOD(ZhTranslationFixture,
                 "corpse display joins species without changing persisted names",
                 "[zh-translation][playtest-round2][items]")
{
    init_monsters();
    init_properties();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (monster_type species : {MONS_BALL_PYTHON, MONS_BAT})
        {
            item_def corpse;
            corpse.base_type = OBJ_CORPSES;
            corpse.quantity = 1;
            corpse.mon_type = species;
            corpse.orig_monnum = species;
            for (int form : {CORPSE_BODY, CORPSE_SKELETON})
            {
                corpse.sub_type = form;
                const string body = T_(form == CORPSE_BODY ? "corpse" : "skeleton");
                const string name = mons_type_name(species, DESC_PLAIN);
                CHECK(corpse.name(DESC_PLAIN)
                      == name + (language == lang_t::ZH ? "" : " ") + body);
                const string identity = corpse.name(DESC_DBNAME);
                corpse.props[CORPSE_NAME_KEY] = "CustomName";
                corpse.props[CORPSE_NAME_TYPE_KEY] = static_cast<int64_t>(0);
                CHECK(corpse.name(DESC_PLAIN).find("CustomName") != string::npos);
                CHECK(get_corpse_name(corpse) == "CustomName");
                CHECK(corpse.name(DESC_DBNAME) == identity);
                corpse.props.erase(CORPSE_NAME_KEY);
                corpse.props.erase(CORPSE_NAME_TYPE_KEY);
                CHECK(corpse.orig_monnum == species);
            }
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "encounter lists keep English count spacing and join Chinese conjunctions",
                 "[zh-translation][playtest-round2][messages]")
{
    init_monsters();
    unwind_var<player> restore_player(you);
    stage_b_player();
    // The production notice consumer expects already-visible monsters. Use
    // the same lightweight wizard-vision setup as the other consumer tests;
    // no allocator or dungeon cells are changed by these stack-local actors.
    you.on_current_level = true;
    you.wizard_vision = true;
    you.current_vision = LOS_DEFAULT_RANGE;
    monster kobold, rat, second_rat;
    kobold.type = MONS_KOBOLD;
    rat.type = second_rat.type = MONS_RAT;
    kobold.set_position(you.pos() + coord_def(1, 0));
    rat.set_position(you.pos() + coord_def(0, 1));
    second_rat.set_position(you.pos() + coord_def(1, 1));
    REQUIRE(you.can_see(kobold));
    REQUIRE(you.can_see(rat));
    REQUIRE(you.can_see(second_rat));
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const string pair = describe_monsters_condensed({&kobold, &rat});
        if (language == lang_t::ZH)
        {
            CHECK(pair.find("和") != string::npos);
            CHECK(pair.find(' ') == string::npos);
            CHECK(describe_monsters_condensed({&rat, &second_rat}).find(' ')
                  == string::npos);
        }
        else
        {
            CHECK(pair.find(" and ") != string::npos);
            CHECK(describe_monsters_condensed({&rat, &second_rat}) == "2 rats");
        }
        CHECK(kobold.type == MONS_KOBOLD);
        CHECK(rat.type == MONS_RAT);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "feature notes localize punctuation without rewriting saved snapshots",
                 "[zh-translation][playtest-round2][notes]")
{
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const string feature = language == lang_t::ZH ? "褪色祭坛" : "a faded altar";
        const Note note(NOTE_SEEN_FEAT, 0, 0, feature + ".");
        CHECK(note.describe(false, false)
              == make_stringf(C_("feature note", "Found %s."), feature.c_str()));
        CHECK(note.name == feature + ".");
        const Note historic(NOTE_SEEN_FEAT, 0, 0, "historic feature");
        CHECK(historic.describe(false, false) == string(T_("Found ")) + historic.name);
        CHECK(historic.name == "historic feature");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "verbose score date grammar and punctuation preserve canonical xlog",
                 "[zh-translation][playtest-round2][protocol]")
{
    const string raw = "v=0.34.1:name=TilesReview:race=Human:cls=Fighter:xl=1:"
        "sk=Fighting:title=Adventurer:br=D:lvl=5:god=No God:ktyp=mon:"
        "killer=an orc:start=20261003120000S:end=20261003130000S";
    scorefile_entry saved;
    REQUIRE(saved.parse(raw));
    string english_birth, english_place;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const string birth = saved.character_description(scorefile_entry::DDV_VERBOSE);
        const string place = saved.death_place(scorefile_entry::DDV_VERBOSE);
        if (language == lang_t::ZH)
        {
            CHECK(birth.find("2026年11月03日") < birth.find("人类战士"));
            CHECK(place.find("……") == 0);
            CHECK(place.find("。") != string::npos);
            CHECK(place.find("...") == string::npos);
            ScopedLangEn canonical;
            CHECK(saved.character_description(scorefile_entry::DDV_VERBOSE) == english_birth);
            CHECK(saved.death_place(scorefile_entry::DDV_VERBOSE) == english_place);
        }
        else
        {
            CHECK(birth.find("Began as a Human Fighter on 2026-11-03.") != string::npos);
            CHECK(place.find("... ") == 0);
            english_birth = birth;
            english_place = place;
        }
        CHECK(saved.raw_string() == raw);
        CHECK(saved.get_fields().str_field("race") == "Human");
        CHECK(saved.get_fields().str_field("cls") == "Fighter");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "derived monster display joins suffixes and retains names and hydra head counts",
                 "[zh-translation][playtest-round3][monster-info]")
{
    init_monsters();
    const vector<pair<monster_type, const char*>> forms = {
        {MONS_ZOMBIE, "zombie"}, {MONS_DRAUGR, "draugr"},
        {MONS_SIMULACRUM, "simulacrum"}
    };
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto& form : forms)
        {
            monster_info ordinary(form.first, MONS_KOBOLD);
            const string displayed = ordinary.full_name(DESC_PLAIN);
            const string species = mons_type_name(MONS_KOBOLD, DESC_PLAIN);
            const string suffix = T_(form.second);
            CHECK(displayed.find(species) != string::npos);
            CHECK(displayed.find(suffix) != string::npos);
            CHECK(displayed.find(species + " " + suffix)
                  == (language == lang_t::ZH ? string::npos : 0));
            CHECK(displayed.find(species + suffix)
                  == (language == lang_t::ZH ? 0 : string::npos));

            ordinary.mname = "Legacy Name";
            CHECK(ordinary.full_name(DESC_A).find("Legacy Name") != string::npos);
            CHECK(ordinary.proper_name() == "Legacy Name");
            CHECK(ordinary.mname == "Legacy Name");
            CHECK(ordinary.type == form.first);
            CHECK(ordinary.base_type == MONS_KOBOLD);

            monster_info hydra(form.first, MONS_HYDRA);
            for (int heads : {1, 10, 11})
            {
                hydra.num_heads = heads;
                const string name = hydra.full_name(DESC_PLAIN);
                INFO(name);
                if (language == lang_t::ZH)
                {
                    CHECK(name.find(" " + suffix) == string::npos);
                    CHECK(name.find(heads == 1 ? "（一头）"
                                    : heads == 10 ? "（十头）" : "（11头）")
                          != string::npos);
                }
                else
                {
                    CHECK(name.find(heads == 1 ? "one-headed hydra "
                                    : heads == 10 ? "ten-headed hydra "
                                                  : "11-headed hydra ") == 0);
                    CHECK(name.find(suffix) != string::npos);
                }
                CHECK(hydra.num_heads == heads);
                CHECK(hydra.base_type == MONS_HYDRA);
            }
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "prefix dart brands join Chinese names without changing lookup or terse forms",
                 "[zh-translation][playtest-round3][items]")
{
    init_properties();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (special_missile_type brand : {SPMSL_POISONED, SPMSL_CURARE,
                                           SPMSL_BLINDING, SPMSL_FRENZY})
        {
            item_def dart;
            dart.base_type = OBJ_MISSILES;
            dart.sub_type = MI_DART;
            dart.brand = brand;
            dart.quantity = 1;
            dart.flags = ISFLAG_IDENTIFIED;
            const string noun = missile_name(MI_DART);
            const string modifier = missile_brand_name(dart, MBN_NAME);
            const string displayed = dart.name(DESC_PLAIN);
            CHECK(displayed.find(modifier) == 0);
            CHECK(displayed.substr(displayed.size() - noun.size()) == noun);
            CHECK(displayed.find(modifier + " " + noun)
                  == (language == lang_t::ZH ? string::npos : 0));
            CHECK(dart.name(DESC_DBNAME) == noun);
            CHECK(dart.name(DESC_BASENAME) == noun);
            const string terse = dart.name(DESC_PLAIN, true);
            CHECK(terse.find(noun) == 0);
            CHECK(terse.find(" (") != string::npos);
            CHECK(terse.find(missile_brand_name(dart, MBN_TERSE)) != string::npos);
            {
                ScopedLangEn canonical;
                CHECK(dart.name(DESC_DBNAME) == "dart");
                CHECK(dart.name(DESC_BASENAME) == "dart");
            }
            CHECK(dart.brand == brand);
            CHECK(dart.sub_type == MI_DART);
            CHECK(dart.quantity == 1);
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "visible monster equipment joins weapon armour and branded darts in both languages",
                 "[zh-translation][playtest-round3][equipment]")
{
    init_properties();
    init_monsters();
    // A visible monster_info inventory is the snapshot consumed by targeting
    // descriptions. Exercise the complete public producer, including the
    // weapon action, armour list, missile naming, and final conjunction.
    monster_info target(MONS_KOBOLD);
    for (mon_inv_type slot : {MSLOT_WEAPON, MSLOT_ARMOUR, MSLOT_MISSILE})
    {
        target.inv[slot].reset(new item_def);
        target.inv[slot]->quantity = 1;
        target.inv[slot]->flags = ISFLAG_IDENTIFIED;
    }
    item_def& weapon = *target.inv[MSLOT_WEAPON];
    weapon.base_type = OBJ_WEAPONS;
    weapon.sub_type = WPN_DAGGER;
    item_def& armour = *target.inv[MSLOT_ARMOUR];
    armour.base_type = OBJ_ARMOUR;
    armour.sub_type = ARM_ROBE;
    item_def& missile = *target.inv[MSLOT_MISSILE];
    missile.base_type = OBJ_MISSILES;
    missile.sub_type = MI_DART;
    missile.brand = SPMSL_CURARE;
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const string displayed = get_monster_equipment_desc(target, DESC_FULL);
        CHECK(displayed.find(weapon.name(DESC_A)) != string::npos);
        CHECK(displayed.find(armour.name(DESC_A)) != string::npos);
        CHECK(displayed.find(missile.name(DESC_PLAIN)) != string::npos);
        if (language == lang_t::ZH)
        {
            const string conjunction = C_("monster equipment", " and ");
            const size_t join = displayed.find(conjunction);
            REQUIRE(join != string::npos);
            REQUIRE(join > 0);
            REQUIRE(join + conjunction.size() < displayed.size());
            CHECK(displayed[join - 1] != ' ');
            CHECK(displayed[join + conjunction.size()] != ' ');
            CHECK(displayed.find(" wielding ") == string::npos);
            CHECK(displayed.find(" and ") == string::npos);
        }
        else
        {
            CHECK(displayed.find("wielding ") != string::npos);
            CHECK(displayed.find(" and ") != string::npos);
            CHECK(displayed.find("curare-tipped darts") != string::npos);
        }
        CHECK(weapon.sub_type == WPN_DAGGER);
        CHECK(armour.sub_type == ARM_ROBE);
        CHECK(missile.sub_type == MI_DART);
        CHECK(missile.brand == SPMSL_CURARE);
        CHECK(weapon.quantity == 1);
        CHECK(armour.quantity == 1);
        CHECK(missile.quantity == 1);
        ScopedLangEn canonical;
        CHECK(weapon.name(DESC_DBNAME) == "dagger");
        CHECK(armour.name(DESC_DBNAME) == "robe");
        CHECK(missile.name(DESC_DBNAME) == "dart");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "wizard item origin has no trailing space before its terminator",
                 "[zh-translation][playtest-004][items]")
{
    init_properties();
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        item_def item;
        item.base_type = OBJ_WEAPONS;
        item.sub_type = WPN_DAGGER;
        item.quantity = 1;
        item.flags = ISFLAG_IDENTIFIED;
        item.orig_place = level_id(BRANCH_DUNGEON, 3);
        item.orig_monnum = -AQ_WIZMODE;
        REQUIRE(origin_describable(item));
        const string conjured = origin_desc(item);
        REQUIRE_FALSE(conjured.empty());
        CHECK(conjured.back() != ' ');
        // Stable description uses an ASCII terminator on this existing path.
        const string terminator = ".";
        CHECK(get_item_description(item).find(conjured + terminator) != string::npos);
        if (language == lang_t::EN)
            CHECK(conjured == "Your wizardly powers created it on level 3 of the Dungeon");
        CHECK(item.orig_monnum == -AQ_WIZMODE);
        CHECK(item.orig_place == level_id(BRANCH_DUNGEON, 3));
    }
}
