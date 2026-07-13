/**
 * @file
 * @brief RAII guard that temporarily forces Options.language to English.
 *
 * Saves the current language, sets EN, and restores the saved value on
 * destruction. Skips the swap entirely if the language is already English
 * (avoiding needless recompute).
 *
 * Inspired by the established save/restore pattern in:
 *   - item-name.cc:4017-4086   (init_item_name_cache)
 *   - describe.cc:2769-2777    (Chinese DB fallback)
 *
 * Example:
 *   {
 *       ScopedLangEn en;
 *       string eng_desc = ::feature_description(feat, trap);
 *       // ... eng_desc is always English ...
 *   }
 *   // language restored to what it was before
 **/

#pragma once

#include "lang-t.h"
#include "options.h"

struct ScopedLangEn
{
    lang_t saved;

    ScopedLangEn()
        : saved(Options.language)
    {
        if (saved != lang_t::EN)
            Options.language = lang_t::EN;
    }

    ~ScopedLangEn()
    {
        Options.language = saved;
    }

    ScopedLangEn(const ScopedLangEn &) = delete;
    ScopedLangEn &operator=(const ScopedLangEn &) = delete;
};
