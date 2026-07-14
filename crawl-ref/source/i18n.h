#pragma once

#include <cstddef>

// i18n.h — DCSS C++ source string internationalization
//
// T_("English")  — lookup translation in dat/i18n/<lang>/source.txt
// C_("ctx","en") — context-qualified lookup for disambiguation
// N_ with an English literal marks a stable deferred key (no lookup).
// NC_ additionally records a disambiguating context for extraction.
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

// Deferred translation markers. These deliberately return the English literal
// without touching i18n_storage; translate the selected key later with T_/C_.
template <std::size_t N>
constexpr const char* _i18n_deferred_literal(const char (&en)[N]) {
    return en;
}

template <std::size_t C, std::size_t N>
constexpr const char* _i18n_deferred_context(const char (&)[C],
                                             const char (&en)[N]) {
    return en;
}

// Concatenation with an empty literal makes non-literal arguments ill-formed,
// including both runtime pointers and named char arrays. Adjacent literals are
// accepted and folded by the compiler before reaching the constexpr helpers.
#define N_(en) _i18n_deferred_literal("" en)
#define NC_(ctx, en) _i18n_deferred_context("" ctx, "" en)
