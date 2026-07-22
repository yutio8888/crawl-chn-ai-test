/**
 * @file
 * @brief Crawl Lua test cases
 *
 * ctest runs Lua tests found in the test directory. The intent here
 * is to test parts of Crawl that can be easily tested from within Crawl
 * itself (such as LOS). As a side-effect, writing Lua bindings to support
 * tests will expand the available Lua bindings. :-)
 *
 * Tests will run only with Crawl built in its source tree without
 * DATA_DIR_PATH set.
**/

#include "AppHdr.h"

#include "ctest.h"

#include <algorithm>
#include <vector>

#include "clua.h"
#include "cluautil.h"
#include "cloud.h"
#include "coordit.h"
#include "database.h"
#include "describe.h"
#include "dlua.h"
#include "dgn-overview.h"
#include "end.h"
#include "errors.h"
#include "files.h"
#include "fixedp.h"
#include "item-name.h"
#include "jobs.h"
#include "libutil.h"
#include "mapdef.h"
#include "maps.h"
#include "message.h"
#include "mon-pick.h"
#include "mon-place.h"
#include "mon-util.h"
#include "ng-init.h"
#include "options.h"
#include "religion.h"
#include "state.h"
#include "stringutil.h"
#include "tags.h"
#include "xom.h"

static const string test_dir = "test";
static const string script_dir = "scripts";
static const char *activity = "test";

static int ntests = 0;
static int nsuccess = 0;

typedef pair<string, string> file_error;
static vector<file_error> failures;

static void _reset_test_data()
{
    ntests = 0;
    nsuccess = 0;
    failures.clear();
    you.your_name = "Superbug99";
    you.species = SP_HUMAN;
    you.char_class = JOB_FIGHTER;
}

static int crawl_begin_test(lua_State *ls)
{
    mprf(MSGCH_PROMPT, "Starting %s: %s",
         activity,
         luaL_checkstring(ls, 1));
    lua_pushinteger(ls, ++ntests);
    return 1;
}

static int crawl_test_success(lua_State *ls)
{
    if (!crawl_state.script)
        mprf(MSGCH_PROMPT, "Test success: %s", luaL_checkstring(ls, 1));
    lua_pushinteger(ls, ++nsuccess);
    return 1;
}

static int crawl_script_args(lua_State *ls)
{
    return clua_stringtable(ls, crawl_state.script_args);
}

// Test-only deterministic injection for the three Zot orb variants.  This is
// intentionally not part of the production CLua/DLua API.
static bool zot_test_state_saved = false;
static monster_type saved_zot_orb_monster;
static bool saved_zot_orb_monster_known;
static lang_t saved_zot_language;

static int crawl_set_zot_orb_monster(lua_State *ls)
{
    const string value = luaL_checkstring(ls, 1);
    if (value == "restore")
    {
        if (!zot_test_state_saved)
            return luaL_error(ls, "Zot test state was not saved");
        you.zot_orb_monster = saved_zot_orb_monster;
        you.zot_orb_monster_known = saved_zot_orb_monster_known;
        Options.language = saved_zot_language;
        zot_test_state_saved = false;
        return 0;
    }

    if (!zot_test_state_saved)
    {
        saved_zot_orb_monster = you.zot_orb_monster;
        saved_zot_orb_monster_known = you.zot_orb_monster_known;
        saved_zot_language = Options.language;
        zot_test_state_saved = true;
    }

    monster_type type;
    if (value == "fire")
        type = MONS_ORB_OF_FIRE;
    else if (value == "winter")
        type = MONS_ORB_OF_WINTER;
    else if (value == "entropy")
        type = MONS_ORB_OF_ENTROPY;
    else
        return luaL_error(ls, "unknown Zot orb variant: %s", value.c_str());

    you.zot_orb_monster = type;
    you.zot_orb_monster_known = true;
    return 0;
}

// Test-only language switch for exercising language-stable serialized Lua
// identities in one ctest process. It is not installed in production DLua.
static int crawl_set_test_language(lua_State *ls)
{
    const string value = luaL_checkstring(ls, 1);
    if (value == "en")
        Options.language = lang_t::EN;
    else if (value == "zh")
        Options.language = lang_t::ZH;
    else
        return luaL_error(ls, "unknown test language: %s", value.c_str());
    return 0;
}

static int crawl_set_test_duration(lua_State *ls)
{
    const string value = luaL_checkstring(ls, 1);
    duration_type duration;
    if (value == "immotile")
        duration = DUR_NO_MOMENTUM;
    else if (value == "mighty")
        duration = DUR_MIGHT;
    else if (value == "slow")
        duration = DUR_SLOW;
    else
        return luaL_error(ls, "unknown test duration: %s", value.c_str());
    you.duration[duration] = luaL_optinteger(ls, 2, 20);
    return 0;
}

static int crawl_set_test_rune(lua_State *ls)
{
    const int rune = luaL_safe_checkint(ls, 1);
    if (rune < 0 || rune >= NUM_RUNE_TYPES)
        return luaL_error(ls, "unknown test rune: %d", rune);
    you.runes.set(rune, lua_toboolean(ls, 2));
    return 0;
}

static int crawl_zot_overview(lua_State *ls)
{
    lua_pushstring(ls, overview_description_string(false).c_str());
    return 1;
}

static int crawl_zot_milestone(lua_State *ls)
{
    lua_pushstring(ls, zot_orb_milestone_text().c_str());
    return 1;
}

static int crawl_test_hint_text(lua_State *ls)
{
    lua_pushstring(ls, getHintString(luaL_checkstring(ls, 1)).c_str());
    return 1;
}

static int crawl_test_speak_text(lua_State *ls)
{
    lua_pushstring(ls, getSpeakString(luaL_checkstring(ls, 1)).c_str());
    return 1;
}

static int crawl_test_long_description(lua_State *ls)
{
    lua_pushstring(ls, getLongDescription(luaL_checkstring(ls, 1)).c_str());
    return 1;
}

static int crawl_test_trap_display_name(lua_State *ls)
{
    const string value = luaL_checkstring(ls, 1);
    if (value != "permanent teleport")
        return luaL_error(ls, "unknown test trap: %s", value.c_str());
    lua_pushstring(ls, trap_name(TRAP_TELEPORT_PERMANENT).c_str());
    return 1;
}

static int crawl_test_cloud_display_name(lua_State *ls)
{
    const string value = luaL_checkstring(ls, 1);
    cloud_type type;
    if (value == "noxious fumes")
        type = CLOUD_MEPHITIC;
    else if (value == "freezing vapour")
        type = CLOUD_COLD;
    else if (value == "foul pestilence")
        type = CLOUD_MIASMA;
    else
        return luaL_error(ls, "unknown test cloud: %s", value.c_str());
    lua_pushstring(ls, cloud_type_name(type).c_str());
    return 1;
}

static bool god_test_state_saved = false;
static god_type saved_test_god;

static int crawl_set_test_god(lua_State *ls)
{
    const string value = luaL_checkstring(ls, 1);
    if (value == "restore")
    {
        if (!god_test_state_saved)
            return luaL_error(ls, "god test state was not saved");
        you.religion = saved_test_god;
        god_test_state_saved = false;
        return 0;
    }
    const god_type god = str_to_god(value);
    if (god == GOD_NO_GOD)
        return luaL_error(ls, "unknown test god: %s", value.c_str());
    if (!god_test_state_saved)
    {
        saved_test_god = you.religion;
        god_test_state_saved = true;
    }
    you.religion = god;
    return 0;
}

// Round-trip one DLua marker through its production write/read methods using
// the same lmark/file marshalling code as a save. The byte buffer is confined
// to ctest and does not create a second serialization format.
static int _roundtrip_dlua_marker(lua_State *ls, const char *class_name)
{
    luaL_checktype(ls, 1, LUA_TTABLE);

    vector<unsigned char> data;
    writer out(&data);
    lua_getglobal(ls, class_name);
    lua_getfield(ls, -1, "write");
    lua_pushvalue(ls, 1);
    lua_pushnil(ls);
    lua_pushlightuserdata(ls, &out);
    lua_call(ls, 3, 0);

    reader in(data, TAG_MINOR_VERSION);
    lua_getfield(ls, -1, "read");
    lua_pushvalue(ls, -2);
    lua_pushnil(ls);
    lua_pushlightuserdata(ls, &in);
    lua_call(ls, 3, 1);
    lua_remove(ls, -2);
    return 1;
}

static int crawl_roundtrip_dgn_triggerer(lua_State *ls)
{
    return _roundtrip_dlua_marker(ls, "DgnTriggerer");
}

static int crawl_roundtrip_trove_marker(lua_State *ls)
{
    return _roundtrip_dlua_marker(ls, "TroveMarker");
}

static int crawl_roundtrip_timed_messaging(lua_State *ls)
{
    luaL_checktype(ls, 1, LUA_TTABLE);

    vector<unsigned char> data;
    writer out(&data);
    lua_getglobal(ls, "TimedMessaging");
    lua_getfield(ls, -1, "write");
    lua_pushvalue(ls, 1);
    lua_pushlightuserdata(ls, &out);
    lua_call(ls, 2, 0);

    reader in(data, TAG_MINOR_VERSION);
    lua_getfield(ls, -1, "read");
    lua_pushvalue(ls, -2);
    lua_pushnil(ls);
    lua_pushlightuserdata(ls, &in);
    lua_call(ls, 3, 1);
    lua_remove(ls, -2);
    return 1;
}

static const struct luaL_Reg crawl_test_lib[] =
{
    { "begin_test", crawl_begin_test },
    { "test_success", crawl_test_success },
    { "script_args", crawl_script_args },
    { "set_zot_orb_monster", crawl_set_zot_orb_monster },
    { "set_test_language", crawl_set_test_language },
    { "set_test_duration", crawl_set_test_duration },
    { "set_test_rune", crawl_set_test_rune },
    { "zot_overview", crawl_zot_overview },
    { "zot_milestone", crawl_zot_milestone },
    { "test_hint_text", crawl_test_hint_text },
    { "test_speak_text", crawl_test_speak_text },
    { "test_long_description", crawl_test_long_description },
    { "test_trap_display_name", crawl_test_trap_display_name },
    { "test_cloud_display_name", crawl_test_cloud_display_name },
    { "set_test_god", crawl_set_test_god },
    { "roundtrip_dgn_triggerer", crawl_roundtrip_dgn_triggerer },
    { "roundtrip_trove_marker", crawl_roundtrip_trove_marker },
    { "roundtrip_timed_messaging", crawl_roundtrip_timed_messaging },
    { nullptr, nullptr }
};

static void _init_test_bindings()
{
    lua_stack_cleaner clean(dlua);
    if (lua_getglobal(dlua, "crawl") == LUA_TNIL) {
        lua_pop(dlua, 1);
        lua_newtable(dlua);
    }
    luaL_setfuncs(dlua, crawl_test_lib, 0);
    lua_setglobal(dlua, "crawl");
    dlua.execfile("dlua/test.lua", true, true);
    initialise_branch_depths();
    initialise_item_descriptions();
}

static bool _is_test_selected(const string &testname)
{
    if (crawl_state.test_list)
    {
        ASSERT(ends_with(testname, ".lua"));
        printf("%s\n", testname.substr(0, testname.length() - 4).c_str());
        return false;
    }

    if (crawl_state.tests_selected.empty() && !starts_with(testname, "big/"))
        return true;
    for (const string& phrase : crawl_state.tests_selected)
    {
        if (testname == phrase || testname == phrase + ".lua")
            return true;
    }
    return false;
}

static void run_test(const string &file)
{
    if (!_is_test_selected(file))
        return;

    // halt immediately if there are HUPs. TODO: interrupt tests?
    if (crawl_state.seen_hups)
        end(0);

    ++ntests;
    if (!crawl_state.script)
        fprintf(stderr, "Running test #%d: '%s'.\n", ntests, file.c_str());
    mprf(MSGCH_DIAGNOSTICS, "Running %s %d: %s",
         activity, ntests, file.c_str());
    flush_prev_message();

    // XXX: We should probably reset more things between tests
    you.position.reset();
    you.on_current_level = true;

    const string path(catpath(crawl_state.script? script_dir : test_dir, file));
    dlua.execfile(path.c_str(), true, false);
    if (dlua.error.empty())
        ++nsuccess;
    else
        failures.emplace_back(file, dlua.error);
}

#ifdef DEBUG_TESTS
static bool _has_test(const string& test)
{
    if (crawl_state.script)
        return false;
    if (crawl_state.tests_selected.empty())
        return true;
    return crawl_state.tests_selected[0].find(test) != string::npos;
}

static void _run_test(const string &name, void (*func)())
{
    // halt immediately if there are HUPs. TODO: interrupt tests?
    if (crawl_state.seen_hups)
        end(0);
    if (crawl_state.test_list)
        return (void)printf("%s\n", name.c_str());

    if (!_has_test(name))
        return;
    if (!crawl_state.script)
        fprintf(stderr, "Running test #%d: '%s'.\n", ntests, name.c_str());

    ++ntests;
    try
    {
        (*func)();
        ++nsuccess;
    }
    catch (const ext_fail_exception &E)
    {
        failures.emplace_back(name, E.what());
    }
}
#endif

// Assumes curses has already been initialized.
void run_tests()
{
    if (crawl_state.script)
        activity = "script";

    flush_prev_message();

    run_map_global_preludes();
    run_map_local_preludes();
    _reset_test_data();

    _init_test_bindings();

#ifdef DEBUG_TESTS
    if (!crawl_state.script)
    {
        _run_test("makeitem", makeitem_tests);
        _run_test("mon-pick", debug_monpick);
        _run_test("mon-data", debug_mondata);
        _run_test("mon-spell", debug_monspells);
        _run_test("coordit", coordit_tests);
        _run_test("makename", make_name_tests);
        _run_test("job-data", debug_jobdata);
        _run_test("mon-bands", debug_bands);
        _run_test("xom-data", validate_xom_events);
        _run_test("maybe-bool", maybe_bool::test_cases);
        _run_test("fixedp", fixedp<>::test_cases);
    }
#else
    ASSERT(crawl_state.script);
#endif

    // Get a list of Lua files in test.
    {
        const string &dir = crawl_state.script ? script_dir : test_dir;
        vector<string> tests = get_dir_files_recursive(dir, ".lua");

        // Make the order consistent from one run to the next, for
        // reproducibility.
        sort(begin(tests), end(tests));

        for_each(tests.begin(), tests.end(), run_test);

        if (failures.empty() && !ntests && crawl_state.script)
        {
            failures.emplace_back("Script setup",
                    "No scripts found matching "
                    + comma_separated_line(crawl_state.tests_selected.begin(),
                                           crawl_state.tests_selected.end(),
                                           ", ", ", "));
        }
    }

#ifdef DEBUG_TAG_PROFILING
    tag_profile_out();
#endif

    if (crawl_state.test_list)
        end(0);
    cio_cleanup();
    for (const file_error &fe : failures)
        fprintf(stderr, "%s error: %s\n", activity, fe.second.c_str());

    const int code = failures.empty() ? 0 : 1;
    // scripts are responsible for printing their own errors
    if (crawl_state.script && ntests == 1)
        end(code, false);
    else
    {
        end(code, false, "%d %ss, %d succeeded, %d failed",
            ntests, activity, nsuccess, (int)failures.size());
    }
}
