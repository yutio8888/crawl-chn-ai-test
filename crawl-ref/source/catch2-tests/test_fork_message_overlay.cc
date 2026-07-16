#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "fork-message-overlay.h"
#include "initfile.h"
#include "random.h"

#include <unistd.h>

#include <deque>

namespace
{
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

canonical_textdb::loaded_candidate canonical_candidate(
    canonical_textdb::candidate_status status, const string &pattern = "")
{
    canonical_textdb::loaded_candidate candidate;
    candidate.status = status;
    candidate.expanded_pattern_en = pattern;
    if (status == canonical_textdb::candidate_status::SELECTED)
    {
        candidate.top_locator = { "beam catchall cast", 0 };
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
    values.actor.localized = { { "en", "The orc" }, { "zh", "兽人" } };
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

    SECTION("valid generated catalog enables both candidate keys")
    {
        scoped_overlay_reset reset;
        rng::subgenerator scoped_rng(0x1234, 0x5678);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const load_report &report = load_monspell_overlay(canonical);
        CHECK(report.state == domain_state::ENABLED);
        CHECK(report.failure == load_failure::NONE);
        CHECK(report.structured_key_count == 2);
        CHECK(monspell_overlay_covers("BEAM CATCHALL CAST"));
        CHECK(monspell_overlay_covers("march of sorrows bone dragon cast"));
        CHECK_FALSE(monspell_overlay_covers(
            "vanquished vanguard nergalle cast"));
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
        source.entries[0].canonical_fingerprint = "fnv1a64:0000000000000000";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        source.entries[0].variants[0].lines[0].templates[0].pattern +=
            " @target@";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);
    }

    SECTION("partial selectable closure disables the whole domain")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        source.entries[0].variants.clear();
        const load_report &report = load_monspell_overlay(canonical, &source);
        CHECK(report.state == domain_state::DISABLED);
        CHECK(report.failure == load_failure::CLOSURE_INCOMPLETE);
        CHECK(report.structured_key_count == 0);
    }

    SECTION("CASE_MAP signatures and slot types are load-time invariants")
    {
        scoped_overlay_reset reset;
        catalog_source source = generated_monspell_catalog();
        source.entries[1].variants[0].materialization_cases[1].signature =
            "forged-signature";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        source.entries[1].variants[0].materialization_cases.pop_back();
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        source.entries[1].variants[0].slot_schema[0].type = "unknown_ref";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        source.entries[1].variants[0].slot_schema[1].type = "resolved_beam";
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        source.entries[1].variants[0].conditions.requires_foe = true;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        source.entries[0].mode = entry_mode::CLOSURE_ONLY;
        source.entries[0].variants[0].conditions.requires_foe = true;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);

        reset_monspell_overlay_for_test();
        source = generated_monspell_catalog();
        source.entries[1].variants[0].materialization_cases[0]
            .lines[0].implies_gesture = true;
        CHECK(load_monspell_overlay(canonical, &source).failure
              == load_failure::CORRUPT);
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
            "Vanquished Vanguard Nergalle cast");
        CHECK(covered.route == message_route::STRUCTURED);
        CHECK(covered.canonical_key == "beam catchall cast");
        CHECK(uncovered.route == message_route::LEGACY);
        const diagnostic_counters diagnostics =
            monspell_overlay_diagnostics();
        CHECK(diagnostics.domain == "monspell");
        CHECK(diagnostics.schema_version == MONSPELL_OVERLAY_SCHEMA_VERSION);
        CHECK(diagnostics.overlay_hit == 1);
        CHECK(diagnostics.legacy_fallback == 1);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }

    SECTION("disabled domain routes every key to legacy before lookup")
    {
        scoped_overlay_reset reset;
        REQUIRE(load_monspell_overlay(canonical, nullptr).state
                == domain_state::DISABLED);
        CHECK(route_monspell_message("beam catchall cast").route
              == message_route::LEGACY);
        const diagnostic_counters diagnostics =
            monspell_overlay_diagnostics();
        CHECK(diagnostics.overlay_hit == 0);
        CHECK(diagnostics.legacy_fallback == 1);
    }

    SECTION("unsupported language routes legacy before lookup")
    {
        scoped_overlay_reset reset;
        REQUIRE(load_monspell_overlay(canonical).state
                == domain_state::ENABLED);
        rng::subgenerator scoped_rng(0x2111, 0x2222);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        CHECK(route_monspell_message("beam catchall cast", "fr").route
              == message_route::LEGACY);
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
        CHECK(route_monspell_message("beam catchall cast").route
              == message_route::LEGACY);
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
    const runtime_binding_resolver bindings = [&]()
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
            [] { return beam_bindings(target_relation::AT); });
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
    CHECK(render_typed_template("plain", one, value).result
          == message_result::CORRUPT);
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
                        [=] { return beam_bindings(relation, kind, visibility); },
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
                [&]
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
        [&]
        {
            ++forged_binding_calls;
            return beam_bindings(target_relation::AT);
        },
        [forged](const string &) { return forged; });
    CHECK(unknown.result == message_result::CORRUPT);
    CHECK(unknown.diagnostic == "CASE_MAP materialization signature is unknown");
    CHECK(forged_binding_calls == 1);
}
