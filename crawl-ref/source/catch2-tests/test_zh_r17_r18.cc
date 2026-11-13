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
