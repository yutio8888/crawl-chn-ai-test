// Test: uses mprf (not mprf_p) with T_() key that has %n$s in source.txt
void test_wrong_mprf()
{
    mprf(T_("You cannot shoot with your %s while %s."), weapon_name, status);
}
