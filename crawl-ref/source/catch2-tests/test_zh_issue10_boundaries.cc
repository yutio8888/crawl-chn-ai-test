#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "areas.h"
#include "cloud.h"
#include "database.h"
#include "describe.h"
#include "english.h"
#include "env.h"
#include "i18n.h"
#include "item-prop.h"
#include "item-use.h"
#include "losglobal.h"
#include "message.h"
#include "mon-info.h"
#include "mon-place.h"
#include "mon-util.h"
#include "movement-i18n.h"
#include "options.h"
#include "player.h"
#include "spl-selfench.h"
#include "spl-util.h"
#include "state.h"
#include "stringutil.h"
#include "test_zh_fixture.h"
#include "unwind.h"

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
    msg::tee capture(raw);
    emit();
    REQUIRE_FALSE(raw.empty());
    const string stored = get_last_messages(1, true);
    REQUIRE_FALSE(stored.empty());
    return stored;
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
    CHECK(glow.find(language == lang_t::ZH ? "发亮" : "glows") != string::npos);
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
    CHECK_FALSE(mon->is_constricted());
    CHECK_FALSE(constrictor->is_constricting());
    CHECK(mon->pos() == coord_def(20, 22));
    CHECK(escape.find(movement) != string::npos);
    if (language == lang_t::ZH)
    {
        CHECK(escape.find(movement + "s") == string::npos);
        CHECK(escape.find("挣脱了") != string::npos);
    }
    else
        CHECK(escape.find(movement + " free of ") != string::npos);
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
