#include "AppHdr.h"

#include "fork-message-overlay.h"

#include "database.h"
#include "initfile.h"
#include "stringutil.h"

#include <algorithm>
#include <iomanip>
#include <map>
#include <set>
#include <sstream>

namespace fork_message_overlay
{
applicability::applicability() = default;

applicability::applicability(bool player, bool foe, bool named_foe, bool god,
                             bool caster_visible)
    : requires_player(player), requires_foe(foe),
      requires_named_foe(named_foe), requires_god(god),
      requires_caster_visible(caster_visible)
{
}

line_metadata::line_metadata() = default;

line_metadata::line_metadata(
    sensory_mode sensory_mode, const string &channel_name, bool gesture,
    bool is_audible, const vector<localized_template> &localized_templates)
    : sensory(sensory_mode), channel(channel_name), implies_gesture(gesture),
      audible(is_audible), templates(localized_templates)
{
}

recursive_capture_definition::recursive_capture_definition() = default;

recursive_capture_definition::recursive_capture_definition(
    const string &capture_name, const string &capture_marker,
    size_t capture_ordinal, const string &capture_vocabulary)
    : name(capture_name), marker(capture_marker), ordinal(capture_ordinal),
      vocabulary(capture_vocabulary)
{
}

recursive_capture_vocabulary_entry::
recursive_capture_vocabulary_entry() = default;

recursive_capture_vocabulary_entry::recursive_capture_vocabulary_entry(
    const string &key, size_t ordinal, const string &fingerprint,
    const string &expanded_replacement)
    : canonical_key(key), variant_ordinal(ordinal),
      variant_fingerprint(fingerprint),
      expanded_replacement_en(expanded_replacement)
{
}

catalog_variant::catalog_variant() = default;

catalog_variant::catalog_variant(
    const string &id, bool is_tombstone, size_t ordinal, int weight,
    const string &variant_fingerprint, const string &snapshot,
    cast_frame cast_message_frame, bool target_resolution,
    const applicability &variant_conditions,
    materialization_policy materialization,
    const vector<slot_definition> &schema,
    const vector<string> &arguments,
    const vector<line_metadata> &message_lines,
    const vector<materialization_case> &cases,
    const vector<string> &dependencies,
    const vector<string> &dependency_fingerprints,
    const vector<recursive_capture_definition> &captures,
    const vector<recursive_capture_vocabulary_entry> &vocabulary,
    bool suppress_message)
    : stable_id(id), tombstone(is_tombstone), variant_ordinal(ordinal),
      upstream_weight(weight),
      upstream_variant_fingerprint(variant_fingerprint),
      english_snapshot(snapshot), frame(cast_message_frame),
      resolves_target(target_resolution), conditions(variant_conditions),
      policy(materialization), slot_schema(schema),
      required_arguments(arguments), lines(message_lines),
      materialization_cases(cases), recursive_dependencies(dependencies),
      recursive_dependency_fingerprints(dependency_fingerprints),
      recursive_captures(captures), recursive_capture_vocabulary(vocabulary),
      suppresses(suppress_message)
{
}

catalog_entry::catalog_entry() = default;

catalog_entry::catalog_entry(
    const string &key, const string &fingerprint,
    const string &graph_fingerprint, entry_mode entry_type,
    const vector<catalog_variant> &entry_variants)
    : canonical_key(key), canonical_fingerprint(fingerprint),
      selection_graph_fingerprint(graph_fingerprint), mode(entry_type),
      variants(entry_variants)
{
}

catalog_source::catalog_source() = default;

catalog_source::catalog_source(
    int version, const string &source_domain,
    const string &semantic_fingerprint, const vector<string> &languages,
    const vector<catalog_entry> &catalog_entries,
    const vector<tombstone_record> &catalog_tombstones)
    : schema_version(version), domain(source_domain),
      inventory_semantic_fingerprint(semantic_fingerprint),
      supported_languages(languages), entries(catalog_entries),
      tombstones(catalog_tombstones)
{
}

namespace
{
load_report current_report;
set<string> covered_keys;
diagnostic_counters current_diagnostics;
map<string, vector<string>> capture_parent_leaf_keys;
catalog_source active_catalog;
bool active_catalog_loaded = false;

const catalog_source &_catalog()
{
    return active_catalog_loaded ? active_catalog
                                 : generated_monspell_catalog();
}

string _fnv1a64(const string &payload)
{
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

string _canonical_fingerprint(const textdb_phase0::canonical_entry &entry)
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
    return _fnv1a64(payload);
}

string _selection_fingerprint(const textdb_phase0::canonical_entry &entry)
{
    string payload("selection-v1\0", 13);
    payload += entry.canonical_key;
    payload += '\0';
    for (const textdb_phase0::canonical_variant &variant : entry.variants)
    {
        payload += std::to_string(variant.locator.variant_ordinal);
        payload += ':';
        payload += std::to_string(variant.weight);
        payload += ':';
        payload += variant.raw_pattern;
        payload += '\0';
    }
    return _fnv1a64(payload);
}

const load_report &_disable(load_failure failure, const string &diagnostic)
{
    covered_keys.clear();
    capture_parent_leaf_keys.clear();
    active_catalog = catalog_source();
    active_catalog_loaded = false;
    current_report.state = domain_state::DISABLED;
    current_report.failure = failure;
    current_report.diagnostic = diagnostic;
    current_report.structured_key_count = 0;
    if (failure == load_failure::UNKNOWN_SCHEMA)
        ++current_diagnostics.unknown_schema;
    else if (failure == load_failure::CORRUPT
             || failure == load_failure::CLOSURE_INCOMPLETE)
    {
        ++current_diagnostics.overlay_corrupt;
    }
    return current_report;
}

void _record_message_result(message_result result)
{
    switch (result)
    {
    case message_result::INAPPLICABLE:
        ++current_diagnostics.candidate_inapplicable;
        break;
    case message_result::SUPPRESS:
        ++current_diagnostics.message_suppressed;
        break;
    case message_result::CORRUPT:
        ++current_diagnostics.overlay_corrupt;
        break;
    case message_result::MISSING:
    case message_result::RENDERED:
        break;
    }
}

message_lookup_request _initial_request(const string &base_key,
                                        message_prefix prefix)
{
    message_lookup_request request;
    request.lookup_key = base_key;
    switch (prefix)
    {
    case message_prefix::NORMAL:
        break;
    case message_prefix::UNSEEN:
        request.lookup_key = "unseen " + base_key;
        break;
    case message_prefix::SILENT:
        request.lookup_key = "silent " + base_key;
        request.attempt = message_attempt::SILENT_PREFIXED;
        break;
    }
    return request;
}

message_lookup_request _silent_unprefixed_request(const string &base_key)
{
    message_lookup_request request;
    request.lookup_key = base_key;
    request.attempt = message_attempt::SILENT_UNPREFIXED_FALLBACK;
    request.applicability = applicability_policy::ACCEPT_ANY_NONEMPTY;
    return request;
}

bool _valid_identifier(const string &name)
{
    if (name.empty() || name[0] < 'a' || name[0] > 'z')
        return false;
    for (const unsigned char c : name)
    {
        if ((c < 'a' || c > 'z') && (c < '0' || c > '9') && c != '_')
            return false;
    }
    return true;
}

bool _collect_template_slots(const string &pattern, set<string> &slots,
                             string &error)
{
    if (pattern.find('@') != string::npos
        || pattern.find('[') != string::npos
        || pattern.find(']') != string::npos
        || pattern.find("{{") != string::npos
        || pattern.find("}}") != string::npos)
    {
        error = "template contains legacy TextDB syntax";
        return false;
    }

    size_t position = 0;
    while ((position = pattern.find("${", position)) != string::npos)
    {
        const size_t end = pattern.find('}', position + 2);
        if (end == string::npos)
        {
            error = "template has an unclosed typed slot";
            return false;
        }
        const string name = pattern.substr(position + 2, end - position - 2);
        if (!_valid_identifier(name))
        {
            error = "template has an invalid typed slot";
            return false;
        }
        slots.insert(name);
        position = end + 1;
    }
    return true;
}

vector<string> _recursive_dependencies(
    const string &pattern,
    const map<string, const textdb_phase0::canonical_entry *> &canonical)
{
    set<string> dependencies;
    size_t position = pattern.find('@');
    while (position != string::npos)
    {
        const size_t end = pattern.find('@', position + 1);
        if (end == string::npos)
            break;
        string key = pattern.substr(position + 1, end - position - 1);
        lowercase(key);
        if (canonical.count(key))
            dependencies.insert(key);
        position = pattern.find('@', end + 1);
    }
    return vector<string>(dependencies.begin(), dependencies.end());
}

vector<string> _recursive_closure(
    const string &pattern,
    const map<string, const textdb_phase0::canonical_entry *> &canonical)
{
    set<string> closure;
    vector<string> pending = _recursive_dependencies(pattern, canonical);
    while (!pending.empty())
    {
        const string key = pending.back();
        pending.pop_back();
        if (!closure.insert(key).second)
            continue;
        const auto found = canonical.find(key);
        if (found == canonical.end())
            continue;
        for (const textdb_phase0::canonical_variant &variant
             : found->second->variants)
        {
            const vector<string> nested =
                _recursive_dependencies(variant.raw_pattern, canonical);
            pending.insert(pending.end(), nested.begin(), nested.end());
        }
    }
    return vector<string>(closure.begin(), closure.end());
}

string _variant_fingerprint(const textdb_phase0::canonical_variant &variant)
{
    return _fnv1a64(variant.raw_pattern);
}

bool _same_strings(vector<string> lhs, vector<string> rhs)
{
    sort(lhs.begin(), lhs.end());
    sort(rhs.begin(), rhs.end());
    return lhs == rhs;
}

bool _has_slot_type(const catalog_variant &variant, const string &type)
{
    return any_of(
        variant.slot_schema.begin(), variant.slot_schema.end(),
        [&type](const slot_definition &slot) { return slot.type == type; });
}

bool _validate_lines(const catalog_source &source,
                     const catalog_variant &variant, string &error)
{
    set<string> declared;
    for (const slot_definition &slot : variant.slot_schema)
    {
        static const set<string> slot_types =
        {
            "actor_ref", "actor_ref_lower", "actor_possessive_name",
            "actor_possessive_name_lower",
            "actor_possessive_pronoun", "actor_subjective_pronoun",
            "player_name", "actor_reflexive",
            "actor_god_possessive", "actor_god_my",
            "actor_god_indefinite",
            "actor_arms_plural", "resolved_target", "resolved_foe",
            "resolved_foe_possessive", "resolved_beam", "recursive_capture",
        };
        if (!_valid_identifier(slot.name) || !slot_types.count(slot.type)
            || !declared.insert(slot.name).second)
        {
            error = "invalid or duplicate slot declaration";
            return false;
        }
    }

    set<string> required(variant.required_arguments.begin(),
                         variant.required_arguments.end());
    if (required.size() != variant.required_arguments.size()
        || required != declared)
    {
        error = "required_arguments do not exactly match slot_schema";
        return false;
    }

    if (variant.suppresses)
    {
        if (variant.english_snapshot != "__NONE"
            || variant.policy != materialization_policy::NONE)
        {
            error = "suppress descriptor must select exact __NONE";
            return false;
        }
        if (variant.resolves_target
            || variant.conditions.requires_player
            || variant.conditions.requires_foe
            || variant.conditions.requires_named_foe
            || variant.conditions.requires_god
            || variant.conditions.requires_caster_visible
            || !variant.slot_schema.empty()
            || !variant.required_arguments.empty()
            || !variant.lines.empty()
            || !variant.materialization_cases.empty()
            || !variant.recursive_dependencies.empty()
            || !variant.recursive_dependency_fingerprints.empty()
            || !variant.recursive_captures.empty()
            || !variant.recursive_capture_vocabulary.empty())
        {
            error = "suppress descriptor contains renderable data";
            return false;
        }
        return true;
    }

    if (variant.policy == materialization_policy::LEGACY_ONLY)
    {
        if (!variant.lines.empty() || !variant.materialization_cases.empty())
        {
            error = "legacy-only variant contains renderable data";
            return false;
        }
        return true;
    }
    const bool has_actor_ref_token =
        variant.english_snapshot.find("@The_monster@") != string::npos
        || variant.english_snapshot.find("@The_something@") != string::npos;
    const bool has_actor_ref_lower_token =
        variant.english_snapshot.find("@the_monster@") != string::npos;
    const bool has_actor_possessive_token =
        variant.english_snapshot.find("@The_monster_possessive@")
            != string::npos;
    const bool has_actor_possessive_lower_token =
        variant.english_snapshot.find("@the_monster_possessive@")
            != string::npos;
    if (has_actor_ref_token != _has_slot_type(variant, "actor_ref"))
    {
        error = "sentence actor token/type mismatch";
        return false;
    }
    const pair<const char *, const char *> god_slots[] =
    {
        { "@possessive_God@", "actor_god_possessive" },
        { "@My_God@", "actor_god_my" },
        { "@a_God@", "actor_god_indefinite" },
    };
    for (const auto &god_slot : god_slots)
    {
        const bool has_token = variant.english_snapshot.find(god_slot.first)
            != string::npos;
        if (has_token != _has_slot_type(variant, god_slot.second))
        {
            error = string(god_slot.first) + " token/type mismatch";
            return false;
        }
    }
    if (has_actor_ref_lower_token
        != _has_slot_type(variant, "actor_ref_lower"))
    {
        error = "lower actor token/type mismatch";
        return false;
    }
    if (has_actor_possessive_token
        != _has_slot_type(variant, "actor_possessive_name"))
    {
        error = "sentence possessive actor token/type mismatch";
        return false;
    }
    if (has_actor_possessive_lower_token
        != _has_slot_type(variant, "actor_possessive_name_lower"))
    {
        error = "lower possessive actor token/type mismatch";
        return false;
    }
    const bool has_subjective_token =
        variant.english_snapshot.find("@subjective@") != string::npos;
    if (has_subjective_token
        != _has_slot_type(variant, "actor_subjective_pronoun"))
    {
        error = "subjective actor token/type mismatch";
        return false;
    }
    const bool has_player_name_token =
        variant.english_snapshot.find("@player_name@") != string::npos;
    if (has_player_name_token != _has_slot_type(variant, "player_name"))
    {
        error = "player-name token/type mismatch";
        return false;
    }
    const bool has_player_only_marker =
        variant.english_snapshot.find("@player_only@") != string::npos;
    if ((has_player_name_token || has_player_only_marker)
        && !variant.conditions.requires_player)
    {
        error = "player token/marker requires player applicability";
        return false;
    }
    if (variant.lines.empty())
    {
        error = "structured variant has no line metadata";
        return false;
    }
    const set<string> relations = variant.resolves_target
        ? set<string>{ "AT", "NEXT_TO", "PAST" }
        : set<string>{ "NONE" };
    if (!variant.resolves_target
        && any_of(variant.slot_schema.begin(), variant.slot_schema.end(),
                  [](const slot_definition &slot)
                  {
                      return slot.type == "resolved_target";
                  }))
    {
        error = "non-target binding declares resolved_target";
        return false;
    }
    set<string> used_slots;
    for (const line_metadata &line : variant.lines)
    {
        if (line.audible)
        {
            error = "audible behavior metadata is not enabled yet";
            return false;
        }
        if (!line.channel.empty() && str_to_channel(line.channel) < 0)
        {
            error = "line metadata has an invalid message channel";
            return false;
        }
        set<pair<string, string>> language_relations;
        for (const localized_template &localized : line.templates)
        {
            if (localized.pattern.empty()
                || localized.pattern.find('\n') != string::npos
                || !relations.count(localized.relation)
                || find(source.supported_languages.begin(),
                        source.supported_languages.end(), localized.language)
                       == source.supported_languages.end()
                || !language_relations.insert(
                       { localized.language, localized.relation }).second)
            {
                error = "invalid or duplicate language/relation template";
                return false;
            }
            if (!_collect_template_slots(localized.pattern, used_slots, error))
                return false;
        }
        for (const string &language : source.supported_languages)
        {
            for (const string &relation : relations)
            {
                if (!language_relations.count({ language, relation }))
                {
                    error = "language/relation template matrix is incomplete";
                    return false;
                }
            }
        }
    }
    if (used_slots != required)
    {
        error = "template slots do not exactly match required_arguments";
        return false;
    }
    return true;
}

string _relation_name(target_relation relation)
{
    switch (relation)
    {
    case target_relation::AT:      return "AT";
    case target_relation::NEXT_TO: return "NEXT_TO";
    case target_relation::PAST:    return "PAST";
    case target_relation::NONE:    return "NONE";
    }
    return "NONE";
}

bool _contains_protocol_text(const string &text)
{
    return text.find('@') != string::npos
        || text.find("${") != string::npos
        || text.find('[') != string::npos
        || text.find(']') != string::npos
        || text.find("{{") != string::npos
        || text.find("}}") != string::npos
        || text.find("%%%%") != string::npos
        || text.find("__NONE") != string::npos
        || text.find("VISUAL:") != string::npos
        || text.find("SOUND:") != string::npos;
}

const catalog_variant *_find_catalog_variant(
    const string &canonical_key, size_t variant_ordinal,
    const string &signature)
{
    for (const catalog_entry &entry : _catalog().entries)
    {
        if (entry.canonical_key != canonical_key
            || entry.mode != entry_mode::CANDIDATE)
        {
            continue;
        }
        for (const catalog_variant &variant : entry.variants)
        {
            if (variant.variant_ordinal != variant_ordinal)
                continue;
            if (signature == "NONE"
                && variant.policy == materialization_policy::NONE)
            {
                return &variant;
            }
            if (variant.policy == materialization_policy::CASE_MAP
                || variant.policy
                   == materialization_policy::RECURSIVE_CASE_MAP)
            {
                for (const materialization_case &materialized
                     : variant.materialization_cases)
                {
                    if (materialized.signature == signature)
                        return &variant;
                }
            }
            return nullptr;
        }
    }
    return nullptr;
}

const materialization_case *_find_materialization_case(
    const catalog_variant &variant, const string &signature)
{
    if (variant.policy != materialization_policy::CASE_MAP
        && variant.policy != materialization_policy::RECURSIVE_CASE_MAP)
        return nullptr;
    for (const materialization_case &materialized
         : variant.materialization_cases)
    {
        if (materialized.signature == signature)
            return &materialized;
    }
    return nullptr;
}

const catalog_variant *_find_catalog_variant_by_locator(
    const string &canonical_key, size_t variant_ordinal)
{
    for (const catalog_entry &entry : _catalog().entries)
    {
        if (entry.canonical_key != canonical_key
            || entry.mode != entry_mode::CANDIDATE)
        {
            continue;
        }
        for (const catalog_variant &variant : entry.variants)
        {
            if (variant.variant_ordinal == variant_ordinal)
                return &variant;
        }
    }
    return nullptr;
}

bool _single_site_case_signatures(const string &key, size_t ordinal,
                                  const string &pattern,
                                  set<string> &signatures)
{
    const size_t open = pattern.find('[');
    const size_t close = open == string::npos
        ? string::npos : pattern.find(']', open + 1);
    if (open == string::npos || close == string::npos
        || pattern.find('[', open + 1) != string::npos
        || pattern.find(']', close + 1) != string::npos)
    {
        return false;
    }
    int options = 1;
    for (size_t i = open + 1; i < close; ++i)
    {
        if (pattern[i] == '[' || pattern[i] == ']')
            return false;
        if (pattern[i] == '|')
            ++options;
    }
    if (options < 2)
        return false;
    const string prefix = "materialization-v1|variants=1|"
        + std::to_string(key.size()) + ':' + key + ':'
        + std::to_string(ordinal) + ":0|lua=0|sites=1|"
        + std::to_string(key.size()) + ':' + key + ':'
        + std::to_string(ordinal) + ":0:" + std::to_string(options) + ':';
    for (int option = 0; option < options; ++option)
        signatures.insert(prefix + std::to_string(option));
    return true;
}

bool _same_case_line_shape(const vector<line_metadata> &lhs,
                           const vector<line_metadata> &rhs)
{
    if (lhs.size() != rhs.size())
        return false;
    for (size_t i = 0; i < lhs.size(); ++i)
    {
        if (lhs[i].sensory != rhs[i].sensory
            || lhs[i].channel != rhs[i].channel
            || lhs[i].implies_gesture != rhs[i].implies_gesture
            || lhs[i].audible != rhs[i].audible)
        {
            return false;
        }
    }
    return true;
}

bool _localized_display(const vector<localized_value> &values,
                        const string &language, string &display)
{
    bool found = false;
    for (const localized_value &value : values)
    {
        if (value.language != language)
            continue;
        if (found || value.display.empty())
            return false;
        found = true;
        display = value.display;
    }
    return found;
}

bool _valid_target_payload(const resolved_target &target)
{
    if (!target.error.empty())
        return false;
    switch (target.kind)
    {
    case target_kind::PLAYER:
    case target_kind::THIN_AIR:
    case target_kind::INDEFINITE:
        return true;
    case target_kind::SELF:
    case target_kind::MONSTER:
        return target.has_actor_mid;
    case target_kind::FEATURE:
        return target.has_feature && target.has_position;
    case target_kind::LOCATION:
        return target.has_position;
    case target_kind::ERROR:
        return false;
    }
    return false;
}

bool _valid_foe_payload(const resolved_foe &foe)
{
    if (!foe.error.empty() || foe.canonical_en.empty())
        return false;
    switch (foe.kind)
    {
    case foe_kind::PLAYER:
        return !foe.has_actor_mid;
    case foe_kind::MONSTER:
        return foe.has_actor_mid;
    case foe_kind::ERROR:
        return false;
    }
    return false;
}

void _append_capture_signature_string(string &signature, const string &value)
{
    signature += std::to_string(value.size());
    signature += ':';
    signature += value;
}

string _capture_identity_signature(
    const canonical_textdb::loaded_candidate &candidate)
{
    string signature = "materialization-v1|variants=";
    signature += std::to_string(candidate.selected_variants.size());
    for (const canonical_textdb::selected_variant &selected
         : candidate.selected_variants)
    {
        signature += '|';
        _append_capture_signature_string(
            signature, selected.locator.canonical_key);
        signature += ':' + std::to_string(selected.locator.variant_ordinal);
        signature += ':' + std::to_string(selected.recursion_path.size());
        for (const size_t step : selected.recursion_path)
            signature += ':' + std::to_string(step);
    }
    signature += "|lua=0|sites=0";
    return signature;
}

struct recursive_identity_outcome
{
    string expanded_pattern;
    vector<canonical_textdb::selected_variant> selected;
};

struct recursive_identity_state
{
    recursive_identity_state(
        const string &source_pattern, size_t scan_position,
        size_t current_site,
        const vector<canonical_textdb::selected_variant> &choices)
        : pattern(source_pattern), position(scan_position),
          site_ordinal(current_site), selected(choices)
    {
    }

    string pattern;
    size_t position;
    size_t site_ordinal;
    vector<canonical_textdb::selected_variant> selected;
};

bool _reachable_weighted_variants(
    const textdb_phase0::canonical_entry &entry,
    vector<const textdb_phase0::canonical_variant *> &reachable)
{
    int total = 0;
    for (const textdb_phase0::canonical_variant &variant : entry.variants)
        total += variant.weight;
    if (total <= 0)
        return false;
    int cumulative = 0;
    int previous_max = 0;
    for (const textdb_phase0::canonical_variant &variant : entry.variants)
    {
        cumulative += variant.weight;
        if (previous_max < min(cumulative, total))
            reachable.push_back(&variant);
        previous_max = max(previous_max, cumulative);
    }
    return !reachable.empty();
}

bool _enumerate_recursive_variant(
    const map<string, const textdb_phase0::canonical_entry *> &canonical,
    const string &key, size_t ordinal, const vector<size_t> &path,
    vector<string> stack, vector<recursive_identity_outcome> &out,
    string &error)
{
    const auto found = canonical.find(key);
    if (found == canonical.end() || ordinal >= found->second->variants.size())
    {
        error = "recursive identity variant is missing";
        return false;
    }
    if (find(stack.begin(), stack.end(), key) != stack.end()
        || stack.size() > 10)
    {
        error = "recursive identity closure is cyclic or too deep";
        return false;
    }
    stack.push_back(key);
    const textdb_phase0::canonical_variant &variant =
        found->second->variants[ordinal];
    if (variant.raw_pattern.find('[') != string::npos
        || variant.raw_pattern.find(']') != string::npos
        || variant.raw_pattern.find("{{") != string::npos
        || variant.raw_pattern.find("}}") != string::npos)
    {
        error = "RECURSIVE_CASE_MAP closure contains Lua or bracket sites";
        return false;
    }

    canonical_textdb::selected_variant root;
    root.locator = { key, ordinal };
    root.recursion_path = path;
    vector<recursive_identity_state> pending = {
        { variant.raw_pattern, 0, 0, { root } },
    };
    while (!pending.empty())
    {
        recursive_identity_state state = pending.back();
        pending.pop_back();
        const size_t start = state.pattern.find('@', state.position);
        if (start == string::npos)
        {
            out.push_back({ state.pattern, state.selected });
            if (out.size() > 10000)
            {
                error = "recursive identity case set exceeds safe limit";
                return false;
            }
            continue;
        }
        const size_t end = state.pattern.find('@', start + 1);
        if (end == string::npos)
        {
            error = "recursive identity closure has an unbalanced marker";
            return false;
        }
        string marker = state.pattern.substr(start + 1, end - start - 1);
        lowercase(marker);
        const auto dependency = canonical.find(marker);
        if (dependency == canonical.end())
        {
            state.position = end + 1;
            ++state.site_ordinal;
            pending.push_back(state);
            continue;
        }

        vector<size_t> child_path = path;
        child_path.push_back(state.site_ordinal);
        vector<const textdb_phase0::canonical_variant *> reachable;
        if (!_reachable_weighted_variants(*dependency->second, reachable))
        {
            error = "recursive identity key has no weighted choice";
            return false;
        }
        for (const textdb_phase0::canonical_variant *child : reachable)
        {
            vector<recursive_identity_outcome> children;
            if (!_enumerate_recursive_variant(
                    canonical, marker, child->locator.variant_ordinal,
                    child_path, stack, children, error))
            {
                return false;
            }
            for (const recursive_identity_outcome &expanded : children)
            {
                recursive_identity_state next = state;
                next.pattern.replace(start, end - start + 1,
                                     expanded.expanded_pattern);
                // Production resumes at the insertion point. This observes
                // any unresolved runtime markers in the replacement before
                // moving on to the parent's next recursive marker.
                next.position = start;
                ++next.site_ordinal;
                next.selected.insert(next.selected.end(),
                                     expanded.selected.begin(),
                                     expanded.selected.end());
                pending.push_back(next);
                if (pending.size() + out.size() > 10000)
                {
                    error = "recursive identity case set exceeds safe limit";
                    return false;
                }
            }
        }
    }
    return true;
}

bool _recursive_case_signatures(
    const map<string, const textdb_phase0::canonical_entry *> &canonical,
    const string &key, size_t ordinal, set<string> &signatures,
    string &error)
{
    vector<recursive_identity_outcome> outcomes;
    if (!_enumerate_recursive_variant(
            canonical, key, ordinal, {}, {}, outcomes, error))
    {
        return false;
    }
    for (const recursive_identity_outcome &outcome : outcomes)
    {
        canonical_textdb::loaded_candidate identity;
        identity.selected_variants = outcome.selected;
        if (!signatures.insert(_capture_identity_signature(identity)).second)
        {
            error = "recursive identity paths do not produce unique signatures";
            return false;
        }
    }
    return true;
}

bool _same_selected_choice(
    const canonical_textdb::selected_variant &selected,
    const canonical_textdb::weighted_choice_trace &choice)
{
    return selected.locator.canonical_key == choice.resolved_canonical_key
        && selected.locator.variant_ordinal == choice.variant_ordinal
        && selected.recursion_path == choice.recursion_path;
}

bool _extract_recursive_captures(
    const catalog_variant &descriptor,
    const canonical_textdb::loaded_candidate &candidate,
    vector<slot_value> &captures, string &identity, string &error)
{
    if (descriptor.policy != materialization_policy::CAPTURE_SLOT)
        return descriptor.recursive_captures.empty();
    if (candidate.trace.weighted_choices.size() != 7
        || candidate.trace.recursive_sites.size() != 7
        || candidate.selected_variants.size() != 7
        || !candidate.trace.lua_sites.empty()
        || candidate.lua_site_count != 0
        || candidate.recursive_site_count != 7
        || candidate.trace.final_replacement_count != 7)
    {
        error = "recursive capture trace shape is invalid";
        return false;
    }
    const auto &choices = candidate.trace.weighted_choices;
    const auto &selected = candidate.selected_variants;
    const auto &sites = candidate.trace.recursive_sites;
    const auto parent_leaf_keys =
        capture_parent_leaf_keys.find(descriptor.stable_id);
    if (parent_leaf_keys == capture_parent_leaf_keys.end()
        || parent_leaf_keys->second.size()
           != descriptor.recursive_captures.size())
    {
        error = "recursive capture parent mapping is unavailable";
        return false;
    }
    if (candidate.top_locator.canonical_key
            != "vanquished vanguard nergalle cast"
        || candidate.top_locator.variant_ordinal != 0
        || choices[0].recursion_path != vector<size_t>()
        || choices[0].requested_key
            != "vanquished vanguard nergalle cast"
        || choices[0].resolved_canonical_key
            != "vanquished vanguard nergalle cast"
        || choices[0].variant_ordinal != 0
        || !_same_selected_choice(selected[0], choices[0])
        || selected[0].locator.canonical_key
            != candidate.top_locator.canonical_key
        || selected[0].locator.variant_ordinal
            != candidate.top_locator.variant_ordinal
        || sites[0].recursion_path != vector<size_t>{ 0 }
        || sites[0].marker != "The_monster"
        || sites[0].status
            != canonical_textdb::recursive_site_status::MISSING
        || !sites[0].replacement.empty())
    {
        error = "recursive capture top-level topology is invalid";
        return false;
    }

    for (size_t index = 0; index < descriptor.recursive_captures.size();
         ++index)
    {
        const recursive_capture_definition &definition =
            descriptor.recursive_captures[index];
        const size_t parent_index = 1 + index * 2;
        const size_t leaf_index = parent_index + 1;
        const vector<size_t> parent_path = { index + 1 };
        const vector<size_t> leaf_path = { index + 1, 0 };
        const canonical_textdb::weighted_choice_trace &parent_choice =
            choices[parent_index];
        const canonical_textdb::weighted_choice_trace &leaf_choice =
            choices[leaf_index];
        const canonical_textdb::recursive_site_trace &parent_site =
            sites[parent_index];
        const canonical_textdb::recursive_site_trace &leaf_site =
            sites[leaf_index];
        if (definition.ordinal != index
            || definition.marker != parent_site.marker
            || definition.vocabulary != "orc_name_leaf_v1"
            || parent_choice.requested_key != "orc name"
            || parent_choice.resolved_canonical_key != "orc name"
            || parent_choice.recursion_path != parent_path
            || parent_site.recursion_path != parent_path
            || parent_site.marker != "orc name"
            || parent_site.status
               != canonical_textdb::recursive_site_status::SELECTED
            || leaf_choice.recursion_path != leaf_path
            || leaf_site.recursion_path != leaf_path
            || leaf_choice.requested_key != leaf_site.marker
            || leaf_choice.resolved_canonical_key != leaf_site.marker
            || parent_choice.variant_ordinal
               >= parent_leaf_keys->second.size()
            || leaf_choice.requested_key
               != parent_leaf_keys->second[parent_choice.variant_ordinal]
            || leaf_choice.resolved_canonical_key
               != parent_leaf_keys->second[parent_choice.variant_ordinal]
            || leaf_site.status
               != canonical_textdb::recursive_site_status::SELECTED
            || parent_site.replacement.empty()
            || parent_site.replacement != leaf_site.replacement
            || !_same_selected_choice(
                selected[parent_index], parent_choice)
            || !_same_selected_choice(selected[leaf_index], leaf_choice))
        {
            error = "recursive capture topology is invalid";
            return false;
        }

        const auto word = find_if(
            descriptor.recursive_capture_vocabulary.begin(),
            descriptor.recursive_capture_vocabulary.end(),
            [&leaf_choice, &leaf_site](
                const recursive_capture_vocabulary_entry &candidate_word)
            {
                return candidate_word.canonical_key
                           == leaf_choice.resolved_canonical_key
                       && candidate_word.variant_ordinal
                           == leaf_choice.variant_ordinal
                       && candidate_word.expanded_replacement_en
                           == leaf_site.replacement;
            });
        if (word == descriptor.recursive_capture_vocabulary.end())
        {
            error = "recursive capture is outside the declared vocabulary";
            return false;
        }
        captures.push_back({ definition.name, parent_site.replacement });
    }
    identity = _capture_identity_signature(candidate);
    return true;
}
}

#include "fork-message-overlay.generated.inc"

const load_report &load_monspell_overlay(
    const vector<textdb_phase0::canonical_entry> &canonical_entries)
{
    return load_monspell_overlay(canonical_entries,
                                 &generated_monspell_catalog());
}

const load_report &load_monspell_overlay(
    const vector<textdb_phase0::canonical_entry> &canonical_entries,
    const catalog_source *source)
{
    if (current_report.state != domain_state::UNINITIALIZED)
        return current_report;
    if (!source)
        return _disable(load_failure::MISSING, "monspell overlay is missing");
    if (source->schema_version != MONSPELL_OVERLAY_SCHEMA_VERSION)
    {
        return _disable(load_failure::UNKNOWN_SCHEMA,
                        "unknown monspell overlay schema");
    }
    const set<string> supported_languages(source->supported_languages.begin(),
                                          source->supported_languages.end());
    if (source->domain != "monspell"
        || source->inventory_semantic_fingerprint.empty()
        || source->supported_languages.empty()
        || supported_languages.size() != source->supported_languages.size()
        || !supported_languages.count("en")
        || !supported_languages.count("zh"))
    {
        return _disable(load_failure::CORRUPT,
                        "invalid monspell overlay header");
    }

    map<string, const textdb_phase0::canonical_entry *> canonical;
    for (const textdb_phase0::canonical_entry &entry : canonical_entries)
        canonical[entry.canonical_key] = &entry;

    set<string> stable_ids;
    for (const tombstone_record &tombstone : source->tombstones)
    {
        if (tombstone.stable_id.empty() || tombstone.reason.empty()
            || !stable_ids.insert(tombstone.stable_id).second)
        {
            return _disable(load_failure::CORRUPT,
                            "invalid or duplicate tombstone stable ID");
        }
    }

    map<string, const catalog_entry *> catalog_entries;
    for (const catalog_entry &entry : source->entries)
    {
        if (entry.canonical_key.empty()
            || !catalog_entries.emplace(entry.canonical_key, &entry).second)
        {
            return _disable(load_failure::CORRUPT,
                            "invalid or duplicate catalog key");
        }
    }
    for (const catalog_entry &entry : source->entries)
    {
        if (entry.canonical_fingerprint.empty()
            || entry.selection_graph_fingerprint.empty())
        {
            return _disable(load_failure::CORRUPT,
                            "catalog fingerprint is missing");
        }
        const auto actual_found = canonical.find(entry.canonical_key);
        if (actual_found == canonical.end())
        {
            return _disable(load_failure::CLOSURE_INCOMPLETE,
                            "catalog key is absent from canonical SpeakDB");
        }
        const textdb_phase0::canonical_entry &actual = *actual_found->second;
        if (entry.canonical_fingerprint != _canonical_fingerprint(actual)
            || entry.selection_graph_fingerprint
               != _selection_fingerprint(actual))
        {
            return _disable(load_failure::CORRUPT,
                            "catalog fingerprint does not match canonical data");
        }
        if (actual.variants.size() != entry.variants.size())
        {
            return _disable(load_failure::CLOSURE_INCOMPLETE,
                            "catalog does not cover every selectable variant");
        }

        set<size_t> variant_ordinals;
        for (const catalog_variant &variant : entry.variants)
        {
            if (variant.stable_id.empty() || variant.tombstone
                || !stable_ids.insert(variant.stable_id).second
                || !variant_ordinals.insert(variant.variant_ordinal).second
                || variant.variant_ordinal >= actual.variants.size())
            {
                return _disable(load_failure::CORRUPT,
                                "invalid active stable ID or locator");
            }
            const textdb_phase0::canonical_variant &actual_variant =
                actual.variants[variant.variant_ordinal];
            if (actual_variant.locator.variant_ordinal
                    != variant.variant_ordinal
                || actual_variant.weight != variant.upstream_weight
                || actual_variant.raw_pattern != variant.english_snapshot
                || variant.upstream_variant_fingerprint.empty())
            {
                return _disable(load_failure::CORRUPT,
                                "canonical variant snapshot drifted");
            }

            const vector<string> direct_dependencies =
                _recursive_dependencies(actual_variant.raw_pattern, canonical);
            const bool full_recursive_closure =
                variant.policy == materialization_policy::CAPTURE_SLOT
                || variant.policy
                   == materialization_policy::RECURSIVE_CASE_MAP;
            const vector<string> dependencies =
                full_recursive_closure
                    ? _recursive_closure(actual_variant.raw_pattern, canonical)
                    : direct_dependencies;
            if (!_same_strings(dependencies,
                               variant.recursive_dependencies)
                || variant.recursive_dependencies.size()
                   != variant.recursive_dependency_fingerprints.size())
            {
                return _disable(load_failure::CLOSURE_INCOMPLETE,
                                "recursive closure declaration is incomplete");
            }
            if (full_recursive_closure)
            {
                for (size_t i = 0; i < dependencies.size(); ++i)
                {
                    const auto dependency = canonical.find(dependencies[i]);
                    if (dependency == canonical.end()
                        || variant.recursive_dependency_fingerprints[i]
                           != _canonical_fingerprint(*dependency->second))
                    {
                        return _disable(
                            load_failure::CLOSURE_INCOMPLETE,
                            "recursive capture closure fingerprint drifted");
                    }
                }
            }
            string binding_snapshot = actual_variant.raw_pattern;
            if (variant.policy
                == materialization_policy::RECURSIVE_CASE_MAP)
            {
                for (const string &dependency_key : dependencies)
                {
                    const auto dependency = canonical.find(dependency_key);
                    if (dependency == canonical.end())
                    {
                        return _disable(
                            load_failure::CLOSURE_INCOMPLETE,
                            "recursive binding closure is incomplete");
                    }
                    for (const textdb_phase0::canonical_variant &child
                         : dependency->second->variants)
                    {
                        binding_snapshot += child.raw_pattern;
                    }
                }
            }
            if (entry.mode == entry_mode::CANDIDATE)
            {
                for (const string &dependency : dependencies)
                {
                    if (variant.policy == materialization_policy::CAPTURE_SLOT)
                        continue;
                    const auto dependency_entry =
                        catalog_entries.find(dependency);
                    if (dependency_entry == catalog_entries.end()
                        || dependency_entry->second->mode
                           == entry_mode::LEGACY_ONLY)
                    {
                        return _disable(load_failure::CLOSURE_INCOMPLETE,
                                        "structured recursive closure missing");
                    }
                }
            }

            if (entry.mode == entry_mode::LEGACY_ONLY
                && variant.policy != materialization_policy::LEGACY_ONLY)
            {
                return _disable(load_failure::CORRUPT,
                                "legacy-only key has structured policy");
            }
            if (entry.mode == entry_mode::CANDIDATE
                && variant.policy == materialization_policy::LEGACY_ONLY)
            {
                return _disable(load_failure::CORRUPT,
                                "candidate key has legacy-only policy");
            }
            if (variant.suppresses && entry.mode != entry_mode::CANDIDATE)
            {
                return _disable(load_failure::CORRUPT,
                                "suppress descriptor must be CANDIDATE");
            }
            if (!variant.suppresses
                && entry.mode == entry_mode::CANDIDATE
                && actual_variant.raw_pattern == "__NONE")
            {
                return _disable(
                    load_failure::CORRUPT,
                    "candidate __NONE requires suppress descriptor");
            }
            if (entry.mode != entry_mode::LEGACY_ONLY
                && (variant.conditions.requires_named_foe
                    || variant.conditions.requires_god))
            {
                return _disable(load_failure::CORRUPT,
                                "applicability metadata is not enabled yet");
            }
            if (entry.mode == entry_mode::CANDIDATE
                && !variant.resolves_target
                && (binding_snapshot.find("@at@") != string::npos
                    || binding_snapshot.find("@target@")
                       != string::npos))
            {
                return _disable(load_failure::CORRUPT,
                                "non-target binding contains target tokens");
            }
            const bool has_foe_token =
                binding_snapshot.find("@foe@") != string::npos;
            const bool has_foe_slot = _has_slot_type(variant, "resolved_foe");
            const bool has_foe_possessive_token =
                binding_snapshot.find("@foe_possessive@") != string::npos;
            const bool has_foe_possessive_slot =
                _has_slot_type(variant, "resolved_foe_possessive");
            if (has_foe_token != has_foe_slot
                || has_foe_possessive_token != has_foe_possessive_slot
                || variant.conditions.requires_foe
                   != (has_foe_slot || has_foe_possessive_slot))
            {
                return _disable(load_failure::CORRUPT,
                                "foe token/type/applicability mismatch");
            }
            const bool has_arms_token =
                binding_snapshot.find("@arms@") != string::npos;
            if (has_arms_token
                != _has_slot_type(variant, "actor_arms_plural"))
            {
                return _disable(load_failure::CORRUPT,
                                "plural arms token/type mismatch");
            }
            if (variant.policy == materialization_policy::CAPTURE_SLOT)
            {
                if (variant.materialization_cases.size()
                    || variant.recursive_captures.size() != 3
                    || variant.recursive_capture_vocabulary.size() != 103
                    || direct_dependencies
                       != vector<string>{ "orc name" })
                {
                    return _disable(load_failure::CORRUPT,
                                    "recursive capture declaration is invalid");
                }
                set<string> capture_names;
                set<string> capture_slot_names;
                for (const slot_definition &slot : variant.slot_schema)
                {
                    if (slot.type == "recursive_capture")
                        capture_slot_names.insert(slot.name);
                }
                for (size_t i = 0; i < variant.recursive_captures.size(); ++i)
                {
                    const recursive_capture_definition &capture =
                        variant.recursive_captures[i];
                    if (!_valid_identifier(capture.name)
                        || !capture_names.insert(capture.name).second
                        || capture.marker != "orc name"
                        || capture.ordinal != i
                        || capture.vocabulary != "orc_name_leaf_v1")
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "recursive capture site declaration is invalid");
                    }
                }
                if (capture_names != capture_slot_names)
                {
                    return _disable(
                        load_failure::CORRUPT,
                        "recursive capture slots do not match declarations");
                }
                map<pair<string, size_t>, pair<string, string>>
                    expected_vocabulary;
                const auto orc_names = canonical.find("orc name");
                if (orc_names == canonical.end())
                {
                    return _disable(
                        load_failure::CORRUPT,
                        "recursive capture vocabulary root is missing");
                }
                set<string> reachable_leaf_keys;
                vector<string> parent_leaf_mapping(
                    orc_names->second->variants.size());
                for (const textdb_phase0::canonical_variant &orc_variant
                     : orc_names->second->variants)
                {
                    const vector<string> leaf_dependencies =
                        _recursive_dependencies(
                            orc_variant.raw_pattern, canonical);
                    if (leaf_dependencies.size() != 1)
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "recursive capture vocabulary root is not leaf-only");
                    }
                    if (orc_variant.raw_pattern
                        != "@" + leaf_dependencies[0] + "@")
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "recursive capture parent is not one exact marker");
                    }
                    if (orc_variant.locator.variant_ordinal
                        >= parent_leaf_mapping.size()
                        || !parent_leaf_mapping[
                            orc_variant.locator.variant_ordinal].empty())
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "recursive capture parent mapping is invalid");
                    }
                    parent_leaf_mapping[
                        orc_variant.locator.variant_ordinal] =
                            leaf_dependencies[0];
                    reachable_leaf_keys.insert(leaf_dependencies[0]);
                }
                if (parent_leaf_mapping.size() != 3
                    || any_of(
                        parent_leaf_mapping.begin(),
                        parent_leaf_mapping.end(),
                        [](const string &key) { return key.empty(); }))
                {
                    return _disable(
                        load_failure::CORRUPT,
                        "recursive capture parent mapping is incomplete");
                }
                for (const string &leaf_key : reachable_leaf_keys)
                {
                    const auto leaf = canonical.find(leaf_key);
                    if (leaf == canonical.end())
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "recursive capture vocabulary leaf is missing");
                    }
                    for (const textdb_phase0::canonical_variant &leaf_variant
                         : leaf->second->variants)
                    {
                        if (!_recursive_dependencies(
                                leaf_variant.raw_pattern, canonical).empty()
                            || leaf_variant.raw_pattern.find('@')
                               != string::npos
                            || leaf_variant.raw_pattern.find('[')
                               != string::npos
                            || leaf_variant.raw_pattern.find(']')
                               != string::npos
                            || leaf_variant.raw_pattern.find("{{")
                               != string::npos
                            || leaf_variant.raw_pattern.find("}}")
                               != string::npos)
                        {
                            return _disable(
                                load_failure::CORRUPT,
                                "recursive capture vocabulary leaf is dynamic");
                        }
                        expected_vocabulary.emplace(
                            make_pair(
                                leaf_key,
                                leaf_variant.locator.variant_ordinal),
                            make_pair(
                                _variant_fingerprint(leaf_variant),
                                leaf_variant.raw_pattern));
                    }
                }
                map<pair<string, size_t>, pair<string, string>>
                    declared_vocabulary;
                for (const recursive_capture_vocabulary_entry &word
                     : variant.recursive_capture_vocabulary)
                {
                    if (!declared_vocabulary.emplace(
                            make_pair(
                                word.canonical_key, word.variant_ordinal),
                            make_pair(
                                word.variant_fingerprint,
                                word.expanded_replacement_en)).second)
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "recursive capture vocabulary is invalid");
                    }
                }
                if (declared_vocabulary != expected_vocabulary)
                {
                    return _disable(
                        load_failure::CORRUPT,
                        "recursive capture vocabulary does not match closure");
                }
                capture_parent_leaf_keys[variant.stable_id] =
                    parent_leaf_mapping;
            }
            else if (!variant.recursive_captures.empty()
                     || !variant.recursive_capture_vocabulary.empty())
            {
                return _disable(load_failure::CORRUPT,
                                "non-capture policy declares captures");
            }
            if (variant.policy == materialization_policy::NONE
                && (actual_variant.raw_pattern.find('[') != string::npos
                    || actual_variant.raw_pattern.find("{{") != string::npos
                    || !dependencies.empty()
                    || !variant.materialization_cases.empty()))
            {
                return _disable(load_failure::CORRUPT,
                                "NONE policy contains dynamic materialization");
            }

            if (variant.policy == materialization_policy::CASE_MAP)
            {
                set<string> expected_signatures;
                if (!_single_site_case_signatures(entry.canonical_key,
                        variant.variant_ordinal, actual_variant.raw_pattern,
                        expected_signatures)
                    || actual_variant.raw_pattern.find("{{") != string::npos
                    || !dependencies.empty() || !variant.lines.empty()
                    || variant.materialization_cases.size()
                       != expected_signatures.size())
                {
                    return _disable(load_failure::CORRUPT,
                                    "CASE_MAP dynamic closure is incomplete");
                }
                set<string> signatures;
                const vector<line_metadata> *shape = nullptr;
                for (const materialization_case &materialized
                     : variant.materialization_cases)
                {
                    if (materialized.case_id.empty()
                        || materialized.signature.empty()
                        || !stable_ids.insert(materialized.case_id).second
                        || !signatures.insert(materialized.signature).second)
                    {
                        return _disable(load_failure::CORRUPT,
                                        "invalid CASE_MAP stable ID/signature");
                    }
                    catalog_variant case_variant = variant;
                    case_variant.policy = materialization_policy::NONE;
                    case_variant.english_snapshot = binding_snapshot;
                    case_variant.lines = materialized.lines;
                    case_variant.materialization_cases.clear();
                    string case_error;
                    if (!_validate_lines(*source, case_variant, case_error))
                        return _disable(load_failure::CORRUPT, case_error);
                    if (shape
                        && !_same_case_line_shape(*shape, materialized.lines))
                    {
                        return _disable(load_failure::CORRUPT,
                            "CASE_MAP changes binding-relevant line metadata");
                    }
                    shape = &materialized.lines;
                }
                if (signatures != expected_signatures)
                {
                    return _disable(load_failure::CORRUPT,
                                    "CASE_MAP signature set is incomplete");
                }
            }

            if (variant.policy
                == materialization_policy::RECURSIVE_CASE_MAP)
            {
                set<string> expected_signatures;
                string identity_error;
                if (direct_dependencies.empty()
                    || actual_variant.raw_pattern.find('[') != string::npos
                    || actual_variant.raw_pattern.find(']') != string::npos
                    || actual_variant.raw_pattern.find("{{") != string::npos
                    || actual_variant.raw_pattern.find("}}") != string::npos
                    || !variant.lines.empty()
                    || !_recursive_case_signatures(
                        canonical, entry.canonical_key,
                        variant.variant_ordinal, expected_signatures,
                        identity_error)
                    || variant.materialization_cases.size()
                       != expected_signatures.size())
                {
                    return _disable(
                        load_failure::CORRUPT,
                        identity_error.empty()
                            ? "RECURSIVE_CASE_MAP dynamic closure is incomplete"
                            : identity_error);
                }
                set<string> signatures;
                const vector<line_metadata> *shape = nullptr;
                for (const materialization_case &materialized
                     : variant.materialization_cases)
                {
                    if (materialized.case_id.empty()
                        || materialized.signature.empty()
                        || !stable_ids.insert(materialized.case_id).second
                        || !signatures.insert(materialized.signature).second)
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "invalid RECURSIVE_CASE_MAP stable ID/signature");
                    }
                    catalog_variant case_variant = variant;
                    case_variant.policy = materialization_policy::NONE;
                    case_variant.english_snapshot = binding_snapshot;
                    case_variant.lines = materialized.lines;
                    case_variant.materialization_cases.clear();
                    string case_error;
                    if (!_validate_lines(*source, case_variant, case_error))
                        return _disable(load_failure::CORRUPT, case_error);
                    if (shape
                        && !_same_case_line_shape(*shape, materialized.lines))
                    {
                        return _disable(
                            load_failure::CORRUPT,
                            "RECURSIVE_CASE_MAP changes binding-relevant line metadata");
                    }
                    shape = &materialized.lines;
                }
                if (signatures != expected_signatures)
                {
                    return _disable(
                        load_failure::CORRUPT,
                        "RECURSIVE_CASE_MAP signature set is incomplete");
                }
            }

            string line_error;
            if (variant.policy != materialization_policy::CASE_MAP
                && variant.policy
                   != materialization_policy::RECURSIVE_CASE_MAP
                && !_validate_lines(*source, variant, line_error))
                return _disable(load_failure::CORRUPT, line_error);
        }
    }

    for (const auto &item : catalog_entries)
    {
        if (item.second->mode == entry_mode::CANDIDATE)
            covered_keys.insert(item.first);
    }
    active_catalog = *source;
    active_catalog_loaded = true;
    current_report.state = domain_state::ENABLED;
    current_report.failure = load_failure::NONE;
    current_report.diagnostic.clear();
    current_report.structured_key_count = covered_keys.size();
    return current_report;
}

const load_report &monspell_overlay_report()
{
    return current_report;
}

bool monspell_overlay_covers(const string &canonical_key)
{
    if (current_report.state == domain_state::UNINITIALIZED)
        _disable(load_failure::NOT_LOADED, "overlay queried before loading");
    if (current_report.state != domain_state::ENABLED)
        return false;
    string key = canonical_key;
    lowercase(key);
    return covered_keys.count(key) != 0;
}

static bool _catalog_declares_candidate(const string &canonical_key)
{
    const catalog_source &catalog = _catalog();
    return any_of(
        catalog.entries.begin(), catalog.entries.end(),
        [&canonical_key](const catalog_entry &entry)
        {
            return entry.mode == entry_mode::CANDIDATE
                   && entry.canonical_key == canonical_key;
        });
}

route_decision route_monspell_message(const string &canonical_key)
{
    return route_monspell_message(canonical_key, "en");
}

route_decision route_monspell_message(const string &canonical_key,
                                      const string &language)
{
    route_decision decision;
    decision.canonical_key = canonical_key;
    lowercase(decision.canonical_key);
    const bool supported_language = language == "en" || language == "zh";
    const bool overlay_enabled =
        monspell_overlay_report().state == domain_state::ENABLED;
    if (supported_language && monspell_overlay_covers(decision.canonical_key))
    {
        decision.route = message_route::STRUCTURED;
        ++current_diagnostics.overlay_hit;
    }
    else
    {
        decision.legacy_behavior_compatibility =
            (!overlay_enabled || !supported_language)
            && _catalog_declares_candidate(decision.canonical_key);
        ++current_diagnostics.legacy_fallback;
    }
    return decision;
}

message_search_action transition_message_candidate(message_attempt attempt,
                                                   message_result result)
{
    switch (result)
    {
    case message_result::SUPPRESS:
        return message_search_action::STOP_SILENT;
    case message_result::RENDERED:
        return message_search_action::STOP_RENDERED;
    case message_result::CORRUPT:
        return message_search_action::STOP_CORRUPT;
    case message_result::MISSING:
    case message_result::INAPPLICABLE:
        return attempt == message_attempt::SILENT_PREFIXED
            ? message_search_action::RETRY_UNPREFIXED
            : message_search_action::NEXT_CANDIDATE;
    }
    die("Invalid message overlay result");
}

message_candidate_search search_message_candidate(
    const string &base_key, message_prefix prefix,
    const message_lookup &lookup)
{
    message_candidate_search search;
    if (!lookup)
    {
        search.lookup.result = message_result::CORRUPT;
        search.lookup.diagnostic = "message lookup callback is missing";
        _record_message_result(search.lookup.result);
        search.action = message_search_action::STOP_CORRUPT;
        return search;
    }
    message_lookup_request request = _initial_request(base_key, prefix);
    search.lookup = lookup(request);
    ++search.lookup_count;
    _record_message_result(search.lookup.result);
    search.action = transition_message_candidate(request.attempt,
                                                  search.lookup.result);
    if (search.action != message_search_action::RETRY_UNPREFIXED)
        return search;

    request = _silent_unprefixed_request(base_key);
    search.lookup = lookup(request);
    ++search.lookup_count;
    _record_message_result(search.lookup.result);
    search.action = transition_message_candidate(request.attempt,
                                                  search.lookup.result);
    return search;
}

canonical_materialization materialize_monspell_candidate(
    const string &canonical_key, message_attempt attempt,
    bool manifest_applicable, const runtime_binding_resolver &bindings)
{
    runtime_applicability applicability;
    applicability.manifest_applicable = manifest_applicable;
    applicability.caster_visibility = message_visibility::VISIBLE;
    return materialize_monspell_candidate(
        canonical_key, attempt, applicability, bindings,
        [](const string &key)
        {
            return canonical_textdb::expand_loaded_english_candidate(key);
        });
}

canonical_materialization materialize_monspell_candidate(
    const string &canonical_key, message_attempt attempt,
    bool manifest_applicable, const runtime_binding_resolver &bindings,
    const canonical_candidate_lookup &lookup)
{
    runtime_applicability applicability;
    applicability.manifest_applicable = manifest_applicable;
    applicability.caster_visibility = message_visibility::VISIBLE;
    return materialize_monspell_candidate(
        canonical_key, attempt, applicability, bindings, lookup);
}

canonical_materialization materialize_monspell_candidate(
    const string &canonical_key, message_attempt attempt,
    const runtime_applicability &applicability,
    const runtime_binding_resolver &bindings)
{
    return materialize_monspell_candidate(
        canonical_key, attempt, applicability, bindings,
        [](const string &key)
        {
            return canonical_textdb::expand_loaded_english_candidate(key);
        });
}

canonical_materialization materialize_monspell_candidate(
    const string &canonical_key, message_attempt attempt,
    const runtime_applicability &applicability,
    const runtime_binding_resolver &bindings,
    const canonical_candidate_lookup &lookup)
{
    canonical_materialization result;
    if (!lookup)
    {
        result.diagnostic = "canonical candidate lookup is missing";
        return result;
    }
    result.canonical = lookup(canonical_key);
    switch (result.canonical.status)
    {
    case canonical_textdb::candidate_status::MISSING:
        result.result = message_result::MISSING;
        result.diagnostic = result.canonical.error;
        return result;
    case canonical_textdb::candidate_status::CORRUPT:
        result.result = message_result::CORRUPT;
        result.diagnostic = result.canonical.error;
        return result;
    case canonical_textdb::candidate_status::SELECTED:
        break;
    }
    if (result.canonical.expanded_pattern_en == "__NONE")
    {
        result.result = message_result::SUPPRESS;
        return result;
    }
    const bool accepts_any =
        attempt == message_attempt::SILENT_UNPREFIXED_FALLBACK;
    if (result.canonical.expanded_pattern_en.empty())
    {
        result.result = message_result::INAPPLICABLE;
        return result;
    }
    const catalog_variant *descriptor = _find_catalog_variant_by_locator(
        result.canonical.top_locator.canonical_key,
        result.canonical.top_locator.variant_ordinal);
    if (!descriptor)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "canonical locator has no catalog descriptor";
        return result;
    }
    if (!accepts_any)
    {
        if (!applicability.manifest_applicable)
        {
            result.result = message_result::INAPPLICABLE;
            return result;
        }
        if (descriptor->conditions.requires_player
            && !applicability.player_applicable)
        {
            result.result = message_result::INAPPLICABLE;
            return result;
        }
        if (descriptor->conditions.requires_foe
            && !applicability.foe_applicable)
        {
            result.result = message_result::INAPPLICABLE;
            return result;
        }
        if (descriptor->conditions.requires_caster_visible)
        {
            if (applicability.caster_visibility == message_visibility::UNSEEN)
            {
                result.result = message_result::INAPPLICABLE;
                return result;
            }
            if (applicability.caster_visibility == message_visibility::UNKNOWN)
            {
                result.result = message_result::CORRUPT;
                result.diagnostic =
                    "caster visibility is required but unknown";
                return result;
            }
        }
    }
    if (!descriptor->resolves_target
        && (result.canonical.expanded_pattern_en.find("@at@") != string::npos
            || result.canonical.expanded_pattern_en.find("@target@")
               != string::npos))
    {
        result.result = message_result::CORRUPT;
        result.diagnostic =
            "non-target materialization contains target tokens";
        return result;
    }
    if (!_extract_recursive_captures(
            *descriptor, result.canonical, result.recursive_captures,
            result.materialization_signature, result.diagnostic))
    {
        result.result = message_result::CORRUPT;
        if (result.diagnostic.empty())
            result.diagnostic = "unexpected recursive capture metadata";
        return result;
    }
    if ((result.canonical.expanded_pattern_en.find("@arms@") != string::npos)
        != _has_slot_type(*descriptor, "actor_arms_plural"))
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "materialized plural arms token/type mismatch";
        return result;
    }
    if (!bindings)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "runtime binding resolver is missing";
        return result;
    }

    const vector<line_metadata> *requirement_lines = &descriptor->lines;
    if (descriptor->policy == materialization_policy::CASE_MAP
        || descriptor->policy
           == materialization_policy::RECURSIVE_CASE_MAP)
    {
        if (descriptor->materialization_cases.empty())
        {
            result.result = message_result::CORRUPT;
            result.diagnostic = "CASE_MAP has no binding metadata";
            return result;
        }
        requirement_lines = &descriptor->materialization_cases.front().lines;
    }
    result.requirements.frame = descriptor->frame;
    result.requirements.resolves_target = descriptor->resolves_target;
    result.requirements.needs_foe =
        _has_slot_type(*descriptor, "resolved_foe")
        || _has_slot_type(*descriptor, "resolved_foe_possessive");
    result.requirements.implies_gesture = any_of(
        requirement_lines->begin(), requirement_lines->end(),
        [](const line_metadata &line) { return line.implies_gesture; });
    result.requirements.needs_actor_arms_plural =
        _has_slot_type(*descriptor, "actor_arms_plural");
    result.requirements.needs_player_name =
        _has_slot_type(*descriptor, "player_name");
    result.binding.rng.before = canonical_textdb::observe_rng();
    result.binding.values = bindings(result.requirements);
    result.binding.rng.after = canonical_textdb::observe_rng();
    result.binding.callback_count = 1;
    const runtime_bindings &resolved = result.binding.values;
    bool needs_actor_ref = false;
    bool needs_actor_ref_lower = false;
    bool needs_actor_possessive_name = false;
    bool needs_actor_possessive_name_lower = false;
    bool needs_actor_possessive_pronoun = false;
    bool needs_actor_subjective_pronoun = false;
    bool needs_actor_god_possessive = false;
    bool needs_actor_god_my = false;
    bool needs_actor_god_indefinite = false;
    bool needs_actor_reflexive = false;
    bool needs_actor_arms_plural = false;
    bool needs_target = false;
    bool needs_foe = false;
    bool needs_foe_possessive = false;
    bool needs_beam = false;
    for (const slot_definition &slot : descriptor->slot_schema)
    {
        needs_actor_ref = needs_actor_ref || slot.type == "actor_ref";
        needs_actor_ref_lower = needs_actor_ref_lower
            || slot.type == "actor_ref_lower";
        needs_actor_possessive_name = needs_actor_possessive_name
            || slot.type == "actor_possessive_name";
        needs_actor_possessive_name_lower = needs_actor_possessive_name_lower
            || slot.type == "actor_possessive_name_lower";
        needs_actor_possessive_pronoun = needs_actor_possessive_pronoun
            || slot.type == "actor_possessive_pronoun";
        needs_actor_subjective_pronoun = needs_actor_subjective_pronoun
            || slot.type == "actor_subjective_pronoun";
        needs_actor_god_possessive = needs_actor_god_possessive
            || slot.type == "actor_god_possessive";
        needs_actor_god_my = needs_actor_god_my
            || slot.type == "actor_god_my";
        needs_actor_god_indefinite = needs_actor_god_indefinite
            || slot.type == "actor_god_indefinite";
        needs_actor_reflexive = needs_actor_reflexive
            || slot.type == "actor_reflexive";
        needs_actor_arms_plural = needs_actor_arms_plural
            || slot.type == "actor_arms_plural";
        needs_target = needs_target || slot.type == "resolved_target";
        needs_foe = needs_foe || slot.type == "resolved_foe";
        needs_foe_possessive = needs_foe_possessive
            || slot.type == "resolved_foe_possessive";
        needs_beam = needs_beam || slot.type == "resolved_beam";
    }
    if ((needs_actor_ref && (resolved.actor.sentence_en.empty()
                             || resolved.actor.canonical_en.empty()))
        || (needs_actor_ref_lower && resolved.actor.canonical_en.empty())
        || (needs_actor_possessive_name
            && resolved.actor.possessive_name_en.empty())
        || (needs_actor_possessive_name_lower
            && resolved.actor.possessive_name_lower_en.empty())
        || (needs_actor_possessive_pronoun
            && resolved.actor.possessive_pronoun_en.empty())
        || (needs_actor_subjective_pronoun
            && resolved.actor.subjective_pronoun_en.empty())
        || (needs_actor_god_possessive
            && resolved.actor.god_possessive_en.empty())
        || (needs_actor_god_my && resolved.actor.god_my_en.empty())
        || (needs_actor_god_indefinite
            && resolved.actor.god_indefinite_en.empty())
        || (needs_actor_reflexive && resolved.actor.reflexive_en.empty())
        || (needs_actor_arms_plural
            && resolved.actor.arms_plural_en.empty())
        || (descriptor->resolves_target
            && (resolved.target.relation == target_relation::NONE
                || resolved.target.relation_en.empty()))
        || (needs_target
            && (!_valid_target_payload(resolved.target)
                || resolved.target.canonical_en.empty()))
        || (needs_foe && !_valid_foe_payload(resolved.foe))
        || (needs_foe_possessive
            && (!_valid_foe_payload(resolved.foe)
                || resolved.foe.possessive_en.empty()))
        || (result.requirements.needs_player_name
            && resolved.player_name.empty())
        || (needs_beam && resolved.beam.canonical_en.empty()))
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "runtime bindings are incomplete";
        return result;
    }
    if (!descriptor->resolves_target
        && resolved.target.relation != target_relation::NONE)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "non-target binding unexpectedly resolved target";
        return result;
    }

    result.bound_pattern_en = replace_all(
        result.canonical.expanded_pattern_en, "@The_monster@",
        resolved.actor.sentence_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@The_something@",
        resolved.actor.sentence_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@the_monster@",
        resolved.actor.canonical_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@The_monster_possessive@",
        resolved.actor.possessive_name_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@the_monster_possessive@",
        resolved.actor.possessive_name_lower_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@possessive@",
        resolved.actor.possessive_pronoun_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@subjective@",
        resolved.actor.subjective_pronoun_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@possessive_God@",
        resolved.actor.god_possessive_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@My_God@", resolved.actor.god_my_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@a_God@",
        resolved.actor.god_indefinite_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@reflexive@",
        resolved.actor.reflexive_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@arms@",
        resolved.actor.arms_plural_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@at@", resolved.target.relation_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@target@", resolved.target.canonical_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@foe@", resolved.foe.canonical_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@foe_possessive@",
        resolved.foe.possessive_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@player_name@", resolved.player_name);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@player_only@", "");
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@beam@", resolved.beam.canonical_en);
    if (result.bound_pattern_en.find('@') != string::npos)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "materialized pattern retains a legacy token";
        return result;
    }

    result.randomized = canonical_textdb::materialize_bound_legacy_randomness(
        result.canonical, result.bound_pattern_en);
    if (result.randomized.status
        != canonical_textdb::candidate_status::SELECTED)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = result.randomized.error;
        return result;
    }
    if (result.canonical.lua_site_count != 0
        || (descriptor->policy != materialization_policy::CAPTURE_SLOT
            && descriptor->policy
               != materialization_policy::RECURSIVE_CASE_MAP
            && result.canonical.selected_variants.size() != 1))
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "structured policy observed unsupported dynamics";
        return result;
    }
    if (descriptor->policy == materialization_policy::NONE
        && (result.randomized.signature != "NONE"
            || result.randomized.random_site_count != 0
            || result.randomized.pattern_en != result.bound_pattern_en
            || result.canonical.expanded_pattern_en.find('[')
               != string::npos))
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "NONE policy observed dynamic materialization";
        return result;
    }
    if (descriptor->policy == materialization_policy::CASE_MAP
        && (result.randomized.signature == "NONE"
            || result.randomized.random_site_count == 0
            || result.randomized.pattern_en.find('[') != string::npos
            || !_find_materialization_case(*descriptor,
                                           result.randomized.signature)))
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "CASE_MAP materialization signature is unknown";
        return result;
    }
    if (descriptor->policy
            == materialization_policy::RECURSIVE_CASE_MAP
        && (result.randomized.signature == "NONE"
            || result.randomized.random_site_count != 0
            || result.randomized.pattern_en != result.bound_pattern_en
            || result.canonical.expanded_pattern_en.find('[')
               != string::npos
            || !_find_materialization_case(*descriptor,
                                           result.randomized.signature)))
    {
        result.result = message_result::CORRUPT;
        result.diagnostic =
            "RECURSIVE_CASE_MAP materialization signature is unknown";
        return result;
    }
    if (descriptor->policy == materialization_policy::CAPTURE_SLOT)
    {
        if (result.randomized.signature
                != result.materialization_signature
            || result.randomized.random_site_count != 0
            || result.randomized.pattern_en != result.bound_pattern_en
            || result.canonical.expanded_pattern_en.find('[')
               != string::npos
            || descriptor->lines.size() != 1)
        {
            result.result = message_result::CORRUPT;
            result.diagnostic =
                "CAPTURE_SLOT observed unsupported materialization";
            return result;
        }
        const localized_template *english_template = nullptr;
        for (const localized_template &localized
             : descriptor->lines[0].templates)
        {
            if (localized.language == "en" && localized.relation == "NONE")
            {
                if (english_template)
                {
                    result.result = message_result::CORRUPT;
                    result.diagnostic =
                        "CAPTURE_SLOT has ambiguous English template";
                    return result;
                }
                english_template = &localized;
            }
        }
        vector<slot_value> english_values = result.recursive_captures;
        for (const slot_definition &slot : descriptor->slot_schema)
        {
            if (slot.type == "actor_ref")
                english_values.push_back(
                    { slot.name, resolved.actor.sentence_en });
            else if (slot.type == "actor_ref_lower")
                english_values.push_back(
                    { slot.name, resolved.actor.canonical_en });
            else if (slot.type == "actor_possessive_name")
                english_values.push_back(
                    { slot.name, resolved.actor.possessive_name_en });
            else if (slot.type == "actor_possessive_name_lower")
                english_values.push_back(
                    { slot.name, resolved.actor.possessive_name_lower_en });
            else if (slot.type == "actor_subjective_pronoun")
                english_values.push_back(
                    { slot.name, resolved.actor.subjective_pronoun_en });
            else if (slot.type == "player_name")
                english_values.push_back({ slot.name, resolved.player_name });
            else if (slot.type == "actor_god_possessive")
                english_values.push_back(
                    { slot.name, resolved.actor.god_possessive_en });
            else if (slot.type == "actor_god_my")
                english_values.push_back(
                    { slot.name, resolved.actor.god_my_en });
            else if (slot.type == "actor_god_indefinite")
                english_values.push_back(
                    { slot.name, resolved.actor.god_indefinite_en });
        }
        const render_result english = english_template
            ? render_typed_template(
                  english_template->pattern, descriptor->slot_schema,
                  english_values)
            : render_result();
        if (english.result != message_result::RENDERED
            || english.lines.size() != 1
            || english.lines[0].text != result.randomized.pattern_en)
        {
            result.result = message_result::CORRUPT;
            result.diagnostic =
                "CAPTURE_SLOT English reconstruction does not match legacy";
            return result;
        }
    }

    const catalog_variant *variant =
        descriptor->policy == materialization_policy::CAPTURE_SLOT
            ? descriptor
            : _find_catalog_variant(
                result.canonical.top_locator.canonical_key,
                result.canonical.top_locator.variant_ordinal,
                result.randomized.signature);
    if (!variant || variant != descriptor
        || variant->frame != resolved.cast.frame)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "canonical locator has no matching catalog case";
        return result;
    }
    const materialization_case *materialized_case =
        _find_materialization_case(*variant, result.randomized.signature);
    result.stable_id = materialized_case
        ? materialized_case->case_id : variant->stable_id;
    result.materialization_signature = result.randomized.signature;
    result.result = message_result::RENDERED;
    return result;
}

render_result render_typed_template(
    const string &pattern, const vector<slot_definition> &declarations,
    const vector<slot_value> &values)
{
    render_result result;
    if (pattern.find('\n') != string::npos)
    {
        result.diagnostic = "typed line contains an embedded newline";
        return result;
    }
    map<string, string> declared;
    for (const slot_definition &slot : declarations)
    {
        if (!_valid_identifier(slot.name) || slot.type.empty()
            || !declared.emplace(slot.name, slot.type).second)
        {
            result.diagnostic = "invalid or duplicate slot declaration";
            return result;
        }
    }
    map<string, string> supplied;
    for (const slot_value &value : values)
    {
        if (!_valid_identifier(value.name) || value.value.empty()
            || !supplied.emplace(value.name, value.value).second)
        {
            result.diagnostic = "invalid or duplicate slot value";
            return result;
        }
    }
    if (declared.size() != supplied.size())
    {
        result.diagnostic = "missing or extra slot value";
        return result;
    }
    for (const auto &item : declared)
    {
        if (!supplied.count(item.first))
        {
            result.diagnostic = "missing or extra slot value";
            return result;
        }
    }
    if (_contains_protocol_text(pattern)
        && pattern.find("${") == string::npos)
    {
        result.diagnostic = "template contains protocol text";
        return result;
    }

    string rendered;
    size_t position = 0;
    while (position < pattern.size())
    {
        const size_t slot = pattern.find("${", position);
        if (slot == string::npos)
        {
            rendered += pattern.substr(position);
            break;
        }
        rendered += pattern.substr(position, slot - position);
        const size_t end = pattern.find('}', slot + 2);
        if (end == string::npos)
        {
            result.diagnostic = "template has an unclosed typed slot";
            return result;
        }
        const string name = pattern.substr(slot + 2, end - slot - 2);
        if (!_valid_identifier(name) || !declared.count(name))
        {
            result.diagnostic = "template references an undeclared slot";
            return result;
        }
        rendered += supplied[name];
        position = end + 1;
    }
    if (_contains_protocol_text(rendered))
    {
        result.diagnostic = "rendered text contains protocol residue";
        return result;
    }
    rendered_line line;
    line.text = rendered;
    result.lines.push_back(line);
    result.result = message_result::RENDERED;
    return result;
}

render_result render_typed_lines(
    const vector<line_metadata> &lines, const string &language,
    target_relation relation, const vector<slot_definition> &declarations,
    const vector<slot_value> &values)
{
    render_result result;
    const string relation_name = _relation_name(relation);
    for (const line_metadata &metadata : lines)
    {
        const localized_template *selected = nullptr;
        for (const localized_template &candidate : metadata.templates)
        {
            if (candidate.language == language
                && candidate.relation == relation_name)
            {
                if (selected)
                {
                    result.diagnostic = "duplicate localized template";
                    return result;
                }
                selected = &candidate;
            }
        }
        if (!selected)
        {
            result.diagnostic = "localized template is missing";
            return result;
        }
        const render_result rendered = render_typed_template(
            selected->pattern, declarations, values);
        if (rendered.result != message_result::RENDERED
            || rendered.lines.size() != 1)
        {
            return rendered;
        }
        rendered_line line = rendered.lines[0];
        line.sensory = metadata.sensory;
        line.channel = metadata.channel;
        line.implies_gesture = metadata.implies_gesture;
        line.audible = metadata.audible;
        result.lines.push_back(line);
    }
    result.result = message_result::RENDERED;
    return result;
}

render_result render_materialized_candidate(
    const canonical_materialization &materialized, const string &language)
{
    render_result result;
    if (materialized.result != message_result::RENDERED)
    {
        result.result = materialized.result;
        result.diagnostic = materialized.diagnostic;
        return result;
    }
    const catalog_variant *variant = _find_catalog_variant_by_locator(
        materialized.canonical.top_locator.canonical_key,
        materialized.canonical.top_locator.variant_ordinal);
    if (variant && variant->policy == materialization_policy::CAPTURE_SLOT)
    {
        vector<slot_value> captures;
        string identity;
        string error;
        if (!_extract_recursive_captures(
                *variant, materialized.canonical, captures, identity, error)
            || identity != materialized.randomized.signature
            || identity != materialized.materialization_signature
            || captures.size() != materialized.recursive_captures.size())
        {
            result.diagnostic = error.empty()
                ? "materialized capture identity is invalid" : error;
            return result;
        }
        for (size_t i = 0; i < captures.size(); ++i)
        {
            if (captures[i].name != materialized.recursive_captures[i].name
                || captures[i].value
                   != materialized.recursive_captures[i].value)
            {
                result.diagnostic =
                    "materialized capture values do not match canonical trace";
                return result;
            }
        }
    }
    else
    {
        variant = _find_catalog_variant(
            materialized.canonical.top_locator.canonical_key,
            materialized.canonical.top_locator.variant_ordinal,
            materialized.materialization_signature);
        if (materialized.materialization_signature
            != materialized.randomized.signature)
        {
            result.diagnostic =
                "materialization signature does not match canonical randomness";
            return result;
        }
    }
    const materialization_case *materialized_case = variant
        ? _find_materialization_case(*variant,
                                     materialized.materialization_signature)
        : nullptr;
    const string expected_id = materialized_case
        ? materialized_case->case_id : (variant ? variant->stable_id : "");
    if (!variant || expected_id != materialized.stable_id)
    {
        result.diagnostic = "materialized stable ID is not in the catalog";
        return result;
    }
    const target_relation relation =
        materialized.binding.values.target.relation;
    if ((variant->resolves_target && relation == target_relation::NONE)
        || (!variant->resolves_target && relation != target_relation::NONE))
    {
        result.diagnostic = "binding relation does not match descriptor";
        return result;
    }
    vector<slot_value> values;
    for (const slot_definition &slot : variant->slot_schema)
    {
        string display;
        if (slot.type == "actor_ref")
        {
            if (!_localized_display(
                    materialized.binding.values.actor.localized,
                    language, display))
            {
                result.diagnostic = "localized actor binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_ref_lower")
        {
            if (!_localized_display(
                    materialized.binding.values.actor.lower_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized lower-case actor binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_possessive_name")
        {
            if (!_localized_display(
                    materialized.binding.values.actor.possessive_name_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized actor possessive-name binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_possessive_name_lower")
        {
            if (!_localized_display(
                    materialized.binding.values.actor
                        .possessive_name_lower_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized lower-case actor possessive-name binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_possessive_pronoun")
        {
            if (!_localized_display(
                    materialized.binding.values.actor
                        .possessive_pronoun_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized actor possessive-pronoun binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_subjective_pronoun")
        {
            if (!_localized_display(
                    materialized.binding.values.actor
                        .subjective_pronoun_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized actor subjective-pronoun binding is missing";
                return result;
            }
        }
        else if (slot.type == "player_name")
        {
            display = materialized.binding.values.player_name;
            if (display.empty())
            {
                result.diagnostic = "player-name binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_god_possessive")
        {
            if (!_localized_display(
                    materialized.binding.values.actor
                        .god_possessive_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized actor possessive-god binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_god_my")
        {
            if (!_localized_display(
                    materialized.binding.values.actor.god_my_localized,
                    language, display))
            {
                result.diagnostic = "localized actor my-god binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_god_indefinite")
        {
            if (!_localized_display(
                    materialized.binding.values.actor
                        .god_indefinite_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized actor indefinite-god binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_reflexive")
        {
            if (!_localized_display(
                    materialized.binding.values.actor.reflexive_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized actor reflexive binding is missing";
                return result;
            }
        }
        else if (slot.type == "actor_arms_plural")
        {
            if (!_localized_display(
                    materialized.binding.values.actor.arms_plural_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized actor plural-arms binding is missing";
                return result;
            }
        }
        else if (slot.type == "resolved_target")
        {
            if (!_localized_display(
                    materialized.binding.values.target.localized,
                    language, display))
            {
                result.diagnostic = "localized target binding is missing";
                return result;
            }
        }
        else if (slot.type == "resolved_foe")
        {
            if (!_localized_display(
                    materialized.binding.values.foe.localized,
                    language, display))
            {
                result.diagnostic = "localized foe binding is missing";
                return result;
            }
        }
        else if (slot.type == "resolved_foe_possessive")
        {
            if (!_localized_display(
                    materialized.binding.values.foe.possessive_localized,
                    language, display))
            {
                result.diagnostic =
                    "localized possessive foe binding is missing";
                return result;
            }
        }
        else if (slot.type == "resolved_beam")
        {
            if (!_localized_display(
                    materialized.binding.values.beam.localized,
                    language, display))
            {
                result.diagnostic = "localized beam binding is missing";
                return result;
            }
        }
        else if (slot.type == "recursive_capture")
        {
            const auto capture = find_if(
                materialized.recursive_captures.begin(),
                materialized.recursive_captures.end(),
                [&slot](const slot_value &value)
                {
                    return value.name == slot.name;
                });
            if (capture == materialized.recursive_captures.end()
                || capture->value.empty())
            {
                result.diagnostic = "recursive capture binding is missing";
                return result;
            }
            display = capture->value;
        }
        else
        {
            result.diagnostic = "unsupported typed slot binding";
            return result;
        }
        values.push_back({ slot.name, display });
    }
    const vector<line_metadata> &lines = materialized_case
        ? materialized_case->lines : variant->lines;
    return render_typed_lines(
        lines, language,
        relation,
        variant->slot_schema, values);
}

diagnostic_counters monspell_overlay_diagnostics()
{
    return current_diagnostics;
}

void reset_monspell_overlay_for_test()
{
    covered_keys.clear();
    capture_parent_leaf_keys.clear();
    active_catalog = catalog_source();
    active_catalog_loaded = false;
    current_report = load_report();
}

void reset_monspell_overlay_diagnostics_for_test()
{
    current_diagnostics = diagnostic_counters();
}
}
