#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "options.h"
#include "syscalls.h"

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
