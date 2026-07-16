#pragma once

#include "mon-cast-message-keys.h"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace mon_cast_candidate_dump
{
struct monster_fragments
{
    std::string type;
    std::string species;
    std::string genus;

    bool operator<(const monster_fragments &other) const;
};

struct scenario
{
    std::string id;
    uint32_t category_bits = 0;
    bool humanoid = false;
    bool at_least_human_intelligence = false;
    bool hoarfrost_finale = false;
    bool targeted = false;
    bool visible_beam = false;
};

struct lookup_expression
{
    std::string expression;
    std::vector<std::string> attempts;
};

struct candidate_dump
{
    int schema_version = 1;
    std::string completeness = "closed_world_upper_bound";
    bool valid = true;
    std::string diagnostic;
    size_t monster_type_count = 0;
    size_t spell_count = 0;
    size_t monster_tuple_count = 0;
    size_t monster_spell_tuple_count = 0;
    size_t scenario_count = 0;
    size_t base_expression_count = 0;
    size_t lookup_expression_count = 0;
    size_t lookup_attempt_count = 0;
    std::vector<scenario> scenarios;
    std::vector<std::string> base_expressions;
    std::vector<lookup_expression> lookup_expressions;
};

std::vector<scenario> scenario_cover();

std::string symbolic_expression(
    const mon_cast_message_keys::key_expression &expression);

candidate_dump build_candidate_dump(
    const std::vector<monster_fragments> &monster_domain,
    const std::vector<std::string> &spell_domain,
    size_t monster_type_count);

// Requires the normal monster and spell data initialisation performed by the
// game or the dump test fixture.
candidate_dump build_production_candidate_dump();

std::string serialize_candidate_dump(const candidate_dump &dump);
bool write_candidate_dump_atomic(const candidate_dump &dump,
                                 const std::string &path,
                                 std::string &error);
}
