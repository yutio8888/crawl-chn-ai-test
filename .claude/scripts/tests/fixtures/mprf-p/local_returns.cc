// Real owned local + exact-key fallback, as in the theft Note display sink.
string guarded()
{
    const string format = T_("You offer a %sprayer to %s.");
    return format == "You offer a %sprayer to %s." ? note.name
        : make_stringf_p(format.c_str(), qualifier, god_name);
}
string immediate()
{
    const std::string format = T_("You offer a %sprayer to %s.");
    return make_stringf_p(format.c_str(), qualifier, god_name);
}
string ordinary()
{
    const string format = T_("You offer a %sprayer to %s.");
    return format == "You offer a %sprayer to %s." ? note.name
        : make_stringf(format.c_str(), qualifier, god_name);
}
string unknown()
{
    const string format = T_("You offer a %sprayer to %s.");
    return unknown_formatter(format.c_str(), qualifier, god_name);
}
string reassigned()
{
    const string format = T_("You offer a %sprayer to %s.");
    format = unknown_value;
    return make_stringf_p(format.c_str(), qualifier, god_name);
}
string escaped()
{
    const string format = T_("You offer a %sprayer to %s.");
    retain(format);
    return make_stringf_p(format.c_str(), qualifier, god_name);
}
string captured()
{
    const string format = T_("You offer a %sprayer to %s.");
    auto callback = [format] { return format; };
    return make_stringf_p(format.c_str(), qualifier, god_name);
}
string escaped_argument()
{
    const string format = T_("You offer a %sprayer to %s.");
    return make_stringf_p(format.c_str(), retain(format), god_name);
}
string adjacent_unknown()
{
    mprf_p(T_("You offer a %sprayer to %s."), qualifier, god_name);
    const string format = T_("You offer a %sprayer to %s.");
    return unknown_formatter(format.c_str(), qualifier, god_name);
}
string mutable_format()
{
    string format = T_("You offer a %sprayer to %s.");
    return make_stringf_p(format.c_str(), qualifier, god_name);
}
