// Test: T_() calls with language-dependent literal args — should be flagged
void test_lang_dependent()
{
    mprf(T_("You offer a %sprayer to %s."), "silent ", god_name);
    mprf(T_("You offer a %sprayer to %s."), T_("silent "), god_name); // OK
}
