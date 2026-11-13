#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "artefact.h"
#include "describe.h"
#include "directn.h"
#include "dungeon-feature-type.h"
#include "dungeon.h"
#include "database.h"
#include "env.h"
#include "i18n.h"
#include "item-status-flag-type.h"
#include "map-cell.h"
#include "mon-info.h"
#include "monster-type.h"
#include "mutation.h"
#include "player.h"
#include "skill-type.h"
#include "stringutil.h"
#include "unwind.h"

#include "item-prop.h"
#include "status.h"
#include "test_zh_fixture.h"
#include <sstream>

namespace
{
item_def make_test_randart()
{
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.flags = ISFLAG_RANDART | ISFLAG_IDENTIFIED;

    CrawlVector &props = item.props[ARTEFACT_PROPS_KEY]
                              .new_vector(SV_SHORT);
    props.resize(ART_PROPERTIES);
    props.set_max_size(ART_PROPERTIES);
    for (vec_size i = 0; i < ART_PROPERTIES; ++i)
        props[i].get_short() = 0;

    artefact_set_property(item, ARTP_FIRE, -1);
    artefact_set_property(item, ARTP_STRENGTH, 9);
    artefact_set_property(item, ARTP_DEXTERITY, 2);
    return item;
}

bool any_line_contains(const vector<string> &lines, const string &needle)
{
    return any_of(lines.begin(), lines.end(), [&](const string &line)
    {
        return line.find(needle) != string::npos;
    });
}
}

TEST_CASE("_monster_habitat_description outputs correct descriptions", "[single-file]")
{
    init_monsters();

    SECTION("Amphibious monsters append correct string")
    {
        const auto info = monster_info(MONS_FRILLED_LIZARD, MONS_FRILLED_LIZARD);

        const string habitat_info = _monster_habitat_description(info);

        REQUIRE(habitat_info == "It can travel through water.\n");
    }

    SECTION("Lava monsters output correct string")
    {
        const auto info = monster_info(MONS_SALAMANDER, MONS_SALAMANDER);

        const string habitat_info = _monster_habitat_description(info);

        REQUIRE(habitat_info == "It can travel through lava.\n");
    }

    SECTION("Monsters with other pronouns output correct string")
    {
        const auto info = monster_info(MONS_CEREBOV, MONS_CEREBOV);

        const string habitat_info = _monster_habitat_description(info);

        REQUIRE(habitat_info == "They can travel through water.\n");
    }

    SECTION("Other monsters output nothing")
    {
        const auto info = monster_info(MONS_KOBOLD, MONS_KOBOLD);

        const string habitat_info = _monster_habitat_description(info);

        REQUIRE(habitat_info == "");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "randart property descriptions survive i18n cache resets",
                 "[zh-translation][describe]")
{
    const item_def item = make_test_randart();
    vector<string> lines;
    desc_randart_props(item, lines);

    REQUIRE(any_line_contains(lines, "使你容易受到火焰"));
    REQUIRE(any_line_contains(lines, "影响你的力量（+9）"));
    REQUIRE(any_line_contains(lines, "影响你的敏捷（+2）"));

    i18n_cache_clear();
    const char *cache_churn[] =
    {
        "cache churn 0",
        "cache churn 1",
        "No target in view!",
        "cache churn 3",
        "No target in range!",
        "cache churn 5",
        "No targets found!",
    };
    for (const char *key : cache_churn)
        T_(key);

    lines.clear();
    desc_randart_props(item, lines);

    REQUIRE(any_line_contains(lines, "使你容易受到火焰"));
    REQUIRE(any_line_contains(lines, "影响你的力量（+9）"));
    REQUIRE(any_line_contains(lines, "影响你的敏捷（+2）"));
    REQUIRE_FALSE(any_line_contains(lines, T_("No target in view!")));
    REQUIRE_FALSE(any_line_contains(lines, T_("No target in range!")));
    REQUIRE_FALSE(any_line_contains(lines, T_("No targets found!")));
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "skill descriptions resolve via canonical English TextDB keys",
                 "[zh-translation][describe]")
{
    const string desc = get_skill_description(SK_AXES, true);

    // Title is the localized display name (skill_name) while the body must
    // come from the zh TextDB layer keyed by the canonical English skill
    // name; a localized lookup key would produce a blank description.
    REQUIRE(desc.find("斧类") != string::npos);
    REQUIRE(desc.find("挥动斧类武器能同时劈砍周围一圈多个敌人") != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "feature descriptions resolve via English display-phrase keys",
                 "[zh-translation][describe]")
{
    // zh features.txt is keyed by English display phrases ("The floor"), so
    // a localized lookup key would produce a blank description.
    REQUIRE(getLongDescription("地面").empty());

    // Exercise the production consumer get_feature_desc() on a mapped floor.
    // The test host has no generated level, so mark the cell as not part of
    // any vault (level gen normally fills level_map_ids with INVALID_MAP_INDEX).
    const coord_def pos(20, 22);
    const coord_def old_pos = you.pos();
    const dungeon_feature_type old_grid = env.grid(pos);
    const map_cell old_knowledge = env.map_knowledge(pos);
    const unsigned int old_map_id = env.level_map_ids(pos);
    you.set_position(pos);
    env.grid(pos) = DNGN_FLOOR;
    env.map_knowledge(pos).set_feature(DNGN_FLOOR);
    env.level_map_ids(pos) = INVALID_MAP_INDEX;

    describe_info inf;
    get_feature_desc(pos, inf, false);

    env.level_map_ids(pos) = old_map_id;
    env.map_knowledge(pos) = old_knowledge;
    env.grid(pos) = old_grid;
    you.set_position(old_pos);

    REQUIRE(inf.title.find("地板") != string::npos);
    REQUIRE(inf.body.str().find("地面") != string::npos);

    // describe_feature_type() key-building seam resolves through the zh layer.
    const string en_key = feature_description_en(DNGN_FLOOR);
    REQUIRE(en_key == "the floor");
    REQUIRE(getLongDescription(en_key).find("地面") != string::npos);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "dynamic mutation bonuses pair parentheses in both languages",
                 "[zh-translation][r7-mutation]")
{
    init_mut_index();
    unwind_var<player> restore_player(you);
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (mutation_type mut : {MUT_ICEMAIL, MUT_CONDENSATION_SHIELD,
                MUT_SANGUINE_ARMOUR, MUT_STONE_BODY, MUT_PROTEAN_GRACE})
        {
            you = player();
            you.species = mut == MUT_STONE_BODY ? SP_GARGOYLE : SP_HUMAN;
            you.mutation[mut] = 1;
            const string text = mutation_desc(mut, 1, false);
            CAPTURE(language, mut, text);
            const auto occurrences = [&text](const string &token) {
                size_t count = 0;
                size_t pos = 0;
                while ((pos = text.find(token, pos)) != string::npos)
                {
                    ++count;
                    pos += token.size();
                }
                return count;
            };
            if (language == lang_t::ZH)
            {
                CHECK(occurrences("（") > 0);
                CHECK(occurrences("（") == occurrences("）"));
            }
            else
            {
                CHECK(occurrences("（") == 0);
                CHECK(occurrences("(") > 0);
                CHECK(occurrences("(") == occurrences(")"));
            }
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "resistance protection sentences preserve English and localize punctuation",
                 "[zh-translation][describe][r5-resistance]")
{
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto prop : {ARTP_FIRE, ARTP_COLD, ARTP_NEGATIVE_ENERGY})
        {
            for (int level : {1, 2, 3})
            {
                CAPTURE(language, prop, level);
                item_def item = make_test_randart();
                artefact_set_property(item, ARTP_FIRE, 0);
                artefact_set_property(item, prop, level);
                vector<string> lines;
                desc_randart_props(item, lines);
                const string element = prop == ARTP_FIRE ? "fire"
                    : prop == ARTP_COLD ? "cold" : "negative energy";
                const string prefix = level == 1 ? "It protects you from "
                    : level == 2 ? "It greatly protects you from "
                                 : "It renders you almost immune to ";
                const string english = prefix + element + ".";
                if (language == lang_t::EN)
                    REQUIRE(any_line_contains(lines, english));
                else
                {
                    const string translated_element = C_("element", element.c_str());
                    bool found = false;
                    for (const string &line : lines)
                    {
                        if (line.find(translated_element) == string::npos)
                            continue;
                        found = true;
                        CHECK(ends_with(line, "。"));
                        CHECK(line.find('.') == string::npos);
                        CHECK(line.find(element) == string::npos);
                    }
                    REQUIRE(found);
                }
            }
        }
    }
}

TEST_CASE("Blind hit chance qualifiers name the actual distance",
          "[zh-translation][r20][hit-chance-distance]")
{
    init_properties();
    init_duration_index();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.hp = you.hp_max = 20;
    item_def bow;
    bow.base_type = OBJ_WEAPONS;
    bow.sub_type = WPN_LONGBOW;
    bow.quantity = 1;
    bow.flags = ISFLAG_IDENTIFIED;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (bool armed : {false, true})
        for (bool blind : {false, true})
        for (int distance : {1, 3})
        {
            you.duration[DUR_BLIND] = blind ? 10 : 0;
            const string name = armed
                ? bow.name(DESC_YOUR, false, false, false)
                : you.hand_name(true);
            ostringstream actual;
            describe_hit_chance(65, actual, armed ? &bow : nullptr,
                                true, distance);
            string expected;
            if (language == lang_t::ZH)
            {
                expected = armed ? name + "的命中率约为65%"
                    : "你用" + name + "攻击的命中率约为65%";
                if (blind)
                {
                    expected += "（你失明时，在距离为"
                        + to_string(distance) + "的情况下）";
                }
            }
            else
            {
                expected = "about 65% to hit with "
                    + (armed ? name : "your " + name);
                if (blind)
                {
                    expected += " (while you are blinded and from distance "
                        + to_string(distance) + ")";
                }
            }
            CAPTURE(language, armed, blind, distance);
            CHECK(actual.str() == expected);
        }
    }
}

TEST_CASE("MP mutation display names follow the resource term without changing identities",
          "[zh-translation][r20][mp-resource-names]")
{
    init_mut_index();
    struct mutation_case
    {
        mutation_type type;
        const char* english;
        const char* chinese;
    };
    const mutation_case cases[] = {
        {MUT_HIGH_MAGIC, "high MP", "高法力"},
        {MUT_LOW_MAGIC, "low MP", "低法力"},
        {MUT_MANA_LINK, "magic link", "法力链接"},
        {MUT_MP_WANDS, "MP-powered wands", "魔杖消耗法力"},
    };
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto& row : cases)
        {
            CAPTURE(language, row.english);
            CHECK(string(mutation_name_en(row.type)) == row.english);
            CHECK(string(mutation_name(row.type))
                  == (language == lang_t::ZH ? row.chinese : row.english));
        }
    }
}
