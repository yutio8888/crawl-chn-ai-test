#include "catch_amalgamated.hpp"
#include "AppHdr.h"
#include "i18n.h"
#include "message.h"
#include "test_zh_fixture.h"

// Shared by the player-hit and visible-monster-hit display sinks in beam.cc.
string klown_pie_flavour_message(const char* flavour);

namespace
{
const pair<const char*, const char*> flavours[] = {
    {"plum", "李子"},
    {"lemon", "柠檬"},
    {"blueberry", "蓝莓"},
    {"cherry", "樱桃"},
    {"peanut brittle", "花生脆糖"},
    {"glitter", "闪粉"},
};
}

TEST_CASE_METHOD(EnTranslationFixture, "en: klown pie labels preserve the hit output",
                 "[zh-translation][klown-pie]")
{
    for (const auto& flavour : flavours)
    {
        const string text = klown_pie_flavour_message(flavour.first);
        CHECK(text == string(flavour.first) + "!");
        string original;
        {
            msg::tee capture(original);
            mprf("%s!", flavour.first);
        }
        REQUIRE_FALSE(original.empty());
        string actual;
        {
            msg::tee capture(actual);
            mprf("%s", text.c_str());
        }
        CHECK(actual == original);
    }
}

TEST_CASE_METHOD(ZhTranslationFixture, "zh: klown pie labels resolve their own context",
                 "[zh-translation][klown-pie]")
{
    for (const auto& flavour : flavours)
    {
        CHECK(string(C_("klown pie flavour", flavour.first)) == flavour.second);
        const string expected = string(flavour.second) + "！";
        const string text = klown_pie_flavour_message(flavour.first);
        CHECK(text == expected);
        msg::tee capture;
        mprf("%s", text.c_str());
        CHECK(capture.get_store().find(expected) != string::npos);
    }
}
