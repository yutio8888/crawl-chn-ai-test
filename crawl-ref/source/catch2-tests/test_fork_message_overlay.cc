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

    SECTION("valid generated catalog enables only the candidate key")
    {
        scoped_overlay_reset reset;
        rng::subgenerator scoped_rng(0x1234, 0x5678);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        const load_report &report = load_monspell_overlay(canonical);
        CHECK(report.state == domain_state::ENABLED);
        CHECK(report.failure == load_failure::NONE);
        CHECK(report.structured_key_count == 1);
        CHECK(monspell_overlay_covers("BEAM CATCHALL CAST"));
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
