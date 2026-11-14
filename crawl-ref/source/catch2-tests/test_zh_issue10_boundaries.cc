#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "areas.h"
#include "beam.h"
#include "cloud.h"
#include "cio.h"
#include "macro.h"
#include "tags.h"
#include "files.h"
#include "unicode.h"
#include "potion.h"
#include "god-passive.h"
#include "syscalls.h"
#include "species.h"
#include "makeitem.h"
#include "database.h"
#include "delay.h"
#include "terrain.h"
#include "mon-cast.h"
#include "coordit.h"
#include "describe.h"
#include "dungeon.h"
#include "english.h"
#include "env.h"
#include "format.h"
#include "god-abil.h"
#include "i18n.h"
#include "invent.h"
#include "lang-en-guard.h"
#include "item-name.h"
#include "item-prop.h"
#include "item-use.h"
#include "items.h"
#include "shopping.h"
#include "losglobal.h"
#include "message.h"
#include "mon-info.h"
#include "mon-place.h"
#include "mon-util.h"
#include "movement-i18n.h"
#include "mutation.h"
#include "status.h"
#include "options.h"
#include "orb.h"
#include "spl-transloc.h"
#include "spl-miscast.h"
#include "player.h"
#include "player-equip.h"
#include "spl-selfench.h"
#include "spl-damage.h"
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
        ? mon->name(DESC_THE)
          + (get<1>(row) ? movement + "！" : "闪烁了一下！")
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

TEST_CASE("terrain fragmentation translates only its display name",
          "[zh-translation][r6-terrain]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const auto row = GENERATE(table<dungeon_feature_type, const char *, const char *>({
        {DNGN_ROCK_WALL, "wall", "墙壁"},
        {DNGN_METAL_WALL, "metal wall", "金属墙"},
    }));
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_zap_index();
    monster *caster = world.place(MONS_KOBOLD_GEOMANCER, coord_def(20, 22));
    const coord_def target(24, 20);
    env.grid(target) = get<0>(row);
    unwind_var<unsigned short> colour(env.grid_colours(target), LIGHTGREY);
    invalidate_los();
    const string text = observe_message([&] {
        REQUIRE(cast_fragmentation(50, caster, target, false) == spret::success);
    });
    CAPTURE(language, text);
    const string expected = language == lang_t::ZH
        ? string(get<2>(row)) + "碎裂了！"
        : "The " + string(get<1>(row)) + " shatters!";
    CHECK(text.find(expected) != string::npos);
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
        ally->attitude = ATT_FRIENDLY;
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

TEST_CASE("Interrupted bee winding uses the caster as subject",
          "[zh-translation][r24-bee-winding]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *caster = world.place(MONS_ORC_WIZARD, coord_def(21, 21));
    REQUIRE(you.can_see(*caster));
    caster->props[CLOCKWORK_BEE_TARGET].get_int() = MID_PLAYER;
    caster->add_ench(mon_enchant(ENCH_CLOCKWORK_BEE_CAST, caster, 100));
    REQUIRE(caster->has_ench(ENCH_CLOCKWORK_BEE_CAST));
    caster->behaviour = BEH_SLEEP;
    const string interrupted = observe_message([&] { caster->apply_enchantments(); });
    CAPTURE(language, interrupted);
    CHECK_FALSE(caster->has_ench(ENCH_CLOCKWORK_BEE_CAST));
    if (language == lang_t::ZH)
        CHECK(interrupted.find("兽人巫师停止了给发条蜜蜂上弦。") != string::npos);
    else
        CHECK(lowercase_string(interrupted).find(
                  "the orc wizard stops winding its clockwork bee.") != string::npos);
}

TEST_CASE("Electric charge explains a stationary landing blocker in the display language",
          "[zh-translation][fts456][charge-blocker]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *blocker = world.place(MONS_OKLOB_PLANT, coord_def(21, 20));
    monster *target = world.place(MONS_ORC, coord_def(22, 20));
    REQUIRE(you.can_see(*blocker));
    REQUIRE(mons_class_is_stationary(blocker->type));
    string reason;
    CHECK(get_electric_charge_landing_spot(you, target->pos(), &reason).origin());
    const string name = blocker->name(DESC_THE);
    CHECK(reason == name + (language == lang_t::ZH
          ? "牢牢固定在你的路径上，无法移动。"
          : " is immovably fixed in your path."));
}

TEST_CASE("Orb pickup custom and null messages translate at the real display boundary",
          "[zh-translation][fts456][orb-display]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool silent = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<bool> saving(crawl_state.need_save, false);
    you.duration[DUR_SILENCE] = silent ? 100 : 0;
    invalidate_agrid(true);
    REQUIRE(silenced(you.pos()) == silent);
    struct orb_message
    {
        const char *audible;
        const char *flashing;
        const char *audible_zh;
        const char *flashing_zh;
    };
    const orb_message cases[] = {
        {"The Orb shrieks and becomes a dead weight against your magic!",
         "The Orb lets out a furious burst of light and becomes a dead weight against your magic!",
         "佐特宝珠尖啸着，沉重得让你的魔法无法拉动它！",
         "佐特宝珠愤怒地迸发出一阵强光，沉重得让你的魔法无法拉动它！"},
        {"The Orb shrieks as your magic touches it!",
         "The Orb lets out a furious burst of light as your magic touches it!",
         "你的魔法一碰到佐特宝珠，它就尖啸起来！",
         "你的魔法一碰到佐特宝珠，它就愤怒地迸发出一阵强光！"},
    };
    for (const auto &test : cases)
    {
        // A zero loudness avoids queuing unrelated noise propagation; the
        // production function still selects its real silence/flash branch.
        const string text = observe_message([&] {
            orb_pickup_noise(you.pos(), 0, test.audible, test.flashing);
        });
        const char *expected = language == lang_t::ZH
            ? (silent ? test.flashing_zh : test.audible_zh)
            : (silent ? test.flashing : test.audible);
        CAPTURE(language, silent, text);
        CHECK(text.find(expected) != string::npos);
    }
    const string fallback = observe_message([&] { orb_pickup_noise(you.pos(), 0); });
    const string expected = language == lang_t::ZH
        ? (silent ? "宝珠猛然迸发出愤怒的光芒！" : "宝珠发出了痛苦的尖叫！")
        : (silent ? "The Orb lets out a furious burst of light!"
                  : "The Orb lets out an agonising shriek!");
    CHECK(fallback.find(expected) != string::npos);
    you.duration[DUR_SILENCE] = 0;
    invalidate_agrid(true);
}

TEST_CASE("Sealing runes name an unseen caster in the active display language",
          "[zh-translation][r27][r27-seal-caster]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool visible = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    you.wizard_vision = false;
    // Seal Doors scans a full LOS_RADIUS square, slightly larger than the
    // shared fixture's original floor. Give that scan a clean, owned arena.
    for (radius_iterator ri(you.pos(), LOS_RADIUS, C_SQUARE); ri; ++ri)
    {
        const coord_def p = *ri;
        if (p.x >= 15 && p.x <= 30 && p.y >= 15 && p.y <= 30)
            continue;
        world.cells.emplace_back(p, env.grid(p), env.mgrid(p), env.level_map_ids(p));
        env.grid(p) = DNGN_FLOOR;
        env.mgrid(p) = NON_MONSTER;
        env.level_map_ids(p) = INVALID_MAP_INDEX;
    }
    const coord_def stairs(21, 20);
    unwind_var<map_cell> knowledge(env.map_knowledge(stairs));
    REQUIRE_FALSE(is_temp_terrain(stairs));
    env.grid(stairs) = DNGN_STONE_STAIRS_DOWN_I;
    unwinder unseal([&] { revert_terrain_change(stairs, TERRAIN_CHANGE_DOOR_SEAL); });
    invalidate_los();
    monster *warden = world.place(MONS_VAULT_WARDEN, coord_def(22, 20));
    if (!visible)
        warden->add_ench(mon_enchant(ENCH_INVIS, warden, 100));
    REQUIRE(warden->visible_to(&you) == visible);
    REQUIRE(warden->can_see(you));
    bolt spell;
    spell.target = you.pos();
    const string message = observe_message([&] {
        mons_cast(warden, spell, SPELL_SEAL_DOORS, MON_SPELL_WIZARD, false);
    });
    CHECK(env.grid(stairs) == DNGN_SEALED_STAIRS_DOWN);
    const string subject = visible ? warden->name(DESC_THE, true)
        : (language == lang_t::ZH ? "有人" : "Someone");
    const string expected = subject + (language == lang_t::ZH
        ? "激活了一道封印符文。" : " activates a sealing rune.");
    CAPTURE(language, visible, message);
    CHECK(trimmed_string(message) == expected);
}

TEST_CASE("Liquefaction renders a reflexive subject without printing a redundant argument",
          "[zh-translation][r27][r27-liquefaction]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    unwind_var<bool> saving(crawl_state.need_save, false);
    monster *caster = world.place(MONS_ORC_WIZARD, coord_def(22, 20));
    REQUIRE(you.can_see(*caster));
    bolt spell;
    spell.target = you.pos();
    const string message = observe_message([&] {
        mons_cast(caster, spell, SPELL_LEDAS_LIQUEFACTION, MON_SPELL_WIZARD, false);
    });
    const string expected = caster->name(DESC_THE) + (language == lang_t::ZH
        ? "将自身周围的地面液化！"
        : " liquefies the ground around " + caster->pronoun(PRONOUN_REFLEXIVE) + "!");
    CAPTURE(language, message);
    CHECK(message.find(expected) != string::npos);
    CHECK(caster->has_ench(ENCH_LIQUEFYING));
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

// Local-Tiles Catch2 bootstraps the real menu geometry and UI resources.
#ifdef USE_TILE_LOCAL
TEST_CASE("Ashenzari destroy-item prompt translates at the real inventory boundary",
          "[zh-translation][r29][r29-ash-prompt]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    item_def &item = you.inv[0];
    item.base_type = OBJ_ARMOUR;
    item.sub_type = ARM_ROBE;
    item.quantity = 1;
    item.link = 0;
    item.slot = 'a';
    item.pos = ITEM_IN_INVENTORY;
    item.flags = ISFLAG_IDENTIFIED | ISFLAG_CURSED;
    equip_item(SLOT_BODY_ARMOUR, 0, false, true);
    REQUIRE(you.equipment.get_first_slot_item(SLOT_BODY_ARMOUR) == &item);
    REQUIRE(item.cursed());
    REQUIRE(get_macro_buf_size() == 0);
    unwinder clear_keys([] { macro_clear_buffers(); });
    // Toggle the inventory list back to the actual text prompt, then cancel.
    macro_buf_add('?');
    macro_buf_add(CK_ESCAPE);
    const string message = observe_message([] { CHECK_FALSE(ashenzari_uncurse_item()); });
    const string expected = language == lang_t::ZH
        ? "解除哪件物品的诅咒并将其摧毁？ (? 菜单，Esc 退出)"
        : "Uncurse and destroy which item? (? for menu, Esc to quit)";
    CAPTURE(language, message);
    CHECK(message.find(expected) != string::npos);
    CHECK(item.cursed());
    CHECK(item.quantity == 1);
}

#endif

TEST_CASE("Shop names preserve English words and join only Chinese neighbours",
          "[zh-translation][r29][r29-shop]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool god_keeper = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    struct shop_case
    {
        const char* type;
        const char* suffix;
        const char* english_tail;
        const char* chinese_tail;
    };
    const shop_case cases[] = {
        { "", "", " Assorted Antiques", "杂项古董" },
        { "Platinum", "Reserve", " Platinum Reserve", " Platinum Reserve" },
        { "Basic", "Armour", " Basic Armour", " Basic Armour" },
        { "Saved type", "Saved suffix", " Saved type Saved suffix", " Saved type Saved suffix" },
        { "杂货", "商场", " 杂货 商场", "杂货商场" },
        { "珠宝", "Shop", " 珠宝 Shop", "珠宝 Shop" },
    };
    const string prefix = language == lang_t::ZH
        ? (god_keeper ? "哥萨戈的" : "Ada Vale的")
        : (god_keeper ? "Gozag's" : "Ada Vale's");
    for (const auto& row : cases)
    {
        shop_struct shop;
        shop.type = SHOP_GENERAL_ANTIQUE;
        shop.pos = coord_def(10, 10);
        shop.shop_name = god_keeper ? "Gozag" : "Ada Vale";
        shop.shop_type_name = row.type;
        shop.shop_suffix_name = row.suffix;
        const auto state = rng::current_generator().get_state();
        const auto count = rng::current_generator().get_count();
        const string expected = prefix + (language == lang_t::ZH
            ? row.chinese_tail : row.english_tail);
        CAPTURE(language, god_keeper, row.type, row.suffix);
        CHECK(shop_name(shop) == expected);
        CHECK(shop.shop_name == (god_keeper ? "Gozag" : "Ada Vale"));
        CHECK(shop.shop_type_name == row.type);
        CHECK(shop.shop_suffix_name == row.suffix);
        CHECK(rng::current_generator().get_state() == state);
        CHECK(rng::current_generator().get_count() == count);
    }
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

TEST_CASE("Skill note frames translate the whole sentence without changing stored IDs",
          "[zh-translation][r30][r30-skill-notes]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool gained = GENERATE(false, true);
    const bool fighting = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const skill_type skill = fighting ? SK_FIGHTING : SK_LONG_BLADES;
    const Note note(gained ? NOTE_GAIN_SKILL : NOTE_LOSE_SKILL, skill, 5);
    const string name = language == lang_t::ZH
        ? (fighting ? "格斗" : "长刃") : (fighting ? "Fighting" : "Long Blades");
    const string expected = language == lang_t::ZH
        ? name + (gained ? "技能达到等级5" : "技能降至等级5")
        : (gained ? "Reached skill level 5 in " + name : "Reduced skill " + name + " to level 5");
    CHECK(note.describe(false, false) == expected);
    r30_note_roundtrip(note);
}

TEST_CASE("Constructed defeat notes cover the defensive ally display frame",
          "[zh-translation][r30][r30-defeat-notes]")
{
    // Decoder/display coverage only: live ally producer reachability is unproved.
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const bool ally = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    const char* verbs[] = { "killed", "banished", "pacified", "bound", "slimified" };
    const char* chinese[] = { "击杀", "放逐", "安抚", "束缚", "黏液化" };
    for (unsigned i = 0; i < ARRAYSZ(verbs); ++i)
    {
        const Note note(NOTE_DEFEAT_MONSTER, MONS_ORC, ally, "Robin", verbs[i]);
        const string expected = language == lang_t::ZH
            ? (ally ? string("Robin（友军）被") + chinese[i] : string(chinese[i]) + "Robin")
            : (ally ? string("Robin (ally) was ") + verbs[i] : uppercase_first(verbs[i]) + " Robin");
        CHECK(note.describe(false, false) == expected);
        r30_note_roundtrip(note);
    }
}

TEST_CASE("State intensity is localized at all five stable gameplay consumers",
          "[zh-translation][r30][r30-intensity]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int action = GENERATE(0, 1, 2, 3, 4);
    const bool repeated = GENERATE(false, true);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    init_duration_index();
    unwind_var<bool> saving(crawl_state.need_save, false);
    string expected;
    string emitted;
    if (action == 0)
    {
        you.duration[DUR_BRILLIANCE] = repeated ? 10 : 0;
        emitted = observe_message([] { REQUIRE(get_potion_effect(POT_BRILLIANCE)->effect()); });
        expected = language == lang_t::ZH
            ? (repeated ? "你突然感到更加聪明了。" : "你突然感到聪明了。")
            : (repeated ? "You feel more clever all of a sudden." : "You feel clever all of a sudden.");
    }
    else if (action == 1)
    {
        you.religion = GOD_QAZLAL;
        you.raw_piety = 200;
        you.duration[DUR_QAZLAL_FIRE_RES] = repeated ? 10 : 0;
        emitted = observe_message([] { qazlal_element_adapt(BEAM_FIRE, 100); });
        expected = language == lang_t::ZH
            ? (repeated ? "你感到更加能抵御火焰。" : "你感到能抵御火焰。")
            : (repeated ? "You feel more protected from fire." : "You feel protected from fire.");
    }
    else if (action == 2)
    {
        you.duration[DUR_CONF] = repeated ? 10 : 0;
        emitted = observe_message([] { REQUIRE(confuse_player(10)); });
        expected = language == lang_t::ZH
            ? (repeated ? "你感到更加困惑了。" : "你感到困惑了。")
            : (repeated ? "You are more confused." : "You are confused.");
    }
    else if (action == 3)
    {
        you.duration[DUR_AGILITY] = repeated ? 10 : 0;
        emitted = observe_message([] { you.be_agile(40); });
        expected = language == lang_t::ZH
            ? (repeated ? "你突然感觉更加敏捷。" : "你突然感觉敏捷。")
            : (repeated ? "You suddenly feel more agile." : "You suddenly feel agile.");
    }
    else
    {
        you.duration[DUR_CONF] = repeated ? 10 : 0;
        emitted = observe_message([] { xom_take_action(XOM_BAD_CONFUSION, 10); });
        expected = language == lang_t::ZH
            ? (repeated ? "你感到更加困惑了。" : "你感到困惑了。")
            : (repeated ? "You are more confused." : "You are confused.");
    }
    CAPTURE(language, action, repeated, emitted, expected);
    CHECK(emitted.find(expected) != string::npos);
    if (language == lang_t::ZH)
        CHECK(emitted.find("更强的") == string::npos);
}

TEST_CASE("Missing species genus and adjective forms use the display fallback",
          "[zh-translation][r31][r31-species]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    int fallbacks = 0;
    for (int i = 0; i < NUM_SPECIES; ++i)
    {
        const species_type sp = static_cast<species_type>(i);
        const species_def& def = get_species_def(sp);
        if (!def.name)
            continue;
        for (const auto form : {species::SPNAME_PLAIN, species::SPNAME_GENUS,
                                species::SPNAME_ADJ})
        {
            INFO("species=" << def.name << " form=" << static_cast<int>(form));
            const char *raw = form == species::SPNAME_GENUS && def.genus_name
                ? def.genus_name : form == species::SPNAME_ADJ && def.adj_name
                ? def.adj_name : def.name;
            CHECK(species::name(sp, form, true) == raw);
            if (language == lang_t::EN)
                CHECK(species::name(sp, form) == raw);
            if (form != species::SPNAME_PLAIN
                && !(form == species::SPNAME_GENUS ? def.genus_name : def.adj_name))
            {
                ++fallbacks;
                CHECK(species::name(sp, form) == species::name(sp));
            }
        }
    }
    REQUIRE(fallbacks > 0);
    CHECK(species::name(SP_HUMAN, species::SPNAME_GENUS)
          == (language == lang_t::ZH ? "人类" : "Human"));
    CHECK(species::name(SP_HUMAN, species::SPNAME_ADJ)
          == (language == lang_t::ZH ? "人类" : "Human"));
    CHECK(species::name(SP_POLTERGEIST, species::SPNAME_PLAIN)
          == (language == lang_t::ZH ? "骚灵" : "Poltergeist"));
    CHECK(species::name(SP_POLTERGEIST, species::SPNAME_ADJ)
          == (language == lang_t::ZH ? "鬼魅" : "Ghostly"));
}

TEST_CASE("Frederick's real SpeakDB line receives a localized Human genus",
          "[zh-translation][r31][r31-frederick]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    issue10_world world;
    monster *frederick = world.place(MONS_FREDERICK, coord_def(21, 20));
    rng::subgenerator scoped_rng(0x310108ULL, 0x31000001ULL);
    string line;
    for (int i = 0; i < 128; ++i)
    {
        line = getSpeakString("Beogh Frederick triumphant");
        if (line.find("@player_genus@") != string::npos)
            break;
    }
    REQUIRE(line.find("@player_genus@") != string::npos);
    const string actual = do_mon_str_replacements(line, *frederick, S_SILENT);
    CHECK(actual == (language == lang_t::ZH
        ? "弗雷德里克叹了口气，\"你的同族只会拖你后腿，人类。\""
        : "Frederick sighs, \"Your brethren were only holding you back, Human.\""));
    CHECK(species::name(you.species, species::SPNAME_GENUS, true) == "Human");
}

TEST_CASE("Stable missile brands keep complete names and original short tags",
          "[zh-translation][r33][r33-missile]")
{
    const lang_t language = GENERATE(lang_t::EN, lang_t::ZH);
    const int quantity = GENERATE(1, 3);
    TranslationFixture translation(language, language == lang_t::ZH ? "zh" : nullptr);
    init_properties();
    struct missile_case
    {
        missile_type type;
        special_missile_type brand;
        const char *en_full;
        const char *en_plural;
        const char *zh_full;
        const char *en_short;
        const char *en_short_plural;
        const char *zh_short;
        const char *en_noun;
        const char *zh_noun;
    };
    const missile_case cases[] = {
        { MI_BOOMERANG, SPMSL_NORMAL,
          "boomerang", "boomerangs", "回旋镖",
          "boomerang", "boomerangs", "回旋镖", "boomerang", "回旋镖" },
        { MI_DART, SPMSL_POISONED,
          "poisoned dart", "poisoned darts", "涂毒飞镖",
          "dart (poison)", "darts (poison)", "飞镖 (毒素)", "dart", "飞镖" },
        { MI_DART, SPMSL_DISPERSAL,
          "dart of dispersal", "darts of dispersal", "空间驱离之飞镖",
          "dart (disperse)", "darts (disperse)", "飞镖 (驱)", "dart", "飞镖" },
        { MI_DART, SPMSL_DISJUNCTION,
          "dart of disjunction", "darts of disjunction", "空间分离之飞镖",
          "dart (disjunct)", "darts (disjunct)", "飞镖 (移位)", "dart", "飞镖" },
        { MI_BOOMERANG, SPMSL_CHAOS,
          "boomerang of chaos", "boomerangs of chaos", "混沌之回旋镖",
          "boomerang (chaos)", "boomerangs (chaos)", "回旋镖 (混沌)",
          "boomerang", "回旋镖" },
        { MI_JAVELIN, SPMSL_CHAOS,
          "javelin of chaos", "javelins of chaos", "混沌之标枪",
          "javelin (chaos)", "javelins (chaos)", "标枪 (混沌)", "javelin", "标枪" },
    };
    for (const auto& test : cases)
    {
        INFO("brand=" << test.brand << " type=" << test.type
             << " quantity=" << quantity << " language=" << static_cast<int>(language));
        REQUIRE(is_missile_brand_ok(test.type, test.brand, true));
        item_def item;
        item.base_type = OBJ_MISSILES;
        item.sub_type = test.type;
        item.brand = test.brand;
        item.quantity = quantity;
        item.flags = ISFLAG_IDENTIFIED;
        const string prefix = quantity == 1 ? "" : "3 ";
        const string full = prefix + (language == lang_t::ZH ? test.zh_full
            : quantity == 1 ? test.en_full : test.en_plural);
        const string short_name = prefix + (language == lang_t::ZH ? test.zh_short
            : quantity == 1 ? test.en_short : test.en_short_plural);
        CHECK(item.name(DESC_PLAIN) == full);
        CHECK(item.name(DESC_PLAIN, true) == short_name);
        CHECK(item.name(DESC_BASENAME)
              == (language == lang_t::ZH ? test.zh_noun : test.en_noun));
        CHECK(item.brand == test.brand);
        CHECK(item.quantity == quantity);
    }
    if (quantity == 1)
    {
        // The other consumer of "item ego prefix|of %s" already puts its
        // modifier first. Keep that valid armour case unchanged.
        item_def robe;
        robe.base_type = OBJ_ARMOUR;
        robe.sub_type = ARM_ROBE;
        robe.brand = SPARM_FIRE_RESISTANCE;
        robe.quantity = 1;
        robe.flags = ISFLAG_IDENTIFIED;
        CHECK(robe.name(DESC_PLAIN) == (language == lang_t::ZH
            ? "+0 火焰抗性之长袍" : "+0 robe of fire resistance"));
    }
}

TEST_CASE("Macro Lua errors translate only the frame and stop the real delay",
          "[zh-translation][r34]")
{
#ifdef CLUA_BINDINGS
    issue10_world world;
    lua_State *ls = clua.state();
    REQUIRE(ls);
    lua_stack_cleaner stack(ls);
    lua_getglobal(ls, "c_macro");
    const int saved = luaL_ref(ls, LUA_REGISTRYINDEX);
    unwinder restore([&]
    {
        lua_rawgeti(ls, LUA_REGISTRYINDEX, saved);
        lua_setglobal(ls, "c_macro");
        luaL_unref(ls, LUA_REGISTRYINDEX, saved);
    });
    unwind_var<string> error(clua.error);
    lua_pushcfunction(ls, [](lua_State *state) -> int
    {
        // This diagnostic deliberately matches a translated catalog key.
        lua_pushliteral(state, "You are poisoned.");
        return lua_error(state);
    });
    lua_setglobal(ls, "c_macro");
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture translation(language,
                                       language == lang_t::ZH ? "zh" : nullptr);
        clua.error.clear();
        const string emitted = observe_message([] { run_macro("r34-test"); });
        REQUIRE(clua.error.find("You are poisoned.") != string::npos);
        const string frame = language == lang_t::ZH ? "Lua错误：" : "Lua error: ";
        CHECK(emitted.find(frame + clua.error) != string::npos);
        CHECK(current_delay() == nullptr);
    }
#endif
}

TEST_CASE("Disjunction keeps a compact localized missile brand label",
          "[zh-translation][r34]")
{
    issue10_world world;
    item_def dart;
    dart.base_type = OBJ_MISSILES;
    dart.sub_type = MI_DART;
    dart.brand = SPMSL_DISJUNCTION;
    dart.quantity = 1;
    dart.flags = ISFLAG_IDENTIFIED;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture translation(language,
                                       language == lang_t::ZH ? "zh" : nullptr);
        const string label = missile_brand_name(dart, MBN_TERSE);
        CHECK(label == (language == lang_t::ZH ? "分离" : "disjunct"));
        CHECK(strwidth(label) == (language == lang_t::ZH ? 4 : 8));
        CHECK(dart.name(DESC_PLAIN, true).find("(" + label + ")") != string::npos);
    }
}
