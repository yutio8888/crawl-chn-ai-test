#include "AppHdr.h"

#include "mon-cast-message-keys.h"

namespace mon_cast_message_keys
{
namespace
{
key_expression _literal(const std::string &text)
{
    key_token token;
    token.text = text;
    key_expression expression;
    expression.tokens.push_back(token);
    return expression;
}

key_expression _beam_expression()
{
    // Keep the two spaces before "cast": the first is the trailing space in
    // " beam ", and the second is the leading space in the legacy cast_str.
    key_expression expression;
    key_token beam;
    beam.kind = key_token_kind::BEAM_SHORT_NAME;
    expression.tokens.push_back(beam);
    expression.tokens.push_back(_literal(" beam ").tokens.front());
    expression.tokens.push_back(_literal(" cast").tokens.front());
    return expression;
}

void _append(std::vector<key_expression> &keys, const std::string &key)
{
    keys.push_back(_literal(key));
}
}

casting_class normalize_casting_class(uint32_t category_bits)
{
    if (category_bits & CATEGORY_WIZARD)
        return casting_class::CLASS_WIZARD;
    if (category_bits & CATEGORY_PRIEST)
        return casting_class::CLASS_PRIEST;
    if (category_bits & CATEGORY_MAGICAL)
        return casting_class::CLASS_MAGICAL;
    if (category_bits & (CATEGORY_NATURAL | CATEGORY_VOCAL))
        return casting_class::CLASS_NATURAL;
    return casting_class::CLASS_NONE;
}

key_recipe build_key_recipe(const recipe_input &input)
{
    const std::string cast_str = " cast";
    const casting_class cast_class =
        normalize_casting_class(input.category_bits);
    const bool real_spell = cast_class == casting_class::CLASS_WIZARD
                            || cast_class == casting_class::CLASS_PRIEST;

    key_recipe result;
    std::vector<key_expression> &keys = result.candidates;

    _append(keys, input.spell_name + " " + input.monster_type + cast_str);
    _append(keys, input.spell_name + " " + input.monster_species + cast_str);
    _append(keys, input.spell_name + " " + input.monster_genus + cast_str);

    switch (cast_class)
    {
    case casting_class::CLASS_WIZARD:
        _append(keys, input.spell_name + " "
                      + (input.humanoid ? "" : "non-humanoid ")
                      + "wizard" + cast_str);
        break;
    case casting_class::CLASS_PRIEST:
        _append(keys, input.spell_name + " priest" + cast_str);
        break;
    case casting_class::CLASS_MAGICAL:
        _append(keys, input.spell_name + " magical" + cast_str);
        break;
    case casting_class::CLASS_NATURAL:
        _append(keys, input.spell_name + " natural" + cast_str);
        break;
    case casting_class::CLASS_NONE:
        break;
    }

    if (input.humanoid)
    {
        if (real_spell)
            _append(keys, input.spell_name + cast_str + " real");
        if (input.at_least_human_intelligence)
            _append(keys, input.spell_name + cast_str + " gestures");
    }

    if (input.hoarfrost_finale)
        _append(keys, input.spell_name + cast_str + " finale");

    _append(keys, input.spell_name + cast_str);

    // Only candidates appended after this point receive a targeted twin.
    const size_t num_spell_keys = keys.size();

    _append(keys, input.monster_type + cast_str);
    _append(keys, input.monster_species + cast_str);
    _append(keys, input.monster_genus + cast_str);

    switch (cast_class)
    {
    case casting_class::CLASS_WIZARD:
        _append(keys, (input.humanoid ? "" : "non-humanoid ")
                      + std::string("wizard") + cast_str);
        break;
    case casting_class::CLASS_PRIEST:
        _append(keys, "priest" + cast_str);
        break;
    case casting_class::CLASS_MAGICAL:
        _append(keys, "magical" + cast_str);
        break;
    case casting_class::CLASS_NATURAL:
    case casting_class::CLASS_NONE:
        break;
    }

    if (input.targeted)
    {
        for (size_t i = keys.size(); i-- > num_spell_keys;)
        {
            key_expression targeted = keys[i];
            targeted.tokens.push_back(_literal(" targeted").tokens.front());
            keys.insert(keys.begin() + i, targeted);
        }

        if (input.visible_beam)
        {
            keys.push_back(_beam_expression());
            _append(keys, "beam catchall cast");
        }
    }

    return result;
}

std::vector<std::string> materialize_key_recipe(
    const key_recipe &recipe, const std::string &beam_short_name)
{
    std::vector<std::string> result;
    result.reserve(recipe.candidates.size());
    for (const key_expression &expression : recipe.candidates)
    {
        std::string key;
        for (const key_token &token : expression.tokens)
        {
            if (token.kind == key_token_kind::BEAM_SHORT_NAME)
                key += beam_short_name;
            else
                key += token.text;
        }
        result.push_back(key);
    }
    return result;
}
}
