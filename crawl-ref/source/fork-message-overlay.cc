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
    return current_report;
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

void reset_monspell_overlay_for_test()
{
    covered_keys.clear();
    current_report = load_report();
}
}
