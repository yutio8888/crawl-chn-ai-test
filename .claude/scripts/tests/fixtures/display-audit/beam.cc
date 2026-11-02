// Mutation of the real final display producer must still block.
string orb_beam_name_display(const string& canonical)
{
    if (canonical == "orb of destruction")
        return "orb of destruction";
    return canonical;
}
