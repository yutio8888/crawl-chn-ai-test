// Fixture for scan_varargs_string.py — Issue #42 class UB detection.
// Each HIGH case below is a std::string temporary in a %s variadic slot.
#include "stringutil.h"

void positives()
{
    // TERNARY: both branches promoted to std::string
    make_stringf(T_("<lightred>%s%s only.</lightred>"),
                 upper ? string(T_("Uppercase")) + " " : "",
                 T_("[Y]es or [N]o"));
    // CONCAT: runtime string concatenation yields std::string temp
    mprf(MSGCH_PROMPT, "%s", some_string + " tail");
    // STRING_CTOR: explicit std::string construction
    mprf(MSGCH_PROMPT, "%s", string("x"));
    // Known std::string-returning functions are blocking.
    make_stringf("%s", god_name(god));
    make_stringf("%s", uppercase_first(word));
    make_stringf("%s", conj_verb("be", plural));
    // Positional %n$s maps to the referenced variadic argument.
    make_stringf_p("%2$d %1$s", god_name(god), count);
    mprf_p(MSGCH_PROMPT, "%2$d %1$s", god_name(god), count);
    // Sequential and positional star width arguments consume/map slots.
    make_stringf("%*s", width, god_name(god));
    make_stringf("%2$*1$s", width, god_name(god));
    make_stringf("%-10.3s", god_name(god));
    make_stringf("%.*s", precision, god_name(god));
    make_stringf("%2$.*1$s", precision, god_name(god));
    // Ambiguous same-name methods are not globally allowlisted.
    make_stringf("%s", actor.pronoun(PRONOUN_SUBJECTIVE));
}

void receiver_qualified_methods()
{
    // Same method name, but monster_info returns const char* and actor returns
    // std::string. The scanner must use the receiver's declared type.
    monster_info subject;
    make_stringf("%s", subject.pronoun(PRONOUN_SUBJECTIVE));
    {
        actor subject;
        make_stringf("%s", subject.pronoun(PRONOUN_SUBJECTIVE));
    }
    // The outer safe binding must become visible again after the inner scope.
    make_stringf("%s", subject.pronoun(PRONOUN_SUBJECTIVE));

    attacked_monster_list victims;
    LookupType lookup;
    make_stringf("%s", victims.suffix());
    make_stringf("%s", lookup.suffix());

    // Without an explicit receiver type, preserve the advisory WARN.
    make_stringf("%s", unresolved.what());
}

void other_receiver_qualified_methods(map_load_exception &error)
{
    scorefile_entry score;
    mon_enchant enchant;
    make_stringf("%s", error.what());
    make_stringf("%s", score.damage_verb());
    make_stringf("%s", enchant.kill_category_desc(KC_YOU));
}

const char* EquipOnDelay::safe_receiver_method()
{
    return make_stringf("%s", get_verb());
}

string AuxKick::unsafe_receiver_method()
{
    return make_stringf("%s", get_verb());
}

void negatives()
{
    // Safe: .c_str() on the temporary
    make_stringf(T_("An illusion of %s"), get_ghost_description(mi).c_str());
    // Safe: T_() returns const char*
    mprf(MSGCH_PROMPT, "%s", T_("safe"));
    // Safe: integer/char arithmetic, not string concatenation
    make_stringf("%d", date->tm_year + 1900);
    mprf(MSGCH_PROMPT, "%c", i + '0');
    // Safe: no %s in format
    mprf(MSGCH_PROMPT, "%d", count);
    // Safe: positional mapping only classifies the %s-referenced slot.
    make_stringf("%2$s %1$d", returns_int(), T_("safe"));
    make_stringf("%1$d %2$s", returns_int(), T_("safe"));
    // Safe: C_ context is not part of the format string.
    make_stringf(C_("context with %s", "%d"), returns_int());
    // Safe: escaped percent consumes no argument.
    make_stringf("%% %s", T_("safe"));
    make_stringf("100%%", god_name(god));
    // Safe: known string returners are converted explicitly.
    make_stringf("%s", god_name(god).c_str());
    make_stringf("%s", uppercase_first(word).c_str());
    make_stringf("%s", conj_verb("be", plural).c_str());
}
