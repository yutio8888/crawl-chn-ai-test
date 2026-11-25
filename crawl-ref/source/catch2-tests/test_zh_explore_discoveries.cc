#include "catch_amalgamated.hpp"

#include "AppHdr.h"

// Auto-explore discovery reports (explore_discoveries::stop_explore). Chinese
// has no plural nouns and needs a measure word after an Arabic count, so the
// summary ("Found two runelights.") and merged-count ("two altars of Trog")
// paths must not fall back to English category names or number_in_words().
// The fit-on-one-line check depends on the terminal width, so the scenarios
// run in a forked child using the existing 80-column headless backend.

#if defined(UNIX) && !defined(USE_TILE)

#include <clocale>
#include <functional>
#include <string>
#include <sys/wait.h>
#include <unistd.h>
#include <vector>

#include "dungeon.h"
#include "env.h"
#include "explore-stop-options.h"
#include "item-prop.h"
#include "items.h"
#include "libutil.h"
#include "message.h"
#include "options.h"
#include "player.h"
#include "shopping.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "travel.h"
#include "unwind.h"

namespace
{
    // Places features on otherwise unseen cells away from any vault and
    // restores every touched cell, tracked-feature counters and shops.
    struct discovery_map
    {
        unwind_var<CrawlHashTable> props;
        unwind_var<map<coord_def, shop_struct>> shops;
        unwind_var<int> stop;
        vector<pair<coord_def, dungeon_feature_type>> grids;
        vector<pair<coord_def, map_cell>> cells;
        vector<pair<coord_def, unsigned int>> map_ids;

        discovery_map()
            : props(env.properties), shops(env.shop),
              stop(Options.explore_stop, ~0)
        {
        }

        ~discovery_map()
        {
            for (const auto &g : grids)
                env.grid(g.first) = g.second;
            for (const auto &c : cells)
                env.map_knowledge(c.first) = c.second;
            for (const auto &m : map_ids)
                env.level_map_ids(m.first) = m.second;
        }

        void place(const coord_def &pos, dungeon_feature_type feat)
        {
            grids.emplace_back(pos, env.grid(pos));
            cells.emplace_back(pos, env.map_knowledge(pos));
            map_ids.emplace_back(pos, env.level_map_ids(pos));
            env.level_map_ids(pos) = INVALID_MAP_INDEX;
            env.grid(pos) = feat;
            env.map_knowledge(pos).set_feature(feat);
        }
    };

    using setup_fn = function<void(explore_discoveries &, discovery_map &)>;

    // Cells far enough apart that the adjacency deduplication of runed doors
    // and transporters never merges them.
    coord_def spot(int i)
    {
        return coord_def(5 + 3 * (i % 20), 5 + 3 * (i / 20));
    }

    setup_fn features(vector<dungeon_feature_type> feats)
    {
        return [feats](explore_discoveries &ed, discovery_map &map)
        {
            for (size_t i = 0; i < feats.size(); ++i)
            {
                map.place(spot(i), feats[i]);
                ed.found_feature(spot(i), feats[i]);
            }
        };
    }

    setup_fn repeated(dungeon_feature_type feat, int n)
    {
        return features(vector<dungeon_feature_type>(n, feat));
    }

    setup_fn shops_named(const string &keeper, int n)
    {
        return [keeper, n](explore_discoveries &ed, discovery_map &map)
        {
            for (int i = 0; i < n; ++i)
            {
                shop_struct shop;
                shop.type = SHOP_GENERAL;
                shop.pos = spot(i);
                shop.shop_name = keeper;
                env.shop[spot(i)] = shop;
                map.place(spot(i), DNGN_ENTER_SHOP);
                ed.found_feature(spot(i), DNGN_ENTER_SHOP);
            }
        };
    }

    setup_fn weapons(vector<weapon_type> types)
    {
        return [types](explore_discoveries &ed, discovery_map &)
        {
            for (size_t i = 0; i < types.size(); ++i)
            {
                item_def item;
                item.base_type = OBJ_WEAPONS;
                item.sub_type = types[i];
                item.quantity = 1;
                item.pos = spot(i);
                ed.found_item(spot(i), item);
            }
        };
    }

    // Adds a stack of stackable items (darts) to the other discoveries.
    setup_fn with_darts(setup_fn others, int quantity)
    {
        return [others, quantity](explore_discoveries &ed, discovery_map &map)
        {
            others(ed, map);
            item_def darts;
            darts.base_type = OBJ_MISSILES;
            darts.sub_type = MI_DART;
            darts.quantity = quantity;
            darts.pos = spot(40);
            ed.found_item(spot(40), darts);
        };
    }

    // Runs every scenario in one forked headless child (the backend has no
    // teardown) and returns each scenario's message-log output.
    vector<string> run_discoveries(lang_t language,
                                   const vector<setup_fn> &scenarios)
    {
        int fds[2];
        REQUIRE(pipe(fds) == 0);
        const pid_t child = fork();
        REQUIRE(child >= 0);
        if (child == 0)
        {
            close(fds[0]);
            enter_headless_mode();
            // The game sets the locale in main(); system wcwidth() needs it
            // to measure CJK as double width for the fits-on-a-line check.
            if (!setlocale(LC_ALL, "C.UTF-8"))
                setlocale(LC_ALL, "en_US.UTF-8");
            TranslationFixture mode(language,
                                    language == lang_t::ZH ? "zh" : nullptr);
            init_properties();
            unwind_var<player> restore_player(you);
            string out;
            for (const setup_fn &setup : scenarios)
            {
                discovery_map map;
                explore_discoveries discoveries;
                setup(discoveries, map);
                msgwin_temporary_mode temporary;
                unwinder clear([]() { msgwin_clear_temporary(); });
                msg::tee observed;
                if (!discoveries.stop_explore())
                    out += "<no stop>";
                out += observed.get_store();
                out += '\x1e';
            }
            const char *p = out.data();
            size_t left = out.size();
            while (left)
            {
                const ssize_t w = write(fds[1], p, left);
                if (w <= 0)
                    _exit(2);
                p += w;
                left -= w;
            }
            _exit(0);
        }
        close(fds[1]);
        string out;
        char buf[4096];
        ssize_t r;
        while ((r = read(fds[0], buf, sizeof buf)) > 0)
            out.append(buf, r);
        close(fds[0]);
        int status = 0;
        REQUIRE(waitpid(child, &status, 0) == child);
        REQUIRE(WIFEXITED(status));
        REQUIRE(WEXITSTATUS(status) == 0);
        vector<string> results = split_string("\x1e", out, true, true);
        if (!results.empty() && results.back().empty())
            results.pop_back();
        for (string &s : results)
            s = trimmed_string(formatted_string::parse_string(s).tostring());
        REQUIRE(results.size() == scenarios.size());
        return results;
    }
}

struct discovery_case
{
    setup_fn setup;
    const char *zh;
    const char *en;
};

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: explore discovery counts use Arabic numerals and measure words",
                 "[zh-translation][explore-discovery]")
{
    const vector<discovery_case> cases =
    {
        // Single discoveries keep the plain name.
        {repeated(DNGN_RUNELIGHT, 1), "发现了符文之光。", "Found a runelight."},
        {repeated(DNGN_PURIFIED_MUTATION_CATALYST, 1), "发现了净化诱变催化器。",
         "Found a purified mutation catalyst."},
        // Unmerged repeats are summarised (the reported "发现了二 runelights。").
        {repeated(DNGN_RUNELIGHT, 2), "发现了2处符文之光。",
         "Found two runelights."},
        {repeated(DNGN_PURIFIED_MUTATION_CATALYST, 2),
         "发现了2个净化诱变催化器。", "Found two mutation catalysts."},
        {repeated(DNGN_TRANSPORTER, 2), "发现了2个传送器。",
         "Found two transporters."},
        {repeated(DNGN_RUNED_DOOR, 2), "发现了2扇符文门。",
         "Found two runed doors."},
        {shops_named("Zin", 2), "发现了2家商店。", "Found two shops."},
        // Merged features carry their own count.
        {repeated(DNGN_ALTAR_TROG, 2), "发现了2座特洛格的祭坛。",
         "Found two altars of Trog."},
        {repeated(DNGN_ESCAPE_HATCH_DOWN, 2), "发现了2处地板上的逃生口。",
         "Found two escape hatches in the floor."},
        {repeated(DNGN_ENTER_BAZAAR, 2), "发现了2处通往集市的传送门。",
         "Found two gateways to a bazaar."},
        // Chinese stair lists always show the count (issue #149).
        {repeated(DNGN_STONE_STAIRS_DOWN_I, 1), "发现了1处向下的石阶。",
         "Found a stone staircase leading down."},
        {repeated(DNGN_STONE_STAIRS_DOWN_I, 2), "发现了2处向下的石阶。",
         "Found two stone staircases leading down."},
        // Branch entrances shown as holes or tunnels are stairs too.
        {repeated(DNGN_ENTER_SPIDER, 1), "发现了1处通往蜘蛛巢穴的洞。",
         "Found a hole to the Spider Nest."},
        // Lists too wide for one line are summarised; Chinese counts the
        // features, including merged ones.
        {features({DNGN_ALTAR_TROG, DNGN_ALTAR_TROG, DNGN_ALTAR_ZIN,
                   DNGN_ALTAR_OKAWARU, DNGN_ALTAR_MAKHLEB, DNGN_ALTAR_SIF_MUNA,
                   DNGN_ALTAR_VEHUMET, DNGN_ALTAR_ELYVILON}),
         "发现了8座祭坛。", "Found seven altars."},
        {features({DNGN_STONE_STAIRS_DOWN_I, DNGN_STONE_STAIRS_DOWN_II,
                   DNGN_STONE_STAIRS_UP_I, DNGN_EXIT_DUNGEON, DNGN_EXIT_LAIR,
                   DNGN_EXIT_SNAKE, DNGN_EXIT_SWAMP}),
         "发现了7座楼梯。", "Found five stairs."},
        {features({DNGN_ESCAPE_HATCH_DOWN, DNGN_ESCAPE_HATCH_UP}),
         "发现了地板上的逃生口、天花板上的逃生口。",
         "Found a escape hatch in the floor and a escape hatch in the ceiling."},
        // The two clubs merge into one entry but count as two items.
        {weapons({WPN_CLUB, WPN_CLUB, WPN_WHIP, WPN_MACE, WPN_FLAIL,
                  WPN_DAGGER, WPN_LONG_SWORD, WPN_SCIMITAR, WPN_GREAT_SWORD,
                  WPN_HAND_AXE, WPN_WAR_AXE, WPN_SPEAR, WPN_HALBERD}),
         "发现了13件物品。", "Found twelve items."},
        // A stack of stackable items is listed once and counts as one item,
        // not as its stack size (5 darts here).
        {with_darts(weapons({WPN_CLUB}), 5), "发现了棍棒、5 飞镖。",
         "Found a club and 5 darts."},
        {with_darts(weapons({WPN_CLUB, WPN_WHIP, WPN_MACE, WPN_FLAIL,
                             WPN_DAGGER, WPN_LONG_SWORD, WPN_SCIMITAR,
                             WPN_GREAT_SWORD, WPN_HAND_AXE, WPN_WAR_AXE,
                             WPN_SPEAR, WPN_HALBERD}), 5),
         "发现了13件物品。", "Found thirteen items."},
        // Same-named floor items merge into one stack name.
        {weapons({WPN_CLUB, WPN_CLUB}), "发现了2 棍棒。", "Found two clubs."},
    };

    vector<setup_fn> scenarios;
    for (const discovery_case &c : cases)
        scenarios.push_back(c.setup);

    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        const vector<string> results = run_discoveries(language, scenarios);
        for (size_t i = 0; i < cases.size(); ++i)
        {
            const string expected = language == lang_t::ZH ? cases[i].zh
                                                           : cases[i].en;
            CAPTURE(i, expected);
            CHECK(results[i] == expected);
            if (language == lang_t::ZH)
            {
                // No English plural category, spelled-out number or
                // Latin-script spacing leaks into the Chinese message.
                CHECK(results[i].find("runelights") == string::npos);
                CHECK(results[i].find("mutation catalysts") == string::npos);
                CHECK(results[i].find("stair") == string::npos);
                CHECK(results[i].find("二") == string::npos);
            }
        }
    }
}

#endif
