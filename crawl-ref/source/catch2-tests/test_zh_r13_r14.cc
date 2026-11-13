#include "catch_amalgamated.hpp"

#include "AppHdr.h"

#include "database.h"
#include "message.h"
#include "mutation.h"
#include "options.h"
#include "player.h"
#include "random.h"
#include "stringutil.h"
#include "syscalls.h"
#include "unwind.h"
#include "xom.h"

#include "test_zh_fixture.h"

namespace
{
struct pseudo_case
{
    const char *root;
    const char *chinese_choice;
    const char *chinese_witness;
    const char *feature;
    const char *english_feature;
    const char *item;
    bool head;
};

const pseudo_case cases[] = {
    {"feature dry", "水短暂地从", "从干涸喷泉中喷出", "干涸喷泉", "the dry fountain", "", false},
    {"underfoot water", "短暂地从你身边退开", "水短暂地从你身边退开了。", "水", "the water", "", false},
    {"feature lava", "喷出了火花", "熔岩喷出了火花！", "熔岩", "the lava", "", false},
    {"ears", "短暂地从你的耳朵里喷出", "短暂地从你的耳朵里喷出！", "", "", "", false},
    {"gizmo slot", "漏出了", "色的烟雾！", "", "", "奇械", false},
    {"cloak slot", "@head@", "你的斗篷短暂地缠住了你的头！", "", "", "斗篷", true},
    {"feature metal wall", "电流的卷须", "电流的卷须在金属墙上爬行。", "金属墙", "the metal wall", "", false},
    {"inventory singular", "振动", "你的法杖短暂地振动了。", "", "", "法杖", false},
    {"inventory plural", "闪起", "短暂地闪起", "", "", "法杖", false},
    {"offhand slot", "闪起", "你的法杖短暂地闪起", "", "", "法杖", false},
};
}

TEST_CASE("Xom pseudo-miscast final display joins Chinese after all substitutions",
          "[zh-translation][r13-r14][xom-space]")
{
    const string saved_locale = setlocale(LC_CTYPE, nullptr);
    unwinder restore_locale([&]() { setlocale(LC_CTYPE, saved_locale.c_str()); });
#if defined(UNIX) && !defined(__ANDROID__)
    REQUIRE(ensure_utf8_ctype());
#endif
    init_mut_index();
    unwind_var<player> restore_player(you);
    you = player();
    unwind_var<bool> condense(Options.msg_condense_repeats, false);
    for (lang_t language : {lang_t::EN, lang_t::ZH})
    {
        TranslationFixture mode(language, language == lang_t::ZH ? "zh" : nullptr);
        for (const auto &row : cases)
        {
            const bool zh = language == lang_t::ZH;
            string selected;
            for (uint64_t seed = 1; seed <= 256; ++seed)
            {
                rng::subgenerator choice(seed, 130014);
                string raw = getSpeakString("Xom " + string(row.root));
                if (!zh || raw.find(row.chinese_choice) != string::npos)
                {
                    if (*row.item)
                    {
                        raw = xom_bind_worn_item_message(
                            raw, zh ? row.item : "Wand A", row.head);
                    }
                    raw = replace_all(raw, "@the_feature@",
                                      zh ? row.feature : row.english_feature);
                    raw = replace_all(raw, "@The_feature@",
                                      zh ? row.feature : row.english_feature);
                    selected = maybe_pick_random_substring(raw);
                    break;
                }
            }
            CAPTURE(language, row.root, selected);
            REQUIRE_FALSE(selected.empty());
            REQUIRE(selected.find('@') == string::npos);
            const auto state = rng::current_generator().get_state();
            const auto count = rng::current_generator().get_count();
            msgwin_temporary_mode temporary;
            unwinder clear_messages([]() { msgwin_clear_temporary(); });
            msg::tee observed;
            xom_emit_pseudo_miscast_message(selected);
            const string emitted = observed.get_store();
            if (zh)
                CHECK(emitted.find(row.chinese_witness) != string::npos);
            else
                CHECK(emitted.find(selected) != string::npos);
            CHECK(rng::current_generator().get_state() == state);
            CHECK(rng::current_generator().get_count() == count);
        }

        msgwin_temporary_mode temporary;
        unwinder clear_messages([]() { msgwin_clear_temporary(); });
        msg::tee observed;
        const string latin = language == lang_t::ZH
            ? "法杖 Wand A 短暂地发光。"
            : "Your Wand A briefly glows.";
        xom_emit_pseudo_miscast_message(latin);
        CHECK(observed.get_store().find(latin) != string::npos);
    }
}
