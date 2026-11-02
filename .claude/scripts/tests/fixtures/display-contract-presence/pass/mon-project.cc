// Canonical beam names feed hit/death identities; only final sinks translate.
void _iood_hit_setup(monster& orb, bolt& beam)
{
    beam.name = N_("orb of destruction");
    if (dist < 3)
        beam.name = make_stringf("wavering %s", beam.name.c_str());
}
void _annihilation_explode_setup(monster& orb, bolt& beam)
{
    ScopedLangEn canonical_language;
    beam.name = make_stringf("annihilating %s", beam.get_short_name().c_str());
}
