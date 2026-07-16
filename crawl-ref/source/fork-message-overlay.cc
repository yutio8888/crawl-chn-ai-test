#include "AppHdr.h"

#include "fork-message-overlay.h"

#include "database.h"
#include "stringutil.h"

#include <algorithm>
#include <iomanip>
#include <map>
#include <set>
#include <sstream>

namespace fork_message_overlay
{
namespace
{
load_report current_report;
set<string> covered_keys;
diagnostic_counters current_diagnostics;

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

bool _same_strings(vector<string> lhs, vector<string> rhs)
{
    sort(lhs.begin(), lhs.end());
    sort(rhs.begin(), rhs.end());
    return lhs == rhs;
}

bool _validate_lines(const catalog_source &source,
                     const catalog_variant &variant, string &error)
{
    set<string> declared;
    for (const slot_definition &slot : variant.slot_schema)
    {
        if (!_valid_identifier(slot.name) || slot.type.empty()
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

    if (variant.policy == materialization_policy::LEGACY_ONLY)
    {
        if (!variant.lines.empty() || !variant.materialization_cases.empty())
        {
            error = "legacy-only variant contains renderable data";
            return false;
        }
        return true;
    }
    if (variant.lines.empty())
    {
        error = "structured variant has no line metadata";
        return false;
    }

    static const set<string> relations = { "AT", "NEXT_TO", "PAST" };
    set<string> used_slots;
    for (const line_metadata &line : variant.lines)
    {
        set<pair<string, string>> language_relations;
        for (const localized_template &localized : line.templates)
        {
            if (localized.pattern.empty()
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
    for (const catalog_entry &entry : generated_monspell_catalog().entries)
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
            // CASE_MAP and CAPTURE_SLOT remain deliberately unavailable in
            // Stage 3. A dynamic signature cannot silently select NONE.
            return nullptr;
        }
    }
    return nullptr;
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

            const vector<string> dependencies = _recursive_dependencies(
                actual_variant.raw_pattern, canonical);
            if (!_same_strings(dependencies,
                               variant.recursive_dependencies)
                || variant.recursive_dependencies.size()
                   != variant.recursive_dependency_fingerprints.size())
            {
                return _disable(load_failure::CLOSURE_INCOMPLETE,
                                "recursive closure declaration is incomplete");
            }
            if (entry.mode == entry_mode::CANDIDATE)
            {
                for (const string &dependency : dependencies)
                {
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
            if (variant.policy == materialization_policy::CASE_MAP
                || variant.policy == materialization_policy::CAPTURE_SLOT)
            {
                return _disable(load_failure::CORRUPT,
                                "materialization policy is not enabled yet");
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

            string line_error;
            if (!_validate_lines(*source, variant, line_error))
                return _disable(load_failure::CORRUPT, line_error);
        }
    }

    for (const auto &item : catalog_entries)
    {
        if (item.second->mode == entry_mode::CANDIDATE)
            covered_keys.insert(item.first);
    }
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

route_decision route_monspell_message(const string &canonical_key)
{
    route_decision decision;
    decision.canonical_key = canonical_key;
    lowercase(decision.canonical_key);
    if (monspell_overlay_covers(decision.canonical_key))
    {
        decision.route = message_route::STRUCTURED;
        ++current_diagnostics.overlay_hit;
    }
    else
        ++current_diagnostics.legacy_fallback;
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
    return materialize_monspell_candidate(
        canonical_key, attempt, manifest_applicable, bindings,
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
    if (result.canonical.expanded_pattern_en.empty()
        || (!accepts_any && !manifest_applicable))
    {
        result.result = message_result::INAPPLICABLE;
        return result;
    }
    if (!bindings)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "runtime binding resolver is missing";
        return result;
    }

    result.binding.rng.before = canonical_textdb::observe_rng();
    result.binding.values = bindings();
    result.binding.rng.after = canonical_textdb::observe_rng();
    result.binding.callback_count = 1;
    const runtime_bindings &resolved = result.binding.values;
    if (resolved.actor.sentence_en.empty()
        || resolved.actor.canonical_en.empty()
        || resolved.target.relation == target_relation::NONE
        || !_valid_target_payload(resolved.target)
        || resolved.target.relation_en.empty()
        || resolved.target.canonical_en.empty()
        || resolved.beam.canonical_en.empty())
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "runtime bindings are incomplete";
        return result;
    }

    result.bound_pattern_en = replace_all(
        result.canonical.expanded_pattern_en, "@The_monster@",
        resolved.actor.sentence_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@the_monster@",
        resolved.actor.canonical_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@at@", resolved.target.relation_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@target@", resolved.target.canonical_en);
    result.bound_pattern_en = replace_all(
        result.bound_pattern_en, "@beam@", resolved.beam.canonical_en);

    result.randomized = canonical_textdb::materialize_bound_legacy_randomness(
        result.canonical, result.bound_pattern_en);
    if (result.randomized.status
        != canonical_textdb::candidate_status::SELECTED)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = result.randomized.error;
        return result;
    }
    if (result.randomized.signature != "NONE"
        || result.randomized.random_site_count != 0
        || result.randomized.pattern_en != result.bound_pattern_en
        || result.canonical.lua_site_count != 0
        || result.canonical.selected_variants.size() != 1
        || result.canonical.expanded_pattern_en.find('[') != string::npos)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "NONE policy observed dynamic materialization";
        return result;
    }

    const catalog_variant *variant = _find_catalog_variant(
        result.canonical.top_locator.canonical_key,
        result.canonical.top_locator.variant_ordinal,
        result.randomized.signature);
    if (!variant || variant->frame != resolved.cast.frame)
    {
        result.result = message_result::CORRUPT;
        result.diagnostic = "canonical locator has no matching catalog case";
        return result;
    }
    result.stable_id = variant->stable_id;
    result.materialization_signature = result.randomized.signature;
    result.result = message_result::RENDERED;
    return result;
}

render_result render_typed_template(
    const string &pattern, const vector<slot_definition> &declarations,
    const vector<slot_value> &values)
{
    render_result result;
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
    set<string> used;
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
        used.insert(name);
        rendered += supplied[name];
        position = end + 1;
    }
    if (used.size() != declared.size())
    {
        result.diagnostic = "declared slot is unused";
        return result;
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
    if (relation_name == "NONE")
    {
        result.diagnostic = "target relation has no render template";
        return result;
    }
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
    const catalog_variant *variant = _find_catalog_variant(
        materialized.canonical.top_locator.canonical_key,
        materialized.canonical.top_locator.variant_ordinal,
        materialized.materialization_signature);
    if (!variant || variant->stable_id != materialized.stable_id)
    {
        result.diagnostic = "materialized stable ID is not in the catalog";
        return result;
    }
    string actor;
    string target;
    string beam;
    if (!_localized_display(materialized.binding.values.actor.localized,
                            language, actor)
        || !_localized_display(materialized.binding.values.target.localized,
                               language, target)
        || !_localized_display(materialized.binding.values.beam.localized,
                               language, beam))
    {
        result.diagnostic = "localized runtime binding is missing";
        return result;
    }
    const vector<slot_value> values =
    {
        { "actor", actor }, { "target", target }, { "beam", beam },
    };
    return render_typed_lines(
        variant->lines, language,
        materialized.binding.values.target.relation,
        variant->slot_schema, values);
}

diagnostic_counters monspell_overlay_diagnostics()
{
    return current_diagnostics;
}

void reset_monspell_overlay_for_test()
{
    covered_keys.clear();
    current_report = load_report();
}

void reset_monspell_overlay_diagnostics_for_test()
{
    current_diagnostics = diagnostic_counters();
}
}
