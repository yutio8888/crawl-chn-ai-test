#include "catch_amalgamated.hpp"
#include "AppHdr.h"

#include <limits>

#include "cloud.h"
#include "dgn-overview.h"
#include "exclude.h"
#include "i18n.h"
#include "lang-en-guard.h"
#include "stringutil.h"
#include "mon-util.h"
#include "player.h"
#include "tags.h"
#include "travel.h"
#include "unwind.h"
#include "test_zh_fixture.h"

extern map<level_id, string> level_exclusions;
extern map<level_id, string> level_annotations;
extern set<pair<string, level_id>> auto_unique_annotations;

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Exclusions separate stored identities from displayed summaries",
                 "[zh-translation][webtiles-playtest][exclusions]")
{
    init_monsters();
    unwind_var<set<pair<string, level_id>>> uniques(auto_unique_annotations, {});
    const level_id level(BRANCH_DUNGEON, 3);
    exclude_set source;
    source.add_exclude(coord_def(10, 10), 0, false, "floor");
    CHECK(source.get_exclusion_desc(level) == "exclusion: floor");
    CHECK(source.get_exclusion_desc(level, true) == "禁区：地板");
    source.add_exclude(coord_def(11, 10), 0, false, "floor");
    CHECK(source.get_exclusion_desc(level) == "exclusion: 2 floors");
    CHECK(source.get_exclusion_desc(level, true) == "禁区：2个地板");

    SECTION("legacy names survive save roundtrip and group with canonical names")
    {
        source.clear();
        source.add_exclude(coord_def(10, 10), 0, true, "oklob plant");
        const string legacy = mons_type_name(MONS_OKLOB_PLANT, DESC_PLAIN);
        source.add_exclude(coord_def(11, 10), 0, true, legacy);
        vector<unsigned char> bytes;
        writer output(&bytes);
        marshallExcludes(output, source);
        reader input(bytes);
        input.setMinorVersion(TAG_MINOR_VERSION);
        exclude_set restored;
        unmarshallExcludes(input, TAG_MINOR_VERSION, restored);
        CHECK(restored.get_exclude_root(coord_def(11, 10))->desc == legacy);
        CHECK(restored.get_exclusion_desc(level) == "exclusion: 2 oklob plants");
        CHECK(restored.get_exclusion_desc(level, true) == "禁区：2个" + legacy);
        CHECK(restored.get_exclude_root(coord_def(11, 10))->desc == legacy);
    }
    SECTION("generic water covers both shallow and deep terrain")
    {
        source.clear();
        source.add_exclude(coord_def(10, 10), 0, false, "water");
        CHECK(source.get_exclusion_desc(level) == "exclusion: water");
        CHECK(source.get_exclusion_desc(level, true) == "禁区：水");
    }
    SECTION("cloud identities are recognised exactly in old and new saves")
    {
        const string english = cloud_type_name_en(CLOUD_FIRE, true) + " cloud";
        const string legacy = make_stringf(T_("%s cloud"),
                                           cloud_type_name(CLOUD_FIRE, true).c_str());
        CHECK(is_cloud_exclusion(english));
        CHECK(is_cloud_exclusion(legacy));
        CHECK_FALSE(is_cloud_exclusion("my cloud garden!"));
        source.clear();
        source.add_exclude(coord_def(10, 10), 0, true, english);
        source.add_exclude(coord_def(11, 10), 0, true, legacy);
        CHECK(source.get_exclusion_desc(level).empty());
        CHECK(source.get_exclusion_desc(level, true).empty());
    }
    SECTION("unique deduplication uses the requested level and legacy identity")
    {
        source.clear();
        source.add_exclude(coord_def(10, 10), 0, false, "Sigmund");
        auto_unique_annotations.emplace(mons_type_name(MONS_SIGMUND, DESC_PLAIN), level);
        CHECK(source.get_exclusion_desc(level, true).empty());
        CHECK_FALSE(source.get_exclusion_desc(level_id(BRANCH_DUNGEON, 4), true).empty());
    }
    SECTION("unknown custom descriptions and unnamed exclusions")
    {
        source.clear();
        source.add_exclude(coord_def(10, 10), 0, false, "custom 云 cloud !");
        CHECK(source.get_exclusion_desc(level, true) == "禁区：custom 云 cloud !");
        source.clear();
        source.add_exclude(coord_def(10, 10), 0, false, "");
        CHECK(source.get_exclusion_desc(level) == "1 exclusion");
        CHECK(source.get_exclusion_desc(level, true) == "1个禁区");
        source.add_exclude(coord_def(11, 10), 0, false, "");
        CHECK(source.get_exclusion_desc(level) == "2 exclusions");
        CHECK(source.get_exclusion_desc(level, true) == "2个禁区");
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "Overview uses structured exclusions and preserves absent-cache fallback",
                 "[zh-translation][webtiles-playtest][exclusions]")
{
    init_monsters();
    unwind_var<player> player_state(you);
    you.where_are_you = BRANCH_DUNGEON;
    you.depth = 3;
    unwind_var<TravelCache> cache(travel_cache, TravelCache());
    unwind_var<exclude_set> exclusions(curr_excludes, exclude_set());
    unwind_var<map<level_id, string>> summaries(level_exclusions, {});
    unwind_var<map<level_id, string>> notes(level_annotations, {});
    unwind_var<set<pair<string, level_id>>> uniques(auto_unique_annotations, {});
    const level_id current = level_id::current();
    const level_id other(BRANCH_DUNGEON, 4);
    level_exclusions[current] = "exclusion: stale";
    curr_excludes.add_exclude(coord_def(10, 10), 0, false, "floor");
    CHECK(get_level_annotation(current, false, true) == "禁区：地板");
    CHECK(level_exclusions[current] == "exclusion: stale");
    level_exclusions[other] = "legacy custom !";
    CHECK(get_level_annotation(other, false, true) == "legacy custom !");
    travel_cache.get_level_info(other).update_excludes();
    CHECK(get_level_annotation(other, false, true) == "禁区：地板");
    curr_excludes.clear();
    travel_cache.get_level_info(other).update_excludes();
    CHECK(get_level_annotation(other, false, true).empty());
}

TEST_CASE("Experience progress stays bounded during pending level-ups",
          "[zh-translation][webtiles-playtest][experience]")
{
    unwind_var<player> player_state(you);
    you = player();
    you.species = SP_HUMAN;
    you.experience_level = 7;
    const unsigned int current = exp_needed(7);
    const unsigned int next = exp_needed(8);
    for (unsigned int experience : {0U, current - 1, current})
    {
        you.experience = experience;
        CHECK(get_exp_progress() == 0);
    }
    you.experience = current + (next - current) / 2;
    CHECK(get_exp_progress() == int((you.experience - current) * 100 / (next - current)));
    for (unsigned int experience : {next, exp_needed(10), std::numeric_limits<unsigned int>::max()})
    {
        you.experience = experience;
        CHECK(get_exp_progress() == 100);
    }
    you.experience_level = you.get_max_xl();
    CHECK(get_exp_progress() == 0);
}
