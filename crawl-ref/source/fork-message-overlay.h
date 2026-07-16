#pragma once

#include <cstddef>
#include <cstdint>
#include <functional>
#include <string>
#include <vector>

#include "database.h"

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

enum class target_relation
{
    NONE,
    AT,
    NEXT_TO,
    PAST,
};

enum class target_kind
{
    PLAYER,
    SELF,
    MONSTER,
    FEATURE,
    LOCATION,
    THIN_AIR,
    INDEFINITE,
    ERROR,
};

enum class message_visibility
{
    VISIBLE,
    UNSEEN,
    UNKNOWN,
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

struct localized_value
{
    std::string language;
    std::string display;
};

struct resolved_actor
{
    std::string sentence_en;
    std::string canonical_en;
    std::vector<localized_value> localized;
    message_visibility visibility = message_visibility::UNKNOWN;
};

struct resolved_target
{
    target_relation relation = target_relation::NONE;
    target_kind kind = target_kind::ERROR;
    message_visibility visibility = message_visibility::UNKNOWN;
    std::string relation_en;
    std::string canonical_en;
    std::vector<localized_value> localized;
    bool has_position = false;
    int position_x = 0;
    int position_y = 0;
    bool has_feature = false;
    int feature_id = 0;
    bool has_actor_mid = false;
    int actor_mid = 0;
    std::string error;
};

struct resolved_beam
{
    std::string canonical_en;
    std::vector<localized_value> localized;
    std::string configured_name_en;
    std::string short_name_en;
    int origin_spell = 0;
    int flavour = 0;
    int real_flavour = 0;
    bool pierce = false;
    bool has_ranged_attack = false;
};

struct cast_context
{
    cast_frame frame = cast_frame::DIRECT_EFFECT;
    message_visibility caster_visibility = message_visibility::UNKNOWN;
    int origin_spell = 0;
    bool has_god = false;
    std::string god_canonical_en;
};

struct runtime_bindings
{
    resolved_actor actor;
    resolved_target target;
    resolved_beam beam;
    cast_context cast;
};

struct rng_boundary
{
    canonical_textdb::rng_observation before;
    canonical_textdb::rng_observation after;
};

struct binding_resolution
{
    runtime_bindings values;
    rng_boundary rng;
    size_t callback_count = 0;
};

using runtime_binding_resolver = std::function<runtime_bindings()>;
using canonical_candidate_lookup = std::function<
    canonical_textdb::loaded_candidate(const std::string &)>;

struct slot_value
{
    std::string name;
    std::string value;
};

struct rendered_line
{
    sensory_mode sensory = sensory_mode::PLAIN;
    std::string channel;
    bool implies_gesture = false;
    bool audible = false;
    std::string text;
};

struct render_result
{
    message_result result = message_result::CORRUPT;
    std::vector<rendered_line> lines;
    std::string diagnostic;
};

struct canonical_materialization
{
    message_result result = message_result::CORRUPT;
    canonical_textdb::loaded_candidate canonical;
    canonical_textdb::randomized_pattern randomized;
    binding_resolution binding;
    std::string stable_id;
    std::string materialization_signature;
    std::string bound_pattern_en;
    std::string diagnostic;
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

canonical_materialization materialize_monspell_candidate(
    const std::string &canonical_key, message_attempt attempt,
    bool manifest_applicable, const runtime_binding_resolver &bindings);
canonical_materialization materialize_monspell_candidate(
    const std::string &canonical_key, message_attempt attempt,
    bool manifest_applicable, const runtime_binding_resolver &bindings,
    const canonical_candidate_lookup &lookup);

// These functions are pure: no TextDB, RNG, Lua, or translation lookup.
render_result render_typed_template(
    const std::string &pattern,
    const std::vector<slot_definition> &declarations,
    const std::vector<slot_value> &values);
render_result render_typed_lines(
    const std::vector<line_metadata> &lines, const std::string &language,
    target_relation relation,
    const std::vector<slot_definition> &declarations,
    const std::vector<slot_value> &values);
render_result render_materialized_candidate(
    const canonical_materialization &materialized,
    const std::string &language);

// Read-only production diagnostics. The returned value is an owning snapshot.
diagnostic_counters monspell_overlay_diagnostics();

// Test-only reset for isolated load-state fixtures. Production must load once
// before the first coverage query.
void reset_monspell_overlay_for_test();
void reset_monspell_overlay_diagnostics_for_test();
}
