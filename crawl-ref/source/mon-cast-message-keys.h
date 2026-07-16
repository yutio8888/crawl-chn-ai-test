#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace mon_cast_message_keys
{
enum casting_category_bit : uint32_t
{
    CATEGORY_NATURAL = 1U << 0,
    CATEGORY_MAGICAL = 1U << 1,
    CATEGORY_VOCAL   = 1U << 2,
    CATEGORY_WIZARD  = 1U << 3,
    CATEGORY_PRIEST  = 1U << 4,
};

enum class casting_class
{
    CLASS_NONE,
    CLASS_WIZARD,
    CLASS_PRIEST,
    CLASS_MAGICAL,
    CLASS_NATURAL,
};

casting_class normalize_casting_class(uint32_t category_bits);

enum class key_token_kind
{
    LITERAL,
    BEAM_SHORT_NAME,
};

struct key_token
{
    key_token_kind kind = key_token_kind::LITERAL;
    std::string text;
};

struct key_expression
{
    std::vector<key_token> tokens;
};

struct key_recipe
{
    std::vector<key_expression> candidates;
};

// Owning snapshot of the runtime facts used by the legacy monspell candidate
// ordering algorithm. Name fragments are opaque owning adapter inputs;
// protocol callers must resolve them to canonical English before this seam.
struct recipe_input
{
    std::string spell_name;
    std::string monster_type;
    std::string monster_species;
    std::string monster_genus;
    uint32_t category_bits = 0;
    bool humanoid = false;
    bool at_least_human_intelligence = false;
    bool hoarfrost_finale = false;
    bool targeted = false;
    bool visible_beam = false;
};

// Pure operations: no RNG, TextDB, Lua, locale, or other global state.
key_recipe build_key_recipe(const recipe_input &input);

std::vector<std::string> materialize_key_recipe(
    const key_recipe &recipe, const std::string &beam_short_name);
}
