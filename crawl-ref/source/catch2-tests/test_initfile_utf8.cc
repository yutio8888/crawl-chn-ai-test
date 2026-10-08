#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "options.h"
#include "syscalls.h"
#include "artefact.h"
#include "database.h"
#include "files.h"
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
