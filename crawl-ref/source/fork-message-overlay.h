#pragma once

#include <cstddef>
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

// Test-only reset for isolated load-state fixtures. Production must load once
// before the first coverage query.
void reset_monspell_overlay_for_test();
}
