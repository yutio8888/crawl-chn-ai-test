#include "AppHdr.h"

#include "monspell_candidate_artifact.h"

#include "fork-message-overlay.h"
#include "mon-util.h"
#include "spl-util.h"
#include "stringutil.h"
#include "syscalls.h"

#include <fstream>
#include <map>
#include <set>
#include <sstream>
#include <tuple>
#include <unistd.h>

namespace mon_cast_candidate_dump
{
namespace
{
namespace fmo = fork_message_overlay;
namespace mcmk = mon_cast_message_keys;
const char RESERVED_BEAM_MARKER[] = "${beam_short_name}";

std::string _json_string(const std::string &value)
{
    static const char hex[] = "0123456789abcdef";
    std::string result = "\"";
    for (const unsigned char c : value)
    {
        switch (c)
        {
        case '"': result += "\\\""; break;
        case '\\': result += "\\\\"; break;
        case '\b': result += "\\b"; break;
        case '\f': result += "\\f"; break;
        case '\n': result += "\\n"; break;
        case '\r': result += "\\r"; break;
        case '\t': result += "\\t"; break;
        default:
            if (c < 0x20)
            {
                result += "\\u00";
                result += hex[c >> 4];
                result += hex[c & 0x0f];
            }
            else
                result += static_cast<char>(c);
        }
    }
    return result + '"';
}

std::string _attempt_name(fmo::message_prefix prefix,
                          fmo::message_attempt attempt)
{
    if (attempt == fmo::message_attempt::SILENT_PREFIXED)
        return "silent_prefixed";
    if (attempt == fmo::message_attempt::SILENT_UNPREFIXED_FALLBACK)
        return "silent_unprefixed_fallback";
    return prefix == fmo::message_prefix::UNSEEN ? "unseen" : "normal";
}

void _record_lookup_attempts(
    const std::string &base,
    std::map<std::string, std::set<std::string>> &lookups)
{
    for (const fmo::message_prefix prefix :
         { fmo::message_prefix::NORMAL, fmo::message_prefix::UNSEEN,
           fmo::message_prefix::SILENT })
    {
        const fmo::message_candidate_search search =
            fmo::search_message_candidate(
                base, prefix,
                [prefix, &lookups](const fmo::message_lookup_request &request)
                {
                    std::string canonical_key = request.lookup_key;
                    lowercase(canonical_key);
                    lookups[canonical_key].insert(
                        _attempt_name(prefix, request.attempt));
                    fmo::message_lookup_result missing;
                    missing.result = fmo::message_result::MISSING;
                    return missing;
                });
        UNUSED(search);
    }
}

bool _contains_reserved_marker(const std::string &value)
{
    std::string canonical = value;
    lowercase(canonical);
    return canonical.find(RESERVED_BEAM_MARKER) != std::string::npos;
}

mcmk::recipe_input _recipe_input(const monster_fragments &monster,
                                 const std::string &spell,
                                 const scenario &scenario)
{
    mcmk::recipe_input input;
    input.spell_name = spell;
    input.monster_type = monster.type;
    input.monster_species = monster.species;
    input.monster_genus = monster.genus;
    input.category_bits = scenario.category_bits;
    input.humanoid = scenario.humanoid;
    input.at_least_human_intelligence =
        scenario.at_least_human_intelligence;
    input.hoarfrost_finale = scenario.hoarfrost_finale;
    input.targeted = scenario.targeted;
    input.visible_beam = scenario.visible_beam;
    return input;
}
}

bool monster_fragments::operator<(const monster_fragments &other) const
{
    return std::tie(type, species, genus)
           < std::tie(other.type, other.species, other.genus);
}

std::vector<scenario> scenario_cover()
{
    const uint32_t classes[] = {
        0,
        mcmk::CATEGORY_WIZARD,
        mcmk::CATEGORY_PRIEST,
        mcmk::CATEGORY_MAGICAL,
        mcmk::CATEGORY_NATURAL,
    };
    const char *ids[] = {
        "none_humanoid_maximal",
        "wizard_humanoid_maximal",
        "priest_humanoid_maximal",
        "magical_humanoid_maximal",
        "natural_humanoid_maximal",
    };

    std::vector<scenario> result;
    for (size_t i = 0; i < ARRAYSZ(classes); ++i)
    {
        scenario item;
        item.id = ids[i];
        item.category_bits = classes[i];
        item.humanoid = true;
        item.at_least_human_intelligence = true;
        item.hoarfrost_finale = true;
        item.targeted = true;
        item.visible_beam = true;
        result.push_back(item);
    }

    scenario non_humanoid_wizard = result[1];
    non_humanoid_wizard.id = "wizard_non_humanoid_maximal";
    non_humanoid_wizard.humanoid = false;
    result.push_back(non_humanoid_wizard);
    return result;
}

std::string symbolic_expression(const mcmk::key_expression &expression)
{
    std::string result;
    for (const mcmk::key_token &token : expression.tokens)
    {
        result += token.kind == mcmk::key_token_kind::BEAM_SHORT_NAME
                  ? RESERVED_BEAM_MARKER : token.text;
    }
    return result;
}

candidate_dump build_candidate_dump(
    const std::vector<monster_fragments> &monster_domain,
    const std::vector<std::string> &spell_domain,
    size_t monster_type_count)
{
    candidate_dump dump;
    dump.monster_type_count = monster_type_count;
    dump.spell_count = spell_domain.size();
    dump.monster_tuple_count = monster_domain.size();
    dump.monster_spell_tuple_count = monster_domain.size()
                                     * spell_domain.size();
    dump.scenarios = scenario_cover();
    dump.scenario_count = dump.scenarios.size();

    for (const monster_fragments &monster : monster_domain)
    {
        if (_contains_reserved_marker(monster.type)
            || _contains_reserved_marker(monster.species)
            || _contains_reserved_marker(monster.genus))
        {
            dump.valid = false;
            dump.diagnostic =
                "monster fragment collides with reserved beam marker";
            return dump;
        }
    }
    for (const std::string &spell : spell_domain)
    {
        if (_contains_reserved_marker(spell))
        {
            dump.valid = false;
            dump.diagnostic =
                "spell fragment collides with reserved beam marker";
            return dump;
        }
    }

    std::set<std::string> bases;
    for (const monster_fragments &monster : monster_domain)
    {
        for (const std::string &spell : spell_domain)
        {
            for (const scenario &scenario : dump.scenarios)
            {
                const mcmk::key_recipe recipe = mcmk::build_key_recipe(
                    _recipe_input(monster, spell, scenario));
                for (const mcmk::key_expression &expression :
                     recipe.candidates)
                {
                    bases.insert(symbolic_expression(expression));
                }
            }
        }
    }
    dump.base_expressions.assign(bases.begin(), bases.end());
    dump.base_expression_count = dump.base_expressions.size();

    std::map<std::string, std::set<std::string>> lookup_map;
    for (const std::string &base : dump.base_expressions)
        _record_lookup_attempts(base, lookup_map);
    for (const auto &item : lookup_map)
    {
        lookup_expression expression;
        expression.expression = item.first;
        expression.attempts.assign(item.second.begin(), item.second.end());
        dump.lookup_attempt_count += expression.attempts.size();
        dump.lookup_expressions.push_back(expression);
    }
    dump.lookup_expression_count = dump.lookup_expressions.size();
    return dump;
}

candidate_dump build_production_candidate_dump()
{
    std::set<monster_fragments> unique_monsters;
    size_t monster_type_count = 0;
    for (int value = 0; value < NUM_MONSTERS; ++value)
    {
        const monster_type type = static_cast<monster_type>(value);
        if (!get_monster_data(type))
            continue;
        ++monster_type_count;
        unique_monsters.insert({
            remove_prepended_the(mons_type_name_en(type, DESC_DBNAME)),
            remove_prepended_the(
                mons_type_name_en(mons_species(type), DESC_DBNAME)),
            remove_prepended_the(
                mons_type_name_en(mons_genus(type), DESC_DBNAME)),
        });
    }

    std::vector<std::string> spells;
    for (int value = 0; value < NUM_SPELLS; ++value)
    {
        const spell_type spell = static_cast<spell_type>(value);
        if (is_valid_spell(spell))
            spells.push_back(spell_english_name(spell));
    }
    std::sort(spells.begin(), spells.end());
    spells.erase(std::unique(spells.begin(), spells.end()), spells.end());

    return build_candidate_dump(
        std::vector<monster_fragments>(unique_monsters.begin(),
                                       unique_monsters.end()),
        spells, monster_type_count);
}

std::string serialize_candidate_dump(const candidate_dump &dump)
{
    std::ostringstream out;
    out << "{\"schema_version\":" << dump.schema_version
        << ",\"domain\":\"monspell_candidate_lookup\""
        << ",\"completeness\":" << _json_string(dump.completeness)
        << ",\"valid\":" << (dump.valid ? "true" : "false")
        << ",\"diagnostic\":"
        << (dump.diagnostic.empty() ? "null" : _json_string(dump.diagnostic))
        << ",\"input_domain\":{"
        << "\"monster_types\":\"integer range [0,NUM_MONSTERS) with "
           "get_monster_data(type) != nullptr\","
        << "\"monster_fragments\":\"unique canonical-English "
           "type/species/genus tuples\","
        << "\"spells\":\"all is_valid_spell(spell) values in "
           "[0,NUM_SPELLS), deduplicated by spell_english_name\","
        << "\"scenarios\":\"finite branch cover proven exhaustive over "
           "32 category masks and all recipe booleans\","
        << "\"beam_short_name\":\"symbolic ${beam_short_name}; runtime "
           "materialization excluded\","
        << "\"lookup_state_machine\":\"search_message_candidate recorder, "
           "then production lowercase canonicalization, "
           "for normal, unseen, silent-prefixed and silent-unprefixed "
           "fallback\"}"
        << ",\"counts\":{"
        << "\"monster_types\":" << dump.monster_type_count
        << ",\"spells\":" << dump.spell_count
        << ",\"monster_tuples\":" << dump.monster_tuple_count
        << ",\"monster_spell_tuples\":"
        << dump.monster_spell_tuple_count
        << ",\"scenarios\":" << dump.scenario_count
        << ",\"base_expressions\":" << dump.base_expression_count
        << ",\"lookup_expressions\":" << dump.lookup_expression_count
        << ",\"lookup_attempts\":" << dump.lookup_attempt_count << "}"
        << ",\"scenarios\":[";
    for (size_t i = 0; i < dump.scenarios.size(); ++i)
    {
        if (i)
            out << ',';
        const scenario &item = dump.scenarios[i];
        out << "{\"id\":" << _json_string(item.id)
            << ",\"category_bits\":" << item.category_bits
            << ",\"humanoid\":" << (item.humanoid ? "true" : "false")
            << ",\"at_least_human_intelligence\":"
            << (item.at_least_human_intelligence ? "true" : "false")
            << ",\"hoarfrost_finale\":"
            << (item.hoarfrost_finale ? "true" : "false")
            << ",\"targeted\":" << (item.targeted ? "true" : "false")
            << ",\"visible_beam\":"
            << (item.visible_beam ? "true" : "false") << '}';
    }
    out << "],\"base_expressions\":[";
    for (size_t i = 0; i < dump.base_expressions.size(); ++i)
    {
        if (i)
            out << ',';
        out << _json_string(dump.base_expressions[i]);
    }
    out << "],\"lookup_expressions\":[";
    for (size_t i = 0; i < dump.lookup_expressions.size(); ++i)
    {
        if (i)
            out << ',';
        const lookup_expression &item = dump.lookup_expressions[i];
        out << "{\"expression\":" << _json_string(item.expression)
            << ",\"attempts\":[";
        for (size_t j = 0; j < item.attempts.size(); ++j)
        {
            if (j)
                out << ',';
            out << _json_string(item.attempts[j]);
        }
        out << "]}";
    }
    out << "]}\n";
    return out.str();
}

bool write_candidate_dump_atomic(const candidate_dump &dump,
                                 const std::string &path,
                                 std::string &error)
{
    const std::string temporary = path + ".tmp." + std::to_string(getpid());
    {
        std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
        if (!output)
        {
            error = "cannot open temporary artifact: " + temporary;
            return false;
        }
        const std::string bytes = serialize_candidate_dump(dump);
        output.write(bytes.data(), bytes.size());
        output.close();
        if (!output)
        {
            error = "cannot write temporary artifact: " + temporary;
            unlink_u(temporary.c_str());
            return false;
        }
    }
    if (rename_u(temporary.c_str(), path.c_str()) != 0)
    {
        error = "cannot rename artifact into place: " + path;
        unlink_u(temporary.c_str());
        return false;
    }
    return true;
}
}
