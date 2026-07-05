#pragma once

// i18n.h — DCSS C++ source string internationalization
//
// T_("English")  — lookup translation in dat/i18n/<lang>/source.txt
// C_("ctx","en") — context-qualified lookup for disambiguation
//
// The 12th TextDB instance (SourceDB) provides the lookup.
// Falls back to the English key if no translation is found.

const char* i18n_source_lookup(const char* ctx, const char* en);
void i18n_cache_clear();

inline const char* T_(const char* en) {
    return i18n_source_lookup(nullptr, en);
}

inline const char* C_(const char* ctx, const char* en) {
    return i18n_source_lookup(ctx, en);
}
