#pragma once

#include "lang-t.h"

// Translation fixtures set a requested display language, reconcile the
// language-specific TextDB layers, and restore both on teardown.
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

struct TranslationFixture
{
    lang_t saved_lang;            // Options.language snapshot
    const char* saved_lang_name;   // Options.lang_name snapshot

    TranslationFixture(lang_t language, const char* language_name);
    ~TranslationFixture();
};

struct ZhTranslationFixture : TranslationFixture
{
    ZhTranslationFixture();
};

struct EnTranslationFixture : TranslationFixture
{
    EnTranslationFixture();
};
