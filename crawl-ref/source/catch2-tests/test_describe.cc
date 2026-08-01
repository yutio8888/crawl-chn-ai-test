#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "artefact.h"
#include "describe.h"
#include "i18n.h"
#include "item-status-flag-type.h"
#include "mon-info.h"
#include "monster-type.h"
#include "skill-type.h"

#include "test_zh_fixture.h"

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
