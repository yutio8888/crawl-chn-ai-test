// Direct display literals require an explicit translation wrapper.
void direct_display_contracts(const char *message)
{
    simple_god_message(" bare direct message");
    god_speaks(GOD_XOM, "Bare divine speech.");
    simple_god_message(("Parenthesized raw."));
    simple_god_message(make_stringf("Nested raw %s.", message));
    simple_god_message("Adjacent "
                       "multiline raw.");
    notify_fail("Bare target failure.");
    notify_fail(N_("Deferred marker is not translated."));

    simple_god_message(T_(" translated direct message"));
    notify_fail(T_("Translated target failure."));
    god_speaks(GOD_XOM, C_("speech", "Translated divine speech."));
    simple_god_message(make_stringf(T_("Translated nested %s."), message));

    // Variables and DB-backed providers are already translated upstream.
    simple_god_message(message);
    god_speaks(GOD_XOM, _get_xom_speech("database lookup key").c_str());
    // simple_god_message("commented-out message");
    simple_god_message(/* translated upstream */ message);
}

// This wrapper calls T_(variable) internally: literals are keys, not direct
// display strings, and must have exact non-empty source.txt coverage.
void dynamic_key_contracts()
{
    xom_is_stimulated(100, "Covered dynamic message.", true);
    xom_is_stimulated(100, "Missing dynamic message.", true);
    xom_is_stimulated(100, "Empty dynamic message.", true);
    xom_is_stimulated(100, "case dynamic message.", true);
    xom_is_stimulated(100, ("Adjacent " "dynamic message."), true);
    xom_is_stimulated(100, XM_INTRIGUED, true);
}
