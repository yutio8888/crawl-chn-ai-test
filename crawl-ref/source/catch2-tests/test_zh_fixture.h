#pragma once

#include "lang-t.h"

// ZhTranslationFixture — sets Options.language=ZH and clears the i18n cache so
// that T_(...) lookups consult dat/i18n/zh/source.txt during a catch2 test.
//
// Solves plan v2 Blocker B3: catch2-tests-executable defaults to
// lang_t::EN (lang_t::EN == 0, options.h), so without switching the language
// all T_(...) invocations return the English key unchanged and Layer 1
// scanning produces all-false-positives.
//
// Usage:
//   TEST_CASE_METHOD(ZhTranslationFixture, "zh: ...", "[zh-translation]") { ... }
//
// M1 acceptance: fixture smoke asserts
//   strcmp(T_("You hit %s."), "You hit %s.") != 0
// which proves dat/i18n/zh/source.txt was actually loaded and T_() returns
// a Chinese translation rather than the English key.

struct ZhTranslationFixture
{
    // Snapshots to restore on teardown so that any subsequent EN-default
    // test is unaffected.
    lang_t saved_lang;            // Options.language snapshot
    const char* saved_lang_name;   // Options.lang_name snapshot

    ZhTranslationFixture();
    ~ZhTranslationFixture();
};