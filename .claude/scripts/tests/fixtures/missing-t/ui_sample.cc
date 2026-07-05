// Test fixture: cprintf + formatted_string + make_stringf without T_()
void test_ui_calls()
{
    cprintf("CTRL");
    cprintf("Abil: ");
    formatted_string("Press %s to continue", key);
    string s = make_stringf("Level %d", n);
}

// Already translated — should NOT be flagged
void test_ui_translated()
{
    cprintf(T_("Skill"));
    formatted_string(T_("Press %s to continue"), key);
    string s = make_stringf(T_("Level %d"), n);
}
