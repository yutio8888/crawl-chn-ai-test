// Test fixture: ALL messages have T_() wrapping — should produce no findings
void test_translated_only()
{
    mprf(T_("The %s passes through %s."), beam_name, mon_name);
    mpr(T_("You are unaffected."));
    mprf_p(T_("%s blocks the %s with %s %s... and reflects it back!"),
            mon_name, beam_name, pronoun, shield);
    mprf(T_("The bolas warps around %s and binds %s in place!"),
         name, pronoun);
}
