/**
 * @file
 * database.h
**/

#pragma once

#include <cstdint>
#include <list>
#include <string>
#include "i18n.h"
#include <vector>

using std::vector;

#ifdef DB_NDBM
extern "C" {
#   include <ndbm.h>
}
#elif defined(DB_DBH)
extern "C" {
#   define DB_DBM_HSEARCH 1
#   include <db.h>
}
#elif defined(USE_SQLITE_DBM)
#   include "sqldbm.h"
#else
#   error DBM interfaces unavailable!
#endif

#define DPTR_COERCE char *

void databaseSystemInit();
void databaseSystemShutdown();

typedef bool (*db_find_filter)(string key, string body);

string getQuoteString(const string &key);
string getLongDescription(const string &key);

vector<string> getLongDescKeysByRegex(const string &regex,
                                      db_find_filter filter = nullptr);
vector<string> getLongDescBodiesByRegex(const string &regex,
                                        db_find_filter filter = nullptr);

string getGameStartDescription(const string &key);

string getShoutString(const string &monst, const string &suffix = "");
string getSpeakString(const string &key);
string getRandMonNameString(const string &montype);
string getRandNameString(const string &itemtype, const string &suffix = "");
string getHelpString(const string &topic);
string getMiscString(const string &misc, const string &suffix = "");
string getHintString(const string &key);
string getEgoString(const string &key);

// Narrow owning production seam for canonical English SpeakDB materialization.
// It delegates to the existing loaded-DB chooser, recursive expander, embedded
// Lua executor, and legacy bracket materializer without changing their syntax
// or selection semantics.
namespace canonical_textdb
{
enum class candidate_status
{
    MISSING,
    SELECTED,
    CORRUPT,
};

struct variant_locator
{
    string canonical_key;
    size_t variant_ordinal = static_cast<size_t>(-1);
};

struct rng_observation
{
    uint64_t current_state = 0;
    uint64_t current_count = 0;
    vector<uint64_t> global_counts;
};

struct selected_variant
{
    variant_locator locator;
    vector<size_t> recursion_path;
};

struct weighted_choice_trace
{
    string requested_key;
    string resolved_canonical_key;
    vector<size_t> recursion_path;
    int recursion_depth = 0;
    int replacement_count = 0;
    size_t variant_ordinal = static_cast<size_t>(-1);
    int weight = 0;
    int total_bound = 0;
    int random_result = 0;
    rng_observation before;
    rng_observation after;
};

enum class recursive_site_status
{
    SELECTED,
    CORRUPT,
    MISSING,
    UNBALANCED,
    DEPTH_LIMIT,
    REPLACEMENT_LIMIT,
};

struct recursive_site_trace
{
    vector<size_t> recursion_path;
    string marker;
    int recursion_depth = 0;
    int replacement_count = 0;
    recursive_site_status status = recursive_site_status::MISSING;
};

enum class lua_site_status
{
    EXECUTED,
    ERROR,
    UNBALANCED,
};

struct lua_site_trace
{
    size_t ordinal = 0;
    string source;
    string result;
    lua_site_status status = lua_site_status::ERROR;
    rng_observation before;
    rng_observation after;
};

struct selection_trace
{
    vector<weighted_choice_trace> weighted_choices;
    vector<recursive_site_trace> recursive_sites;
    vector<lua_site_trace> lua_sites;
    int final_replacement_count = 0;
};

struct loaded_candidate
{
    candidate_status status = candidate_status::MISSING;
    variant_locator top_locator;
    string expanded_pattern_en;
    vector<selected_variant> selected_variants;
    selection_trace trace;
    size_t recursive_site_count = 0;
    size_t lua_site_count = 0;
    rng_observation before;
    rng_observation after;
    string error;
};

struct randomized_pattern
{
    candidate_status status = candidate_status::CORRUPT;
    string pattern_en;
    string signature;
    size_t random_site_count = 0;
    struct site
    {
        variant_locator top_locator;
        vector<selected_variant> recursive_variants;
        size_t expanded_site_ordinal = 0;
        int option_count = 0;
        int option_index = -1;
    };
    vector<site> sites;
    rng_observation before;
    rng_observation after;
    string error;
};

loaded_candidate expand_loaded_english_candidate(const string &key);
randomized_pattern materialize_bound_legacy_randomness(
    const loaded_candidate &candidate, const string &bound_pattern_en);
rng_observation observe_rng();
}

// Read-only audit surface for the Phase 0 TextDB migration prototype. These
// types deliberately keep the runtime locator (key + variant ordinal) apart
// from source provenance. They do not participate in normal database startup.
namespace textdb_phase0
{
struct source
{
    string name;
    string text;
};

struct variant_locator
{
    string canonical_key;
    size_t variant_ordinal = static_cast<size_t>(-1);
};

struct source_provenance
{
    string source_name;
    size_t load_index;
    size_t definition_ordinal;
};

struct source_snapshot
{
    string source_name;
    size_t load_index;
    string normalized_utf8;
};

struct source_normalization_result
{
    bool valid;
    string normalized_utf8;
    string error;
};

struct weighted_variant
{
    size_t variant_ordinal;
    int weight;
    string raw_pattern;
};

struct weighted_parse_result
{
    vector<weighted_variant> variants;
    string parse_error;
};

struct canonical_variant
{
    variant_locator locator;
    source_provenance provenance;
    int weight;
    string raw_pattern;
};

struct canonical_entry
{
    string canonical_key;
    source_provenance provenance;
    vector<source_provenance> source_history;
    string raw_body;
    vector<canonical_variant> variants;
    string parse_error;
    bool body_empty = true;
};

struct canonical_speakdb_dump
{
    int schema_version;
    string database_name;
    string source_directory;
    vector<source_snapshot> sources;
    vector<canonical_entry> entries;
};

struct rng_observation
{
    uint64_t current_state;
    uint64_t current_count;
    vector<uint64_t> global_counts;
};

struct weighted_choice_trace
{
    string requested_key;
    string resolved_canonical_key;
    vector<size_t> recursion_path;
    int recursion_depth;
    int replacement_count;
    size_t variant_ordinal;
    int weight;
    int total_bound;
    int random_result;
    rng_observation before;
    rng_observation after;
};

enum class recursive_site_status
{
    SELECTED,
    CORRUPT,
    MISSING,
    UNBALANCED,
    DEPTH_LIMIT,
    REPLACEMENT_LIMIT,
};

struct recursive_site_trace
{
    vector<size_t> recursion_path;
    string marker;
    int recursion_depth;
    int replacement_count;
    recursive_site_status status;
};

enum class lua_site_status
{
    EXECUTED,
    ERROR,
    UNBALANCED,
};

struct lua_site_trace
{
    size_t ordinal;
    string source;
    string result;
    lua_site_status status;
    rng_observation before;
    rng_observation after;
};

struct selection_trace
{
    vector<weighted_choice_trace> weighted_choices;
    vector<recursive_site_trace> recursive_sites;
    vector<lua_site_trace> lua_sites;
    int final_replacement_count = 0;
};

enum class raw_selection_status
{
    MISSING,
    SELECTED,
    CORRUPT,
};

struct raw_selection
{
    raw_selection_status status;
    string raw_pattern;
    variant_locator locator;
    selection_trace trace;
};

struct expanded_selection
{
    raw_selection_status status = raw_selection_status::MISSING;
    string text;
    selection_trace trace;
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

struct message_candidate_evaluation
{
    message_result result;
    string expanded_text;
    selection_trace trace;
    bool applicability_checked;
    // Always false in this slice: expansion/Lua may have run, but target-slot
    // replacement and [a|b] legacy materialization are deliberately absent.
    bool post_expansion_materialized;
};

struct canonical_pre_random_pattern
{
    variant_locator top_locator;
    selection_trace selection;
    // Canonical English after runtime slots needed by bracket materialization
    // have been bound, but before legacy [a|b] choices are made.
    string pattern_en;
};

struct selected_recursive_variant
{
    variant_locator locator;
    vector<size_t> recursion_path;
};

struct legacy_random_site_identity
{
    variant_locator top_locator;
    vector<selected_recursive_variant> recursive_variants;
    size_t expanded_site_ordinal;
};

struct legacy_random_site
{
    legacy_random_site_identity identity;
    int option_count = 0;
    int option_index = -1;
};

enum class legacy_materialization_status
{
    MATERIALIZED,
    CORRUPT,
};

struct legacy_materialization
{
    legacy_materialization_status status =
        legacy_materialization_status::CORRUPT;
    string randomized_pattern_en;
    vector<legacy_random_site> sites;
    rng_observation before;
    rng_observation after;
    string error;
};

// Owning values returned by the Phase 0 runtime-binding seam. The callback is
// invoked only after canonical selection/recursion/Lua and before [a|b]
// materialization, matching the legacy speech call order.
struct message_runtime_bindings
{
    string actor_sentence_en;
    string actor_en;
    string relation_en;
    string target_en;
    string beam_en;
};

using message_runtime_binding_resolver =
    message_runtime_bindings (*)(void *context);

struct runtime_binding_trace
{
    message_runtime_bindings values;
    rng_observation before;
    rng_observation after;
};

struct structured_message_materialization
{
    raw_selection_status status = raw_selection_status::MISSING;
    variant_locator top_locator;
    string expanded_pattern_en;
    string bound_pattern_en;
    string randomized_message_en;
    selection_trace database_trace;
    runtime_binding_trace binding_trace;
    legacy_materialization substring_trace;
    rng_observation total_before;
    rng_observation database_after;
    rng_observation total_after;
    string error;
};

weighted_parse_result parse_weighted_entry_result(const string &entry);
vector<weighted_variant> parse_weighted_entry(const string &entry);
string choose_weighted_entry(const string &entry, int fixed_weight = -1);

// Parse sources in load order, retaining only the last definition of each key
// just as DBM_REPLACE does. The returned entries are sorted by canonical key.
vector<canonical_entry> canonicalise_sources(const vector<source> &sources,
                                             bool trim_keys = true);
source_normalization_result normalize_textdb_source(const string &text);
canonical_speakdb_dump canonicalise_source_dump(
    const vector<source> &sources, bool trim_keys = true);

// Re-read the canonical English SpeakDB inputs through the production parser.
// This is intentionally independent of DBM, whose schema has no provenance.
vector<canonical_entry> dump_canonical_english_speakdb();
canonical_speakdb_dump dump_canonical_english_speakdb_typed();
bool is_valid_textdb_locale(const string &language);
vector<string> order_localized_speakdb_sources(vector<string> files);
canonical_speakdb_dump dump_localized_speakdb_typed(const string &language);

// Select and recursively expand a key from a canonical dump using the same
// weighted chooser, replacement walk, and embedded-Lua stage as the legacy
// TextDB path.
string expand_canonical_speakdb(const vector<canonical_entry> &entries,
                                const string &key);

// Run the legacy recursive core against the already-loaded canonical English
// SpeakDB base, explicitly bypassing any translation DB.
string expand_loaded_canonical_english_speakdb(const string &key);
expanded_selection expand_loaded_canonical_english_speakdb_traced(
    const string &key);

raw_selection select_canonical_english(
    const vector<canonical_entry> &entries, const string &key);
expanded_selection expand_canonical_selection(
    const vector<canonical_entry> &entries, const raw_selection &selection);

// Test/audit surface for the existing embedded-Lua materializer. It records
// interpreter outcomes and RNG observations, but cannot prove equivalence of
// arbitrary external Lua side effects.
expanded_selection materialize_embedded_lua(const string &pattern);

// Pure Phase 0 prototype; no runtime speech caller uses this state machine.
message_candidate_evaluation evaluate_message_candidate(
    const vector<canonical_entry> &entries, const string &key,
    message_attempt attempt, bool manifest_applicable);
message_search_action transition_message_candidate(message_attempt attempt,
                                                    message_result result);

// Pure Phase 0 prototype for the existing post-binding [a|b] stage.
legacy_materialization materialize_legacy_randomness(
    const canonical_pre_random_pattern &pattern);

// Pure Phase 0 orchestration prototype. It is not connected to a speech
// caller or catalog; the callback supplies already-owned semantic display
// values and is observed without performing a second selection.
structured_message_materialization materialize_structured_message(
    const vector<canonical_entry> &entries, const string &key,
    message_runtime_binding_resolver resolve_bindings, void *context);
}

vector<string> getAllFAQKeys();
string getFAQ_Question(const string &key);
string getFAQ_Answer(const string &question);
