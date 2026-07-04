// Test fixture: T_()-wrapped literals (should all be skipped by default)
#include <string>

void test_wrapped_literals() {
    std::string desc;
    std::ostringstream text;

    // All WRAPPED — should be SKIPPED in default mode
    desc += T_("open ");
    desc += T_("close");
    text << T_("hello");
    text << T_("You hit %s.");

    // T_() with compile-time concat
    desc += T_("long "
                "string");

    // Mixed: T_() on one arg, bare on another
    // NOTE: bare args to non-wrapper function calls are outside this scanner's
    // scope — scan_i18n.py missing-t covers mprf/mpr/cprintf/make_stringf calls.
    some_func(T_("translated"), "bare");  // "bare" NOT detected (not in concat context)

    // C_() context wrapper — also skipped
    text << C_("context", "some text");

    // N_() deferred translation — also skipped
    const char *msg = N_("deferred text");
}
