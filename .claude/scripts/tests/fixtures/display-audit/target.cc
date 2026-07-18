void extended_display_sinks(const string &action)
{
    notify_fail(T_("Translated target failure."));
    yesno(("Really " + action + "?").c_str(), false, 'n');
    prompt_for_int("How many? ", true);
    set_more("Raw menu help.");
    draw_desc("Mouse description");
    title_prompt(buffer, sizeof(buffer), "Enter a value:");
    add_entry(new MenuEntry("Items", MEL_ITEM));
    game_ended(game_exit::abort, "Quit message");

    tiles.json_write_string("msg", "protocol field");
    add_entry(new MenuEntry("(%c) %s", MEL_ITEM));
    add_entry(new MenuEntry("<w> </w>", MEL_ITEM));
}

#ifdef WIZARD
void wizard_only_display()
{
    yesno("Wizard-only confirmation?", false, 'n');
}
#endif
