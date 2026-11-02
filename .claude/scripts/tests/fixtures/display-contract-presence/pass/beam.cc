// The actual final display producer remains a blocking literal contract.
string orb_beam_name_display(const string& canonical)
{
    if (canonical == "orb of destruction")
        return T_("orb of destruction");
    return canonical;
}
