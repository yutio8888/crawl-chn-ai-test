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
