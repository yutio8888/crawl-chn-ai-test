#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "fork-message-overlay.h"
#include "initfile.h"
#include "random.h"

#include <unistd.h>

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
    }
    ~scoped_overlay_reset()
    {
        fork_message_overlay::reset_monspell_overlay_for_test();
    }
};
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
