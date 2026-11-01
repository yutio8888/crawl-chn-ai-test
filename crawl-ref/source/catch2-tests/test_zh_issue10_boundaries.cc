#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "act-iter.h"
#include "areas.h"
#include "beam.h"
#include "cloud.h"
#include "clua.h"
#include "database.h"
#include "describe.h"
#include "directn.h"
#include "dungeon.h"
#include "english.h"
#include "env.h"
#include "format.h"
#include "ghost.h"
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
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "transform.h"
#include "unwind.h"
#include "xom.h"

#include <functional>
#include <tuple>

namespace
{
// Reuse the real allocator and the small lit-floor fixture convention from
// the monspeak consumer tests. Multiple actors let targeting and constriction
// run through their actual mid/foe lookup paths.
struct issue10_world
{
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
    CHECK(announcement.find(mon->name(DESC_THE) + " " + movement + "!")
          != string::npos);
    if (language == lang_t::ZH)
        CHECK(announcement.find(movement + "s") == string::npos);
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

TEST_CASE("issue 10 Xom cleaving describes both weapon variants completely",
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
    const string message = observe_message([] { xom_take_action(XOM_GOOD_CLEAVING, 10); });
    CAPTURE(language, message);
    if (language == lang_t::ZH)
    {
        const string suffix = weapon == WPN_HAND_AXE
            ? "看起来很锋利（一如既往）。" : "看起来很锋利。";
        CHECK(message.find(item.name(DESC_YOUR) + suffix) != string::npos);
        CHECK(message.find("sharp") == string::npos);
        CHECK(message.find("look") == string::npos);
    }
    else
    {
        const string suffix = weapon == WPN_HAND_AXE
            ? " looks sharp (like it always does)." : " looks sharp.";
        CHECK(message.find(item.name(DESC_YOUR) + suffix) != string::npos);
    }
    CHECK(you.duration[DUR_CLEAVE] > 0);
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
    const string subject = shot.defender_name(false);
    const string proj = shot.projectile_name();
    string method;
    if (protection == 1)
        method = T_(" with an invisible shield");
    else if (protection == 2)
        method = T_(" with a divine shield");
    else if (protection == 3)
        method = T_(" with ") + you.pronoun(PRONOUN_POSSESSIVE)
                 + " " + you.shield()->name(DESC_PLAIN);
    const int hp = you.hp;
    const string message = observe_message([&] { shot.handle_phase_blocked(); });
    INFO(message);
    CHECK(you.hp == hp);
    CHECK(shot.damage_done == 0);
    CHECK(shot.reflected == (protection != 0));
    CHECK(shot.range_used == (protection ? 0 : BEAM_STOP));
    if (language == lang_t::EN)
    {
        const string ending = protection ? "... and reflect it back!" : ".";
        CHECK(message == subject + " block the " + proj + method + ending + "\n");
    }
    else
    {
        const string verb = you.verb_for_display(NC_("verb", "block"), "verb");
        CHECK(message.find(verb) != string::npos);
        CHECK(message.find(proj) != string::npos);
        if (protection)
            CHECK(message.find(method) < message.find(verb));
        CHECK(message.find(verb) < message.find(proj));
        CHECK(message.find(" block ") == string::npos);
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
