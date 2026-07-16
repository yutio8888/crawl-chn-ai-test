#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "mon-cast-message-keys.h"
#include "mon-util.h"
#include "options.h"
#include "random.h"
#include "stringutil.h"

#include "test_zh_fixture.h"

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

std::vector<std::string> expression_signature(const mcmk::key_recipe &recipe)
{
    std::vector<std::string> result;
    for (const mcmk::key_expression &expression : recipe.candidates)
    {
        std::string value;
        for (const mcmk::key_token &token : expression.tokens)
        {
            value += token.kind == mcmk::key_token_kind::BEAM_SHORT_NAME
                     ? "${BEAM_SHORT_NAME}" : token.text;
        }
        result.push_back(value);
    }
    return result;
}

bool contains_non_ascii(const std::string &text)
{
    for (unsigned char c : text)
    {
        if (c >= 0x80)
            return true;
    }
    return false;
}

mcmk::recipe_input runtime_monster_fragments(monster_type type)
{
    mcmk::recipe_input input = base_input();
    input.monster_type = remove_prepended_the(
        mons_type_name_en(type, DESC_DBNAME));
    input.monster_species = remove_prepended_the(
        mons_type_name_en(mons_species(type), DESC_DBNAME));
    input.monster_genus = remove_prepended_the(
        mons_type_name_en(mons_genus(type), DESC_DBNAME));
    input.targeted = true;
    input.visible_beam = true;
    return input;
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

TEST_CASE_METHOD(ZhTranslationFixture,
                 "canonical monster key fragments ignore display language",
                 "[mon-cast-message-keys][phase1][zh]")
{
    init_monsters();

    const uint64_t state_before = rng::current_generator().get_state();
    const uint64_t count_before = rng::current_generator().get_count();

    Options.language = lang_t::ZH;
    Options.lang_name = "zh";
    i18n_cache_clear();
    const std::string ordinary_zh =
        mons_type_name_en(MONS_ORC_WIZARD, DESC_DBNAME);
    const std::string unique_the_zh =
        mons_type_name_en(MONS_ENCHANTRESS, DESC_THE);
    const std::string random_zh =
        mons_type_name_en(RANDOM_MONSTER, DESC_THE);
    const std::string invalid_zh = mons_type_name_en(
        static_cast<monster_type>(NUM_MONSTERS), DESC_THE);
    const std::string localized_ordinary =
        mons_type_name(MONS_ORC_WIZARD, DESC_DBNAME);
    const std::string localized_random =
        mons_type_name(RANDOM_MONSTER, DESC_THE);
    const mcmk::key_recipe recipe_zh = mcmk::build_key_recipe(
        runtime_monster_fragments(MONS_ORC_WIZARD));

    Options.language = lang_t::EN;
    Options.lang_name = nullptr;
    i18n_cache_clear();
    const std::string ordinary_en =
        mons_type_name_en(MONS_ORC_WIZARD, DESC_DBNAME);
    const std::string unique_the_en =
        mons_type_name_en(MONS_ENCHANTRESS, DESC_THE);
    const std::string random_en =
        mons_type_name_en(RANDOM_MONSTER, DESC_THE);
    const std::string invalid_en = mons_type_name_en(
        static_cast<monster_type>(NUM_MONSTERS), DESC_THE);
    const mcmk::key_recipe recipe_en = mcmk::build_key_recipe(
        runtime_monster_fragments(MONS_ORC_WIZARD));

    CHECK(ordinary_en == "orc wizard");
    CHECK(unique_the_en == "the Enchantress");
    CHECK(random_en == "the random monster");
    CHECK(invalid_en == "the invalid monster_type "
                        + std::to_string(NUM_MONSTERS));
    CHECK(ordinary_zh == ordinary_en);
    CHECK(unique_the_zh == unique_the_en);
    CHECK(random_zh == random_en);
    CHECK(invalid_zh == invalid_en);

    // The existing display helper remains localized and unchanged.
    CHECK(localized_ordinary != ordinary_en);
    CHECK(localized_random != random_en);
    CHECK(contains_non_ascii(localized_ordinary));
    CHECK(contains_non_ascii(localized_random));
    CHECK(mons_type_name(MONS_ORC_WIZARD, DESC_DBNAME) == ordinary_en);

    const std::vector<std::string> signature_en =
        expression_signature(recipe_en);
    const std::vector<std::string> signature_zh =
        expression_signature(recipe_zh);
    CHECK(signature_en == signature_zh);
    REQUIRE_FALSE(signature_en.empty());
    for (const std::string &candidate : signature_en)
        CHECK_FALSE(contains_non_ascii(candidate));
    CHECK(signature_en[signature_en.size() - 2]
          == "${BEAM_SHORT_NAME} beam  cast");

    CHECK(rng::current_generator().get_state() == state_before);
    CHECK(rng::current_generator().get_count() == count_before);
}
