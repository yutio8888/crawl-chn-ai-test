// Test: correctly uses mprf_p with T_() key that has %n$s in source.txt
void test_correct_mprf_p()
{
    mprf_p(T_("You offer a %sprayer to %s."), qualifier, god_name);
}
