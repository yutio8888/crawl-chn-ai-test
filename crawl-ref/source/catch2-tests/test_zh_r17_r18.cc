#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "i18n.h"
#include "item-prop.h"
#include "message.h"
#include "options.h"
#include "player.h"
#include "status.h"
#include "syscalls.h"
#include "traps.h"
#include "unwind.h"

#include "test_zh_fixture.h"

TEST_CASE("Held status sentences do not duplicate the passive marker",
          "[zh-translation][r17-r18][held-sentence]")
{
    init_properties();
    init_duration_index();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.attribute[ATTR_HELD] = 1;
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        const bool zh = language == lang_t::ZH;
        // Nets, magical nets, and webs share this one status producer.
        for (int kind = 0; kind < 3; ++kind)
        {
            you.props.erase(NET_IS_REAL_KEY);
            if (kind != 0)
                you.props[NET_IS_REAL_KEY].get_bool() = kind == 1;
            const string fragment = held_status();
            status_info info;
            REQUIRE(fill_status_info(STATUS_NET, info));
            CAPTURE(language, kind, fragment);
            CHECK(info.long_text == (zh
                ? (kind == 0 ? "你被蛛网缠住了。" : "你被网困住了。")
                : (kind == 0 ? "You are stuck in a web." : "You are held in a net.")));
            CHECK(fragment == (zh ? (kind == 0 ? "被蛛网缠住" : "被网困住")
                                  : (kind == 0 ? "stuck in a web" : "held in a net")));
            CHECK(info.db_key == "Held");
        }
        // The shared template has unrelated consumers and must stay unchanged.
        CHECK(string(T_("You are %s.")) == (zh ? "你被%s了。" : "You are %s."));
    }
}
#include "describe.h"
#include "hash.h"
#include "mon-info.h"
#include "mon-util.h"
#include "spl-util.h"
#include "state.h"
#include "transform.h"

namespace
{
bool contains_cjk_text(const string& text)
{
    return any_of(text.begin(), text.end(),
                  [](unsigned char ch) { return ch >= 128; });
}
}

TEST_CASE("Panlord description templates cover every body and both flight branches",
          "[zh-translation][r17-r18][panlord-body]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([&]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
#if defined(UNIX) && !defined(__ANDROID__)
    REQUIRE(ensure_utf8_ctype());
#endif
    init_monsters();
    init_spell_descs();
    unwind_var<bool> started(crawl_state.game_started, false);
    unwind_var<god_type> religion(you.religion, GOD_NO_GOD);
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        set<unsigned> bodies;
        for (unsigned n = 0; n < 4096 && bodies.size() < 14; ++n)
        {
            const string name = "Panlord " + to_string(n);
            const uint32_t seed = hash32(name.data(), name.size());
            const unsigned body = hash_with_seed(14, seed, 2);
            if (!bodies.insert(body).second)
                continue;
            for (bool flying : {false, true})
            {
                monster_info mi(MONS_PANDEMONIUM_LORD);
                mi.mname = name;
                mi.ghost_colour = RED;
                mi.mb.reset();
                if (flying)
                    mi.mb.set(MB_AIRBORNE);
                describe_info info;
                bool stats = false;
                get_monster_db_desc(mi, info, stats);
                const string text = info.body.str();
                CAPTURE(language, body, flying, name);
                REQUIRE(stats);
                CHECK(text.find(name) != string::npos);
                CHECK(text.find("的的") == string::npos);
                if (language == lang_t::ZH)
                    CHECK(text.find("躯体") != string::npos);
                else
                    CHECK(text.find(" body ") != string::npos);
            }
        }
        CHECK(bodies.size() == 14);
    }
}

TEST_CASE("Stable generated forms have localized player-facing catalog fields",
          "[zh-translation][r17-r18][forms-catalog]")
{
    init_properties();
    init_duration_index();
    unwind_var<player> restore_player(you);
    you = player();
    you.species = SP_HUMAN;
    you.skills[SK_SHAPESHIFTING] = 27;
    you.hp = you.hp_max = 100;
    ZhTranslationFixture chinese;
    for (int i = 1; i < NUM_TRANSFORMS; ++i)
    {
        const auto type = static_cast<transformation>(i);
        you.form = type;
        const Form* form = get_form(type);
        CAPTURE(i, form->short_name);
        CHECK(contains_cjk_text(form->get_short_name()));
        CHECK(contains_cjk_text(form->get_description(false)));
        CHECK(contains_cjk_text(form->get_description(true)));
        const string long_name = form->get_long_name();
        if (!long_name.empty())
            CHECK(contains_cjk_text(T_(long_name.c_str())));
        const string description = form->get_transform_description();
        if (!description.empty())
            CHECK(contains_cjk_text(T_(description.c_str())));
        if (!form->flesh_equivalent.empty())
            CHECK(contains_cjk_text(T_(form->flesh_equivalent.c_str())));
        for (const auto& pair : form->get_fakemuts())
        {
            if (!pair.first.empty())
            {
                INFO(pair.first);
                CHECK(contains_cjk_text(T_(pair.first.c_str())));
            }
            if (!pair.second.empty())
            {
                INFO(pair.second);
                CHECK(contains_cjk_text(T_(pair.second.c_str())));
            }
        }
        for (const auto& pair : form->get_bad_fakemuts())
        {
            if (!pair.first.empty())
            {
                INFO(pair.first);
                CHECK(contains_cjk_text(T_(pair.first.c_str())));
            }
            if (!pair.second.empty())
            {
                INFO(pair.second);
                CHECK(contains_cjk_text(T_(pair.second.c_str())));
            }
        }
        if (!form->special_dice_name.empty())
            CHECK(contains_cjk_text(T_(form->special_dice_name.c_str())));
    }
    CHECK(get_form(transformation::flux)->get_description(false)
          == "你充满了变形能量。");
    CHECK(get_form(transformation::flux)->get_description(true)
          == "你当时充满了变形能量。");
    {
        EnTranslationFixture english;
        CHECK(get_form(transformation::flux)->get_description(false)
              == "You are overflowing with transmutational energy.");
        CHECK(get_form(transformation::flux)->get_description(true)
              == "You were overflowing with transmutational energy.");
    }
}
