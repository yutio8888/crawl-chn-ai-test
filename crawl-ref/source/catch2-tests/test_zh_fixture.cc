#include "AppHdr.h"

#include "test_zh_fixture.h"

#include "database.h"      // databaseSystemInit, i18n_cache_clear
#include "options.h"        // Options, lang_t

TranslationFixture::TranslationFixture(lang_t language,
                                       const char* language_name)
{
    saved_lang      = Options.language;
    saved_lang_name = Options.lang_name;

    Options.language  = language;
    Options.lang_name = language_name;
    databaseSystemInit();
    i18n_cache_clear();
}

TranslationFixture::~TranslationFixture()
{
    Options.language  = saved_lang;
    Options.lang_name = saved_lang_name;

    databaseSystemInit();
    i18n_cache_clear();
}

ZhTranslationFixture::ZhTranslationFixture()
    : TranslationFixture(lang_t::ZH, "zh")
{
}

EnTranslationFixture::EnTranslationFixture()
    : TranslationFixture(lang_t::EN, nullptr)
{
}
