bool InventoryRegion::update_tip_text(string &tip)
{
    tip = "Next page";
    tip += T_("Translated tooltip.");
    string tmp;
    tmp += "Use item";
    string tip_prefix = "Initializer prefix";
    tip += getLongDescription(db_key + " status");
    tip += tip_prefix;
    tip += tmp;
    return true;
}

void InventoryRegion::update_tab_tip_text(string &tip)
{
    tip = T_("Translated tab tooltip.");
}
