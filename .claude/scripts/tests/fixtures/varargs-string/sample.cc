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
}
