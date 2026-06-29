// Test: make_stringf_p + vmake_stringf_p are correctly recognized
void test_make_stringf_p()
{
    // Uses make_stringf_p with a key that has %n$s in source.txt → should NOT be flagged
    string msg = make_stringf_p(T_("You cannot shoot with your %s while %s."),
                                weapon_name, held_status());
    // Uses mprf_p → should NOT be flagged
    mprf_p(T_("You offer a %sprayer to %s."), qualifier, god_name);
}
