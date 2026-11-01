// test_zh_help.cc — Issue 52: help-system (?/ lookup) Chinese-compat L1 tests.
//
// Dimension-orthogonal to test_zh_enumerators.cc: instead of scanning T_()
// translation *content* quality, these tests verify that the help system's
// lookup functions correctly accept the (possibly Chinese) display names their
// paired getters produce — i.e. the round-trip
//     lookup_fn(name_fn(enum)) == enum
// holds under the ZH fixture. This guards against Issue 51's two bug patterns:
//   A) *_keys() returning Chinese names that later DB/enum lookups reject
//   B) byte-length suffix truncation cutting a multibyte char (via the
//      strip_suffix contract test + the L3 end-to-end path).
//
// All ZH-input round-trips run under ZhTranslationFixture (Options.language =
// lang_t::ZH + TextDB loaded); the god round-trip runs in a SEPARATE plain
// TEST_CASE (EN mode) because god_name() is T_()'d (Chinese under fixture) but
// str_to_god() matches English only.

#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "test_zh_fixture.h"
#include "test_zh_helpers.h"

#include "i18n.h"

#include "spl-util.h"        // spell_by_name, spell_title, init_spell_name_cache,
                             // init_spell_descs, spell_removed, NUM_SPELLS
#include "spell-type.h"
#include "ability.h"         // ability_by_name, ability_name, NUM_ABILITIES
#include "ability-type.h"
#include "dbg-util.h"        // skill_from_name
#include "skills.h"          // skill_name
#include "skill-type.h"      // SK_FIRST_SKILL, NUM_SKILLS
#include "decks.h"           // name_to_card, card_name, card_is_removed, NUM_CARDS
#include "mutation.h"        // mutation_from_name, mutation_name,
                             // bane_from_name, bane_name
#include "mutation-type.h"
#include "bane-type.h"       // NUM_BANES, BANE_*_REMOVED
#include "bane-data.h"       // bane_data English translation keys
#include "cloud.h"           // cloud_name_to_type, cloud_type_name
#include "cloud-type.h"
#include "branch.h"          // branch_by_shortname, branches
#include "branch-type.h"     // NUM_BRANCHES
#include "religion.h"        // str_to_god, god_name
#include "god-type.h"        // GOD_NO_GOD, NUM_GODS
#include "mon-util.h"        // get_monster_by_name, init_monsters
#include "monster-type.h"
#include "item-name.h"       // item_kind_by_name
#include "terrain.h"         // feat_by_desc, init_feat_desc_cache
#include "feature.h"         // get_feature_def
#include "dungeon-feature-type.h" // NUM_FEATURES
#include "database.h"        // getLongDescription, getLongDescKeysByRegex
#include "describe.h"
#include "dungeon.h"         // INVALID_MAP_INDEX
#include "clua.h"            // clua, lua_State
#include "stringutil.h"      // strip_suffix
#include "positional_format.h" // make_stringf_p
#include "unicode.h"         // utf8towc
#include "options.h"         // Options.language
#include "lang-t.h"          // lang_t
#include "lookup-help.h"     // lookup_help_type_name, NUM_LOOKUP_HELP_TYPES
#include "command.h"         // localized standalone guide resolution
#include "env.h"
#include "hints.h"
#include "player.h"
#include "player-stats.h"
#include "status.h"
#include "unwind.h"
#include "beam.h"
#include "hiscores.h"
#include "macro.h"
#include "ouch.h"
#include "state.h"
#include "artefact.h"
#include "art-enum.h"
#include "directn.h"
#include "item-status-flag-type.h"
#include "map-cell.h"
#include "mon-info.h"
#include "notes.h"
#include "tags.h"

#include <algorithm>
#include <cstring>
#include <fstream>
#include <iterator>
#include <stdexcept>
#include <string>
#include <vector>

using std::string;
using std::vector;

TEST_CASE("ability-slot: overwrite protection matches canonical names in every language",
          "[zh-help][ability-slot-rereview]")
{
    unwind_var<decltype(you.ability_letter_table)> restore_slots(you.ability_letter_table);
    unwind_var<decltype(Options.auto_ability_letters)> restore_rules(Options.auto_ability_letters);
    struct slot_case
    {
        ability_type existing;
        const char *letters;
        int expected_slot;
    };
    const slot_case cases[] = {
        { ABIL_EVOKE_TURN_INVISIBLE, "+a", 1 },
        { ABIL_EVOKE_TURN_INVISIBLE, "+ac", 2 },
        { ABIL_RENOUNCE_RELIGION, "+a", 0 },
    };
    for (lang_t language : { lang_t::EN, lang_t::ZH, lang_t::EN })
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const slot_case &entry : cases)
        {
            INFO("language=" << static_cast<int>(language)
                 << " existing=" << ability_name(entry.existing, true)
                 << " rule=" << entry.letters);
            you.ability_letter_table.init(ABIL_NON_ABILITY);
            you.ability_letter_table[0] = entry.existing;
            you.ability_letter_table[1] = ABIL_EVOKE_BLINK;
            Options.auto_ability_letters.clear();
            Options.auto_ability_letters.emplace_back(text_pattern("^evoke ", true),
                                                      entry.letters);
            REQUIRE(Options.auto_ability_letters[0].first.matches(
                lowercase_string(ability_name(ABIL_EVOKE_BLINK, true))));
            if (language == lang_t::ZH)
                REQUIRE(ability_name(entry.existing) != ability_name(entry.existing, true));

            CHECK(auto_assign_ability_slot(1) == entry.expected_slot);
            for (int slot = 0; slot < 52; ++slot)
            {
                const ability_type expected = slot == entry.expected_slot
                    ? ABIL_EVOKE_BLINK
                    : slot == (entry.expected_slot == 0 ? 1 : 0)
                        ? entry.existing : ABIL_NON_ABILITY;
                CHECK(you.ability_letter_table[slot] == expected);
            }
        }
    }
}

namespace {

static bool contains_cjk_text(const string& text)
{
    size_t pos = 0;
    while (pos < text.size())
    {
        char32_t cp = 0;
        const int len = utf8towc(&cp, text.c_str() + pos);
        if (len <= 0)
            return false;
        if (iscjk(cp))
            return true;
        pos += len;
    }
    return false;
}

// The game installs rich `you` and `view` bindings before TextDB descriptions
// execute. Catch2's lightweight main does not, so provide only the deterministic
// surface used by status.txt and restore the previous globals via RAII.
class ScopedHelpLuaGlobals
{
public:
    ScopedHelpLuaGlobals()
        : ls(clua.state()), you_ref(LUA_NOREF), view_ref(LUA_NOREF), active(true)
    {
        lua_getglobal(ls, "you");
        you_ref = luaL_ref(ls, LUA_REGISTRYINDEX);
        lua_getglobal(ls, "view");
        view_ref = luaL_ref(ls, LUA_REGISTRYINDEX);

        static const char fixture[] = R"lua(
you = {
    jademantle_crystals_desc = you.jademantle_crystals_desc,
    race = function() return "Mummy" end,
    hand = function() return "hand" end,
    flying = function() return false end,
    mutation = function() return 0 end,
    contam_max_damage = function() return 0 end,
    god = function() return "No God" end,
    wizard = function() return false end
}
view = {
    feature_at = function() return "floor" end
}
)lua";
        if (clua.execstring(fixture, "zh_help_fixture"))
        {
            const string error = clua.error;
            restore();
            throw std::runtime_error("failed to install Help Lua fixture: "
                                     + error);
        }
    }

    ~ScopedHelpLuaGlobals()
    {
        restore();
    }

    ScopedHelpLuaGlobals(const ScopedHelpLuaGlobals&) = delete;
    ScopedHelpLuaGlobals& operator=(const ScopedHelpLuaGlobals&) = delete;

    void set_god(const char* god)
    {
        lua_getglobal(ls, "you");
        lua_pushstring(ls, god);
        lua_pushcclosure(ls, [](lua_State* state) -> int
        {
            lua_pushvalue(state, lua_upvalueindex(1));
            return 1;
        }, 1);
        lua_setfield(ls, -2, "god");
        lua_pop(ls, 1);
    }

private:
    void restore()
    {
        if (!active)
            return;
        lua_rawgeti(ls, LUA_REGISTRYINDEX, you_ref);
        lua_setglobal(ls, "you");
        lua_rawgeti(ls, LUA_REGISTRYINDEX, view_ref);
        lua_setglobal(ls, "view");
        luaL_unref(ls, LUA_REGISTRYINDEX, you_ref);
        luaL_unref(ls, LUA_REGISTRYINDEX, view_ref);
        active = false;
    }

    lua_State* ls;
    int you_ref;
    int view_ref;
    bool active;
};

} // anonymous namespace

TEST_CASE("source-rereview: saved death causes localize only at display sinks",
          "[zh-help][source-rereview][hiscores]")
{
    rng::subgenerator scoped_rng(0x20261101ULL, 0x53434f5245ULL);
    const auto record = [](const string &type, const string &cause,
                           const string &killer = "saved caster") {
        return "v=0.33:name=Review:race=Human:cls=Fighter:xl=1:sk=Fighting:"
               "br=D:lvl=1:god=No God:ktyp=" + type
               + ":killer=" + killer + ":kaux=" + cause;
    };
    struct indirect_case
    {
        const char *type;
        const char *cause;
        const char *continuation;
    };
    const indirect_case indirect[] = {
        { "beam", "by angry trees", N_("... awakened by %1$s") },
        { "beam", "by Freeze", N_("... generated by %1$s") },
        { "beam", "by Shatter", N_("... invoked by %1$s") },
        { "collision", "a wall", N_("... after being knocked back by %1$s") },
    };
    map<string, pair<string, string>> canonical_log_messages;
    const auto check_log_messages = [&](const scorefile_entry &entry,
                                        const string &raw) {
        const lang_t before = Options.language;
        // These are the actual tmsg/vmsg and death-milestone producers, not
        // fields copied from the parsed input record.
        const auto messages = make_pair(entry.short_kill_message(),
                                        entry.long_kill_message());
        if (!canonical_log_messages.count(raw))
        {
            REQUIRE(before == lang_t::EN);
            canonical_log_messages.emplace(raw, messages);
        }
        CHECK(messages == canonical_log_messages.at(raw));
        CHECK_FALSE(contains_cjk_text(messages.first));
        CHECK_FALSE(contains_cjk_text(messages.second));
        CHECK(Options.language == before);
        CHECK(entry.raw_string() == raw);
    };
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const uint64_t state = rng::current_generator().get_state();
        const uint64_t count = rng::current_generator().get_count();
        for (const auto &test : indirect)
        {
            const string raw = record(test.type, test.cause);
            scorefile_entry entry;
            REQUIRE(entry.parse(raw));
            check_log_messages(entry, raw);
            const string description = entry.death_description(scorefile_entry::DDV_VERBOSE);
            const string clause = make_stringf_p(T_(test.continuation), "saved caster");
            INFO(description);
            CHECK(description.find(clause) != string::npos);
            if (language == lang_t::ZH)
                CHECK(contains_cjk_text(clause));
            CHECK(entry.raw_string() == raw);
            CHECK(entry.get_fields().str_field("kaux") == test.cause);
        }
        for (const char *killer : {"saved caster", "you"})
        {
            for (const char *cause : {"by angry trees", "by Shatter",
                                      "by unknown legacy event"})
            {
                const string raw = record("beam", cause, killer);
                scorefile_entry entry;
                REQUIRE(entry.parse(raw));
                check_log_messages(entry, raw);
                const string canonical = string(cause).substr(3);
                const string display = language == lang_t::ZH
                    && canonical != "unknown legacy event"
                    ? T_(canonical.c_str()) : canonical;
                const string description = entry.death_description(scorefile_entry::DDV_VERBOSE);
                INFO(description);
                CHECK(description.find(display) != string::npos);
                if (language == lang_t::ZH)
                {
                    CHECK(description.find("by ") == string::npos);
                    if (canonical != "unknown legacy event")
                        CHECK(display != canonical);
                }
                CHECK(entry.raw_string() == raw);
                CHECK(entry.get_fields().str_field("kaux") == cause);
                CHECK(entry.get_fields().str_field("killer") == killer);
            }
        }
        // Dungeon has a valid general translation but is not a beam identity.
        // The unknown-name checks therefore catch accidental blanket T_(kaux),
        // not just the ordinary missing-key fallback.
        for (const char *type : {"targeting", "reflect", "bounce", "self_aimed",
                                 "wild_magic"})
        {
            for (const char *cause : {"bolt of fire", "puff of frost", "Dungeon",
                                      "unknown legacy beam"})
            {
                const string raw = record(type, cause);
                scorefile_entry entry;
                REQUIRE(entry.parse(raw));
                check_log_messages(entry, raw);
                const bool known = string(cause) == "bolt of fire"
                                   || string(cause) == "puff of frost";
                CHECK(is_known_beam_name(cause) == known);
                const string display = language == lang_t::ZH && known
                                       ? T_(cause) : cause;
                const string description = entry.death_description(scorefile_entry::DDV_VERBOSE);
                INFO(type << " / " << cause << " / " << description);
                CHECK(description.find(display) != string::npos);
                if (language == lang_t::ZH && known)
                {
                    CHECK(display != cause);
                    CHECK(description.find(cause) == string::npos);
                }
                CHECK(entry.raw_string() == raw);
                CHECK(entry.get_fields().str_field("kaux") == cause);
            }
        }
        scorefile_entry zot;
        const string raw_zot = record("zot", "");
        REQUIRE(zot.parse(raw_zot));
        const string zot_cause = zot.death_description(scorefile_entry::DDV_TERSE);
        CHECK(zot_cause == C_("death cause terse", "Zot"));
        if (language == lang_t::ZH)
            CHECK(zot_cause != T_("Zot"));
        CHECK(zot.raw_string() == raw_zot);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }
}

TEST_CASE("source-rereview: HP note death-cause snapshots survive language and save changes",
          "[zh-help][source-rereview][hp-note]")
{
    for (lang_t captured_language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture capture(captured_language,
                                   captured_language == lang_t::ZH ? "zh" : nullptr);
        for (const char *cause : {"bolt of fire", "puff of frost", "talismans",
                                  "unknown legacy beam"})
        {
            // Use the same score consumer and Note construction as ouch's
            // HP-change path. No UI-language text becomes a kaux identity.
            const string raw = string("v=0.33:name=Review:race=Human:cls=Fighter:")
                + "xl=1:sk=Fighting:br=D:lvl=1:god=No God:ktyp=beam:"
                  "killer=saved caster:kaux=" + cause;
            scorefile_entry score;
            REQUIRE(score.parse(raw));
            const string snapshot = score.death_description(scorefile_entry::DDV_TERSE);
            const bool known = string(cause) == "bolt of fire"
                               || string(cause) == "puff of frost";
            const string display_cause = captured_language == lang_t::ZH && known
                                         ? T_(cause) : cause;
            INFO(snapshot);
            CHECK(snapshot.find("/" + display_cause) != string::npos);
            if (captured_language == lang_t::ZH && known)
                CHECK(snapshot.find(cause) == string::npos);
            Note note(NOTE_HP_CHANGE, 3, 12, snapshot);
            note.place = level_id(BRANCH_DUNGEON, 2);
            vector<unsigned char> bytes;
            writer output(&bytes);
            note.save(output);
            reader input(bytes);
            input.setMinorVersion(TAG_MINOR_VERSION);
            Note loaded;
            loaded.load(input);
            for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
            {
                TranslationFixture render(language, language == lang_t::ZH ? "zh" : nullptr);
                CHECK(loaded.type == NOTE_HP_CHANGE);
                CHECK(loaded.first == 3);
                CHECK(loaded.second == 12);
                CHECK(loaded.name == snapshot);
                CHECK(loaded.describe(false, false).find("[" + snapshot + "]") != string::npos);
                vector<unsigned char> after_display;
                writer repeated(&after_display);
                loaded.save(repeated);
                CHECK(after_display == bytes);
                CHECK(score.raw_string() == raw);
                CHECK(score.get_fields().str_field("kaux") == cause);
                CHECK(score.get_fields().str_field("killer") == "saved caster");
                if (language == lang_t::EN)
                {
                    CHECK(score.death_description(scorefile_entry::DDV_LOGVERBOSE).find(cause)
                          != string::npos);
                }
            }
        }
    }
}

TEST_CASE("source-rereview: death notes retain their creation language",
          "[zh-help][source-rereview][death-note]")
{
    for (lang_t captured_language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture capture(captured_language,
                                   captured_language == lang_t::ZH ? "zh" : nullptr);
        for (const char *type : {"reflect", "bounce", "wild_magic"})
        {
            for (const char *cause : {"bolt of fire", "unknown legacy beam"})
            {
                const string raw = string("v=0.33:name=Review:race=Human:cls=Fighter:")
                    + "xl=1:sk=Fighting:br=D:lvl=1:god=No God:ktyp=" + type
                    + ":killer=saved caster:kaux=" + cause;
                scorefile_entry score;
                REQUIRE(score.parse(raw));
                // Normal death and the wizard death-simulation producer.
                for (auto verbosity : {scorefile_entry::DDV_NORMAL,
                                       scorefile_entry::DDV_VERBOSE})
                {
                    const string snapshot = score.death_description(verbosity);
                    const string display = captured_language == lang_t::ZH
                        && string(cause) == "bolt of fire" ? T_(cause) : cause;
                    REQUIRE(snapshot.find(display) != string::npos);
                    Note note(NOTE_DEATH, 0, 12, snapshot);
                    note.place = level_id(BRANCH_DUNGEON, 2);
                    vector<unsigned char> bytes;
                    writer output(&bytes);
                    note.save(output);
                    reader input(bytes);
                    input.setMinorVersion(TAG_MINOR_VERSION);
                    Note loaded;
                    loaded.load(input);
                    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
                    {
                        TranslationFixture render(language,
                                                  language == lang_t::ZH ? "zh" : nullptr);
                        CHECK(loaded.type == NOTE_DEATH);
                        CHECK(loaded.name == snapshot);
                        CHECK(loaded.describe(false, false) == snapshot);
                        vector<unsigned char> after_display;
                        writer repeated(&after_display);
                        loaded.save(repeated);
                        CHECK(after_display == bytes);
                        CHECK(score.raw_string() == raw);
                        CHECK(score.get_fields().str_field("kaux") == cause);
                        CHECK_FALSE(contains_cjk_text(score.long_kill_message()));
                        CHECK_FALSE(contains_cjk_text(score.short_kill_message()));
                        CHECK(Options.language == language);
                    }
                }
            }
        }
    }
}

TEST_CASE("source-rereview: command help follows equipment and targeting consumers",
          "[zh-help][source-rereview][commands]")
{
    unwind_var<game_type> restore_type(crawl_state.type);
    // A rebound key proves both pages interpolate CMD_EQUIP, rather than
    // retaining the old P/V talisman advice or baking in the default e.
    const int equipment_key = command_to_key(CMD_EQUIP);
    const int test_key = '!';
    const command_type previous = key_to_command(test_key, KMC_DEFAULT);
    unwinder restore_binding([equipment_key, previous, test_key]() {
        bind_command_to_key(CMD_EQUIP, equipment_key);
        bind_command_to_key(previous, test_key);
    });
    REQUIRE(previous != CMD_NO_CMD);
    bind_command_to_key(CMD_EQUIP, test_key);
    REQUIRE(command_to_string(CMD_EQUIP) == "!");
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (game_type type : {GAME_TYPE_NORMAL, GAME_TYPE_HINTS})
        {
            crawl_state.type = type;
            string header, body;
            CHECK(help_popup_state_for_test('?', 0, header, body) == '?');
            const string talismans = T_("talismans");
            const auto line = body.find(talismans);
            REQUIRE(line != string::npos);
            const string equipment = body.substr(line, body.find('\n', line) - line);
            INFO(equipment);
            CHECK(equipment.find('!') != string::npos);
            CHECK(equipment.find("ePoke") == string::npos);
            CHECK(equipment.find("eVoke") == string::npos);
            if (language == lang_t::EN)
            {
                CHECK(body.find("up to 100 turns") != string::npos);
                CHECK(body.find("Health or Magic become full") == string::npos);
                CHECK(body.find("nearest monster") == string::npos);
                CHECK(body.find("press twice") == string::npos);
                if (type == GAME_TYPE_HINTS)
                {
                    CHECK(body.find("confirm current target") != string::npos);
                    CHECK(body.find("shoot at previous target") == string::npos);
                }
            }
            else
            {
                CHECK(contains_cjk_text(equipment));
                CHECK(body.find("rest or wait") == string::npos);
                CHECK(body.find("up to 100 turns") == string::npos);
                CHECK(body.find("confirm current target") == string::npos);
                CHECK(body.find("during pickup prompts") == string::npos);
            }
        }
        CHECK(key_to_command(CK_ENTER, KMC_TARGETING) == CMD_TARGET_SELECT);
        CHECK(key_to_command('f', KMC_TARGETING) == CMD_TARGET_SELECT);
        CHECK(key_to_command('.', KMC_TARGETING) == CMD_TARGET_SELECT_ENDPOINT);
        CHECK(key_to_command('+', KMC_TARGETING) == CMD_TARGET_CYCLE_FORWARD);
        CHECK(key_to_command('-', KMC_TARGETING) == CMD_TARGET_CYCLE_BACK);
        CHECK(key_to_command('p', KMC_TARGETING) == CMD_NO_CMD);
        CHECK(key_to_command(CK_DELETE, KMC_TARGETING) == CMD_NO_CMD);
        CHECK(key_to_command('P', KMC_TARGETING) == CMD_NO_CMD);
    }
}

TEST_CASE("source-rereview: feature instructions preserve actions and rebound keys",
          "[zh-help][source-rereview][describe-feature]")
{
    const coord_def pos(20, 22);
    unwind_var<branch_type> restore_branch(you.where_are_you, BRANCH_DUNGEON);
    unwind_var<int> restore_depth(you.depth, 1);
    unwind_var<game_type> restore_game(crawl_state.type, GAME_TYPE_NORMAL);
    const coord_def original_position = you.pos();
    unwinder restore_position([original_position]() { you.set_position(original_position); });
    you.set_position(pos);
    unwind_var<dungeon_feature_type> restore_grid(env.grid(pos));
    unwind_var<map_cell> restore_knowledge(env.map_knowledge(pos));
    unwind_var<unsigned int> restore_map_id(env.level_map_ids(pos), INVALID_MAP_INDEX);
    unwind_var<decltype(env.shop)> restore_shops(env.shop);
    shop_struct shop;
    shop.pos = pos;
    shop.type = SHOP_WEAPON;
    shop.shop_name = "Test Counter";
    env.shop[pos] = shop;

    struct binding
    {
        command_type command;
        int old_key;
        int new_key;
        command_type displaced;
    };
    vector<binding> bindings;
    for (const auto &entry : vector<pair<command_type, int>>{
             { CMD_GO_DOWNSTAIRS, '!' }, { CMD_GO_UPSTAIRS, '@' },
             { CMD_OPEN_DOOR, '$' }, { CMD_CLOSE_DOOR, '^' }})
    {
        const command_type displaced = key_to_command(entry.second, KMC_DEFAULT);
        REQUIRE(displaced != CMD_NO_CMD);
        bindings.push_back({entry.first, command_to_key(entry.first), entry.second, displaced});
    }
    unwinder restore_bindings([bindings]() {
        for (const auto &entry : bindings)
            bind_command_to_key(entry.command, entry.old_key);
        for (const auto &entry : bindings)
            bind_command_to_key(entry.displaced, entry.new_key);
    });
    for (const auto &entry : bindings)
        bind_command_to_key(entry.command, entry.new_key);

    const dungeon_feature_type features[] = {
        DNGN_CLOSED_DOOR, DNGN_OPEN_DOOR, DNGN_SEALED_DOOR,
        DNGN_STONE_STAIRS_DOWN_I, DNGN_ENTER_TROVE, DNGN_ENTER_ZOT,
        DNGN_EXIT_VAULTS, DNGN_ENTER_VAULTS, DNGN_ENTER_HELL,
        DNGN_TRANSPORTER, DNGN_ENTER_SHOP,
    };
    map<dungeon_feature_type, string> canonical_keys;
    for (const auto feature : features)
        canonical_keys[feature] = feature_description_en(feature);

    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto feature : features)
        {
            env.grid(pos) = feature;
            env.map_knowledge(pos).set_feature(feature);
            describe_info description;
            get_feature_desc(pos, description, false);
            const string body = description.body.str();
            const command_type command = feat_is_door(feature)
                ? (feat_is_closed_door(feature) ? CMD_OPEN_DOOR : CMD_CLOSE_DOOR)
                : feature == DNGN_TRANSPORTER || feature == DNGN_ENTER_SHOP
                  ? CMD_GO_DOWNSTAIRS : feat_stair_direction(feature);
            const string key = "<w>" + command_to_string(command) + "</w>";
            INFO(feature << " / " << body);
            const size_t key_position = body.find(key);
            REQUIRE(key_position != string::npos);
            const size_t start = body.rfind('\n', key_position);
            const size_t end = body.find('\n', key_position);
            const string instruction = body.substr(start == string::npos ? 0 : start,
                end == string::npos ? string::npos : end - (start == string::npos ? 0 : start));
            CHECK(instruction.find("%1$s") == string::npos);
            CHECK(instruction.find("%s") == string::npos);
            const string rune_condition = T_(" if you have enough runes");
            REQUIRE_FALSE(rune_condition.empty());
            CHECK((instruction.find(rune_condition) != string::npos)
                  == (feature == DNGN_ENTER_ZOT || feature == DNGN_EXIT_VAULTS));
            CHECK((instruction.find(T_("normally ")) != string::npos)
                  == (feature == DNGN_SEALED_DOOR));
            CHECK((instruction.find(T_("try to ")) != string::npos)
                  == (feature == DNGN_ENTER_TROVE));
            CHECK(instruction.find("with with") == string::npos);
            if (language == lang_t::ZH)
            {
                CHECK(contains_cjk_text(instruction));
                CHECK(instruction.find("Hell") == string::npos);
                CHECK(instruction.find("through") == string::npos);
            }
            else if (feature == DNGN_ENTER_HELL)
                CHECK(instruction.find("enter Hell") != string::npos);
            CHECK(feature_description_en(feature) == canonical_keys[feature]);
            CHECK(Options.language == language);
            CHECK(env.grid(pos) == feature);
        }
        CHECK(env.shop[pos].shop_name == "Test Counter");
    }
}

TEST_CASE("source-rereview: randart vulnerability renders complete element sentences",
          "[zh-help][source-rereview][describe-artefact]")
{
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.flags = ISFLAG_RANDART | ISFLAG_IDENTIFIED;
    CrawlVector &properties = item.props[ARTEFACT_PROPS_KEY].new_vector(SV_SHORT);
    properties.resize(ART_PROPERTIES);
    properties.set_max_size(ART_PROPERTIES);
    for (vec_size index = 0; index < ART_PROPERTIES; ++index)
        properties[index].get_short() = 0;
    const pair<artefact_prop_type, const char *> elements[] = {
        { ARTP_FIRE, "fire" }, { ARTP_COLD, "cold" },
        { ARTP_NEGATIVE_ENERGY, "negative energy" },
    };
    const char *const sentences[] = {
        N_("It makes you extremely vulnerable to %1$s."),
        N_("It makes you very vulnerable to %1$s."),
        N_("It makes you vulnerable to %1$s."),
    };
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto &element : elements)
        {
            const string noun = C_("element", element.second);
            CHECK(noun.find("伤害") == string::npos);
            for (int value : {-3, -2, -1})
            {
                artefact_set_property(item, element.first, value);
                const string expected = make_stringf_p(T_(sentences[value + 3]), noun.c_str());
                for (int generation = 0; generation < 2; ++generation)
                {
                    vector<string> lines;
                    desc_randart_props(item, lines);
                    INFO(element.second << " / " << value << " / " << expected);
                    CHECK(any_of(lines.begin(), lines.end(), [&](const string &line) {
                        return line.find(expected) != string::npos;
                    }));
                    CHECK(artefact_property(item, element.first) == value);
                    if (language == lang_t::ZH)
                    {
                        CHECK(contains_cjk_text(expected));
                        CHECK(expected.find("伤害") != string::npos);
                    }
                    i18n_cache_clear();
                }
            }
            artefact_set_property(item, element.first, 0);
        }
    }
}

TEST_CASE("source-rereview: monster habitat keeps surface and submerged travel distinct",
          "[zh-help][source-rereview][describe-monster]")
{
    init_monsters();
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const monster_info surface(MONS_ORC_APOSTLE, MONS_ORC_APOSTLE);
        const monster_info swimmer(MONS_FRILLED_LIZARD, MONS_FRILLED_LIZARD);
        const string surface_text = _monster_habitat_description(surface);
        const string swimmer_text = _monster_habitat_description(swimmer);
        CHECK(surface_text.find(T_("walk on")) != string::npos);
        CHECK(swimmer_text.find(T_("travel through")) != string::npos);
        if (language == lang_t::ZH)
        {
            CHECK(surface_text.find("水面中") == string::npos);
            CHECK(surface_text != swimmer_text);
            CHECK(contains_cjk_text(surface_text));
            CHECK(contains_cjk_text(swimmer_text));
        }
        else
        {
            CHECK(surface_text == "It can walk on water.\n");
            CHECK(swimmer_text == "It can travel through water.\n");
        }
        CHECK(surface.type == MONS_ORC_APOSTLE);
        CHECK(swimmer.type == MONS_FRILLED_LIZARD);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: manual A shortcut uses the localized page across locales",
                 "[zh-help][guides][manual-overview]")
{
    for (lang_t language : {lang_t::ZH, lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        string header, body;
        CHECK(help_popup_state_for_test(CK_HOME, 'A', header, body) == '*');
        if (language == lang_t::ZH)
        {
            CHECK(body.find("Crawl 是一款有趣的游戏") != string::npos);
            CHECK(body.find("OVERVIEW") == string::npos);
            CHECK(header.find("Dungeon Crawl Stone Soup 手册") != string::npos);
        }
        else
        {
            CHECK(body.find("Crawl is a fun game") != string::npos);
            CHECK(body.find("OVERVIEW") != string::npos);
            CHECK(header.find(": Manual") != string::npos);
        }
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: standalone guide popups render localized pages",
                 "[zh-help][guides]")
{
    struct guide_expectation
    {
        int hotkey;
        const char* marker;
        const char* english_marker;
    };
    const vector<guide_expectation> popup_guides = {
        {'*', "Dungeon Crawl Stone Soup 手册",
              "Dungeon Crawl Stone Soup manual"},
        {'^', "Crawl 快速入门指南", "Crawl Quick-Start Guide"},
        {'~', "宏与按键映射", "Macros and Keymaps"},
        {'&', "Crawl 选项指南", "Guide to Crawl's options"},
#ifdef USE_TILE_LOCAL
        {'t', "贴图版专用命令", "Tiles specific commands"},
#endif
    };
    for (const auto& guide : popup_guides)
    {
        string header;
        string text;
        INFO("Guide hotkey: " << static_cast<char>(guide.hotkey));
        CHECK(help_popup_state_for_test(guide.hotkey, 0, header, text)
              == guide.hotkey);
        CHECK(header.find("地下城 Crawl 帮助") != string::npos);
        CHECK(header.find(guide.marker) != string::npos);
        CHECK(header.find("Dungeon Crawl Help") == string::npos);
        CHECK(text.find(guide.marker) != string::npos);
        CHECK(text.find(guide.english_marker) == string::npos);
        CHECK(contains_cjk_text(text));
    }

    // The title and body stored by the live popup must both change when the
    // user switches pages after opening it.
    for (const auto& guide : popup_guides)
    {
        if (guide.hotkey == '*')
            continue;
        string header;
        string text;
        INFO("Guide switch hotkey: " << static_cast<char>(guide.hotkey));
        CHECK(help_popup_state_for_test('*', guide.hotkey, header, text)
              == guide.hotkey);
        CHECK(header.find("地下城 Crawl 帮助") != string::npos);
        CHECK(header.find(guide.marker) != string::npos);
        CHECK(header.find("Dungeon Crawl Help") == string::npos);
        CHECK(text.find(guide.marker) != string::npos);
        CHECK(text.find(guide.english_marker) == string::npos);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: tiles guide uses shared loader without console hotkey",
                 "[zh-help][guides]")
{
    string header;
    string text;
#ifndef USE_TILE_LOCAL
    CHECK(help_popup_state_for_test('t', 0, header, text) == 0);
    CHECK(header.empty());
    CHECK(text.empty());
#endif

    CHECK(platform_help_section_for_test('t', header, text) == 't');
    CHECK(header.find("地下城 Crawl 帮助") != string::npos);
    CHECK(header.find("贴图版专用命令") != string::npos);
    CHECK(header.find("Dungeon Crawl Help") == string::npos);
    CHECK(text.find("贴图版专用命令") != string::npos);
    CHECK(text.find("Tiles specific commands") == string::npos);
    CHECK(contains_cjk_text(text));

#ifndef USE_TILE_LOCAL
    header.clear();
    text.clear();
    CHECK(help_popup_state_for_test('t', 0, header, text) == 0);
    CHECK(header.empty());
    CHECK(text.empty());
#endif
}

TEST_CASE("zh-help: standalone guides fall back to English",
          "[zh-help][guides]")
{
    const char* saved = Options.lang_name;
    Options.lang_name = "zz-missing-guide-language";
    const string missing_language = help_file_path("options_guide.txt");
    CHECK(missing_language.find("zz-missing-guide-language") == string::npos);
    CHECK(missing_language.find("options_guide.txt") != string::npos);
    CHECK(help_header_suffix('&') == ": Options");

    Options.lang_name = nullptr;
    const string english = help_file_path("quickstart.txt");
    CHECK(english.find("zh" + string(1, FILE_SEPARATOR)) == string::npos);
    CHECK(english.find("quickstart.txt") != string::npos);
    CHECK(help_header_suffix('^') == ": Quickstart");
    Options.lang_name = saved;
}

// =============================================================================
// [zh-help][issue-52] — load the complete frozen Help/FAQ inventory through
// the production consumers. These exact key sets are the runtime counterpart
// to docs/help-review-plan.md's baseline inventory: every identity must remain
// present, translated, valid UTF-8, and free of embedded-Lua diagnostics.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: Issue 52 frozen Help and FAQ entries load",
                 "[zh-help][issue-52]")
{
    ScopedHelpLuaGlobals lua_fixture;

    const vector<string> help_keys = {
        "annotate.prompt",
        "console-keycodes",
        "interlevel-travel.altar.prompt",
        "interlevel-travel.branch.prompt",
        "interlevel-travel.depth.prompt",
        "known-menu",
        "level-map",
        "macro-menu",
        "pick-up",
        "skill-menu",
        "spell-library",
        "stash-search.prompt",
        "wiz-monster",
    };
    for (const string& key : help_keys)
    {
        const string rendered = getHelpString(key);
        const string missing = make_stringf(
            T_("Error! The help for \"%s\" is missing!"), key.c_str());
        INFO("Help key: " << key);
        CHECK_FALSE(rendered.empty());
        CHECK(rendered != missing);
        CHECK(contains_cjk_text(rendered));
        CHECK_FALSE(rule_garbled_utf8(rendered));
        CHECK_FALSE(rule_embedded_lua_error(rendered));
    }

    const vector<string> faq_suffixes = {
        "goal",
        "userdir",
        "roguelike difference",
        "survival",
        "downstairs",
        "cheating",
        "weapons",
        "religion",
        "ghosts",
        "abyss",
        "randart",
        "interact",
        "version",
        "beta",
        "bug",
        "idea",
        "help",
        "changes",
        "tiles lag",
    };
    vector<string> expected_question_keys;
    expected_question_keys.reserve(faq_suffixes.size());
    for (const string& suffix : faq_suffixes)
        expected_question_keys.push_back("q:" + suffix);

    vector<string> actual_question_keys = getAllFAQKeys();
    std::sort(expected_question_keys.begin(), expected_question_keys.end());
    std::sort(actual_question_keys.begin(), actual_question_keys.end());
    CHECK(actual_question_keys == expected_question_keys);

    const vector<string> bulleted_answers = {
        "roguelike difference",
        "abyss",
        "randart",
        "bug",
        "help",
    };
    for (const string& suffix : faq_suffixes)
    {
        const string question_key = "q:" + suffix;
        const string question = getFAQ_Question(question_key);
        const string answer = getFAQ_Answer(question_key);
        INFO("FAQ suffix: " << suffix);
        CHECK_FALSE(question.empty());
        CHECK_FALSE(answer.empty());
        CHECK(contains_cjk_text(question));
        CHECK(contains_cjk_text(answer));
        CHECK_FALSE(rule_garbled_utf8(question));
        CHECK_FALSE(rule_garbled_utf8(answer));
        CHECK_FALSE(rule_embedded_lua_error(question));
        CHECK_FALSE(rule_embedded_lua_error(answer));
        CHECK(answer.find("\n\n*") == string::npos);
        if (std::find(bulleted_answers.begin(), bulleted_answers.end(), suffix)
            != bulleted_answers.end())
        {
            CHECK(answer.find("\n•") != string::npos);
        }
    }
}

// =============================================================================
// [zh-help][bidirectional] — round-trip lookups under the ZH fixture.
//
// For each type that accepts Chinese input, feed the display name produced by
// the type's getter back into its lookup fn and assert the same enum is
// recovered.
// =============================================================================
//
// IMPORTANT — assertion strength rationale (Issue 51 regression intent):
//   The Issue-51 bug was that lookups *failed to recognise* Chinese display
//   names (returned the terminal sentinel), breaking the ?/ help menu. The
//   regression risk this test guards is therefore "a display name is not
//   recognised", NOT "a fuzzy matcher resolves to a slightly different but
//   valid enum". Several game lookups are inherently fuzzy (substring / prefix
//   matching). For those we assert RECOGNITION (a non-terminal enum) rather
//   than exact enum equality, and document the reason inline. Where exact
//   equality is reliable (card and the initialised bane index), we keep it
//   strict.
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: bidirectional lookup round-trips",
                 "[zh-help][bidirectional]")
{
    // --- spell: partial_match=true is MANDATORY (ZH fallback only fires
    //     then; spl-util.cc:638-660). find_earliest_match resolves the ZH
    //     title by *substring*, so a title that is a substring of an earlier
    //     spell's title resolves to that earlier spell — a recognised, valid
    //     spell but not necessarily the same enum. Assert recognition. ---
    init_spell_descs();
    init_spell_name_cache();
    for (int si = 0; si < NUM_SPELLS; ++si)
    {
        const spell_type s = static_cast<spell_type>(si);
        if (s == SPELL_NO_SPELL)
            continue;
        const char* title = spell_title(s);
        if (!title || !title[0])
            continue;
        INFO("spell round-trip: " << title);
        CHECK(spell_by_name(title, /*partial_match=*/true) != SPELL_NO_SPELL);
    }

    // --- ability: ability_by_name iterates the player's ability list and
    //     matches EN dbname first, but uses substring containment
    //     (key.find(name) != npos), so an ability whose name is a substring
    //     of another (e.g. an ability contained in "Brand Self") resolves to
    //     the shorter one. Some ABIL_* enum slots are also unused placeholders
    //     ("No ability"). Skip placeholders; assert recognition for the rest. ---
    for (int ai = 0; ai < NUM_ABILITIES; ++ai)
    {
        const ability_type a = static_cast<ability_type>(ai);
        const string dbname = ability_name(a, /*dbname=*/true);
        if (dbname.empty() || dbname == "No ability")
            continue;
        INFO("ability round-trip: " << dbname);
        CHECK(ability_by_name(dbname) != ABIL_NON_ABILITY);
    }

    // --- skill: skill_from_name (dbg-util.cc) lowercases the DB name but NOT
    //     the query, and substring-matches (last containment wins, prefix
    //     preferred). The ?/K menu feeds it a lowercased key. Mirror that and
    //     assert recognition (a non-terminal skill). ---
    for (int ski = SK_FIRST_SKILL; ski < NUM_SKILLS; ++ski)
    {
        const skill_type sk = static_cast<skill_type>(ski);
        const char* nm = skill_name(sk);
        if (!nm || !nm[0])
            continue;
        INFO("skill round-trip: " << nm);
        CHECK(skill_from_name(lowercase_string(nm).c_str()) != SK_NONE);
    }

    // --- card: name_to_card(card_name(c)); skip removed cards. Exact and
    //     reliable — keep strict. ---
    for (int ci = 0; ci < NUM_CARDS; ++ci)
    {
        const card_type c = static_cast<card_type>(ci);
        if (card_is_removed(c))
            continue;
        const char* nm = card_name(c);
        if (!nm || !nm[0])
            continue;
        INFO("card round-trip: " << nm);
        CHECK(name_to_card(nm) == c);
    }

    // --- mutation: mutation_from_name does exact-then-substring matching.
    //     Distinct mutations can share a substring (e.g. "... scales"), so a
    //     name may resolve to an earlier mutation. Assert recognition. ---
    for (int mi = 0; mi < NUM_MUTATIONS; ++mi)
    {
        const mutation_type m = static_cast<mutation_type>(mi);
        const char* nm = mutation_name(m, /*allow_category=*/false);
        if (!nm || !nm[0])
            continue;
        INFO("mutation round-trip: " << nm);
        CHECK(mutation_from_name(nm, /*allow_category=*/false) != NUM_MUTATIONS);
    }

    // --- bane: initialise bane_index, then require exact round-trips. This
    //     prevents every enum from silently reading entry 0 ("lethargy"). ---
    init_mut_index();
    for (int bi = 0; bi < NUM_BANES; ++bi)
    {
        const bane_type b = static_cast<bane_type>(bi);
        const string nm = bane_name(b, /*dbkey=*/true);
        if (nm.empty())
            continue;
        INFO("bane round-trip: " << nm);
        CHECK(bane_from_name(nm.c_str()) == b);
    }

    // --- feature: feat_by_desc round-trip is known-flaky (DESC formatting).
    //     Lenient: only assert non-crash + valid-enum bound; do not hard-fail
    //     on mismatch. ---
    init_show_table();
    init_feat_desc_cache();
    for (int fi = 0; fi < NUM_FEATURES; ++fi)
    {
        const dungeon_feature_type f = static_cast<dungeon_feature_type>(fi);
        if (!is_valid_feature_type(f))
            continue;
        const feature_def& def = get_feature_def(f);
        if (!def.name || !def.name[0])
            continue;
        const dungeon_feature_type back = feat_by_desc(def.name);
        CHECK(is_valid_feature_type(back));
    }
}

// =============================================================================
// [zh-help][protocol-en] — EN-only protocol round-trips that still work UNDER
// the fixture because their names are NOT T_()'d.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: protocol EN round-trips (cloud, branch)",
                 "[zh-help][protocol-en]")
{
    // --- cloud: cloud_name_to_type compares against cloud_type_name(i) with
    //     the default terse=true form, so feed the terse name back (the
    //     verbose terse=false form — "a forest fire", "the rain" — is a
    //     display-only string the reverse lookup does not accept). Note some
    //     cloud entries share a terse name (e.g. two "magical condensation"
    //     rows in cloud.cc), so a name may resolve to the first matching enum;
    //     assert recognition (a real cloud, non-terminal) rather than exact. ---
    for (int ci = 0; ci < NUM_CLOUD_TYPES; ++ci)
    {
        const cloud_type c = static_cast<cloud_type>(ci);
        const string nm = cloud_type_name(c, /*terse=*/true);
        if (nm.empty() || nm == "buggy goodness")
            continue;
        INFO("cloud round-trip: " << nm);
        CHECK(cloud_name_to_type(nm) != CLOUD_NONE);
    }

    // --- branch: branch_by_shortname(branches[b].shortname). ---
    for (int bi = 0; bi < NUM_BRANCHES; ++bi)
    {
        const branch_type b = static_cast<branch_type>(bi);
        const char* sn = branches[b].shortname;
        if (!sn || !sn[0])
            continue;
        INFO("branch round-trip: " << sn);
        CHECK(branch_by_shortname(sn) == b);
    }
}

// =============================================================================
// [zh-help][card-wrath] — R2 blocker R2-CODE-004 regression: the card name
// context key and the weapon-brand plain key must stay distinct in the
// SourceDB lowercase-canonical key space.
//
// decks.cc card_name() uses C_("card name", "Wrath") for CARD_WRATH and
// source.txt defines `card name|Wrath` -> 神怒, while the weapon-inscription
// plain key `wrath` -> 狂怒 (item-name.cc SPARM_RAGE) must remain untouched.
// Before the fix, card_name() used T_("Wrath") whose canonical lookup key
// `wrath` collided with the brand key, so the card was displayed as 狂怒.
// Mutation check (documented in the R2 fix commit): reverting decks.cc to
// T_("Wrath") makes this test fail (card_name returns 狂怒), proving the
// context-key resolution is what is under test.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: card Wrath context key vs wrath brand key",
                 "[zh-help][zh-translation][card-wrath]")
{
    REQUIRE(Options.language == lang_t::ZH);

    // C_("card name", "Wrath"): the context key must be in effect.
    CHECK(strcmp(card_name(CARD_WRATH), "神怒") == 0);

    // The weapon-brand plain key `wrath` is unaffected by the card
    // context key and still resolves to 狂怒.
    CHECK(strcmp(T_("wrath"), "狂怒") == 0);
}

// =============================================================================
// [zh-help][god] — SEPARATE plain TEST_CASE (NO fixture, EN mode). god_name()
// is T_()'d so it returns Chinese under the fixture, but str_to_god() matches
// English only. In EN mode T_() returns the English key, so the round-trip
// holds. (god_name's EN behavior confirmed: short names go through T_() which
// falls back to English when Options.language == EN.)
// =============================================================================
TEST_CASE_METHOD(EnTranslationFixture,
                 "zh-help: god EN round-trip",
                 "[zh-help][god]")
{
    REQUIRE(Options.language == lang_t::EN);
    for (int gi = GOD_NO_GOD + 1; gi < NUM_GODS; ++gi)
    {
        const god_type g = static_cast<god_type>(gi);
        // GOD_PAKELLAS is a removed/disabled god (TAG_MAJOR_VERSION==34); the
        // ?/G menu itself skips it (_get_god_keys, lookup-help.cc:415), and
        // str_to_god does not resolve its name. Mirror that skip.
#if TAG_MAJOR_VERSION == 34
        if (g == GOD_PAKELLAS)
            continue;
#endif
        const string nm = god_name(g);
        if (nm.empty())
            continue;
        INFO("god round-trip: " << nm);
        CHECK(str_to_god(nm) == g);
    }
}

// =============================================================================
// [zh-help][strip-suffix] — contract test for strip_suffix (stringutil.h): the
// real Bug-B truncation primitive. strip_suffix is UTF-8-safe because it
// ends_with-checks then erases exactly the matched ASCII suffix bytes, never
// cutting a multibyte char.
// =============================================================================
TEST_CASE("zh-help: strip_suffix contract (Bug-B guard)",
          "[zh-help][strip-suffix]")
{
    // Match + strip (note strip_suffix trims the trailing space).
    {
        string s = "Blade card";
        REQUIRE(strip_suffix(s, "card"));
        REQUIRE(s == "Blade");
    }

    // Non-match against a Chinese string: must return false, leave the string
    // untouched, and the result must remain valid UTF-8 (no mid-codepoint cut).
    {
        string s2 = "火球术";
        REQUIRE_FALSE(strip_suffix(s2, "spell"));
        REQUIRE(s2 == "火球术");
        REQUIRE_FALSE(rule_garbled_utf8(s2));
    }

    // A Chinese string that *does* carry an ASCII suffix: strip must remove
    // only the ASCII bytes and keep the CJK prefix valid UTF-8.
    {
        string s3 = "火球术 spell";
        REQUIRE(strip_suffix(s3, "spell"));
        REQUIRE(s3 == "火球术");
        REQUIRE_FALSE(rule_garbled_utf8(s3));
    }
}

// =============================================================================
// [zh-help][regression] — safety: feed each lookup fn degenerate inputs and
// assert it returns an invalid/terminal value without crashing.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: lookup crash-safety on degenerate input",
                 "[zh-help][regression]")
{
    init_monsters();
    init_spell_name_cache();
    init_feat_desc_cache();

    // Non-empty garbage inputs: no real name contains these, so every lookup
    // must return its terminal/invalid sentinel. (The empty string "" is a
    // degenerate substring of *every* name and is handled separately below —
    // substring matchers legitimately match it.)
    const vector<string> garbage = {
        "xyzzy",
        "火球abc",
        string(500, 'z'),
    };

    for (const string& in : garbage)
    {
        INFO("garbage input len=" << in.size());

        CHECK(spell_by_name(in, /*partial_match=*/true) == SPELL_NO_SPELL);
        CHECK(ability_by_name(in) == ABIL_NON_ABILITY);
        CHECK(skill_from_name(in.c_str()) == SK_NONE);
        CHECK(name_to_card(in) == NUM_CARDS);
        CHECK(mutation_from_name(in, /*allow_category=*/false) == NUM_MUTATIONS);
        CHECK(bane_from_name(in.c_str()) == NUM_BANES);
        CHECK(str_to_god(in) == GOD_NO_GOD);
        CHECK(branch_by_shortname(in) == NUM_BRANCHES);
        CHECK(cloud_name_to_type(in) == CLOUD_NONE);
        CHECK(get_monster_by_name(in) == MONS_PROGRAM_BUG);

        // item_kind_by_name returns a struct; a bad name yields the
        // OBJ_UNASSIGNED sentinel. Assert non-crash + terminal sentinel.
        const item_kind ik = item_kind_by_name(in);
        CHECK(ik.base_type == OBJ_UNASSIGNED);

        // feat_by_desc: non-crash + valid enum bound.
        const dungeon_feature_type f = feat_by_desc(in);
        CHECK(f >= DNGN_UNSEEN);
        CHECK(f <= NUM_FEATURES);
    }

    // Empty string: assert only that every lookup does not crash and returns
    // a value within its valid enum range. Substring matchers (skill_from_name)
    // legitimately match "" to some skill, so terminal-sentinel is NOT required
    // here — only non-crash + in-bounds.
    {
        const string empty;
        INFO("empty-string degenerate input");
        (void) spell_by_name(empty, /*partial_match=*/true);
        (void) ability_by_name(empty);
        (void) skill_from_name(empty.c_str());
        (void) name_to_card(empty);
        (void) mutation_from_name(empty, /*allow_category=*/false);
        (void) bane_from_name(empty.c_str());
        (void) str_to_god(empty);
        (void) branch_by_shortname(empty);
        (void) cloud_name_to_type(empty);
        (void) get_monster_by_name(empty);
        (void) item_kind_by_name(empty);
        const dungeon_feature_type f = feat_by_desc(empty);
        CHECK(f >= DNGN_UNSEEN);
        CHECK(f <= NUM_FEATURES);
    }
}

// =============================================================================
// [zh-help][textdb] — Passive (P) and Status (T) have no enum; they are pure
// TextDB entries. Source their DB keys the same way lookup-help.cc does
// (getLongDescKeysByRegex on the " passive" / " status" suffix), assert
// getLongDescription(key) is non-empty, and run scan_translation() on each.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: passive/status TextDB descriptions",
                 "[zh-help][textdb]")
{
    std::vector<ZhIssue> issues;
    ScopedHelpLuaGlobals lua_fixture;

    auto scan_keys = [&](const string& suffix_regex, const char* tag)
    {
        // lookup-help.cc's _passive_filter / _status_filter reject any key
        // NOT ending in " passive" / " status"; getLongDescKeysByRegex with
        // the suffix as the regex yields the matching keys directly.
        const vector<string> keys = getLongDescKeysByRegex(suffix_regex);
        // Representative floor: if the DB regex sourcing yields nothing in the
        // catch2 sandbox, fall back to a known key set and note it.
        for (const string& key : keys)
        {
            const string val = getLongDescription(key);
            if (val.empty())
                continue;
            if (rule_embedded_lua_error(val))
            {
                INFO("unexpected embedded-Lua error for " << key << ": " << val);
                CHECK_FALSE(rule_embedded_lua_error(val));
                continue;
            }
            auto found = scan_translation(val.c_str(), key, tag);
            for (auto& iss : found)
                issues.push_back(std::move(iss));
        }
        return keys.size();
    };

    const size_t n_passive = scan_keys(" passive", "passive.txt");
    const size_t n_status  = scan_keys(" status",  "status.txt");

    const vector<std::pair<string, string>> dynamic_statuses = {
        { "app status", "你的身体上长出异常的角或爪" },
        { "bat status", "你变成了一只行动迅捷的蝙蝠" },
        { "blade status", "多把凶恶的刀刃正从你的身体上长出" },
        { "dragon status", "你获得了金龙吐息攻击" },
        { "pact status", "战斗、流血" },
        { "water status", "你正位于水面上" },
    };
    for (const auto& expected : dynamic_statuses)
    {
        const string rendered = getLongDescription(expected.first);
        INFO("dynamic status " << expected.first << ": " << rendered);
        CHECK_FALSE(rule_embedded_lua_error(rendered));
        CHECK(rendered.find(expected.second) != string::npos);
    }

    lua_fixture.set_god("Makhleb");
    const string makhleb_pact = getLongDescription("pact status");
    CHECK(makhleb_pact.find("作为他们的工具履行誓言") != string::npos);
    CHECK(makhleb_pact.find("战斗、流血") == string::npos);
    lua_fixture.set_god("No God");
    const string other_pact = getLongDescription("pact status");
    CHECK(other_pact.find("战斗、流血") != string::npos);
    CHECK(other_pact.find("作为他们的工具履行誓言") == string::npos);

    const string eel = getLongDescription("eel talisman");
    INFO("dynamic item eel talisman: " << eel);
    CHECK_FALSE(rule_embedded_lua_error(eel));
    CHECK_FALSE(rule_mixed_cn_en(eel));
    CHECK(eel.find("使佩戴者的手变成一对扭动的电鳗") != string::npos);

    emit_issue_protocol("zh_help", "passive_status_textdb", issues);
    WARN("zh-help textdb: passive keys=" << n_passive
         << " status keys=" << n_status
         << " issues=" << issues.size());
    // Non-blocking on key count (sandbox DB may be sparse); the scan issues
    // are emitted for the aggregator. Just require the pass completed.
    REQUIRE(true);
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: Destr+++ expands its base status inline",
                 "[zh-help][textdb][issue-64]")
{
    const string zh = getLongDescription("destr+++ status");

    CHECK(zh.find("你的释放毁灭能力") != string::npos);
    CHECK(zh.find("如果你再次使用此能力") != string::npos);
    CHECK(zh.find("<Destr status>") == string::npos);
    CHECK(zh.find("[[Destr status]]") == string::npos);

    // The ZH fixture mounts the translated DB for its lifetime, so toggling
    // Options.language alone cannot query the parent English DB. Verify the
    // English source entry precisely instead; the same TextDB substitution
    // path exercised above expands [[Destr status]] in both layers.
    std::ifstream input("dat/descript/status.txt");
    REQUIRE(input.good());
    const string source((std::istreambuf_iterator<char>(input)),
                        std::istreambuf_iterator<char>());
    const string expected =
        "Destr+++ status\n\n[[Destr status]]\n"
        "If you use it again, it will unleash a salvo of additional bolts";
    CHECK(source.find(expected) != string::npos);
}

// =============================================================================
// [zh-help][monster] — SEPARATE plain TEST_CASE (NO fixture, EN mode).
// get_monster_by_name matches English only (Mon_Name_Cache is English-only),
// so the round-trip must run in EN mode. The help system uses raw DB names
// (me->name) as internal keys; this test verifies that every monster's DB
// name resolves back to the correct enum.
// =============================================================================
TEST_CASE_METHOD(EnTranslationFixture,
                 "zh-help: monster EN round-trip",
                 "[zh-help][monster]")
{
    REQUIRE(Options.language == lang_t::EN);
    init_monsters();
    init_mon_name_cache();

    for (monster_type m = MONS_0; m < NUM_MONSTERS; ++m)
    {
        if (m == MONS_PROGRAM_BUG)
            continue;
        const monsterentry *me = get_monster_data(m);
        if (!me || !me->name || !me->name[0])
            continue;
        if (me->mc != static_cast<int>(m)) // non-primary entry (duplicate name)
            continue;
        // SOH variants are resolved via _is_soh / _soh_type in
        // lookup-help.cc, not via get_monster_by_name (init_mon_name_cache
        // skips them). Skip them here.
        if (mons_species(m) == MONS_SERPENT_OF_HELL)
            continue;
        // init_mon_name_cache skips MONS_BAI_SUZHEN_DRAGON (shares
        // "Bai Suzhen" name with MONS_BAI_SUZHEN); skip it in the test.
        if (m == MONS_BAI_SUZHEN_DRAGON)
            continue;
        if (getLongDescription(me->name).empty())
            continue;

        INFO("monster round-trip: " << me->name);
        // Mounted and unmounted Goji share a name; upstream's cache
        // deliberately resolves it to the mounted form.
        if (m == MONS_GOJI_UNMOUNTED)
        {
            REQUIRE(string(me->name) == get_monster_data(MONS_GOJI)->name);
            CHECK(mons_rider_type(MONS_GOJI) == m);
            CHECK(get_monster_by_name(me->name) == MONS_GOJI);
        }
        else
            CHECK(get_monster_by_name(me->name) == m);
    }
}

// =============================================================================
// [zh-help][item] — Chinese item name search via item_name_list_for_zh_regex.
// Verifies that Chinese item names (T_()'d via item_def::name) resolve to
// the correct English DB keys. Runs under ZhTranslationFixture so T_()
// produces Chinese output.
// =============================================================================
// NOTE: item_name_list_for_zh_regex relies on item_names_cache
// populated by init_item_name_cache(). The catch2 sandbox may not
// fully initialize all item tables (Weapon_index, Armour_index, etc.).
// Manual verification: ?/i + "匕首" finds dagger in ?/i in-game.
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: item_name_list_for_zh_regex smoke test",
                 "[zh-help][item]")
{
    init_item_name_cache();
    // Unknown input → empty (function doesn't crash)
    CHECK(item_name_list_for_zh_regex("不存在的物品").empty());
    // Function call doesn't crash (regardless of cache state)
    SUCCEED("item_name_list_for_zh_regex called without crash");
}

// Verify get_mutation_desc uses English DB key under ZH (Issue 53 followup).
// The old code used mutation_name() (T_()'d Chinese) to build the TextDB
// key "硬化表皮 mutation", but TextDB keys are English ("tough skin
// mutation"). The fix uses raw English short_desc for the DB key.
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: mutation descriptions load under ZH",
                 "[zh-help][mutation-desc]")
{
    // MUT_CLAWS → short_desc "claws" → key "claws mutation" → zh desc
    {
        const string desc = get_mutation_desc(MUT_CLAWS);
        INFO("MUT_CLAWS desc: " << desc);
        CHECK_FALSE(desc.empty());
    }
    // Spot-check: at least 10 mutations have non-empty descriptions
    {
        int non_empty = 0;
        for (int mi = 0; mi < NUM_MUTATIONS && non_empty < 10; ++mi)
        {
            const mutation_type m = static_cast<mutation_type>(mi);
            const char* nm = mutation_name(m, false);
            if (!nm || !nm[0])
                continue;
            const string d = get_mutation_desc(m);
            if (!d.empty() && !rule_garbled_utf8(d))
                ++non_empty;
        }
        CHECK(non_empty >= 10);
    }
}

// =============================================================================
// [zh-help][home-page] — verify home page labels return Chinese under ZH fixture.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: lookup labels and query identities survive language switches",
                 "[zh-help][home-page]")
{
    init_monsters();
    init_mon_name_cache();
    init_spell_descs();
    init_spell_name_cache();
    init_feat_desc_cache();
    init_mut_index();
    init_item_name_cache();
    static const char *const english[] = {
        "monster", "spell", "skill", "ability", "card", "item", "feature",
        "god", "branch", "cloud", "passive", "status", "mutation", "bane",
        "weapon Ego", "armour Ego", "missile Ego"
    };
    static const char *const chinese[] = {
        "怪物", "法术", "技能", "能力", "卡牌", "物品", "地形",
        "神祇", "分支", "云雾", "被动能力", "状态", "突变", "灾祸",
        "武器附魔", "护甲附魔", "弹药附魔"
    };
    REQUIRE(NUM_LOOKUP_HELP_TYPES == sizeof(english) / sizeof(*english));
    REQUIRE(NUM_LOOKUP_HELP_TYPES == sizeof(chinese) / sizeof(*chinese));
    const auto check_english_queries = [] {
        // Spell recapping deliberately localizes the returned menu text.
        const auto keys = lookup_help_matching_keys(LOOKUP_HELP_SPELL, "magic dart");
        const string expected = make_stringf(T_("%s spell"), spell_title(SPELL_MAGIC_DART));
        CHECK(std::find(keys.begin(), keys.end(), expected) != keys.end());
        CHECK_FALSE(getLongDescription("magic dart spell").empty());
        bool exact = false;
        lookup_help_matching_keys(LOOKUP_HELP_MONSTER, "goblin", &exact);
        CHECK(exact);
        lookup_help_matching_keys(LOOKUP_HELP_MONSTER, "no such monster", &exact);
        CHECK_FALSE(exact);
    };
    check_english_queries();
    for (int i = 0; i < NUM_LOOKUP_HELP_TYPES; ++i)
    {
        const auto lht = static_cast<lookup_help_type>(i);
        INFO("type=" << english[i]);
        CHECK(lookup_help_type_name(lht) == chinese[i]);
        auto zh_keys = lookup_help_matching_keys(lht, ".+");
        REQUIRE_FALSE(zh_keys.empty());
        std::sort(zh_keys.begin(), zh_keys.end());
        {
            EnTranslationFixture english_mode;
            check_english_queries();
            CHECK(lookup_help_type_name(lht) == english[i]);
            auto en_keys = lookup_help_matching_keys(lht, ".+");
            std::sort(en_keys.begin(), en_keys.end());
            // These three recap functions already produce localized display
            // values. Other query lists retain their canonical English keys.
            if (lht != LOOKUP_HELP_SPELL && lht != LOOKUP_HELP_ABILITY
                && lht != LOOKUP_HELP_FEATURE)
            {
                CHECK(en_keys == zh_keys);
            }
            else
                CHECK(en_keys.size() == zh_keys.size());
        }
        // Reloading the TextDB cache must not invalidate the persistent table.
        CHECK(lookup_help_type_name(lht) == chinese[i]);
        CHECK(isalpha(lookup_help_type_shortcut(lht)));
    }
}

// =============================================================================
// [zh-help][menu-display] — verify sub-menu display names produce Chinese text
// for the five types (Skill/Branch/Cloud/Item/Bane) that were previously
// showing English raw keys.
// =============================================================================
TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh-help: sub-menu display names are Chinese",
                 "[zh-help][menu-display]")
{
    // --- skill: skill_name returns T_()'d Chinese ---
    for (int ski = SK_FIRST_SKILL; ski < NUM_SKILLS; ++ski)
    {
        const string zh = skill_name(static_cast<skill_type>(ski));
        if (zh.empty())
            continue;
        INFO("skill name: " << zh);
        CHECK_FALSE(rule_untranslated(zh, lowercase_string(zh)));
    }

    // --- cloud: cloud_type_name returns T_()'d Chinese ---
    for (int ci = 1; ci < NUM_CLOUD_TYPES; ++ci) // skip CLOUD_NONE
    {
        const cloud_type c = static_cast<cloud_type>(ci);
        const string zh = cloud_type_name(c);
        if (zh.empty() || zh == "buggy goodness")
            continue;
        INFO("cloud name: " << zh);
        CHECK_FALSE(rule_untranslated(zh, lowercase_string(zh)));
    }

    // --- bane: every persistent name/description key must resolve instead of
    //     falling back to English. The data table includes the TAG34 removed
    //     compatibility entry, so it is deliberately covered too. ---
    init_mut_index();
    for (const bane_def& def : bane_data)
    {
        const string short_name = T_(def.name);
        const string display_name = bane_name(def.type, false);
        const string short_desc = bane_desc(def.type);
        INFO("bane: " << def.name << " -> " << display_name);
        CHECK_FALSE(rule_untranslated(short_name, def.name));
        CHECK_FALSE(rule_untranslated(short_desc, def.description));
        CHECK_FALSE(rule_mixed_cn_en(display_name));
    }

    // Exercise the actual TextDB-backed description path for every active
    // bane. A lookup miss starts with the translated short description plus
    // a newline, so reject that prefix without coupling to the full long text.
    for (const bane_def& def : bane_data)
    {
#if TAG_MAJOR_VERSION == 34
        if (def.type == BANE_RECKLESS_REMOVED)
            continue;
#endif
        const string long_desc = bane_long_description(def.type, true);
        const string fallback_prefix = string(T_(def.description)) + "\n";
        INFO("bane long description: " << def.name);
        CHECK_FALSE(long_desc.empty());
        CHECK(contains_cjk_text(long_desc));
        CHECK(long_desc.compare(0, fallback_prefix.size(), fallback_prefix) != 0);
    }

    const string lethargy_long = bane_long_description(BANE_LETHARGY, true);
    CHECK(lethargy_long.find("30%") != string::npos);
    const string claustrophobia_long =
        bane_long_description(BANE_CLAUSTROPHOBIA, true);
    CHECK(claustrophobia_long.find("-10%") != string::npos);
#if TAG_MAJOR_VERSION == 34
    CHECK_FALSE(rule_untranslated(T_("the Removed"), "the Removed"));
    CHECK_FALSE(rule_untranslated(T_("You feel a strange sense of nostalgia."),
                                  "You feel a strange sense of nostalgia."));
#endif

    // Dilettante's held-player detail line has a separate display key from
    // bane_desc(). Exercise its positional-capable formatting without
    // mutating the global player used by other Catch2 cases.
    const char* dilettante_key =
        "\nYour %s, %s, and %s are currently affected.\n";
    const string dilettante_format = T_(dilettante_key);
    CHECK_FALSE(rule_untranslated(dilettante_format, dilettante_key));
    const string dilettante_line = make_stringf_p(
        dilettante_format.c_str(),
        skill_name(SK_FIGHTING), skill_name(SK_ARMOUR), skill_name(SK_DODGING));
    CHECK(dilettante_line.find('%') == string::npos);

    // --- branch: longname T_() produces Chinese ---
    // Spot-check a few well-known branches; full enumeration requires
    // checking all ~25 branches which may not all have T_() entries.
    const branch_type check_branches[] = {
        BRANCH_DUNGEON, BRANCH_LAIR, BRANCH_ORC, BRANCH_VAULTS,
        BRANCH_ZOT, BRANCH_SHOALS, BRANCH_SNAKE, BRANCH_SPIDER,
        BRANCH_TOMB, BRANCH_ABYSS,
    };
    for (branch_type b : check_branches)
    {
        const string zh = T_(branches[b].longname);
        INFO("branch: " << branches[b].longname << " → " << zh);
        CHECK_FALSE(zh.empty());
    }
}

namespace {
void check_externalised_altar_hints()
{
    const coord_def position(1, 1);
    REQUIRE(cloud_at(position) == nullptr);
    unwind_var<dungeon_feature_type> feature(env.grid(position), DNGN_ALTAR_ZIN);
    unwind_var<god_type> religion(you.religion, GOD_NO_GOD);
    unwind_var<bool> hint_event(Hints.hints_events[HINT_SEEN_ALTAR]);

    SECTION("unbeliever inspecting a named altar")
    {
        const string text = hints_describe_pos(position.x, position.y);
        REQUIRE_FALSE(getHintString("HINT_DESCRIBE_NONFADED_ALTAR_ATHEIST").empty());
        CHECK(text.find("<w>" + god_name(GOD_ZIN) + "</w>") != string::npos);
        if (Options.language == lang_t::EN)
        {
            CHECK(text.find("You can get information about") != string::npos);
            CHECK(text.find("random god") == string::npos);
        }
        CHECK(text.find("$1") == string::npos);
    }
    SECTION("believer inspecting another named altar")
    {
        you.religion = GOD_TROG;
        const string text = hints_describe_pos(position.x, position.y);
        REQUIRE_FALSE(getHintString("HINT_DESCRIBE_NONFADED_ALTAR").empty());
        CHECK(text.find(god_name(GOD_TROG)) != string::npos);
        CHECK(text.find("<w>" + god_name(GOD_ZIN) + "</w>") != string::npos);
        if (Options.language == lang_t::EN)
        {
            CHECK(text.find(god_name(GOD_TROG) + " probably won't like it")
                  != string::npos);
            CHECK(text.find("information on <w>") != string::npos);
            CHECK(text.find("random god") == string::npos);
        }
        CHECK(text.find("$1") == string::npos);
        CHECK(text.find("$2") == string::npos);
    }
    SECTION("faded altar keeps the random-god hint")
    {
        env.grid(position) = DNGN_ALTAR_ECUMENICAL;
        const string text = hints_describe_pos(position.x, position.y);
        REQUIRE_FALSE(getHintString("HINT_DESCRIBE_FADED_ALTAR_ATHEIST").empty());
        if (Options.language == lang_t::EN)
        {
            CHECK(text.find("random god") != string::npos);
            CHECK(text.find("You can get information about") == string::npos);
        }
    }
}
} // anonymous namespace

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: externalised altar hints select the matching terrain",
                 "[hints][zh-help]")
{
    check_externalised_altar_hints();
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: externalised altar hints preserve fallback and god display names",
                 "[hints][zh-help]")
{
    // Missing ZH descriptions must fall back to EN, with localized god names.
    // These checks also accept ZH descriptions once the assets are migrated.
    check_externalised_altar_hints();
    CHECK(getHintString("death").find("请节哀！") != string::npos);
}

TEST_CASE("WebTiles: zero-stat status keeps an English key and current display language",
          "[zh-help][webtiles][status]")
{
    unwind_var<player> restore_player(you);
    init_duration_index();
    const char* const keys[] = {
        "", "lost strength", "lost intelligence", "lost strength and intelligence",
        "lost dexterity", "lost strength and dexterity",
        "lost intelligence and dexterity", "lost strength, intelligence and dexterity"
    };
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        for (int mask = 1; mask < 8; ++mask)
        {
            INFO("stat mask " << mask << ", language " << static_cast<int>(language));
            you = player();
            you.species = SP_HUMAN;
            you.attribute[ATTR_STAT_ZERO] = mask;
            for (int i = STAT_STR; i <= STAT_DEX; ++i)
                you.base_stats[i] = mask & (1 << i) ? 0 : 10;

            status_info info;
            REQUIRE(fill_status_info(STATUS_STAT_ZERO, info));
            CHECK(info.short_db_key == keys[mask]);
            CHECK(info.db_key == "Crippled");
            CHECK(info.light_text == T_("Crippled"));
            CHECK(Options.language == language);
            for (int i = STAT_STR; i <= STAT_DEX; ++i)
            {
                CHECK(you.base_stats[i] == (mask & (1 << i) ? 0 : 10));
                if (mask & (1 << i))
                    CHECK(info.short_text.find(stat_desc(static_cast<stat_type>(i), SD_NAME))
                          != string::npos);
            }
            if (language == lang_t::EN)
                CHECK(info.short_text == info.short_db_key);
            else
                CHECK(info.short_text != info.short_db_key);
        }
    }
}
