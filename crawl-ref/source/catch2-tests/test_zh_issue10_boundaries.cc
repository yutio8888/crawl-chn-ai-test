#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "act-iter.h"
#include "areas.h"
#include "abyss.h"
#include "branch.h"
#include "dgn-overview.h"
#include "mapmark.h"
#include "map-knowledge.h"
#include "map-cell.h"
#include "macro.h"
#include "terrain.h"
#include "output.h"
#include "view.h"
#include "beam.h"
#include "cloud.h"
#include "libutil.h"
#include "syscalls.h"
#include "viewgeom.h"
#include "clua.h"
#include "unicode.h"
#include "database.h"
#include "describe.h"
#include "directn.h"
#include "dungeon.h"
#include "english.h"
#include "env.h"
#include "format.h"
#include "ghost.h"
#include "fight.h"
#include "hiscores.h"
#include "lang-en-guard.h"
#include "melee-attack.h"
#include "notes.h"
#include "positional_format.h"
#include "target.h"
#include "i18n.h"
#include "invent.h"
#include "item-prop.h"
#include "item-status-flag-type.h"
#include "item-use.h"
#include "items.h"
#include "losglobal.h"
#include "message.h"
#include "mon-death.h"
#include "mon-info.h"
#include "mon-place.h"
#include "mon-util.h"
#include "movement-i18n.h"
#include "movement.h"
#include "mutation.h"
#include "options.h"
#include "player.h"
#include "player-notices.h"
#include "positional_format.h"
#include "player-equip.h"
#include "random.h"
#include "ranged-attack.h"
#include "religion-enum.h"
#include "spl-monench.h"
#include "spl-cast.h"
#include "spl-selfench.h"
#include "spl-summoning.h"
#include "spl-util.h"
#include "state.h"
#include "skills.h"
#include "status.h"
#include "skills.h"
#include "random.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "transform.h"
#include "unwind.h"
#include "xom.h"

#include <clocale>
#include <functional>
#include <tuple>

#ifdef UNIX
#include <sys/stat.h>
#include <unistd.h>
#include <sys/wait.h>
#endif

#include "fprop.h"
#include "describe-spells.h"
#include "cleansing-flame-source-type.h"
#include "spl-damage.h"
#include "spl-goditem.h"
#include "spl-transloc.h"
#include "spl-miscast.h"

#include "fineff.h"
#include "mon-project.h"
#include "shout.h"
#include "tags.h"
#include "mon-cast.h"
#include "mon-abil.h"

#include "artefact.h"
#include "art-enum.h"
#include "decks.h"
#include "traps.h"
#include "item-name.h"
#include "place.h"
#include "religion.h"
#include "shopping.h"
#include "stash.h"
#include "ability.h"
#include "god-abil.h"
#include "god-wrath.h"
#include "kills.h"
#include "files.h"
#include "dgn-shoals.h"
#include "wiz-fsim.h"
#include "wiz-item.h"
#include <cstdio>
#include <utility>

namespace
{
// Reuse the real allocator and the small lit-floor fixture convention from
// the monspeak consumer tests. Multiple actors let targeting and constriction
// run through their actual mid/foe lookup paths.
struct issue10_world
{
    // Rebind after saved_player restores its props, not to the temporary player.
    unwinder restore_shopping{[] { shopping_list.refresh(); }};
    unwind_var<player> saved_player{you};
    unwind_var<bool> saved_test{crawl_state.test, true};
    unwind_var<bool> saved_started{crawl_state.game_started, false};
    const mid_t old_last_mid = you.last_mid;
    const int old_max_mon_index = env.max_mon_index;
    const map<mid_t, unsigned short> old_mid_cache = env.mid_cache;
    vector<tuple<coord_def, dungeon_feature_type, unsigned short, uint32_t>> cells;
    vector<monster *> monsters;

    issue10_world()
    {
        init_properties();
        init_monsters();
        init_spell_descs();
        you = player();
        shopping_list.refresh();
        you.last_mid = old_last_mid;
        you.species = SP_HUMAN;
        you.hp = you.hp_max = 100;
        you.on_current_level = true;
        you.current_vision = LOS_DEFAULT_RANGE;
        you.wizard_vision = true;
        for (int x = 15; x <= 30; ++x)
            for (int y = 15; y <= 30; ++y)
            {
                const coord_def p(x, y);
                cells.emplace_back(p, env.grid(p), env.mgrid(p),
                                   env.level_map_ids(p));
                env.grid(p) = DNGN_FLOOR;
                env.mgrid(p) = NON_MONSTER;
                env.level_map_ids(p) = INVALID_MAP_INDEX;
            }
        you.set_position(coord_def(20, 20));
        invalidate_los();
        invalidate_agrid();
    }

    ~issue10_world()
    {
        for (monster *m : monsters)
            m->reset();
        env.mid_cache = old_mid_cache;
        env.max_mon_index = old_max_mon_index;
        for (const auto &cell : cells)
        {
            env.grid(get<0>(cell)) = get<1>(cell);
            env.mgrid(get<0>(cell)) = get<2>(cell);
            env.level_map_ids(get<0>(cell)) = get<3>(cell);
        }
        invalidate_los();
        invalidate_agrid();
    }

    monster *place(monster_type type, coord_def p)
    {
        monster *m = get_free_monster();
        REQUIRE(m);
        monsters.push_back(m);
        m->type = type;
        m->set_hit_dice(1);
        m->hit_points = m->max_hit_points = 50;
        m->speed = 10;
        m->base_attitude = ATT_HOSTILE;
        m->behaviour = BEH_SEEK;
        m->foe = MHITYOU;
        m->set_position(p);
        m->set_new_monster_id();
        // This test exercises messages and movement, not cloud placement.
        m->props[FAKE_BLINK_KEY] = true;
        env.mgrid(p) = m->mindex();
        return m;
    }
};

string observe_message(const std::function<void()> &emit)
{
    string raw;
    {
        msg::tee capture(raw);
        emit();
    }
    REQUIRE_FALSE(raw.empty());
    // tee observes this invocation before final capitalization and history
    // filtering. A consumer may emit more than one line (e.g. movement then
    // an encounter), so retain all of its actual emissions and strip markup.
    return formatted_string::parse_string(raw).tostring();
}

// Observe the actual prompt at the supported Lua answer hook, and decline it
// before any interactive UI or gameplay continuation can run.
struct action_prompt_capture
{
    string prompt;
    lua_State *ls = clua.state();
    int previous;

    action_prompt_capture()
    {
        lua_getglobal(ls, "c_answer_prompt");
        previous = luaL_ref(ls, LUA_REGISTRYINDEX);
        lua_pushlightuserdata(ls, &prompt);
        lua_pushcclosure(ls, [](lua_State *state) -> int
        {
            auto *text = static_cast<string*>(lua_touserdata(state, lua_upvalueindex(1)));
            *text = luaL_checkstring(state, 1);
            lua_pushboolean(state, false);
            return 1;
        }, 1);
        lua_setglobal(ls, "c_answer_prompt");
    }

    ~action_prompt_capture()
    {
        lua_rawgeti(ls, LUA_REGISTRYINDEX, previous);
        lua_setglobal(ls, "c_answer_prompt");
        luaL_unref(ls, LUA_REGISTRYINDEX, previous);
    }
};

string target_description(const monster &m, bool ally_target)
{
    monster_info mi(m.type);
    mi.pos = m.pos();
    mi.attitude = m.attitude();
    if (ally_target)
        mi.mb.set(MB_ALLY_TARGET);
    describe_info info;
    bool has_stats = false;
    get_monster_db_desc(mi, info, has_stats);
    REQUIRE(has_stats);
    return info.body.str();
}
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 10 display verbs keep base keys and context",
                 "[zh-translation][issue10]")
{
    monster mon;
    // These singular-form keys have different or missing translations. A
    // conjugate-then-lookup implementation cannot pass these checks.
    CHECK(mon.verb_for_display(NC_("verb", "are"), "verb") == "被");
    CHECK(mon.verb_for_display(N_("blast")) == "冲击");
    CHECK(mon.verb_for_display(N_("drown")) == "溺亡");
    CHECK(you.verb_for_display(N_("blast")) == "冲击");
    CHECK(conjugate_verb_for_display(N_("glow"), false) == "发亮");
    CHECK(conjugate_verb_for_display(N_("glow"), true) == "发亮");
    // Empty and absent entries both take an English-only morphology path.
    CHECK(conjugate_verb_for_display("are", false) == "is");
    CHECK(conjugate_verb_for_display("make room", false) == "makes room");
    CHECK(conjugate_verb_for_display("make room", true) == "make room");
    const string owned = mon.verb_for_display(N_("blast"));
    i18n_cache_clear();
    CHECK(owned == "冲击");
    CHECK(Options.language == lang_t::ZH);
}

TEST_CASE_METHOD(EnTranslationFixture,
                 "en: issue 10 actor and body-part agreement is unchanged",
                 "[zh-translation][issue10]")
{
    issue10_world world;
    monster mon;
    CHECK(mon.verb_for_display(NC_("verb", "are"), "verb") == "is");
    CHECK(you.verb_for_display(NC_("verb", "are"), "verb") == "are");
    CHECK(mon.verb_for_display(N_("blast")) == "blasts");
    CHECK(you.verb_for_display(N_("blast")) == "blast");
    CHECK(you.hands_act("get", "new energy.") == "Your hands get new energy.");
    CHECK(you.hands_act("burn", "!") == "Your hands burn!");
    you.mutation[MUT_MISSING_HAND] = 1;
    CHECK(you.hands_act("get", "new energy.") == "Your hand gets new energy.");
    CHECK(you.hands_act("are", "glowing red.") == "Your hand is glowing red.");
}

TEST_CASE_METHOD(ZhTranslationFixture,
                 "zh: issue 10 hands actions are complete localized sentences",
                 "[zh-translation][issue10]")
{
    issue10_world world;
    const auto row = GENERATE(table<const char *, const char *, const char *>({
        {"get", "new energy.", "你的%s焕发出新的活力。"},
        {"stop", "glowing.", "你的%s不再发光了。"},
        {"slow", "down.", "你的%s慢了下来。"},
        {"burn", "!", "你的%s一阵灼痛！"},
        {"tingle", "!", "你的%s一阵发麻！"},
        {"look", "sharp.", "你的%s看起来很锋利。"},
        {"are", "glowing red.", "你的%s正发出红光。"},
        {"are", "covered in slime.", "你的%s覆满了黏液。"},
        {"begin", "to glow red.", "你的%s开始发出红光。"},
        {"begin", "to glow brighter.", "你的%s开始发出更亮的光芒。"},
    }));
    const string message = you.hands_act(get<0>(row), get<1>(row));
    CAPTURE(message);
    CHECK(message == make_stringf(get<2>(row), you.hand_name(true).c_str()));
    CHECK(message.find(you.hand_name(true)) != string::npos);
    CHECK(message.find_first_of("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ")
          == string::npos);
    // An unknown complete action must not combine Chinese hands with an
    // untranslated English predicate, and must retain singular agreement.
    you.mutation[MUT_MISSING_HAND] = 1;
    CHECK(you.hands_act("make", "room.") == "Your hand makes room.");
    CHECK(Options.language == lang_t::ZH);
}

TEST_CASE("issue 10 Confusing Touch emits both complete action variants",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const string first = observe_message([] { cast_confusing_touch(30, false); });
    const string second = observe_message([] { cast_confusing_touch(30, false); });
    if (language == lang_t::ZH)
    {
        CHECK(first.find("begin") == string::npos);
        CHECK(first.find("red") == string::npos);
        CHECK(second.find("brighter") == string::npos);
        CHECK(first.find("你的" + you.hand_name(true) + "开始发出红光。")
              != string::npos);
        CHECK(second.find("你的" + you.hand_name(true) + "开始发出更亮的光芒。")
              != string::npos);
    }
    else
    {
        CHECK(first.find("Your hands begin to glow red.") != string::npos);
        CHECK(second.find("Your hands begin to glow brighter.") != string::npos);
    }
    CHECK(you.duration[DUR_CONFUSING_TOUCH] > 0);
}

TEST_CASE("issue 10 cloud and armour consumers use display verbs",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *mon = world.place(MONS_ORC, coord_def(20, 21));
    cloud_struct cloud;
    cloud.type = CLOUD_RAIN;
    const string rain = observe_message([&] { cloud.announce_actor_engulfed(mon); });
    CHECK(rain.find(language == lang_t::ZH ? "嘶嘶作响" : "sizzles") != string::npos);
    cloud.type = CLOUD_FIRE;
    const string fire = observe_message([&] { cloud.announce_actor_engulfed(mon); });
    CHECK(fire.find(language == lang_t::ZH ? "被吞没" : "is engulfed") != string::npos);

    item_def armour;
    armour.base_type = OBJ_ARMOUR;
    armour.sub_type = ARM_ROBE;
    armour.quantity = 1;
    armour.plus = 0;
    const string glow = observe_message([&] { REQUIRE(enchant_armour(armour, false)); });
    CHECK(glow.find(language == lang_t::ZH ? "泛起绿光" : "glows green") != string::npos);
    CHECK(armour.plus == 1);
}

TEST_CASE("item action messages preserve armour number and duration",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    const armour_type type = GENERATE(ARM_ROBE, ARM_FIRE_DRAGON_ARMOUR);
    const bool final_enchantment = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    item_def armour;
    armour.base_type = OBJ_ARMOUR;
    armour.sub_type = type;
    armour.quantity = 1;
    armour.plus = final_enchantment ? armour_max_enchant(armour) - 1 : 0;
    const int old_plus = armour.plus;
    const string message = observe_message([&] { REQUIRE(enchant_armour(armour, false)); });
    CAPTURE(language, type, message);
    CHECK(armour.plus == old_plus + 1);
    if (language == lang_t::ZH)
    {
        CHECK(message.find("泛起绿光，持续了") != string::npos);
        CHECK(message.find(final_enchantment ? T_("while") : T_("moment")) != string::npos);
        CHECK(message.find("发亮绿色") == string::npos);
    }
    else
    {
        CHECK(message.find(type == ARM_ROBE ? " glows green" : " glow green") != string::npos);
        CHECK(message.find(final_enchantment ? "for a while." : "for a moment.") != string::npos);
    }
}

TEST_CASE("item action inventory counts use language appropriate number",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    struct count_menu : InvMenu
    {
        count_menu() : InvMenu(MF_MULTISELECT | MF_PAGED_INVENTORY) {}
        using InvMenu::get_select_count_string;
        void add_selected(const item_def &item)
        {
            InvEntry *entry = new InvEntry(item);
            add_entry(entry);
            entry->selected_qty = 1;
            sel.push_back(entry);
        }
    } menu;
    CHECK(menu.get_select_count_string(0).empty());
    item_def items[2];
    for (int i = 0; i < 2; ++i)
    {
        items[i].base_type = OBJ_POTIONS;
        items[i].sub_type = POT_CURING;
        items[i].quantity = 1;
        items[i].link = i;
        menu.add_selected(items[i]);
        CHECK(menu.get_selitems(true).size() == static_cast<size_t>(i + 1));
        CHECK(menu.get_select_count_string(i + 1)
              == (language == lang_t::ZH ? make_stringf(" %d件物品", i + 1)
                                        : i == 0 ? " 1 item" : " 2 items"));
    }
}

TEST_CASE("item action flight removal warnings translate the actual terrain risk",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    const dungeon_feature_type terrain = GENERATE(DNGN_DEEP_WATER, DNGN_LAVA);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    item_def &ring = you.inv[0];
    ring.base_type = OBJ_JEWELLERY;
    ring.sub_type = RING_FLIGHT;
    ring.quantity = 1;
    ring.link = 0;
    ring.pos = ITEM_IN_INVENTORY;
    ring.flags |= ISFLAG_IDENTIFIED;
    equip_item(SLOT_RING, 0, false, true);
    REQUIRE(you.equip_flight() == 1);
    env.grid(you.pos()) = terrain;
    const string message = observe_message([&]
    {
        CHECK_FALSE(warn_about_changing_gear({&ring}, nullptr, true));
    });
    CAPTURE(language, terrain, message);
    CHECK(message.find(ring.name(DESC_YOUR)) != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(message.find(terrain == DNGN_DEEP_WATER ? "溺水" : "被灼烧") != string::npos);
        CHECK(message.find("drown") == string::npos);
        CHECK(message.find("burn") == string::npos);
    }
    else
        CHECK(message.find(terrain == DNGN_DEEP_WATER ? "drown!" : "burn!") != string::npos);
    CHECK(you.equip_flight() == 1);
}

TEST_CASE("navigation feature descriptions translate the Pandemonium wall at the sink",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const string description = feature_description(DNGN_ROCK_WALL, "", DESC_PLAIN,
                                                   level_id(BRANCH_PANDEMONIUM, 1));
    CHECK(description == T_("wall of the weird stuff which makes up Pandemonium"));
    if (language == lang_t::ZH)
        CHECK(description.find("Pandemonium") == string::npos);
}

TEST_CASE("navigation ice movement warnings preserve both active effects",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    const int effects = GENERATE(1, 2, 3);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    world.place(MONS_ORC, coord_def(21, 20));
    you.duration[DUR_ICY_ARMOUR] = effects & 1 ? 50 : 0;
    you.duration[DUR_FROZEN_RAMPARTS] = effects & 2 ? 50 : 0;
    action_prompt_capture capture;
    CHECK(cancel_harmful_move(false));
    const char *expected = effects == 3
        ? "Your icy armour and frozen ramparts will break if you move. Continue?"
        : effects == 1 ? "Your icy armour will break if you move. Continue?"
                       : "Your frozen ramparts will break if you move. Continue?";
    CAPTURE(language, effects, capture.prompt);
    CHECK(capture.prompt == T_(expected));
    if (language == lang_t::ZH)
    {
        CHECK(capture.prompt.find("icy armour") == string::npos);
        CHECK(capture.prompt.find("frozen ramparts") == string::npos);
    }
    CHECK(you.duration[DUR_ICY_ARMOUR] == (effects & 1 ? 50 : 0));
    CHECK(you.duration[DUR_FROZEN_RAMPARTS] == (effects & 2 ? 50 : 0));
}

TEST_CASE("navigation confusion prompts preserve ally and penance clauses",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    const bool stationary = GENERATE(false, true);
    const bool penance = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *ally = world.place(MONS_ORC, coord_def(21, 20));
    ally->base_attitude = ATT_FRIENDLY;
    you.religion = penance ? GOD_ELYVILON : GOD_NO_GOD;
    you.duration[DUR_CONF] = 50;
    action_prompt_capture capture;
    CHECK_FALSE(check_confused_move(stationary));
    CAPTURE(language, stationary, penance, capture.prompt);
    CHECK(capture.prompt.find(ally->name(DESC_PLAIN)) != string::npos);
    CHECK(capture.prompt.find(T_(stationary ? "swing wildly" : "stumble around")) != string::npos);
    CHECK((capture.prompt.find(T_(" This could place you under penance!")) != string::npos) == penance);
    if (language == lang_t::ZH)
    {
        CHECK(capture.prompt.find("the ") == string::npos);
        CHECK(capture.prompt.find("while confused") == string::npos);
        CHECK(capture.prompt.find("你的") != string::npos);
    }
    else
        CHECK(capture.prompt.find("while confused and next to your ") != string::npos);
    CHECK(ally->hit_points == 50);
    CHECK(you.duration[DUR_CONF] == 50);
}

TEST_CASE("navigation water beam uses its display context",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    bolt beam;
    beam.flavour = beam.real_flavour = BEAM_WATER;
    CHECK(beam.get_short_name() == C_("beam flavour", "water"));
    CHECK(beam.get_short_name() == (language == lang_t::ZH ? "水" : "water"));
    CHECK(beam.flavour == BEAM_WATER);
}

TEST_CASE("item action hit labels remain distinct from successful hits",
          "[zh-translation][actions-rereview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH, lang_t::EN);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    for (attack_type type : {AT_HIT, AT_WEAP_ONLY, AT_CHERUB, AT_RANDOM,
#if TAG_MAJOR_VERSION == 34
                             AT_SHOOT,
#endif
                            })
    {
        CHECK(mon_attack_name_short(type) == (language == lang_t::ZH ? "击打" : "hit"));
    }
    CHECK(mon_attack_name(AT_HIT, true) == (language == lang_t::ZH ? "击中" : "hit"));
}

TEST_CASE("issue 10 blink escapes use contextual movement at the real sink",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const auto row = GENERATE(table<monster_type, bool, const char *>({
        {MONS_BULLFROG, true, "hop"}, {MONS_ORC, true, "leap"},
        {MONS_ORC, false, "blink"},
    }));
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *constrictor = world.place(MONS_BALL_PYTHON, coord_def(21, 21));
    monster *mon = world.place(get<0>(row), coord_def(20, 21));
    constrictor->start_constricting(*mon, CONSTRICT_MELEE);
    REQUIRE(mon->is_constricted());
    const string movement = language == lang_t::ZH
        ? translated_move_phrase(get<2>(row), move_phrase_context::bare)
        : mon->conj_verb(get<2>(row));
    const string escape = observe_message([&] {
        REQUIRE(mon->blink_to(coord_def(20, 22), false, get<1>(row)));
    });
    CAPTURE(language, movement, escape);
    CHECK_FALSE(mon->is_constricted());
    CHECK_FALSE(constrictor->is_constricting());
    CHECK(mon->pos() == coord_def(20, 22));
    string constrictor_name = constrictor->name(DESC_THE);
    lowercase(constrictor_name);
    const string expected_escape = language == lang_t::ZH
        ? mon->name(DESC_THE) + movement + "挣脱了"
          + constrictor_name + "！"
        : mon->name(DESC_THE) + " " + movement + " free of "
          + constrictor_name + "!";
    CHECK(escape.find(expected_escape) != string::npos);
    if (language == lang_t::ZH)
        CHECK(escape.find(movement + "s") == string::npos);

    const string announcement = observe_message([&] {
        REQUIRE(mon->blink_to(coord_def(20, 23), false, get<1>(row)));
    });
    // Chinese joins the name and verb directly and uses the full-width
    // exclamation mark; English keeps its ASCII separator and mark.
    const string announcement_expected = language == lang_t::ZH
        ? mon->name(DESC_THE)
          + (get<1>(row) ? movement + "！" : "闪烁了一下！")
        : mon->name(DESC_THE) + " " + movement + "!";
    CAPTURE(language, movement, announcement);
    CHECK(announcement.find(announcement_expected) != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(announcement.find(movement + "s") == string::npos);
        // PT61: no ASCII separator before the verb, no half-width mark.
        CHECK(announcement.find(mon->name(DESC_THE) + " ") == string::npos);
        CHECK(announcement.find(movement + " ") == string::npos);
        CHECK(announcement.find("!") == string::npos);
        CHECK(announcement.find("！") != string::npos);
    }
}

TEST_CASE("playtest: ordinary constriction escapes use complete display sentences",
          "[zh-translation][playtest-fixes][constriction]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool player_victim = GENERATE(false, true);
    const constrict_type type = GENERATE(CONSTRICT_MELEE, CONSTRICT_BVC,
                                         CONSTRICT_ROOTS, CONSTRICT_ENTANGLE);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *constrictor = world.place(MONS_BALL_PYTHON, coord_def(21, 21));
    actor *victim = player_victim ? static_cast<actor *>(&you)
        : world.place(MONS_ORC, coord_def(20, 21));
    constrictor->start_constricting(*victim, type);
    REQUIRE(victim->is_constricted());
    const string attacker = type == CONSTRICT_BVC ? T_("the zombie hands")
        : type == CONSTRICT_ROOTS ? T_("the grasping roots")
        : type == CONSTRICT_ENTANGLE ? T_("the vines")
        : constrictor->name(DESC_THE);
    const string name = victim->name(DESC_THE);
    const mid_t id = victim->mid;
    const string expected = player_victim
        ? make_stringf(T_("You break free of %s!"), attacker.c_str())
        : make_stringf(T_("%s breaks free of %s!"), name.c_str(), attacker.c_str());
    const string escaped = observe_message([&] { victim->stop_being_constricted(); });
    CHECK(escaped == expected + "\n");
    if (language == lang_t::EN)
    {
        CHECK(escaped == (player_victim ? "You break" : name + " breaks")
                         + " free of " + attacker + "!\n");
    }
    else
        CHECK(escaped.find("break") == string::npos);
    CHECK_FALSE(victim->is_constricted());
    CHECK_FALSE(constrictor->is_constricting());
    CHECK(victim->mid == id);
    CHECK(victim->name(DESC_THE) == name);
}

TEST_CASE("playtest: player escape movement retains its grammar context",
          "[zh-translation][playtest-fixes][constriction]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const char *verb = GENERATE("blink", "hop", "leap");
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *constrictor = world.place(MONS_BALL_PYTHON, coord_def(21, 21));
    constrictor->start_constricting(you, CONSTRICT_MELEE);
    REQUIRE(you.is_constricted());
    const string movement = language == lang_t::ZH
        ? translated_move_phrase(verb, move_phrase_context::bare) : verb;
    const string player_name = you.name(DESC_THE);
    const string attacker = constrictor->name(DESC_THE);
    const string expected = make_stringf(T_("%s %s free of %s!"),
        player_name.c_str(), movement.c_str(), attacker.c_str());
    const string escaped = observe_message([&] {
        you.stop_being_constricted(false, verb);
    });
    CHECK(escaped == expected + "\n");
    CHECK_FALSE(you.is_constricted());
    CHECK_FALSE(constrictor->is_constricting());
}

TEST_CASE("issue 10 monster target descriptions preserve direction and list shape",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *target = world.place(MONS_ORC, coord_def(20, 21));
    monster *ally = world.place(MONS_HOBGOBLIN, coord_def(21, 21));
    ally->base_attitude = ATT_FRIENDLY;
    ally->foe = target->mindex();
    const string single = target_description(*target, true);
    const string active = target_description(*ally, false);
    CHECK(single.find(ally->name(DESC_YOUR)) != string::npos);
    CHECK(active.find(target->name(DESC_THE)) != string::npos);

    monster *other = world.place(MONS_GOBLIN, coord_def(22, 21));
    other->base_attitude = ATT_FRIENDLY;
    other->foe = target->mindex();
    const string multiple = target_description(*target, true);
    CHECK(multiple.find("  " + ally->name(DESC_YOUR) + "\n") != string::npos);
    CHECK(multiple.find("  " + other->name(DESC_YOUR) + "\n") != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(single.find("当前被" + ally->name(DESC_YOUR) + "锁定。\n")
              != string::npos);
        CHECK(active.find("当前正锁定" + target->name(DESC_THE) + "。\n")
              != string::npos);
        CHECK(multiple.find("当前被以下单位锁定：\n") != string::npos);
        CHECK(single.find("are") == string::npos);
        CHECK(active.find("are") == string::npos);
        CHECK(multiple.find("are") == string::npos);
    }
    else
    {
        CHECK(single.find("It is currently targeted by ") != string::npos);
        CHECK(active.find("It is currently targeting ") != string::npos);
        CHECK(multiple.find("It is currently targeted by:\n") != string::npos);
    }
}

TEST_CASE("issue 10 penetration weapon messages suppress English verb slots",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const int index = get_mitm_slot();
    REQUIRE(index != NON_ITEM);
    unwind_var<item_def> restore_item(env.item[index]);
    item_def &bow = env.item[index];
    bow.base_type = OBJ_WEAPONS;
    bow.sub_type = WPN_LONGBOW;
    bow.quantity = 1;
    bow.brand = SPWPN_PENETRATION;
    monster *mon = world.place(MONS_ORC, coord_def(20, 21));
    const string monster_message = observe_message([&] {
        REQUIRE(mon->pickup_item(bow, true, true));
    });
    CHECK(mon->weapon() == &bow);
    if (language == lang_t::ZH)
    {
        CHECK(monster_message.find("短暂地穿过了它") != string::npos);
        CHECK(monster_message.find("才将它握稳") != string::npos);
        CHECK(monster_message.find("pass") == string::npos);
        CHECK(monster_message.find("manage") == string::npos);
    }
    else
        CHECK(monster_message.find("briefly pass through it") != string::npos);

    item_def &player_bow = you.inv[0];
    player_bow.base_type = OBJ_WEAPONS;
    player_bow.sub_type = WPN_LONGBOW;
    player_bow.quantity = 1;
    player_bow.brand = SPWPN_PENETRATION;
    player_bow.link = 0;
    player_bow.pos = ITEM_IN_INVENTORY;
    const string player_message = observe_message([&] {
        equip_item(SLOT_WEAPON, 0);
    });
    REQUIRE(you.weapon() == &player_bow);
    if (language == lang_t::ZH)
    {
        CHECK(player_message.find("短暂地穿过了它") != string::npos);
        CHECK(player_message.find("随后你才将它握稳") != string::npos);
        CHECK(player_message.find("pass") == string::npos);
    }
    else
        CHECK(player_message.find("Your hands briefly pass through it") != string::npos);
}

TEST_CASE("issue 10 Tukima unarmed failure formats the complete hand action",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *mon = world.place(MONS_ORC, coord_def(20, 21));
    REQUIRE_FALSE(mon->weapon());
    const string message = observe_message([&] { cast_tukimas_dance(30, mon); });
    if (language == lang_t::ZH)
    {
        CHECK(message.find(mon->hand_name(true) + "抽动了一下。") != string::npos);
        CHECK(message.find("twitch") == string::npos);
    }
    else
        CHECK(message.find("hands twitch.") != string::npos);
    CHECK_FALSE(mon->weapon());
}

TEST_CASE("issue 10 Xom cleave blessing names the equipped weapon",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const weapon_type weapon = GENERATE(WPN_HAND_AXE, WPN_DAGGER);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    item_def &item = you.inv[0];
    item.base_type = OBJ_WEAPONS;
    item.sub_type = weapon;
    item.quantity = 1;
    item.link = 0;
    item.pos = ITEM_IN_INVENTORY;
    equip_item(SLOT_WEAPON, 0, false, true);
    REQUIRE(you.weapon() == &item);
    const string message = observe_message([] { xom_take_action(XOM_BLESSING_CLEAVE, 10); });
    CAPTURE(language, message);
    // The blessing message names the wielded weapon and describes its new
    // brand; the exact sentence differs per randomly chosen brand.
    CHECK(message.find(item.name(DESC_YOUR)) != string::npos);
    CHECK(you.attribute[ATTR_XOM_BLESSING] == XOM_BLESSING_CLEAVE);
    CHECK(you.props.exists(XOM_CLEAVE_BRAND_KEY));
}

TEST_CASE("monster wand drops localize articles only at the death message sink",
          "[zh-translation][playtest-fixes][wand-drop]")
{
    const monster_type type = GENERATE(MONS_ELEIONOMA, MONS_FENSTRIDER_WITCH);
    issue10_world world;
    const coord_def pos(20, 21);
    unwind_var<int> saved_grid(env.igrid(pos), NON_ITEM);
    const string identity = mons_type_name_en(type, DESC_PLAIN);
    item_def english_drop;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        rng::subgenerator scoped_rng(0x221023ddULL, 0x221023eeULL);
        REQUIRE(you.see_cell(pos));
        string message = observe_message([&] {
            maybe_drop_monster_organ(type, type, pos, false);
        });
        trim_string_right(message);
        const int index = env.igrid(pos);
        REQUIRE(index != NON_ITEM);
        unwinder cleanup([index] { destroy_item(index); });
        const item_def &drop = env.item[index];
        CHECK(drop.base_type == OBJ_WANDS);
        CHECK(drop.quantity == 1);
        CHECK(drop.plus > 0);
        CHECK((drop.flags & ISFLAG_IDENTIFIED) == ISFLAG_IDENTIFIED);
        CHECK(drop.link == NON_ITEM);
        CHECK(mons_type_name_en(type, DESC_PLAIN) == identity);

        // The production message precedes identification of this item. Recover
        // that display state from the actual drop, rather than guessing its
        // randomly chosen type or appearance.
        item_def unidentified = drop;
        unidentified.flags &= ~ISFLAG_IDENTIFIED;
        const string subject = mons_type_name(type, language == lang_t::ZH
                                                    ? DESC_PLAIN : DESC_A);
        const string expected = make_stringf(T_("%s's bones magically twist into %s."),
                                            subject.c_str(),
                                            unidentified.name(DESC_A).c_str());
        INFO("actual death message: " << message);
        CHECK(message == expected);
        if (language == lang_t::EN)
        {
            english_drop = drop;
            CHECK((message.find("an " + identity + "'s bones") == 0
                   || message.find("a " + identity + "'s bones") == 0));
        }
        else
        {
            // Reject the original mixed-language a/an prefix independently
            // of the complete-template comparison above.
            CHECK(message.find(subject) == 0);
            CHECK(message.find("a ") != 0);
            CHECK(message.find("an ") != 0);
            CHECK(drop.sub_type == english_drop.sub_type);
            CHECK(drop.plus == english_drop.plus);
            CHECK(drop.quantity == english_drop.quantity);
            CHECK(drop.flags == english_drop.flags);
            CHECK(drop.rnd == english_drop.rnd);
        }
    }
}

TEST_CASE("family: real player escape attempts consume every constrictor possessive once",
          "[zh-translation][family-fixes][constriction]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const constrict_type type = GENERATE(CONSTRICT_MELEE, CONSTRICT_BVC,
                                         CONSTRICT_ROOTS, CONSTRICT_ENTANGLE);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *constrictor = world.place(MONS_BALL_PYTHON, coord_def(21, 21));
    rng::subgenerator scoped_rng(20261025, 7);
    bool succeeded = false;
    bool failed = false;
    for (int trial = 0; trial < 40 && !(succeeded && failed); ++trial)
    {
        you.duration[DUR_CONSTRICTION_IMMUNITY] = 0;
        constrictor->start_constricting(you, type);
        REQUIRE(you.is_constricted());
        you.escape_attempts = 0;
        bool escaped = false;
        const string text = observe_message([&] { escaped = you.attempt_escape(); });
        INFO(text);
        succeeded |= escaped;
        failed |= !escaped;
        CHECK(you.is_constricted() == !escaped);
        if (language == lang_t::ZH)
        {
            CHECK(text.find("的的") == string::npos);
            CHECK(text.find("的对") == string::npos);
            CHECK(text.find(escaped ? "挣脱了" : "束缚减弱") != string::npos);
        }
        else
        {
            CHECK(text.find("'s's") == string::npos);
            CHECK(text.find(escaped ? "You break free of" : "hold on you weakens") != string::npos);
            if (escaped)
                CHECK(text.find("grasp.") != string::npos);
        }
        if (!escaped)
            you.stop_being_constricted(true);
    }
    CHECK(succeeded);
    CHECK(failed);
}

TEST_CASE("family: real clockwork bee target and dormancy messages keep owner grammar",
          "[zh-translation][family-fixes][bee]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool player_owner = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *target = world.place(MONS_ORC, coord_def(21, 21));
    monster *bee = world.place(MONS_CLOCKWORK_BEE, coord_def(20, 21));
    bee->base_attitude = ATT_FRIENDLY;
    bee->summoner = player_owner ? MID_PLAYER : MID_NOBODY;
    bee->props[CLOCKWORK_BEE_TARGET].get_int() = target->mid;
    const string targeted = observe_message([&] { clockwork_bee_pick_new_target(*bee); });
    INFO(targeted);
    CHECK(bee->props[CLOCKWORK_BEE_TARGET].get_int() == target->mid);
    CHECK(bee->has_ench(ENCH_HAUNTING));
    if (language == lang_t::ZH)
    {
        CHECK(targeted.find("的的") == string::npos);
        CHECK(targeted.find(player_owner ? "你的发条蜜蜂" : "某人的发条蜜蜂") != string::npos);
    }
    else
    {
        CHECK(targeted.find("your's") == string::npos);
        CHECK(targeted.find("someone's's") == string::npos);
    }
    bee->add_ench(mon_enchant(ENCH_SUMMON_TIMER, &you, 300));
    const string dormant = observe_message([&] { clockwork_bee_go_dormant(*bee); });
    INFO(dormant);
    CHECK(bee->type == MONS_CLOCKWORK_BEE_INACTIVE);
    CHECK(bee->get_ench(ENCH_SUMMON_TIMER).duration <= 120);
    if (language == lang_t::ZH)
    {
        CHECK(dormant.find("Your") == string::npos);
        CHECK(dormant.find("The") == string::npos);
        CHECK(dormant.find("的的") == string::npos);
        CHECK(dormant.find("发条蜜蜂") != string::npos);
    }
    else
        CHECK(dormant.find(player_owner ? "Your clockwork bee" : "The clockwork bee") != string::npos);
}

TEST_CASE("family: real monster bee launch and interrupted winding use a subject and one owner",
          "[zh-translation][family-fixes][bee]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *caster = world.place(MONS_ORC_WIZARD, coord_def(21, 21));
    caster->props[CLOCKWORK_BEE_TARGET].get_int() = MID_PLAYER;
    const string launched = observe_message([&] { launch_clockwork_bee(*caster); });
    INFO(launched);
    monster *bee = nullptr;
    for (monster_iterator mi; mi; ++mi)
        if (mi->type == MONS_CLOCKWORK_BEE && mi->summoner == caster->mid)
        {
            bee = *mi;
            world.monsters.push_back(bee);
        }
    REQUIRE(bee);
    CHECK(bee->props[CLOCKWORK_BEE_TARGET].get_int() == MID_PLAYER);
    if (language == lang_t::ZH)
    {
        CHECK(launched.find("的的") == string::npos);
        CHECK(launched.find("发条蜜蜂") != string::npos);
    }
    else
        CHECK(launched.find("clockwork bee launches itself at you") != string::npos);

    caster->add_ench(mon_enchant(ENCH_CLOCKWORK_BEE_CAST, caster, 100));
    caster->behaviour = BEH_SLEEP;
    const string interrupted = observe_message([&] { caster->apply_enchantments(); });
    INFO(interrupted);
    CHECK_FALSE(caster->has_ench(ENCH_CLOCKWORK_BEE_CAST));
    if (language == lang_t::ZH)
    {
        CHECK(interrupted.find("的停止") == string::npos);
        CHECK(interrupted.find("的的") == string::npos);
        CHECK(interrupted.find("停止") != string::npos);
    }
    else
    {
        CHECK(interrupted.find("wizard stops winding") != string::npos);
        CHECK(interrupted.find("wizard's stops") == string::npos);
    }
}


TEST_CASE("playtest: zero-damage roots keep the damage suffix localized",
          "[zh-translation][playtest-followups][constriction]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *victim = world.place(MONS_ORC, coord_def(21, 20));
    you.props[FASTROOT_POWER_KEY] = 10;
    you.start_constricting(*victim, CONSTRICT_ROOTS);
    REQUIRE(victim->is_constricted());
    REQUIRE_FALSE(victim->has_invalid_constrictor());
    // Force only the final timescale to zero; execute the real damage and
    // message producer rather than reconstructing its template in the test.
    you.time_taken = 0;
    const int hp = victim->hit_points;
    const string message = observe_message([&] { you.handle_constriction(); });
    CHECK(victim->hit_points == hp);
    CHECK(message.find(string(T_(" but do no damage")) + T_(".")) != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(message.find(" but do no damage") == string::npos);
        CHECK(message.find("根须") != string::npos);
    }
    else
        CHECK(message.find(" but do no damage.") != string::npos);
    victim->stop_being_constricted(true);
}

namespace
{
struct blocked_ranged_probe : ranged_attack
{
    using ranged_attack::ranged_attack;
    // Public base interface retains virtual dispatch to the production
    // ranged override, without simulating accuracy or shield-block RNG.
    using attack::handle_phase_blocked;
};
}

TEST_CASE("playtest: reflected blocks place shield method before the Chinese action",
          "[zh-translation][playtest-followups][reflection]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int protection = GENERATE(0, 1, 2, 3);
    CAPTURE(language, protection);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *shooter = world.place(MONS_ORC, coord_def(21, 20));
    item_def projectile;
    projectile.base_type = OBJ_MISSILES;
    projectile.sub_type = MI_STONE;
    projectile.quantity = 1;
    projectile.rnd = 1;
    projectile.pos = coord_def(-1, -1);
    if (protection == 1 || protection == 3)
    {
        item_def &item = you.inv[0];
        item.base_type = protection == 1 ? OBJ_JEWELLERY : OBJ_ARMOUR;
        item.sub_type = protection == 1 ? static_cast<int>(AMU_REFLECTION)
                                        : static_cast<int>(ARM_BUCKLER);
        item.brand = protection == 1 ? 0 : SPARM_REFLECTION;
        item.quantity = 1;
        item.rnd = 1;
        item.link = 0;
        item.pos = ITEM_IN_INVENTORY;
        item.flags = ISFLAG_IDENTIFIED;
        you.equipment.add(item, protection == 1 ? SLOT_AMULET : SLOT_OFFHAND);
        you.equipment.update();
    }
    if (protection == 2)
        you.duration[DUR_DIVINE_SHIELD] = 10;
    REQUIRE(you.reflection() == (protection != 0));
    blocked_ranged_probe shot(shooter, &you, &projectile);
    shot.needs_message = true;
    const string proj = make_stringf(T_("the %s"),
                                     shot.projectile_name().c_str());
    const int hp = you.hp;
    const string message = observe_message([&] { shot.handle_phase_blocked(); });
    INFO(message);
    CHECK(you.hp == hp);
    CHECK(shot.damage_done == 0);
    CHECK(shot.reflected == (protection != 0));
    CHECK(shot.range_used == (protection ? 0 : BEAM_STOP));
    // Block and reflection messages are produced by the shared
    // block_event_string() helper, which translates complete sentences.
    CHECK(message == block_event_string(&you, proj, protection != 0) + "\n");
    if (language == lang_t::ZH)
    {
        CHECK(message.find(" block ") == string::npos);
        CHECK(message.find("blocks") == string::npos);
        CHECK(message.find("reflect") == string::npos);
    }
}

// These checks exercise the actual producers. Until the translator lands the
// keys they verify EN output and ZH fallback; the same assertions automatically
// exercise the translated templates once source.txt contains them.
TEST_CASE("trunk sync mutation catalyst refusals use complete display keys",
          "[trunk-sync][messages]")
{
    for (bool zh : {false, true})
    {
        TranslationFixture language(zh ? lang_t::ZH : lang_t::EN,
                                    zh ? "zh" : nullptr);
        issue10_world world;
        const char *keys[] = {
            "Zin forbids you from drinking this foul brew!",
            "You must return to life before you may mutate.",
            "Sadly, you cannot mutate.",
        };
        for (int i = 0; i < 3; ++i)
        {
            you.religion = i == 0 ? GOD_ZIN : GOD_NO_GOD;
            you.form = i == 1 ? transformation::death : transformation::none;
            you.mutation[MUT_MUTATION_RESISTANCE] = i == 2 ? 3 : 0;
            const string expected = T_(keys[i]);
            const string actual = observe_message([] { use_mutation_catalyst(); });
            INFO(actual);
            CHECK(actual.find(expected) != string::npos);
            if (!zh)
                CHECK(expected == keys[i]);
        }
    }
}

TEST_CASE("trunk sync wind and enchantment expiry use display keys",
          "[trunk-sync][messages]")
{
    for (bool zh : {false, true})
    {
        TranslationFixture language(zh ? lang_t::ZH : lang_t::EN,
                                    zh ? "zh" : nullptr);
        issue10_world world;
        monster *mon = world.place(MONS_ORC, coord_def(21, 20));
        const string name = mon->name(DESC_THE);
        const string exposed = make_stringf(T_("A bitter wind exposes %s."), name.c_str());
        CHECK(observe_message([&] { east_wind_expose_monster(mon); }).find(exposed)
              != string::npos);
        CHECK(observe_message([&] { mon->del_ench(ENCH_EXPOSED); }).find(
                  name + T_(" is no longer exposed.")) != string::npos);
        mon->add_ench(mon_enchant(ENCH_STAMPEDE, mon, INFINITE_DURATION));
        CHECK(observe_message([&] { mon->del_ench(ENCH_STAMPEDE); }).find(
                  name + T_(" stops stampeding.")) != string::npos);
        if (!zh)
            CHECK(exposed == "A bitter wind exposes the orc.");
    }
}

TEST_CASE("trunk sync teleport targeting preserves immunity and display lookup",
          "[trunk-sync][targeting]")
{
    for (bool zh : {false, true})
    {
        TranslationFixture language(zh ? lang_t::ZH : lang_t::EN,
                                    zh ? "zh" : nullptr);
        issue10_world world;
        monster_info mi(MONS_ORC);
        mi.mb.set(MB_NO_TELE);
        const pair<spell_type, const char *> cases[] = {
            {SPELL_WARP_SPACE, "immune to blinking"},
            {SPELL_DISPERSAL, "immune to dispersal"},
            {SPELL_TELEPORT_OTHER, "immune to teleportation"},
        };
        for (const auto &c : cases)
        {
            const auto describe = targeter_addl_desc(c.first, 50,
                                                     get_spell_flags(c.first), nullptr);
            REQUIRE(describe);
            const vector<string> actual = describe(mi);
            CHECK(actual == vector<string>{T_(c.second)});
            if (!zh)
                CHECK(actual == vector<string>{c.second});
        }
    }
}

// Explicitly selected after the translator lands the assets; no Chinese test
// literals or temporary edits to the translator-owned source.txt are needed.
TEST_CASE_METHOD(ZhTranslationFixture,
                 "trunk sync translation handoff keys are populated",
                 "[.][trunk-sync-translation-pending]")
{
    const char *keys[] = {
        "\nIt does %dd%d damage.",
        "%s pins %s in place with %s attack.",
        "You perform a powerful leap!",
        "None of your crystals are currently charged.",
        "earthen",
        "fiery",
        "airy",
        "icy",
        "Your %s crystal is infused with energy.",
        "Your %s crystals are infused with energy.",
        " raises briars to defend itself!",
        " vitality is bolstered.",
        "%s starts stampeding towards %s.",
        " is no longer exposed.",
        " stops stampeding.",
        "living %s spell",
        "Doom befalls %s, leaving %s %s.",
        "deeply drained",
        "A bitter wind exposes %s.",
        "Zin forbids you from drinking this foul brew!",
        "You must return to life before you may mutate.",
        "Sadly, you cannot mutate.",
        "You break open the mutation catalyst, and crackling magic pours forth!",
        "You bathe in the mists of the mutagenic serum and feel extremely strange.",
        "Your athame gleams mockingly in your nearly-destroyed state.",
        "Your athame gleams mockingly in your nearly-dead state.",
        "Your athame demands its blood price!",
        "Your athame demands its blood price! (Figuratively speaking.)",
        "%s forbids the use of this item.",
        "%s remembers how to cast %s spells more powerfully.",
        "%s remembers how to pin enemies in place with %s attacks.",
        "%s remembers the full extent of %s fortitude.",
        "immune to blinking",
        "immune to dispersal",
        "immune to teleportation",
        "You cannot harm %s.",
        "A giggling sprite leaps out and plays with %s.",
        " goes berserk!",
        "Mutagenic energy floods into you!",
        "Your body decomposes!",
        "Salvo (%d)",
        "salvo (%d)",
        "You are no longer poisoned.",
        "%s blinded and untethered in space!",
        "%s interlaced with infuriating chaos!",
    };
    for (const char *key : keys)
    {
        INFO(key);
        CHECK(string(T_(key)) != key);
    }
}

TEST_CASE_METHOD(EnTranslationFixture,
                 "trunk sync positional message sinks preserve English grammar",
                 "[trunk-sync][messages]")
{
    issue10_world world;
    CHECK(observe_message([] {
        mprf_p(T_("%s pins %s in place with %s attack."),
               "Your ancestor", "the orc", "its");
    }).find("Your ancestor pins the orc in place with its attack.") != string::npos);
    CHECK(observe_message([] {
        mprf_p(T_("Doom befalls %s, leaving %s %s."),
               "the orc", "it", "deeply drained");
    }).find("Doom befalls the orc, leaving it deeply drained.") != string::npos);
}

TEST_CASE("trunk sync jademantle crystal lists use language-specific separators",
          "[trunk-sync][trunk-sync-jademantle-list][zh-translation]")
{
    unwind_var<player> restore_player(you);
    const int two = (int)spschool::earth | (int)spschool::fire;
    const int three = two | (int)spschool::air;
    for (bool zh : {false, true})
    {
        TranslationFixture language(zh ? lang_t::ZH : lang_t::EN,
                                    zh ? "zh" : nullptr);
        for (int elements : {two, three})
        {
            you.props[JADEMANTLE_CRYSTAL_KEY] = elements;
            lua_State *ls = clua.state();
            lua_stack_cleaner restore_stack(ls);
            REQUIRE(clua.execstring("return you.jademantle_crystals_desc()",
                                   "trunk-sync-jademantle-list", 1) == 0);
            REQUIRE(lua_isstring(ls, -1));
            const string actual = lua_tostring(ls, -1);
            const string expected = zh
                ? (elements == two ? "你的土和火玉晶充满了能量。"
                                   : "你的土、火和气玉晶充满了能量。")
                : (elements == two
                   ? "Your earthen and fiery crystals are infused with energy."
                   : "Your earthen, fiery and airy crystals are infused with energy.");
            INFO(actual);
            CHECK(actual == expected);
        }
    }
}

TEST_CASE("monster encounter equipment retains its subject across locales",
          "[zh-translation][monster-equipment-subject]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    // One monster, distinct monsters, grouped monsters, grouped dancing
    // weapons, a female unique, and a singular neutral-gender character.
    const int scenario = GENERATE(0, 1, 2, 3, 4, 5);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const int first_slot = get_mitm_slot();
    REQUIRE(first_slot != NON_ITEM);
    unwind_var<item_def> restore_first(env.item[first_slot]);
    item_def &first_weapon = env.item[first_slot];
    first_weapon.base_type = OBJ_WEAPONS;
    first_weapon.sub_type = WPN_DAGGER;
    first_weapon.quantity = 1;
    first_weapon.brand = SPWPN_DISTORTION;
    const int second_slot = get_mitm_slot();
    REQUIRE(second_slot != NON_ITEM);
    REQUIRE(second_slot != first_slot);
    unwind_var<item_def> restore_second(env.item[second_slot]);
    env.item[second_slot] = first_weapon;
    env.item[second_slot].sub_type = scenario == 3 ? WPN_DAGGER : WPN_SPEAR;

    const monster_type type = scenario == 3 ? MONS_DANCING_WEAPON
                              : scenario == 4 ? MONS_JESSICA : MONS_ORC;
    monster *first = world.place(type, coord_def(20, 21));
    first->inv[MSLOT_WEAPON] = first_slot;
    first->flags |= MF_WAS_IN_VIEW;
    if (scenario == 5)
        first->props[MON_GENDER_KEY] = GENDER_NEUTRAL;
    vector<monster *> announced = {first};
    if (scenario >= 1 && scenario <= 3)
    {
        monster *second = world.place(scenario == 1 ? MONS_HOBGOBLIN : type,
                                      coord_def(21, 20));
        second->inv[MSLOT_WEAPON] = second_slot;
        second->flags |= MF_WAS_IN_VIEW;
        announced.push_back(second);
    }
    if (scenario == 3)
    {
        for (monster *mon : announced)
        {
            ghost_demon ghost;
            ghost.init_dancing_weapon(*mon->mslot_item(MSLOT_WEAPON), 100);
            mon->set_ghost(ghost);
            mon->ghost_demon_init();
        }
    }

    vector<monster *> no_new_monsters;
    const string emitted = observe_message([&] {
        notice_new_monsters(no_new_monsters, announced);
    });
    CAPTURE(language, scenario, emitted);
    for (monster *mon : announced)
    {
        const bool single = announced.size() == 1;
        const auto level = scenario == 3 ? DESC_WEAPON
                           : single ? DESC_NOTEWORTHY_AND_WEAPON : DESC_NOTEWORTHY;
        const string equipment = get_monster_equipment_desc(monster_info(mon),
                                                            level, DESC_NONE);
        REQUIRE_FALSE(equipment.empty());
        string subject = single ? mon->pronoun(PRONOUN_SUBJECTIVE)
                         : scenario == 3 ? T_("There is")
                         : mon->full_name(scenario == 1 ? DESC_THE : DESC_A);
        if (language == lang_t::EN)
        {
            subject = uppercase_first(subject);
            if (scenario != 3)
                subject += scenario == 5 ? " are" : " is";
            CHECK(emitted.find(subject + " " + equipment + ".") != string::npos);
        }
        else
        {
            CHECK(emitted.find(subject + equipment + "。") != string::npos);
            CHECK(emitted.find(" is ") == string::npos);
            CHECK(emitted.find(" are ") == string::npos);
        }
    }
}

TEST_CASE("sirocco knockback localizes its cause without changing beam identity",
          "[zh-translation][scorching-wind-knockback]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_zap_index();
    unwind_var<use_animations_type> restore_animations(
        Options.use_animations, use_animations_type());
    monster *mon = world.place(MONS_TERENCE, coord_def(21, 20));
    mon->flags |= MF_SEEN | MF_WAS_IN_VIEW;
    mon->hit_points = mon->max_hit_points = 1000;
    bolt wind;
    zappy(ZAP_SIROCCO, 100, false, wind);
    wind.source = you.pos();
    wind.target = mon->pos();
    wind.source_id = MID_PLAYER;
    wind.thrower = KILL_YOU;
    wind.range = 1;
    wind.hit = AUTOMATIC_HIT;
    wind.aimed_at_spot = true;
    wind.origin_spell = SPELL_SIROCCO;
    const string message = observe_message([&] { wind.fire(); });
    CHECK(wind.name == "scorching wind");
    CHECK(mon->pos() == coord_def(23, 20));
    if (language == lang_t::ZH)
    {
        CHECK(message.find("特伦斯被灼热风击退了。") != string::npos);
        CHECK(message.find("scorching wind") == string::npos);
    }
    else
        CHECK(message.find("Terence is knocked back by the scorching wind.")
              != string::npos);
}

namespace
{
struct combat_ranged_consumer : ranged_attack
{
    using ranged_attack::ranged_attack;
    using attack::handle_phase_hit;
};
struct combat_melee_consumer : melee_attack
{
    using melee_attack::melee_attack;
    using attack::announce_hit;
    using attack::handle_phase_hit;
    int calc_damage() override { return 0; }
};
struct combat_fixed_melee : combat_melee_consumer
{
    using combat_melee_consumer::combat_melee_consumer;
    int calc_damage() override { return 4; }
};
}

TEST_CASE("combat rereview: real ranged producers keep score parsing and display separate",
          "[zh-translation][combat-rereview][ranged-protocol]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    monster *source = world.place(MONS_ORC, coord_def(20, 21));
    for (bool launched : {false, true})
    {
        item_def projectile;
        projectile.base_type = launched ? OBJ_WEAPONS : OBJ_MISSILES;
        projectile.sub_type = launched ? static_cast<int>(WPN_SHORTBOW)
                                       : static_cast<int>(MI_STONE);
        projectile.quantity = 1;
        combat_ranged_consumer hit(source, &you, &projectile);
        string projectile_en, attacker_en;
        {
            ScopedLangEn en;
            projectile_en = launched_projectile_name(projectile);
            attacker_en = source->name(DESC_A);
        }
        const string canonical = make_stringf(launched
            ? "Shot with a%s %s by %s" : "Hit by a%s %s thrown by %s",
            is_vowel(projectile_en[0]) ? "n" : "", projectile_en.c_str(),
            attacker_en.c_str());
        REQUIRE(hit.aux_source == canonical);
        scorefile_entry score(3, source->mid, KILLED_BY_BEAM,
                              hit.aux_source.c_str(), true);
        score.init(1600000000);
        const string raw = score.raw_string();
        CHECK(score.get_fields().str_field("kaux") == canonical);
        scorefile_entry loaded;
        REQUIRE(loaded.parse(raw));
        {
            ScopedLangEn en;
            const string terse = loaded.death_description(scorefile_entry::DDV_TERSE);
            CHECK(terse.find("???") == string::npos);
            CHECK(terse.find("orc/" + projectile_en) != string::npos);
        }
        const string display = loaded.death_description(scorefile_entry::DDV_VERBOSE);
        CHECK(display.find(launched_projectile_name(projectile)) != string::npos);
        if (language == lang_t::ZH)
            CHECK(display.find(projectile_en) == string::npos);
        CHECK(loaded.raw_string() == raw);
        CHECK(loaded.get_fields().str_field("kaux") == canonical);
    }
    for (const char* unknown : {"unknown legacy projectile", "wind-blessed future missile"})
        CHECK(projectile_display_name(unknown) == unknown);
}

TEST_CASE("combat rereview: actual disjunction dart stores canonical source after prefix and copy",
          "[zh-translation][combat-rereview][blink-protocol]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    monster *source = world.place(MONS_ORC, coord_def(20, 21));
    item_def dart;
    dart.base_type = OBJ_MISSILES;
    dart.sub_type = MI_DART;
    dart.brand = SPMSL_DISJUNCTION;
    dart.quantity = 1;
    combat_ranged_consumer original(source, &you, &dart);
    original.set_projectile_prefix("wind-blessed");
    combat_ranged_consumer hit(source, &you, &dart);
    original.copy_params_to(hit);
    hit.needs_message = true;
    const string message = observe_message([&] { hit.handle_phase_hit(); });
    CHECK(message.find(T_("You become untethered in space!")) != string::npos);
    REQUIRE(you.duration[DUR_BLINKITIS] > 0);
    string source_en, projectile_en;
    {
        ScopedLangEn en;
        source_en = source->name(DESC_A, true);
        projectile_en = "wind-blessed " + launched_projectile_name(dart);
    }
    CHECK(you.props[BLINKITIS_SOURCE_KEY].get_string() == source_en);
    CHECK(you.props[BLINKITIS_AUX_KEY].get_string() == projectile_en);
    scorefile_entry score(2, source->mid, KILLED_BY_BLINKING, "", true);
    score.init(1600000000);
    const string raw = score.raw_string();
    CHECK(score.get_fields().str_field("killer") == source_en);
    CHECK(score.get_fields().str_field("kaux") == projectile_en);
    CHECK(score.death_description(scorefile_entry::DDV_VERBOSE)
          .find(projectile_display_name(projectile_en)) != string::npos);
    CHECK(score.raw_string() == raw);
}

TEST_CASE("combat rereview: actual body actions use complete predicates for damage and zero damage",
          "[zh-translation][combat-rereview][body-actions]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    struct action { int index; const char* canonical; const char* predicate; bool possessive; };
    const action actions[] = {
        {6, "tickle", "tickles %s", false},
        {14, "eye-gouge", "gouges %s eyes", true},
        {16, "headlock", "locks %s head", true},
        {17, "wrestle", "wrestles with %s", false},
        {19, "kneecap", "strikes %s knees", true},
        {1, "head-knock", "knocks %s head", true},
    };
    monster *source = world.place(MONS_KILLER_KLOWN, coord_def(20, 21));
    monster *victim = world.place(MONS_ORC, coord_def(21, 21));
    const int item_index = get_mitm_slot();
    REQUIRE(item_index != NON_ITEM);
    unwind_var<item_def> restore_item(env.item[item_index]);
    item_def& helmet = env.item[item_index];
    helmet.base_type = OBJ_ARMOUR;
    helmet.sub_type = ARM_HELMET;
    helmet.quantity = 1;
    for (const auto& action : actions)
    for (bool zero_damage : {false, true})
    for (bool player_target : {true, false})
    {
        source->type = string(action.canonical) == "head-knock"
            ? MONS_HAUNTED_ARMOUR : MONS_KILLER_KLOWN;
        source->inv[MSLOT_ARMOUR] = source->type == MONS_HAUNTED_ARMOUR
            ? item_index : NON_ITEM;
        const int choices = source->type == MONS_HAUNTED_ARMOUR ? 3 : 20;
        uint64_t chosen_seed = 0;
        for (uint64_t seed = 1; seed < 512 && !chosen_seed; ++seed)
        {
            rng::subgenerator probe(seed, 0x434f4d424154ULL);
            if (random2(choices) == action.index) chosen_seed = seed;
        }
        REQUIRE(chosen_seed != 0);
        actor* target = player_target ? static_cast<actor*>(&you) : victim;
        const int hp_before = player_target ? you.hp : victim->hit_points;
        combat_melee_consumer hit(source, target);
        hit.needs_message = hit.attacker_visible = hit.defender_visible = true;
        hit.attk_type = AT_HIT;
        hit.attk_flavour = AF_PLAIN;
        hit.damage_done = 7;
        string output;
        {
            rng::subgenerator random(chosen_seed, 0x434f4d424154ULL);
            output = observe_message([&] {
                if (zero_damage) hit.handle_phase_hit();
                else hit.announce_hit();
            });
        }
        CAPTURE(action.canonical, zero_damage, player_target, output);
        if (language == lang_t::ZH)
        {
            const string target = action.possessive ? apostrophise(hit.defender_name(true))
                                                    : hit.defender_name(true);
            const string predicate = make_stringf(C_("monster body action", action.predicate),
                                                  target.c_str());
            CHECK(output.find(predicate) != string::npos);
            CHECK(output.find(action.canonical) == string::npos);
        }
        else
            CHECK(output.find(source->conj_verb(action.canonical) + " " + hit.defender_name(true)) != string::npos);
        if (zero_damage)
        {
            CHECK(hit.damage_done == 0);
            CHECK((player_target ? you.hp : victim->hit_points) == hp_before);
        }
    }
}

TEST_CASE("combat rereview: real anchor and sap enchantments distinguish initial and renewed duration",
          "[zh-translation][combat-rereview][enchantment-messages]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_duration_index();
    no_notes suppress_notes;
    const auto old_animations = Options.use_animations;
    unwinder restore_animations([&] { Options.use_animations = old_animations; });
    Options.use_animations = use_animations_type();
    for (bool renewal : {false, true})
    {
        you.duration[DUR_DIMENSION_ANCHOR] = renewal ? 1 : 0;
        you.duration[DUR_SAP_MAGIC] = renewal ? 1 : 0;
        for (beam_type flavour : {BEAM_DIMENSION_ANCHOR, BEAM_SAP_MAGIC})
        {
            bolt beam;
            beam.flavour = flavour;
            // Test the real duration/message path without uninitialized UI animations.
            beam.animate = false;
            beam.thrower = KILL_YOU;
            beam.source_id = MID_PLAYER;
            const char* key = flavour == BEAM_DIMENSION_ANCHOR
                ? (renewal ? "You feel more firmly anchored in space."
                           : "You feel firmly anchored in space.")
                : (renewal ? "Your magic feels more tainted." : "Your magic feels tainted.");
            const string output = observe_message([&] { beam.affect_player_enchantment(false); });
            CHECK(output.find(T_(key)) != string::npos);
            if (language == lang_t::ZH) CHECK(output.find("more ") == string::npos);
        }
    }
}

TEST_CASE("combat rereview: actual attack and summoning prompts preserve action and spatial roles",
          "[zh-translation][combat-rereview][prompts]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *ally = world.place(MONS_ORC, coord_def(20, 21));
    ally->base_attitude = ATT_FRIENDLY;
    action_prompt_capture captured;
    for (bool beam : {false, true})
    for (coord_def target : {ally->pos(), coord_def(20, 22)})
    {
        captured.prompt.clear();
        REQUIRE(stop_attack_prompt(ally, beam, target));
        REQUIRE_FALSE(captured.prompt.empty());
        if (language == lang_t::EN)
            CHECK(captured.prompt.find(beam ? "fire " : "attack ") != string::npos);
        else
        {
            CHECK(captured.prompt.find("fire ") == string::npos);
            CHECK(captured.prompt.find("attack ") == string::npos);
            CHECK(captured.prompt.find(ally->name(DESC_PLAIN)) != string::npos);
        }
    }
    targeter_smite area(&you, LOS_RADIUS, 1, 1);
    REQUIRE(area.set_aim(ally->pos()));
    for (const monster* defender : {static_cast<const monster*>(nullptr), static_cast<const monster*>(ally)})
    {
        captured.prompt.clear();
        REQUIRE(stop_attack_prompt(area, "attack", nullptr, nullptr, defender));
        if (language == lang_t::EN)
            CHECK((captured.prompt.find("attack near ") != string::npos) == !defender);
        else
        {
            CHECK(captured.prompt.find(ally->name(DESC_PLAIN)) != string::npos);
            CHECK(captured.prompt.find(" near") == string::npos);
        }
    }
    for (duration_type duration : {DUR_TOXIC_RADIANCE, DUR_NOXIOUS_BOG, DUR_VORTEX, DUR_FUSILLADE})
    {
        you.duration[duration] = 1;
        captured.prompt.clear();
        REQUIRE(stop_summoning_prompt());
        REQUIRE_FALSE(captured.prompt.empty());
        if (language == lang_t::EN) CHECK(captured.prompt.find("Really do that while ") == 0);
        else
        {
            CHECK(captured.prompt.find("do that") == string::npos);
            CHECK(captured.prompt.find(" while ") == string::npos);
        }
        you.duration[duration] = 0;
    }
}

TEST_CASE("playtest: area attack prompts resolve actions in their own context",
          "[zh-translation][playtest-fixes][prompts]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *ally = world.place(MONS_ORC, coord_def(21, 20));
    ally->base_attitude = ATT_FRIENDLY;
    targeter_smite area(&you, LOS_RADIUS, 1, 1);
    REQUIRE(area.set_aim(ally->pos()));
    action_prompt_capture captured;

    const auto prompt_for = [&](const char *verb) -> string
    {
        captured.prompt.clear();
        // The hook declines, so the observed text is the complete final prompt
        // and no gameplay continuation runs.
        stop_attack_prompt(area, verb, nullptr, nullptr);
        return captured.prompt;
    };

    // The action identities the area overload's production callers pass.
    const char *const verbs[] = {
        "attack", "blast", "blind", "conjure a freezing cloud",
        "create a bog", "drain life", "hailstorm", "hurl reagents",
        "intoxicate", "irradiate", "make a polar vortex", "poison",
        "refrigerate", "release a tremorstone", "Slouch", "unravel", "zap",
    };
    for (const char *verb : verbs)
    {
        const string action = C_("attack prompt action", verb);
        const string prompt = prompt_for(verb);
        CAPTURE(language, verb, action, prompt);
        REQUIRE_FALSE(prompt.empty());
        CHECK(prompt.find(action) != string::npos);
        CHECK(prompt.find(ally->name(DESC_PLAIN)) != string::npos);
        if (language == lang_t::ZH)
            CHECK(prompt.find(verb) == string::npos);
        else
            CHECK(prompt.find(verb) != string::npos);
    }

    if (language == lang_t::ZH)
    {
        // The action context must not rewrite the global noun/status keys other
        // sinks share (blind/poison/Hailstorm/Slouch and friends). The sink must
        // use the action phrase rather than the bare shared noun, and must leave
        // the shared key itself untouched.
        for (const char *verb : {"blind", "poison", "hailstorm", "Slouch"})
        {
            const string shared_name = T_(verb);
            const string action = C_("attack prompt action", verb);
            const string prompt = prompt_for(verb);
            // The same display value used as the action identity is what a
            // global-state leak would look like.
            const string bare_prompt = prompt_for(shared_name.c_str());
            CAPTURE(verb, shared_name, action, prompt, bare_prompt);
            REQUIRE(shared_name != verb);
            CHECK(action != shared_name);
            CHECK(prompt.find(action) != string::npos);
            CHECK(prompt != bare_prompt);
            CHECK(T_(verb) == shared_name);
        }
    }

    // Legacy callers pre-translated "attack " with padding; the English
    // identity is normalized before the contextual lookup.
    CHECK(prompt_for("attack") == prompt_for("attack "));

    // "read the %s" reaches this sink already formatted in the current
    // language: that complete display is retained verbatim and never becomes a
    // new action identity.
    const string rendered = make_stringf(T_("read the %s"), T_("scroll"));
    const string rendered_prompt = prompt_for(rendered.c_str());
    CAPTURE(rendered, rendered_prompt);
    CHECK(rendered_prompt.find(rendered) != string::npos);
    if (language == lang_t::ZH)
        CHECK(rendered_prompt.find("read the ") == string::npos);
}

TEST_CASE("playtest: examined stash frame localizes and keeps the item name",
          "[zh-translation][playtest-fixes][stash]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<branch_type> saved_branch(you.where_are_you, BRANCH_DUNGEON);
    unwind_var<int> saved_depth(you.depth, 1);
    const coord_def pos(20, 21);
    const int index = get_mitm_slot();
    REQUIRE(index != NON_ITEM);
    unwind_var<item_def> restore_item(env.item[index]);
    item_def &item = env.item[index];
    item = item_def();
    item.base_type = OBJ_ARMOUR;
    item.sub_type = ARM_SCALE_MAIL;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    item.link = NON_ITEM;
    item.pos = pos;
    unwind_var<int> saved_grid(env.igrid(pos), NON_ITEM);
    env.igrid(pos) = index;
    env.grid(pos) = DNGN_FLOOR;
    // Isolate this case instead of permanently dropping a pre-existing
    // current-level stash: the shared tracker is restored on scope exit.
    unwind_var<StashTracker> saved_stashes(StashTrack, StashTracker());
    StashTrack.add_stash(pos);

    const string name = item.name(DESC_A);
    const string description = get_stash_desc(pos);
    CAPTURE(language, name, description);
    REQUIRE_FALSE(description.empty());
    // The item name is display-only here: the frame is translated around it.
    CHECK(description == make_stringf(T_("[Stash: %s]"), name.c_str()));
    CHECK(description.find(name) != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(description.find("Stash:") == string::npos);
        CHECK(description.find(name) != string::npos);
    }
    else
        CHECK(description == "[Stash: " + name + "]");
}

TEST_CASE("combat rereview: real player melee constriction localizes its subject",
          "[zh-translation][combat-rereview][constriction]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    you.species = SP_OCTOPODE;
    monster *victim = world.place(MONS_ORC, coord_def(21, 20));
    you.start_constricting(*victim, CONSTRICT_MELEE);
    REQUIRE(victim->is_constricted());
    REQUIRE_FALSE(victim->has_invalid_constrictor());
    you.time_taken = 0;
    const int hp = victim->hit_points;
    const string output = observe_message([&] { you.handle_constriction(); });
    CHECK(victim->hit_points == hp);
    CHECK(output.find(T_("You")) != string::npos);
    if (language == lang_t::ZH)
        CHECK(output.find("You") == string::npos);
    victim->stop_being_constricted(true);
}

TEST_CASE("combat rereview: actual hydra decapitation preserves claw and blade semantics",
          "[zh-translation][combat-rereview][decapitation]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_mut_index();
    no_notes suppress_notes;
    you.species = SP_TROLL;
    you.mutation[MUT_CLAWS] = 3;
    you.base_stats.init(10);
    REQUIRE(you.has_claws() >= 3);
    monster* hydra = world.place(MONS_HYDRA, coord_def(20, 21));
    hydra->hit_points = hydra->max_hit_points = 1000;
    item_def blade;
    blade.base_type = OBJ_WEAPONS;
    blade.sub_type = WPN_LONG_SWORD;
    blade.quantity = 1;
    const vector<vector<const char*>> actions = {
        {"rip", "tear", "claw"}, {"slice", "lop", "chop", "hack"}
    };
    for (int kind : {0, 1})
    for (int index = 0; index < static_cast<int>(actions[kind].size()); ++index)
    {
        uint64_t chosen_seed = 0;
        for (uint64_t seed = 1; seed < 512 && !chosen_seed; ++seed)
        {
            rng::subgenerator probe(seed, 0x434f4d48454144ULL);
            if (random2(actions[kind].size()) == index) chosen_seed = seed;
        }
        REQUIRE(chosen_seed != 0);
        hydra->num_heads = 3;
        combat_fixed_melee hit(&you, hydra);
        hit.set_weapon(kind == 0 ? nullptr : &blade);
        hit.needs_message = hit.attacker_visible = hit.defender_visible = true;
        // The real damage/head/message producer runs with a fixed damage roll;
        // simulation suppresses blood scheduling. Player/world state is restored.
        hit.simu = true;
        const string verb = language == lang_t::ZH
            ? C_("decapitation verb", actions[kind][index]) : actions[kind][index];
        string output;
        {
            rng::subgenerator random(chosen_seed, 0x434f4d48454144ULL);
            output = observe_message([&] { hit.handle_phase_hit(); });
        }
        CAPTURE(kind, index, output);
        CHECK(output.find(verb) != string::npos);
        CHECK(hydra->num_heads == 4);
        if (language == lang_t::ZH)
            CHECK(output.find(actions[kind][index]) == string::npos);
    }
}

TEST_CASE("magic rereview: real fragmentation tables keep canonical beam and score names",
          "[zh-translation][magic-rereview][fragmentation]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    struct material { monster_type type; const char* name; };
    const material materials[] = {
        {MONS_TOENAIL_GOLEM, "blast of toenail fragments"},
        {MONS_SALTLING, "blast of salt crystal fragments"},
        {MONS_PILE_OF_DEBRIS, "blast of stone fragments"},
        {MONS_EARTH_ELEMENTAL, "blast of rock fragments"},
        {MONS_IRON_ELEMENTAL, "blast of metal fragments"},
        {MONS_PLATINUM_PARAGON, "blast of platinum fragments"},
        {MONS_JADE_CRYSTAL_AIR, "blast of jade shards"},
        {MONS_GLASS_EYE, "blast of glass shards"},
        {MONS_CRYSTAL_GUARDIAN, "blast of crystal shards"},
        {MONS_ORANGE_STATUE, "blast of orange crystal shards"},
        {MONS_OBSIDIAN_STATUE, "blast of obsidian shards"},
        {MONS_DIAMOND_SAWBLADE, "blast of diamond shards"},
        {MONS_ROXANNE, "blast of sapphire shards"},
    };
    monster* victim = world.place(MONS_TOENAIL_GOLEM, coord_def(20, 21));
    unwind_var<int> sanctuary_time(env.sanctuary_time, 1);
    unwind_var<coord_def> sanctuary_pos(env.sanctuary_pos, victim->pos());
    const auto old_properties = env.pgrid(victim->pos());
    unwinder restore_properties([&] { env.pgrid(victim->pos()) = old_properties; });
    for (const auto& material : materials)
    {
        CAPTURE(material.name);
        // Target eligibility must be checked before sanctuary protects it.
        // Sanctuary is enabled only for the real final explosion display.
        env.pgrid(victim->pos()) &= ~(FPROP_SANCTUARY_1 | FPROP_SANCTUARY_2);
        victim->type = material.type;
        bolt beam;
        REQUIRE(setup_fragmentation_beam(beam, 50, &you, victim->pos(), true, nullptr));
        REQUIRE(beam.name == material.name);
        CHECK(beam.aux_source == material.name);
        const string display = C_("fragmentation blast", material.name);
        // Run the real explosion-name sink. Sanctuary returns before damage,
        // noise or terrain changes, so the fixture tests presentation only.
        beam.target = victim->pos();
        beam.use_target_as_pos = true;
        env.pgrid(victim->pos()) |= FPROP_SANCTUARY_1;
        const string output = observe_message([&] { CHECK(beam.explode(false)); });
        CHECK(output.find(display) != string::npos);
        CHECK(beam.name == material.name);
        CHECK(beam.aux_source == material.name);
        scorefile_entry score(1, victim->mid, KILLED_BY_BEAM, beam.aux_source.c_str(), true);
        score.init(1600000000);
        const string raw = score.raw_string();
        CHECK(score.get_fields().str_field("kaux") == material.name);
        scorefile_entry loaded;
        REQUIRE(loaded.parse(raw));
        CHECK(loaded.death_description(scorefile_entry::DDV_VERBOSE).find(display) != string::npos);
        CHECK(loaded.raw_string() == raw);
        if (language == lang_t::ZH)
        {
            CHECK(display != material.name);
            CHECK(output.find(material.name) == string::npos);
        }
    }
    for (const char* unknown : {"blast of unknown material", "unknown saved explosion"})
        CHECK(fragmentation_name_display(unknown) == unknown);
    for (dungeon_feature_type feature : {DNGN_ROCK_WALL, DNGN_METAL_WALL, DNGN_CRYSTAL_WALL})
    {
        const coord_def target(22, 20);
        // Use the real recoloured-terrain path: this name test has no UI
        // element-colour registry, and must not initialize that global twice.
        unwind_var<unsigned short> colour(env.grid_colours(target), LIGHTGREY);
        env.grid(target) = feature;
        bolt beam;
        REQUIRE(setup_fragmentation_beam(beam, 50, &you, target, true, nullptr));
        CHECK(beam.name == beam.aux_source);
        CHECK(beam.name.find("blast of ") == 0);
        CHECK(fragmentation_name_display(beam.name) == C_("fragmentation blast", beam.name.c_str()));
    }
}

TEST_CASE("magic rereview: cleansing flame sources remain canonical through score capture",
          "[zh-translation][magic-rereview][cleansing-protocol]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    for (cleansing_flame_source source : {cleansing_flame_source::tso, cleansing_flame_source::generic})
    {
        bolt beam;
        setup_cleansing_flame_beam(beam, 20, source, you.pos(), &you);
        const string expected = source == cleansing_flame_source::tso
            ? "the Shining One's cleansing flame" : "cleansing flame";
        CHECK(beam.name == "golden flame");
        CHECK(beam.aux_source == expected);
        scorefile_entry score(1, MID_NOBODY, KILLED_BY_BEAM, beam.aux_source.c_str(), true);
        score.init(1600000000);
        const string raw = score.raw_string();
        CHECK(score.get_fields().str_field("kaux") == expected);
        CHECK(score.death_description(scorefile_entry::DDV_VERBOSE).find(T_(expected.c_str())) != string::npos);
        CHECK(score.raw_string() == raw);
    }
}

#if defined(UNIX) && !defined(USE_TILE)
TEST_CASE("magic rereview: actual LOS spell messages cover player visible and unseen caster",
          "[zh-translation][magic-rereview][los-messages]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    // Ring animation refreshes the console even with animations disabled.
    // The existing headless backend has no teardown; isolate it in a child.
    const pid_t child = fork();
    REQUIRE(child >= 0);
    if (child != 0)
    {
        int status = 0;
        REQUIRE(waitpid(child, &status, 0) == child);
        REQUIRE(WIFEXITED(status));
        REQUIRE(WEXITSTATUS(status) == 0);
        return;
    }
    unwinder fail_child([]() { fflush(nullptr); _exit(1); });
    enter_headless_mode();
    crawl_view.init_geometry();
    cgotoxy(1, 1, GOTO_CRT);
    unwind_var<int> delay(Options.view_delay, 0);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    init_zap_index();
    init_duration_index();
    struct messages { spell_type spell; const char* player; const char* global; const char* visible; const char* unseen; };
    const messages families[] = {
        {SPELL_OZOCUBUS_REFRIGERATION, "The heat is drained from your surroundings.",
         "Something drains the heat from around you.", " drains the heat from the surrounding environment!",
         "The ambient heat is drained!"},
        {SPELL_DRAIN_LIFE, "You draw life from your surroundings.",
         "Something draws the life force from your surroundings.", " draws from the surrounding life force!",
         "The surrounding life force dissipates!"},
        {SPELL_SONIC_WAVE, "You send a blast of sound all around you.",
         "Something sends a blast of sound all around you.", " sends a blast of sound all around you!",
         "Sound blasts the surrounding area!"}
    };
    const auto old_animations = Options.use_animations;
    unwinder restore_animations([&] { Options.use_animations = old_animations; });
    Options.use_animations = use_animations_type();
    // Real callers always supply a player/monster. Null global messages are
    // statically translated; null is not a supported damage/animation caster.
    for (const auto& family : families)
    for (int mode : {0, 2, 3})
    {
        // Drain Life has no player zap/to-hit definition in this branch.
        // Its player/global text is source-covered, not a legal runtime cast.
        if (family.spell == SPELL_DRAIN_LIFE && mode == 0)
            continue;
        CAPTURE(family.spell, mode);
        issue10_world world;
        no_notes suppress_notes;
        you.hp = you.hp_max = 10000;
        monster* caster = world.place(MONS_ORC, coord_def(20, 21));
        caster->hit_points = caster->max_hit_points = 10000;
        if (mode == 3) caster->add_ench(mon_enchant(ENCH_INVIS, caster, 100));
        if (mode >= 2)
        {
            REQUIRE(you.see_cell(caster->pos()));
            REQUIRE(you.can_see(*caster) == (mode == 2));
        }
        const actor* agent = mode == 0 ? static_cast<const actor*>(&you)
                           : mode == 1 ? nullptr : caster;
        const char* key = mode == 0 ? family.player : mode == 1 ? family.global
                          : mode == 2 ? family.visible : family.unseen;
        const string output = observe_message([&] {
            REQUIRE(fire_los_attack_spell(family.spell, 1, agent) == spret::success);
        });
        CAPTURE(family.spell, mode, output);
        REQUIRE(output.find(T_(key)) != string::npos);
        if (language == lang_t::ZH) REQUIRE(output.find(key) == string::npos);
    }
    fflush(nullptr);
    _exit(0);
}
#endif

TEST_CASE("magic rereview: real enhancement consumer covers six complete degrees and zero silence",
          "[zh-translation][magic-rereview][surge]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const char* keys[] = {"You feel an extraordinarily numb sensation.",
        "You feel an extremely numb sensation.", "You feel a numb sensation.",
        "You feel a surge of power!", "You feel a strong surge of power!", "You feel a huge surge of power!"};
    int i = 0;
    for (int degree : {-3, -2, -1, 1, 2, 3})
    {
        const string output = observe_message([&] { surge_power(degree); });
        CHECK(output.find(T_(keys[i])) != string::npos);
        if (language == lang_t::ZH) CHECK(output.find(keys[i]) == string::npos);
        ++i;
    }
    string silent;
    { msg::tee messages(silent); surge_power(0); }
    CHECK(silent.empty());
}

TEST_CASE("magic rereview: JinxBite initial and renewed casts use distinct quantity words",
          "[zh-translation][magic-rereview][jinxbite]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_duration_index();
    no_notes suppress_notes;
    world.place(MONS_ORC, coord_def(20, 21));
    REQUIRE(jinxbite_targets_available());
    for (bool renewal : {false, true})
    {
        you.duration[DUR_JINXBITE] = renewal ? 1 : 0;
        const string expected = make_stringf(T_("You beckon %s vexing sprites to accompany your attacks."),
                                             renewal ? T_("more") : T_("some"));
        const string output = observe_message([&] { CHECK(cast_jinxbite(20, false) == spret::success); });
        CHECK(output.find(expected) != string::npos);
        CHECK(you.duration[DUR_JINXBITE] > 1);
    }
    CHECK(string(T_("more")) != T_("some"));
}

TEST_CASE("magic rereview: real direction consumer translates each compass direction",
          "[zh-translation][magic-rereview][directions]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    const char* keys[] = {"north", "south", "west", "east", "northwest", "northeast", "southwest", "southeast"};
    const coord_def directions[] = {{0,-1}, {0,1}, {-1,0}, {1,0}, {-1,-1}, {1,-1}, {-1,1}, {1,1}};
    for (int i = 0; i < 8; ++i)
    {
        issue10_world world;
        // A stationary caster still emits the real direction message without
        // invoking unrelated player-movement viewport updates.
        you.species = SP_FORMICID;
        REQUIRE(you.stasis());
        const string output = observe_message([&] { CHECK(cast_gavotte(0, directions[i], false) == spret::success); });
        CHECK(output.find(make_stringf(T_("Gravity reorients to the %s!"), T_(keys[i]))) != string::npos);
        if (language == lang_t::ZH) CHECK(output.find(keys[i]) == string::npos);
    }
}

TEST_CASE("magic rereview: monster spell damage duration units come from real description consumers",
          "[zh-translation][magic-rereview][damage-unit]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    init_properties();
    init_monsters();
    init_zap_index();
    init_spell_descs();
    const monster_info owner(MONS_ORC_WIZARD);
    for (spell_type spell : {SPELL_STICKY_FLAME, SPELL_PYRE_ARROW})
    {
        const string description = spell_effect_string(spell, &owner);
        CHECK(description.find(T_("/turn")) != string::npos);
        if (language == lang_t::ZH) CHECK(description.find("/turn") == string::npos);
    }
}

TEST_CASE("magic rereview: real target rejection keeps known unseen and absent targets distinct",
          "[zh-translation][magic-rereview][target-negation]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster* target = world.place(MONS_ORC, coord_def(23, 20));
    target->add_ench(mon_enchant(ENCH_INVIS, target, 100));
    target->flags |= MF_KNOWN_INVISIBLE;
    REQUIRE(you.aware_of(*target));
    REQUIRE_FALSE(you.can_see(*target));
    string reason;
    CHECK_FALSE(valid_electric_charge_target(you, target->pos(), &reason));
    const string expected = make_stringf_p(
        T_("%1$s cannot be targeted properly because %2$s outline is unclear."),
        target->pronoun(PRONOUN_SUBJECTIVE).c_str(),
        target->pronoun(PRONOUN_POSSESSIVE).c_str());
    CHECK(reason == expected);
    CHECK_FALSE(valid_electric_charge_target(you, coord_def(23, 23), &reason));
    CHECK(reason == T_("You can't see anything there to charge at."));
    CHECK(reason != expected);
    target->del_ench(ENCH_INVIS, true);
    REQUIRE(valid_electric_charge_target(you, target->pos(), &reason));
}

TEST_CASE("magic rereview: player and icy special fragments keep their canonical names",
          "[zh-translation][magic-rereview][special-fragments]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_mut_index();
    monster* caster = world.place(MONS_ORC, coord_def(20, 21));
    const char* expected[] = {"blast of rock fragments", "blast of jade fragments",
                              "blast of bone shards", "blast of petrified fragments"};
    for (int branch : {0, 1, 2, 3})
    {
        you.species = branch == 2 ? SP_REVENANT : SP_HUMAN;
        you.form = branch == 0 ? transformation::statue
                   : branch == 1 ? transformation::jademantle : transformation::none;
        you.duration[DUR_PETRIFIED] = branch == 3 ? 1 : 0;
        bolt beam;
        REQUIRE(setup_fragmentation_beam(beam, 50, caster, you.pos(), true, nullptr));
        CHECK(beam.name == expected[branch]);
        CHECK(beam.aux_source == "by Lee's Rapid Deconstruction");
        CHECK(fragmentation_name_display(beam.name) == C_("fragmentation blast", expected[branch]));
    }
    you.species = SP_HUMAN;
    you.form = transformation::none;
    you.duration[DUR_PETRIFIED] = 0;
    caster->type = MONS_ICE_BEAST;
    bolt icy;
    REQUIRE(setup_fragmentation_beam(icy, 50, &you, caster->pos(), true, nullptr));
    CHECK(icy.name == "icy blast");
    CHECK(icy.aux_source == "icy blast");
    CHECK(fragmentation_name_display(icy.name) == C_("fragmentation blast", "icy blast"));
}

TEST_CASE("magic rereview: real forced floor attacks retain attack and glare actions",
          "[zh-translation][magic-rereview][anguish]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    for (int mode : {0, 1, 2})
    {
        issue10_world world;
        no_notes suppress_notes;
        monster* mon = world.place(mode == 2 ? MONS_BUTTERFLY : MONS_ORC, coord_def(20, 21));
        actor& attacker = mode == 0 ? static_cast<actor&>(you) : *mon;
        const string action = mode == 2 ? T_("glares at") : mode == 0 ? T_("attack") : T_("attacks");
        // No aligned actor is adjacent, so the actual forced-ally path must
        // choose the floor/ceiling, without invoking combat damage.
        const string output = observe_message([&] { do_vexed_attack(attacker, true); });
        CHECK(output.find(action) != string::npos);
        if (language == lang_t::ZH)
        {
            CHECK(output.find(T_("summon")) == string::npos);
            CHECK(output.find("glares") == string::npos);
        }
    }
}

TEST_CASE("magic rereview: real servitor initialization uses one forge action for both caster kinds",
          "[zh-translation][magic-rereview][servitor]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    for (bool player_caster : {false, true})
    {
        issue10_world world;
        init_duration_index();
        no_notes suppress_notes;
        monster* caster_mon = world.place(MONS_ORC_WIZARD, coord_def(20, 21));
        caster_mon->spells.emplace_back(SPELL_STONE_ARROW, 10, MON_SPELL_WIZARD);
        monster* servitor = world.place(MONS_SPELLSPARK_SERVITOR, coord_def(21, 20));
        actor* caster = player_caster ? static_cast<actor*>(&you) : caster_mon;
        if (player_caster)
        {
            you.base_stats.init(30);
            you.experience_level = 27;
            for (skill_type skill = SK_FIRST_SKILL; skill < NUM_SKILLS; ++skill)
            {
                you.skills[skill] = 27;
                you.skill_points[skill] = skill_exp_needed(27, skill);
            }
            REQUIRE(add_spell_to_memory(SPELL_STONE_ARROW));
            REQUIRE(player_servitor_spell() == SPELL_STONE_ARROW);
        }
        const string expected = make_stringf_p(C_("servitor creation",
            "%1$s %2$s a servant imbued with %3$s destructive magic!"),
            caster->name(DESC_THE).c_str(), caster->verb_for_display(N_("forge")).c_str(),
            caster->pronoun(PRONOUN_POSSESSIVE).c_str());
        const string output = observe_message([&] { init_servitor(servitor, caster, 50); });
        CHECK(output.find(expected) != string::npos);
        REQUIRE_FALSE(servitor->spells.empty());
        CHECK(servitor->spells[0].spell == SPELL_STONE_ARROW);
        if (language == lang_t::ZH) CHECK(output.find(T_("summon")) == string::npos);
    }
}

TEST_CASE("monster rereview: real gold theft writes canonical marked note and roundtrips both languages",
          "[zh-translation][monster-rereview][gold-theft]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    unwind_var<vector<Note>> saved_notes(note_list);
    const bool was_active = notes_are_active();
    activate_notes(true);
    unwinder restore_active([&] { activate_notes(was_active); });
    note_list.clear();
    monster* thief = world.place(MONS_MAURICE, coord_def(20, 21));
    const int index = get_mitm_slot();
    REQUIRE(index != NON_ITEM);
    unwind_var<item_def> saved_gold(env.item[index]);
    item_def& gold = env.item[index];
    gold.base_type = OBJ_GOLD;
    gold.sub_type = 0;
    gold.quantity = 1;
    gold.set_holding_monster(*thief);
    thief->inv[MSLOT_GOLD] = index;
    you.gold = 10; // every original amount roll steals exactly these ten
    you.attribute[ATTR_GOLD_FOUND] = 10;
    const string output = observe_message([&] { thief->steal_item_from_player(); });
    CHECK(you.gold == 0);
    CHECK(gold.quantity == 11);
    REQUIRE(note_list.size() == 1);
    const Note& note = note_list.back();
    CHECK(note.name == "Maurice stole 10 gold");
    CHECK(note.desc == "gold theft");
    CHECK(note.first == 10);
    vector<unsigned char> bytes;
    writer writer_out(&bytes);
    note.save(writer_out);
    reader input(bytes);
    input.setMinorVersion(TAG_MINOR_VERSION);
    Note loaded;
    loaded.load(input);
    for (lang_t display_language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        unwind_var<lang_t> lang(Options.language, display_language);
        const string display = loaded.describe(false, false, true);
        if (display_language == lang_t::ZH)
        {
            CHECK(display == make_stringf_p(T_("%1$s stole %2$d gold"),
                death_source_display_name("Maurice").c_str(), 10));
        }
        else CHECK(display == loaded.name);
        CHECK(loaded.name == "Maurice stole 10 gold");
        vector<unsigned char> after;
        writer output_after(&after);
        loaded.save(output_after);
        CHECK(after == bytes);
    }
    // Same text without the producer marker is a historical/Lua snapshot.
    const Note unmarked(NOTE_MESSAGE, 10, 0, note.name);
    CHECK(unmarked.describe(false, false, true) == note.name);
    const Note wrong_count(NOTE_MESSAGE, 9, 0, note.name, "gold theft");
    CHECK(wrong_count.describe(false, false, true) == note.name);
}

TEST_CASE("monster rereview: real item theft describes stolen quantity and keeps unknown saved names English",
          "[zh-translation][monster-rereview][item-theft]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    for (int quantity : {1, 10})
    {
        issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
        unwind_var<vector<Note>> saved_notes(note_list);
        const bool was_active = notes_are_active();
        activate_notes(true);
        unwinder restore_active([&] { activate_notes(was_active); });
        note_list.clear();
        monster* thief = world.place(MONS_MAURICE, coord_def(20, 21));
        item_def& inventory = you.inv[0];
        inventory.base_type = OBJ_MISSILES;
        inventory.sub_type = MI_STONE;
        inventory.quantity = quantity;
        inventory.link = 0;
        inventory.pos = ITEM_IN_INVENTORY;
        inventory.flags = ISFLAG_IDENTIFIED;
        const int index = get_mitm_slot(10);
        REQUIRE(index != NON_ITEM);
        unwind_var<item_def> saved_item(env.item[index]);
        item_def* stolen = nullptr;
        string output;
        {
            rng::subgenerator random(1, 0x4e5448454654ULL);
            output = observe_message([&] { stolen = thief->take_item(0, MSLOT_MISSILE, true); });
        }
        REQUIRE(stolen == &env.item[index]);
        const int amount = stolen->quantity;
        REQUIRE(amount >= 1);
        REQUIRE(amount <= quantity);
        CHECK((inventory.defined() ? inventory.quantity : 0) == quantity - amount);
        if (amount < quantity)
        {
            CHECK(output.find(make_stringf(T_("%s steals %s from you!"),
                thief->name(DESC_THE).c_str(), stolen->name(DESC_A).c_str())) != string::npos);
        }
        REQUIRE(note_list.size() == 1);
        string expected;
        { ScopedLangEn en; expected = "Maurice stole " + stolen->name(DESC_A); }
        const Note note = note_list.back();
        CHECK(note.name == expected);
        CHECK(note.desc == "item theft");
        vector<unsigned char> bytes;
        writer output_before(&bytes);
        note.save(output_before);
        reader input(bytes);
        input.setMinorVersion(TAG_MINOR_VERSION);
        Note loaded;
        loaded.load(input);
        CHECK(loaded.name == expected);
        const Note unknown(NOTE_MESSAGE, 0, 0,
            "Maurice stole an unknown saved artefact", "item theft");
        CHECK(unknown.describe(false, false, true) == unknown.name);
        const Note empty(NOTE_MESSAGE, 0, 0, "Maurice stole ", "item theft");
        CHECK(empty.describe(false, false, true) == empty.name);
        vector<unsigned char> after;
        writer output_after(&after);
        loaded.describe(false, false, true);
        loaded.save(output_after);
        CHECK(after == bytes);
    }
}

TEST_CASE("monster rereview: actual vex stores canonical cause and note across language changes",
          "[zh-translation][monster-rereview][vex-protocol]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    unwind_var<vector<Note>> saved_notes(note_list);
    const bool was_active = notes_are_active();
    activate_notes(true);
    unwinder restore_active([&] { activate_notes(was_active); });
    note_list.clear();
    const bool divine_cause = GENERATE(false, true);
    monster* caster = divine_cause ? nullptr
        : world.place(MONS_ORC_WIZARD, coord_def(20, 21));
    string expected = "Trog's wrath";
    if (caster)
    {
        ScopedLangEn en;
        expected = caster->name(DESC_A);
    }
    const string message = observe_message([&]
    {
        REQUIRE(you.vex(caster, 3, divine_cause ? "Trog's wrath" : ""));
    });
    CHECK(you.props[DISABLED_BY_KEY].get_string() == expected);
    REQUIRE(note_list.size() == 1);
    CHECK(note_list.back().type == NOTE_VEXED);
    CHECK(note_list.back().name == expected);
    const Note note = note_list.back();
    vector<unsigned char> bytes;
    writer output(&bytes);
    note.save(output);
    reader input(bytes);
    input.setMinorVersion(TAG_MINOR_VERSION);
    Note loaded;
    loaded.load(input);
    for (lang_t display_language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture display_mode(display_language,
            display_language == lang_t::ZH ? "zh" : nullptr);
        CHECK(loaded.describe(false, false, true) == make_stringf(
            T_("Vexed by %s for %d turns"), death_source_display_name(expected).c_str(), 3));
        if (display_language == lang_t::ZH)
            CHECK(death_source_display_name(expected) != expected);
        CHECK(loaded.name == expected);
        CHECK(you.props[DISABLED_BY_KEY].get_string() == expected);
    }

    // Corrosion shares the canonical-cause display path with vex: a god-wrath
    // name is first rendered by god_wrath_display_name(), every other raw cause
    // keeps its exact English identity and is translated by T_() only at the
    // emission sink (player and monster).
    // Deterministic local RNG stream: corrosion rolls must not advance or be
    // perturbed by the parent generator.
    const uint64_t corrosion_parent_state = rng::current_generator().get_state();
    const uint64_t corrosion_parent_count = rng::current_generator().get_count();
    {
        rng::subgenerator corrosion_rng(0xc0440051ULL, 0xc0440052ULL);
        for (const char *cause : {"the entropic weave", "the acid",
                                  "Your corrupting presence", "a flying bit",
                                  "the fiery rage of Trog"})
        {
            const string cause_display = god_wrath_display_name(cause);
            const string shown = T_(cause_display.c_str());
            CAPTURE(language, cause, cause_display, shown);
            if (language == lang_t::EN)
                CHECK(shown == cause);
            else if (cause_display == cause)
            {
                // A raw cause must have its own SourceDB key; the identity string
                // handed to corrode() never changes.
                CHECK(shown != cause);
            }

            you.duration[DUR_CORROSION] = 0;
            const string player_message = observe_message([&]
            {
                you.corrode(nullptr, cause, 8);
            });
            CAPTURE(player_message);
            CHECK(player_message.find(make_stringf(T_("%s corrodes you!"),
                                                  shown.c_str())) != string::npos);
            if (language == lang_t::ZH)
                CHECK(player_message.find(cause) == string::npos);

            monster *victim = world.place(MONS_ORC, coord_def(21, 21));
            const string monster_message = observe_message([&]
            {
                victim->corrode(&you, cause, 8);
            });
            CAPTURE(monster_message);
            CHECK(monster_message.find(make_stringf(T_("%s corrodes %s!"), shown.c_str(),
                                                    victim->name(DESC_THE).c_str()))
                  != string::npos);
            if (language == lang_t::ZH)
                CHECK(monster_message.find(cause) == string::npos);
        }
    }

    // The scoped subgenerator restored the parent stream untouched.
    CHECK(rng::current_generator().get_state() == corrosion_parent_state);
    CHECK(rng::current_generator().get_count() == corrosion_parent_count);
}

TEST_CASE("monster rereview: real yell places wild adverb before Chinese action and keeps fugue",
          "[zh-translation][monster-rereview][shout]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    for (bool berserk : {false, true})
    for (bool fugue : {false, true})
    {
        you.duration[DUR_BERSERK] = berserk ? 10 : 0;
        you.duration[DUR_FUGUE] = fugue ? 10 : 0;
        const string verb = you.shout_verb(false);
        const string suffix = fugue ? T_(", and the damned howl along") : "";
        const string expected = make_stringf_p(berserk ? T_("You %1$s wildly%2$s!")
                                                       : T_("You %1$s for attention%2$s!"),
                                               verb.c_str(), suffix.c_str());
        const string output = observe_message([&] { yell(); });
        CHECK(output.find(expected) != string::npos);
        if (language == lang_t::ZH) CHECK(output.find("wildly") == string::npos);
    }
}

TEST_CASE("monster rereview: soul-bound naming and four item binding displays use separate contexts",
          "[zh-translation][monster-rereview][bound-context]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    struct item_kind { object_class_type base; int subtype; };
    const item_kind kinds[] = {{OBJ_WEAPONS, WPN_DAGGER}, {OBJ_ARMOUR, ARM_ROBE},
                              {OBJ_JEWELLERY, RING_FIRE}, {OBJ_STAVES, STAFF_FIRE}};
    for (const auto& kind : kinds)
    {
        item_def item;
        item.base_type = kind.base;
        item.sub_type = kind.subtype;
        item.quantity = 1;
        item.flags = ISFLAG_CURSED | ISFLAG_IDENTIFIED;
        const string display = item.name(DESC_PLAIN);
        CHECK(display.find(T_("bound ")) != string::npos);
        CHECK(display.find('\n') == string::npos);
        CHECK(item.cursed());
    }
    monster_info soul(MONS_BOUND_SOUL);
    soul.base_type = MONS_ORC;
    const string display = soul.common_name(DESC_PLAIN);
    CHECK(display.find(C_("bound soul name", "bound ")) != string::npos);
    CHECK(display.find('\n') == string::npos);
    if (language == lang_t::ZH)
        CHECK(string(C_("bound soul name", "bound ")) != T_("bound "));
}

TEST_CASE("monster rereview: actual delayed discharge translates raw source at firing",
          "[zh-translation][monster-rereview][discharge]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    no_notes suppress_notes;
    monster* source = world.place(MONS_SHOCK_SERPENT, coord_def(20, 21));
    you.hp = you.hp_max = 1000;
    for (const char* raw_source : {"electric aura", "shield"})
    for (int power : {3, 6})
    {
        const int before = you.hp;
        schedule_shock_discharge_fineff(source, you, source->pos(), power, raw_source);
        i18n_cache_clear();
        const string output = observe_message([&] { fire_final_effects(); });
        const int damage = before - you.hp;
        CHECK(output.find(make_stringf_p(T_("%1$s %2$s discharges%3$s, shocking %4$s%5$s"),
            source->name(DESC_ITS).c_str(), C_("shock discharge source", raw_source),
            power < 4 ? "" : T_(" violently"), you.name(DESC_THE).c_str(),
            attack_strength_punctuation(damage).c_str())) != string::npos);
        if (language == lang_t::ZH)
        {
            CHECK(output.find(raw_source) == string::npos);
            CHECK(output.find("violently") == string::npos);
        }
    }
}

TEST_CASE("monster rereview: actual slow orb keeps canonical caster property through serialization",
          "[zh-translation][monster-rereview][orb-caster]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    no_notes suppress_notes;
    init_zap_index();
    monster* caster = world.place(MONS_ORC_WIZARD, coord_def(20, 21));
    string canonical;
    { ScopedLangEn en; canonical = caster->name(DESC_A, true); }
    REQUIRE(cast_iood(caster, 50, nullptr, 1, 0, MHITNOT, false, false) == spret::success);
    monster* orb = nullptr;
    for (monster_iterator mi; mi; ++mi)
        if (mi->type == MONS_ORB_OF_DESTRUCTION && mi->summoner == caster->mid)
        {
            orb = *mi;
            world.monsters.push_back(orb);
        }
    REQUIRE(orb);
    CHECK(orb->props[IOOD_CASTER].get_string() == canonical);
    vector<unsigned char> bytes;
    writer output(&bytes);
    marshallMonster(output, *orb);
    reader input(bytes);
    input.setMinorVersion(TAG_MINOR_VERSION);
    monster loaded;
    unmarshallMonster(input, loaded);
    CHECK(loaded.props[IOOD_CASTER].get_string() == canonical);
}

TEST_CASE("monster rereview: finite canonical orb names render at actual beam and score sinks",
          "[zh-translation][monster-rereview][orb-display]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    monster* source = world.place(MONS_ORC_WIZARD, coord_def(20, 21));
    const char* names[] = {"orb of destruction", "wavering orb of destruction",
        "annihilating fire", "annihilating cold", "annihilating electricity",
        "annihilating negative energy", "annihilating magma", "annihilating ice",
        "annihilating devastation", "annihilating acid", "annihilating fragments"};
    unwind_var<int> sanctuary_time(env.sanctuary_time, 1);
    unwind_var<coord_def> sanctuary_pos(env.sanctuary_pos, source->pos());
    const auto old_props = env.pgrid(source->pos());
    unwinder restore_props([&] { env.pgrid(source->pos()) = old_props; });
    env.pgrid(source->pos()) |= FPROP_SANCTUARY_1;
    for (const char* canonical : names)
    {
        // These are the bounded canonical setup outputs. This case exercises
        // final sinks, not the private random annihilation setup itself.
        bolt beam;
        beam.animate = false;
        beam.name = canonical;
        beam.aux_source = canonical;
        beam.origin_spell = starts_with(canonical, "annihilating ")
            ? SPELL_UNLEASH_DESTRUCTION : SPELL_IOOD;
        beam.flavour = BEAM_FIRE;
        beam.target = source->pos();
        beam.use_target_as_pos = true;
        const string display = C_("orb beam name", canonical);
        const string output = observe_message([&] { CHECK(beam.explode(false)); });
        CHECK(output.find(display) != string::npos);
        CHECK(beam.name == canonical);
        CHECK(beam.aux_source == canonical);
        scorefile_entry score(1, source->mid, KILLED_BY_BEAM, beam.aux_source.c_str(), true);
        score.init(1600000000);
        const string raw = score.raw_string();
        CHECK(score.get_fields().str_field("kaux") == canonical);
        CHECK(score.death_description(scorefile_entry::DDV_VERBOSE).find(display) != string::npos);
        CHECK(score.raw_string() == raw);
    }
    CHECK(orb_beam_name_display("annihilating unknown substance") == "annihilating unknown substance");
}

TEST_CASE("monster rereview: actual Waterstrike translates grounded and airborne motion",
          "[zh-translation][monster-rereview][waterstrike]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool airborne = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    no_notes suppress_notes;
    init_zap_index();
    you.hp = you.hp_max = 1000;
    you.duration[DUR_FLIGHT] = airborne ? 10 : 0;
    REQUIRE(you.airborne() == airborne);
    monster* caster = world.place(MONS_ORC_WIZARD, coord_def(20, 21));
    caster->target = you.pos();
    const int before = you.hp;
    const string output = observe_message([&]
    {
        mons_cast(caster, bolt(), SPELL_WATERSTRIKE, MON_SPELL_MAGICAL, false);
    });
    CHECK(output.find(make_stringf(T_("The water %s and strikes %s%s"),
        airborne ? T_("rises up") : T_("swirls"), you.name(DESC_THE).c_str(),
        attack_strength_punctuation(before - you.hp).c_str())) != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(output.find("rises up") == string::npos);
        CHECK(output.find("swirls") == string::npos);
    }
}

TEST_CASE("monster rereview: real thrown-creature score parses canonical cause and translates final sinks",
          "[zh-translation][monster-rereview][thrown-creature]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    monster* thrower = world.place(MONS_ORC_WIZARD, coord_def(20, 21));
    // Exercise the real legacy parser and score sinks using the exact producer
    // shape. The private throw-site selection/movement producer is source-audited.
    const char* canonical = "Hit by an orc thrown by orc wizard";
    scorefile_entry score(1, thrower->mid, KILLED_BY_BEAM, canonical, true);
    score.init(1600000000);
    const string raw = score.raw_string();
    CHECK(score.get_fields().str_field("kaux") == canonical);
    const string target = death_source_display_name("orc");
    const string output = score.death_description(scorefile_entry::DDV_VERBOSE);
    if (language == lang_t::ZH)
    {
        CHECK(output.find(make_stringf_p(T_("Hit by %1$s thrown by %2$s"),
            target.c_str(), death_source_display_name("an orc wizard").c_str())) != string::npos);
    }
    else
        CHECK(output.find(canonical) != string::npos);
    CHECK(score.death_description(scorefile_entry::DDV_LOGVERBOSE).find(target) != string::npos);
    CHECK(score.raw_string() == raw);
}

TEST_CASE("monster rereview: actual dream dust covers strengths, plural endings and monster targets",
          "[zh-translation][monster-rereview][dream-dust]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool player_target = GENERATE(false, true);
    const int branch = GENERATE(0, 1, 2, 3, 4, 5);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<use_animations_type> animations(
        Options.use_animations, use_animations_type());
    no_notes suppress_notes;
    init_zap_index();
    const int count[] = {1, 2, 6, 6, 6, 6};
    const int lower[] = {0, 0, 0, 25, 75, 125};
    const int upper[] = {25, 25, 25, 75, 125, 151};
    monster* sheep = world.place(MONS_DREAM_SHEEP, coord_def(20, 21));
    for (int i = 1; i < count[branch]; ++i)
        world.place(MONS_DREAM_SHEEP, coord_def(21 + i, 21));
    actor* target = &you;
    if (!player_target)
    {
        monster* victim = world.place(MONS_ORC, coord_def(21, 20));
        sheep->foe = victim->mindex();
        target = victim;
    }
    sheep->target = target->pos();
    unsigned int seed = 0;
    int power = 0;
    // Pick a deterministic fixture seed for each existing strength branch.
    // The real spell below makes its own unchanged draw and emits the message.
    for (; seed < 256; ++seed)
    {
        rng::subgenerator random(seed, 0x4e445245414dULL);
        power = random2(count[branch] * 25) + 1;
        if (power >= lower[branch] && power < upper[branch])
            break;
    }
    REQUIRE(seed < 256);
    if (power < 25)
        power = 0;
    const string target_name = target->name(DESC_THE);
    string output;
    {
        rng::subgenerator random(seed, 0x4e445245414dULL);
        output = observe_message([&]
        {
            mons_cast(sheep, bolt(), SPELL_DREAM_DUST, MON_SPELL_MAGICAL, false);
        });
    }
    string expected;
    if (!player_target)
    {
        const char* pluralize = count[branch] == 1 ? "s" : "";
        expected = power
            ? make_stringf_p(T_("As the sheep sparkle%1$s and sway%2$s, %3$s falls asleep."),
                             pluralize, pluralize, target_name.c_str())
            : make_stringf_p(T_("The dream sheep attempt%1$s to lull %2$s to sleep."),
                             pluralize, target_name.c_str());
    }
    else if (power >= 125)
        expected = T_("You are overwhelmed by glittering dream dust!");
    else if (power >= 75)
        expected = T_("The dream sheep are wreathed in dream dust.");
    else if (power)
        expected = T_("The dream sheep shake their wool and sparkle.");
    else
        expected = make_stringf(T_("The dream sheep ruffle%s wool and motes of "
                                   "dream dust sparkle, to no effect."),
                               count[branch] == 1 ? T_("s its") : T_(" their"));
    CAPTURE(count[branch], power, output);
    CHECK(output.find(expected) != string::npos);
    if (!player_target)
        CHECK(output.find(target_name) != string::npos);
}

TEST_CASE("item effects rereview: four ordinary terse names show binding without changing curse flag",
          "[zh-translation][item-effects-rereview][terse-bound]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const pair<object_class_type, int> kinds[] = {
        {OBJ_WEAPONS, WPN_DAGGER}, {OBJ_ARMOUR, ARM_ROBE},
        {OBJ_JEWELLERY, RING_FIRE}, {OBJ_STAVES, STAFF_FIRE}
    };
    for (const auto& kind : kinds)
    {
        item_def item;
        item.base_type = kind.first;
        item.sub_type = kind.second;
        item.quantity = 1;
        item.flags = ISFLAG_IDENTIFIED | ISFLAG_CURSED;
        const string terse = item.name(DESC_PLAIN, true);
        CHECK(ends_with(terse, T_(" (bound)")));
        CHECK(terse.find("(curse)") == string::npos);
        CHECK(item.cursed());
        CHECK(item.flags == (ISFLAG_IDENTIFIED | ISFLAG_CURSED));
        CHECK(item.name(DESC_DBNAME, true).find(T_(" (bound)")) == string::npos);
        CHECK(item.name(DESC_QUALNAME, true).find(T_(" (bound)")) == string::npos);
    }
}

TEST_CASE("item effects rereview: god gift origin uses actual god and original place in complete display",
          "[zh-translation][item-effects-rereview][gift-origin]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    for (god_type god : {GOD_OKAWARU, GOD_TROG, GOD_SHINING_ONE})
    for (const level_id place : {level_id(BRANCH_DUNGEON, 3), level_id(BRANCH_LAIR, 2)})
    {
        item.orig_monnum = -god;
        item.orig_place = place;
        REQUIRE(origin_describable(item));
        const string expected = make_stringf_p(T_("%1$s gifted it to you %2$s"),
            god_name(god).c_str(), prep_branch_level_name(place).c_str());
        CHECK(origin_desc(item) == expected);
        const string description = get_item_description(item);
        CHECK(description.find(expected + T_(".")) != string::npos);
        CHECK(item.orig_monnum == -god);
        CHECK(item.orig_place == place);
        if (language == lang_t::ZH)
        {
            CHECK(expected.find(" gifted ") == string::npos);
            CHECK(expected.find(" to you ") == string::npos);
        }
    }
}

TEST_CASE("item effects rereview: actual Throatcutter callback distinguishes thorough beheading",
          "[zh-translation][item-effects-rereview][throatcutter]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int heads = GENERATE(1, 4);
    const bool monster_attacker = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    monster* victim = world.place(MONS_HYDRA, coord_def(20, 21));
    victim->hit_points = victim->max_hit_points = 20;
    victim->num_heads = heads;
    victim->flags |= MF_HARD_RESET | MF_NO_REWARD;
    actor* attacker = &you;
    if (monster_attacker)
        attacker = world.place(MONS_ORC, coord_def(21, 20));
    const string expected = make_stringf_p(heads > 1
        ? T_("%1$s thoroughly behead%2$s %3$s!")
        : T_("%1$s behead%2$s %3$s!"), attacker->name(DESC_THE).c_str(),
        monster_attacker ? "s" : "", victim->name(DESC_THE).c_str());
    unsigned int seed = 0;
    for (; seed < 256; ++seed)
    {
        rng::subgenerator random(seed, 0x495448524f4154ULL);
        if (one_chance_in(3))
            break;
    }
    REQUIRE(seed < 256);
    const auto callback = get_unrand_entry(UNRAND_THROATCUTTER)->melee_effects;
    REQUIRE(callback);
    item_def weapon;
    string output;
    {
        rng::subgenerator random(seed, 0x495448524f4154ULL);
        output = observe_message([&] { callback(&weapon, attacker, victim, 1, nullptr); });
    }
    CHECK(output.find(expected) != string::npos);
    CHECK_FALSE(victim->alive());
    if (language == lang_t::ZH)
        CHECK(output.find(" thoroughly") == string::npos);
}

TEST_CASE("item effects rereview: actual Victory death callback emits ordinary and capped glow",
          "[zh-translation][item-effects-rereview][victory]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int initial_bonus = GENERATE(0, 6);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.base_stats.init(10);
    no_notes suppress_notes;
    monster* victim = world.place(MONS_ORB_OF_FIRE, coord_def(20, 21));
    define_monster(*victim);
    REQUIRE(mons_threat_level(*victim) == MTHRT_NASTY);
    const auto* entry = get_unrand_entry(UNRAND_VICTORY);
    item_def item;
    item.base_type = entry->base_type;
    item.sub_type = entry->sub_type;
    item.quantity = 1;
    REQUIRE(make_item_unrandart(item, UNRAND_VICTORY));
    item.props[VICTORY_STAT_KEY] = initial_bonus;
    REQUIRE(entry->death_effects);
    const string output = observe_message([&] { entry->death_effects(&item, victim, KILL_YOU); });
    const int bonus = initial_bonus + 1;
    CHECK(item.props[VICTORY_STAT_KEY].get_int() == bonus);
    CHECK(item.plus == bonus);
    CHECK(artefact_property(item, ARTP_SLAYING) == bonus);
    CHECK(artefact_property(item, ARTP_INTELLIGENCE) == bonus);
    const string expected = make_stringf(bonus == 7
        ? T_("%s glows brightly.") : T_("%s glows."),
        item.name(DESC_THE, false, true, false).c_str());
    CHECK(output.find(expected) != string::npos);
    if (language == lang_t::ZH)
        CHECK(output.find(" brightly") == string::npos);
}

TEST_CASE("item effects rereview: actual shop dump translates unknown suffix without changing stock",
          "[zh-translation][item-effects-rereview][shop-unknown]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([&] { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
    issue10_world world;
    ShopInfo shop;
    shop.shop.type = SHOP_GENERAL;
    item_def item;
    item.base_type = OBJ_POTIONS;
    item.sub_type = POT_HASTE;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    REQUIRE(shop_item_unknown(item));
    shop.shop.stock.push_back(item);
    FILE* file = tmpfile();
    REQUIRE(file);
    unwinder close_file([&] { fclose(file); });
    shop.write(file);
    REQUIRE(fseek(file, 0, SEEK_SET) == 0);
    string output;
    char buffer[512];
    while (fgets(buffer, sizeof(buffer), file))
        output += buffer;
    const string expected = make_stringf(T_("%s%s (%d gold)"),
        Stash::stash_item_name(item).c_str(), T_(" (unknown)"), item_price(item, shop.shop));
    INFO(output);
    INFO(expected);
    CHECK(output.find(expected) != string::npos);
    CHECK(shop.shop.stock.front().flags == item.flags);
    CHECK_FALSE(item_type_known(shop.shop.stock.front()));
    if (language == lang_t::ZH)
        CHECK(output.find("(unknown)") == string::npos);
}

TEST_CASE("item effects rereview: actual normal and punishment draws keep complete deal actions",
          "[zh-translation][item-effects-rereview][deck-actions]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    you.props[NEMELEX_STACK_KEY].new_vector(SV_INT).push_back(static_cast<int>(CARD_ELIXIR));
    const string ordinary = observe_message([&] { REQUIRE(deck_draw(DECK_STACK)); });
    CHECK(ordinary.find(T_("You draw a card...")) != string::npos);
    CHECK(deck_cards(DECK_STACK) == 0);
    unsigned int seed = 0;
    for (; seed < 256; ++seed)
    {
        rng::subgenerator random(seed, 0x494341524453ULL);
        // The existing punishment deck has four equal weights of5; select
        // its Wraith entry to keep the real callback free of interactive effects.
        if (random2(20) < 5)
            break;
    }
    REQUIRE(seed < 256);
    for (bool deal : {false, true})
    {
        string output;
        {
            rng::subgenerator random(seed, 0x494341524453ULL);
            output = observe_message([&] { draw_from_deck_of_punishment(deal); });
        }
        CHECK(output.find(deal ? T_("You deal a card...") : T_("You draw a card...")) != string::npos);
    }
}

TEST_CASE("item effects rereview: all card deck lists localize categories while persistent deck names stay English",
          "[zh-translation][item-effects-rereview][which-decks]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    for (int d = FIRST_PLAYER_DECK; d <= LAST_PLAYER_DECK; ++d)
    {
        const auto deck = static_cast<deck_type>(d);
        string canonical;
        { ScopedLangEn en; canonical = deck_name(deck); }
        CHECK(deck_name(deck) == canonical);
        you.props[canonical] = d + 1;
        CHECK(deck_cards(deck) == d + 1);
    }
    for (int c = 0; c < NUM_CARDS; ++c)
    {
        const string output = which_decks(static_cast<card_type>(c));
        REQUIRE_FALSE(output.empty());
        if (language == lang_t::ZH)
        {
            CHECK(output.find("escape") == string::npos);
            CHECK(output.find("destruction") == string::npos);
            CHECK(output.find("summoning") == string::npos);
            CHECK(output.find(" and ") == string::npos);
            CHECK(output.find('\n', 1) == string::npos);
        }
    }
}

TEST_CASE("item effects rereview: actual plutonium callback localizes all three contamination variants",
          "[zh-translation][item-effects-rereview][plutonium]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int variant = GENERATE(0, 1, 2);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    monster* attacker = world.place(MONS_ORC, coord_def(20, 21));
    you.hp = you.hp_max = 1000;
    REQUIRE(you.can_mutate());
    item_def weapon;
    weapon.base_type = OBJ_WEAPONS;
    weapon.sub_type = WPN_LONG_SWORD;
    weapon.quantity = 1;
    weapon.flags = ISFLAG_IDENTIFIED;
    melee_attack hit(attacker, &you);
    const auto callback = get_unrand_entry(UNRAND_PLUTONIUM_SWORD)->melee_effects;
    REQUIRE(callback);
    unsigned int seed = 0;
    for (; seed < 1024; ++seed)
    {
        rng::subgenerator random(seed, 0x49504c55544fULL);
        if (one_chance_in(5) && !one_chance_in(10)
            && random_choose(0, 1, 2) == variant)
        {
            break;
        }
    }
    REQUIRE(seed < 1024);
    string output;
    {
        rng::subgenerator random(seed, 0x49504c55544fULL);
        output = observe_message([&] { callback(&weapon, attacker, &you, 1, &hit); });
    }
    const char* messages[] = {
        "Your body deforms painfully.", "Your limbs ache and wobble like jelly.",
        "Your body is flooded with magical radiation."
    };
    CHECK(output.find(T_(messages[variant])) != string::npos);
    CHECK(you.magic_contamination >= 700);
    CHECK(you.hp < 1000);
    if (language == lang_t::ZH)
        CHECK(output.find(messages[variant]) == string::npos);
}

TEST_CASE("item effects rereview: ordinary definite item names omit Chinese articles in both quantity branches",
          "[zh-translation][item-effects-rereview][definite-article]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    struct specimen { object_class_type base; int subtype; int quantity; };
    const specimen kinds[] = {
        {OBJ_WEAPONS, WPN_DAGGER, 1}, {OBJ_ARMOUR, ARM_ROBE, 1},
        {OBJ_JEWELLERY, RING_FIRE, 1}, {OBJ_STAVES, STAFF_FIRE, 1},
        {OBJ_ARMOUR, ARM_FIRE_DRAGON_ARMOUR, 1},
        {OBJ_MISSILES, MI_STONE, 2}, {OBJ_POTIONS, POT_HASTE, 2}
    };
    for (const auto& kind : kinds)
    {
        item_def item;
        item.base_type = kind.base;
        item.sub_type = kind.subtype;
        item.quantity = kind.quantity;
        item.flags = ISFLAG_IDENTIFIED;
        const string plain = item.name(DESC_PLAIN);
        CHECK(item.name(DESC_THE) == (language == lang_t::ZH ? plain : "the " + plain));
        CHECK(item.quantity == kind.quantity);
        CHECK(item.flags == ISFLAG_IDENTIFIED);
    }
}

TEST_CASE("item effects rereview: actual power gloves equip callback translates both casting-resource branches",
          "[zh-translation][item-effects-rereview][power-gloves]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool hp_casting = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.mutation[MUT_HP_CASTING] = hp_casting ? 1 : 0;
    REQUIRE(you.has_mutation(MUT_HP_CASTING) == hp_casting);
    const auto callback = get_unrand_entry(UNRAND_POWER_GLOVES)->equip_func;
    REQUIRE(callback);
    bool show_messages = true;
    const string output = observe_message([&] { callback(nullptr, &show_messages, false); });
    const char* message = hp_casting
        ? "The gloves are unable to connect with your magical essence."
        : "You feel an incredible surge of magic.";
    CHECK(output.find(T_(message)) != string::npos);
    CHECK(you.has_mutation(MUT_HP_CASTING) == hp_casting);
    if (language == lang_t::ZH)
        CHECK(output.find(message) == string::npos);
}

TEST_CASE("item effects rereview: item note display payloads survive actual save load and language switches verbatim",
          "[zh-translation][item-effects-rereview][note-snapshots]")
{
    TranslationFixture translation(lang_t::ZH, "zh");
    issue10_world world;
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    item.orig_monnum = -GOD_OKAWARU;
    item.orig_place = level_id(BRANCH_DUNGEON, 3);
    const string payload_name = item.name(DESC_A);
    const string payload_desc = origin_desc(item);
    for (NOTE_TYPES type : {NOTE_ID_ITEM, NOTE_GET_ITEM, NOTE_FOUND_UNRAND,
                            NOTE_ACQUIRE_ITEM, NOTE_BUY_ITEM})
    {
        // Use production formatters and actual Note serialization, not a fake
        // typed item encoding. Producer call-site enumeration is in the audit.
        const Note original(type, type == NOTE_BUY_ITEM ? 123 : 0, 0,
            payload_name, type == NOTE_BUY_ITEM ? "" : payload_desc);
        vector<unsigned char> bytes;
        writer output(&bytes);
        original.save(output);
        reader input(bytes);
        input.setMinorVersion(TAG_MINOR_VERSION);
        Note loaded;
        loaded.load(input);
        for (lang_t language : {lang_t::ZH, lang_t::EN, lang_t::ZH})
        {
            unwind_var<lang_t> mode(Options.language, language);
            i18n_cache_clear();
            CHECK(loaded.name == original.name);
            CHECK(loaded.desc == original.desc);
            const string display = loaded.describe(false, false, true);
            CHECK(display.find(payload_name) != string::npos);
            if (type == NOTE_ID_ITEM)
                CHECK(display.find(payload_desc) != string::npos);
            vector<unsigned char> after;
            writer second_output(&after);
            loaded.save(second_output);
            CHECK(after == bytes);
        }
    }
    CHECK(item.orig_monnum == -GOD_OKAWARU);
    CHECK(item.orig_place == level_id(BRANCH_DUNGEON, 3));
}

TEST_CASE("item effects rereview: actual identification note snapshots localized payload while collectible milestone stays English",
          "[zh-translation][item-effects-rereview][note-producer]")
{
    TranslationFixture translation(lang_t::ZH, "zh");
    issue10_world world;
    unwind_var<vector<Note>> saved_notes(note_list);
    const bool active = notes_are_active();
    activate_notes(true);
    unwinder restore_active([&] { activate_notes(active); });
    note_list.clear();
    const auto* entry = get_unrand_entry(UNRAND_VICTORY);
    item_def& item = you.inv[0];
    item.base_type = entry->base_type;
    item.sub_type = entry->sub_type;
    item.quantity = 1;
    item.link = 0;
    item.pos = ITEM_IN_INVENTORY;
    REQUIRE(make_item_unrandart(item, UNRAND_VICTORY));
    item.flags &= ~(ISFLAG_IDENTIFIED | ISFLAG_NOTED_ID | ISFLAG_NOTED_GET);
    item.orig_monnum = -GOD_OKAWARU;
    item.orig_place = level_id(BRANCH_DUNGEON, 3);
    REQUIRE_FALSE(item.is_identified());
    identify_item(item);
    REQUIRE(note_list.size() == 1);
    const Note& note = note_list.back();
    CHECK(note.type == NOTE_ID_ITEM);
    CHECK(note.name == item.name(DESC_A, false, false, true, false, false));
    CHECK(note.desc == origin_desc(item));
    item_def rune;
    rune.base_type = OBJ_RUNES;
    rune.sub_type = RUNE_SWAMP;
    rune.quantity = 1;
    string canonical;
    { ScopedLangEn en; canonical = "found " + rune.name(DESC_A) + "."; }
    const string display = rune.name(DESC_A);
    CHECK(collectible_milestone(rune) == canonical);
    CHECK(collectible_milestone(rune).find(display) == string::npos);
}

TEST_CASE("item effects rereview: actual seven league boots callbacks localize readiness and its end",
          "[zh-translation][item-effects-rereview][seven-league]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool removing = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const auto* entry = get_unrand_entry(UNRAND_SEVEN_LEAGUE_BOOTS);
    REQUIRE(entry->equip_func);
    REQUIRE(entry->unequip_func);
    bool show_messages = true;
    const string output = observe_message([&]
    {
        if (removing)
            entry->unequip_func(nullptr, &show_messages);
        else
            entry->equip_func(nullptr, &show_messages, false);
    });
    const char* key = removing
        ? "You no longer feel ready to stride towards your foes."
        : "You feel ready to stride towards your foes.";
    CHECK(output.find(T_(key)) != string::npos);
    if (language == lang_t::ZH)
        CHECK(output.find(key) == string::npos);
}

TEST_CASE("item effects rereview: actual named weapon welcome and return preserve its free proper name",
          "[zh-translation][item-effects-rereview][weapon-welcome]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    item_def weapon;
    weapon.base_type = OBJ_WEAPONS;
    weapon.sub_type = WPN_DAGGER;
    weapon.quantity = 1;
    weapon.flags = ISFLAG_IDENTIFIED;
    const string first = observe_message([&] { maybe_name_weapon(weapon); });
    REQUIRE(weapon.props.exists(WEAPON_NAME_KEY));
    const string proper_name = weapon.props[WEAPON_NAME_KEY].get_string();
    const string inscription = weapon.inscription;
    const string full_name = get_weapon_name(weapon, true);
    CHECK(first.find(make_stringf(T_("You welcome %s into your grasp."), full_name.c_str()))
          != string::npos);
    const string second = observe_message([&] { maybe_name_weapon(weapon); });
    CHECK(second.find(make_stringf(T_("You welcome %s back into your grasp."), full_name.c_str()))
          != string::npos);
    CHECK(weapon.props[WEAPON_NAME_KEY].get_string() == proper_name);
    CHECK(weapon.inscription == inscription);
    if (language == lang_t::ZH)
        CHECK(second.find(" back") == string::npos);
}

TEST_CASE("item effects rereview: actual archmage trap reports real drain and every empowerment branch",
          "[zh-translation][item-effects-rereview][archmage-trap]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int initial_mp = GENERATE(0, 9);
    const bool empower = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    you.magic_points = initial_mp;
    you.max_magic_points = 9;
    env.grid(you.pos()) = DNGN_TRAP_ARCHMAGE;
    monster* mage = nullptr;
    string expected;
    if (empower)
    {
        mage = world.place(MONS_ORC_WIZARD, coord_def(20, 21));
        mage->spells = {{SPELL_MAGIC_DART, 100, MON_SPELL_WIZARD}};
        REQUIRE(mage->antimagic_susceptible());
        const string name = describe_monsters_condensed({mage});
        expected = make_stringf(initial_mp
            ? T_("Your power is siphoned away as the spells of %s are empowered!")
            : T_("The spells of %s are empowered!"), name.c_str());
    }
    else
        expected = initial_mp ? T_("Your power is siphoned away!")
                              : T_("Nothing appears to happen.");
    const string output = observe_message([&] { trigger_trap(you); });
    CHECK(output.find(expected) != string::npos);
    CHECK(you.magic_points == (initial_mp ? 6 : 0));
    if (mage)
        CHECK(mage->has_ench(ENCH_EMPOWERED_SPELLS));
    if (!initial_mp && !empower)
        CHECK(output.find(T_("Your power is siphoned away!")) == string::npos);
}

TEST_CASE("interface rereview: real corruption producer stores English and marked typed note displays across locales",
          "[zh-translation][interface-rereview][corruption-note]")
{
    vector<int> continuation;
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        issue10_world world;
        unwind_var<vector<Note>> saved_notes(note_list);
        const bool active = notes_are_active();
        activate_notes(true);
        unwinder restore_active([&] { activate_notes(active); });
        note_list.clear();
        you.where_are_you = BRANCH_DUNGEON;
        you.depth = 3;
        you.religion = GOD_LUGONU;
        you.base_stats.init(10);
        const level_id place = level_id::current();
        REQUIRE(get_level_annotation(place).empty());
        unwinder clear_annotation([&] { clear_level_annotations(place); });
        unwind_var<decltype(env.grid)> grid(env.grid);
        unwind_var<decltype(env.mgrid)> mgrid(env.mgrid);
        unwind_var<decltype(env.mons)> monsters(env.mons);
        unwind_var<map_markers> markers(env.markers);
        unwind_var<int> delay(Options.view_delay, 0);
        env.grid.init(DNGN_PERMAROCK_WALL);
        env.mgrid.init(NON_MONSTER);
        env.markers.clear();
        // The real full producer runs. Permanent rock prevents terrain/item
        // movement and servant placement; it does not bypass any caller draw.
        {
            rng::subgenerator random(19, 0x4b434f5252555054ULL);
            observe_message([&] { lugonu_corrupt_level(0); });
            continuation.push_back(random2(1000000));
        }
        REQUIRE(note_list.size() == 1);
        const Note original = note_list.back();
        CHECK(original.name == "Corrupted D:3");
        CHECK(original.desc == "corrupted level");
        CHECK(original.place == place);
        vector<unsigned char> bytes;
        writer output(&bytes);
        original.save(output);
        reader input(bytes);
        input.setMinorVersion(TAG_MINOR_VERSION);
        Note loaded;
        loaded.load(input);
        for (lang_t display_language : {lang_t::EN, lang_t::ZH, lang_t::EN})
        {
            TranslationFixture display_mode(display_language,
                display_language == lang_t::ZH ? "zh" : nullptr);
            const string display = loaded.describe(false, false, true);
            CHECK(display == (display_language == lang_t::ZH
                ? make_stringf(T_("Corrupted %s"), place.describe(true, true).c_str())
                : loaded.name));
            CHECK(loaded.name == original.name);
            CHECK(loaded.desc == original.desc);
            CHECK(loaded.place == original.place);
            vector<unsigned char> after;
            writer output_after(&after);
            loaded.save(output_after);
            CHECK(after == bytes);
            Note unmarked = loaded;
            unmarked.desc.clear();
            CHECK(unmarked.describe(false, false, true) == original.name);
            Note unknown_marker = loaded;
            unknown_marker.desc = "unknown marker";
            CHECK(unknown_marker.describe(false, false, true) == original.name);
            Note malformed = loaded;
            malformed.name += " extra";
            CHECK(malformed.describe(false, false, true) == malformed.name);
            Note invalid = loaded;
            invalid.place = level_id();
            CHECK(invalid.describe(false, false, true) == invalid.name);
            invalid.place = level_id(NUM_BRANCHES, 1);
            CHECK(invalid.describe(false, false, true) == invalid.name);
        }
        {
            TranslationFixture missing_database(lang_t::ZH, nullptr);
            CHECK(loaded.describe(false, false, true) == original.name);
        }
    }
    REQUIRE(continuation.size() == 3);
    CHECK(continuation[0] == continuation[1]);
    CHECK(continuation[1] == continuation[2]);
}

TEST_CASE("interface rereview: real abyss encounter selects every original weighted display leaf",
          "[zh-translation][interface-rereview][abyss-encounter]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int variant = GENERATE(0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    monster* mon = world.place(MONS_ORC, coord_def(20, 21));
    mon->flags |= MF_WAS_IN_VIEW;
    const int weights[] = {17, 34, 45, 13, 26, 33, 9, 18, 7, 14, 5, 10, 2, 7, 3};
    const char* messages[] = {
        " appears in a shower of translocational energy.", " appears in a shower of sparks.",
        " materialises.", " emerges from chaos.", " emerges from the beyond.",
        " assembles %s!", " erupts from nowhere.", " bursts from nowhere.",
        " is cast out of space.", " is cast out of reality.",
        " coalesces out of pure chaos.", " coalesces out of seething chaos.",
        " punctures the fabric of time!", " punctures the fabric of the universe.",
        " manifests with a bang!"
    };
    int total = 0, low = 0;
    for (int i = 0; i < 15; ++i)
    {
        total += weights[i];
        if (i < variant)
            low += weights[i];
    }
    unsigned int seed = 0;
    for (; seed < 8192; ++seed)
    {
        rng::subgenerator random(seed, 0x4b4142595353ULL);
        const int choice = random2(total);
        if (choice >= low && choice < low + weights[variant])
            break;
    }
    REQUIRE(seed < 8192);
    vector<monster*> none, announced = {mon};
    string output;
    {
        rng::subgenerator random(seed, 0x4b4142595353ULL);
        output = observe_message([&] { notice_new_monsters(none, announced, SC_ABYSS); });
    }
    const string expected = variant == 5
        ? make_stringf(T_(messages[variant]), mon->pronoun(PRONOUN_REFLEXIVE).c_str())
        : T_(messages[variant]);
    CHECK(output.find(expected) != string::npos);
    CHECK(output.find(mon->name(DESC_A)) != string::npos);
    if (language == lang_t::ZH)
        CHECK(output.find(messages[variant]) == string::npos);
}

TEST_CASE("interface rereview: real abyss encounter preserves death cob and silent manifestation branches",
          "[zh-translation][interface-rereview][abyss-special]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int variant = GENERATE(0, 1, 2);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    monster* mon = world.place(variant ? MONS_DEATH_COB : MONS_ORC, coord_def(20, 21));
    mon->flags |= MF_WAS_IN_VIEW;
    if (!variant)
    {
        you.duration[DUR_SILENCE] = 100;
        invalidate_agrid();
        REQUIRE(silenced(you.pos()));
    }
    unsigned int seed = 0;
    for (; seed < 8192; ++seed)
    {
        rng::subgenerator random(seed, 0x4b414253504543ULL);
        if ((!variant && random2(243) >= 240)
            || (variant && coinflip() == (variant == 1)))
        {
            break;
        }
    }
    REQUIRE(seed < 8192);
    vector<monster*> none, announced = {mon};
    string output;
    {
        rng::subgenerator random(seed, 0x4b414253504543ULL);
        output = observe_message([&] { notice_new_monsters(none, announced, SC_ABYSS); });
    }
    const char* key = !variant ? " manifests!" : variant == 1
        ? " appears in a burst of microwaves!" : " pops from nullspace!";
    CHECK(output.find(T_(key)) != string::npos);
    if (!variant)
        CHECK(output.find(T_(" manifests with a bang!")) == string::npos);
    if (language == lang_t::ZH)
        CHECK(output.find(key) == string::npos);
}

TEST_CASE("interface rereview: actual catalyst description covers every permission and use-key paragraph",
          "[zh-translation][interface-rereview][catalyst]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int branch = GENERATE(0, 1, 2, 3, 4);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const coord_def pos(21, 20);
    unwind_var<map_cell> knowledge(env.map_knowledge(pos));
    env.grid(pos) = DNGN_PURIFIED_MUTATION_CATALYST;
    env.map_knowledge(pos).set_feature(DNGN_PURIFIED_MUTATION_CATALYST);
    const char* key = nullptr;
    if (branch == 0)
    {
        you.religion = GOD_ZIN;
        key = "\nYour adherence to the laws of Zin forbids you from using such a device.";
    }
    else if (branch == 1)
    {
        you.form = transformation::death;
        key = "\nYou must first come back to life before you may mutate.";
    }
    else if (branch == 2)
    {
        you.species = SP_MUMMY;
        REQUIRE(you.is_lifeless_undead());
        key = "\nThis is completely useless to you, as you cannot mutate.";
    }
    else if (branch == 3)
    {
        you.mutation[MUT_MUTATION_RESISTANCE] = 3;
        key = "\nThis is completely useless to you, as you cannot mutate.";
    }
    describe_info description;
    get_feature_desc(pos, description, false);
    const string body = description.body.str();
    if (key)
        CHECK(body.find(T_(key)) != string::npos);
    else
    {
        const string feature = feature_description_at(pos, false, DESC_THE);
        const string command = command_to_string(CMD_GO_DOWNSTAIRS);
        const string expected = make_stringf_p(T_("<w>\nWhile standing here, you can crack open %1$s with "
                                                 "the</w> <cyan>%2$s</cyan> <w>key</w>."),
                                               feature.c_str(), command.c_str());
        CHECK(body.find(expected) != string::npos);
        CHECK(body.find("<cyan>" + command + "</cyan>") != string::npos);
    }
    CHECK(env.grid(pos) == DNGN_PURIFIED_MUTATION_CATALYST);
}

TEST_CASE("interface rereview: actual ice-thorns owner trigger uses complete player and monster frames",
          "[zh-translation][interface-rereview][ice-thorns]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool player_owner = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    no_notes suppress_notes;
    unwind_var<map_markers> markers(env.markers);
    env.markers.clear();
    actor* owner = &you;
    if (!player_owner)
        owner = world.place(MONS_ORC, coord_def(20, 21));
    const coord_def pos = owner->pos();
    unwind_var<map_cell> knowledge(env.map_knowledge(pos));
    const auto old_properties = env.pgrid(pos);
    unwinder restore_properties([&] { env.pgrid(pos) = old_properties; });
    REQUIRE_FALSE(owner->airborne());
    temp_change_terrain(pos, DNGN_ICE_THORNS, 50,
                        TERRAIN_CHANGE_ICE_THORNS, owner->mid, 10);
    REQUIRE(env.markers.get_terrain_change_at(pos, TERRAIN_CHANGE_ICE_THORNS));
    const string expected = make_stringf(player_owner
        ? T_("Your icy thorns crumble before %s.")
        : T_("The icy thorns crumble before %s."), owner->name(DESC_THE).c_str());
    const string output = observe_message([&] { ice_thorns_trigger(*owner, pos); });
    CHECK(output.find(expected) != string::npos);
    CHECK(env.grid(pos) == DNGN_FLOOR);
    CHECK_FALSE(env.markers.get_terrain_change_at(pos, TERRAIN_CHANGE_ICE_THORNS));
    if (language == lang_t::ZH)
        CHECK(output.find("The") == string::npos);
}

TEST_CASE("interface rereview: actual overview rune row retains real command counts and full rune list",
          "[zh-translation][interface-rereview][rune-overview]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int count = GENERATE(1, 2);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.base_stats.init(10);
    you.experience_level = 1;
    you.runes.reset();
    you.runes.set(RUNE_SWAMP);
    if (count == 2)
        you.runes.set(RUNE_SNAKE);
    you.obtainable_runes = 3;
    const auto before = you.runes;
    vector<string> runes;
    for (int i = 0; i < NUM_RUNE_TYPES; ++i)
        if (you.runes.get(i))
            runes.emplace_back(rune_type_name(i));
    const string list = join_strings(runes.begin(), runes.end(),
                                     language == lang_t::ZH ? "、" : ", ");
    const string expected = formatted_string::parse_string(make_stringf_p(
        T_("\n<w>%1$s:</w> %2$d/%3$d rune%4$s: %5$s"),
        command_to_string(CMD_DISPLAY_RUNES).c_str(), count, 3, "s", list.c_str())).tostring();
    const string output = dump_overview_screen();
    CHECK(output.find(expected) != string::npos);
    for (const string& rune : runes)
        CHECK(output.find(rune) != string::npos);
    for (int i = 0; i < NUM_RUNE_TYPES; ++i)
        CHECK(you.runes.get(i) == before.get(i));
    CHECK(you.obtainable_runes == 3);
}

TEST_CASE("interface rereview: audited game-start note snapshots preserve actual display values across save load and locales",
          "[zh-translation][interface-rereview][game-start-snapshot]")
{
    const lang_t creation_language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(creation_language,
        creation_language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    item_def item;
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    const string actor_name = "Ada%custom";
    const string items = string(T_("the following items: ")) + item.name(DESC_A);
    const string spells = string(T_("the following spell memorised: "))
        + spell_title(SPELL_MAGIC_DART);
    const string library = string(T_("the following spells available to memorise: "))
        + spell_title(SPELL_BLINK);
    const string separator = T_("; and ");
    // The startup producers are private to main.o (not linked into Catch2).
    // This covers the actual Note serialization/display boundary with real
    // catalog/item/spell accessors; it does not execute a startup producer.
    for (const string& payload : {
        make_stringf(C_("game start", "%s the %s %s began the quest for the Orb."),
            actor_name.c_str(), T_("Human"), T_("Fighter")),
        make_stringf(C_("game start", "%s set off with %s%s%s."),
            actor_name.c_str(), "", "", spells.c_str()),
        make_stringf(C_("game start", "%s set off with %s%s%s."),
            actor_name.c_str(), items.c_str(), (separator + spells).c_str(),
            (separator + library).c_str())})
    {
        const Note original(NOTE_MESSAGE, 0, 0, payload);
        vector<unsigned char> bytes;
        writer output(&bytes);
        original.save(output);
        reader input(bytes);
        input.setMinorVersion(TAG_MINOR_VERSION);
        Note loaded;
        loaded.load(input);
        for (lang_t display_language : {lang_t::ZH, lang_t::EN, lang_t::ZH})
        {
            unwind_var<lang_t> mode(Options.language, display_language);
            CHECK(loaded.describe(false, false, true) == payload);
            CHECK(loaded.name == original.name);
            CHECK(loaded.desc.empty());
            CHECK(loaded.name.find(actor_name) != string::npos);
            vector<unsigned char> after;
            writer second_output(&after);
            loaded.save(second_output);
            CHECK(after == bytes);
        }
    }
}

TEST_CASE("interface rereview: actual branch rune descriptions preserve all remaining names and omit English plural morphology",
          "[zh-translation][interface-rereview][branch-runes]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const branch_type branch = GENERATE(BRANCH_DUNGEON, BRANCH_SWAMP,
                                        BRANCH_PANDEMONIUM);
    const bool remaining_only = GENERATE(false, true);
    const int collected = GENERATE(0, 1, 5);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.runes.reset();
    int index = 0;
    for (rune_type rune : branches[branch].runes)
        if (index++ < collected)
            you.runes.set(rune);
    const auto before = you.runes;
    vector<string> names;
    for (rune_type rune : branches[branch].runes)
        if (!(remaining_only && you.runes.get(rune)))
            names.emplace_back(rune_type_name(rune));
    const string output = branch_rune_desc(branch, remaining_only);
    if (names.empty())
        CHECK(output.empty());
    else
    {
        const string list = language == lang_t::ZH
            ? join_strings(names.begin(), names.end(), "、")
            : comma_separated_line(names.begin(), names.end());
        const string expected = language == lang_t::ZH
            ? "这个分支包含" + list + "佐特符文。"
            : "This branch contains the " + list + " rune"
                + (names.size() > 1 ? "s" : "") + " of Zot.";
        CHECK(output == expected);
        for (const string& name : names)
            CHECK(output.find(name) != string::npos);
    }
    for (int i = 0; i < NUM_RUNE_TYPES; ++i)
        CHECK(you.runes.get(i) == before.get(i));
}

TEST_CASE("interface rereview: actual slime wall damage localizes all wall counts and icy victim predicates",
          "[zh-translation][interface-rereview][slime-walls]")
{
    const bool icy = GENERATE(false, true);
    const int walls = GENERATE(1, 2);
    vector<pair<int, int>> results;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        issue10_world world;
        no_notes suppress_notes;
        you.base_stats.init(10);
        monster* victim = world.place(icy ? MONS_ICE_BEAST : MONS_ORC,
                                       coord_def(21, 20));
        victim->hit_points = victim->max_hit_points = 1000;
        REQUIRE(victim->is_icy() == icy);
        REQUIRE_FALSE(actor_slime_wall_immune(victim));
        const coord_def first(22, 20), second(22, 21);
        env.grid(first) = DNGN_SLIMY_WALL;
        if (walls > 1)
            env.grid(second) = DNGN_SLIMY_WALL;
        invalidate_los();
        REQUIRE(count_adjacent_slime_walls(victim->pos()) == walls);
        REQUIRE(you.see_cell_no_trans(victim->pos()));
        const char* key = icy
            ? (walls > 1 ? "The walls melt %s!" : "The wall melts %s!")
            : (walls > 1 ? "The walls burn %s!" : "The wall burns %s!");
        const string expected = make_stringf(T_(key), victim->name(DESC_THE).c_str());
        {
            rng::subgenerator random(17, 0x4b534c494d45ULL);
            const string output = observe_message([&] {
                slime_wall_damage(victim, BASELINE_DELAY);
            });
            CHECK(output.find(expected) != string::npos);
            results.emplace_back(victim->hit_points, random2(1000000));
        }
        CHECK(victim->hit_points < 1000);
        CHECK(victim->alive());
        CHECK(env.grid(first) == DNGN_SLIMY_WALL);
        CHECK(env.grid(second) == (walls > 1 ? DNGN_SLIMY_WALL : DNGN_FLOOR));
    }
    REQUIRE(results.size() == 2);
    CHECK(results[0] == results[1]);
}

TEST_CASE("interface rereview: real canned empty-grasp messages preserve all body parts and already versus now",
          "[zh-translation][interface-rereview][empty-grasp]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int body = GENERATE(0, 1, 2, 3);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.base_stats.init(10);
    if (body == 1)
        you.mutation[MUT_CLAWS] = 3;
    else if (body == 2)
        you.mutation[MUT_TENTACLE_ARMS] = 1;
    else if (body == 3)
        you.mutation[MUT_NO_GRASPING] = 1;
    you.equipment.update();
    REQUIRE(you.has_mutation(MUT_NO_GRASPING) == (body == 3));
    REQUIRE(bool(you.has_usable_claws(true)) == (body == 1));
    REQUIRE(bool(you.has_usable_tentacles(true)) == (body == 2));
    const char* frames[] = {
        "You are %s empty-handed.", "You are %s empty-clawed.",
        "You are %s empty-tentacled.", "Your mouth is %s empty."
    };
    vector<string> outputs;
    for (bool already : {false, true})
    {
        const string when = already ? C_("empty-handed timing", "already")
                                    : C_("empty-handed timing", "now");
        const string expected = make_stringf(T_(frames[body]), when.c_str());
        const string output = observe_message([&] {
            canned_msg(already ? MSG_EMPTY_HANDED_ALREADY : MSG_EMPTY_HANDED_NOW);
        });
        CHECK(output.find(expected) != string::npos);
        if (language == lang_t::ZH)
        {
            CHECK(output.find("already") == string::npos);
            CHECK(output.find("now") == string::npos);
        }
        outputs.push_back(output);
    }
    REQUIRE(outputs.size() == 2);
    CHECK(outputs[0] != outputs[1]);
}

TEST_CASE("interface rereview: real manual exhaustion keeps the Throwing joke and actual training cost",
          "[zh-translation][interface-rereview][manual-exhaustion]")
{
    const skill_type skill = GENERATE(SK_FIGHTING, SK_THROWING);
    vector<pair<unsigned int, int>> results;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        issue10_world world;
        no_notes suppress_notes;
        unwind_var<bool> simulation(crawl_state.simulating_xp_gain, false);
        you.base_stats.init(10);
        you.experience_level = 1;
        you.skill_cost_level = 1;
        you.total_experience = 0;
        you.exp_available = calc_skill_cost(1);
        you.auto_training = false;
        you.train.init(TRAINING_DISABLED);
        you.train[skill] = TRAINING_ENABLED;
        you.training.init(0);
        you.training[skill] = 100;
        you.skill_manual_points[skill] = 1;
        const char* key = skill == SK_THROWING
            ? "You have finished your manual of %s and skilfully toss it away."
            : "You have finished your manual of %s and toss it away.";
        const string expected = make_stringf(T_(key), skill_name(skill));
        {
            rng::subgenerator random(23, 0x4b4d414e55414cULL);
            const string output = observe_message([] { train_skills(); });
            CHECK(output.find(expected) != string::npos);
            results.emplace_back(you.skill_points[skill], random2(1000000));
        }
        CHECK(you.skill_manual_points[skill] == 0);
        CHECK(you.exp_available == 0);
        CHECK(you.total_experience == calc_skill_cost(1));
        CHECK(you.skill_points[skill] == 2);
    }
    REQUIRE(results.size() == 2);
    CHECK(results[0] == results[1]);
}

TEST_CASE("residual rereview: actual immune and living spell effects use one display wrapper",
          "[zh-translation][residual-rereview][spell-immune]")
{
    issue10_world world;
    unwind_var<bool> saving(crawl_state.need_save, true);
    init_zap_index();
    monster_info owner(MONS_EARTHEN_TOME);
    owner.attitude = ATT_HOSTILE;
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        you.form = transformation::statue;
        REQUIRE(you.immune_to_hex(SPELL_PETRIFY));
        const string immune = spell_effect_string(SPELL_PETRIFY, &owner);
        CHECK(immune == T_("(immune)"));
        if (language == lang_t::ZH)
            CHECK(immune != "(immune)");
        else
            CHECK(immune == "(immune)");
        const int count = living_spell_count(SPELL_PETRIFY, false);
        CHECK(spell_effect_string(SPELL_CONJURE_LIVING_SPELLS, &owner)
              == make_stringf(T_("%dx%s"), count, immune.c_str()));

        you.form = transformation::none;
        REQUIRE_FALSE(you.immune_to_hex(SPELL_PETRIFY));
        const string chance = spell_effect_string(SPELL_PETRIFY, &owner);
        REQUIRE_FALSE(chance.empty());
        CHECK(spell_effect_string(SPELL_CONJURE_LIVING_SPELLS, &owner)
              == make_stringf(T_("%dx%s"), count, chance.c_str()));
        CHECK(spell_effect_string(SPELL_PETRIFY, nullptr).empty());
    }
}

#ifdef WIZARD
TEST_CASE("residual rereview: actual fsim human summary localizes without changing TSV",
          "[zh-translation][residual-rereview][fsim]")
{
    string canonical_tsv;
    string canonical_hit_summary;
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        fight_damage_stats stats("Player");
        const string human = stats.summary("A: ", false);
        CHECK(human == make_stringf(T_("%s%6s | No hits"), "A: ", "Player"));
        if (language == lang_t::ZH)
            CHECK(human.find("No hits") == string::npos);
        const string tsv = stats.summary("A:\t", true);
        CHECK(tsv == "A:\tPlayer\t0.0\t0\t0%\t0.0\t0\t0.00\t0.0");
        if (canonical_tsv.empty())
            canonical_tsv = tsv;
        CHECK(tsv == canonical_tsv);
        CHECK(fight_data::header(true)
              == "Damage source\tAvHitDam\tMaxDam\tAccuracy\tAvDam\tAvTime\tAvSpeed\tAvEffDam");
        stats.hits = 1;
        stats.av_hit_dam = 2.0;
        const string hit_summary = stats.summary("A: ", false);
        if (canonical_hit_summary.empty())
            canonical_hit_summary = hit_summary;
        CHECK(hit_summary == canonical_hit_summary);
    }
}

TEST_CASE("residual rereview: noninteractive wizard consumers retain their state contracts",
          "[zh-translation][residual-rereview][wizard]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    for (int i = UNRAND_START + 1; i < UNRAND_LAST; ++i)
        you.unique_items[i - UNRAND_START] = UNIQ_EXISTS;
    const string unrands = observe_message([] { wizard_unobtain_unrands(); });
    CHECK(unrands.find(T_("All unrands are now eligible to generate once again."))
          != string::npos);
    for (int i = UNRAND_START + 1; i < UNRAND_LAST; ++i)
        CHECK(you.unique_items[i - UNRAND_START] == UNIQ_NOT_EXISTS);
    unwind_var<branch_type> branch(you.where_are_you, BRANCH_DUNGEON);
    const string tide = observe_message([] { wizard_mod_tide(); });
    CHECK(tide.find(T_("Not in Shoals or no heightmap; tide not available."))
          != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(unrands.find("All unrands") == string::npos);
        CHECK(tide.find("Not in Shoals") == string::npos);
    }
}
#endif

TEST_CASE("residual rereview: burstshroom stats retain damage while localizing the label",
          "[zh-translation][residual-rereview][spore-damage]")
{
    issue10_world world;
    init_zap_index();
    monster_info spore(MONS_BURSTSHROOM);
    spore.hd = 6;
    spore.summoner_id = MID_NOBODY;
    const dice_def damage = zap_damage(ZAP_BURSTSPORE, spore.hd * 10, true, false);
    const string dice = make_stringf("%dd%d", damage.num, damage.size);
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        describe_info description;
        bool stats = false;
        get_monster_db_desc(spore, description, stats);
        REQUIRE(stats);
        const string output = description.body.str();
        CHECK(output.find(string(T_("Spore damage:")) + " " + dice) != string::npos);
        if (language == lang_t::ZH)
            CHECK(output.find("Spore damage:") == string::npos);
        CHECK(spore.type == MONS_BURSTSHROOM);
        CHECK(spore.hd == 6);
    }
}

TEST_CASE("legacy concat: ability description localizes title while looking up the canonical key",
          "[zh-translation][legacy-concat][ability-title]")
{
    issue10_world world;
    const ability_type ability = ABIL_ZIN_RECITE;
    const string canonical = ability_name(ability, true);
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        you.religion = GOD_ZIN;
        you.raw_piety = 100;
        const string body = getLongDescription(canonical + " ability");
        REQUIRE_FALSE(body.empty());
        const string output = get_ability_desc(ability, true);
        CHECK(starts_with(output, ability_name(ability) + "\n\n"));
        CHECK(output.find(body) != string::npos);
        CHECK(ability_name(ability, true) == canonical);
        if (language == lang_t::ZH)
            CHECK_FALSE(starts_with(output, canonical + "\n\n"));
    }
}

TEST_CASE("legacy concat: real unrand callbacks translate the complete literal message group",
          "[zh-translation][legacy-concat][equip-callbacks]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_mut_index();
    struct callback_case { int unrand; bool remove; const char *key; };
    const callback_case cases[] = {
        {UNRAND_WUCAD_MU, false, "The crystal ball is unable to connect with your magical essence."},
        {UNRAND_DEVASTATOR, false, "Time to lay down the shillelagh law."},
        {UNRAND_DRAGONSKIN, false, "You feel oddly protected from the elements."},
        {UNRAND_DRAGONSKIN, true, "You no longer feel protected from the elements."},
        {UNRAND_ZEPHYR, false, "You feel the wind guiding your aim."},
        {UNRAND_ZEPHYR, true, "The winds around you sigh wistfully and grow still."},
        {UNRAND_WYRMBANE, false, "You feel an overwhelming desire to slay dragons!"}
    };
    you.mutation[MUT_HP_CASTING] = 1;
    for (const auto &entry : cases)
    {
        const auto *unrand = get_unrand_entry(entry.unrand);
        bool show_messages = true;
        const string output = observe_message([&]
        {
            if (entry.remove)
            {
                REQUIRE(unrand->unequip_func);
                unrand->unequip_func(nullptr, &show_messages);
            }
            else
            {
                REQUIRE(unrand->equip_func);
                unrand->equip_func(nullptr, &show_messages, false);
            }
        });
        CHECK(output.find(T_(entry.key)) != string::npos);
        CHECK_FALSE(show_messages);
        if (language == lang_t::ZH)
            CHECK(output.find(entry.key) == string::npos);
    }
}

namespace
{
struct legacy_aux_accuracy : melee_attack
{
    legacy_aux_accuracy(actor *source, actor *target, bool hit)
        : melee_attack(source, target), adjustment(hit ? 100000 : -100000) { }
    int post_roll_to_hit_modifiers(int, bool) override { return adjustment; }
    const int adjustment;
};
}

TEST_CASE("legacy concat: actual auxiliary hit miss and list consumers translate their finite actions",
          "[zh-translation][legacy-concat][aux-actions]")
{
    const bool claws = GENERATE(false, true);
    const bool hit = GENERATE(false, true);
    vector<tuple<int, int, int>> results;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        bool observed = false;
        // The real miss path has an independent 1/30 auto-hit. Select a seed
        // by observing the actual consumer, without reproducing its RNG formula.
        for (int seed = 1; seed <= 64 && !observed; ++seed)
        {
            issue10_world world;
            no_notes suppress_notes;
            init_mut_index();
            you.base_stats.init(10);
            you.experience_level = 10;
            you.mutation[MUT_CLAWS] = claws ? 3 : 0;
            you.equipment.update();
            REQUIRE(you.has_usable_offhand());
            monster *target = world.place(MONS_ORC, coord_def(21, 20));
            target->hit_points = target->max_hit_points = 10000;
            legacy_aux_accuracy attack(&you, target, hit);
            const char *name = claws ? "off-hand claw" : "off-hand punch";
            const char *verb = claws ? "claw" : "punch";
            rng::subgenerator random(seed, 0x4a415558414354ULL);
            const string output = observe_message([&] { attack.player_do_aux_attack(UNAT_PUNCH); });
            if (attack.did_hit != hit)
                continue;
            observed = true;
            CHECK(attack.aux_attack == C_("auxiliary attack name", name));
            CHECK(attack.aux_verb == C_("auxiliary attack verb", verb));
            const vector<string> names = get_player_aux_names();
            CHECK(std::find(names.begin(), names.end(), attack.aux_attack) != names.end());
            if (hit)
                CHECK(output.find(attack.aux_verb) != string::npos);
            else
            {
                CHECK(output.find(make_stringf(T_("Your %s misses %s."),
                    attack.aux_attack.c_str(), target->name(DESC_THE).c_str())) != string::npos);
            }
            if (language == lang_t::ZH)
            {
                CHECK(attack.aux_attack != name);
                CHECK(attack.aux_verb != verb);
            }
            results.emplace_back(seed, target->hit_points, random2(1000000));
        }
        REQUIRE(observed);
    }
    REQUIRE(results.size() == 2);
    CHECK(results[0] == results[1]);
}

TEST_CASE("legacy concat: actual speech tokens localize atheists nameless and named gods",
          "[zh-translation][legacy-concat][speech-gods]")
{
    const god_type god = GENERATE(GOD_NO_GOD, GOD_NAMELESS, GOD_ZIN);
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        issue10_world world;
        monster *speaker = world.place(MONS_ORC, coord_def(21, 20));
        monster *foe = world.place(MONS_ORC, coord_def(22, 20));
        foe->god = god;
        speaker->foe = foe->mindex();
        const string name = god == GOD_NO_GOD ? T_("you")
            : god == GOD_NAMELESS ? T_("your god") : god_name(god, false);
        const string capital = god == GOD_NO_GOD ? T_("You")
            : god == GOD_NAMELESS ? T_("Your god") : uppercase_first(name);
        CHECK(do_mon_str_replacements("@foe_god@", *speaker) == name);
        CHECK(do_mon_str_replacements("@Foe_god@", *speaker) == capital);
        const char *frame = god == GOD_NO_GOD ? "%s are" : "%s is";
        CHECK(do_mon_str_replacements("@god_is@", *speaker)
              == make_stringf(C_("speech god copula", frame), name.c_str()));
        CHECK(do_mon_str_replacements("@God_is@", *speaker)
              == make_stringf(C_("speech god copula", frame), capital.c_str()));
        CHECK(foe->god == god);
        if (language == lang_t::ZH)
            CHECK(do_mon_str_replacements("@god_is@", *speaker).find("be") == string::npos);
    }
}

TEST_CASE("legacy concat: fixed god shop owners translate only at the display boundary",
          "[zh-translation][legacy-concat][shop-owners]")
{
    for (const char *owner : {"Gozag", "Cheibriados", "Zin", "Ada Custom", "zin"})
    {
        shop_struct shop;
        shop.type = SHOP_GENERAL;
        shop.pos = coord_def(21, 20);
        shop.shop_name = owner;
        shop.shop_type_name = "General";
        shop.shop_suffix_name = "Store";
        const string canonical = shop.shop_name;
        for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
        {
            TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
            const bool fixed = canonical == "Gozag" || canonical == "Cheibriados" || canonical == "Zin";
            const string name = fixed ? T_(canonical.c_str()) : canonical;
            const string prefix = apostrophise(name) + (language == lang_t::ZH ? "" : " ");
            CHECK(starts_with(shop_name(shop), prefix));
            CHECK(shop.shop_name == canonical);
            CHECK(shop.shop_type_name == "General");
            CHECK(shop.shop_suffix_name == "Store");
        }
    }
}

TEST_CASE("legacy concat: real monster list slime tag and recite diagnostic use display templates",
          "[zh-translation][legacy-concat][monster-details]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.religion = GOD_JIYVA;
    you.raw_piety = 200;
    monster_info slime(MONS_JELLY);
    slime.attitude = ATT_GOOD_NEUTRAL;
    REQUIRE(slime.fellow_slime());
    string line;
    int colour;
    slime.to_string(1, line, colour, true, nullptr, false);
    CHECK(line.find(T_(" (fellow slime)")) != string::npos);
    you.religion = GOD_ZIN;
    you.wizard = true;
    monster *target = world.place(MONS_ORC, coord_def(21, 20));
    target->set_hit_dice(10);
    monster_info orc(target);
    describe_info description;
    bool has_stats = false;
    get_monster_db_desc(orc, description, has_stats);
    REQUIRE(has_stats);
    CHECK(description.body.str().find(make_stringf(T_(" (Recite power:%d, Hit dice:%d)"),
          zin_recite_power(), orc.hd)) != string::npos);
}

TEST_CASE("legacy concat: real Lua spell-title binding preserves canonical lookup and errors",
          "[zh-translation][legacy-concat][spell-title-binding]")
{
    issue10_world world;
    lua_State *ls = clua.state();
    unwinder restore_spell_cache([] { init_spell_name_cache(); });
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        init_spell_name_cache();
        for (const char *canonical : {"Sting", "Metal Splinters"})
        {
            lua_stack_cleaner stack(ls);
            lua_getglobal(ls, "spells");
            lua_getfield(ls, -1, "title");
            REQUIRE(lua_isfunction(ls, -1));
            lua_pushstring(ls, canonical);
            REQUIRE(lua_pcall(ls, 1, 1, 0) == LUA_OK);
            REQUIRE(lua_isstring(ls, -1));
            const spell_type spell = spell_by_name(canonical, false);
            REQUIRE(is_valid_spell(spell));
            CHECK(string(lua_tostring(ls, -1)) == spell_title(spell));
            CHECK(string(spell_english_name(spell)) == canonical);
        }
        lua_stack_cleaner stack(ls);
        lua_getglobal(ls, "spells");
        lua_getfield(ls, -1, "title");
        lua_pushstring(ls, "not a real spell %s");
        CHECK(lua_pcall(ls, 1, 1, 0) != LUA_OK);
        REQUIRE(lua_isstring(ls, -1));
        CHECK(string(lua_tostring(ls, -1)).find("Invalid spell: not a real spell %s") != string::npos);
    }
}

TEST_CASE("legacy concat: actual numeric spell display helpers localize only the unavailable marker",
          "[zh-translation][legacy-concat][not-applicable]")
{
    issue10_world world;
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        // Unavailable ranges are omitted instead of claiming "N/A".
        CHECK(range_string(0).empty());
        CHECK(range_string(3, 5) == "3/5");
        CHECK(range_string(3, 5, 2) == "2-3/5");
    }
}

TEST_CASE("legacy concat: real detailed kill dump preserves canonical selectors and saved counts",
          "[zh-translation][legacy-concat][kill-dump]")
{
    issue10_world world;
    lua_State *ls = clua.state();
    lua_stack_cleaner stack(ls);
    const char *globals[] = {"kill_filter", "show_sorted_list", "group_kills", "holiness_list",
        "count_list", "symbol_list", "classic_list", "separator", "newline", "c_kill_list",
        "DUMP_KILL_BREAKDOWNS", "chk_lua_option"};
    vector<pair<const char *, int>> saved;
    for (const char *name : globals)
    {
        lua_getglobal(ls, name);
        saved.emplace_back(name, luaL_ref(ls, LUA_REGISTRYINDEX));
    }
    unwinder restore_globals([&]
    {
        for (const auto &entry : saved)
        {
            lua_rawgeti(ls, LUA_REGISTRYINDEX, entry.second);
            lua_setglobal(ls, entry.first);
            luaL_unref(ls, LUA_REGISTRYINDEX, entry.second);
        }
    });
    lua_newtable(ls);
    lua_setglobal(ls, "chk_lua_option");
    REQUIRE(CLua::loadfile(ls, "clua/kills.lua", true, false) == 0);
    REQUIRE(clua.pcall(0, 0) == 0);
    // Observe canonical category/holiness arguments, then delegate to the
    // actual loaded script. No kill list/header/summary implementation is mocked.
    REQUIRE(clua.execstring(R"(
        local actual = c_kill_list
        c_kill_list = function(a, who, needsep)
            if a then
                assert(who == nil or who == "collateral kills" or who == "others")
                for _, k in ipairs(a) do assert(kills.holiness(k) == "natural") end
            end
            return actual(a, who, needsep)
        end
    )", "legacy-real-kill-dump") == 0);
    int old_map[KC_NCATEGORIES];
    for (int i = 0; i < KC_NCATEGORIES; ++i)
    {
        old_map[i] = Options.kill_map[i];
        Options.kill_map[i] = i;
    }
    unwinder restore_map([&]
    {
        for (int i = 0; i < KC_NCATEGORIES; ++i)
            Options.kill_map[i] = old_map[i];
    });
    monster *orc = world.place(MONS_ORC, coord_def(21, 20));
    you.kills.record_kill(orc, KILL_YOU, false);
    you.kills.record_kill(orc, KILL_YOU, false);
    you.kills.record_kill(orc, KILL_MON, false);
    vector<unsigned char> before;
    writer save_before(&before);
    you.kills.save(save_before);
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        for (bool detailed : {false, true})
        {
            lua_pushboolean(ls, detailed);
            lua_setglobal(ls, "DUMP_KILL_BREAKDOWNS");
            // _sdump_kills directly appends this exact service result.
            const string output = you.kills.kill_info();
            CHECK(output.find(make_stringf(T_("Grand Total: %d creatures vanquished"), 3)) != string::npos);
            if (detailed)
            {
                CHECK(output.find(make_stringf(T_("%u creatures vanquished."), 2u)) != string::npos);
                CHECK(output.find(make_stringf(T_("%u creature vanquished."), 1u)) != string::npos);
                CHECK(output.find(T_("Monster Nature")) != string::npos);
                CHECK(output.find(T_("Natural Monsters")) != string::npos);
            }
            else
            {
                CHECK(output.find(make_stringf(T_("%s (%s)"), T_("Vanquished Creatures"),
                      T_("others"))) != string::npos);
            }
            CHECK(you.kills.total_kills() == 3);
            CHECK(clua.error.empty());
            vector<unsigned char> after;
            writer save_after(&after);
            you.kills.save(save_after);
            CHECK(after == before);
        }
    }
}

#if defined(UNIX) && !defined(DGL_MACRO_ABSOLUTE_PATH) && !defined(DGL_NAMED_MACRO_FILE)
TEST_CASE("legacy concat: actual macro save failure localizes only its message frame",
          "[zh-translation][legacy-concat][macro-save-error]")
{
    char pattern[] = "catch2-legacy-macro-XXXXXX";
    char *created = mkdtemp(pattern);
    REQUIRE(created);
    const string directory = created;
    const string blocked_file = directory + "/macro.txt";
    REQUIRE(mkdir(blocked_file.c_str(), 0700) == 0);
    unwinder cleanup([&]
    {
        rmdir(blocked_file.c_str());
        rmdir(directory.c_str());
    });
    unwind_var<string> macro_directory(Options.macro_dir, directory);
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        const string output = observe_message([] { macro_save(); });
        CHECK(output.find(make_stringf(T_("Couldn't open %s for writing!"),
                                      blocked_file.c_str())) != string::npos);
        CHECK(Options.macro_dir == directory);
    }
}
#endif

TEST_CASE("legacy markers: bane preview agrees with actual addition without changing current state",
          "[zh-translation][legacy-markers][bane-preview]")
{
    const bool existing = GENERATE(false, true);
    const bool accursed = GENERATE(false, true);
    issue10_world world;
    no_notes suppress_notes;
    init_mut_index();
    you.experience_level = 10;
    you.max_level = 10;
    you.experience = exp_needed(10);
    you.total_experience = 10000;
    you.skill_cost_level = calc_skill_cost_level(you.total_experience, 1);
    you.mutation[MUT_ACCURSED] = accursed ? 1 : 0;
    if (existing)
        REQUIRE(add_bane(BANE_LETHARGY, "test", 0, 100));
    const int before = you.banes[BANE_LETHARGY];
    const int old_preview = xl_to_remove_bane(BANE_LETHARGY);
    const int preview = xl_to_remove_bane(BANE_LETHARGY, 200, true);
    CHECK(you.banes[BANE_LETHARGY] == before);
    CHECK(xl_to_remove_bane(BANE_LETHARGY) == old_preview);
    REQUIRE(add_bane(BANE_LETHARGY, "Entering a Trove", 0, 200));
    CHECK(preview == xl_to_remove_bane(BANE_LETHARGY));
    CHECK(you.banes[BANE_LETHARGY] > before);
    if (existing)
        CHECK(preview > old_preview);

    Note original(NOTE_GET_BANE, BANE_LETHARGY, 0, "Entering a Trove");
    vector<unsigned char> bytes;
    writer output(&bytes);
    original.save(output);
    reader input(bytes);
    input.setMinorVersion(TAG_MINOR_VERSION);
    Note loaded;
    loaded.load(input);
    for (lang_t language : {lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        CHECK(loaded.name == "Entering a Trove");
        CHECK(loaded.describe(false, false, true).find(T_("Entering a Trove")) != string::npos);
        vector<unsigned char> after;
        writer saved(&after);
        loaded.save(saved);
        CHECK(after == bytes);
    }
}

TEST_CASE("legacy markers: fixed elementalist names preserve raw and arbitrary name identities",
          "[zh-translation][legacy-markers][fixed-monster-names]")
{
    for (const char *name : {"master elementalist", "grandmaster elementalist", "Ada %s Custom"})
    {
        monster_info monster(MONS_OCCULTIST);
        monster.mname = name;
        monster.mb.set(MB_NAME_REPLACE);
        for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
        {
            TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
            CHECK(monster.full_name(DESC_PLAIN) == T_(name));
            CHECK(monster.mname == name);
            CHECK(monster.db_name() == "occultist");
        }
    }
}

TEST_CASE("starcursed screams translate complete player and monster messages",
          "[zh-translation][monster-abilities][starcursed]")
{
    rng::subgenerator local_rng(0x53544152ULL, 0x5343524dULL);
    const char *const player_frames[] = {
        "The starcursed mass shrieks in your mind.",
        "A chorus of shrieks assaults your mind.",
        "A deafening chorus of shrieks assaults your mind!",
        "A cacophony of accursed wailing tears at your sanity!",
    };
    const coord_def positions[] = {
        {22, 20}, {22, 21}, {22, 22}, {21, 22},
        {20, 22}, {23, 20}, {23, 21}, {23, 22},
    };
    for (lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    for (int branch = 0; branch < 6; ++branch)
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        issue10_world world;
        no_notes suppress_notes;
        const bool player_target = branch < 4;
        const int count = player_target ? (branch == 0 ? 1 : branch == 1 ? 2 : branch == 2 ? 5 : 8) : 1;
        actor *target = &you;
        if (!player_target)
        {
            monster *victim = world.place(branch == 4 ? MONS_ORC : MONS_FIRE_VORTEX,
                                          coord_def(21, 20));
            victim->base_attitude = ATT_FRIENDLY;
            victim->hit_points = victim->max_hit_points = 100;
            REQUIRE((mons_intel(*victim) > I_BRAINLESS) == (branch == 4));
            target = victim;
        }
        monster *source = nullptr;
        for (int i = 0; i < count; ++i)
        {
            monster *voice = world.place(MONS_STARCURSED_MASS, positions[i]);
            // Seven HP retains a live screamer but makes splitting impossible.
            voice->hit_points = 7;
            voice->blob_size = 1;
            voice->target = target->pos();
            voice->foe = player_target ? MHITYOU : target->as_monster()->mindex();
            if (!source)
                source = voice;
        }
        REQUIRE(source->near_foe());
        const string raw_frame = player_target ? player_frames[branch]
            : branch == 4 ? "%s writhes in pain as voices assail %s mind."
                          : "%s writhes as voices assail %s being.";
        const string frame = T_(raw_frame.c_str());
        const string expected = player_target ? frame
            : make_stringf(frame.c_str(), target->name(DESC_THE).c_str(),
                            target->pronoun(PRONOUN_POSSESSIVE).c_str());
        const int old_hp = target->stat_hp();
        const string output = observe_message([&] {
            // Run the real chance-gated ability with a fixed local RNG stream.
            // Stop after its first scream/cooldown; this is not a seed search.
            for (int attempt = 0; attempt < 256
                 && !source->has_ench(ENCH_ABILITY_COOLDOWN); ++attempt)
            {
                mon_special_ability(source);
            }
        });
        CAPTURE(language, branch, count, output, expected);
        CHECK(source->has_ench(ENCH_ABILITY_COOLDOWN));
        CHECK(output.find(expected) != string::npos);
        CHECK(target->stat_hp() < old_hp);
        for (monster *voice : world.monsters)
            if (voice->type == MONS_STARCURSED_MASS)
                CHECK(voice->has_ench(ENCH_ABILITY_COOLDOWN));
        if (language == lang_t::ZH)
        {
            CHECK(frame != raw_frame);
            CHECK(output.find("writhes") == string::npos);
            CHECK(output.find("voices assail") == string::npos);
            CHECK(output.find("being.") == string::npos);
        }
    }
}

TEST_CASE("target descriptions translate silence without changing status identities",
          "[zh-translation][playtest-fixes][target-silence]")
{
    issue10_world world;
    monster* target = world.place(MONS_ORC, coord_def(20, 21));
    const coord_def pos = target->pos();
    unwind_var<map_cell> saved_memory(env.map_knowledge(pos), map_cell());
    env.map_knowledge(pos).set_monster(monster_info(target));

    for (const lang_t language : {lang_t::EN, lang_t::ZH, lang_t::EN})
    {
        TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
        you.duration[DUR_SILENCE] = 100;
        invalidate_agrid();
        REQUIRE(silenced(pos));
        for (int rebuild = 0; rebuild < 2; ++rebuild)
        {
            if (rebuild)
                i18n_cache_clear();
            const string display = cell_monster_description(pos, true);
            const string label = T_("silenced");
            CHECK(display.find(label) != string::npos);
            if (language == lang_t::ZH)
            {
                REQUIRE(label != "silenced");
                CHECK(display.find("silenced") == string::npos);
            }
            CHECK(cell_monster_description(pos, false).find(label) == string::npos);
            const auto details = get_monster_status_descriptors(monster_info(target));
            REQUIRE_FALSE(details.empty());
            CHECK(details.front().key == "silenced monstatus");
            CHECK(details.front().description == label);
        }
        you.duration[DUR_SILENCE] = 0;
        invalidate_agrid();
        CHECK_FALSE(silenced(pos));
        CHECK(cell_monster_description(pos, true).find(T_("silenced")) == string::npos);
    }
}

TEST_CASE("follower healing localizes singular and plural without changing English",
          "[zh-translation][r6-healing]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int count = GENERATE(1, 2);
    const bool greatly = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.religion = GOD_BEOGH;
    you.raw_piety = 160;
    vector<monster *> allies;
    for (int i = 0; i < count; ++i)
    {
        monster *ally = world.place(MONS_ORC_APOSTLE, coord_def(21 + i, 20));
        ally->base_attitude = ATT_FRIENDLY;
        ally->god = GOD_BEOGH;
        ally->flags |= MF_GOD_GIFT;
        ally->hit_points = 1;
        ally->max_hit_points = 200;
        REQUIRE(ally->is_divine_companion());
        allies.push_back(ally);
    }
    const string subject = count == 1 ? allies[0]->name(DESC_THE)
        : language == lang_t::ZH ? "你的追随者们" : "Your followers are";
    string text;
    // The production ability sometimes skips a heal. Retry its real entry
    // point rather than replacing RNG or copying the message expression.
    for (int attempt = 0; attempt < 100 && allies[0]->hit_points == 1; ++attempt)
    {
        you.props[BEOGH_DAMAGE_DONE_KEY] = greatly ? 100 : 20;
        msg::tee capture(text);
        beogh_ally_healing();
    }
    REQUIRE(allies[0]->hit_points > 1);
    const string expected = language == lang_t::ZH
        ? subject + "因你的英勇而" + (count == 1 ? "感到" : "")
          + (greatly ? "极其" : "") + "精神振奋。"
        : subject + " " + (count == 1 ? "is " : "")
          + (greatly ? " greatly " : "") + "invigorated by your bravery.";
    CAPTURE(language, count, greatly, text);
    CHECK(text.find(expected) != string::npos);
}

TEST_CASE("Player miscasts join expanded Chinese colours at the production display sink",
          "[zh-translation][r26-miscast-space]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool dust = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<bool> condense(Options.msg_condense_repeats, false);
    REQUIRE(you.see_cell(you.pos()));

    // Choose a real expanded database variant that exposes an internal space.
    // With zero level/failure, damage calculation draws no random numbers and
    // the alchemy miscast adds no poison. Replaying the seed reaches _do_msg
    // through the public gameplay entry point, without replacing the database.
    uint64_t selected_seed = 0;
    string raw;
    for (uint64_t seed = 1; seed <= 512; ++seed)
    {
        rng::subgenerator choice(seed, 260301);
        const string candidate = getSpeakString("alchemy miscast player");
        if (language == lang_t::ZH && candidate.find_first_of(
                "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789")
                != string::npos)
        {
            continue;
        }
        const string witness = language == lang_t::ZH
            ? (dust ? "尘云环绕着你" : "你的皮肤浮现出")
            : (dust ? "You are surrounded by clouds of" : "Your skin changes to");
        if (candidate.find(witness) != string::npos
            && candidate.find(' ') != string::npos
            && candidate.find_first_of("[]@") == string::npos)
        {
            raw = candidate;
            selected_seed = seed;
            break;
        }
    }
    CAPTURE(language, dust, raw, selected_seed);
    REQUIRE(selected_seed != 0);
    // These witnesses contain only Chinese words in ZH. Do not derive the
    // expected display by invoking the production space-normalisation helper.
    const string expected = (language == lang_t::ZH
        ? replace_all(raw, " ", "") + "。" : raw + ".");
    rng::subgenerator replay(selected_seed, 260301);
    const string emitted = observe_message([] {
        miscast_effect(you, nullptr, {miscast_source::wizard},
                       spschool::alchemy, 0, 0, "regression miscast");
    });
    CHECK(trimmed_string(emitted) == expected);
    CHECK(you.hp == 100);
    CHECK(you.duration[DUR_POISONING] == 0);
}

TEST_CASE("Adjectival weapon brands reach full inventory names and item examination",
          "[zh-translation][r28][r28-brand-names]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int variant = GENERATE(0, 1, 2, 3, 4);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const brand_type brands[] = { SPWPN_VAMPIRISM, SPWPN_ANTIMAGIC, SPWPN_HEAVY,
                                  SPWPN_SPECTRAL, SPWPN_DEVIOUS };
    const char * const english[] = { "vampiric", "antimagic", "heavy", "spectral", "devious" };
    const char * const chinese[] = { "吸血", "禁魔", "沉重", "幽魂", "狡诈" };
    item_def &item = you.inv[0];
    item.base_type = OBJ_WEAPONS;
    item.sub_type = WPN_DAGGER;
    item.brand = brands[variant];
    item.quantity = 1;
    item.flags = ISFLAG_IDENTIFIED;
    item.link = 0;
    item.slot = 'a';
    item.pos = ITEM_IN_INVENTORY;
    const string expected = language == lang_t::ZH
        ? string("+0 ") + chinese[variant] + "匕首"
        : string("+0 ") + english[variant] + " dagger";
    CAPTURE(language, variant, expected);
    CHECK(item.name(DESC_PLAIN) == expected);
    const InvEntry entry(item);
    CHECK(entry.get_fullname().find(expected) != string::npos);
    describe_info info;
    get_item_desc(item, info);
    CHECK(info.body.str().find(expected + ".") != string::npos);
    // The legal numeric separator and the canonical identity stay intact.
    CHECK(item.name(DESC_PLAIN).substr(0, 3) == "+0 ");
    {
        ScopedLangEn canonical;
        CHECK(item.name(DESC_DBNAME) == "dagger");
    }
}

TEST_CASE("Jinxbite uses the same full branded name at its real display sink",
          "[zh-translation][r28][r28-brand-sprite]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<bool> saving(crawl_state.need_save, false);
    const int index = get_mitm_slot();
    REQUIRE(index != NON_ITEM);
    unwind_var<item_def> restore_item(env.item[index]);
    item_def &dagger = env.item[index];
    dagger = item_def();
    dagger.base_type = OBJ_WEAPONS;
    dagger.sub_type = WPN_DAGGER;
    dagger.brand = SPWPN_HEAVY;
    dagger.quantity = 1;
    dagger.flags = ISFLAG_IDENTIFIED;
    monster *mon = world.place(MONS_ORC, coord_def(22, 20));
    REQUIRE(mon->pickup_item(dagger, true, true));
    REQUIRE(mon->weapon() == &dagger);
    mon->hit_points = mon->max_hit_points = 10000;
    const string expected = language == lang_t::ZH ? "+0 沉重匕首" : "+0 heavy dagger";
    string witness;
    for (uint64_t seed = 1; seed <= 128 && witness.empty(); ++seed)
    {
        rng::subgenerator choice(seed, 280403);
        string raw;
        {
            msg::tee capture(raw);
            attempt_jinxbite_hit(*mon);
        }
        const string message = formatted_string::parse_string(raw).tostring();
        if (message.find(expected) != string::npos)
            witness = message;
    }
    CAPTURE(language, expected, witness);
    CHECK_FALSE(witness.empty());
}

namespace
{
void r30_note_roundtrip(const Note& note)
{
    vector<unsigned char> bytes;
    writer output(&bytes);
    note.save(output);
    reader input(bytes);
    input.setMinorVersion(TAG_MINOR_VERSION);
    Note loaded;
    loaded.load(input);
    CHECK(loaded.type == note.type);
    CHECK(loaded.first == note.first);
    CHECK(loaded.second == note.second);
    CHECK(loaded.name == note.name);
    CHECK(loaded.desc == note.desc);
    vector<unsigned char> after;
    writer output_after(&after);
    loaded.save(output_after);
    CHECK(after == bytes);
}
}

TEST_CASE("Life notes keep natural count order and preserve singular English",
          "[zh-translation][r30][r30-life-notes]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int remaining = GENERATE(0, 1, 2);
    const bool gained = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const Note note(gained ? NOTE_GAIN_LIFE : NOTE_LOSE_LIFE, remaining);
    const string expected = language == lang_t::ZH
        ? string(gained ? "获得了一条命（剩余" : "失去了一条命（剩余")
            + to_string(remaining) + "条命）"
        : string(gained ? "Gained a life (" : "Lost a life (")
            + to_string(remaining) + (remaining == 1 ? " life remaining)" : " lives remaining)");
    CHECK(note.describe(false, false) == expected);
    r30_note_roundtrip(note);
}

TEST_CASE("Disjunction status keeps its actor and a four-column light",
          "[zh-translation][r30][r30-disjunction]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
#if defined(UNIX) && !defined(__ANDROID__)
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([&] { setlocale(LC_CTYPE, saved_locale.c_str()); });
    REQUIRE(ensure_utf8_ctype());
#endif
    init_duration_index();
    you.duration[DUR_DISJUNCTION] = 1000;
    status_info info;
    REQUIRE(fill_status_info(DUR_DISJUNCTION, info));
    CHECK(info.db_key == "Disjoin");
    CHECK(info.short_db_key == "disjoining");
    if (language == lang_t::ZH)
    {
        CHECK(info.light_text == "分离");
        CHECK(info.short_text == "空间分离中");
        CHECK(info.long_text == "你正在使周围的空间分离。");
        CHECK(strwidth(info.light_text) == 4);
        const string topbar = C_("topbar status", info.db_key.c_str());
        CHECK(topbar == "分离");
        CHECK(chop_string(topbar, 4, false) == "分离");
    }
    else
    {
        CHECK(info.light_text == "Disjoin");
        CHECK(info.short_text == "disjoining");
        CHECK(info.long_text == "You are disjoining your surroundings.");
    }
}
