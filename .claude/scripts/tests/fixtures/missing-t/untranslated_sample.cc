// Test fixture: messages WITHOUT T_() wrapping — should be flagged
void test_untranslated()
{
    mprf("%s %s healed.", name.c_str(), conj_verb("are").c_str());
    mpr("You resist.");
    mprf("The %s hits %s.", beam_name, mon_name);
}

// Test fixture: messages WITH T_() wrapping — should NOT be flagged (regression)
void test_translated()
{
    mprf(T_("The %s passes through %s."), beam_name, mon_name);
    mpr(T_("You are unaffected."));
    mprf_p(T_("%s blocks the %s with %s %s... and reflects it back!"),
            mon_name, beam_name, pronoun, shield);
}

// Debug/diagnostic messages — should be filtered
void test_debug()
{
    mprf(MSGCH_DIAGNOSTICS, "Debug: %d", value);
    mprf(MSGCH_ERROR, "Error: %s", msg);
}
