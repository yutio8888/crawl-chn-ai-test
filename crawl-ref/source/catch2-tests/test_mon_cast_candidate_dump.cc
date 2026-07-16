#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "fork-message-overlay.h"
#include "monspell_candidate_artifact.h"
#include "mon-place.h"
#include "mon-util.h"
#include "spl-util.h"

#include <cstdlib>
#include <fstream>
#include <iterator>
#include <set>

namespace
{
namespace mccd = mon_cast_candidate_dump;
namespace mcmk = mon_cast_message_keys;

mcmk::recipe_input input_for(const mccd::scenario &scenario)
{
    mcmk::recipe_input input;
    input.spell_name = "Magic Dart";
    input.monster_type = "orc wizard";
    input.monster_species = "orc";
    input.monster_genus = "humanoid";
    input.category_bits = scenario.category_bits;
    input.humanoid = scenario.humanoid;
    input.at_least_human_intelligence =
        scenario.at_least_human_intelligence;
    input.hoarfrost_finale = scenario.hoarfrost_finale;
    input.targeted = scenario.targeted;
    input.visible_beam = scenario.visible_beam;
    return input;
}

std::set<std::string> recipe_expressions(const mcmk::recipe_input &input)
{
    std::set<std::string> result;
    for (const mcmk::key_expression &expression :
         mcmk::build_key_recipe(input).candidates)
    {
        result.insert(mccd::symbolic_expression(expression));
    }
    return result;
}

const mccd::lookup_expression *find_lookup(
    const mccd::candidate_dump &dump, const std::string &expression)
{
    for (const mccd::lookup_expression &item : dump.lookup_expressions)
    {
        if (item.expression == expression)
            return &item;
    }
    return nullptr;
}
}

TEST_CASE("candidate dump scenario cover contains every recipe branch",
          "[mon-cast-candidate-dump][phase1]")
{
    std::set<std::string> cover;
    const std::vector<mccd::scenario> scenarios = mccd::scenario_cover();
    REQUIRE(scenarios.size() == 6);
    for (const mccd::scenario &scenario : scenarios)
    {
        const std::set<std::string> expressions =
            recipe_expressions(input_for(scenario));
        cover.insert(expressions.begin(), expressions.end());
    }

    for (uint32_t bits = 0; bits < 32; ++bits)
    {
        for (unsigned booleans = 0; booleans < 32; ++booleans)
        {
            mcmk::recipe_input input = input_for(mccd::scenario());
            input.category_bits = bits;
            input.humanoid = booleans & 1U;
            input.at_least_human_intelligence = booleans & 2U;
            input.hoarfrost_finale = booleans & 4U;
            input.targeted = booleans & 8U;
            input.visible_beam = booleans & 16U;
            const std::set<std::string> expressions =
                recipe_expressions(input);
            CAPTURE(bits, booleans);
            for (const std::string &expression : expressions)
                CHECK(cover.count(expression) == 1);
        }
    }
}

TEST_CASE("candidate dump is sorted deterministic and records production lookup attempts",
          "[mon-cast-candidate-dump][phase1]")
{
    fork_message_overlay::reset_monspell_overlay_diagnostics_for_test();
    const std::vector<mccd::monster_fragments> monsters = {
        { "orc wizard", "orc", "orc" },
        { "the Enchantress", "spriggan", "spriggan" },
    };
    const std::vector<std::string> spells = { "Magic Dart", "Fireball" };
    const mccd::candidate_dump first =
        mccd::build_candidate_dump(monsters, spells, 3);
    fork_message_overlay::reset_monspell_overlay_diagnostics_for_test();
    const mccd::candidate_dump second =
        mccd::build_candidate_dump(monsters, spells, 3);
    fork_message_overlay::reset_monspell_overlay_diagnostics_for_test();

    CHECK(first.schema_version == 1);
    CHECK(first.completeness == "closed_world_upper_bound");
    CHECK(first.valid);
    CHECK(first.monster_type_count == 3);
    CHECK(first.spell_count == 2);
    CHECK(first.monster_tuple_count == 2);
    CHECK(first.monster_spell_tuple_count == 4);
    CHECK(first.scenario_count == 6);
    CHECK(first.base_expression_count == first.base_expressions.size());
    CHECK(first.lookup_expression_count == first.lookup_expressions.size());
    CHECK(first.lookup_expression_count == first.base_expression_count * 3);
    CHECK(first.lookup_attempt_count == first.base_expression_count * 4);
    CHECK(std::is_sorted(first.base_expressions.begin(),
                         first.base_expressions.end()));
    CHECK(std::adjacent_find(first.base_expressions.begin(),
                             first.base_expressions.end())
          == first.base_expressions.end());

    const mccd::lookup_expression *normal =
        find_lookup(first, "magic dart orc wizard cast");
    const mccd::lookup_expression *unseen =
        find_lookup(first, "unseen magic dart orc wizard cast");
    const mccd::lookup_expression *silent =
        find_lookup(first, "silent magic dart orc wizard cast");
    REQUIRE(normal != nullptr);
    REQUIRE(unseen != nullptr);
    REQUIRE(silent != nullptr);
    CHECK(normal->attempts == std::vector<std::string>{
        "normal", "silent_unprefixed_fallback" });
    CHECK(unseen->attempts == std::vector<std::string>{ "unseen" });
    CHECK(silent->attempts
          == std::vector<std::string>{ "silent_prefixed" });
    CHECK(find_lookup(first, "${beam_short_name} beam  cast") != nullptr);

    const std::string first_bytes = mccd::serialize_candidate_dump(first);
    const std::string second_bytes = mccd::serialize_candidate_dump(second);
    CHECK(first_bytes == second_bytes);
    CHECK(first_bytes.find("\"completeness\":\"closed_world_upper_bound\"")
          != std::string::npos);
    CHECK(first_bytes.find("${beam_short_name} beam  cast")
          != std::string::npos);

    const mccd::candidate_dump case_collision =
        mccd::build_candidate_dump(
            { { "orc wizard", "orc", "humanoid" } },
            { "Magic Dart", "magic dart" }, 1);
    const mccd::lookup_expression *merged =
        find_lookup(case_collision, "magic dart orc wizard cast");
    REQUIRE(merged != nullptr);
    CHECK(merged->attempts == std::vector<std::string>{
        "normal", "silent_unprefixed_fallback" });
    CHECK(case_collision.lookup_expression_count
          < case_collision.base_expression_count * 3);

    const mccd::candidate_dump marker_collision =
        mccd::build_candidate_dump(
            { { "orc ${BEAM_SHORT_NAME}", "orc", "humanoid" } },
            { "Magic Dart" }, 1);
    CHECK_FALSE(marker_collision.valid);
    CHECK(marker_collision.diagnostic
          == "monster fragment collides with reserved beam marker");
    CHECK(marker_collision.base_expressions.empty());

    const mccd::candidate_dump spell_marker_collision =
        mccd::build_candidate_dump(
            { { "orc wizard", "orc", "humanoid" } },
            { "Magic ${Beam_Short_Name}" }, 1);
    CHECK_FALSE(spell_marker_collision.valid);
    CHECK(spell_marker_collision.diagnostic
          == "spell fragment collides with reserved beam marker");
    CHECK(spell_marker_collision.base_expressions.empty());
}

TEST_CASE("write production monspell candidate upper-bound artifact",
          "[.textdb-monspell-candidate-dump]")
{
    const char *output_path =
        std::getenv("TEXTDB_MONSPELL_CANDIDATE_DUMP");
    REQUIRE(output_path != nullptr);
    REQUIRE(*output_path != '\0');

    init_show_table();
    init_monsters();
    init_spell_descs();
    const mccd::candidate_dump dump =
        mccd::build_production_candidate_dump();
    REQUIRE(dump.valid);
    REQUIRE(dump.monster_type_count > 0);
    REQUIRE(dump.spell_count > 0);
    REQUIRE(dump.monster_tuple_count > 0);
    REQUIRE(dump.base_expression_count > 0);
    REQUIRE(dump.lookup_expression_count > dump.base_expression_count);

    const std::string expected = mccd::serialize_candidate_dump(dump);
    std::string error;
    REQUIRE(mccd::write_candidate_dump_atomic(dump, output_path, error));
    REQUIRE(mccd::write_candidate_dump_atomic(dump, output_path, error));
    std::ifstream input(output_path, std::ios::binary);
    REQUIRE(input.good());
    const std::string actual((std::istreambuf_iterator<char>(input)),
                             std::istreambuf_iterator<char>());
    CHECK(actual == expected);
}
