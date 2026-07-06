#include "AppHdr.h"

#include "test_zh_fixture.h"

#include "database.h"      // databaseSystemInit, i18n_cache_clear
#include "options.h"       // Options, lang_t

// `Options.lang_name` is `const char*` (options.h:836); the existing code
// stores pointers into the lang_data table (which has program lifetime) or
// `nullptr` for English. Our fixture stores a literal "zh" (also static
// storage duration), so it's safe even if not enumerated in the lang table.
namespace {
constexpr const char* ZH_LANG_NAME = "zh";
}

ZhTranslationFixture::ZhTranslationFixture()
{
    saved_lang      = Options.language;
    saved_lang_name = Options.lang_name;

    // Switch the global Options to Chinese and purge the i18n cache so
    // subsequent T_(...) calls re-resolve against dat/i18n/zh/source.txt
    // (database.cc / i18n_source_lookup).
    //
    // We deliberately reach into the public fields rather than call
    // Options.set_lang(...) which is private (options.h:1016); plan v2 §2.2
    // named `set_lang` but the public API surface is the two members.
    Options.language  = lang_t::ZH;
    Options.lang_name = ZH_LANG_NAME;

    // Catch2's main (test_main.cc + fake-main.hpp) skips crawl_init_data()
    // (startup.cc), so the TextDB layers are never opened. databaseSystemInit()
    // opens all AllDBs[] entries lazily and reads source.txt via
    // datafile_path() (dat/ resolved relative to crawl-ref/source CWD).
    // Without this call, _query_database always returns an empty string,
    // so T_() falls back to the English key and every enumerator mis-fires.
    databaseSystemInit();
    i18n_cache_clear();
}

ZhTranslationFixture::~ZhTranslationFixture()
{
    // Restore the previous language. Snapshot pointers are valid because
    // they originally came from `Options.lang_name`, which is either null
    // (English) or a static-storage pointer owned by `get_lang_data()`.
    Options.language  = saved_lang;
    Options.lang_name = saved_lang_name;
    i18n_cache_clear();
}