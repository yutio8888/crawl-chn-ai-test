#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "fork-message-overlay.h"
#include "initfile.h"
#include "random.h"

#include <unistd.h>

#include <deque>
#include <iomanip>
#include <sstream>

namespace
{
string test_canonical_fingerprint(
    const textdb_phase0::canonical_entry &entry)
{
    string payload("canonical-v1\0", 13);
    payload += entry.canonical_key;
    payload += '\0';
    for (const textdb_phase0::canonical_variant &variant : entry.variants)
    {
        payload += std::to_string(variant.locator.variant_ordinal);
        payload += ':';
        payload += variant.raw_pattern;
        payload += '\0';
    }
    uint64_t value = 14695981039346656037ULL;
    for (const unsigned char byte : payload)
    {
        value ^= byte;
        value *= 1099511628211ULL;
    }
    ostringstream formatted;
    formatted << "fnv1a64:" << hex << setfill('0') << setw(16) << value;
    return formatted.str();
}

void ensure_overlay_data_root()
{
    if (!SysEnv.crawl_dir.empty())
        return;
    char cwd[4096];
    REQUIRE(getcwd(cwd, sizeof(cwd)) != nullptr);
    SysEnv.crawl_dir = cwd;
}

struct scoped_overlay_reset
{
    scoped_overlay_reset()
    {
        fork_message_overlay::reset_monspell_overlay_for_test();
        fork_message_overlay::reset_monspell_overlay_diagnostics_for_test();
    }
    ~scoped_overlay_reset()
    {
        fork_message_overlay::reset_monspell_overlay_for_test();
        fork_message_overlay::reset_monspell_overlay_diagnostics_for_test();
    }
};

fork_message_overlay::message_lookup_result lookup_result(
    fork_message_overlay::message_result result, const string &message = "",
    bool applicability_checked = false)
{
    fork_message_overlay::message_lookup_result value;
    value.result = result;
    value.message = message;
    value.applicability_checked = applicability_checked;
    return value;
}

fork_message_overlay::catalog_entry &catalog_entry_by_key(
    fork_message_overlay::catalog_source &source, const string &key)
{
    auto entry = find_if(source.entries.begin(), source.entries.end(),
                         [&key](const fork_message_overlay::catalog_entry &item)
                         {
                             return item.canonical_key == key;
                         });
    REQUIRE(entry != source.entries.end());
    return *entry;
}

canonical_textdb::loaded_candidate canonical_candidate(
    canonical_textdb::candidate_status status, const string &pattern = "",
    const string &key = "beam catchall cast", size_t ordinal = 0)
{
    canonical_textdb::loaded_candidate candidate;
    candidate.status = status;
    candidate.expanded_pattern_en = pattern;
    if (status == canonical_textdb::candidate_status::SELECTED)
    {
        candidate.top_locator = { key, ordinal };
        canonical_textdb::selected_variant selected;
        selected.locator = candidate.top_locator;
        candidate.selected_variants.push_back(selected);
    }
    return candidate;
}

fork_message_overlay::runtime_bindings beam_bindings(
    fork_message_overlay::target_relation relation,
    fork_message_overlay::target_kind kind =
        fork_message_overlay::target_kind::PLAYER,
    fork_message_overlay::message_visibility visibility =
        fork_message_overlay::message_visibility::VISIBLE)
{
    using namespace fork_message_overlay;
    runtime_bindings values;
    values.actor.sentence_en = "The orc";
    values.actor.canonical_en = "the orc";
    values.actor.possessive_name_en = "The orc's";
    values.actor.possessive_pronoun_en = "its";
    values.actor.reflexive_en = "itself";
    values.actor.arms_plural_en = "arms";
    values.actor.localized = { { "en", "The orc" }, { "zh", "兽人" } };
    values.actor.possessive_name_localized =
        { { "en", "The orc's" }, { "zh", "兽人的" } };
    values.actor.possessive_pronoun_localized =
        { { "en", "its" }, { "zh", "它的" } };
    values.actor.reflexive_localized =
        { { "en", "itself" }, { "zh", "自己" } };
    values.actor.arms_plural_localized =
        { { "en", "arms" }, { "zh", "手臂" } };
    values.actor.visibility = visibility;
    values.target.relation = relation;
    values.target.kind = kind;
    values.target.visibility = visibility;
    values.target.canonical_en = "you";
    values.target.localized = { { "en", "you" }, { "zh", "你" } };
    switch (relation)
    {
    case target_relation::AT:      values.target.relation_en = "at"; break;
    case target_relation::NEXT_TO: values.target.relation_en = "next to"; break;
    case target_relation::PAST:    values.target.relation_en = "past"; break;
    case target_relation::NONE:    break;
    }
    if (kind == target_kind::SELF || kind == target_kind::MONSTER)
    {
        values.target.has_actor_mid = true;
        values.target.actor_mid = 42;
    }
    if (kind == target_kind::FEATURE || kind == target_kind::LOCATION)
    {
        values.target.has_position = true;
        values.target.position_x = 7;
        values.target.position_y = 9;
    }
    if (kind == target_kind::FEATURE)
    {
        values.target.has_feature = true;
        values.target.feature_id = 3;
    }
    values.beam.canonical_en = "a bolt";
    values.beam.localized =
        { { "en", "a bolt" }, { "zh", "一支箭" } };
    values.beam.configured_name_en = "bolt";
    values.beam.short_name_en = "bolt";
    values.beam.origin_spell = 17;
    values.beam.flavour = 2;
    values.beam.real_flavour = 2;
    values.beam.pierce = false;
    values.beam.has_ranged_attack = false;
    values.cast.frame = cast_frame::PROJECTILE;
    values.cast.caster_visibility = visibility;
    values.cast.origin_spell = 17;
    return values;
}

fork_message_overlay::runtime_bindings blizzard_demon_bindings()
{
    using namespace fork_message_overlay;
    runtime_bindings values = beam_bindings(target_relation::NONE);
    values.actor.sentence_en = "The blizzard demon";
    values.actor.canonical_en = "the blizzard demon";
    values.actor.possessive_name_en = "The blizzard demon's";
    values.actor.localized =
        { { "en", "The blizzard demon" }, { "zh", "暴雪恶魔" } };
    values.actor.possessive_name_localized =
        { { "en", "The blizzard demon's" }, { "zh", "暴雪恶魔的" } };
    values.actor.arms_plural_en = "strata";
    values.actor.arms_plural_localized =
        { { "en", "strata" }, { "zh", "云层" } };
    return values;
}

void check_rng_equal(const canonical_textdb::rng_observation &production,
                     const textdb_phase0::rng_observation &prototype)
{
    CHECK(production.current_state == prototype.current_state);
    CHECK(production.current_count == prototype.current_count);
    CHECK(production.global_counts == prototype.global_counts);
}
}

TEST_CASE("monspell overlay validates completely before coverage queries",
          "[single-file][message-overlay][phase1]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    REQUIRE(monspell_overlay_report().state == domain_state::ENABLED);
    REQUIRE(monspell_overlay_covers("beam catchall cast"));
    const vector<textdb_phase0::canonical_entry> canonical =
        textdb_phase0::dump_canonical_english_speakdb();

    SECTION("valid generated catalog enables every candidate key")
    {
        scoped_overlay_reset reset;
        rng::subgenerator scoped_rng(0x1234, 0x5678);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const load_report &report = load_monspell_overlay(canonical);
        CHECK(report.state == domain_state::ENABLED);
        CHECK(report.failure == load_failure::NONE);
        CHECK(report.structured_key_count == 125);
        CHECK(monspell_overlay_covers("BEAM CATCHALL CAST"));
        CHECK(monspell_overlay_covers("march of sorrows bone dragon cast"));
        CHECK(monspell_overlay_covers("ensnare arachne cast"));
        CHECK(monspell_overlay_covers("guardian serpent cast targeted"));
        CHECK(monspell_overlay_covers("wizard cast targeted"));
        CHECK(monspell_overlay_covers("wizard cast"));
        CHECK(monspell_overlay_covers("magical cast targeted"));
        CHECK(monspell_overlay_covers("magical cast"));
        CHECK(monspell_overlay_covers(
            "awaken flesh kobold fleshcrafter cast"));
        CHECK(monspell_overlay_covers("dispel undead revenant cast"));
        CHECK(monspell_overlay_covers("malign offering priest cast"));
        CHECK(monspell_overlay_covers("sheza's dance cast"));
        CHECK(monspell_overlay_covers("silent blizzard demon cast"));
        CHECK(monspell_overlay_covers("ushabti cast targeted"));
        CHECK(monspell_overlay_covers("mennas cast"));
        CHECK(monspell_overlay_covers("airstrike blizzard demon cast"));
        CHECK(monspell_overlay_covers("vv cast"));
        CHECK(monspell_overlay_covers("smiting jeremiah cast"));
        CHECK(monspell_overlay_covers("cantrip gastronok cast"));
        CHECK(monspell_overlay_covers("hellfire mortar wiglaf cast"));
        CHECK(monspell_overlay_covers(
            "vanquished vanguard nergalle cast"));
        CHECK(monspell_overlay_covers("clockroach cast"));
        CHECK(monspell_overlay_covers("ghost moth cast targeted"));
        CHECK_FALSE(monspell_overlay_covers("acid splash cast"));
        CHECK_FALSE(monspell_overlay_covers("branch summon cast prefix"));
        CHECK_FALSE(monspell_overlay_covers("chilling breath cast"));
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("missing overlay disables the whole domain")
    {
        scoped_overlay_reset reset;
        const load_report &report = load_monspell_overlay(canonical, nullptr);
        CHECK(report.state == domain_state::DISABLED);
        CHECK(report.failure == load_failure::MISSING);
        CHECK_FALSE(monspell_overlay_covers("beam catchall cast"));
    }

    SECTION("querying before load seals the domain as disabled")
    {
        scoped_overlay_reset reset;
        CHECK_FALSE(monspell_overlay_covers("beam catchall cast"));
        CHECK(monspell_overlay_report().failure == load_failure::NOT_LOADED);
        CHECK(load_monspell_overlay(canonical).state == domain_state::DISABLED);
    }

    SECTION("unknown schema disables the whole domain")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        source.schema_version = 99;
        const load_report &report = load_monspell_overlay(canonical, &source);
        CHECK(report.state == domain_state::DISABLED);
        CHECK(report.failure == load_failure::UNKNOWN_SCHEMA);
    }

    SECTION("fingerprint or template corruption disables the whole domain")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        catalog_entry_by_key(source, "beam catchall cast")
            .canonical_fingerprint = "fnv1a64:0000000000000000";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "beam catchall cast")
            .variants[0].lines[0].templates[0].pattern +=
            " @target@";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);
    }

    SECTION("partial selectable closure disables the whole domain")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        catalog_entry_by_key(source, "beam catchall cast").variants.clear();
        const load_report &report = load_monspell_overlay(canonical, &source);
        CHECK(report.state == domain_state::DISABLED);
        CHECK(report.failure == load_failure::CLOSURE_INCOMPLETE);
        CHECK(report.structured_key_count == 0);
    }

    SECTION("CASE_MAP signatures and slot types are load-time invariants")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        catalog_entry_by_key(source, "march of sorrows bone dragon cast")
            .variants[0].materialization_cases[1].signature =
            "forged-signature";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "march of sorrows bone dragon cast")
            .variants[0].materialization_cases.pop_back();
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "march of sorrows bone dragon cast")
            .variants[0].slot_schema[0].type = "unknown_ref";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        bool applicability::* const unsupported[] =
        {
            &applicability::requires_named_foe,
            &applicability::requires_god,
        };
        for (const auto field : unsupported)
        {
            reset_monspell_overlay_for_test();
            source = generated_monspell_catalog();
            catalog_entry_by_key(source,
                "march of sorrows bone dragon cast")
                .variants[0].conditions.*field = true;
            CHECK(load_monspell_overlay(canonical, &source).failure
                  == load_failure::CORRUPT);
        }

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "beam catchall cast")
            .variants[0].conditions.requires_player = true;
        CHECK(load_monspell_overlay(canonical, &source).state
              == domain_state::ENABLED);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "beam catchall cast")
            .variants[0].conditions.requires_caster_visible = true;
        CHECK(load_monspell_overlay(canonical, &source).state
              == domain_state::ENABLED);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "beam catchall cast").mode =
            entry_mode::CLOSURE_ONLY;
        catalog_entry_by_key(source, "beam catchall cast")
            .variants[0].conditions.requires_foe = true;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "march of sorrows bone dragon cast")
            .variants[0].materialization_cases[0]
            .lines[0].implies_gesture = true;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);
    }

    SECTION("Phase 2 binding relation and behavior metadata fail closed")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        catalog_entry_by_key(source, "ensnare arachne cast")
            .variants[0].resolves_target = false;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "wizard cast")
            .variants[0].slot_schema.push_back(
            { "target", "resolved_target" });
        catalog_entry_by_key(source, "wizard cast")
            .variants[0].required_arguments.push_back("target");
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "wizard cast")
            .variants[0].lines[0].templates[0].relation = "AT";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "wizard cast targeted")
            .variants[0].lines[0].templates[0].relation = "NONE";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        catalog_entry_by_key(source, "ensnare arachne cast")
            .variants[0].lines[0].audible = true;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);
    }

    SECTION("plural arms token cannot use a generic slot type")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        auto entry = find_if(
            source.entries.begin(), source.entries.end(),
            [](const catalog_entry &candidate)
            {
                return candidate.canonical_key
                       == "airstrike blizzard demon cast";
            });
        REQUIRE(entry != source.entries.end());
        REQUIRE(entry->variants.size() == 3);
        REQUIRE(entry->variants[2].slot_schema.size() == 3);
        entry->variants[2].slot_schema[2].type = "actor_ref";
        const load_report &report = load_monspell_overlay(canonical, &source);
        CHECK(report.state == domain_state::DISABLED);
        CHECK(report.failure == load_failure::CORRUPT);
        CHECK(report.diagnostic == "plural arms token/type mismatch");
    }

    SECTION("recursive capture vocabulary exactly matches reachable leaves")
    {
        auto nergalle_variant = [](catalog_source &source)
            -> catalog_variant &
        {
            auto entry = find_if(
                source.entries.begin(), source.entries.end(),
                [](const catalog_entry &candidate)
                {
                    return candidate.canonical_key
                           == "vanquished vanguard nergalle cast";
                });
            REQUIRE(entry != source.entries.end());
            REQUIRE_FALSE(entry->variants.empty());
            return entry->variants[0];
        };

        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        catalog_variant &replaced = nergalle_variant(source);
        REQUIRE(replaced.recursive_capture_vocabulary.size() == 103);
        replaced.recursive_capture_vocabulary[0] =
            replaced.recursive_capture_vocabulary[1];
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        nergalle_variant(source).recursive_capture_vocabulary.pop_back();
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        recursive_capture_vocabulary_entry &unreachable =
            nergalle_variant(source).recursive_capture_vocabulary[0];
        unreachable.canonical_key = "acid splash cast";
        unreachable.variant_ordinal = 0;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        nergalle_variant(source).recursive_capture_vocabulary[0]
            .variant_fingerprint = "fnv1a64:0000000000000000";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);
    }

    SECTION("recursive capture parents are exact single markers")
    {
        for (const string replacement :
             { "prefix @_beogh_name_@",
               "@_beogh_name_@@_beogh_name_@" })
        {
            CAPTURE(replacement);
            reset_monspell_overlay_for_test();
            vector<textdb_phase0::canonical_entry> changed = canonical;
            auto parent = find_if(
                changed.begin(), changed.end(),
                [](const textdb_phase0::canonical_entry &entry)
                {
                    return entry.canonical_key == "orc name";
                });
            REQUIRE(parent != changed.end());
            REQUIRE_FALSE(parent->variants.empty());
            parent->variants[0].raw_pattern = replacement;

            catalog_source source = generated_monspell_catalog();
            auto nergalle = find_if(
                source.entries.begin(), source.entries.end(),
                [](const catalog_entry &entry)
                {
                    return entry.canonical_key
                           == "vanquished vanguard nergalle cast";
                });
            REQUIRE(nergalle != source.entries.end());
            REQUIRE_FALSE(nergalle->variants.empty());
            auto dependency = find(
                nergalle->variants[0].recursive_dependencies.begin(),
                nergalle->variants[0].recursive_dependencies.end(),
                "orc name");
            REQUIRE(dependency
                    != nergalle->variants[0].recursive_dependencies.end());
            const size_t dependency_index = static_cast<size_t>(
                dependency
                - nergalle->variants[0].recursive_dependencies.begin());
            nergalle->variants[0]
                .recursive_dependency_fingerprints[dependency_index] =
                    test_canonical_fingerprint(*parent);

            const load_report &report =
                load_monspell_overlay(changed, &source);
            CHECK(report.failure == load_failure::CORRUPT);
            CHECK(report.diagnostic
                  == "recursive capture parent is not one exact marker");
        }
    }
}

TEST_CASE("monspell routing is final before selection and tracks diagnostics",
          "[single-file][message-overlay][phase1]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    const vector<textdb_phase0::canonical_entry> canonical =
        textdb_phase0::dump_canonical_english_speakdb();

    SECTION("enabled covered and uncovered keys route without RNG")
    {
        scoped_overlay_reset reset;
        REQUIRE(load_monspell_overlay(canonical).state
                == domain_state::ENABLED);
        rng::subgenerator scoped_rng(0x2001, 0x2002);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();

        const route_decision covered =
            route_monspell_message("BEAM CATCHALL CAST");
        const route_decision uncovered = route_monspell_message(
            "Acid Splash cast");
        CHECK(covered.route == message_route::STRUCTURED);
        CHECK_FALSE(covered.legacy_behavior_compatibility);
        CHECK(covered.canonical_key == "beam catchall cast");
        CHECK(uncovered.route == message_route::LEGACY);
        CHECK_FALSE(uncovered.legacy_behavior_compatibility);
        const diagnostic_counters diagnostics =
            monspell_overlay_diagnostics();
        CHECK(diagnostics.domain == "monspell");
        CHECK(diagnostics.schema_version == MONSPELL_OVERLAY_SCHEMA_VERSION);
        CHECK(diagnostics.overlay_hit == 1);
        CHECK(diagnostics.legacy_fallback == 1);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("uninitialized candidate fails safe to compatibility legacy")
    {
        scoped_overlay_reset reset;
        rng::subgenerator scoped_rng(0x2011, 0x2012);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const route_decision decision =
            route_monspell_message("beam catchall cast");
        CHECK(decision.route == message_route::LEGACY);
        CHECK(decision.legacy_behavior_compatibility);
        CHECK(monspell_overlay_report().state == domain_state::DISABLED);
        CHECK(monspell_overlay_report().failure == load_failure::NOT_LOADED);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("disabled domain routes every key to legacy before lookup")
    {
        scoped_overlay_reset reset;
        REQUIRE(load_monspell_overlay(canonical, nullptr).state
                == domain_state::DISABLED);
        const route_decision former_covered =
            route_monspell_message("beam catchall cast");
        const route_decision truly_uncovered =
            route_monspell_message("acid splash cast");
        CHECK(former_covered.route == message_route::LEGACY);
        CHECK(former_covered.legacy_behavior_compatibility);
        CHECK(truly_uncovered.route == message_route::LEGACY);
        CHECK_FALSE(truly_uncovered.legacy_behavior_compatibility);
        const diagnostic_counters diagnostics =
            monspell_overlay_diagnostics();
        CHECK(diagnostics.overlay_hit == 0);
        CHECK(diagnostics.legacy_fallback == 2);
    }

    SECTION("disabled silent fallback marks only the compiled base candidate")
    {
        scoped_overlay_reset reset;
        REQUIRE(load_monspell_overlay(canonical, nullptr).state
                == domain_state::DISABLED);
        const route_decision prefixed =
            route_monspell_message("silent beam catchall cast");
        const route_decision unprefixed =
            route_monspell_message("beam catchall cast");
        CHECK(prefixed.route == message_route::LEGACY);
        CHECK_FALSE(prefixed.legacy_behavior_compatibility);
        CHECK(unprefixed.route == message_route::LEGACY);
        CHECK(unprefixed.legacy_behavior_compatibility);
    }

    SECTION("disabled unseen prefix remains ordinary legacy")
    {
        scoped_overlay_reset reset;
        REQUIRE(load_monspell_overlay(canonical, nullptr).state
                == domain_state::DISABLED);
        const route_decision unseen =
            route_monspell_message("unseen beam catchall cast");
        CHECK(unseen.route == message_route::LEGACY);
        CHECK_FALSE(unseen.legacy_behavior_compatibility);
    }

    SECTION("unsupported language routes legacy before lookup")
    {
        scoped_overlay_reset reset;
        REQUIRE(load_monspell_overlay(canonical).state
                == domain_state::ENABLED);
        rng::subgenerator scoped_rng(0x2111, 0x2222);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const route_decision decision =
            route_monspell_message("beam catchall cast", "fr");
        CHECK(decision.route == message_route::LEGACY);
        CHECK(decision.legacy_behavior_compatibility);
        const diagnostic_counters diagnostics =
            monspell_overlay_diagnostics();
        CHECK(diagnostics.overlay_hit == 0);
        CHECK(diagnostics.legacy_fallback == 1);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("unknown schema disables routing and has its own counter")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        source.schema_version = 99;
        REQUIRE(load_monspell_overlay(canonical, &source).failure
                == load_failure::UNKNOWN_SCHEMA);
        const route_decision decision =
            route_monspell_message("beam catchall cast");
        CHECK(decision.route == message_route::LEGACY);
        CHECK(decision.legacy_behavior_compatibility);
        const diagnostic_counters diagnostics =
            monspell_overlay_diagnostics();
        CHECK(diagnostics.unknown_schema == 1);
        CHECK(diagnostics.legacy_fallback == 1);
    }
}

TEST_CASE("production candidate state machine preserves speech search semantics",
          "[single-file][message-overlay][phase1]")
{
    using namespace fork_message_overlay;
    scoped_overlay_reset reset;

    SECTION("all five results have exact normal and unseen actions")
    {
        const vector<pair<message_result, message_search_action>> cases =
        {
            { message_result::MISSING,
              message_search_action::NEXT_CANDIDATE },
            { message_result::INAPPLICABLE,
              message_search_action::NEXT_CANDIDATE },
            { message_result::SUPPRESS,
              message_search_action::STOP_SILENT },
            { message_result::RENDERED,
              message_search_action::STOP_RENDERED },
            { message_result::CORRUPT,
              message_search_action::STOP_CORRUPT },
        };
        for (const auto &item : cases)
        {
            for (const message_prefix prefix :
                 { message_prefix::NORMAL, message_prefix::UNSEEN })
            {
                size_t calls = 0;
                const message_candidate_search search =
                    search_message_candidate(
                        "beam catchall cast", prefix,
                        [&](const message_lookup_request &request)
                        {
                            ++calls;
                            CHECK(request.attempt
                                  == message_attempt::NORMAL_OR_UNSEEN);
                            CHECK(request.applicability
                                  == applicability_policy::REQUIRE_APPLICABLE);
                            CHECK(request.lookup_key
                                  == (prefix == message_prefix::UNSEEN
                                      ? "unseen beam catchall cast"
                                      : "beam catchall cast"));
                            return lookup_result(
                                item.first,
                                item.first == message_result::RENDERED
                                    ? "rendered" : "");
                        });
                CHECK(search.action == item.second);
                CHECK(search.lookup_count == 1);
                CHECK(calls == 1);
            }
        }
    }

    SECTION("silent missing and inapplicable retry the unprefixed key")
    {
        for (const message_result first :
             { message_result::MISSING, message_result::INAPPLICABLE })
        {
            vector<message_lookup_request> requests;
            const message_candidate_search search = search_message_candidate(
                "beam catchall cast", message_prefix::SILENT,
                [&](const message_lookup_request &request)
                {
                    requests.push_back(request);
                    if (requests.size() == 1)
                        return lookup_result(first);
                    // This owns the legacy compatibility decision: any
                    // selected nonempty fallback is classified as rendered
                    // without another applicability check.
                    return lookup_result(message_result::RENDERED,
                                         "fallback", false);
                });
            REQUIRE(requests.size() == 2);
            CHECK(requests[0].lookup_key == "silent beam catchall cast");
            CHECK(requests[0].attempt == message_attempt::SILENT_PREFIXED);
            CHECK(requests[0].applicability
                  == applicability_policy::REQUIRE_APPLICABLE);
            CHECK(requests[1].lookup_key == "beam catchall cast");
            CHECK(requests[1].attempt
                  == message_attempt::SILENT_UNPREFIXED_FALLBACK);
            CHECK(requests[1].applicability
                  == applicability_policy::ACCEPT_ANY_NONEMPTY);
            CHECK(search.action == message_search_action::STOP_RENDERED);
            CHECK(search.lookup_count == 2);
            CHECK_FALSE(search.lookup.applicability_checked);
        }
    }

    SECTION("silent terminal results never perform a second lookup")
    {
        const vector<pair<message_result, message_search_action>> cases =
        {
            { message_result::SUPPRESS,
              message_search_action::STOP_SILENT },
            { message_result::RENDERED,
              message_search_action::STOP_RENDERED },
            { message_result::CORRUPT,
              message_search_action::STOP_CORRUPT },
        };
        for (const auto &item : cases)
        {
            size_t calls = 0;
            const message_candidate_search search = search_message_candidate(
                "beam catchall cast", message_prefix::SILENT,
                [&](const message_lookup_request &)
                {
                    ++calls;
                    return lookup_result(
                        item.first,
                        item.first == message_result::RENDERED
                            ? "rendered" : "");
                });
            CHECK(search.action == item.second);
            CHECK(search.lookup_count == 1);
            CHECK(calls == 1);
            if (item.first == message_result::CORRUPT)
            {
                CHECK(monspell_overlay_diagnostics().overlay_corrupt >= 1);
            }
        }
    }

    SECTION("diagnostic updates and reads do not consume RNG")
    {
        rng::subgenerator scoped_rng(0x3001, 0x3002);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        CHECK(search_message_candidate(
                  "key", message_prefix::NORMAL,
                  [](const message_lookup_request &)
                  {
                      return lookup_result(message_result::INAPPLICABLE);
                  }).action == message_search_action::NEXT_CANDIDATE);
        CHECK(search_message_candidate(
                  "key", message_prefix::NORMAL,
                  [](const message_lookup_request &)
                  {
                      return lookup_result(message_result::SUPPRESS);
                  }).action == message_search_action::STOP_SILENT);
        const diagnostic_counters diagnostics =
            monspell_overlay_diagnostics();
        CHECK(diagnostics.candidate_inapplicable == 1);
        CHECK(diagnostics.message_suppressed == 1);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("a missing production lookup is terminal corruption")
    {
        const message_candidate_search search = search_message_candidate(
            "beam catchall cast", message_prefix::SILENT, message_lookup());
        CHECK(search.action == message_search_action::STOP_CORRUPT);
        CHECK(search.lookup.result == message_result::CORRUPT);
        CHECK(search.lookup_count == 0);
        CHECK(monspell_overlay_diagnostics().overlay_corrupt == 1);
    }
}

TEST_CASE("canonical monspell materialization observes all five boundaries",
          "[single-file][message-overlay][phase1][stage3]")
{
    using namespace fork_message_overlay;
    rng::subgenerator scoped_rng(0x3501, 0x3502);
    const uint64_t initial_state = rng::current_generator().get_state();
    const uint64_t initial_count = rng::current_generator().get_count();
    size_t binding_calls = 0;
    const runtime_binding_resolver bindings =
        [&](const binding_requirements &)
    {
        ++binding_calls;
        return beam_bindings(target_relation::AT);
    };
    const auto run = [&](canonical_textdb::loaded_candidate candidate,
                         bool applicable = true)
    {
        return materialize_monspell_candidate(
            "beam catchall cast", message_attempt::NORMAL_OR_UNSEEN,
            applicable, bindings,
            [candidate](const string &) { return candidate; });
    };

    CHECK(run(canonical_candidate(
              canonical_textdb::candidate_status::MISSING)).result
          == message_result::MISSING);
    CHECK(run(canonical_candidate(
              canonical_textdb::candidate_status::CORRUPT)).result
          == message_result::CORRUPT);
    CHECK(run(canonical_candidate(
              canonical_textdb::candidate_status::SELECTED,
              "__NONE")).result == message_result::SUPPRESS);
    CHECK(run(canonical_candidate(
              canonical_textdb::candidate_status::SELECTED,
              "@The_monster@ throws @beam@ @at@ @target@."), false).result
          == message_result::INAPPLICABLE);
    CHECK(binding_calls == 0);
    CHECK(rng::current_generator().get_state() == initial_state);
    CHECK(rng::current_generator().get_count() == initial_count);

    const canonical_materialization rendered = run(canonical_candidate(
        canonical_textdb::candidate_status::SELECTED,
        "@The_monster@ throws @beam@ @at@ @target@."));
    CHECK(rendered.result == message_result::RENDERED);
    CHECK(binding_calls == 1);
    CHECK(rendered.binding.callback_count == 1);
    CHECK(rendered.binding.rng.before.current_state
          == rendered.binding.rng.after.current_state);
    CHECK(rendered.binding.rng.before.current_count
          == rendered.binding.rng.after.current_count);
    CHECK(rendered.bound_pattern_en == "The orc throws a bolt at you.");
    CHECK(rendered.bound_pattern_en.find('@') == string::npos);
    CHECK(rendered.randomized.random_site_count == 0);
    CHECK(rendered.materialization_signature == "NONE");
    CHECK(rendered.stable_id == "mon.cast.beam_catchall.v1");
}

TEST_CASE("production canonical trace and pure renderer are language neutral",
          "[single-file][message-overlay][phase1][stage3]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    rng::subgenerator scoped_rng(0x4001, 0x4002);
    const canonical_materialization materialized =
        materialize_monspell_candidate(
            "beam catchall cast", message_attempt::NORMAL_OR_UNSEEN, true,
            [](const binding_requirements &)
            { return beam_bindings(target_relation::AT); });
    REQUIRE(materialized.result == message_result::RENDERED);
    REQUIRE(materialized.canonical.trace.weighted_choices.size() == 1);
    const canonical_textdb::weighted_choice_trace &top =
        materialized.canonical.trace.weighted_choices[0];
    CHECK(top.requested_key == "beam catchall cast");
    CHECK(top.resolved_canonical_key == "beam catchall cast");
    CHECK(top.recursion_path.empty());
    CHECK(top.variant_ordinal == 0);
    CHECK(top.weight == 10);
    CHECK(top.total_bound == 10);
    CHECK(top.before.current_count <= top.after.current_count);
    CHECK(materialized.canonical.trace.final_replacement_count > 0);
    CHECK_FALSE(materialized.canonical.trace.recursive_sites.empty());
    CHECK(materialized.canonical.trace.lua_sites.empty());
    CHECK(materialized.randomized.sites.empty());

    const uint64_t state = rng::current_generator().get_state();
    const uint64_t count = rng::current_generator().get_count();
    const render_result en = render_materialized_candidate(materialized, "en");
    const render_result zh = render_materialized_candidate(materialized, "zh");
    REQUIRE(en.result == message_result::RENDERED);
    REQUIRE(zh.result == message_result::RENDERED);
    REQUIRE(en.lines.size() == 1);
    REQUIRE(zh.lines.size() == 1);
    CHECK(en.lines[0].text == "The orc throws a bolt at you.");
    CHECK(zh.lines[0].text == "兽人向你射出一支箭。");
    CHECK(rng::current_generator().get_state() == state);
    CHECK(rng::current_generator().get_count() == count);
}

TEST_CASE("typed renderer rejects malformed slots and preserves line metadata",
          "[single-file][message-overlay][phase1][stage3]")
{
    using namespace fork_message_overlay;
    const vector<slot_definition> one = { { "actor", "actor_ref" } };
    const vector<slot_value> value = { { "actor", "兽人" } };
    CHECK(render_typed_template("${actor", one, value).result
          == message_result::CORRUPT);
    CHECK(render_typed_template("${missing}", one, value).result
          == message_result::CORRUPT);
    const render_result language_local_omission =
        render_typed_template("plain", one, value);
    REQUIRE(language_local_omission.result == message_result::RENDERED);
    CHECK(language_local_omission.lines[0].text == "plain");
    CHECK(render_typed_template("${actor} @target@", one, value).result
          == message_result::CORRUPT);
    CHECK(render_typed_template("${actor} __NONE", one, value).result
          == message_result::CORRUPT);
    CHECK(render_typed_template("${actor}\nsecond line", one, value).result
          == message_result::CORRUPT);
    CHECK(render_typed_template("${actor}", one,
          { { "actor", "兽人" }, { "beam", "箭" } }).result
          == message_result::CORRUPT);

    line_metadata visual;
    visual.sensory = sensory_mode::VISUAL;
    visual.channel = "talk";
    visual.implies_gesture = true;
    visual.templates.push_back({ "zh", "AT", "${actor}挥手。" });
    line_metadata sound;
    sound.sensory = sensory_mode::SOUND;
    sound.channel = "sound";
    sound.audible = true;
    sound.templates.push_back({ "zh", "AT", "${actor}喊叫。" });
    const render_result rendered = render_typed_lines(
        { visual, sound }, "zh", target_relation::AT, one, value);
    REQUIRE(rendered.result == message_result::RENDERED);
    REQUIRE(rendered.lines.size() == 2);
    CHECK(rendered.lines[0].sensory == sensory_mode::VISUAL);
    CHECK(rendered.lines[0].channel == "talk");
    CHECK(rendered.lines[0].implies_gesture);
    CHECK(rendered.lines[0].text == "兽人挥手。");
    CHECK(rendered.lines[1].sensory == sensory_mode::SOUND);
    CHECK(rendered.lines[1].channel == "sound");
    CHECK(rendered.lines[1].audible);
    CHECK(rendered.lines[1].text == "兽人喊叫。");
}

TEST_CASE("beam templates cover relation target kind and visibility snapshots",
          "[single-file][message-overlay][phase1][stage3]")
{
    using namespace fork_message_overlay;
    const vector<target_relation> relations =
        { target_relation::AT, target_relation::NEXT_TO,
          target_relation::PAST };
    const vector<target_kind> kinds =
        { target_kind::PLAYER, target_kind::SELF, target_kind::MONSTER,
          target_kind::FEATURE, target_kind::LOCATION,
          target_kind::THIN_AIR, target_kind::INDEFINITE };
    const vector<message_visibility> visibilities =
        { message_visibility::VISIBLE, message_visibility::UNSEEN,
          message_visibility::UNKNOWN };
    for (const target_relation relation : relations)
    {
        for (const target_kind kind : kinds)
        {
            for (const message_visibility visibility : visibilities)
            {
                const canonical_materialization materialized =
                    materialize_monspell_candidate(
                        "beam catchall cast",
                        message_attempt::NORMAL_OR_UNSEEN, true,
                        [=](const binding_requirements &)
                        { return beam_bindings(relation, kind, visibility); },
                        [](const string &)
                        {
                            return canonical_candidate(
                                canonical_textdb::candidate_status::SELECTED,
                                "@The_monster@ throws @beam@ @at@ @target@.");
                        });
                REQUIRE(materialized.result == message_result::RENDERED);
                const render_result rendered =
                    render_materialized_candidate(materialized, "zh");
                REQUIRE(rendered.result == message_result::RENDERED);
                REQUIRE(rendered.lines.size() == 1);
                const string &text = rendered.lines[0].text;
                CHECK(text.find("${") == string::npos);
                CHECK(text.find('@') == string::npos);
                CHECK(text.find("__NONE") == string::npos);
                if (relation == target_relation::AT)
                    CHECK(text == "兽人向你射出一支箭。");
                else if (relation == target_relation::NEXT_TO)
                    CHECK(text == "兽人朝你旁边射出一支箭。");
                else
                    CHECK(text == "兽人射出一支箭，从你旁边掠过。");
            }
        }
    }
}

TEST_CASE("bound legacy materializer rejects runtime tokens without RNG",
          "[single-file][message-overlay][phase1][stage3]")
{
    canonical_textdb::loaded_candidate candidate = canonical_candidate(
        canonical_textdb::candidate_status::SELECTED, "ignored");
    rng::subgenerator scoped_rng(0x5001, 0x5002);
    for (const string token : { "@at@", "@target@", "@beam@" })
    {
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const canonical_textdb::randomized_pattern result =
            canonical_textdb::materialize_bound_legacy_randomness(
                candidate, "still " + token);
        CHECK(result.status == canonical_textdb::candidate_status::CORRUPT);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("non-selected candidates are rejected without materialization")
    {
        canonical_textdb::loaded_candidate missing;
        missing.status = canonical_textdb::candidate_status::MISSING;
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const canonical_textdb::randomized_pattern result =
            canonical_textdb::materialize_bound_legacy_randomness(
                missing, "[casts|pitches]");
        CHECK(result.status == canonical_textdb::candidate_status::CORRUPT);
        CHECK(result.sites.empty());
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("dynamic signatures encode the selected bracket case")
    {
        const canonical_textdb::randomized_pattern result =
            canonical_textdb::materialize_bound_legacy_randomness(
                candidate, "it [casts|pitches]");
        REQUIRE(result.status == canonical_textdb::candidate_status::SELECTED);
        REQUIRE(result.sites.size() == 1);
        CHECK(result.signature.find("materialization-v1|") == 0);
        CHECK(result.signature.find("|sites=1|") != string::npos);
        CHECK(result.signature != "DYNAMIC");
    }
}

TEST_CASE("production seam preserves complete canonical and bracket traces",
          "[single-file][message-overlay][phase1][stage3]")
{
    ensure_overlay_data_root();
    databaseSystemInit();
    textdb_phase0::expanded_selection prototype;
    canonical_textdb::loaded_candidate production;
    {
        rng::subgenerator scoped_rng(0x6001, 0x6002);
        prototype = textdb_phase0::
            expand_loaded_canonical_english_speakdb_traced(
                "beam catchall cast");
    }
    {
        rng::subgenerator scoped_rng(0x6001, 0x6002);
        production = canonical_textdb::expand_loaded_english_candidate(
            "beam catchall cast");
    }
    REQUIRE(prototype.status == textdb_phase0::raw_selection_status::SELECTED);
    REQUIRE(production.status == canonical_textdb::candidate_status::SELECTED);
    CHECK(production.expanded_pattern_en == prototype.text);
    REQUIRE(production.trace.weighted_choices.size()
            == prototype.trace.weighted_choices.size());
    for (size_t i = 0; i < prototype.trace.weighted_choices.size(); ++i)
    {
        const auto &actual = production.trace.weighted_choices[i];
        const auto &expected = prototype.trace.weighted_choices[i];
        CHECK(actual.requested_key == expected.requested_key);
        CHECK(actual.resolved_canonical_key == expected.resolved_canonical_key);
        CHECK(actual.recursion_path == expected.recursion_path);
        CHECK(actual.recursion_depth == expected.recursion_depth);
        CHECK(actual.replacement_count == expected.replacement_count);
        CHECK(actual.variant_ordinal == expected.variant_ordinal);
        CHECK(actual.weight == expected.weight);
        CHECK(actual.total_bound == expected.total_bound);
        CHECK(actual.random_result == expected.random_result);
        check_rng_equal(actual.before, expected.before);
        check_rng_equal(actual.after, expected.after);
    }
    REQUIRE(production.trace.recursive_sites.size()
            == prototype.trace.recursive_sites.size());
    for (size_t i = 0; i < prototype.trace.recursive_sites.size(); ++i)
    {
        const auto &actual = production.trace.recursive_sites[i];
        const auto &expected = prototype.trace.recursive_sites[i];
        CHECK(actual.recursion_path == expected.recursion_path);
        CHECK(actual.marker == expected.marker);
        CHECK(actual.replacement == expected.replacement);
        CHECK(actual.recursion_depth == expected.recursion_depth);
        CHECK(actual.replacement_count == expected.replacement_count);
        CHECK(static_cast<int>(actual.status)
              == static_cast<int>(expected.status));
    }
    REQUIRE(production.trace.lua_sites.size()
            == prototype.trace.lua_sites.size());
    for (size_t i = 0; i < prototype.trace.lua_sites.size(); ++i)
    {
        const auto &actual = production.trace.lua_sites[i];
        const auto &expected = prototype.trace.lua_sites[i];
        CHECK(actual.ordinal == expected.ordinal);
        CHECK(actual.source == expected.source);
        CHECK(actual.result == expected.result);
        CHECK(static_cast<int>(actual.status)
              == static_cast<int>(expected.status));
        check_rng_equal(actual.before, expected.before);
        check_rng_equal(actual.after, expected.after);
    }
    CHECK(production.trace.final_replacement_count
          == prototype.trace.final_replacement_count);

    textdb_phase0::canonical_pre_random_pattern prototype_pattern;
    prototype_pattern.top_locator = { "dynamic test", 2 };
    prototype_pattern.pattern_en = "[casts|pitches]";
    textdb_phase0::weighted_choice_trace recursive;
    recursive.resolved_canonical_key = "flavour child";
    recursive.variant_ordinal = 4;
    recursive.recursion_path = { 1, 3 };
    prototype_pattern.selection.weighted_choices.push_back(recursive);
    canonical_textdb::loaded_candidate production_pattern;
    production_pattern.status = canonical_textdb::candidate_status::SELECTED;
    production_pattern.top_locator = { "dynamic test", 2 };
    canonical_textdb::selected_variant production_recursive;
    production_recursive.locator = { "flavour child", 4 };
    production_recursive.recursion_path = { 1, 3 };
    production_pattern.selected_variants.push_back(production_recursive);

    textdb_phase0::legacy_materialization prototype_random;
    canonical_textdb::randomized_pattern production_random;
    {
        rng::subgenerator scoped_rng(0x7001, 0x7002);
        prototype_random = textdb_phase0::materialize_legacy_randomness(
            prototype_pattern);
    }
    {
        rng::subgenerator scoped_rng(0x7001, 0x7002);
        production_random =
            canonical_textdb::materialize_bound_legacy_randomness(
                production_pattern, "[casts|pitches]");
    }
    REQUIRE(production_random.status
            == canonical_textdb::candidate_status::SELECTED);
    CHECK(production_random.pattern_en
          == prototype_random.randomized_pattern_en);
    REQUIRE(production_random.sites.size() == prototype_random.sites.size());
    REQUIRE(production_random.sites.size() == 1);
    const auto &actual_site = production_random.sites[0];
    const auto &expected_site = prototype_random.sites[0];
    CHECK(actual_site.top_locator.canonical_key
          == expected_site.identity.top_locator.canonical_key);
    CHECK(actual_site.top_locator.variant_ordinal
          == expected_site.identity.top_locator.variant_ordinal);
    REQUIRE(actual_site.recursive_variants.size()
            == expected_site.identity.recursive_variants.size());
    CHECK(actual_site.recursive_variants[0].locator.canonical_key
          == expected_site.identity.recursive_variants[0].locator.canonical_key);
    CHECK(actual_site.recursive_variants[0].locator.variant_ordinal
          == expected_site.identity.recursive_variants[0].locator.variant_ordinal);
    CHECK(actual_site.recursive_variants[0].recursion_path
          == expected_site.identity.recursive_variants[0].recursion_path);
    CHECK(actual_site.expanded_site_ordinal
          == expected_site.identity.expanded_site_ordinal);
    CHECK(actual_site.option_count == expected_site.option_count);
    CHECK(actual_site.option_index == expected_site.option_index);
    check_rng_equal(production_random.before, prototype_random.before);
    check_rng_equal(production_random.after, prototype_random.after);
}

TEST_CASE("production materializer preserves real monspell bracket sites",
          "[single-file][message-overlay][phase1][materialization]")
{
    ensure_overlay_data_root();
    databaseSystemInit();
    const vector<pair<string, string>> cases =
    {
        { "March of Sorrows Boris cast", "[casts|pitches]" },
        { "orb of entropy cast", "[pulses|vibrates]" },
    };

    for (const auto &item : cases)
    {
        bool found = false;
        for (uint64_t seed = 1; seed <= 256 && !found; ++seed)
        {
            rng::subgenerator scoped_rng(seed, seed ^ 0x9e3779b97f4a7c15ULL);
            const canonical_textdb::loaded_candidate candidate =
                canonical_textdb::expand_loaded_english_candidate(item.first);
            REQUIRE(candidate.status
                    == canonical_textdb::candidate_status::SELECTED);
            if (candidate.expanded_pattern_en.find(item.second)
                == string::npos)
            {
                continue;
            }
            const canonical_textdb::randomized_pattern materialized =
                canonical_textdb::materialize_bound_legacy_randomness(
                    candidate, candidate.expanded_pattern_en);
            REQUIRE(materialized.status
                    == canonical_textdb::candidate_status::SELECTED);
            REQUIRE(materialized.sites.size() >= 1);
            CHECK(materialized.pattern_en.find(item.second) == string::npos);
            CHECK(materialized.signature.find("materialization-v1|") == 0);
            found = true;
        }
        CHECK(found);
    }
}

TEST_CASE("production CASE_MAP maps every March of Sorrows seed",
          "[single-file][message-overlay][phase1][case-map]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    set<string> english;
    set<string> chinese;
    set<string> stable_cases;
    // Phase 0 already proves legacy target/RNG equivalence for this exact key
    // over 1024 seeds. This production slice exhaustively proves that every
    // observed option index maps to the corresponding stable case and locale.
    for (uint64_t seed = 1; seed <= 1024; ++seed)
    {
        size_t binding_calls = 0;
        rng::subgenerator scoped_rng(seed, seed ^ 0x517cc1b727220a95ULL);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "march of sorrows bone dragon cast",
                message_attempt::NORMAL_OR_UNSEEN, true,
                [&](const binding_requirements &)
                {
                    ++binding_calls;
                    runtime_bindings values = beam_bindings(
                        target_relation::AT);
                    values.actor.sentence_en = "The bone dragon";
                    values.actor.canonical_en = "the bone dragon";
                    values.actor.localized =
                        { { "en", "The bone dragon" }, { "zh", "骨龙" } };
                    return values;
                });
        REQUIRE(materialized.result == message_result::RENDERED);
        REQUIRE(materialized.randomized.sites.size() == 1);
        const int option = materialized.randomized.sites[0].option_index;
        REQUIRE((option == 0 || option == 1));
        CHECK(binding_calls == 1);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const render_result en = render_materialized_candidate(
            materialized, "en");
        const render_result zh = render_materialized_candidate(
            materialized, "zh");
        REQUIRE(en.result == message_result::RENDERED);
        REQUIRE(zh.result == message_result::RENDERED);
        REQUIRE(en.lines.size() == 1);
        REQUIRE(zh.lines.size() == 1);
        CHECK(en.lines[0].text == materialized.randomized.pattern_en);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
        english.insert(en.lines[0].text);
        chinese.insert(zh.lines[0].text);
        stable_cases.insert(materialized.stable_id);
        if (option == 0)
        {
            CHECK(materialized.stable_id ==
                "mon.cast.march_of_sorrows_bone_dragon.collective_despair.v1");
            CHECK(en.lines[0].text ==
                  "The bone dragon breathes collective despair at you.");
            CHECK(zh.lines[0].text == "骨龙朝你吐出集体的绝望。");
        }
        else
        {
            CHECK(materialized.stable_id ==
                "mon.cast.march_of_sorrows_bone_dragon.endless_sorrows.v1");
            CHECK(en.lines[0].text ==
                  "The bone dragon breathes endless sorrows at you.");
            CHECK(zh.lines[0].text == "骨龙朝你吐出无尽的悲伤。");
        }

        canonical_materialization adjacent = materialized;
        adjacent.binding.values.target.relation = target_relation::NEXT_TO;
        const render_result next_zh = render_materialized_candidate(
            adjacent, "zh");
        REQUIRE(next_zh.result == message_result::RENDERED);
        CHECK(next_zh.lines[0].text == (option == 0
            ? "骨龙朝你旁边吐出集体的绝望。"
            : "骨龙朝你旁边吐出无尽的悲伤。"));
        canonical_materialization past = materialized;
        past.binding.values.target.relation = target_relation::PAST;
        const render_result past_zh = render_materialized_candidate(past,
                                                                     "zh");
        REQUIRE(past_zh.result == message_result::RENDERED);
        CHECK(past_zh.lines[0].text == (option == 0
            ? "骨龙吐出集体的绝望，从你旁边掠过。"
            : "骨龙吐出无尽的悲伤，从你旁边掠过。"));
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }
    CHECK(english == set<string>{
        "The bone dragon breathes collective despair at you.",
        "The bone dragon breathes endless sorrows at you.",
    });
    CHECK(chinese == set<string>{
        "骨龙朝你吐出集体的绝望。",
        "骨龙朝你吐出无尽的悲伤。",
    });
    CHECK(stable_cases == set<string>{
        "mon.cast.march_of_sorrows_bone_dragon.collective_despair.v1",
        "mon.cast.march_of_sorrows_bone_dragon.endless_sorrows.v1",
    });

    canonical_textdb::loaded_candidate forged = canonical_candidate(
        canonical_textdb::candidate_status::SELECTED,
        "@The_monster@ breathes [one|two|three] @at@ @target@.");
    forged.top_locator = { "march of sorrows bone dragon cast", 0 };
    forged.selected_variants[0].locator = forged.top_locator;
    size_t forged_binding_calls = 0;
    const canonical_materialization unknown = materialize_monspell_candidate(
        "march of sorrows bone dragon cast",
        message_attempt::NORMAL_OR_UNSEEN, true,
        [&](const binding_requirements &)
        {
            ++forged_binding_calls;
            return beam_bindings(target_relation::AT);
        },
        [forged](const string &) { return forged; });
    CHECK(unknown.result == message_result::CORRUPT);
    CHECK(unknown.diagnostic == "CASE_MAP materialization signature is unknown");
    CHECK(forged_binding_calls == 1);
}

TEST_CASE("Phase 2 gesture variants bind once and render every relation",
          "[single-file][message-overlay][phase2]")
{
    using namespace fork_message_overlay;
    struct fixture
    {
        const char *key;
        size_t ordinal;
        const char *pattern;
        bool gesture;
        cast_frame frame;
        const char *bound_at;
        const char *en[3];
        const char *zh[3];
    };
    const fixture cases[] =
    {
        { "ensnare arachne cast", 0,
          "@The_monster@ points @possessive@ staff @at@ @target@, shooting a stream of webbing.",
          true, cast_frame::GESTURE,
          "The orc points its staff at you, shooting a stream of webbing.",
          { "The orc points its staff at you, shooting a stream of webbing.",
            "The orc points its staff next to you, shooting a stream of webbing.",
            "The orc points its staff past you, shooting a stream of webbing." },
          { "兽人用法杖指向你，射出一股蛛网。",
            "兽人用法杖指向你旁边，射出一股蛛网。",
            "兽人用法杖指向你身后，射出一股蛛网。" } },
        { "ensnare arachne cast", 1,
          "@The_monster_possessive@ staff shoots out a stream of webbing.",
          false, cast_frame::PROJECTILE,
          "The orc's staff shoots out a stream of webbing.",
          { "The orc's staff shoots out a stream of webbing.",
            "The orc's staff shoots out a stream of webbing.",
            "The orc's staff shoots out a stream of webbing." },
          { "兽人的法杖射出一股蛛网。", "兽人的法杖射出一股蛛网。",
            "兽人的法杖射出一股蛛网。" } },
        { "guardian serpent cast targeted", 0,
          "@The_monster@ coils @reflexive@ and waves @possessive@ upper body @at@ @target@.",
          false, cast_frame::GESTURE,
          "The orc coils itself and waves its upper body at you.",
          { "The orc coils itself and waves its upper body at you.",
            "The orc coils itself and waves its upper body next to you.",
            "The orc coils itself and waves its upper body past you." },
          { "兽人盘起身躯，向你摆动上半身。",
            "兽人盘起身躯，向你旁边摆动上半身。",
            "兽人盘起身躯，向你身后摆动上半身。" } },
        { "guardian serpent cast targeted", 1,
          "@The_monster@ gestures with @possessive@ tail @at@ @target@.",
          true, cast_frame::GESTURE,
          "The orc gestures with its tail at you.",
          { "The orc gestures with its tail at you.",
            "The orc gestures with its tail next to you.",
            "The orc gestures with its tail past you." },
          { "兽人用尾巴向你做出手势。",
            "兽人用尾巴向你旁边做出手势。",
            "兽人用尾巴向你身后做出手势。" } },
        { "guardian serpent cast targeted", 2,
          "@The_monster@ weaves intricate patterns with the tip of @possessive@ tongue.",
          false, cast_frame::GESTURE,
          "The orc weaves intricate patterns with the tip of its tongue.",
          { "The orc weaves intricate patterns with the tip of its tongue.",
            "The orc weaves intricate patterns with the tip of its tongue.",
            "The orc weaves intricate patterns with the tip of its tongue." },
          { "兽人用舌尖编织出复杂的图案。",
            "兽人用舌尖编织出复杂的图案。",
            "兽人用舌尖编织出复杂的图案。" } },
    };
    const target_relation relations[] =
        { target_relation::AT, target_relation::NEXT_TO,
          target_relation::PAST };
    for (const fixture &item : cases)
    {
        CAPTURE(item.key, item.ordinal);
        size_t calls = 0;
        binding_requirements observed;
        const canonical_textdb::loaded_candidate candidate =
            canonical_candidate(
                canonical_textdb::candidate_status::SELECTED,
                item.pattern, item.key, item.ordinal);
        canonical_materialization materialized =
            materialize_monspell_candidate(
                item.key, message_attempt::NORMAL_OR_UNSEEN, true,
                [&](const binding_requirements &requirements)
                {
                    ++calls;
                    observed = requirements;
                    runtime_bindings values =
                        beam_bindings(target_relation::AT);
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(calls == 1);
        CHECK(materialized.binding.callback_count == 1);
        CHECK(observed.resolves_target);
        CHECK(observed.implies_gesture == item.gesture);
        CHECK(observed.frame == item.frame);
        CHECK(materialized.bound_pattern_en == item.bound_at);
        CHECK(materialized.bound_pattern_en.find('@') == string::npos);
        for (size_t relation = 0; relation < 3; ++relation)
        {
            materialized.binding.values.target.relation =
                relations[relation];
            const render_result en =
                render_materialized_candidate(materialized, "en");
            const render_result zh =
                render_materialized_candidate(materialized, "zh");
            REQUIRE(en.result == message_result::RENDERED);
            REQUIRE(zh.result == message_result::RENDERED);
            CHECK(en.lines[0].text == item.en[relation]);
            CHECK(zh.lines[0].text == item.zh[relation]);
            CHECK(en.lines[0].implies_gesture == item.gesture);
            CHECK(zh.lines[0].implies_gesture == item.gesture);
        }
    }
}

TEST_CASE("actor binding validation follows declared slot types",
          "[single-file][message-overlay][phase2]")
{
    using namespace fork_message_overlay;
    const canonical_textdb::loaded_candidate beam = canonical_candidate(
        canonical_textdb::candidate_status::SELECTED,
        "@The_monster@ throws @beam@ @at@ @target@.");
    const canonical_materialization actor_only =
        materialize_monspell_candidate(
            "beam catchall cast", message_attempt::NORMAL_OR_UNSEEN, true,
            [](const binding_requirements &requirements)
            {
                runtime_bindings values =
                    beam_bindings(target_relation::AT);
                values.cast.frame = requirements.frame;
                values.actor.possessive_name_en.clear();
                values.actor.possessive_pronoun_en.clear();
                values.actor.reflexive_en.clear();
                return values;
            },
            [beam](const string &) { return beam; });
    CHECK(actor_only.result == message_result::RENDERED);

    const canonical_textdb::loaded_candidate possessive =
        canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            "@The_monster_possessive@ staff shoots out a stream of webbing.",
            "ensnare arachne cast", 1);
    const canonical_materialization possessive_only =
        materialize_monspell_candidate(
            "ensnare arachne cast",
            message_attempt::NORMAL_OR_UNSEEN, true,
            [](const binding_requirements &requirements)
            {
                runtime_bindings values =
                    beam_bindings(target_relation::AT);
                values.cast.frame = requirements.frame;
                values.actor.sentence_en.clear();
                values.actor.canonical_en.clear();
                values.actor.possessive_pronoun_en.clear();
                values.actor.reflexive_en.clear();
                return values;
            },
            [possessive](const string &) { return possessive; });
    CHECK(possessive_only.result == message_result::RENDERED);

    const canonical_materialization missing_declared =
        materialize_monspell_candidate(
            "ensnare arachne cast",
            message_attempt::NORMAL_OR_UNSEEN, true,
            [](const binding_requirements &requirements)
            {
                runtime_bindings values =
                    beam_bindings(target_relation::AT);
                values.cast.frame = requirements.frame;
                values.actor.possessive_name_en.clear();
                return values;
            },
            [possessive](const string &) { return possessive; });
    CHECK(missing_declared.result == message_result::CORRUPT);
    CHECK(missing_declared.diagnostic == "runtime bindings are incomplete");
}

TEST_CASE("non-target materialization rejects late target tokens before binding",
          "[single-file][message-overlay][phase2]")
{
    using namespace fork_message_overlay;
    const canonical_textdb::loaded_candidate forged = canonical_candidate(
        canonical_textdb::candidate_status::SELECTED,
        "@The_monster@ gestures @at@ @target@.", "wizard cast", 0);
    size_t calls = 0;
    rng::subgenerator scoped_rng(0x90210, 0x314159);
    const uint64_t state = rng::current_generator().get_state();
    const uint64_t count = rng::current_generator().get_count();
    const canonical_materialization materialized =
        materialize_monspell_candidate(
            "wizard cast", message_attempt::NORMAL_OR_UNSEEN, true,
            [&](const binding_requirements &)
            {
                ++calls;
                return beam_bindings(target_relation::NONE);
            },
            [forged](const string &) { return forged; });
    CHECK(materialized.result == message_result::CORRUPT);
    CHECK(materialized.diagnostic
          == "non-target materialization contains target tokens");
    CHECK(calls == 0);
    CHECK(materialized.binding.callback_count == 0);
    CHECK(rng::current_generator().get_state() == state);
    CHECK(rng::current_generator().get_count() == count);
}

TEST_CASE("common cast variants render targeted and NONE relation matrices",
          "[single-file][message-overlay][phase2]")
{
    using namespace fork_message_overlay;
    struct fixture
    {
        const char *key;
        size_t ordinal;
        const char *pattern;
        bool resolves_target;
        bool gesture;
        cast_frame frame;
        const char *en_at;
        const char *zh_at;
        const char *en_none;
        const char *zh_none;
    };
    const fixture cases[] =
    {
        { "wizard cast targeted", 0,
          "@The_monster@ gestures @at@ @target@ while chanting.",
          true, true, cast_frame::GESTURE,
          "The orc gestures at you while chanting.",
          "兽人一边吟诵，一边向你做出手势。", "", "" },
        { "wizard cast targeted", 1,
          "@The_monster@ points @at@ @target@ and mumbles some strange words.",
          true, true, cast_frame::GESTURE,
          "The orc points at you and mumbles some strange words.",
          "兽人指向你，咕哝着一些奇怪的话。", "", "" },
        { "wizard cast targeted", 2,
          "@The_monster@ casts a spell @at@ @target@.",
          true, false, cast_frame::DIRECT_EFFECT,
          "The orc casts a spell at you.",
          "兽人向你施展了一个法术。", "", "" },
        { "wizard cast", 0,
          "@The_monster@ gestures wildly while chanting.",
          false, true, cast_frame::GESTURE, "", "",
          "The orc gestures wildly while chanting.",
          "兽人一边吟诵，一边狂乱地做出手势。" },
        { "wizard cast", 1,
          "@The_monster@ mumbles some strange words.",
          false, false, cast_frame::VOCAL, "", "",
          "The orc mumbles some strange words.",
          "兽人咕哝着一些奇怪的话。" },
        { "wizard cast", 2,
          "@The_monster@ casts a spell.",
          false, false, cast_frame::DIRECT_EFFECT, "", "",
          "The orc casts a spell.", "兽人施展了一个法术。" },
        { "magical cast targeted", 0,
          "@The_monster@ gestures @at@ @target@.",
          true, true, cast_frame::GESTURE,
          "The orc gestures at you.", "兽人向你做出手势。", "", "" },
        { "magical cast", 0,
          "@The_monster@ gestures.",
          false, true, cast_frame::GESTURE, "", "",
          "The orc gestures.", "兽人做出手势。" },
    };

    for (const fixture &item : cases)
    {
        CAPTURE(item.key, item.ordinal);
        size_t calls = 0;
        binding_requirements observed;
        const canonical_textdb::loaded_candidate candidate =
            canonical_candidate(
                canonical_textdb::candidate_status::SELECTED,
                item.pattern, item.key, item.ordinal);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                item.key, message_attempt::NORMAL_OR_UNSEEN, true,
                [&](const binding_requirements &requirements)
                {
                    ++calls;
                    observed = requirements;
                    runtime_bindings values = beam_bindings(
                        requirements.resolves_target
                            ? target_relation::AT : target_relation::NONE);
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(calls == 1);
        CHECK(observed.resolves_target == item.resolves_target);
        CHECK(observed.implies_gesture == item.gesture);
        CHECK(observed.frame == item.frame);
        CHECK(materialized.binding.values.target_trace.empty());
        const render_result en =
            render_materialized_candidate(materialized, "en");
        const render_result zh =
            render_materialized_candidate(materialized, "zh");
        REQUIRE(en.result == message_result::RENDERED);
        REQUIRE(zh.result == message_result::RENDERED);
        CHECK(en.lines[0].text
              == (item.resolves_target ? item.en_at : item.en_none));
        CHECK(zh.lines[0].text
              == (item.resolves_target ? item.zh_at : item.zh_none));
    }
}

TEST_CASE("third Phase 2 batch has exact Chinese catalog goldens",
          "[single-file][message-overlay][phase2]")
{
    using namespace fork_message_overlay;
    struct fixture
    {
        const char *key;
        size_t ordinal;
        const char *pattern;
        bool resolves_target;
        bool gesture;
        cast_frame frame;
        sensory_mode sensory;
        const char *zh[3];
    };
    const fixture cases[] =
    {
        { "awaken flesh kobold fleshcrafter cast", 0,
          "@The_monster@ cackles and gestures.",
          false, true, cast_frame::GESTURE, sensory_mode::PLAIN,
          { "兽人咯咯笑着做出手势。", nullptr, nullptr } },
        { "awaken flesh kobold fleshcrafter cast", 1,
          "@The_monster@ chants and writhes.",
          false, false, cast_frame::VOCAL, sensory_mode::PLAIN,
          { "兽人一边吟诵，一边扭动身躯。", nullptr, nullptr } },
        { "dispel undead revenant cast", 0,
          "@The_monster@ gestures violently @at@ @target@.",
          true, true, cast_frame::GESTURE, sensory_mode::PLAIN,
          { "兽人向你猛烈地做出手势。",
            "兽人向你旁边猛烈地做出手势。",
            "兽人向你身后猛烈地做出手势。" } },
        { "malign offering priest cast", 0,
          "@The_monster@ utters a dark prayer and points @at@ @target@.",
          true, true, cast_frame::INVOCATION, sensory_mode::PLAIN,
          { "兽人低声念出一段黑暗祷词，指向你。",
            "兽人低声念出一段黑暗祷词，指向你旁边。",
            "兽人低声念出一段黑暗祷词，指向你身后。" } },
        { "sheza's dance cast", 0,
          "@The_monster@ sends weapons flying into battle!",
          false, false, cast_frame::DIRECT_EFFECT, sensory_mode::PLAIN,
          { "兽人让武器飞入战场！", nullptr, nullptr } },
        { "sheza's dance cast", 1,
          "@The_monster@ gestures, and weapons take to the air!",
          false, true, cast_frame::GESTURE, sensory_mode::PLAIN,
          { "兽人做出手势，武器随即飞上空中！", nullptr, nullptr } },
        { "silent blizzard demon cast", 0,
          "@The_monster@ lashes out with icy intensity.",
          false, false, cast_frame::DIRECT_EFFECT, sensory_mode::PLAIN,
          { "兽人以刺骨寒意猛烈出击。", nullptr, nullptr } },
        { "silent blizzard demon cast", 1,
          "@The_monster@ gestures with frozen lightning.",
          false, true, cast_frame::GESTURE, sensory_mode::PLAIN,
          { "兽人做出手势，释放出冰封闪电。", nullptr, nullptr } },
        { "ushabti cast targeted", 0,
          "@The_monster@ gestures stiffly @at@ @target@.",
          true, true, cast_frame::GESTURE, sensory_mode::PLAIN,
          { "兽人僵硬地向你做出手势。",
            "兽人僵硬地向你旁边做出手势。",
            "兽人僵硬地向你身后做出手势。" } },
        { "mennas cast", 0,
          "VISUAL:@The_monster@ gestures frantically.",
          false, true, cast_frame::GESTURE, sensory_mode::VISUAL,
          { "兽人疯狂地做出手势。", nullptr, nullptr } },
    };
    const target_relation relations[] =
    {
        target_relation::AT,
        target_relation::NEXT_TO,
        target_relation::PAST,
    };

    for (const fixture &item : cases)
    {
        CAPTURE(item.key, item.ordinal);
        const canonical_textdb::loaded_candidate candidate =
            canonical_candidate(
                canonical_textdb::candidate_status::SELECTED,
                item.pattern, item.key, item.ordinal);
        canonical_materialization materialized =
            materialize_monspell_candidate(
                item.key, message_attempt::NORMAL_OR_UNSEEN, true,
                [&](const binding_requirements &requirements)
                {
                    CHECK(requirements.resolves_target
                          == item.resolves_target);
                    CHECK(requirements.implies_gesture == item.gesture);
                    CHECK(requirements.frame == item.frame);
                    runtime_bindings values = beam_bindings(
                        requirements.resolves_target
                            ? target_relation::AT : target_relation::NONE);
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);

        const size_t relation_count = item.resolves_target ? 3 : 1;
        for (size_t relation = 0; relation < relation_count; ++relation)
        {
            if (item.resolves_target)
                materialized.binding.values.target.relation =
                    relations[relation];
            const render_result zh =
                render_materialized_candidate(materialized, "zh");
            REQUIRE(zh.result == message_result::RENDERED);
            REQUIRE(zh.lines.size() == 1);
            CHECK(zh.lines[0].text == item.zh[relation]);
            CHECK(zh.lines[0].sensory == item.sensory);
            CHECK(zh.lines[0].implies_gesture == item.gesture);
        }
    }
}

TEST_CASE("airstrike blizzard demon uses a fail-closed plural-arms slot",
          "[single-file][message-overlay][phase2]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    reset_monspell_overlay_for_test();
    REQUIRE(load_monspell_overlay(
        textdb_phase0::dump_canonical_english_speakdb()).state
        == domain_state::ENABLED);
    struct fixture
    {
        size_t ordinal;
        const char *pattern;
        bool gesture;
        cast_frame frame;
        const char *english;
        const char *chinese;
    };
    const fixture cases[] =
    {
        { 0, "@The_monster@ lashes out with icy intensity.",
          false, cast_frame::DIRECT_EFFECT,
          "The blizzard demon lashes out with icy intensity.",
          "暴雪恶魔以刺骨寒意猛烈出击。" },
        { 1, "@The_monster@ gestures with frozen lightning.",
          true, cast_frame::GESTURE,
          "The blizzard demon gestures with frozen lightning.",
          "暴雪恶魔做出手势，释放出冰封闪电。" },
        { 2, "@The_monster@ waves @possessive@ @arms@ in writhing circles.",
          false, cast_frame::GESTURE,
          "The blizzard demon waves its strata in writhing circles.",
          "暴雪恶魔挥动它的云层，令其盘旋扭动。" },
    };

    for (const fixture &item : cases)
    {
        CAPTURE(item.ordinal);
        const canonical_textdb::loaded_candidate candidate =
            canonical_candidate(
                canonical_textdb::candidate_status::SELECTED,
                item.pattern, "airstrike blizzard demon cast", item.ordinal);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "airstrike blizzard demon cast",
                message_attempt::NORMAL_OR_UNSEEN, true,
                [&](const binding_requirements &requirements)
                {
                    CHECK_FALSE(requirements.resolves_target);
                    CHECK(requirements.implies_gesture == item.gesture);
                    CHECK(requirements.frame == item.frame);
                    CHECK(requirements.needs_actor_arms_plural
                          == (item.ordinal == 2));
                    runtime_bindings values = blizzard_demon_bindings();
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        INFO(materialized.diagnostic);
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(materialized.binding.values.target_trace.empty());
        const render_result en =
            render_materialized_candidate(materialized, "en");
        const render_result zh =
            render_materialized_candidate(materialized, "zh");
        REQUIRE(en.result == message_result::RENDERED);
        REQUIRE(zh.result == message_result::RENDERED);
        CHECK(en.lines[0].text == item.english);
        CHECK(zh.lines[0].text == item.chinese);
        if (item.ordinal == 2)
        {
            CHECK(materialized.binding.values.actor.arms_plural_en == "strata");
            CHECK(materialized.bound_pattern_en == item.english);
        }
    }

    const canonical_textdb::loaded_candidate arms_candidate =
        canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            "@The_monster@ waves @possessive@ @arms@ in writhing circles.",
            "airstrike blizzard demon cast", 2);
    const auto materialize_arms =
        [&](const runtime_bindings &bindings)
        {
            return materialize_monspell_candidate(
                "airstrike blizzard demon cast",
                message_attempt::NORMAL_OR_UNSEEN, true,
                [&](const binding_requirements &requirements)
                {
                    runtime_bindings values = bindings;
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [arms_candidate](const string &) { return arms_candidate; });
        };

    runtime_bindings missing_canonical = blizzard_demon_bindings();
    missing_canonical.actor.arms_plural_en.clear();
    const canonical_materialization unavailable =
        materialize_arms(missing_canonical);
    CHECK(unavailable.result == message_result::CORRUPT);
    CHECK(unavailable.diagnostic == "runtime bindings are incomplete");

    runtime_bindings missing_localized = blizzard_demon_bindings();
    missing_localized.actor.arms_plural_localized.clear();
    const canonical_materialization missing =
        materialize_arms(missing_localized);
    REQUIRE(missing.result == message_result::RENDERED);
    const render_result missing_zh =
        render_materialized_candidate(missing, "zh");
    CHECK(missing_zh.result == message_result::CORRUPT);
    CHECK(missing_zh.diagnostic
          == "localized actor plural-arms binding is missing");

    runtime_bindings duplicate_localized = blizzard_demon_bindings();
    duplicate_localized.actor.arms_plural_localized.push_back(
        { "zh", "额外手臂" });
    const canonical_materialization duplicate =
        materialize_arms(duplicate_localized);
    REQUIRE(duplicate.result == message_result::RENDERED);
    const render_result duplicate_zh =
        render_materialized_candidate(duplicate, "zh");
    CHECK(duplicate_zh.result == message_result::CORRUPT);
    CHECK(duplicate_zh.diagnostic
          == "localized actor plural-arms binding is missing");
}

TEST_CASE("Vv and Jeremiah variants have exact weighted bilingual goldens",
          "[single-file][message-overlay][phase2]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    reset_monspell_overlay_for_test();
    REQUIRE(load_monspell_overlay(
        textdb_phase0::dump_canonical_english_speakdb()).state
        == domain_state::ENABLED);

    struct fixture
    {
        const char *key;
        size_t ordinal;
        int weight;
        const char *pattern;
        bool gesture;
        sensory_mode sensory;
        const char *english;
        const char *chinese;
    };
    const fixture cases[] =
    {
        { "vv cast", 0, 10,
          "VISUAL:@The_monster@ gestures sharply.", true,
          sensory_mode::VISUAL,
          "The orc gestures sharply.", "兽人猛然做出手势。" },
        { "vv cast", 1, 10,
          "VISUAL:@The_monster@ stamps @possessive@ foot.", false,
          sensory_mode::VISUAL,
          "The orc stamps its foot.", "兽人用它的脚猛跺地面。" },
        { "vv cast", 2, 10,
          "VISUAL:@The_monster@ slams @possessive@ palms together.", false,
          sensory_mode::VISUAL,
          "The orc slams its palms together.", "兽人用力合拢它的双掌。" },
        { "vv cast", 3, 3,
          "VISUAL:@The_monster@ makes an elaborate arcing motion.", false,
          sensory_mode::VISUAL,
          "The orc makes an elaborate arcing motion.",
          "兽人划出一道精巧的弧线。" },
        { "smiting jeremiah cast", 0, 10,
          "@The_monster@ lets out a twisted cry.", false,
          sensory_mode::PLAIN,
          "The orc lets out a twisted cry.", "兽人发出一声扭曲的喊叫。" },
        { "smiting jeremiah cast", 1, 10,
          "@The_monster@ mumbles a slurred invocation.", false,
          sensory_mode::PLAIN,
          "The orc mumbles a slurred invocation.",
          "兽人含糊不清地咕哝着祷文。" },
        { "smiting jeremiah cast", 2, 10,
          "VISUAL:@The_monster@ throws @possessive@ arms up pleadingly.",
          false, sensory_mode::VISUAL,
          "The orc throws its arms up pleadingly.",
          "兽人恳求般地举起它的双臂。" },
        { "smiting jeremiah cast", 3, 10,
          "@The_monster@ cries, \"Fearful master, protect me!\"", false,
          sensory_mode::PLAIN,
          "The orc cries, \"Fearful master, protect me!\"",
          "兽人哭喊道：“可畏的主人，保护我吧！”" },
        { "smiting jeremiah cast", 4, 10,
          "@The_monster@ shouts, \"O dreadful one, destroy my foe!\"", false,
          sensory_mode::PLAIN,
          "The orc shouts, \"O dreadful one, destroy my foe!\"",
          "兽人大喊道：“可怖者啊，毁灭我的敌人！”" },
    };

    const catalog_source &catalog = generated_monspell_catalog();
    for (const fixture &item : cases)
    {
        CAPTURE(item.key, item.ordinal);
        const auto entry = find_if(
            catalog.entries.begin(), catalog.entries.end(),
            [&](const catalog_entry &candidate)
            {
                return candidate.canonical_key == item.key;
            });
        REQUIRE(entry != catalog.entries.end());
        REQUIRE(item.ordinal < entry->variants.size());
        CHECK(entry->variants[item.ordinal].upstream_weight == item.weight);

        const canonical_textdb::loaded_candidate candidate =
            canonical_candidate(
                canonical_textdb::candidate_status::SELECTED,
                item.pattern, item.key, item.ordinal);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                item.key, message_attempt::NORMAL_OR_UNSEEN, true,
                [&](const binding_requirements &requirements)
                {
                    CHECK_FALSE(requirements.resolves_target);
                    CHECK_FALSE(requirements.needs_actor_arms_plural);
                    CHECK(requirements.implies_gesture == item.gesture);
                    runtime_bindings values =
                        beam_bindings(target_relation::NONE);
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(materialized.binding.values.target_trace.empty());
        const render_result en =
            render_materialized_candidate(materialized, "en");
        const render_result zh =
            render_materialized_candidate(materialized, "zh");
        REQUIRE(en.result == message_result::RENDERED);
        REQUIRE(zh.result == message_result::RENDERED);
        REQUIRE(en.lines.size() == 1);
        REQUIRE(zh.lines.size() == 1);
        CHECK(en.lines[0].text == item.english);
        CHECK(zh.lines[0].text == item.chinese);
        CHECK(en.lines[0].sensory == item.sensory);
        CHECK(zh.lines[0].sensory == item.sensory);
        CHECK(en.lines[0].implies_gesture == item.gesture);
        CHECK(zh.lines[0].implies_gesture == item.gesture);
    }
}

TEST_CASE("Wiglaf mortar variants keep relation and foe bindings independent",
          "[single-file][message-overlay][phase2][applicability][foe]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    reset_monspell_overlay_for_test();
    REQUIRE(load_monspell_overlay(
        textdb_phase0::dump_canonical_english_speakdb()).state
        == domain_state::ENABLED);

    const catalog_source &catalog = generated_monspell_catalog();
    const auto entry = find_if(
        catalog.entries.begin(), catalog.entries.end(),
        [](const catalog_entry &candidate)
        {
            return candidate.canonical_key
                   == "hellfire mortar wiglaf cast";
        });
    REQUIRE(entry != catalog.entries.end());
    REQUIRE(entry->variants.size() == 3);
    CHECK(entry->variants[0].conditions.requires_caster_visible);
    CHECK_FALSE(entry->variants[0].conditions.requires_foe);
    CHECK(entry->variants[1].conditions.requires_foe);
    CHECK(entry->variants[2].conditions.requires_foe);
    for (const catalog_variant &variant : entry->variants)
    {
        CHECK(variant.upstream_weight == 10);
        CHECK_FALSE(variant.lines[0].implies_gesture);
    }

    const char *patterns[] =
    {
        "VISUAL:@The_monster@ slams @possessive@ weapon against the ground.",
        "@The_monster@ shouts @at@ @foe@, \"Taste the blood o the mountain!\"",
        "@The_monster@ roars @at@ @foe@, \"Let me show ye whit a REAL cannon looks like!\"",
    };
    const target_relation relations[] =
    {
        target_relation::AT,
        target_relation::NEXT_TO,
        target_relation::PAST,
    };
    const char *relation_en[] = { "at", "next to", "past" };
    const char *relation_zh[] = { "", "旁边", "身后" };

    auto bindings = [](target_relation relation, const string &relation_text,
                       bool with_foe)
    {
        runtime_bindings values = beam_bindings(relation);
        values.actor.sentence_en = "Wiglaf";
        values.actor.canonical_en = "Wiglaf";
        values.actor.possessive_pronoun_en = "his";
        values.actor.localized =
            { { "en", "Wiglaf" }, { "zh", "威格拉夫" } };
        values.actor.possessive_pronoun_localized =
            { { "en", "his" }, { "zh", "他的" } };
        values.target.relation_en = relation_text;
        if (with_foe)
        {
            values.foe.kind = foe_kind::PLAYER;
            values.foe.canonical_en = "you";
            values.foe.localized =
                { { "en", "you" }, { "zh", "你" } };
        }
        return values;
    };

    SECTION("all variants render exact locale metadata")
    {
        for (size_t ordinal = 0; ordinal < 3; ++ordinal)
        {
            CAPTURE(ordinal);
            const bool targeted = ordinal > 0;
            const auto candidate = canonical_candidate(
                canonical_textdb::candidate_status::SELECTED,
                patterns[ordinal], "hellfire mortar wiglaf cast", ordinal);
            runtime_applicability applicability;
            applicability.caster_visibility = message_visibility::VISIBLE;
            size_t callback_count = 0;
            const canonical_materialization materialized =
                materialize_monspell_candidate(
                    "hellfire mortar wiglaf cast",
                    message_attempt::NORMAL_OR_UNSEEN, applicability,
                    [&](const binding_requirements &requirements)
                    {
                        ++callback_count;
                        CHECK(requirements.resolves_target == targeted);
                        CHECK(requirements.needs_foe == targeted);
                        CHECK_FALSE(requirements.implies_gesture);
                        runtime_bindings values = bindings(
                            targeted ? target_relation::AT
                                     : target_relation::NONE,
                            targeted ? "at" : "", targeted);
                        values.cast.frame = requirements.frame;
                        return values;
                    },
                    [candidate](const string &) { return candidate; });
            CAPTURE(materialized.diagnostic);
            REQUIRE(materialized.result == message_result::RENDERED);
            CHECK(callback_count == 1);
            const render_result en =
                render_materialized_candidate(materialized, "en");
            const render_result zh =
                render_materialized_candidate(materialized, "zh");
            REQUIRE(en.result == message_result::RENDERED);
            REQUIRE(zh.result == message_result::RENDERED);
            if (ordinal == 0)
            {
                CHECK(en.lines[0].text
                      == "Wiglaf slams his weapon against the ground.");
                CHECK(zh.lines[0].text
                      == "威格拉夫将他的武器砸向地面。");
                CHECK(en.lines[0].sensory == sensory_mode::VISUAL);
            }
            else if (ordinal == 1)
            {
                CHECK(en.lines[0].text
                      == "Wiglaf shouts at you, \"Taste the blood o the mountain!\"");
                CHECK(zh.lines[0].text
                      == "威格拉夫向你喊道：“尝尝大山的血！”");
            }
            else
            {
                CHECK(en.lines[0].text
                      == "Wiglaf roars at you, \"Let me show ye whit a REAL cannon looks like!\"");
                CHECK(zh.lines[0].text
                      == "威格拉夫向你咆哮道：“让老子给你看看什么才叫真正的炮！”");
            }
        }
    }

    SECTION("every target relation keeps the same independent foe")
    {
        for (size_t ordinal = 1; ordinal <= 2; ++ordinal)
        {
            for (size_t relation = 0; relation < 3; ++relation)
            {
                CAPTURE(ordinal, relation);
                const auto candidate = canonical_candidate(
                    canonical_textdb::candidate_status::SELECTED,
                    patterns[ordinal], "hellfire mortar wiglaf cast", ordinal);
                runtime_applicability applicability;
                applicability.caster_visibility = message_visibility::VISIBLE;
                const canonical_materialization materialized =
                    materialize_monspell_candidate(
                        "hellfire mortar wiglaf cast",
                        message_attempt::NORMAL_OR_UNSEEN, applicability,
                        [&](const binding_requirements &requirements)
                        {
                            runtime_bindings values =
                                bindings(relations[relation],
                                         relation_en[relation], true);
                            values.cast.frame = requirements.frame;
                            return values;
                        },
                        [candidate](const string &) { return candidate; });
                CAPTURE(materialized.diagnostic);
                REQUIRE(materialized.result == message_result::RENDERED);
                const render_result zh =
                    render_materialized_candidate(materialized, "zh");
                REQUIRE(zh.result == message_result::RENDERED);
                CHECK(zh.lines[0].text.find(
                          "向你" + string(relation_zh[relation]))
                      != string::npos);
            }
        }
    }

    SECTION("normal missing foe skips callback and candidate")
    {
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            patterns[1], "hellfire mortar wiglaf cast", 1);
        runtime_applicability applicability;
        applicability.foe_applicable = false;
        applicability.caster_visibility = message_visibility::VISIBLE;
        size_t callback_count = 0;
        canonical_materialization observed;
        const message_candidate_search search =
            search_message_candidate(
                "hellfire mortar wiglaf cast", message_prefix::NORMAL,
                [&](const message_lookup_request &request)
                {
                    observed = materialize_monspell_candidate(
                        "hellfire mortar wiglaf cast", request.attempt,
                        applicability,
                        [&](const binding_requirements &)
                        {
                            ++callback_count;
                            return bindings(target_relation::AT, "at", false);
                        },
                        [candidate](const string &) { return candidate; });
                    return lookup_result(observed.result, "", true);
                });
        CHECK(observed.result == message_result::INAPPLICABLE);
        CHECK(search.action == message_search_action::NEXT_CANDIDATE);
        CHECK(callback_count == 0);
        CHECK(observed.binding.callback_count == 0);
        CHECK(observed.binding.values.target_trace.empty());
    }

    SECTION("silent missing foe cannot leak protocol")
    {
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            patterns[1], "hellfire mortar wiglaf cast", 1);
        runtime_applicability applicability;
        applicability.foe_applicable = false;
        applicability.caster_visibility = message_visibility::VISIBLE;
        size_t callback_count = 0;
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "hellfire mortar wiglaf cast",
                message_attempt::SILENT_UNPREFIXED_FALLBACK, applicability,
                [&](const binding_requirements &)
                {
                    ++callback_count;
                    return bindings(target_relation::AT, "at", false);
                },
                [candidate](const string &) { return candidate; });
        CHECK(materialized.result == message_result::CORRUPT);
        CHECK(materialized.diagnostic == "runtime bindings are incomplete");
        CHECK(callback_count == 1);
    }

    SECTION("unseen visual variant skips binding")
    {
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            patterns[0], "hellfire mortar wiglaf cast", 0);
        runtime_applicability applicability;
        applicability.caster_visibility = message_visibility::UNSEEN;
        size_t callback_count = 0;
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "hellfire mortar wiglaf cast",
                message_attempt::NORMAL_OR_UNSEEN, applicability,
                [&](const binding_requirements &)
                {
                    ++callback_count;
                    return bindings(target_relation::NONE, "", false);
                },
                [candidate](const string &) { return candidate; });
        CHECK(materialized.result == message_result::INAPPLICABLE);
        CHECK(callback_count == 0);
    }
}

TEST_CASE("Nergalle recursive captures are ordered and vocabulary-bound",
          "[single-file][message-overlay][phase2][capture]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    reset_monspell_overlay_for_test();
    REQUIRE(load_monspell_overlay(
        textdb_phase0::dump_canonical_english_speakdb()).state
        == domain_state::ENABLED);

    canonical_textdb::loaded_candidate selected;
    for (uint64_t seed = 1; seed <= 4096; ++seed)
    {
        rng::subgenerator scoped_rng(
            seed, seed ^ 0x9e3779b97f4a7c15ULL);
        selected = canonical_textdb::expand_loaded_english_candidate(
            "vanquished vanguard nergalle cast");
        if (selected.status == canonical_textdb::candidate_status::SELECTED
            && selected.top_locator.variant_ordinal == 0)
        {
            break;
        }
    }
    REQUIRE(selected.top_locator.variant_ordinal == 0);

    auto bindings = [](const binding_requirements &requirements)
    {
        runtime_bindings values = beam_bindings(target_relation::NONE);
        values.actor.sentence_en = "Nergalle";
        values.actor.canonical_en = "Nergalle";
        values.actor.localized =
            { { "en", "Nergalle" }, { "zh", "内尔加勒" } };
        values.cast.frame = requirements.frame;
        return values;
    };
    runtime_applicability applicability;
    applicability.caster_visibility = message_visibility::VISIBLE;

    size_t callback_count = 0;
    const canonical_materialization materialized =
        materialize_monspell_candidate(
            "vanquished vanguard nergalle cast",
            message_attempt::NORMAL_OR_UNSEEN, applicability,
            [&](const binding_requirements &requirements)
            {
                ++callback_count;
                CHECK_FALSE(requirements.resolves_target);
                CHECK_FALSE(requirements.implies_gesture);
                return bindings(requirements);
            },
            [selected](const string &) { return selected; });
    CAPTURE(materialized.diagnostic);
    REQUIRE(materialized.result == message_result::RENDERED);
    CHECK(callback_count == 1);
    REQUIRE(materialized.recursive_captures.size() == 3);
    CHECK(materialized.randomized.signature.find("materialization-v1|") == 0);
    CHECK(materialized.materialization_signature
          == materialized.randomized.signature);
    const render_result en =
        render_materialized_candidate(materialized, "en");
    const render_result zh =
        render_materialized_candidate(materialized, "zh");
    REQUIRE(en.result == message_result::RENDERED);
    REQUIRE(zh.result == message_result::RENDERED);
    CHECK(en.lines[0].text == materialized.randomized.pattern_en);
    CHECK(zh.lines[0].text
          == "内尔加勒呼唤道：“"
             + materialized.recursive_captures[0].value + "、"
             + materialized.recursive_captures[1].value + "、"
             + materialized.recursive_captures[2].value
             + "——到我这里来！”");

    SECTION("renderer rejects both identity signatures changed together")
    {
        canonical_materialization corrupt = materialized;
        corrupt.materialization_signature += "|tampered";
        corrupt.randomized.signature = corrupt.materialization_signature;
        const render_result rejected =
            render_materialized_candidate(corrupt, "en");
        CHECK(rejected.result == message_result::CORRUPT);
        CHECK(rejected.diagnostic
              == "materialized capture identity is invalid");
    }

    SECTION("renderer rejects a changed capture value")
    {
        canonical_materialization corrupt = materialized;
        corrupt.recursive_captures[0].value = "INJECTED";
        const render_result rejected =
            render_materialized_candidate(corrupt, "zh");
        CHECK(rejected.result == message_result::CORRUPT);
        CHECK(rejected.diagnostic
              == "materialized capture values do not match canonical trace");
    }

    SECTION("opaque replacement injection is rejected before binding")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        auto site = find_if(
            corrupt.trace.recursive_sites.begin(),
            corrupt.trace.recursive_sites.end(),
            [](const canonical_textdb::recursive_site_trace &candidate)
            {
                return candidate.recursion_path.size() == 1
                       && candidate.marker == "orc name";
            });
        REQUIRE(site != corrupt.trace.recursive_sites.end());
        site->replacement = "INJECTED";
        callback_count = 0;
        const canonical_materialization rejected =
            materialize_monspell_candidate(
                "vanquished vanguard nergalle cast",
                message_attempt::NORMAL_OR_UNSEEN, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++callback_count;
                    return bindings(requirements);
                },
                [corrupt](const string &) { return corrupt; });
        CHECK(rejected.result == message_result::CORRUPT);
        CHECK(rejected.diagnostic
              == "recursive capture topology is invalid");
        CHECK(callback_count == 0);
    }

    SECTION("incomplete capture trace is rejected")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        corrupt.trace.recursive_sites.pop_back();
        callback_count = 0;
        const canonical_materialization rejected =
            materialize_monspell_candidate(
                "vanquished vanguard nergalle cast",
                message_attempt::SILENT_UNPREFIXED_FALLBACK, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++callback_count;
                    return bindings(requirements);
                },
                [corrupt](const string &) { return corrupt; });
        CHECK(rejected.result == message_result::CORRUPT);
        CHECK(rejected.diagnostic
              == "recursive capture trace shape is invalid");
        CHECK(callback_count == 0);
    }

    auto reject_trace = [&](canonical_textdb::loaded_candidate corrupt)
    {
        callback_count = 0;
        const canonical_materialization rejected =
            materialize_monspell_candidate(
                "vanquished vanguard nergalle cast",
                message_attempt::NORMAL_OR_UNSEEN, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++callback_count;
                    return bindings(requirements);
                },
                [corrupt](const string &) { return corrupt; });
        CHECK(rejected.result == message_result::CORRUPT);
        CHECK(callback_count == 0);
    };

    SECTION("choice ordinal mismatch is rejected")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        ++corrupt.trace.weighted_choices[2].variant_ordinal;
        reject_trace(corrupt);
    }

    SECTION("choice key mismatch is rejected")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        corrupt.trace.weighted_choices[2].resolved_canonical_key =
            "_orcish_name_";
        reject_trace(corrupt);
    }

    SECTION("choice path mismatch is rejected")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        corrupt.trace.weighted_choices[2].recursion_path = { 1, 1 };
        reject_trace(corrupt);
    }

    SECTION("selected variant mismatch is rejected")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        ++corrupt.selected_variants[2].locator.variant_ordinal;
        reject_trace(corrupt);
    }

    SECTION("coordinated parent ordinal change cannot retain the old leaf")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        const size_t parent_index = 1;
        const size_t changed_ordinal =
            (corrupt.trace.weighted_choices[parent_index].variant_ordinal + 1)
            % 3;
        corrupt.trace.weighted_choices[parent_index].variant_ordinal =
            changed_ordinal;
        corrupt.selected_variants[parent_index].locator.variant_ordinal =
            changed_ordinal;
        reject_trace(corrupt);
    }

    SECTION("non-capture recursive site mutation is rejected")
    {
        canonical_textdb::loaded_candidate corrupt = selected;
        corrupt.trace.recursive_sites[0].marker = "other";
        reject_trace(corrupt);
    }
}

TEST_CASE("Gastronok cantrip variants preserve weights, locale and applicability",
          "[single-file][message-overlay][phase2][applicability]")
{
    using namespace fork_message_overlay;
    ensure_overlay_data_root();
    databaseSystemInit();
    reset_monspell_overlay_for_test();
    REQUIRE(load_monspell_overlay(
        textdb_phase0::dump_canonical_english_speakdb()).state
        == domain_state::ENABLED);

    struct fixture
    {
        const char *pattern;
        int weight;
        sensory_mode sensory;
        const char *english;
        const char *chinese;
    };
    const fixture cases[] =
    {
        { "@The_monster@ bubbles merrily.", 10, sensory_mode::PLAIN,
          "Gastronok bubbles merrily.", "加斯特罗诺克欢快地咕嘟冒泡。" },
        { "VISUAL:@The_monster@ glows a brilliant shade of cerise.", 10,
          sensory_mode::VISUAL,
          "Gastronok glows a brilliant shade of cerise.",
          "加斯特罗诺克泛起鲜亮的樱桃红光芒。" },
        { "VISUAL:@The_monster@ wobbles crazily.", 10,
          sensory_mode::VISUAL,
          "Gastronok wobbles crazily.", "加斯特罗诺克疯狂地摇晃起来。" },
        { "VISUAL:@The_monster_possessive@ eyestalks stretch out, then return to normal size.",
          10, sensory_mode::VISUAL,
          "Gastronok's eyestalks stretch out, then return to normal size.",
          "加斯特罗诺克的眼柄伸展开来，随后恢复原状。" },
        { "You wobble.", 10, sensory_mode::PLAIN,
          "You wobble.", "你晃了晃。" },
        { "You take on a slight green cast.", 10, sensory_mode::PLAIN,
          "You take on a slight green cast.", "你的脸色微微发绿。" },
        { "You feel briefly sluggish.", 10, sensory_mode::PLAIN,
          "You feel briefly sluggish.", "你短暂地感到迟钝。" },
        { "You feel a sudden, passing aversion to salt.", 10,
          sensory_mode::PLAIN,
          "You feel a sudden, passing aversion to salt.",
          "你突然对盐产生了一阵厌恶。" },
        { "You feel a sudden urge to swivel your nonexistent eyestalks around.",
          5, sensory_mode::PLAIN,
          "You feel a sudden urge to swivel your nonexistent eyestalks around.",
          "你突然很想转动自己并不存在的眼柄。" },
    };

    const catalog_source &catalog = generated_monspell_catalog();
    const auto entry = find_if(
        catalog.entries.begin(), catalog.entries.end(),
        [](const catalog_entry &candidate)
        {
            return candidate.canonical_key == "cantrip gastronok cast";
        });
    REQUIRE(entry != catalog.entries.end());
    REQUIRE(entry->variants.size() == 9);

    auto gastronok_bindings = []()
    {
        runtime_bindings values = beam_bindings(target_relation::NONE);
        values.actor.sentence_en = "Gastronok";
        values.actor.canonical_en = "Gastronok";
        values.actor.possessive_name_en = "Gastronok's";
        values.actor.localized =
            { { "en", "Gastronok" }, { "zh", "加斯特罗诺克" } };
        values.actor.possessive_name_localized =
            { { "en", "Gastronok's" }, { "zh", "加斯特罗诺克的" } };
        return values;
    };

    for (size_t ordinal = 0; ordinal < entry->variants.size(); ++ordinal)
    {
        CAPTURE(ordinal);
        const catalog_variant &descriptor = entry->variants[ordinal];
        CHECK(descriptor.upstream_weight == cases[ordinal].weight);
        CHECK(descriptor.conditions.requires_caster_visible
              == (ordinal >= 1 && ordinal <= 3));
        runtime_applicability applicability;
        applicability.caster_visibility = message_visibility::VISIBLE;
        size_t binding_calls = 0;
        const canonical_textdb::loaded_candidate candidate =
            canonical_candidate(
                canonical_textdb::candidate_status::SELECTED,
                cases[ordinal].pattern, "cantrip gastronok cast", ordinal);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "cantrip gastronok cast",
                message_attempt::NORMAL_OR_UNSEEN, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++binding_calls;
                    CHECK_FALSE(requirements.resolves_target);
                    CHECK_FALSE(requirements.implies_gesture);
                    runtime_bindings values = gastronok_bindings();
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(binding_calls == 1);
        CHECK(materialized.binding.values.target_trace.empty());
        const render_result en =
            render_materialized_candidate(materialized, "en");
        const render_result zh =
            render_materialized_candidate(materialized, "zh");
        REQUIRE(en.result == message_result::RENDERED);
        REQUIRE(zh.result == message_result::RENDERED);
        REQUIRE(en.lines.size() == 1);
        REQUIRE(zh.lines.size() == 1);
        CHECK(en.lines[0].text == cases[ordinal].english);
        CHECK(zh.lines[0].text == cases[ordinal].chinese);
        CHECK(en.lines[0].sensory == cases[ordinal].sensory);
        CHECK(zh.lines[0].sensory == cases[ordinal].sensory);
        CHECK_FALSE(en.lines[0].implies_gesture);
        CHECK_FALSE(zh.lines[0].implies_gesture);
    }

    SECTION("unseen visual selection consumes canonical RNG then skips binding")
    {
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            cases[1].pattern, "cantrip gastronok cast", 1);
        uint64_t expected_state = 0;
        uint64_t expected_count = 0;
        {
            rng::subgenerator scoped_rng(0x91a2, 0x37b4);
            (void) random2(97);
            expected_state = rng::current_generator().get_state();
            expected_count = rng::current_generator().get_count();
        }
        size_t lookup_calls = 0;
        size_t binding_calls = 0;
        runtime_applicability applicability;
        applicability.caster_visibility = message_visibility::UNSEEN;
        rng::subgenerator scoped_rng(0x91a2, 0x37b4);
        canonical_materialization observed;
        const message_candidate_search search =
            search_message_candidate(
                "cantrip gastronok cast", message_prefix::NORMAL,
                [&](const message_lookup_request &request)
                {
                    CHECK(request.attempt
                          == message_attempt::NORMAL_OR_UNSEEN);
                    observed = materialize_monspell_candidate(
                        "cantrip gastronok cast", request.attempt,
                        applicability,
                        [&](const binding_requirements &)
                        {
                            ++binding_calls;
                            return gastronok_bindings();
                        },
                        [&](const string &)
                        {
                            ++lookup_calls;
                            (void) random2(97);
                            return candidate;
                        });
                    return lookup_result(observed.result, "", true);
                });
        CHECK(observed.result == message_result::INAPPLICABLE);
        CHECK(search.action == message_search_action::NEXT_CANDIDATE);
        CHECK(search.lookup_count == 1);
        CHECK(lookup_calls == 1);
        CHECK(binding_calls == 0);
        CHECK(rng::current_generator().get_state() == expected_state);
        CHECK(rng::current_generator().get_count() == expected_count);
        CHECK(observed.binding.callback_count == 0);
        CHECK(observed.binding.values.target_trace.empty());
    }

    SECTION("unseen plain player line remains renderable")
    {
        runtime_applicability applicability;
        applicability.caster_visibility = message_visibility::UNSEEN;
        size_t binding_calls = 0;
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            cases[4].pattern, "cantrip gastronok cast", 4);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "cantrip gastronok cast",
                message_attempt::NORMAL_OR_UNSEEN, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++binding_calls;
                    runtime_bindings values = gastronok_bindings();
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(binding_calls == 1);
        const render_result zh =
            render_materialized_candidate(materialized, "zh");
        REQUIRE(zh.result == message_result::RENDERED);
        CHECK(zh.lines[0].text == "你晃了晃。");
    }

    SECTION("player-directed line without player applicability skips binding")
    {
        runtime_applicability applicability;
        applicability.player_applicable = false;
        applicability.caster_visibility = message_visibility::VISIBLE;
        size_t binding_calls = 0;
        size_t lookup_calls = 0;
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            cases[4].pattern, "cantrip gastronok cast", 4);
        canonical_materialization observed;
        const message_candidate_search search =
            search_message_candidate(
                "cantrip gastronok cast", message_prefix::NORMAL,
                [&](const message_lookup_request &request)
                {
                    observed = materialize_monspell_candidate(
                        "cantrip gastronok cast", request.attempt,
                        applicability,
                        [&](const binding_requirements &)
                        {
                            ++binding_calls;
                            return gastronok_bindings();
                        },
                        [&](const string &)
                        {
                            ++lookup_calls;
                            return candidate;
                        });
                    return lookup_result(observed.result, "", true);
                });
        CHECK(observed.result == message_result::INAPPLICABLE);
        CHECK(search.action == message_search_action::NEXT_CANDIDATE);
        CHECK(search.lookup_count == 1);
        CHECK(lookup_calls == 1);
        CHECK(binding_calls == 0);
        CHECK(observed.binding.callback_count == 0);
        CHECK(observed.binding.values.target_trace.empty());
    }

    SECTION("caster plain line does not require player applicability")
    {
        runtime_applicability applicability;
        applicability.player_applicable = false;
        applicability.caster_visibility = message_visibility::VISIBLE;
        size_t binding_calls = 0;
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            cases[0].pattern, "cantrip gastronok cast", 0);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "cantrip gastronok cast",
                message_attempt::NORMAL_OR_UNSEEN, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++binding_calls;
                    runtime_bindings values = gastronok_bindings();
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(binding_calls == 1);
        const render_result en =
            render_materialized_candidate(materialized, "en");
        REQUIRE(en.result == message_result::RENDERED);
        CHECK(en.lines[0].text == "Gastronok bubbles merrily.");
    }

    SECTION("silent unprefixed fallback preserves accept-any bypass")
    {
        runtime_applicability applicability;
        applicability.caster_visibility = message_visibility::UNSEEN;
        size_t binding_calls = 0;
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            cases[1].pattern, "cantrip gastronok cast", 1);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "cantrip gastronok cast",
                message_attempt::SILENT_UNPREFIXED_FALLBACK, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++binding_calls;
                    runtime_bindings values = gastronok_bindings();
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(binding_calls == 1);
        const render_result en =
            render_materialized_candidate(materialized, "en");
        REQUIRE(en.result == message_result::RENDERED);
        CHECK(en.lines[0].sensory == sensory_mode::VISUAL);
    }

    SECTION("silent unprefixed fallback also bypasses player applicability")
    {
        runtime_applicability applicability;
        applicability.player_applicable = false;
        applicability.caster_visibility = message_visibility::VISIBLE;
        size_t binding_calls = 0;
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            cases[4].pattern, "cantrip gastronok cast", 4);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "cantrip gastronok cast",
                message_attempt::SILENT_UNPREFIXED_FALLBACK, applicability,
                [&](const binding_requirements &requirements)
                {
                    ++binding_calls;
                    runtime_bindings values = gastronok_bindings();
                    values.cast.frame = requirements.frame;
                    return values;
                },
                [candidate](const string &) { return candidate; });
        REQUIRE(materialized.result == message_result::RENDERED);
        CHECK(binding_calls == 1);
    }

    SECTION("required visibility cannot be unknown")
    {
        runtime_applicability applicability;
        applicability.caster_visibility = message_visibility::UNKNOWN;
        size_t binding_calls = 0;
        const auto candidate = canonical_candidate(
            canonical_textdb::candidate_status::SELECTED,
            cases[1].pattern, "cantrip gastronok cast", 1);
        const canonical_materialization materialized =
            materialize_monspell_candidate(
                "cantrip gastronok cast",
                message_attempt::NORMAL_OR_UNSEEN, applicability,
                [&](const binding_requirements &)
                {
                    ++binding_calls;
                    return gastronok_bindings();
                },
                [candidate](const string &) { return candidate; });
        CHECK(materialized.result == message_result::CORRUPT);
        CHECK(materialized.diagnostic
              == "caster visibility is required but unknown");
        CHECK(binding_calls == 0);
    }
}
