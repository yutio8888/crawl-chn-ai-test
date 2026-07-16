#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>

namespace textdb_phase0
{
struct canonical_entry;
}

namespace fork_message_overlay
{
constexpr int MONSPELL_OVERLAY_SCHEMA_VERSION = 1;

enum class domain_state
{
    UNINITIALIZED,
    ENABLED,
    DISABLED,
};

enum class load_failure
{
    NONE,
    NOT_LOADED,
    MISSING,
    CORRUPT,
    UNKNOWN_SCHEMA,
    CLOSURE_INCOMPLETE,
};

enum class message_result
{
    MISSING,
    SUPPRESS,
    INAPPLICABLE,
    RENDERED,
    CORRUPT,
};

enum class message_attempt
{
    NORMAL_OR_UNSEEN,
    SILENT_PREFIXED,
    SILENT_UNPREFIXED_FALLBACK,
};

enum class message_search_action
{
    NEXT_CANDIDATE,
    RETRY_UNPREFIXED,
    STOP_SILENT,
    STOP_RENDERED,
    STOP_CORRUPT,
};

enum class message_prefix
{
    NORMAL,
    UNSEEN,
    SILENT,
};

enum class applicability_policy
{
    REQUIRE_APPLICABLE,
    ACCEPT_ANY_NONEMPTY,
};

enum class message_route
{
    STRUCTURED,
    LEGACY,
};

enum class entry_mode
{
    CANDIDATE,
    CLOSURE_ONLY,
    LEGACY_ONLY,
};

enum class materialization_policy
{
    NONE,
    CASE_MAP,
    CAPTURE_SLOT,
    LEGACY_ONLY,
};

enum class cast_frame
{
    PROJECTILE,
    GAZE,
    GESTURE,
    VOCAL,
    INVOCATION,
    DIRECT_EFFECT,
};

enum class sensory_mode
{
    PLAIN,
    VISUAL,
    SOUND,
};

struct applicability
{
    bool requires_player = false;
    bool requires_foe = false;
    bool requires_named_foe = false;
    bool requires_god = false;
    bool requires_caster_visible = false;
};

struct slot_definition
{
    std::string name;
    std::string type;
};

struct localized_template
{
    std::string language;
    std::string relation;
    std::string pattern;
};

struct line_metadata
{
    sensory_mode sensory = sensory_mode::PLAIN;
    std::string channel;
    bool implies_gesture = false;
    bool audible = false;
    std::vector<localized_template> templates;
};

struct materialization_case
{
    std::string case_id;
    std::string signature;
    std::vector<line_metadata> lines;
};

struct catalog_variant
{
    std::string stable_id;
    bool tombstone = false;
    size_t variant_ordinal = static_cast<size_t>(-1);
    int upstream_weight = 0;
    std::string upstream_variant_fingerprint;
    std::string english_snapshot;
    cast_frame frame = cast_frame::DIRECT_EFFECT;
    applicability conditions;
    materialization_policy policy = materialization_policy::LEGACY_ONLY;
    std::vector<slot_definition> slot_schema;
    std::vector<std::string> required_arguments;
    std::vector<line_metadata> lines;
    std::vector<materialization_case> materialization_cases;
    std::vector<std::string> recursive_dependencies;
    std::vector<std::string> recursive_dependency_fingerprints;
};

struct catalog_entry
{
    std::string canonical_key;
    std::string canonical_fingerprint;
    std::string selection_graph_fingerprint;
    entry_mode mode = entry_mode::LEGACY_ONLY;
    std::vector<catalog_variant> variants;
};

struct tombstone_record
{
    std::string stable_id;
    std::string reason;
};

struct catalog_source
{
    int schema_version = 0;
    std::string domain;
    std::string inventory_semantic_fingerprint;
    std::vector<std::string> supported_languages;
    std::vector<catalog_entry> entries;
    std::vector<tombstone_record> tombstones;
};

struct load_report
{
    domain_state state = domain_state::UNINITIALIZED;
    load_failure failure = load_failure::NONE;
    std::string diagnostic;
    size_t structured_key_count = 0;
};

// All fields own their data. Stage 2 deliberately does not expose Phase 0
// selection/materialization types as part of the production adapter API.
struct message_lookup_result
{
    message_result result = message_result::MISSING;
    std::string message;
    std::string diagnostic;
    bool applicability_checked = false;
};

struct message_lookup_request
{
    std::string lookup_key;
    message_attempt attempt = message_attempt::NORMAL_OR_UNSEEN;
    applicability_policy applicability =
        applicability_policy::REQUIRE_APPLICABLE;
};

struct message_candidate_search
{
    message_lookup_result lookup;
    message_search_action action = message_search_action::NEXT_CANDIDATE;
    size_t lookup_count = 0;
};

using message_lookup = std::function<message_lookup_result(
    const message_lookup_request &)>;

struct route_decision
{
    message_route route = message_route::LEGACY;
    std::string canonical_key;
    int schema_version = MONSPELL_OVERLAY_SCHEMA_VERSION;
};

struct diagnostic_counters
{
    std::string domain = "monspell";
    int schema_version = MONSPELL_OVERLAY_SCHEMA_VERSION;
    uint64_t overlay_hit = 0;
    uint64_t legacy_fallback = 0;
    uint64_t candidate_inapplicable = 0;
    uint64_t message_suppressed = 0;
    uint64_t overlay_corrupt = 0;
    uint64_t unknown_schema = 0;
};

const catalog_source &generated_monspell_catalog();

// Phase 1 stage 1 loading boundary. Validation is deterministic and performs
// no TextDB selection, Lua execution, or RNG calls.
const load_report &load_monspell_overlay(
    const std::vector<textdb_phase0::canonical_entry> &canonical_entries);
const load_report &load_monspell_overlay(
    const std::vector<textdb_phase0::canonical_entry> &canonical_entries,
    const catalog_source *source);

const load_report &monspell_overlay_report();
bool monspell_overlay_covers(const std::string &canonical_key);

// Must be called before any TextDB selection, recursive expansion, Lua, or RNG.
// The decision is final for the attempt: structured failures never fall back
// to legacy lookup.
route_decision route_monspell_message(const std::string &canonical_key);

// Pure transition plus the Stage 2 lookup harness. The silent unprefixed
// request explicitly carries ACCEPT_ANY_NONEMPTY to preserve the current
// compatibility rule that bypasses a second applicability check.
message_search_action transition_message_candidate(message_attempt attempt,
                                                    message_result result);
message_candidate_search search_message_candidate(
    const std::string &base_key, message_prefix prefix,
    const message_lookup &lookup);

// Read-only production diagnostics. The returned value is an owning snapshot.
diagnostic_counters monspell_overlay_diagnostics();

// Test-only reset for isolated load-state fixtures. Production must load once
// before the first coverage query.
void reset_monspell_overlay_for_test();
void reset_monspell_overlay_diagnostics_for_test();
}
