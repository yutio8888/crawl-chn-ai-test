#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "mon-cast-message-keys.h"
#include "random.h"

namespace
{
namespace mcmk = mon_cast_message_keys;

mcmk::recipe_input base_input()
{
    mcmk::recipe_input input;
    input.spell_name = "Magic Dart";
    input.monster_type = "orc wizard";
    input.monster_species = "orc";
    input.monster_genus = "orc genus";
    return input;
}

std::vector<std::string> keys(const mcmk::recipe_input &input,
                              const std::string &beam = "crystal")
{
    return mcmk::materialize_key_recipe(mcmk::build_key_recipe(input), beam);
}
}

TEST_CASE("monspell key recipe preserves representative legacy ordering",
          "[mon-cast-message-keys][phase1]")
{
    mcmk::recipe_input input = base_input();
    input.category_bits = mcmk::CATEGORY_WIZARD;
    input.humanoid = true;
    input.at_least_human_intelligence = true;
    input.hoarfrost_finale = true;
    input.targeted = true;
    input.visible_beam = true;

    // Frozen from the pre-extraction _speech_keys algorithm. This intentionally
    // lists every candidate instead of reconstructing the production recipe.
    const std::vector<std::string> expected = {
        "Magic Dart orc wizard cast",
        "Magic Dart orc cast",
        "Magic Dart orc genus cast",
        "Magic Dart wizard cast",
        "Magic Dart cast real",
        "Magic Dart cast gestures",
        "Magic Dart cast finale",
        "Magic Dart cast",
        "orc wizard cast targeted",
        "orc wizard cast",
        "orc cast targeted",
        "orc cast",
        "orc genus cast targeted",
        "orc genus cast",
        "wizard cast targeted",
        "wizard cast",
        "crystal beam  cast",
        "beam catchall cast",
    };
    CHECK(keys(input) == expected);
}

TEST_CASE("monspell key recipe retains duplicate monster classifications",
          "[mon-cast-message-keys][phase1]")
{
    mcmk::recipe_input input = base_input();
    input.monster_type = "same";
    input.monster_species = "same";
    input.monster_genus = "same";

    const std::vector<std::string> expected = {
        "Magic Dart same cast",
        "Magic Dart same cast",
        "Magic Dart same cast",
        "Magic Dart cast",
        "same cast",
        "same cast",
        "same cast",
    };
    CHECK(keys(input) == expected);
}

TEST_CASE("all casting category masks use legacy priority",
          "[mon-cast-message-keys][phase1]")
{
    for (uint32_t bits = 0; bits < 32; ++bits)
    {
        mcmk::casting_class expected = mcmk::casting_class::CLASS_NONE;
        if (bits & mcmk::CATEGORY_WIZARD)
            expected = mcmk::casting_class::CLASS_WIZARD;
        else if (bits & mcmk::CATEGORY_PRIEST)
            expected = mcmk::casting_class::CLASS_PRIEST;
        else if (bits & mcmk::CATEGORY_MAGICAL)
            expected = mcmk::casting_class::CLASS_MAGICAL;
        else if (bits & (mcmk::CATEGORY_NATURAL | mcmk::CATEGORY_VOCAL))
            expected = mcmk::casting_class::CLASS_NATURAL;
        CAPTURE(bits);
        CHECK(mcmk::normalize_casting_class(bits) == expected);
    }
}

TEST_CASE("humanoid intelligence and real-spell keys remain independent",
          "[mon-cast-message-keys][phase1]")
{
    mcmk::recipe_input input = base_input();
    input.category_bits = mcmk::CATEGORY_PRIEST;
    input.humanoid = true;
    CHECK(keys(input) == std::vector<std::string>{
        "Magic Dart orc wizard cast",
        "Magic Dart orc cast",
        "Magic Dart orc genus cast",
        "Magic Dart priest cast",
        "Magic Dart cast real",
        "Magic Dart cast",
        "orc wizard cast",
        "orc cast",
        "orc genus cast",
        "priest cast",
    });

    input.category_bits = mcmk::CATEGORY_NATURAL;
    input.at_least_human_intelligence = true;
    CHECK(keys(input) == std::vector<std::string>{
        "Magic Dart orc wizard cast",
        "Magic Dart orc cast",
        "Magic Dart orc genus cast",
        "Magic Dart natural cast",
        "Magic Dart cast gestures",
        "Magic Dart cast",
        "orc wizard cast",
        "orc cast",
        "orc genus cast",
    });

    input.humanoid = false;
    input.category_bits = mcmk::CATEGORY_WIZARD;
    CHECK(keys(input) == std::vector<std::string>{
        "Magic Dart orc wizard cast",
        "Magic Dart orc cast",
        "Magic Dart orc genus cast",
        "Magic Dart non-humanoid wizard cast",
        "Magic Dart cast",
        "orc wizard cast",
        "orc cast",
        "orc genus cast",
        "non-humanoid wizard cast",
    });
}

TEST_CASE("finale and targeted insertion retain their legacy boundaries",
          "[mon-cast-message-keys][phase1]")
{
    mcmk::recipe_input input = base_input();
    input.hoarfrost_finale = true;
    input.targeted = true;

    CHECK(keys(input) == std::vector<std::string>{
        "Magic Dart orc wizard cast",
        "Magic Dart orc cast",
        "Magic Dart orc genus cast",
        "Magic Dart cast finale",
        "Magic Dart cast",
        "orc wizard cast targeted",
        "orc wizard cast",
        "orc cast targeted",
        "orc cast",
        "orc genus cast targeted",
        "orc genus cast",
    });
}

TEST_CASE("visible beam stays symbolic until materialization",
          "[mon-cast-message-keys][phase1]")
{
    mcmk::recipe_input input = base_input();
    input.targeted = true;
    input.visible_beam = true;
    const mcmk::key_recipe recipe = mcmk::build_key_recipe(input);

    REQUIRE(recipe.candidates.size() == 12);
    const mcmk::key_expression &beam = recipe.candidates[10];
    REQUIRE(beam.tokens.size() == 3);
    CHECK(beam.tokens[0].kind == mcmk::key_token_kind::BEAM_SHORT_NAME);
    CHECK(beam.tokens[1].kind == mcmk::key_token_kind::LITERAL);
    CHECK(beam.tokens[1].text == " beam ");
    CHECK(beam.tokens[2].kind == mcmk::key_token_kind::LITERAL);
    CHECK(beam.tokens[2].text == " cast");
    CHECK(mcmk::materialize_key_recipe(recipe, "orb")[10]
          == "orb beam  cast");
}

TEST_CASE("monspell key recipe operations do not consume game RNG",
          "[mon-cast-message-keys][phase1]")
{
    mcmk::recipe_input input = base_input();
    input.category_bits = mcmk::CATEGORY_WIZARD | mcmk::CATEGORY_PRIEST;
    input.targeted = true;
    input.visible_beam = true;

    const uint64_t state_before = rng::current_generator().get_state();
    const uint64_t count_before = rng::current_generator().get_count();
    const mcmk::key_recipe recipe = mcmk::build_key_recipe(input);
    const std::vector<std::string> materialized =
        mcmk::materialize_key_recipe(recipe, "bolt");
    CHECK_FALSE(materialized.empty());
    CHECK(rng::current_generator().get_state() == state_before);
    CHECK(rng::current_generator().get_count() == count_before);
}
