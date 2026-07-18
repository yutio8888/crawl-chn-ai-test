string cannot_evoke_item_reason(bool formatted, const char *item)
{
    if (formatted)
        return make_stringf("Cannot evoke %s.", item);
    if (item)
        return "Bare producer reason.";
    return T_("Translated producer reason.");
}

bool producer_call_is_not_a_definition(const char *item)
{
    if (cannot_evoke_item_reason(false, item).empty())
        return true;
    return false;
}
