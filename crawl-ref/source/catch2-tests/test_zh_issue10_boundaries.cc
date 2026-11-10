#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "areas.h"
#include "cloud.h"
#include "database.h"
#include "describe.h"
#include "dungeon.h"
#include "english.h"
#include "env.h"
#include "format.h"
#include "i18n.h"
#include "item-prop.h"
#include "item-use.h"
#include "items.h"
#include "losglobal.h"
#include "message.h"
#include "mon-info.h"
#include "mon-place.h"
#include "mon-util.h"
#include "movement-i18n.h"
#include "mutation.h"
#include "status.h"
#include "options.h"
#include "player.h"
#include "player-equip.h"
#include "spl-selfench.h"
#include "spl-summoning.h"
#include "spl-util.h"
#include "state.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
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
        m->attitude = ATT_HOSTILE;
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

string target_description(const monster &m, bool ally_target)
{
    monster_info mi(m.type);
    mi.pos = m.pos();
    mi.attitude = m.attitude;
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
    CHECK(glow.find(language == lang_t::ZH ? "泛起绿光" : "glows") != string::npos);
    CHECK(armour.plus == 1);
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
    const string announcement_expected = language == lang_t::ZH
        ? mon->name(DESC_THE) + movement + "！"
        : mon->name(DESC_THE) + " " + movement + "!";
    CHECK(announcement.find(announcement_expected) != string::npos);
    if (language == lang_t::ZH)
        CHECK(announcement.find(movement + "s") == string::npos);
}

TEST_CASE("issue 10 monster target descriptions preserve direction and list shape",
          "[zh-translation][issue10]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *target = world.place(MONS_ORC, coord_def(20, 21));
    monster *ally = world.place(MONS_HOBGOBLIN, coord_def(21, 21));
    ally->attitude = ATT_FRIENDLY;
    ally->foe = target->mindex();
    const string single = target_description(*target, true);
    const string active = target_description(*ally, false);
    CHECK(single.find(ally->name(DESC_YOUR)) != string::npos);
    CHECK(active.find(target->name(DESC_THE)) != string::npos);

    monster *other = world.place(MONS_GOBLIN, coord_def(22, 21));
    other->attitude = ATT_FRIENDLY;
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

// PR #250 regression consumers adapted to stable APIs.
#include "clua.h"
#include "fight.h"
#include "target.h"
#include "stash.h"
#include "god-wrath.h"
#include "random.h"
#include "monster.h"

namespace {
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

}
TEST_CASE("playtest: area attack prompts resolve actions in their own context",
          "[zh-translation][playtest-fixes][prompts]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *ally = world.place(MONS_ORC, coord_def(21, 20));
    ally->attitude = ATT_FRIENDLY;
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
        "drain life", "hailstorm", "hurl reagents",
        "irradiate", "make a polar vortex", "poison",
        "refrigerate", "release a tremorstone", "Slouch", "unravel", "zap",
        "invoke Cleansing Flame",
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


TEST_CASE("playtest: corrosion translates canonical causes at player and monster sinks",
          "[zh-translation][playtest-fixes][corrosion]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
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

#include "mon-abil.h"
#include "notes.h"
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
    for (int branch = 0; branch < 5; ++branch)
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
            victim->attitude = ATT_FRIENDLY;
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
            : "%s writhes in pain as voices assail %s mind.";
        const string frame = T_(raw_frame.c_str());
        const string expected = player_target ? frame
            : make_stringf(frame.c_str(), target->name(DESC_THE).c_str(),
                            target->pronoun(PRONOUN_POSSESSIVE).c_str());
        const int old_hp = target->stat_hp();
        const string output = observe_message([&] {
            // Run the real chance-gated ability with a fixed local RNG stream.
            // Stop after its first scream/cooldown; this is not a seed search.
            for (int attempt = 0; attempt < 256
                 && !source->has_ench(ENCH_SCREAMED); ++attempt)
            {
                mon_special_ability(source);
            }
        });
        CAPTURE(language, branch, count, output, expected);
        CHECK(source->has_ench(ENCH_SCREAMED));
        CHECK(output.find(expected) != string::npos);
        CHECK(target->stat_hp() < old_hp);
        for (monster *voice : world.monsters)
            if (voice->type == MONS_STARCURSED_MASS)
                CHECK(voice->has_ench(ENCH_SCREAMED));
        if (language == lang_t::ZH)
        {
            CHECK(frame != raw_frame);
            CHECK(output.find("writhes") == string::npos);
            CHECK(output.find("voices assail") == string::npos);
            CHECK(output.find("being.") == string::npos);
        }
    }
}

#include "map-cell.h"
#include "directn.h"
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
        invalidate_agrid(true);
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
            CHECK(details.front() == label);
        }
        you.duration[DUR_SILENCE] = 0;
        invalidate_agrid(true);
        CHECK_FALSE(silenced(pos));
        CHECK(cell_monster_description(pos, true).find(T_("silenced")) == string::npos);
    }
}

TEST_CASE("stable followup raw movement escapes translate at the real sink",
          "[zh-translation][stable-followup][raw-escape]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *constrictor = world.place(MONS_BALL_PYTHON, coord_def(21, 20));
    const pair<const char*, const char*> verbs[] = {
        {"blink", "闪烁"}, {"hop", "跳跃"},
        {"leap", "飞扑"}, {"bolt", "疾冲"},
    };
    for (const auto &verb : verbs)
    {
        constrictor->start_constricting(you, CONSTRICT_MELEE);
        REQUIRE(you.is_constricted());
        const string output = observe_message([&] {
            // Spell and ability callers pass these exact raw identities.
            you.stop_being_constricted(false, verb.first);
        });
        CHECK_FALSE(you.is_constricted());
        CHECK_FALSE(constrictor->is_constricting());
        const string displayed = language == lang_t::ZH ? verb.second : verb.first;
        const string expected = make_stringf(T_("%s %s free of %s!"),
            you.name(DESC_THE).c_str(), displayed.c_str(),
            lowercase_string(constrictor->name(DESC_THE)).c_str());
        CAPTURE(language, verb.first, output, expected);
        CHECK(output.find(expected) != string::npos);
        if (language == lang_t::ZH)
            CHECK(output.find(verb.first) == string::npos);
    }
    // Blinkbolt's verb context must not replace the projectile noun.
    CHECK(string(T_("bolt")) == (language == lang_t::ZH ? "弩箭" : "bolt"));
}

TEST_CASE("stable followup Golden Breath bad target prompt localizes its action",
          "[zh-translation][stable-followup][bad-target]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *ally = world.place(MONS_ORC, coord_def(21, 20));
    ally->attitude = ATT_FRIENDLY;
    action_prompt_capture captured;
    REQUIRE(warn_about_bad_targets(SPELL_GOLDEN_BREATH, {ally->pos()},
                                   nullptr, "Breathe anyway?"));
    const string expected = language == lang_t::ZH ? "仍要吐息吗？" : "Breathe anyway?";
    CHECK(captured.prompt.find(expected) != string::npos);
    CHECK(captured.prompt.find(ally->name(DESC_THE)) != string::npos);
    if (language == lang_t::ZH)
        CHECK(captured.prompt.find("Breathe anyway?") == string::npos);
}

TEST_CASE("stable followup damage rating keeps its localized label and full stop",
          "[zh-translation][stable-followup][damage-rating]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_mut_index();
    init_duration_index();
    you.equipment.items.clear();
    you.equipment.update();
    REQUIRE(you.weapon() == nullptr);
    // SourceDB lookup is case-folded: the existing unarmed key is sufficient.
    CHECK(string(T_("Unarmed")) == (language == lang_t::ZH ? "空手" : "Unarmed"));
    const string output = observe_message([] { display_char_status(); });
    const string rating = damage_rating(nullptr);
    const string expected = language == lang_t::ZH
        ? "空手的伤害评级约为" + rating + "。"
        : "Your damage rating with Unarmed is about " + rating + ".";
    CHECK(output.find(expected) != string::npos);
}
