#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "options.h"
#include "syscalls.h"
#include "artefact.h"
#include "database.h"
#include "files.h"
#include "game-options.h"
#include "macro.h"
#include "initfile.h"
#include "invent.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "message.h"
#include "player.h"
#include "player-equip.h"
#include "randbook.h"
#include "spl-book.h"
#include "spl-util.h"
#include "stringutil.h"
#include "test_player_fixture.h"
#include "test_zh_fixture.h"
#include "unwind.h"

#include <fstream>
#include <unistd.h>

namespace
{
class temporary_options_file
{
public:
    explicit temporary_options_file(const string &contents)
        : path("catch2-options-utf8-" + std::to_string(getpid()) + "-"
               + std::to_string(next_id++) + ".txt")
    {
        FILE *file = fopen_u(path.c_str(), "wb");
        REQUIRE(file);
        REQUIRE(fwrite(contents.data(), 1, contents.size(), file)
                == contents.size());
        REQUIRE(fclose(file) == 0);
    }

    ~temporary_options_file()
    {
        unlink_u(path.c_str());
    }

    const string path;

private:
    static unsigned int next_id;
};

unsigned int temporary_options_file::next_id = 0;

void load_default_menu_colours(game_options &options)
{
    options.include_utf8(datafile_path("defaults/standard_colours.txt"),
                         false, false);
    options.include_utf8(datafile_path("defaults/menu_colours.txt"),
                         false, false);
}
}

TEST_CASE("All bundled menu colour rules parse in both languages",
          "[initfile][zh-defaults][menu-colours]")
{
    for (const auto language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture display(language, language == lang_t::ZH ? "zh" : nullptr);
        INFO("language=" << (language == lang_t::ZH ? "zh" : "en"));
        game_options options;
        const size_t builtin_count = options.menu_colour_mappings.size();
        clear_message_store();
        load_default_menu_colours(options);
        CHECK(get_last_messages(1000, true).find("Unknown color") == string::npos);

        std::ifstream file(datafile_path("defaults/menu_colours.txt"));
        REQUIRE(file.good());
        size_t rule_count = 0;
        for (string line; std::getline(file, line); )
            if (starts_with(trim_string(line), "menu +=")
                || starts_with(line, "menu_colour +="))
            {
                ++rule_count;
            }
        REQUIRE(rule_count > 0);
        REQUIRE(options.menu_colour_mappings.size() == builtin_count + rule_count);
        for (const colour_mapping &rule : options.menu_colour_mappings)
        {
            INFO(rule.pattern.tostring());
            CHECK(rule.tag != "none");
            CHECK(rule.colour >= BLACK);
            CHECK(rule.colour < NUM_TERM_COLOURS);
            CHECK(rule.pattern.valid());
        }
    }
}

TEST_CASE_METHOD(MockPlayerYouTestsFixture,
                 "Chinese inventory colours bound equipment but not book titles",
                 "[initfile][zh-defaults][menu-colours][inventory]")
{
    ZhTranslationFixture display;
    init_spell_descs();
    game_options defaults;
    load_default_menu_colours(defaults);
    unwind_var<vector<colour_mapping>> mappings(Options.menu_colour_mappings,
                                                defaults.menu_colour_mappings);
    you.religion = GOD_ASHENZARI;

    const pair<object_class_type, int> equipment[] = {
        {OBJ_WEAPONS, WPN_DAGGER}, {OBJ_ARMOUR, ARM_CHAIN_MAIL},
        {OBJ_JEWELLERY, RING_PROTECTION}, {OBJ_STAVES, STAFF_FIRE},
    };
    for (const auto &kind : equipment)
    {
        item_def &item = you.inv[0];
        item.clear();
        item.base_type = kind.first;
        item.sub_type = kind.second;
        item.quantity = 1;
        item.flags = ISFLAG_IDENTIFIED | ISFLAG_CURSED;
        item.plus = 2;
        item.slot = 'a';
        item.pos = ITEM_IN_INVENTORY;
        item.link = 0;
        INFO("class=" << item_class_name(item.base_type, true));
        InvEntry entry(item);
        REQUIRE(entry.get_text().find("束缚") != string::npos);
        CHECK(entry.highlight_colour() == RED);
        entry.select(1);
        CHECK(entry.highlight_colour() == RED);
    }

    item_def &weapon = you.inv[0];
    weapon.base_type = OBJ_WEAPONS;
    weapon.sub_type = WPN_DAGGER;
    equip_item(SLOT_WEAPON, 0, false);
    InvEntry equipped(weapon);
    REQUIRE(item_prefix(weapon, false).find("equipped") != string::npos);
    CHECK(equipped.highlight_colour() == LIGHTRED);
    unequip_item(weapon, false);

    item_def &book = you.inv[1];
    book.clear();
    book.base_type = OBJ_BOOKS;
    book.sub_type = BOOK_RANDART_THEME;
    book.quantity = 1;
    book.flags = ISFLAG_IDENTIFIED | ISFLAG_RANDART;
    book.slot = 'b';
    book.pos = ITEM_IN_INVENTORY;
    book.link = 1;
    _set_book_spell_list(book, {SPELL_MAGIC_DART});
    book.props[BOOK_TITLED_KEY].get_bool() = true;
    // A saved random title uses the ordinary artefact-name display path.
    book.props[ARTEFACT_NAME_KEY].get_string() = "束缚的魔法书";
    InvEntry title(book);
    REQUIRE(title.get_text().find("束缚的") != string::npos);
    REQUIRE(item_prefix(book, false).find("book") != string::npos);
    CHECK(title.highlight_colour() != RED);
    CHECK(title.highlight_colour() != LIGHTRED);
}

TEST_CASE("Chinese distribution defaults do not require init.txt",
          "[initfile][zh-defaults]")
{
    game_options options;

    REQUIRE(options.language == lang_t::EN);
    options.apply_distribution_defaults();
    REQUIRE(options.language == lang_t::ZH);
    REQUIRE(options.lang_name);
    REQUIRE(string(options.lang_name) == "zh");
#ifdef USE_TILE_LOCAL
    const string maple_font = "dat/tiles/MapleMono-NF-CN-Regular.ttf";
    REQUIRE(options.tile_font_crt_file == maple_font);
    REQUIRE(options.tile_font_msg_file == maple_font);
    REQUIRE(options.tile_font_stat_file == maple_font);
    REQUIRE(options.tile_font_tip_file == maple_font);
    REQUIRE(options.tile_font_lbl_file == maple_font);
    REQUIRE(options.tile_full_screen == SCREENMODE_WINDOW);
    REQUIRE(options.tile_window_width == 1280);
    REQUIRE(options.tile_window_height == 800);
    REQUIRE(options.tile_window_ratio == 0);
#endif
}

TEST_CASE("Bundled option files preserve UTF-8 without a BOM",
          "[initfile][utf8]")
{
    const temporary_options_file file(
        "menu_colour += lightblue:^unidentified .*armour.*(符文|发光)\n"
        "force_more_message += 你已达到\n"
        "note_items += 获取, 佐特\n");
    game_options options;

    options.include_utf8(file.path, false, false);

    REQUIRE(options.menu_colour_mappings.size() == 1);
    const colour_mapping &menu = options.menu_colour_mappings.front();
    REQUIRE(menu.colour == LIGHTBLUE);
    REQUIRE(menu.pattern.tostring()
            == "^unidentified .*armour.*(符文|发光)");
    REQUIRE(menu.pattern.matches("unidentified armour刻有符文的 宝珠"));

    REQUIRE(options.force_more_message.size() == 1);
    REQUIRE(options.force_more_message.front().pattern.tostring()
            == "你已达到");
    REQUIRE(options.force_more_message.front().pattern.matches(
        "你已达到经验等级 2！"));

    REQUIRE(options.note_items.size() == 2);
    REQUIRE(options.note_items[0].tostring() == "获取");
    REQUIRE(options.note_items[1].tostring() == "佐特");
}

TEST_CASE("User option includes retain the locale-aware reader",
          "[initfile][utf8]")
{
    // A UTF-8 BOM selects the existing FileLineInput UTF-8 path. This locks
    // down the public user-include entry point separately from include_utf8().
    const temporary_options_file file(
        "\xEF\xBB\xBFnote_items += 获取\n");
    game_options options;

    options.include(file.path, false, false);

    REQUIRE(options.note_items.size() == 1);
    REQUIRE(options.note_items.front().tostring() == "获取");
}

TEST_CASE("residual rereview: actual option parsing localizes errors without accepting translated values",
          "[initfile][zh-translation][residual-rereview][option-errors]")
{
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        game_options options;
        options.autopickup_on = false;
        options.basefilename = "residual-test.rc";
        options.line_num = 17;
        const GameOption *option = options.option_from_name("default_autopickup");
        REQUIRE(option);
        const bool was_loaded = option->was_loaded();
        clear_message_store();
        options.read_option_line("default_autopickup = invalid%s");
        CHECK_FALSE(options.autopickup_on);
        CHECK(option->was_loaded() == was_loaded);
        const string error = make_stringf(
            T_("Bad %s value: %s (should be true or false)"),
            "default_autopickup", "invalid%s");
        const string output = get_last_messages(10, true);
        // The message store wraps long English diagnostics across lines.
        const string unwrapped = replace_all(output, "\n", " ");
        CHECK(unwrapped.find(error) != string::npos);
        CHECK(output.find("default_autopickup") != string::npos);
        CHECK(output.find("invalid%s") != string::npos);
        CHECK(output.find("residual-test.rc:17") != string::npos);
        if (language == lang_t::ZH)
            CHECK(output.find("(should be true or false)") == string::npos);
        options.read_option_line("default_autopickup = yes");
        CHECK(options.autopickup_on);
        CHECK(option->was_loaded());
        options.read_option_line("default_autopickup = no");
        CHECK_FALSE(options.autopickup_on);

        int value = 3;
        IntGameOption integer(value, {"test_integer"}, 3, 1, 5);
        for (const char *invalid : {"not-a-number", "0", "6"})
        {
            CHECK_FALSE(integer.loadFromString(invalid, RCFILE_LINE_EQUALS).empty());
            CHECK(value == 3);
            CHECK_FALSE(integer.was_loaded());
        }
        CHECK(integer.loadFromString("4", RCFILE_LINE_EQUALS).empty());
        CHECK(value == 4);
        CHECK(integer.was_loaded());

        int choice = 0;
        const map<string, int> choices = {{"auto", 0}, {"false", 1}, {"true", 2}};
        MultipleChoiceGameOption<int> multiple(choice, {"test_choice"}, 0, choices);
        const string choices_text = comma_separated_fn(choices.begin(), choices.end(),
            [] (const pair<string, int> &entry) { return entry.first; },
            C_("rc option choices", " or "), C_("rc option choices", ", "));
        CHECK(multiple.loadFromString("invalid", RCFILE_LINE_EQUALS)
              == make_stringf(T_("Bad %s value: %s (should be %s)"),
                              "test_choice", "invalid", choices_text.c_str()));
        CHECK(choice == 0);
        CHECK_FALSE(multiple.was_loaded());
        for (const auto &entry : choices)
            CHECK(choices_text.find(entry.first) != string::npos);
        if (language == lang_t::ZH)
            CHECK(choices_text.find(" or ") == string::npos);
        CHECK(multiple.loadFromString("true", RCFILE_LINE_EQUALS).empty());
        CHECK(choice == 2);
        CHECK(multiple.was_loaded());

        DisabledGameOption disabled({"unavailable"});
        opt_parse_state state;
        state.key = "actual_disabled_alias";
        CHECK(disabled.loadFromParseState(state)
              == make_stringf(T_("Option '%s' is disabled in this build."), state.key.c_str()));
    }
}

TEST_CASE("residual rereview: option errors fall back before a language database is loaded",
          "[initfile][zh-translation][residual-rereview][option-errors]")
{
    // Same lookup state as early startup: language requested, no language DB.
    TranslationFixture translation(lang_t::ZH, nullptr);
    bool value = false;
    BoolGameOption option(value, {"test_flag"}, false);
    CHECK(option.loadFromString("invalid", RCFILE_LINE_EQUALS)
          == "Bad test_flag value: invalid (should be true or false)");
    CHECK_FALSE(value);
    CHECK_FALSE(option.was_loaded());
    CHECK(option.loadFromString("yes", RCFILE_LINE_EQUALS).empty());
    CHECK(value);
}

TEST_CASE("residual rereview: malformed rc macro diagnostics do not treat input as a format",
          "[initfile][zh-translation][residual-rereview][macro-errors]")
{
    REQUIRE_FALSE(has_pending_input());
    pause_all_key_recorders paused;
    // Observe existing keymaps through their real expansion API, without
    // editing/saving any user bindings or introducing production test hooks.
    auto keymap_outputs = []
    {
        vector<keyseq> outputs;
        for (int context = KMC_DEFAULT; context < KMC_CONTEXT_COUNT; ++context)
        {
            macro_buf_add_with_keymap({'x', 'y', '%', 's'}, KeymapContext(context));
            keyseq expanded;
            for (int key; (key = macro_buf_get()) != -1; )
                expanded.push_back(key);
            outputs.push_back(expanded);
        }
        return outputs;
    };
    const vector<keyseq> before = keymap_outputs();
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        game_options options;
        const char *inputs[] = {"M%s", "M x%s", "X%s x y"};
        const string expected[] = {
            make_stringf(T_("Cannot parse macros += %s, there is only one argument"), inputs[0]),
            make_stringf(T_("Cannot parse macros += %s, there are only two arguments"), inputs[1]),
            make_stringf(T_("'%s' is not a valid macro or keymap context (macros += %s)"),
                         "X%s", inputs[2])
        };
        for (int i = 0; i < 3; ++i)
        {
            CHECK(read_rc_file_macro(inputs[i]) == expected[i]);
            clear_message_store();
            options.read_option_line(string("macros += ") + inputs[i]);
            const string output = get_last_messages(10, true);
            CHECK(output.find(expected[i]) != string::npos);
            CHECK(output.find(inputs[i]) != string::npos);
            if (language == lang_t::ZH)
            {
                CHECK(output.find("is not a valid macro") == string::npos);
                CHECK(output.find("Cannot parse macros") == string::npos);
            }
        }
        CHECK(keymap_outputs() == before);
        CHECK_FALSE(has_pending_input());
    }
}

#ifdef USE_TILE
TEST_CASE("legacy concat: actual custom text colour parser reports the rejected key not its value",
          "[initfile][zh-translation][legacy-concat][invalid-colour-key]")
{
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        game_options options;
        clear_message_store();
        options.read_option_line("custom_text_colours = invalid_key_37:red");
        const string output = get_last_messages(10, true);
        CHECK(output.find(make_stringf(T_("Options error: Bad custom_text_colours key: '%s'"),
                                      "invalid_key_37")) != string::npos);
        CHECK(output.find("'red'") == string::npos);
        REQUIRE(options.custom_text_colours.size() == 1);
        CHECK_FALSE(options.custom_text_colours.front().valid());
        CHECK(options.custom_text_colours.front().colour_index == NUM_TERM_COLOURS);
        options.read_option_line("custom_text_colours = white:red");
        REQUIRE(options.custom_text_colours.size() == 1);
        CHECK(options.custom_text_colours.front().colour_index == WHITE);
    }
}
#endif
