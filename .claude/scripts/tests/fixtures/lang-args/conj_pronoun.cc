// Test: conj_verb() and pronoun() in T_() context — heuristic detection
void test_conj_pronoun()
{
    mprf(T_("%s %s yanked forward by the %s."), name.c_str(), conj_verb("are").c_str(), beam_name);
    mprf(T_("%s seems less certain of %s magic."), mon_name, mon->pronoun(PRONOUN_POSSESSIVE));
}
