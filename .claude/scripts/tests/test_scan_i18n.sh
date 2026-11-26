#!/bin/bash
# test_scan_i18n.sh — Run scan_i18n.py against test fixtures, diff expected output
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SCAN_I18N="$SCRIPT_DIR/../scan_i18n.py"
FIXTURES="$SCRIPT_DIR/fixtures"
EXPECTED="$SCRIPT_DIR/expected"
PASS=0
FAIL=0

assert_output() {
    local name="$1"
    local actual="$2"
    local expected="$3"
    if diff -u "$expected" "$actual" > /tmp/test_diff_$$.txt 2>&1; then
        echo "  PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name"
        cat /tmp/test_diff_$$.txt
        FAIL=$((FAIL + 1))
    fi
    rm -f /tmp/test_diff_$$.txt
}

assert_status() {
    local name="$1"
    local expected="$2"
    local actual="$3"
    if [ "$actual" -eq "$expected" ]; then
        echo "  PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (expected exit $expected, got $actual)"
        FAIL=$((FAIL + 1))
    fi
}

assert_contains() {
    local name="$1"
    local needle="$2"
    local actual="$3"
    if grep -Fq -- "$needle" "$actual"; then
        echo "  PASS: $name"
        PASS=$((PASS + 1))
    else
        echo "  FAIL: $name (missing: $needle)"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== scan_i18n.py Test Suite ==="
echo ""

# ── missing-t ──
echo "--- missing-t ---"
python3 "$SCAN_I18N" missing-t "$FIXTURES/missing-t/" > /tmp/actual_missing_t.txt 2>&1 || true
assert_output "missing-t: default CLI remains backward compatible" \
    /tmp/actual_missing_t.txt "$EXPECTED/missing-t_untranslated.txt"

# ── missing-t regression ──
python3 "$SCAN_I18N" missing-t "$FIXTURES/missing-t/translated_sample.cc" > /tmp/actual_mt_reg.txt 2>&1 || true
assert_output "missing-t: regression (no false positives)" \
    /tmp/actual_mt_reg.txt "$EXPECTED/missing-t_regression.txt"

# ── missing-t multiline mprf ──
MULTILINE_MT_DIR=$(mktemp -d)
cat > "$MULTILINE_MT_DIR/multiline.cc" <<'EOF'
void test_multiline()
{
    mprf(MSGCH_INTRINSIC_GAIN,
         "Your demonic ancestry asserts itself...");
    mprf(MSGCH_INTRINSIC_GAIN,
         T_("Welcome back to level %d!"), 2);
    mprf(T_(true
         ? "Wrapped ternary."
         : "Wrapped ternary."));
    mprf(MSGCH_DIAGNOSTICS,
         "Diagnostic message.");
    // Translated replacement arg must not mask an unwrapped format string
    mprf(MSGCH_INTRINSIC_GAIN,
         "Your scales start turning %s.",
         T_(species::scale_type(you.species)));
    // Same-line bare format string + T_("...") replacement arg
    mprf(MSGCH_INTRINSIC_GAIN, "Your %s glows.", T_("skin"));
    // Inline block comment before closing paren must not leak into next stmt
    mpr(
         already_translated /* owned text */);
    auto id = "internal key";
    // Inline block comment on first line or continuation line before literal
    mpr(/* player warning */
         "You fall!");
    mpr(
         /* player warning */ "You stumble!");
    // Adjacent C++ string literals split across lines (both first-line & continuation)
    mprf(MSGCH_WARN, "%s "
         "falls!", name);
    mprf(MSGCH_WARN,
         "%s "
         "stumbles!", name);
    // (channel, int param with string subscript, fmt) must report fmt, not subscript
    mprf(MSGCH_WARN, you.props["piety"].get_int(),
         "Piety warning!");
    // Dynamic format arg followed by props["internal_key"] must NOT flag internal_key
    mprf(localized_fmt.c_str(),
         you.props["internal_key"].get_int());
    // Mixed diagnostic + player-visible channel ternary must still be flagged
    mprf(is_diag ? MSGCH_DIAGNOSTICS : MSGCH_WARN,
         "Mixed channel warning!");
    // Call spanning more than 8 physical lines must still be caught
    mprf(
         cond1
         ? MSGCH_WARN
         : cond2
         ? MSGCH_WARN
         : cond3
         ? MSGCH_WARN
         : cond4
         ? MSGCH_WARN
         : MSGCH_PLAIN,
         "Deep multiline warning!");
    // Channel variable such as veto_channel must not hide bare format string
    mprf(veto_channel, "Veto warning!");
    // Mixed-channel ternary with string literal in condition must report message, not condition
    mprf(mode == "debug" ? MSGCH_DIAGNOSTICS : MSGCH_WARN, "Condition warning!");
    // Dynamic const char *fmt variable must NOT promote replacement literal arg
    mprf(MSGCH_WARN, fmt, "orc");
    // Pass-through make_stringf inside mpr must still flag unwrapped format, not wrapped/dynamic
    mpr(make_stringf("You lose %d HP.", n));
    mpr(make_stringf(T_("You gain %d HP."), n));
    mpr(make_stringf(fmt, "orc"));
    // Subscript arithmetic (formats[i + 1]) must NOT be treated as int param
    mprf(MSGCH_WARN, formats[i + 1], "orc");
    // Multiline nested make_stringf must not emit stray [STR] or duplicate findings
    mpr(
         make_stringf(fmt, "orc"));
    mpr(
         make_stringf("Multiline nested %d HP.", n));
}
void test_channel_decl(msg_channel_type fallback)
{
    mprf(fallback, "Fallback channel warning!");
}
void test_char_decl(const char *fallback)
{
    mprf(fallback, "orc");
}
void test_shadowed_channel(msg_channel_type fallback)
{
    {
        const char *fallback = "x";
        mprf(fallback, "orc");
    }
    mprf(fallback, "After shadow!");
    // Explicit channel + continuation dynamic make_stringf must not emit stray [STR]
    mprf(MSGCH_WARN,
         make_stringf(fmt, "orc").c_str());
    // Skipped diagnostic channel + continuation make_stringf must not emit stray [STR]
    mprf(MSGCH_DIAGNOSTICS,
         make_stringf("diag %s", x).c_str());
    // for-initializer shadow must end after the loop body
    for (const char *fallback = text; *fallback; ++fallback)
    {
        mprf(fallback, "orc");
    }
    mprf(fallback, "After loop!");
    // (channel, int param, continuation dynamic make_stringf) must not emit stray [STR]
    mprf(MSGCH_WARN, 1,
         make_stringf(fmt, "orc").c_str());
    // Unbraced for-loop body containing '{' char literal must still end shadow at ';'
    for (const char *fallback = text; *fallback; ++fallback)
        putchar('{');
    mprf(fallback, "After unbraced loop!");
    // Declared int variable as channel param must cover continuation dynamic make_stringf
    int n = 1;
    mprf(MSGCH_WARN, n,
         make_stringf(fmt, "orc").c_str());
    mprf(MSGCH_WARN, n,
         "Declared int param warning!");
    // Raw string containing fake declaration must NOT shadow channel parameter
    auto sample = R"("const char *fallback;")";
    mprf(fallback, "After raw string!");
    // C++14 digit separator before raw string containing '/* must not swallow next mprf
    auto big_num = 1'000;
    auto tricky_raw = R"('/*)";
    mprf(MSGCH_WARN, "After digit sep and raw string!");
    // Keyword immediately before char literal (`case'a':`) must NOT be treated as digit separator
    switch (x) { case'a': break; }
    auto tricky_raw2 = R"('/*)";
    mprf(MSGCH_WARN, "After case char literal!");
    // In-call C++14 digit separators in ternary channel and int param
    mprf(n > 1'000 ? MSGCH_WARN : MSGCH_PLAIN, "In-call digit sep!");
    mprf(MSGCH_WARN, 1'000'000, "Digit sep int param!");
    // Leading-dot C++14 float digit separator immediately after keyword (`return.1'25`)
    auto lead_dot = []() -> double { return.1'25; };
    auto tricky_raw3 = R"('/*)";
    mpr("After leading-dot digit sep!");
    // Raw string format literal with embedded quotes
    mprf(R"("Raw danger!")");
    // Brace-initialized std::string and braced-init-list message literals
    mpr(std::string{"Brace string danger!"});
    mpr({"Braced init danger!"});
    // `auto`-deduced channel variable
    auto dest = MSGCH_WARN;
    mprf(dest, "Auto channel danger!");
    // Char literal promoted to int channel param
    mprf(MSGCH_WARN, 'a', "Char param danger!");
    // Globally / enum-qualified skipped diagnostic/error channels must stay skipped
    mprf(::MSGCH_ERROR, "Qualified internal error");
    mprf(msg_channel_type::MSGCH_DEBUG, "Enum-qualified debug");
    // Nested make_stringf inside non-passthrough helper must NOT be hidden by MSG span
    mpr(block_event_string(defender,
                           make_stringf("the %s", proj_name.c_str()),
                           reflected));
    // Raw string containing fake multiline mprf(...) must NOT be discovered as a real call
    const char *doc_example = R"(
        mprf(
            "Example only.");
    )";
}
void unsigned_param_test(unsigned n, unsigned long long int m) {
    mprf(MSGCH_WARN, n, "An alarm sounds.");
    mprf(MSGCH_WARN, m, "Long long alarm.");
    int x = 0, y = 1;
    mprf(MSGCH_WARN, y, "Multi-decl alarm.");
    for (int i = 0, j = 1; i < 1; ++i)
        mprf(MSGCH_WARN, j, "For multi-decl alarm.");
    mpr(block_event_string(defender, make_stringf("same-line %s", name), reflected));
}
void round14_regressions(unsigned const char uc, char volatile cv, int idx) {
    mprf(MSGCH_WARN, uc, "Unsigned const char warning.");
    mprf(MSGCH_WARN, cv, "Volatile char warning.");
    msg_channel_type channels[] = { MSGCH_WARN };
    mprf(channels[idx], "Channel array warning.");
    int params[] = { 1 };
    mprf(MSGCH_WARN, params[idx], "Param array warning.");
#if 1
    msg_channel_type destination = MSGCH_WARN;
#else
    const char *destination = "unused";
#endif
    mprf(destination, "Active branch channel warning.");
    /* "Developer note" */ cprintf(fmt);
}
struct MsgOptions { msg_channel_type destination; };
using intensity = unsigned int;
void round15_regressions(const char values[], const int *p_params,
                         const msg_channel_type *p_dest, MsgOptions opts,
                         intensity level, int idx) {
    mprf(MSGCH_WARN, values[idx], "Char array element warning.");
    mprf(MSGCH_WARN, p_params[idx], "Int pointer element warning.");
    mprf(p_dest[idx], "Channel pointer element warning.");
    mpr(
#if 0
        "Inactive debug details."
#else
        T_("Visible message.")
#endif
    );
    mprf(opts.destination, "Member channel warning.");
    mprf(MSGCH_WARN, level, "Alias int warning.");
}
EOF
set +e
python3 "$SCAN_I18N" missing-t "$MULTILINE_MT_DIR" > "$MULTILINE_MT_DIR/out.txt" 2>&1
MULTILINE_MT_RC=$?
set -e
assert_status "missing-t: multiline unwrapped mprf exits non-zero" 1 "$MULTILINE_MT_RC"
assert_contains "missing-t: multiline unwrapped mprf flagged"     '[MSG] multiline.cc:3  "Your demonic ancestry asserts itself..."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: translated replacement arg does not mask format string"     '[MSG] multiline.cc:13  "Your scales start turning %s."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: first-line bare format with T_() replacement arg flagged"     '[MSG] multiline.cc:17  "Your %s glows."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: first-line inline block comment before literal flagged"     '[MSG] multiline.cc:23  "You fall!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: continuation inline block comment before literal flagged"     '[MSG] multiline.cc:25  "You stumble!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: first-line + continuation literal concatenation flagged"     '[MSG] multiline.cc:28  "%s falls!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: continuation adjacent literal concatenation flagged"     '[MSG] multiline.cc:30  "%s stumbles!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: (channel, props[key], fmt) reports fmt not subscript"     '[MSG] multiline.cc:34  "Piety warning!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: mixed diagnostic/player channel ternary flagged"     '[MSG] multiline.cc:40  "Mixed channel warning!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: deep (>8 line) multiline mprf flagged"     '[MSG] multiline.cc:43  "Deep multiline warning!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: channel variable (veto_channel) does not hide bare format"     '[MSG] multiline.cc:55  "Veto warning!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: mixed-channel ternary condition string ignored, message flagged"     '[MSG] multiline.cc:57  "Condition warning!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: nested make_stringf inside mpr still flagged"     '[MSG] multiline.cc:61  "You lose %d HP."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: multiline nested make_stringf flagged once as MSG"     '[MSG] multiline.cc:69  "Multiline nested %d HP."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: declared msg_channel_type param (fallback) flagged"     '[MSG] multiline.cc:74  "Fallback channel warning!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: shadowed channel restored after inner block"     '[MSG] multiline.cc:86  "After shadow!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: shadowed channel restored after for-loop initializer"     '[MSG] multiline.cc:98  "After loop!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: shadowed channel restored after unbraced loop with brace char"     '[MSG] multiline.cc:105  "After unbraced loop!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: declared int param selects format arg"     '[MSG] multiline.cc:110  "Declared int param warning!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: raw string fake declaration does not shadow channel"     '[MSG] multiline.cc:114  "After raw string!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: C++14 digit separator + raw string does not hide mprf"     '[MSG] multiline.cc:118  "After digit sep and raw string!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: case char literal before raw string does not hide mprf"     '[MSG] multiline.cc:122  "After case char literal!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: in-call digit separator in ternary channel flagged"     '[MSG] multiline.cc:124  "In-call digit sep!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: digit separator integer param selects format arg"     '[MSG] multiline.cc:125  "Digit sep int param!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: leading-dot float digit sep after keyword does not hide mpr"     '[MSG] multiline.cc:129  "After leading-dot digit sep!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: raw string with embedded quotes flagged"     '[MSG] multiline.cc:131  ""Raw danger!""' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: brace-initialized std::string flagged"     '[MSG] multiline.cc:133  "Brace string danger!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: bare braced-init-list mpr flagged"     '[MSG] multiline.cc:134  "Braced init danger!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: auto-deduced channel variable selects format arg"     '[MSG] multiline.cc:137  "Auto channel danger!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: char literal channel param selects format arg"     '[MSG] multiline.cc:139  "Char param danger!"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: nested make_stringf inside non-passthrough helper still flagged as STR"     '[STR] multiline.cc:145  "the %s"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: standalone unsigned parameter selects format arg"     '[MSG] multiline.cc:154  "An alarm sounds."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: unsigned long long int parameter selects format arg"     '[MSG] multiline.cc:155  "Long long alarm."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: comma multi-declarator int selects format arg"     '[MSG] multiline.cc:157  "Multi-decl alarm."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: for-loop multi-declarator int selects format arg"     '[MSG] multiline.cc:159  "For multi-decl alarm."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: same-line nested make_stringf inside non-passthrough helper flagged as STR"     '[STR] multiline.cc:160  "same-line %s"' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: unsigned const char param selects format arg"     '[MSG] multiline.cc:163  "Unsigned const char warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: char volatile param selects format arg"     '[MSG] multiline.cc:164  "Volatile char warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: declared channel array element selects format arg"     '[MSG] multiline.cc:166  "Channel array warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: declared int array element selects format arg"     '[MSG] multiline.cc:168  "Param array warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: inactive #else declaration does not shadow active channel"     '[MSG] multiline.cc:174  "Active branch channel warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: char array subscript promotes to int param"     '[MSG] multiline.cc:182  "Char array element warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: int pointer subscript selects format arg"     '[MSG] multiline.cc:183  "Int pointer element warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: channel pointer subscript selects format arg"     '[MSG] multiline.cc:184  "Channel pointer element warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: struct member channel selects format arg"     '[MSG] multiline.cc:192  "Member channel warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: using-aliased integral param selects format arg"     '[MSG] multiline.cc:193  "Alias int warning."' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: multiline MSG exact count"     'MSG: 44 candidates' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: multiline STR exact count (nested non-passthrough STR calls)"     'STR: 2 candidates' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: multiline UI exact count (block comment before cprintf ignored)"     'UI: 0 candidates' "$MULTILINE_MT_DIR/out.txt"
assert_contains "missing-t: multiline SMM exact count"     'SMM: 0 candidates' "$MULTILINE_MT_DIR/out.txt"
rm -rf "$MULTILINE_MT_DIR"

# Standalone file with conditional #ifdef inside mprf and NO inactive #if 0 blocks
COND_ARG_DIR=$(mktemp -d)
cat > "$COND_ARG_DIR/cond_arg.cc" <<'EOF'
#define SHOW_WARNING() mprf("Macro danger!")
#define SHOW_DEST_WARNING(dest) mprf(dest, "Macro channel danger!")
#define DEBUG_WRAPPER() SHOW_DEST_WARNING(MSGCH_DIAGNOSTICS)
#define SHOW_DIAG_ONLY(channel) mprf(channel, "Internal diagnostic!")
#define EMIT_FWD(channel) mprf(channel, "Forwarded player warning!")
#define FORWARD_WARN(dest) EMIT_FWD(dest)
#define PRE_FWD(dest) POST_EMIT(dest)
#define POST_EMIT(dest) mprf(dest, "Pre-declared forward warning!")
#define CHAIN_M0(d) mprf(d, "Deep chain warning!")
#define CHAIN_M1(d) CHAIN_M0(d)
#define CHAIN_M2(d) CHAIN_M1(d)
#define CHAIN_M3(d) CHAIN_M2(d)
#define CHAIN_M4(d) CHAIN_M3(d)
#define SHOW_PARAM_WARNING(dest, \
                           lvl) mprf(dest, lvl, "Macro param danger!")
#define SHOW_FMT(fmt) mprf(fmt, "arg")
void halo_fade() {
    SHOW_WARNING();
    DEBUG_WRAPPER();
    SHOW_DEST_WARNING(MSGCH_WARN);
    SHOW_DIAG_ONLY(MSGCH_DIAGNOSTICS);
    EMIT_FWD(MSGCH_DIAGNOSTICS);
    FORWARD_WARN(MSGCH_WARN);
    POST_EMIT(MSGCH_DIAGNOSTICS);
    PRE_FWD(MSGCH_WARN);
    CHAIN_M4(MSGCH_WARN);
    SHOW_PARAM_WARNING(MSGCH_WARN, 2);
    SHOW_FMT(T_("You see %s."));
    mprf(MSGCH_GOD,
#ifdef USE_TILE_WEB
         you.religion,
#endif
         "Your divine halo fades away.");
    mprf(R"(
#Danger!
)");
    mprf("Danger! " R"(
#if 0
)");
}
#undef SHOW_DIAG_ONLY
void SHOW_DIAG_ONLY(msg_channel_type c) {}
void after_undef() { SHOW_DIAG_ONLY(MSGCH_WARN); }

#define OUTER_PRE(d) INNER_PRE(d)
#define INNER_PRE(d) EMIT_PRE(d)
#define EMIT_PRE(d) mprf(d, "Nested pre-order before undef!")
void nested_pre() { OUTER_PRE(MSGCH_WARN); }
#undef EMIT_PRE

#define ZERO_ARG_WARN() ZERO_TARGET(MSGCH_WARN)
#define ZERO_TARGET(d) mprf(d, "Zero-arg wrapper warning!")
void zero_arg_fn() { ZERO_ARG_WARN(); }

#define REDEF_FWD(d) REDEF_EMIT(d)
#define REDEF_EMIT(c) mprf(c, "Old diagnostic only!")
void redef_1() { REDEF_FWD(MSGCH_DIAGNOSTICS); }
#undef REDEF_EMIT
#define REDEF_EMIT(c) mprf(c, "New player warning!")
void redef_2() { REDEF_FWD(MSGCH_WARN); }

#define ALIAS_TARGET(d) mprf(d, "Object alias warning!")
#define ALIAS_WARN ALIAS_TARGET
void alias_fn() { ALIAS_WARN(MSGCH_WARN); }

#define VARIADIC_TARGET(d) mprf(d, "Variadic macro warning!")
#define VARIADIC_WARN(...) VARIADIC_TARGET(__VA_ARGS__)
void variadic_fn() { VARIADIC_WARN(MSGCH_WARN); }

#define STR_LIT(x) #x
#define STR_DIAG_ONLY(c) mprf(c, "Stringified diagnostic only!")
void str_fn() {
    const char *s = STR_LIT(STR_DIAG_ONLY(MSGCH_WARN));
    STR_DIAG_ONLY(MSGCH_DIAGNOSTICS);
}

#define DEEP_0(d) mprf(d, "Deep 35-wrapper warning!")
#define DEEP_1(d) DEEP_0(d)
#define DEEP_2(d) DEEP_1(d)
#define DEEP_3(d) DEEP_2(d)
#define DEEP_4(d) DEEP_3(d)
#define DEEP_5(d) DEEP_4(d)
#define DEEP_6(d) DEEP_5(d)
#define DEEP_7(d) DEEP_6(d)
#define DEEP_8(d) DEEP_7(d)
#define DEEP_9(d) DEEP_8(d)
#define DEEP_10(d) DEEP_9(d)
#define DEEP_11(d) DEEP_10(d)
#define DEEP_12(d) DEEP_11(d)
#define DEEP_13(d) DEEP_12(d)
#define DEEP_14(d) DEEP_13(d)
#define DEEP_15(d) DEEP_14(d)
#define DEEP_16(d) DEEP_15(d)
#define DEEP_17(d) DEEP_16(d)
#define DEEP_18(d) DEEP_17(d)
#define DEEP_19(d) DEEP_18(d)
#define DEEP_20(d) DEEP_19(d)
#define DEEP_21(d) DEEP_20(d)
#define DEEP_22(d) DEEP_21(d)
#define DEEP_23(d) DEEP_22(d)
#define DEEP_24(d) DEEP_23(d)
#define DEEP_25(d) DEEP_24(d)
#define DEEP_26(d) DEEP_25(d)
#define DEEP_27(d) DEEP_26(d)
#define DEEP_28(d) DEEP_27(d)
#define DEEP_29(d) DEEP_28(d)
#define DEEP_30(d) DEEP_29(d)
#define DEEP_31(d) DEEP_30(d)
#define DEEP_32(d) DEEP_31(d)
#define DEEP_33(d) DEEP_32(d)
#define DEEP_34(d) DEEP_33(d)
void deep_fn() { DEEP_34(MSGCH_WARN); }
EOF
set +e
python3 "$SCAN_I18N" missing-t "$COND_ARG_DIR" > "$COND_ARG_DIR/out.txt" 2>&1
COND_ARG_RC=$?
set -e
assert_status "missing-t: #ifdef inside mprf without inactive blocks exits non-zero" 1 "$COND_ARG_RC"
assert_contains "missing-t: #define macro body mprf is preserved and flagged" \
    '[MSG] cond_arg.cc:1  "Macro danger!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define channel macro param survives wrapper macro before player call" \
    '[MSG] cond_arg.cc:2  "Macro channel danger!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define forwarded player warning not masked by diagnostic call" \
    '[MSG] cond_arg.cc:5  "Forwarded player warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define forwarder defined before target macro propagates channel" \
    '[MSG] cond_arg.cc:8  "Pre-declared forward warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define 4-wrapper forwarding chain propagates channel" \
    '[MSG] cond_arg.cc:9  "Deep chain warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define multiline param list infers channel+int from call site" \
    '[MSG] cond_arg.cc:15  "Macro param danger!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #ifdef inside mprf without inactive blocks flags message" \
    '[MSG] cond_arg.cc:29  "Your divine halo fades away."' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: multiline raw string line starting with # is not blanked as directive" \
    '[MSG] cond_arg.cc:34' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: multiline raw string #if 0 does not blank call or closing delimiter" \
    '[MSG] cond_arg.cc:37' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define nested pre-order wrapper before #undef flagged" \
    '[MSG] cond_arg.cc:47  "Nested pre-order before undef!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define zero-arg wrapper before target macro flagged" \
    '[MSG] cond_arg.cc:52  "Zero-arg wrapper warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define redefined target after #undef flags only new player warning" \
    '[MSG] cond_arg.cc:59  "New player warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define object-like alias macro rescans with trailing parens" \
    '[MSG] cond_arg.cc:62  "Object alias warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define variadic wrapper macro forwards __VA_ARGS__" \
    '[MSG] cond_arg.cc:66  "Variadic macro warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: #define 35-wrapper acyclic chain propagates channel" \
    '[MSG] cond_arg.cc:77  "Deep 35-wrapper warning!"' "$COND_ARG_DIR/out.txt"
assert_contains "missing-t: cond_arg exact MSG count (stringified arg does not pollute diag macro)" \
    'MSG: 15 candidates' "$COND_ARG_DIR/out.txt"
rm -rf "$COND_ARG_DIR"

R26_DIR=$(mktemp -d)
cat > "$R26_DIR/r26_cases.cc" <<'EOF'
#define TRACE_DIAG_ONLY(d) mprf(d, "Internal trace only!")
#define TRACE_MPR(x) mprf(MSGCH_DIAGNOSTICS, "%s", #x)
void f_trace() {
    TRACE_MPR(TRACE_DIAG_ONLY(MSGCH_WARN));
    TRACE_DIAG_ONLY(MSGCH_DIAGNOSTICS);
}

#define JOIN_TOK(a, b) a##b
#define JOIN_REPORT(d) mprf(d, "Token pasted channel warning!")
void f_join() { JOIN_REPORT(JOIN_TOK(MSGCH_, WARN)); }

#define GNU_TARGET(d, p) mprf(d, p, "GNU variadic paste warning!")
#define GNU_WRAP(d, args...) GNU_TARGET(d, ##args)
void f_gnu() { GNU_WRAP(MSGCH_WARN, 3); }

#define DIRECT_VA(...) mprf(__VA_ARGS__, "Direct variadic warning!")
void f_va() { DIRECT_VA(MSGCH_WARN); }

#define CHAIN_REPORT(d) mprf(d, "Chained alias warning!")
#define CHAIN_GET() CHAIN_REPORT
#define CHAIN_ALIAS CHAIN_GET
void f_chain() { CHAIN_ALIAS()(MSGCH_WARN); }

void f_skipped_local(bool err) {
    auto ch_skip = err ? MSGCH_ERROR : MSGCH_DIAGNOSTICS;
    mprf(ch_skip, "Unreassigned skipped local");
    msg_channel_type ch_exp = MSGCH_DIAGNOSTICS;
    mprf(ch_exp, "Explicit skipped local");
    auto ch_mut = MSGCH_DIAGNOSTICS;
    ch_mut = MSGCH_WARN;
    mprf(ch_mut, "Reassigned local warning!");
}

#define SPLICE_WARN(d) mprf(\
    d, "Splice channel warning!")
void f_splice() { SPLICE_WARN(MSGCH_WARN); }

void f_same_line(const char *name) {
    mprf("%s", name); mpr("After format-only warning!");
}
EOF
set +e
python3 "$SCAN_I18N" missing-t "$R26_DIR" > "$R26_DIR/out.txt" 2>&1
R26_RC=$?
set -e
assert_status "missing-t: r26_cases exits non-zero" 1 "$R26_RC"
assert_contains "missing-t: ## token pasting reconstructs channel"     '[MSG] r26_cases.cc:9  "Token pasted channel warning!"' "$R26_DIR/out.txt"
assert_contains "missing-t: GNU , ##args token pasting forwards int param"     '[MSG] r26_cases.cc:12  "GNU variadic paste warning!"' "$R26_DIR/out.txt"
assert_contains "missing-t: direct __VA_ARGS__ channel in mprf macro flagged"     '[MSG] r26_cases.cc:16  "Direct variadic warning!"' "$R26_DIR/out.txt"
assert_contains "missing-t: chained alias ALIAS()(MSGCH_WARN) rescans repeatedly"     '[MSG] r26_cases.cc:19  "Chained alias warning!"' "$R26_DIR/out.txt"
assert_contains "missing-t: reassigned local channel still flagged"     '[MSG] r26_cases.cc:31  "Reassigned local warning!"' "$R26_DIR/out.txt"
assert_contains "missing-t: macro line splice inside mprf preserves channel detection"     '[MSG] r26_cases.cc:34  "Splice channel warning!"' "$R26_DIR/out.txt"
assert_contains "missing-t: format-only call does not hide next mpr on same line"     '[MSG] r26_cases.cc:39  "After format-only warning!"' "$R26_DIR/out.txt"
assert_contains "missing-t: r26_cases exact count (stringified mpr arg & unreassigned skipped locals excluded)"     'MSG: 7 candidates' "$R26_DIR/out.txt"
rm -rf "$R26_DIR"

R27_DIR=$(mktemp -d)
cat > "$R27_DIR/r27_cases.cc" <<'EOF'
void f_paren_assign() {
    auto ch1 = MSGCH_DIAGNOSTICS;
    (ch1) = MSGCH_WARN;
    mprf(ch1, "Parenthesized assign warning!");

    auto ch2 = MSGCH_DIAGNOSTICS;
    auto &ref = ch2;
    ref = MSGCH_WARN;
    mprf(ch2, "Reference assign warning!");

    auto ch3 = MSGCH_DIAGNOSTICS;
    mutate_channel(ch3);
    mprf(ch3, "Mutated by call warning!");
}

msg_channel_type global_dest = MSGCH_DIAGNOSTICS;
void f_global() {
    mprf(global_dest, "Mutable global warning!");
}

template <class T> struct Event { T dest; };
void f_member(Event<msg_channel_type> ev) {
    auto dest = MSGCH_DIAGNOSTICS;
    mprf(dest, "Local dest stays skipped");
    mprf(ev.dest, "Member dest warning!");
}

#define R27_WARN() R27_LOG(MSGCH_WARN)
#define R27_DIAG() R27_LOG(MSGCH_DIAGNOSTICS)
#define R27_LOG(c) mprf(c, "Explicit empty variadic warning!")
#define R27_PICK(a, b, c, ...) c()
#define R27_ROUTE(x, ...) R27_PICK(0, ##__VA_ARGS__, R27_WARN, R27_DIAG)
void f_route_empty() { R27_ROUTE(1,); }

#define R27_OMIT_LOG(c) mprf(c, "Omitted variadic stays diagnostic")
#define R27_OMIT_WARN() R27_OMIT_LOG(MSGCH_WARN)
#define R27_OMIT_DIAG() R27_OMIT_LOG(MSGCH_DIAGNOSTICS)
#define R27_OMIT_ROUTE(x, ...) R27_PICK(0, ##__VA_ARGS__, R27_OMIT_WARN, R27_OMIT_DIAG)
void f_route_omitted() { R27_OMIT_ROUTE(1); }

#define R27_EMIT(...) mprf(__VA_ARGS__, "internal_key")
void f_emit_pack() { R27_EMIT(MSGCH_WARN, T_("Found %s!")); }

#define R27_ID(x) x
#define R27_REPORT(d) mprf(d, "Diagnostic trace via ID!")
void f_id_rescan() { R27_ID(R27_REPORT)(R27_ID(MSGCH_DIAGNOSTICS)); }
EOF
set +e
python3 "$SCAN_I18N" missing-t "$R27_DIR" > "$R27_DIR/out.txt" 2>&1
R27_RC=$?
set -e
assert_status "missing-t: r27_cases exits non-zero" 1 "$R27_RC"
assert_contains "missing-t: parenthesized local reassignment still flagged"     '[MSG] r27_cases.cc:4  "Parenthesized assign warning!"' "$R27_DIR/out.txt"
assert_contains "missing-t: reference-bound local channel still flagged"     '[MSG] r27_cases.cc:9  "Reference assign warning!"' "$R27_DIR/out.txt"
assert_contains "missing-t: call-passed local channel still flagged"     '[MSG] r27_cases.cc:13  "Mutated by call warning!"' "$R27_DIR/out.txt"
assert_contains "missing-t: mutable file-scope global channel still flagged"     '[MSG] r27_cases.cc:18  "Mutable global warning!"' "$R27_DIR/out.txt"
assert_contains "missing-t: local skipped channel does not suppress unrelated member"     '[MSG] r27_cases.cc:25  "Member dest warning!"' "$R27_DIR/out.txt"
assert_contains "missing-t: GNU , ##__VA_ARGS__ preserves explicit empty variadic arg"     '[MSG] r27_cases.cc:30  "Explicit empty variadic warning!"' "$R27_DIR/out.txt"
assert_contains "missing-t: r27_cases exact count (omitted variadic, pack-supplied format, ID-rescanned diag excluded)"     'MSG: 6 candidates' "$R27_DIR/out.txt"
rm -rf "$R27_DIR"

R28_DIR=$(mktemp -d)
cat > "$R28_DIR/r28_cases.cc" <<'EOF'
void f_call_in_cmp() {
    auto dest = MSGCH_DIAGNOSTICS;
    if (update_dest(dest) == 1)
        mprf(dest, "Call-in-cmp mutated warning!");
}

#define R28_MARK const
msg_channel_type r28_global_after_define = MSGCH_DIAGNOSTICS;
void f_after_define() {
    r28_global_after_define = MSGCH_WARN;
    mprf(r28_global_after_define, "Global after #define const warning!");
}

extern "C" {
msg_channel_type r28_extern_c_ch = MSGCH_DIAGNOSTICS;
void f_extern_c_emit() {
    mprf(r28_extern_c_ch, "Extern C global warning!");
}
}
void f_extern_c_set() { r28_extern_c_ch = MSGCH_WARN; }

#define R28_EMIT(...) mprf(__VA_ARGS__, "Int-expr variadic warning!")
void f_int_expr_va(int base, int offset) {
    R28_EMIT(MSGCH_TALK, base + offset);
}

#define R28_ID(x) x
#define R28_START R28_ID
#define R28_AGAIN() R28_ID
#define R28_LOG(d) mprf(d, "Route warning!")
void f_hideset_route() { R28_START(R28_AGAIN)()(R28_LOG)(MSGCH_WARN); }
EOF
set +e
python3 "$SCAN_I18N" missing-t "$R28_DIR" > "$R28_DIR/out.txt" 2>&1
R28_RC=$?
set -e
assert_status "missing-t: r28_cases exits non-zero" 1 "$R28_RC"
assert_contains "missing-t: call inside == comparison does not whitelist mutated local" \
    '[MSG] r28_cases.cc:4  "Call-in-cmp mutated warning!"' "$R28_DIR/out.txt"
assert_contains "missing-t: #define const on prior line does not make global const" \
    '[MSG] r28_cases.cc:11  "Global after #define const warning!"' "$R28_DIR/out.txt"
assert_contains "missing-t: extern C linkage block global is not treated as block-local" \
    '[MSG] r28_cases.cc:17  "Extern C global warning!"' "$R28_DIR/out.txt"
assert_contains "missing-t: variadic pack with (channel, int + int) still flags format" \
    '[MSG] r28_cases.cc:22  "Int-expr variadic warning!"' "$R28_DIR/out.txt"
assert_contains "missing-t: chained rescan hideset intersection allows fresh ID from AGAIN()" \
    '[MSG] r28_cases.cc:30  "Route warning!"' "$R28_DIR/out.txt"
assert_contains "missing-t: r28_cases exact count" \
    'MSG: 5 candidates' "$R28_DIR/out.txt"
rm -rf "$R28_DIR"

R29_DIR=$(mktemp -d)
cat > "$R29_DIR/r29_cases.cc" <<'EOF'
#define R29_MARK \
const
msg_channel_type r29_route = MSGCH_DIAGNOSTICS;
void f_cont_define() {
    r29_route = MSGCH_WARN;
    mprf(r29_route, "Continued define mutable warning!");
}

void f_readonly_reads() {
    auto dest = MSGCH_DIAGNOSTICS;
    if (dest == MSGCH_DIAGNOSTICS)
        mprf((dest), "Diagnostic only paren read");
}

void f_ptr_add(int offset, const char *fmt) {
    mprf(MSGCH_TALK, offset + (fmt), "Raw data argument!");
}

#define R29_EMIT(...) mprf(__VA_ARGS__, "Shift int variadic warning!")
void f_shift_va(int base, int offset) {
    R29_EMIT(MSGCH_TALK, base << offset);
}

#define R29_START(x) x
#define R29_AGAIN() R29_START(R29_START)
#define R29_LOG(d) mprf(d, "Blue-painted diag only!")
void f_blue_paint() {
    R29_START(R29_AGAIN)()(R29_LOG)(MSGCH_WARN);
    R29_LOG(MSGCH_DIAGNOSTICS);
}
EOF
set +e
python3 "$SCAN_I18N" missing-t "$R29_DIR" > "$R29_DIR/out.txt" 2>&1
R29_RC=$?
set -e
assert_status "missing-t: r29_cases exits non-zero" 1 "$R29_RC"
assert_contains "missing-t: backslash-continued #define const does not make global const" \
    '[MSG] r29_cases.cc:6  "Continued define mutable warning!"' "$R29_DIR/out.txt"
assert_contains "missing-t: shift expression (base << offset) in variadic pack flags format" \
    '[MSG] r29_cases.cc:19  "Shift int variadic warning!"' "$R29_DIR/out.txt"
assert_contains "missing-t: r29_cases exact count (if==, mprf((dest)), offset+(fmt), and blue-painted START excluded)" \
    'MSG: 2 candidates' "$R29_DIR/out.txt"
rm -rf "$R29_DIR"

R30_DIR=$(mktemp -d)
cat > "$R30_DIR/r30_cases.cc" <<'EOF'
void f_inc_dec(int offset, const char *fmt) {
    mprf(MSGCH_TALK, ++offset, "Prefix inc warning!");
    mprf(MSGCH_TALK, offset++, "Postfix inc warning!");
    mprf(MSGCH_TALK, --offset, "Prefix dec warning!");
    mprf(MSGCH_TALK, offset--, "Postfix dec warning!");
    mprf(MSGCH_TALK, ++fmt, "Pointer inc raw data!");
}

#define R30_PASTE(x, y) x ## y
#define R30_START(x) x
#define R30_AGAIN() R30_PASTE(R30_START(R30_START), )
#define R30_LOG(d) mprf(d, "Placemarker paste diag only!")
void f_paste_blue() {
    R30_START(R30_AGAIN)()(R30_LOG)(MSGCH_WARN);
    R30_LOG(MSGCH_DIAGNOSTICS);
}
EOF
set +e
python3 "$SCAN_I18N" missing-t "$R30_DIR" > "$R30_DIR/out.txt" 2>&1
R30_RC=$?
set -e
assert_status "missing-t: r30_cases exits non-zero" 1 "$R30_RC"
assert_contains "missing-t: ++offset int param selects format" \
    '[MSG] r30_cases.cc:2  "Prefix inc warning!"' "$R30_DIR/out.txt"
assert_contains "missing-t: offset++ int param selects format" \
    '[MSG] r30_cases.cc:3  "Postfix inc warning!"' "$R30_DIR/out.txt"
assert_contains "missing-t: --offset int param selects format" \
    '[MSG] r30_cases.cc:4  "Prefix dec warning!"' "$R30_DIR/out.txt"
assert_contains "missing-t: offset-- int param selects format" \
    '[MSG] r30_cases.cc:5  "Postfix dec warning!"' "$R30_DIR/out.txt"
assert_contains "missing-t: r30_cases exact count (++fmt and empty-paste blue-paint excluded)" \
    'MSG: 4 candidates' "$R30_DIR/out.txt"
rm -rf "$R30_DIR"

R31_DIR=$(mktemp -d)
cat > "$R31_DIR/r31_cases.cc" <<'EOF'
using R31_SELF = int;
#define R31_SELF R31_SELF
#define R31_MAKE(prefix, x, y) prefix x ## y
#define R31_OUT() R31_MAKE(R31_SELF, , X)
#define R31_SELFX(d) mprf(d, "Diagnostic only via empty left paste!")
void f_empty_left_paste() {
    R31_OUT()(MSGCH_WARN);
    R31_SELFX(MSGCH_DIAGNOSTICS);
}

#define R31_CHAIN(a, b, c) a ## b ## c
#define R31_CHAIN_LOG(d) mprf(d, "Chained empty middle paste warning!")
void f_chained_empty_paste() {
    R31_CHAIN(R31_CHAIN_, , LOG)(MSGCH_WARN);
    R31_CHAIN_LOG(MSGCH_DIAGNOSTICS);
}

#define R31_MAKE2(prefix, x, y, z) prefix x ## y ## z
#define R31_OUT2() R31_MAKE2(R31_SELF, , , Y)
#define R31_SELFY(d) mprf(d, "Diagnostic only via double empty left paste!")
void f_double_empty_left_paste() {
    R31_OUT2()(MSGCH_WARN);
    R31_SELFY(MSGCH_DIAGNOSTICS);
}

#define R31_PASTE2(x, y) x ## y
#define R31_ID(x) x
#define R31_WRAP(a) R31_PASTE2(, a)
#define R31_AGAIN3() R31_WRAP(R31_ID(R31_ID))
#define R31_LOG2(d) mprf(d, "Empty left paste preserves right blue-paint!")
void f_empty_left_preserves_right_blue() {
    R31_AGAIN3()(R31_LOG2)(MSGCH_WARN);
    R31_LOG2(MSGCH_DIAGNOSTICS);
}
EOF
set +e
python3 "$SCAN_I18N" missing-t "$R31_DIR" > "$R31_DIR/out.txt" 2>&1
R31_RC=$?
set -e
assert_status "missing-t: r31_cases exits non-zero" 1 "$R31_RC"
assert_contains "missing-t: chained a ## empty ## c still pastes and records non-skipped channel" \
    '[MSG] r31_cases.cc:12  "Chained empty middle paste warning!"' "$R31_DIR/out.txt"
assert_contains "missing-t: r31_cases exact count (empty left placemarker paste does not fuse preceding token or clear right blue-paint)" \
    'MSG: 1 candidates' "$R31_DIR/out.txt"
rm -rf "$R31_DIR"

R31_SOH_DIR=$(mktemp -d)
python3 - "$R31_SOH_DIR/r31_soh.cc" <<'PYEOF'
import sys
from pathlib import Path
Path(sys.argv[1]).write_bytes(
    b'#define R31_SOH_ID(x) x\n'
    b'#define R31_SOH_LOG(k) mprf(MSGCH_WARN, k, "SOH char literal warning!")\n'
    b"void f_soh() { R31_SOH_LOG(R31_SOH_ID('\x01')); }\n"
)
PYEOF
set +e
python3 "$SCAN_I18N" missing-t "$R31_SOH_DIR" > "$R31_SOH_DIR/out.txt" 2>&1
R31_SOH_RC=$?
set -e
assert_status "missing-t: r31_soh exits non-zero" 1 "$R31_SOH_RC"
assert_contains "missing-t: literal 0x01 byte in char constant survives macro substitution" \
    '[MSG] r31_soh.cc:2  "SOH char literal warning!"' "$R31_SOH_DIR/out.txt"
rm -rf "$R31_SOH_DIR"

# ── display contracts ──
set +e
PYTHONNOUSERSITE=1 python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-contracts/source.txt" \
    --allowlist "$FIXTURES/display-contracts/fail_closed_allowlist.json" \
    > /tmp/actual_display_contracts.txt 2>&1
DISPLAY_CONTRACT_RC=$?
set -e
assert_output "missing-t: direct sinks and dynamic-key wrappers" \
    /tmp/actual_display_contracts.txt "$EXPECTED/display-contracts.txt"
assert_status "missing-t: display-contract violations block without tree-sitter" \
    1 "$DISPLAY_CONTRACT_RC"

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts/" \
    --display-contracts-only > /tmp/actual_display_no_source.txt 2>&1
DISPLAY_NO_SOURCE_RC=$?
set -e
assert_status "missing-t: contract mode requires source.txt" \
    2 "$DISPLAY_NO_SOURCE_RC"
assert_contains "missing-t: missing source.txt has a clear CLI error" \
    "--source-txt is required with --display-contracts-only" \
    /tmp/actual_display_no_source.txt

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts-debug/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-contracts/source.txt" \
    > /tmp/actual_display_debug_default.txt 2>&1
DISPLAY_DEBUG_DEFAULT_RC=$?
set -e
assert_output "missing-t: default excludes dead branches but scans live alternatives" \
    /tmp/actual_display_debug_default.txt \
    "$EXPECTED/display-contracts-debug-default.txt"
assert_status "missing-t: live else/elif and unknown branches block by default" \
    1 "$DISPLAY_DEBUG_DEFAULT_RC"

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-contracts-debug/" \
    --display-contracts-only --strict \
    --source-txt "$FIXTURES/display-contracts/source.txt" \
    > /tmp/actual_display_debug_strict.txt 2>&1
DISPLAY_DEBUG_STRICT_RC=$?
set -e
assert_output "missing-t: --strict includes every preprocessor branch" \
    /tmp/actual_display_debug_strict.txt \
    "$EXPECTED/display-contracts-strict-debug.txt"
assert_status "missing-t: --strict dead-branch violations block" \
    1 "$DISPLAY_DEBUG_STRICT_RC"

# ── blocking display producers/builders and compatibility flag ──
set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-audit/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_display_audit.txt 2>&1
DISPLAY_AUDIT_RC=$?
set -e
assert_output "missing-t: sinks, producers, and builders block by default" \
    /tmp/actual_display_audit.txt "$EXPECTED/display-audit.txt"
assert_status "missing-t: every registered display contract blocks" \
    1 "$DISPLAY_AUDIT_RC"
assert_contains "orb names: final display producer still rejects raw literal mutation" \
    "DISPLAY003 orb_beam_name_display return: orb of destruction" /tmp/actual_display_audit.txt

# ── ranged weapon noise display builder ──
RANGED_NOISE_FIXTURES="$FIXTURES/display-ranged-noise"
python3 "$SCAN_I18N" missing-t "$RANGED_NOISE_FIXTURES/pass/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_ranged_noise_pass.txt 2>&1
assert_contains "ranged noise: translated msg assignments pass" \
    "DISPLAY: 0 candidates" /tmp/actual_ranged_noise_pass.txt

set +e
python3 "$SCAN_I18N" missing-t "$RANGED_NOISE_FIXTURES/fail/" \
    --display-contracts-only \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_ranged_noise_fail.txt 2>&1
RANGED_NOISE_FAIL_RC=$?
set -e
assert_status "ranged noise: raw msg assignment blocks" \
    1 "$RANGED_NOISE_FAIL_RC"
assert_contains "ranged noise: finding identifies the raw bow message" \
    "DISPLAY004 _throw_noise msg: You hear a bow twang." \
    /tmp/actual_ranged_noise_fail.txt

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-audit/" \
    --extended-display-audit \
    > /tmp/actual_display_audit_bad_cli.txt 2>&1
DISPLAY_AUDIT_BAD_CLI_RC=$?
set -e
assert_status "missing-t: extended audit requires contract mode" \
    2 "$DISPLAY_AUDIT_BAD_CLI_RC"
assert_contains "missing-t: extended audit CLI error is clear" \
    "--extended-display-audit requires --display-contracts-only" \
    /tmp/actual_display_audit_bad_cli.txt

set +e
python3 "$SCAN_I18N" missing-t "$FIXTURES/display-audit/" \
    --display-contracts-only --extended-display-audit --strict \
    --source-txt "$FIXTURES/display-audit/source.txt" \
    > /tmp/actual_display_audit_strict.txt 2>&1
DISPLAY_AUDIT_STRICT_RC=$?
set -e
assert_contains "missing-t: strict contracts include WIZARD branches" \
    "Wizard-only confirmation?" /tmp/actual_display_audit_strict.txt
assert_status "missing-t: strict WIZARD display violation blocks" \
    1 "$DISPLAY_AUDIT_STRICT_RC"

# ── registered producer/builder definition cardinality ──
PRESENCE_FIXTURES="$FIXTURES/display-contract-presence"
python3 "$SCAN_I18N" missing-t "$PRESENCE_FIXTURES/pass/" \
    --display-contracts-only \
    --source-txt "$PRESENCE_FIXTURES/pass/source.txt" \
    > /tmp/actual_contract_presence_pass.txt 2>&1
assert_contains "display registry: one producer/builder definition passes" \
    "DISPLAY: 0 candidates" /tmp/actual_contract_presence_pass.txt
assert_contains "orb names: canonical identity builders and translated final producer pass" \
    "DISPLAY: 0 candidates" /tmp/actual_contract_presence_pass.txt

for contract_case in missing-producer missing-builder \
                     duplicate-producer duplicate-builder; do
    set +e
    python3 "$SCAN_I18N" missing-t "$PRESENCE_FIXTURES/$contract_case/" \
        --display-contracts-only \
        --source-txt "$PRESENCE_FIXTURES/pass/source.txt" \
        > "/tmp/actual_contract_${contract_case}.txt" 2>&1
    contract_status=$?
    set -e
    assert_status "display registry: $contract_case blocks" 1 "$contract_status"
done
assert_contains "display registry: missing producer fails closed" \
    "DISPLAY005 producer contract cannot_evoke_item_reason: expected exactly one definition, found 0" \
    /tmp/actual_contract_missing-producer.txt
assert_contains "display registry: duplicate producer fails closed" \
    "DISPLAY005 producer contract cannot_evoke_item_reason: expected exactly one definition, found 2" \
    /tmp/actual_contract_duplicate-producer.txt
assert_contains "display registry: missing builder fails closed" \
    "DISPLAY006 builder contract update_tip_text: expected exactly one definition, found 0" \
    /tmp/actual_contract_missing-builder.txt
assert_contains "display registry: duplicate builder fails closed" \
    "DISPLAY006 builder contract update_tip_text: expected exactly one definition, found 2" \
    /tmp/actual_contract_duplicate-builder.txt

# ── Lua protocol identity producers (function-qualified, fail-closed) ──
echo "--- lua-identity ---"
python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/pass" --strict > /tmp/actual_lua_identity_pass.txt 2>&1
assert_status "lua identity: canonical/raw accessors pass" 0 $?
set +e
python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/fail" --strict > /tmp/actual_lua_identity_fail.txt 2>&1
lua_identity_fail_status=$?
set -e
assert_status "lua identity: localized accessor mutation blocks" 1 "$lua_identity_fail_status"
assert_contains "lua identity: failure identifies binding contract" "you_species" /tmp/actual_lua_identity_fail.txt
for binding_case in you-species you-race you-class genus monster; do
    set +e
    python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/fail-$binding_case" --strict > "/tmp/actual_lua_identity_$binding_case.txt" 2>&1
    binding_status=$?
    set -e
    assert_status "lua identity: independent $binding_case mutation blocks" 1 "$binding_status"
done
assert_contains "lua identity: species mutation is binding-specific" "you_species" /tmp/actual_lua_identity_you-species.txt
assert_contains "lua identity: race mutation is binding-specific" "you_race" /tmp/actual_lua_identity_you-race.txt
assert_contains "lua identity: class mutation is binding-specific" "you_class" /tmp/actual_lua_identity_you-class.txt
assert_contains "lua identity: genus dataflow mutation is binding-specific" "l_you_genus" /tmp/actual_lua_identity_genus.txt
assert_contains "lua identity: monster dataflow mutation is binding-specific" "l_you_monster" /tmp/actual_lua_identity_monster.txt
for mutation_case in mixed-ternary overwrite-localized pluralise-localized lowercase-after-push; do
    set +e
    python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/$mutation_case" --strict > "/tmp/actual_lua_identity_$mutation_case.txt" 2>&1
    mutation_status=$?
    set -e
    assert_status "lua identity: $mutation_case fails closed" 1 "$mutation_status"
done
assert_contains "lua identity: mixed ternary identifies species" "you_species" /tmp/actual_lua_identity_mixed-ternary.txt
assert_contains "lua identity: overwrite identifies genus" "l_you_genus" /tmp/actual_lua_identity_overwrite-localized.txt
assert_contains "lua identity: localized pluralise RHS is rejected" "exact genus = pluralise(genus)" /tmp/actual_lua_identity_pluralise-localized.txt
assert_contains "lua identity: lowercase after push is rejected" "lowercase processing before lua_pushstring" /tmp/actual_lua_identity_lowercase-after-push.txt
for artifact_case in missing-artifact duplicate-definition decoy-dataflow two-artifacts; do
    set +e
    python3 "$SCAN_I18N" anti-patterns "$FIXTURES/lua-identity/$artifact_case" --strict > "/tmp/actual_lua_identity_$artifact_case.txt" 2>&1
    artifact_status=$?
    set -e
    assert_status "lua identity: $artifact_case fails closed" 1 "$artifact_status"
done
assert_contains "lua identity: missing artifact is explicit" "exactly one production l-you.cc artifact" /tmp/actual_lua_identity_missing-artifact.txt
assert_contains "lua identity: duplicate definition is explicit" "exactly one LUARET1 definition" /tmp/actual_lua_identity_duplicate-definition.txt
assert_contains "lua identity: decoy dataflow is rejected" "canonical accessor must initialize" /tmp/actual_lua_identity_decoy-dataflow.txt
assert_contains "lua identity: duplicate artifacts are explicit" "exactly one production l-you.cc artifact" /tmp/actual_lua_identity_two-artifacts.txt

# ── anti-patterns git-visible gating (ignored copies match CI semantics) ──
# The anti-patterns walk must scan only files git would version.  A fresh CI
# checkout cannot contain ignored build/generated copies (e.g. the Android
# zh-guide assets copied under crawl-ref/source/android-project), so findings
# raised solely by such copies are local-only noise.  Tracked files and newly
# created untracked (non-ignored) files must still be scanned.
echo "--- anti-patterns git-visible gating ---"
AP_GIT_ROOT=$(mktemp -d)
trap 'rm -rf "$AP_GIT_ROOT"' EXIT
(
    cd "$AP_GIT_ROOT"
    git init -q .
    cp "$FIXTURES/lua-identity/pass/l-you.cc" l-you.cc
    printf '中文里混入 the 冠词是错误的。\n' > tracked.txt
    printf 'ignored.txt\n' > .gitignore
    printf '中文里混入 the 冠词是错误的。\n' > ignored.txt
    printf '无错误文本。\n' > clean.txt
    git add l-you.cc tracked.txt clean.txt .gitignore
)
set +e
python3 "$SCAN_I18N" anti-patterns "$AP_GIT_ROOT" --strict > /tmp/actual_ap_git.txt 2>&1
ap_git_status=$?
set -e
assert_status "anti-patterns: ignored copies are skipped in a git worktree" 1 "$ap_git_status"
assert_contains "anti-patterns: tracked article file still flagged" \
    "tracked.txt:1" /tmp/actual_ap_git.txt
if grep -Fq "ignored.txt" /tmp/actual_ap_git.txt; then
    echo "  FAIL: anti-patterns scanned ignored copy (ignored.txt)"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: anti-patterns skips ignored copy (ignored.txt)"
    PASS=$((PASS + 1))
fi
if grep -Fq "clean.txt" /tmp/actual_ap_git.txt; then
    echo "  FAIL: anti-patterns flagged clean tracked file (clean.txt)"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: anti-patterns leaves clean tracked file alone"
    PASS=$((PASS + 1))
fi

# Newly created untracked files (not ignored) must still be scanned: a
# coder's fresh file has not been committed yet and must not escape the gate.
printf '新增文件也混入 the 冠词。\n' > "$AP_GIT_ROOT/new_sample.txt"
set +e
python3 "$SCAN_I18N" anti-patterns "$AP_GIT_ROOT" --strict > /tmp/actual_ap_git_new.txt 2>&1
ap_git_new_status=$?
set -e
assert_status "anti-patterns: new untracked file still scanned in git worktree" 1 "$ap_git_new_status"
assert_contains "anti-patterns: new untracked file is flagged" \
    "new_sample.txt:1" /tmp/actual_ap_git_new.txt
assert_contains "anti-patterns: ignored copy still skipped with new file" \
    "tracked.txt:1" /tmp/actual_ap_git_new.txt
if grep -Fq "ignored.txt" /tmp/actual_ap_git_new.txt; then
    echo "  FAIL: anti-patterns scanned ignored copy after new-file check (ignored.txt)"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: anti-patterns keeps skipping ignored copy with new file"
    PASS=$((PASS + 1))
fi
rm -rf "$AP_GIT_ROOT"
trap - EXIT

# ── Issue 68 registered protocol/display producers ──
echo "--- protocol-boundaries ---"
set +e
python3 - "$SCAN_I18N" "$REPO_ROOT/crawl-ref/source" \
    > /tmp/actual_protocol_boundaries.txt 2>&1 <<'PY'
import importlib.util
import os
import re
import shutil
import sys
import tempfile

scan_path, source_root = sys.argv[1:]
spec = importlib.util.spec_from_file_location("scan_i18n", scan_path)
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)


def copy_contract(root, contract_id):
    for artifact in scan.PROTOCOL_BOUNDARY_CONTRACTS[contract_id]:
        src = os.path.join(source_root, artifact["file"])
        dst = os.path.join(root, artifact["file"])
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
        # CR-021 compatibility: the monspeak visual-channel checker
        # observes both TextDB sides through the production parse layer,
        # so its custom artifact must also carry the EN reference file
        # for the passing fixture and the ZH mutations below.
        if artifact.get('custom') == 'monspeak-visual-channels':
            en_src = os.path.join(source_root, 'dat/database/monspeak.txt')
            en_dst = os.path.join(root, 'dat/database/monspeak.txt')
            shutil.copyfile(en_src, en_dst)
            # A protocol fixture needs matching structure independently of
            # pending trunk translations. Mirror the complete EN snapshot
            # into its ZH fixture; production ZH remains checked by the CLI.
            shutil.copyfile(en_src, dst)


# CR-021: the monspeak custom artifact has no start/end/required producer
# schema, so its negative fixtures are the checker's own minimal
# mutations -- a line shift inside a ZH pattern and a newline-position
# change.  Both break the EN/ZH line correspondence that
# _monspeak_visual_channel_findings validates (the per-line channel
# routing and the runtime line count) while leaving the frozen EN
# identity set untouched.
MONSPEAK_VISUAL_MUTATIONS = (
    # Trunk Goji: an unknown identity accessor must block the real scanner.
    ("lua-identity-accessor",
     "you.species():lower()", "you.name()",
     "Lua return topology not bindable"),
    ("line-shift",
     '@The_monster@ intones a prayer.\nVISUAL:A sense of peace washes over you.',
     'VISUAL:A sense of peace washes over you.\n@The_monster@ intones a prayer.',
     "VISUAL channel prefix lost at an EN-aligned line"),
    ("newline-merge",
     'VISUAL:@The_monster@ gestures.\n'
     'VISUAL:You feel [cursed|doomed].',
     'VISUAL:@The_monster@ gestures.'
     'VISUAL:You feel [cursed|doomed].',
     "runtime line count differs from EN"),
    # CR-023: Lua blocks are evaluated by getSpeakString before the sink,
    # so a literal ``return "VISUAL:..."`` emission is a runtime line of
    # its own.  The branch-expanded checker binds that topology: changing
    # one return's VISUAL prefix (``friendly shoals hound`` #2, the
    # reviewer probe) must fail the per-branch channel correspondence, and
    # deleting a return branch must fail the branch count.
    ("lua-return-visual-prefix",
     'return "VISUAL:A distinct wet dog smell emanates from @the_monster@."',
     'return "SOUND:A distinct wet dog smell emanates from @the_monster@."',
     "VISUAL channel prefix lost at an EN-aligned line"),
    ("lua-return-delete",
     '    return "VISUAL:A distinct wet dog smell emanates from @the_monster@."\n'
     'else\n'
     '    return "VISUAL:@The_monster@ motions as if to dry @reflexive@ off on '
     'you."\n'
     'end',
     '    return "VISUAL:A distinct wet dog smell emanates from @the_monster@."\n'
     'end',
     "Lua return branch count differs from EN"),
    # CR-027: a token whose closure introduces Lua (``@friendly hound@``,
    # 9 variants, 1 with Lua) changes the runtime channels when a plain
    # prefix is added in front of the token: every expanded line drops
    # from TALK_VISUAL to TALK while the unexpanded literals and the
    # per-site return texts stay identical.
    ("closure-lua-prefix",
     'w:50\n@friendly hound@',
     'w:50\n前缀@friendly hound@',
     "VISUAL channel prefix lost at an EN-aligned line"),
    # CR-028: fragment bytes spliced into a Lua return literal take part
    # in the Lua escape interpretation; a raw newline injected by a
    # fragment (the _Sprozz_common_ variant reachable through Sprozz's
    # Lua return) makes the expanded Lua source fail the vendored 5.4.8
    # syntax gate.
    ("fragment-raw-newline",
     '@The_monster@ says, "Allow me to demonstrate the bee of the future!"',
     '@The_monster@ says, "Allow me to demonstrate the bee of the future!\nActually, never mind"',
     "Lua return topology not bindable"),
    # CR-030/CR-032: the same splice path with an unescaped single quote
    # terminates the Lua string literal early, so the expanded source
    # fails the vendored 5.4.8 syntax gate exactly like the raw newline.
    ("fragment-unescaped-quote",
     '@The_monster@ says, "Allow me to demonstrate the bee of the future!"',
     '@The_monster@ says, "Allow me to demonstrate the bee of the future!\'"',
     "Lua return topology not bindable"),
    # CR-030/CR-032: the Lua hex escape \x56 becomes 'V' after the
    # splice, so the branch emits a VISUAL: line (talk_visual) where
    # every expanded EN line of the same branch stays talk.
    ("fragment-hex-visual",
     '@The_monster@ says, "Allow me to demonstrate the bee of the future!"',
     '\\x56ISUAL:@The_monster@ says, "Allow me to demonstrate the bee of the future!"',
     "line channel differs from EN"),
    # CR-030/CR-032: every @marker@ site increments the one shared
    # replacement counter (MAX_REPLACEMENTS 100), including the
    # block-external @player_only@ markers and the rescans production
    # performs over their literal bytes.  With 96 external markers the
    # in-Lua @_Sprozz_common_@ is still inside the budget: both returns
    # expand on both sides (branch parity 88) and the mutated ZH body
    # renders 97 runtime lines.  With 97 external markers the common
    # marker is site 101 and stays literal, so the ZH expansion loses
    # the common variants (8 branches vs EN's 88).  A gate that
    # re-expands the site source with a fresh counter would restore
    # branch parity for the 97-marker case and produce the line-count
    # finding instead, so the pinned finding type proves the shared
    # counter.
    ("replacement-boundary-100",
     'Sprozz\n{{\n  if spells.memorised("launch clockwork bee") '
     'then\n    return \'@_Sprozz_thief_@\'\n  else\n    '
     'return \'@_Sprozz_common_@\'\n  end\n}} @player_only@\n',
     'Sprozz\n' + '@player_only@\n' * 96
     + '{{\n  if spells.memorised("launch clockwork bee") '
     'then\n    return \'@_Sprozz_thief_@\'\n  else\n    '
     'return \'@_Sprozz_common_@\'\n  end\n}} @player_only@\n',
     "runtime line count differs from EN: EN has 1 line(s), "
     "ZH has 97 (Lua branch 0)"),
    ("replacement-boundary-101",
     'Sprozz\n{{\n  if spells.memorised("launch clockwork bee") '
     'then\n    return \'@_Sprozz_thief_@\'\n  else\n    '
     'return \'@_Sprozz_common_@\'\n  end\n}} @player_only@\n',
     'Sprozz\n' + '@player_only@\n' * 97
     + '{{\n  if spells.memorised("launch clockwork bee") '
     'then\n    return \'@_Sprozz_thief_@\'\n  else\n    '
     'return \'@_Sprozz_common_@\'\n  end\n}} @player_only@\n',
     "Lua return branch count differs from EN: EN has 88 branch(es), "
     "ZH has 8"),
)


def mutate_monspeak_visual(root, kind):
    path = os.path.join(root, 'dat/database/zh/monspeak.txt')
    with open(path, 'r', encoding='utf-8') as f:
        source = f.read()
    for name, old, new, detail in MONSPEAK_VISUAL_MUTATIONS:
        if name != kind:
            continue
        mutated = source.replace(old, new, 1)
        if mutated == source:
            raise AssertionError(
                f"monspeak {kind} mutation target missing from ZH "
                f"fixture")
        with open(path, 'w', encoding='utf-8') as f:
            f.write(mutated)
        return detail
    raise AssertionError(kind)


def mutate(root, contract_id, artifact_index, required_index, kind):
    artifact = scan.PROTOCOL_BOUNDARY_CONTRACTS[contract_id][artifact_index]
    path = os.path.join(root, artifact["file"])
    with open(path, "r", encoding="utf-8") as f:
        source = f.read()
    start = list(re.finditer(artifact["start"], source, re.MULTILINE))[0]
    end = re.search(artifact["end"], source[start.end():], re.MULTILINE)
    scope_end = start.end() + end.start()
    pattern = artifact["required"][required_index][0]
    match = re.search(pattern, source[start.end():scope_end], re.MULTILINE)
    if not match:
        raise AssertionError(f"fixture producer missing for {contract_id}")
    left = start.end() + match.start()
    right = start.end() + match.end()
    token = source[left:right]
    if kind == "localized":
        replacement = artifact["localized"]
    elif kind == "missing":
        replacement = ""
    elif kind == "duplicate":
        replacement = token + "\n" + token
    elif kind == "decoy":
        replacement = ""
        source += "\n" + token + "\n"
    else:
        raise AssertionError(kind)
    source = source[:left] + replacement + source[right:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(source)


failures = []
artifact_count = 0
fixture_count = 0
for contract_id in scan.PROTOCOL_BOUNDARY_CONTRACTS:
    artifacts = scan.PROTOCOL_BOUNDARY_CONTRACTS[contract_id]
    artifact_count += len(artifacts)
    with tempfile.TemporaryDirectory() as root:
        copy_contract(root, contract_id)
        fixture_count += 1
        if scan.protocol_boundary_findings(root, contract_id):
            failures.append(f"{contract_id}: passing fixture rejected")
    for artifact_index, artifact in enumerate(artifacts):
        artifact_label = f'{artifact["file"]}#{artifact_index + 1}'
        if artifact.get('custom'):
            # CR-021: custom checkers have no required-producer schema,
            # so the generic localized/missing/duplicate/decoy matrix
            # cannot index them.  Dispatch to checker-specific fixtures:
            # the passing contract already ran above, and each minimal
            # line-shift / newline mutation must independently fail
            # closed through the monspeak checker.
            if artifact['custom'] != 'monspeak-visual-channels':
                failures.append(
                    f"{contract_id}/{artifact_label}: unknown custom "
                    f"checker {artifact['custom']!r} has no fixture "
                    f"dispatch")
                continue
            for kind in ("lua-identity-accessor", "line-shift", "newline-merge",
                         "lua-return-visual-prefix", "lua-return-delete",
                         "closure-lua-prefix", "fragment-raw-newline",
                         "fragment-unescaped-quote", "fragment-hex-visual",
                         "replacement-boundary-100",
                         "replacement-boundary-101"):
                with tempfile.TemporaryDirectory() as root:
                    copy_contract(root, contract_id)
                    detail = mutate_monspeak_visual(root, kind)
                    fixture_count += 1
                    findings = scan.protocol_boundary_findings(
                        root, contract_id)
                    if not any(detail in finding[2]
                               for finding in findings):
                        failures.append(
                            f"{contract_id}/{artifact_label}/{kind}: "
                            f"fixture accepted (expected {detail!r})")
            continue
        # Each required invariant must independently fail closed.  The
        # localized producer replacement remains artifact-level metadata;
        # missing/duplicate/decoy mutations exercise every required pattern.
        mutations = [(0, "localized")]
        mutations.extend(
            (required_index, kind)
            for required_index in range(len(artifact["required"]))
            for kind in ("missing", "duplicate", "decoy")
        )
        for required_index, kind in mutations:
            with tempfile.TemporaryDirectory() as root:
                copy_contract(root, contract_id)
                mutate(root, contract_id, artifact_index, required_index, kind)
                fixture_count += 1
                if not scan.protocol_boundary_findings(root, contract_id):
                    failures.append(
                        f"{contract_id}/{artifact_label}/required#"
                        f"{required_index + 1}: {kind} fixture accepted"
                    )

if failures:
    print("\n".join(failures))
    raise SystemExit(1)
print(f"OK: {len(scan.PROTOCOL_BOUNDARY_CONTRACTS)} rows, "
      f"{artifact_count} artifacts, {fixture_count} fixtures passed")
PY
protocol_boundary_status=$?
set -e
cat /tmp/actual_protocol_boundaries.txt
assert_status "protocol registry: passing + mutation matrix with custom monspeak dispatch" \
    0 "$protocol_boundary_status"
assert_contains "protocol registry: every artifact receives negative mutations" \
    "OK: 21 rows, 65 artifacts, 363 fixtures passed" \
    /tmp/actual_protocol_boundaries.txt

# CR-034: a malformed weighted TextDB entry must fail closed at the custom
# monspeak parser boundary instead of publishing a partial position map.
echo "--- malformed monspeak weighted entry ---"
set +e
python3 - "$SCAN_I18N" <<'PY' > /tmp/actual_monspeak_parse_error.txt 2>&1
import importlib.util
import os
import sys
import tempfile

scan_path = sys.argv[1]
spec = importlib.util.spec_from_file_location("scan_i18n", scan_path)
scan = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scan)

with tempfile.TemporaryDirectory() as root:
    path = os.path.join(root, "dat/database/monspeak.txt")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("%%%%\nmalformed fixture\n%%%%")
    positions, error = scan._monspeak_textdb_positions(
        root, "dat/database/monspeak.txt", "fixture")
    if positions is not None or not error or "weighted-entry parse error" not in error:
        raise AssertionError(
            f"malformed weighted entry was accepted: positions={positions!r} "
            f"error={error!r}")
    print(error)
PY
monspeak_parse_status=$?
set -e
assert_status "monspeak parser: malformed weighted entry fails closed" \
    0 "$monspeak_parse_status"
assert_contains "monspeak parser: error identifies weighted parse" \
    "weighted-entry parse error" /tmp/actual_monspeak_parse_error.txt

# ── direct T_ branches remain extractable ──
python3 "$SCRIPT_DIR/../i18n_extract.py" extract \
    "$REPO_ROOT/crawl-ref/source" > /tmp/actual_i18n_extract.txt
assert_contains "i18n extract: singular XP evoker recharge key" \
    "%%s has regained %d charge." /tmp/actual_i18n_extract.txt
assert_contains "i18n extract: plural XP evoker recharge key" \
    "%%s has regained %d charges." /tmp/actual_i18n_extract.txt

# ── mprf-p ──
echo "--- mprf-p ---"
python3 "$SCAN_I18N" mprf-p "$FIXTURES/mprf-p/" --source-txt "$FIXTURES/mprf-p/source.txt" > /tmp/actual_mprfp.txt 2>&1 || true
assert_output "mprf-p: bounded local returns pass and unsafe consumers still block" \
    /tmp/actual_mprfp.txt "$EXPECTED/mprf-p_violations.txt"

# ── arg-mismatch ──
echo "--- arg-mismatch ---"
python3 "$SCAN_I18N" arg-mismatch --source-txt "$FIXTURES/arg-mismatch/source.txt" > /tmp/actual_arg.txt 2>&1 || true
assert_output "arg-mismatch: finds %s count mismatch" \
    /tmp/actual_arg.txt "$EXPECTED/arg-mismatch.txt"

# ── active rejected-term decisions ──
echo "--- validate-terms decisions parser ---"
TERMS_ROOT=$(mktemp -d)
DECISIONS="$TERMS_ROOT/decisions.md"
printf '%s\n' \
    '### D-Z-901 — multiline parser fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `Pandemonium → 万魔殿`' \
    '  - `Pandemonium lord → 万魔殿领主`' \
    '- **Rejected**: 魔窟、魔窟领主' \
    '### D-Z-902 — paired rejected-term fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**: 排斥飞弹' \
    '- **Rejected**: 弹飞弹、弹开飞弹' \
    '### D-Z-903 — multiline proper-name fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `Erebora → 埃雷博拉`' \
    '  - `Ereborans → 埃雷博拉人`' \
    '- **Rejected**: 埃瑞博拉、埃瑞博拉人' \
    '### D-Z-904 — shared replacement fixture' \
    '- **Type**: Z — arbitrary fixture type' \
    '- **Status**: active' \
    '- **Choice**: 宗古德洛克' \
    '- **Rejected**: 宗古多克、宗古尔德罗克' \
    '### D-Z-906 — per-token explanatory exemption fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词、说明词（context-specific exemption）' \
    '### D-Q-905 — contextual fixture' \
    '- **Type**: Q — arbitrary contextual fixture type' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `DUR_SANGUINE_ARMOUR` / `status\|Blood` defensive status | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`（fixture）' \
    > "$DECISIONS"
python3 - "$SCAN_I18N" "$DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rejected = module.parse_decisions(sys.argv[2])
expected = {
    "魔窟", "弹飞弹", "弹开飞弹", "埃瑞博拉",
    "宗古多克", "宗古尔德罗克", "遗留词",
}
assert expected.issubset(rejected)
assert "嗜血" not in rejected
assert {
    "鱼人（与现行名称", "保留原译", "保留两对重名",
    '混合使用"的"和"之', "仅否定该法术名", "死", "亡", "魔", "驱散",
    "说明词",
}.isdisjoint(rejected)
contextual = module.parse_contextual_decisions(sys.argv[2])
assert {
    (rule["key"], rule["rejected"], rule["correct"])
    for rule in contextual
} >= {("status|Blood", "嗜血", "血甲")}
PY
assert_status "validate-terms: active multiline/arbitrary-type decisions parse" \
    0 "$?"

python3 - "$SCAN_I18N" "$REPO_ROOT/docs/decisions.md" <<'PY'
import collections
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
counts = collections.Counter(
    classification["kind"]
    for classification in registry["classifications"]
)
assert counts["global"] == 12, counts
assert counts["contextual"] == 13, counts
assert len(registry["rejected_map"]) == counts["global"], registry
assert {
    "弹飞弹": "排斥飞弹",
    "弹开飞弹": "排斥飞弹",
    "埃瑞博拉": "埃雷博拉",
    "埃瑞博拉人": "埃雷博拉人",
    "宗古多克": "宗古德洛克",
    "宗古尔德罗克": "宗古德洛克",
    "月牙铲": "双头杖",
    "曳焰": "伊格尼斯",
    "曳焰伊格尼斯": "伊格尼斯",
}.items() <= registry["rejected_map"].items(), registry
contextual_by_decision = collections.Counter(
    rule["decision"] for rule in registry["contextual_rules"]
)
assert contextual_by_decision == {
    "D-A-007": 1,
    "D-D-005": 1,
    "D-A-046": 8,
    "D-C-107": 2,
    "D-C-108": 1,
}, contextual_by_decision
assert {
    (rule["decision"], rule["key"], rule["rejected"], rule["correct"])
    for rule in registry["contextual_rules"]
    if rule["decision"] in {"D-C-107", "D-C-108"}
} == {
    ("D-C-107", "status|ambrosia-drunk", "仙酒醉", "神食酣醉"),
    ("D-C-107", "status|Ambros", "仙酒", "神食"),
    ("D-C-108", "status|confused", "困惑", "混乱"),
}, registry["contextual_rules"]
PY
assert_status "validate-terms: production globals all have Choice mappings" \
    0 "$?"

VALID_DECISION_STATUSES="$TERMS_ROOT/valid-decision-statuses.md"
printf '%s\n' \
    '### D-Z-980 — exact reversed status fixture' \
    '- **Status**: reversed' \
    '- **Rejected**: other|Key' \
    '### D-Z-981 — active decision without Rejected fixture' \
    '- **Status**: active' \
    '### D-Z-982 — exact superseded status fixture' \
    '- **Status**: superseded → D-Z-981' \
    '- **Rejected**: other|Key' \
    > "$VALID_DECISION_STATUSES"

INVALID_DECISION_METADATA="$TERMS_ROOT/invalid-decision-metadata.md"
printf '%s\n' \
    '### D-Z-960 — active duplicate Rejected fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词' \
    '- **Rejected**: 旧译词' \
    '### D-Z-961 — reversed duplicate Rejected fixture' \
    '- **Status**: reversed' \
    '- **Rejected**: 遗留词' \
    '- **Rejected**: 旧译词' \
    '### D-Z-962 — superseded duplicate Rejected fixture' \
    '- **Status**: superseded → D-Z-981' \
    '- **Rejected**: 遗留词' \
    '- **Rejected**: 旧译词' \
    '### D-Z-963 — active duplicate Choice fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Choice**: 正确译名' \
    '- **Rejected**: 遗留词' \
    '### D-Z-964 — reversed duplicate Choice fixture' \
    '- **Status**: reversed' \
    '- **Choice**: 正确词' \
    '- **Choice**: 正确译名' \
    '### D-Z-965 — superseded duplicate Choice fixture' \
    '- **Status**: superseded → D-Z-981' \
    '- **Choice**: 正确词' \
    '- **Choice**: 正确译名' \
    '### D-Z-966 — duplicate Status fixture' \
    '- **Status**: active' \
    '- **Status**: active' \
    '### D-Z-967 — conflicting Status fixture' \
    '- **Status**: active' \
    '- **Status**: reversed' \
    '### D-Z-968 — misspelled Status fixture' \
    '- **Status**: actve' \
    '### D-Z-969 — missing Status fixture' \
    '- **Choice**: 正确词' \
    '### D-Z-970 — unknown Status fixture' \
    '- **Status**: draft' \
    '### D-Z-971 — active prefix Status fixture' \
    '- **Status**: active-ish' \
    '### D-Z-972 — decorated active Status fixture' \
    '- **Status**: active (draft)' \
    '### D-Z-973 — case-drift Status fixture' \
    '- **Status**: Active' \
    '### D-Z-974 — ASCII superseded arrow fixture' \
    '- **Status**: superseded -> D-Z-981' \
    > "$INVALID_DECISION_METADATA"

python3 - "$SCAN_I18N" "$VALID_DECISION_STATUSES" \
    "$INVALID_DECISION_METADATA" "$REPO_ROOT/docs/decisions.md" <<'PY'
import importlib.util
import re
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

real_classify = module._classify_decision_rejections
valid_classify_calls = []
def counting_valid(decision_id, block, *args):
    valid_classify_calls.append(decision_id)
    return real_classify(decision_id, block, *args)
module._classify_decision_rejections = counting_valid
try:
    valid = module.parse_decision_registry(sys.argv[2])
finally:
    module._classify_decision_rejections = real_classify
assert valid["rejected_map"] == {}, valid
assert valid["contextual_rules"] == [], valid
assert valid["classifications"] == [], valid
assert valid_classify_calls == ["D-Z-981"], valid_classify_calls

invalid_classify_calls = []
def counting_invalid(decision_id, block, *args):
    invalid_classify_calls.append(decision_id)
    return real_classify(decision_id, block, *args)
module._classify_decision_rejections = counting_invalid
try:
    module.parse_decision_registry(sys.argv[3])
except ValueError as error:
    message = str(error)
    expected = {
        "D-Z-960": "duplicate Rejected fields",
        "D-Z-961": "duplicate Rejected fields",
        "D-Z-962": "duplicate Rejected fields",
        "D-Z-963": "duplicate Choice fields",
        "D-Z-964": "duplicate Choice fields",
        "D-Z-965": "duplicate Choice fields",
        "D-Z-966": "duplicate Status fields",
        "D-Z-967": "conflicting Status fields",
        "D-Z-968": "invalid Status value: 'actve'",
        "D-Z-969": "missing Status field",
        "D-Z-970": "invalid Status value: 'draft'",
        "D-Z-971": "invalid Status value: 'active-ish'",
        "D-Z-972": "invalid Status value: 'active (draft)'",
        "D-Z-973": "invalid Status value: 'Active'",
        "D-Z-974": "invalid Status value: 'superseded -> D-Z-981'",
    }
    for decision, diagnostic in expected.items():
        assert f"{decision}: {diagnostic}" in message, message
else:
    raise AssertionError("invalid decision metadata was accepted")
finally:
    module._classify_decision_rejections = real_classify
assert invalid_classify_calls == [], invalid_classify_calls

with open(sys.argv[4], "r", encoding="utf-8") as stream:
    production_content = stream.read()
production_blocks = list(module._iter_decision_blocks(production_content))
heading_ids = re.findall(r"^###\s+(D-[A-Z]-\d+)\b", production_content, re.MULTILINE)
assert heading_ids, "production decision headings are missing"
assert [decision_id for decision_id, _ in production_blocks] == heading_ids
for decision_id, block in production_blocks:
    fields = module._decision_metadata_fields(block)
    assert fields.get("Status") == ["active"], (decision_id, fields)
    assert len(fields.get("Choice", [])) <= 1, (decision_id, fields)
    assert len(fields.get("Rejected", [])) <= 1, (decision_id, fields)
PY
assert_status "validate-terms: structured decision metadata is fail-closed" \
    0 "$?"

METADATA_SOURCE="$TERMS_ROOT/metadata/i18n/zh/source.txt"
mkdir -p "$(dirname "$METADATA_SOURCE")"
printf '%s\n' '%%%%' 'metadata fixture' '合法文本。' \
    > "$METADATA_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$INVALID_DECISION_METADATA" \
    --source-txt "$METADATA_SOURCE" \
    > /tmp/actual_validate_metadata.txt 2>&1
invalid_metadata_status=$?
set -e
assert_status "validate-terms: malformed decision metadata blocks CLI" \
    2 "$invalid_metadata_status"
for diagnostic in \
    "D-Z-960: duplicate Rejected fields" \
    "D-Z-961: duplicate Rejected fields" \
    "D-Z-962: duplicate Rejected fields" \
    "D-Z-963: duplicate Choice fields" \
    "D-Z-964: duplicate Choice fields" \
    "D-Z-965: duplicate Choice fields" \
    "D-Z-966: duplicate Status fields" \
    "D-Z-967: conflicting Status fields" \
    "D-Z-968: invalid Status value: 'actve'" \
    "D-Z-969: missing Status field" \
    "D-Z-970: invalid Status value: 'draft'" \
    "D-Z-971: invalid Status value: 'active-ish'" \
    "D-Z-972: invalid Status value: 'active (draft)'" \
    "D-Z-973: invalid Status value: 'Active'" \
    "D-Z-974: invalid Status value: 'superseded -> D-Z-981'"
do
    assert_contains "validate-terms metadata: $diagnostic" \
        "$diagnostic" /tmp/actual_validate_metadata.txt
done

python3 "$SCAN_I18N" validate-terms \
    --glossary "$VALID_DECISION_STATUSES" \
    --source-txt "$METADATA_SOURCE" \
    > /tmp/actual_validate_metadata.txt 2>&1
assert_status "validate-terms: exact inactive statuses stay inactive" \
    0 "$?"

CANONICAL_RESERVED_FIELDS="$TERMS_ROOT/canonical-reserved-fields.md"
printf '%b\n' \
    '### D-Z-989 — canonical reserved field whitespace fixture' \
    '-   **Status**: active' \
    '-\t\t**Choice**:\t正确词' \
    '- \t **Rejected**:\t遗留词' \
    '- **Rejected (old)**: distinct unknown field control' \
    '### D-Z-988 — lexical boundary negative controls' \
    '- **Status**: reversed' \
    'Rejected (old): raw distinct unknown field control' \
    'Ordinary prose mentions Rejected: without declaring it.' \
    'Rejected reason: historical spelling note' \
    'Choice of words: phrasing note' \
    '- **Rejected reason**: decorated historical spelling note' \
    '- **Choice of words**: decorated phrasing note' \
    > "$CANONICAL_RESERVED_FIELDS"

MALFORMED_RESERVED_FIELDS="$TERMS_ROOT/malformed-reserved-fields.md"
printf '%b\n' \
    '### D-Z-990 — missing marker reserved declaration fixture' \
    '- **Status**: active' \
    '**Rejected**: 遗留词' \
    '### D-Z-991 — one-space indented reserved declaration fixture' \
    '- **Status**: reversed' \
    ' - **Rejected**: 遗留词' \
    '### D-Z-992 — three-space indented reserved declaration fixture' \
    '- **Status**: superseded → D-Z-990' \
    '   - **Rejected**: 遗留词' \
    '### D-Z-993 — tab-indented reserved declaration fixture' \
    '- **Status**: active' \
    '\t- **Rejected**: 遗留词' \
    '### D-Z-994 — star marker reserved declaration fixture' \
    '- **Status**: reversed' \
    '* **Rejected**: 遗留词' \
    '### D-Z-995 — plus marker reserved declaration fixture' \
    '- **Status**: superseded → D-Z-990' \
    '+ **Rejected**: 遗留词' \
    '### D-Z-996 — numbered-dot marker reserved declaration fixture' \
    '- **Status**: active' \
    '1. **Rejected**: 遗留词' \
    '### D-Z-997 — numbered-paren marker reserved declaration fixture' \
    '- **Status**: reversed' \
    '1) **Rejected**: 遗留词' \
    '### D-Z-998 — lowercase reserved label fixture' \
    '- **Status**: superseded → D-Z-990' \
    '- **rejected**: 遗留词' \
    '### D-Z-999 — uppercase reserved label fixture' \
    '- **Status**: active' \
    '- **REJECTED**: 遗留词' \
    '### D-Z-1000 — leading label whitespace fixture' \
    '- **Status**: reversed' \
    '- ** Rejected**: 遗留词' \
    '### D-Z-1001 — trailing label whitespace fixture' \
    '- **Status**: superseded → D-Z-990' \
    '- **Rejected **: 遗留词' \
    '### D-Z-1002 — triple-bold reserved label fixture' \
    '- **Status**: active' \
    '- ***Rejected***: 遗留词' \
    '### D-Z-1003 — colon-inside-bold reserved label fixture' \
    '- **Status**: reversed' \
    '- **Rejected:** 遗留词' \
    '### D-Z-1004 — whitespace-before-colon reserved label fixture' \
    '- **Status**: superseded → D-Z-990' \
    '- **Rejected** : 遗留词' \
    '### D-Z-1005 — malformed Choice reserved label fixture' \
    '- **Status**: active' \
    '- **choice**: 正确词' \
    '### D-Z-1006 — malformed Status reserved label fixture' \
    '- **Status**: reversed' \
    '- ***Status***: active' \
    '### D-Z-1007 — underscore emphasis fixture' \
    '- **Status**: active' \
    '- __Rejected__: 遗留词' \
    '### D-Z-1008 — triple underscore emphasis fixture' \
    '- **Status**: reversed' \
    '- ___Rejected___: 遗留词' \
    '### D-Z-1009 — mixed emphasis fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- **_Rejected_**: 遗留词' \
    '### D-Z-1010 — raw reserved label fixture' \
    '- **Status**: active' \
    '- Rejected: 遗留词' \
    '### D-Z-1011 — blockquote container fixture' \
    '- **Status**: reversed' \
    '> - **Rejected**: 遗留词' \
    '### D-Z-1012 — nested unordered container fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- - **Rejected**: 遗留词' \
    '### D-Z-1013 — nested ordered container fixture' \
    '- **Status**: active' \
    '1. 1. **Rejected**: 遗留词' \
    '### D-Z-1014 — task-list container fixture' \
    '- **Status**: reversed' \
    '- [ ] **Rejected**: 遗留词' \
    '### D-Z-1015 — backtick wrapper fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- `Rejected`: 遗留词' \
    '### D-Z-1016 — fullwidth colon fixture' \
    '- **Status**: active' \
    '- **Rejected**：遗留词' \
    '### D-Z-1017 — disguised Choice fixture' \
    '- **Status**: reversed' \
    '> - __Choice__：正确词' \
    '### D-Z-1018 — disguised Status fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- [ ] `Status`：active' \
    '### D-Z-1019 — zero-separator marker fixture' \
    '- **Status**: active' \
    '-**Rejected**: 遗留词' \
    '### D-Z-1020 — doubled delimiter fixture' \
    '- **Status**: reversed' \
    '- **Rejected**:: 遗留词' \
    '### D-Z-1021 — mixed doubled delimiter fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- **Rejected**:：遗留词' \
    '### D-Z-1022 — decorated missing delimiter fixture' \
    '- **Status**: active' \
    '- **Rejected** 遗留词' \
    '### D-Z-1023 — wrapper tail fixture' \
    '- **Status**: reversed' \
    '- **Rejected**x: 遗留词' \
    '### D-Z-1024 — nested value-start fixture' \
    '- **Status**: superseded → D-Z-989' \
    '- **Rejected**: - **Choice**: 正确词' \
    > "$MALFORMED_RESERVED_FIELDS"

python3 - "$SCAN_I18N" "$CANONICAL_RESERVED_FIELDS" \
    "$MALFORMED_RESERVED_FIELDS" "$REPO_ROOT/docs/decisions.md" \
    "$METADATA_SOURCE" <<'PY'
import collections
import importlib.util
import itertools
import os
import subprocess
import sys
import tempfile

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

canonical = module.parse_decision_registry(sys.argv[2])
assert canonical["rejected_map"] == {"遗留词": "正确词"}, canonical
with open(sys.argv[2], "r", encoding="utf-8") as stream:
    canonical_blocks = list(module._iter_decision_blocks(stream.read()))
canonical_block = canonical_blocks[0][1]
fields = module._decision_metadata_fields(canonical_block)
assert fields["Status"] == ["active"], fields
assert fields["Choice"] == ["正确词"], fields
assert fields["Rejected"] == ["遗留词"], fields
assert fields["Rejected (old)"] == [
    "distinct unknown field control",
], fields

real_classify = module._classify_decision_rejections
classify_calls = []
def counting_classify(decision_id, block, *args):
    classify_calls.append(decision_id)
    return real_classify(decision_id, block, *args)
module._classify_decision_rejections = counting_classify

def assert_malformed(content, expected_decisions):
    blocks = list(module._iter_decision_blocks(content))
    assert [decision for decision, _block in blocks] == expected_decisions
    try:
        module._parse_decision_content(content)
    except ValueError as error:
        message = str(error)
        for decision in expected_decisions:
            assert decision in message, (decision, message)
            assert (
                f"{decision}: malformed reserved metadata declaration"
                in message
            ), message
    else:
        raise AssertionError("malformed reserved declarations were accepted")
    for decision, block in blocks:
        declarations = module._decision_reserved_declarations(block)
        assert len(declarations) == 2, (decision, declarations)
        assert sum(item[2] for item in declarations) == 1, (
            decision,
            declarations,
        )

try:
    with open(sys.argv[3], "r", encoding="utf-8") as stream:
        assert_malformed(
            stream.read(),
            [f"D-Z-{number}" for number in range(990, 1025)],
        )

    c8_malformed_declarations = [
        "**Rejected**: 遗留词",
        " - **Rejected**: 遗留词",
        "   - **Rejected**: 遗留词",
        "\t- **Rejected**: 遗留词",
        "* **Rejected**: 遗留词",
        "+ **Rejected**: 遗留词",
        "1. **Rejected**: 遗留词",
        "1) **Rejected**: 遗留词",
        "- **rejected**: 遗留词",
        "- **REJECTED**: 遗留词",
        "- ** Rejected**: 遗留词",
        "- **Rejected **: 遗留词",
        "- ***Rejected***: 遗留词",
        "- **Rejected:** 遗留词",
        "- **Rejected** : 遗留词",
        "- **choice**: 正确词",
        "- ***Status***: active",
    ]
    values = {
        "Status": "active",
        "Choice": "正确词",
        "Rejected": "遗留词",
    }
    reviewer_templates = [
        "- __{name}__: {value}",
        "- ___{name}___: {value}",
        "- **_{name}_**: {value}",
        "{name}: {value}",
        "- {name}: {value}",
        "> - **{name}**: {value}",
        "- - **{name}**: {value}",
        "1. 1. **{name}**: {value}",
        "- [ ] **{name}**: {value}",
        "- `{name}`: {value}",
        "- **{name}**：{value}",
    ]
    reviewer_malformed_declarations = [
        template.format(name=name, value=values[name])
        for template in reviewer_templates
        for name in ("Status", "Choice", "Rejected")
    ]
    names = ("Status", "Choice", "Rejected")
    zero_separator_declarations = [
        f"{marker}**{name}**: {values[name]}"
        for marker in ("-", "+", "1.", "1)")
        for name in names
    ]
    delimiter_declarations = []
    for name in names:
        for count in range(5):
            for delimiters in itertools.product(":：", repeat=count):
                delimiter = "".join(delimiters)
                if delimiter == ":":
                    continue
                delimiter_declarations.append(
                    f"- **{name}**{delimiter} {values[name]}"
                )
        for whitespace in (" ", "\t"):
            for delimiter in (":", "："):
                delimiter_declarations.append(
                    f"- **{name}**{whitespace}{delimiter} "
                    f"{values[name]}"
                )
    wrapper_tail_templates = [
        "- **{name}**x: {value}",
        "- **{name}** x: {value}",
        "- **{name}**\tx: {value}",
        "- __{name}__x: {value}",
        "- `{name}`x: {value}",
        "- ** _{name}_ **x: {value}",
        "- * {name}*x: {value}",
        "- *\t{name}*\tx: {value}",
    ]
    wrapper_tail_declarations = [
        template.format(name=name, value=values[name])
        for template in wrapper_tail_templates
        for name in names
    ]
    nested_value_templates = [
        "- **{outer}**: - **{inner}**: {value}",
        "- **{outer}**: {inner}: {value}",
        "- **{outer}**: > - __{inner}__：{value}",
    ]
    nested_value_declarations = [
        template.format(
            outer=outer,
            inner=inner,
            value=values[inner],
        )
        for template in nested_value_templates
        for outer in names
        for inner in names
    ]
    repeated_container_templates = [
        "> > - [ ] 1. **{name}**: {value}",
        "- -**{name}**: {value}",
        "1. > +**{name}**: {value}",
        ">1)**{name}**: {value}",
    ]
    repeated_container_declarations = [
        template.format(name=name, value=values[name])
        for template in repeated_container_templates
        for name in names
    ]
    assert len(c8_malformed_declarations) == 17
    assert len(reviewer_malformed_declarations) == 33
    assert len(zero_separator_declarations) == 12
    assert len(delimiter_declarations) == 102
    assert len(wrapper_tail_declarations) == 24
    assert len(nested_value_declarations) == 27
    assert len(repeated_container_declarations) == 12
    lifecycle_statuses = [
        "active",
        "reversed",
        "superseded → D-Z-989",
    ]
    matrix_blocks = []
    matrix_decisions = []
    next_number = 1100
    for declaration in (
        c8_malformed_declarations
        + reviewer_malformed_declarations
        + zero_separator_declarations
        + delimiter_declarations
        + wrapper_tail_declarations
        + nested_value_declarations
        + repeated_container_declarations
    ):
        for status in lifecycle_statuses:
            decision = f"D-Z-{next_number}"
            matrix_decisions.append(decision)
            matrix_blocks.extend([
                f"### {decision} — lifecycle matrix fixture",
                f"- **Status**: {status}",
                declaration,
            ])
            next_number += 1
    assert len(matrix_decisions) == 681, len(matrix_decisions)
    matrix_content = "\n".join(matrix_blocks)
    assert_malformed(matrix_content, matrix_decisions)

    with tempfile.TemporaryDirectory() as temp_root:
        matrix_path = os.path.join(temp_root, "decisions.md")
        with open(matrix_path, "w", encoding="utf-8") as stream:
            stream.write(matrix_content)
        result = subprocess.run(
            [
                sys.executable,
                sys.argv[1],
                "validate-terms",
                "--glossary",
                matrix_path,
                "--source-txt",
                sys.argv[5],
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2, (
            result.returncode,
            result.stdout,
            result.stderr,
        )
        diagnostic = result.stdout + result.stderr
        for decision in matrix_decisions:
            assert (
                f"{decision}: malformed reserved metadata declaration"
                in diagnostic
            ), (decision, diagnostic)

    for name in names:
        for line in (
            f"- **{name}**: {values[name]}",
            f"-\t**{name}**:\t{values[name]}",
            f"- **{name}**: term: explanation",
            f"- **{name}**: Rejected (old): explanation",
        ):
            token = module._decision_reserved_token(line)
            assert token is not None and token[0] == name, (line, token)
            assert module._decision_canonical_reserved_field(
                line, name
            ), line

    span_line = "> > - [ ] 1. **Rejected**: 遗留词"
    span_token = module._decision_reserved_token(span_line)
    assert span_token is not None, span_line
    span_name, span_start, span_end = span_token
    assert span_name == "Rejected", span_token
    assert span_line[span_start:span_end] == "**Rejected**", (
        span_line,
        span_token,
    )
    for line in (
        "Rejected (old): raw distinct unknown field control",
        "Rejected reason: historical spelling note",
        "Choice of words: phrasing note",
        "- **Rejected (old)**: decorated historical spelling note",
        "- **Rejected reason**: decorated historical spelling note",
        "- **Choice of words**: decorated phrasing note",
        "Ordinary prose mentions Rejected: without declaring it.",
    ):
        assert module._decision_reserved_token(line) is None, line

    canonical_declarations = [
        (decision, *declaration)
        for decision, block in canonical_blocks
        for declaration in module._decision_reserved_declarations(block)
    ]
    assert [
        (decision, name, is_canonical)
        for decision, name, _line, is_canonical
        in canonical_declarations
    ] == [
        ("D-Z-989", "Status", True),
        ("D-Z-989", "Choice", True),
        ("D-Z-989", "Rejected", True),
        ("D-Z-988", "Status", True),
    ], canonical_declarations
    assert all(
        not module._decision_reserved_field_errors(decision, block)
        for decision, block in canonical_blocks
    )

    with open(sys.argv[4], "r", encoding="utf-8") as stream:
        production_blocks = list(
            module._iter_decision_blocks(stream.read())
        )
    production_declarations = [
        (decision, *declaration)
        for decision, block in production_blocks
        for declaration in module._decision_reserved_declarations(block)
    ]
    expected_identities = collections.Counter(
        (decision, name)
        for decision, block in production_blocks
        for name, values in module._decision_metadata_fields(block).items()
        if name in ("Status", "Choice", "Rejected")
        for _value in values
    )
    actual_identities = collections.Counter(
        (decision, name)
        for decision, name, _line, _is_canonical
        in production_declarations
    )
    assert actual_identities == expected_identities, (
        actual_identities,
        expected_identities,
    )
    assert production_declarations, "production reserved declarations are missing"
    assert all(
        is_canonical
        for _decision, _name, _line, is_canonical
        in production_declarations
    ), production_declarations
finally:
    module._classify_decision_rejections = real_classify
assert classify_calls == [], classify_calls
PY
assert_status "validate-terms: reserved field syntax is exact" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MALFORMED_RESERVED_FIELDS" \
    --source-txt "$METADATA_SOURCE" \
    > /tmp/actual_reserved_metadata.txt 2>&1
malformed_reserved_status=$?
set -e
assert_status "validate-terms: malformed reserved fields block CLI" \
    2 "$malformed_reserved_status"
for number in \
    990 991 992 993 994 995 996 997 998 \
    999 1000 1001 1002 1003 1004 1005 1006 \
    1007 1008 1009 1010 1011 1012 1013 1014 \
    1015 1016 1017 1018 1019 1020 1021 1022 \
    1023 1024
do
    assert_contains "validate-terms reserved declaration: D-Z-$number" \
        "D-Z-$number: malformed reserved metadata declaration" \
        /tmp/actual_reserved_metadata.txt
done

CANONICAL_RESERVED_SOURCE="$TERMS_ROOT/canonical-reserved/i18n/zh/source.txt"
mkdir -p "$(dirname "$CANONICAL_RESERVED_SOURCE")"
printf '%s\n' '%%%%' 'canonical reserved fixture' '仍有遗留词。' \
    > "$CANONICAL_RESERVED_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CANONICAL_RESERVED_FIELDS" \
    --source-txt "$CANONICAL_RESERVED_SOURCE" \
    > /tmp/actual_reserved_metadata.txt 2>&1
canonical_reserved_status=$?
set -e
assert_status "validate-terms: canonical horizontal whitespace stays valid" \
    1 "$canonical_reserved_status"
assert_contains "validate-terms: canonical reserved field reaches scan" \
    "Rejected: '遗留词'" /tmp/actual_reserved_metadata.txt

CANONICAL_DECISIONS="$TERMS_ROOT/canonical-decisions.md"
CANONICAL_KEY='It inflicts extra damage against dragons and draconians.'
printf '%s\n' \
    '### D-A-007 — canonical unqualified contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    "| \`$CANONICAL_KEY\` | 对龙和龙人造成额外伤害。 |" \
    '- **Rejected**: `IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIANS. → 龙裔`' \
    > "$CANONICAL_DECISIONS"
python3 - "$SCAN_I18N" "$CANONICAL_DECISIONS" "$CANONICAL_KEY" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.parse_contextual_decisions(sys.argv[2]) == [{
    "decision": "D-A-007",
    "key": sys.argv[3],
    "rejected": "龙裔",
    "correct": "对龙和龙人造成额外伤害。",
}]
PY
assert_status "validate-terms: uppercase unqualified arrow binds canonical key" \
    0 "$?"

CANONICAL_SOURCE="$TERMS_ROOT/canonical/i18n/zh/source.txt"
mkdir -p "$(dirname "$CANONICAL_SOURCE")"
printf '%s\n' \
    '%%%%' 'IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIANS.' \
    '前缀龙裔后缀' \
    > "$CANONICAL_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CANONICAL_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
canonical_case_status=$?
set -e
assert_status "validate-terms: uppercase unqualified scope reaches SourceDB" \
    1 "$canonical_case_status"
assert_contains "validate-terms: uppercase unqualified scope checks rejection" \
    "Rejected: '龙裔'" /tmp/actual_validate_terms.txt

TYPO_DECISIONS="$TERMS_ROOT/typo-decisions.md"
printf '%s\n' \
    '### D-A-007 — typo contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    "| \`$CANONICAL_KEY\` | 对龙和龙人造成额外伤害。 |" \
    '- **Rejected**: `IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIAN. → 龙裔`' \
    > "$TYPO_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TYPO_DECISIONS" --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
typo_context_status=$?
set -e
assert_status "validate-terms: table-bound typo arrow fails closed" \
    2 "$typo_context_status"
assert_contains "validate-terms: typo diagnostic names Context mismatch" \
    "does not match an exact non-empty Context table key" \
    /tmp/actual_validate_terms.txt

MISSING_ARROW_DECISIONS="$TERMS_ROOT/missing-arrow-decisions.md"
printf '%s\n' \
    '### D-A-007 — missing-arrow contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    "| \`$CANONICAL_KEY\` | 对龙和龙人造成额外伤害。 |" \
    '- **Rejected**: `IT INFLICTS EXTRA DAMAGE AGAINST DRAGONS AND DRACONIANS.`' \
    > "$MISSING_ARROW_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MISSING_ARROW_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_arrow_status=$?
set -e
assert_status "validate-terms: uppercase table token without arrow fails closed" \
    2 "$missing_arrow_status"
assert_contains "validate-terms: missing-arrow diagnostic is explicit" \
    "contextual Rejected mapping is missing an arrow" \
    /tmp/actual_validate_terms.txt

QUALIFIED_CASE_DECISIONS="$TERMS_ROOT/qualified-case-decisions.md"
printf '%s\n' \
    '### D-D-005 — qualified canonical association fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `DUR_SANGUINE_ARMOUR` / `status\|Blood` defensive status | 血甲 |' \
    '- **Rejected**: `STATUS|BLOOD → 嗜血`' \
    > "$QUALIFIED_CASE_DECISIONS"
python3 - "$SCAN_I18N" "$QUALIFIED_CASE_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.parse_contextual_decisions(sys.argv[2]) == [{
    "decision": "D-D-005",
    "key": "status|Blood",
    "rejected": "嗜血",
    "correct": "血甲",
}]
PY
assert_status "validate-terms: qualified case resolves exact raw table key" \
    0 "$?"

UNBACKTICKED_DECISIONS="$TERMS_ROOT/unbackticked-decisions.md"
printf '%s\n' \
    '### D-D-005 — unbackticked contextual mapping fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: status|Blood → 嗜血' \
    > "$UNBACKTICKED_DECISIONS"

MIXED_REJECTED_DECISIONS="$TERMS_ROOT/mixed-rejected-decisions.md"
printf '%s\n' \
    '### D-D-005 — mixed rejected-field fixture' \
    '- **Status**: active' \
    '- **Choice**: 万魔殿' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: 魔窟、`status|Blood → 嗜血`' \
    > "$MIXED_REJECTED_DECISIONS"

GLOBAL_WITH_EXPLANATION="$TERMS_ROOT/global-with-explanation.md"
printf '%s\n' \
    '### D-Z-922 — global plus ordinary arrow explanation fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词、`source → target`（历史说明，不是 SourceDB key）' \
    > "$GLOBAL_WITH_EXPLANATION"

FUSED_PAREN_ARROW_EXPLANATION="$TERMS_ROOT/fused-paren-arrow.md"
printf '%s\n' \
    '### D-Z-952 — global plus fused parenthetical arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词（历史说明："legacy → 旧译"）' \
    > "$FUSED_PAREN_ARROW_EXPLANATION"

FUSED_QUOTED_ARROW_EXPLANATION="$TERMS_ROOT/fused-quoted-arrow.md"
printf '%s\n' \
    '### D-Z-953 — global plus fused quoted arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词 "legacy → 旧译"' \
    > "$FUSED_QUOTED_ARROW_EXPLANATION"

MIDDLE_ARROW_BOTH_SIDES="$TERMS_ROOT/middle-arrow-both-sides.md"
printf '%s\n' \
    '### D-Z-954 — arrow explanation with two residuals fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留前（历史说明："legacy → 旧译"）遗留后' \
    > "$MIDDLE_ARROW_BOTH_SIDES"

FUSED_ARROW_WITH_SUFFIX="$TERMS_ROOT/fused-arrow-with-suffix.md"
printf '%s\n' \
    '### D-Z-955 — fused arrow plus unconsumed suffix fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词（历史说明："legacy → 旧译"）尾词' \
    > "$FUSED_ARROW_WITH_SUFFIX"

LEADING_ARROW_GLOBAL="$TERMS_ROOT/leading-arrow-global.md"
printf '%s\n' \
    '### D-Z-956 — leading arrow explanation plus global fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: （历史说明："legacy → 旧译"）遗留词' \
    > "$LEADING_ARROW_GLOBAL"

MULTI_ARROW_GLOBAL="$TERMS_ROOT/multi-arrow-global.md"
printf '%s\n' \
    '### D-Z-957 — multiple arrow explanations plus global fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: （历史说明："legacy → 旧译"）（历史说明："old → 旧"）遗留词' \
    > "$MULTI_ARROW_GLOBAL"

PURE_ARROW_EXPLANATIONS="$TERMS_ROOT/pure-arrow-explanations.md"
printf '%s\n' \
    '### D-Z-958 — fully quoted arrow explanation fixture' \
    '- **Status**: active' \
    '- **Rejected**: "legacy → 旧译"' \
    '### D-Z-959 — fully parenthesized arrow explanation fixture' \
    '- **Status**: active' \
    '- **Rejected**: （历史说明："legacy → 旧译"）' \
    '### D-Z-960 — explicitly prefixed arrow explanation fixture' \
    '- **Status**: active' \
    '- **Rejected**: 历史说明："legacy → 旧译"' \
    > "$PURE_ARROW_EXPLANATIONS"

CONTEXT_WITH_EXPLANATION="$TERMS_ROOT/context-with-explanation.md"
printf '%s\n' \
    '### D-D-005 — contextual mapping plus historical arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`、（历史说明："legacy → 旧译"）' \
    > "$CONTEXT_WITH_EXPLANATION"

TABLE_QUOTED_UNQUALIFIED="$TERMS_ROOT/table-quoted-unqualified.md"
printf '%s\n' \
    '### D-A-007 — quoted unqualified mapping with Context table fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `EXACT KEY` | 正确词 |' \
    '- **Rejected**: "EXACT KEY → 遗留词"' \
    > "$TABLE_QUOTED_UNQUALIFIED"

TABLE_MARKED_MATCHING_ARROW="$TERMS_ROOT/table-marked-matching-arrow.md"
printf '%s\n' \
    '### D-A-007 — marked arrow matching Context identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `EXACT KEY` | 正确词 |' \
    '- **Rejected**: "exact key → 遗留词（历史说明）"' \
    > "$TABLE_MARKED_MATCHING_ARROW"

CONTEXT_BOUNDARY_PUNCTUATION="$TERMS_ROOT/context-boundary-punctuation.md"
CONTEXT_BOUNDARY_CHARS=(
    ',' '，' ';' '；' '.' '。' '!' '！' '?' '？' '/' '、'
)
CONTEXT_BOUNDARY_WRAPPERS=('quoted' 'parenthesized')
CONTEXT_BOUNDARY_DECISION_IDS=()
: > "$CONTEXT_BOUNDARY_PUNCTUATION"
context_boundary_id=1100
for context_boundary_char in "${CONTEXT_BOUNDARY_CHARS[@]}"; do
    for context_boundary_wrapper in "${CONTEXT_BOUNDARY_WRAPPERS[@]}"; do
        context_boundary_decision="D-Z-$context_boundary_id"
        CONTEXT_BOUNDARY_DECISION_IDS+=("$context_boundary_decision")
        if [ "$context_boundary_wrapper" = "quoted" ]; then
            context_boundary_rejected="\"历史说明${context_boundary_char}EXACT KEY → 遗留词\""
        else
            context_boundary_rejected="（历史说明${context_boundary_char}EXACT KEY → 遗留词）"
        fi
        printf '%s\n' \
            "### $context_boundary_decision — punctuation boundary fixture" \
            '- **Status**: active' \
            '| Context | ZH |' \
            '|---------|----|' \
            '| `EXACT KEY` | 正确词 |' \
            "- **Rejected**: $context_boundary_rejected" \
            >> "$CONTEXT_BOUNDARY_PUNCTUATION"
        context_boundary_id=$((context_boundary_id + 1))
    done
done
unset context_boundary_char context_boundary_wrapper
unset context_boundary_decision context_boundary_rejected context_boundary_id

QUOTED_QUALIFIED_DECISIONS="$TERMS_ROOT/quoted-qualified-decisions.md"
printf '%s\n' \
    '### D-D-005 — quoted qualified mapping fixture' \
    '- **Status**: active' \
    '- **Choice**: 血甲' \
    '- **Rejected**: "status|Blood → 嗜血"' \
    > "$QUOTED_QUALIFIED_DECISIONS"

PAREN_QUALIFIED_DECISIONS="$TERMS_ROOT/paren-qualified-decisions.md"
printf '%s\n' \
    '### D-D-005 — parenthesized qualified mapping fixture' \
    '- **Status**: active' \
    '- **Choice**: 血甲' \
    '- **Rejected**: （status|Blood → 嗜血）' \
    > "$PAREN_QUALIFIED_DECISIONS"

QUALIFIED_NO_TABLE_DECISIONS="$TERMS_ROOT/qualified-no-table-decisions.md"
printf '%s\n' \
    '### D-D-005 — qualified mapping without Context table fixture' \
    '- **Status**: active' \
    '- **Choice**: 血甲' \
    '- **Rejected**: `status|Blood → 嗜血`' \
    > "$QUALIFIED_NO_TABLE_DECISIONS"

PREFIXED_ORDINARY_ARROW_DECISIONS="$TERMS_ROOT/prefixed-ordinary-arrow.md"
printf '%s\n' \
    '### D-Z-926 — unconsumed prefix before ordinary arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词 `source → target`' \
    > "$PREFIXED_ORDINARY_ARROW_DECISIONS"

PAREN_PREFIXED_ORDINARY_ARROW="$TERMS_ROOT/paren-prefixed-ordinary-arrow.md"
printf '%s\n' \
    '### D-Z-928 — parenthetical suffix cannot hide prefix fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词 `source → target`（历史说明，不是 SourceDB key）' \
    > "$PAREN_PREFIXED_ORDINARY_ARROW"

PAREN_SUFFIXED_ORDINARY_ARROW="$TERMS_ROOT/paren-suffixed-ordinary-arrow.md"
printf '%s\n' \
    '### D-Z-929 — parenthetical suffix cannot absorb plain suffix fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: `source → target` 遗留词（历史说明）' \
    > "$PAREN_SUFFIXED_ORDINARY_ARROW"

NO_ARROW_CONTEXT_DECISIONS="$TERMS_ROOT/no-arrow-context-decisions.md"
printf '%s\n' \
    '### D-D-930 — bare Context identity without arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: status|Blood' \
    '### D-D-931 — quoted Context identity without arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: "status|Blood"' \
    '### D-D-932 — parenthesized Context identity without arrow fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: （status|Blood）' \
    '### D-D-933 — mixed historical Context identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: 历史说明："status|Blood"' \
    '### D-D-941 — bare nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: other|Key' \
    '### D-D-942 — quoted nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: "other|Key"' \
    '### D-D-943 — parenthesized nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: （other|Key）' \
    '### D-D-944 — mixed historical nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: 历史说明："other|Key"' \
    '### D-D-945 — escaped nonmatching pipe identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: other\|Key' \
    > "$NO_ARROW_CONTEXT_DECISIONS"

NO_CONTEXT_PIPE_DECISIONS="$TERMS_ROOT/no-context-pipe-decisions.md"
printf '%s\n' \
    '### D-Z-946 — bare pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: other|Key' \
    '### D-Z-947 — quoted pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: "other|Key"' \
    '### D-Z-948 — parenthesized pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: （other|Key）' \
    '### D-Z-949 — mixed historical pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: 历史说明："other|Key"' \
    '### D-Z-950 — escaped pipe identity without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: other\|Key' \
    > "$NO_CONTEXT_PIPE_DECISIONS"

NO_CONTEXT_HISTORICAL_DECISIONS="$TERMS_ROOT/no-context-historical.md"
printf '%s\n' \
    '### D-Z-951 — narrow historical explanation without Context fixture' \
    '- **Status**: active' \
    '- **Rejected**: 历史说明："legacy identity"' \
    > "$NO_CONTEXT_HISTORICAL_DECISIONS"

HISTORICAL_NON_CONTEXT_DECISIONS="$TERMS_ROOT/historical-non-context.md"
printf '%s\n' \
    '### D-D-934 — nonmatching historical explanation fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: （历史说明："legacy status identity"）' \
    > "$HISTORICAL_NON_CONTEXT_DECISIONS"

LIST_MARKER_DECISIONS="$TERMS_ROOT/list-marker-decisions.md"
printf '%s\n' \
    '### D-Z-935 — every supported Markdown list marker fixture' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `One → 正一`' \
    '  * `Two → 正二`' \
    '  + `Three → 正三`' \
    '  1. `Four → 正四`' \
    '  2) `Five → 正五`' \
    '- **Rejected**:' \
    '  - 旧一' \
    '  * 旧二' \
    '  + 旧三' \
    '  1. 旧四' \
    '  2) 旧五' \
    > "$LIST_MARKER_DECISIONS"

GLOBAL_ORDINAL_DECISIONS="$TERMS_ROOT/global-ordinal-decisions.md"
printf '%s\n' \
    '### D-Z-936 — explanations do not shift Choice pairing fixture' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `One → 正甲`' \
    '  - `Two → 正乙`' \
    '  - `Three → 正丙`' \
    '- **Rejected**:' \
    '  - （前置历史说明）' \
    '  - 旧甲' \
    '  - （中间历史说明）' \
    '  - 旧乙' \
    '  - 旧丙' \
    '  - （尾部历史说明）' \
    > "$GLOBAL_ORDINAL_DECISIONS"

MISSING_CHOICE_DECISIONS="$TERMS_ROOT/missing-choice-decisions.md"
printf '%s\n' \
    '### D-Z-937 — global rejection without Choice fixture' \
    '- **Status**: active' \
    '- **Rejected**: 遗留词' \
    > "$MISSING_CHOICE_DECISIONS"

UNPARSEABLE_CHOICE_DECISIONS="$TERMS_ROOT/unparseable-choice-decisions.md"
printf '%s\n' \
    '### D-Z-938 — global rejection with prose Choice fixture' \
    '- **Status**: active' \
    '- **Choice**: 以下为完整对照表：' \
    '- **Rejected**: 遗留词' \
    > "$UNPARSEABLE_CHOICE_DECISIONS"

AMBIGUOUS_CHOICE_DECISIONS="$TERMS_ROOT/ambiguous-choice-decisions.md"
printf '%s\n' \
    '### D-Z-939 — ambiguous Choice cardinality fixture' \
    '- **Status**: active' \
    '- **Choice**:' \
    '  - `One → 正一`' \
    '  - `Two → 正二`' \
    '- **Rejected**: 旧一、旧二、旧三' \
    > "$AMBIGUOUS_CHOICE_DECISIONS"

python3 - "$SCAN_I18N" "$NO_ARROW_CONTEXT_DECISIONS" \
    "$HISTORICAL_NON_CONTEXT_DECISIONS" "$LIST_MARKER_DECISIONS" \
    "$GLOBAL_ORDINAL_DECISIONS" "$MISSING_CHOICE_DECISIONS" \
    "$UNPARSEABLE_CHOICE_DECISIONS" "$AMBIGUOUS_CHOICE_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

try:
    module.parse_contextual_decisions(sys.argv[2])
except ValueError as error:
    message = str(error)
    for decision in ("D-D-930", "D-D-931", "D-D-932", "D-D-933"):
        assert decision in message, message
    assert message.count("matches an exact Context table key") == 4, message
    for decision in (
        "D-D-941", "D-D-942", "D-D-943", "D-D-944", "D-D-945",
    ):
        assert decision in message, message
    assert message.count(
        "pipe-qualified Rejected identity must use a backticked arrow mapping"
    ) == 5, message
else:
    raise AssertionError("no-arrow pipe identities were accepted")

historical = module.parse_decision_registry(sys.argv[3])
assert [
    item["kind"] for item in historical["classifications"]
] == ["explanation"], historical

markers = module.parse_decision_registry(sys.argv[4])
assert markers["rejected_map"] == {
    "旧一": "正一",
    "旧二": "正二",
    "旧三": "正三",
    "旧四": "正四",
    "旧五": "正五",
}, markers
assert [
    item["kind"] for item in markers["classifications"]
] == ["global"] * 5, markers

ordinals = module.parse_decision_registry(sys.argv[5])
assert ordinals["rejected_map"] == {
    "旧甲": "正甲",
    "旧乙": "正乙",
    "旧丙": "正丙",
}, ordinals
assert [
    item["kind"] for item in ordinals["classifications"]
] == [
    "explanation", "global", "explanation", "global", "global",
    "explanation",
], ordinals

expected_errors = (
    "global Rejected terms require a non-empty Choice",
    "cannot determine a Choice mapping for global Rejected terms",
    "Choice count 2 cannot map deterministically to 3 global Rejected terms",
)
for path, diagnostic in zip(sys.argv[6:], expected_errors):
    try:
        module.parse_decision_registry(path)
    except ValueError as error:
        assert diagnostic in str(error), str(error)
    else:
        raise AssertionError(f"unmapped global rejection accepted: {path}")
PY
assert_status "validate-terms: Context, Choice, list, and ordinal invariants" \
    0 "$?"

python3 - "$SCAN_I18N" "$NO_CONTEXT_PIPE_DECISIONS" \
    "$NO_CONTEXT_HISTORICAL_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.parse_decision_registry(sys.argv[2])
except ValueError as error:
    message = str(error)
    for decision in (
        "D-Z-946", "D-Z-947", "D-Z-948", "D-Z-949", "D-Z-950",
    ):
        assert decision in message, message
    assert message.count(
        "pipe-qualified Rejected identity must use a backticked arrow mapping"
    ) == 5, message
else:
    raise AssertionError("no-Context pipe identities were accepted")

historical = module.parse_decision_registry(sys.argv[3])
assert [
    item["kind"] for item in historical["classifications"]
] == ["explanation"], historical
PY
assert_status "validate-terms: pipe syntax fails closed without Context" \
    0 "$?"

UNBALANCED_DECISIONS="$TERMS_ROOT/unbalanced-decisions.md"
printf '%s\n' \
    '### D-Z-923 — unclosed code span fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: `遗留词' \
    '### D-Z-924 — unclosed quote fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: "遗留词' \
    '### D-Z-925 — unclosed parenthesis fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: （遗留词' \
    > "$UNBALANCED_DECISIONS"

python3 - "$SCAN_I18N" "$UNBACKTICKED_DECISIONS" \
    "$MIXED_REJECTED_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.parse_decisions(sys.argv[3])
except ValueError as error:
    assert "unconsumed contextual Rejected text" in str(error), str(error)
else:
    raise AssertionError("global parser skipped the mixed Rejected field")
expected = (
    "must be enclosed in backticks",
    "unconsumed contextual Rejected text",
)
for path, diagnostic in zip(sys.argv[2:], expected):
    try:
        module.parse_contextual_decisions(path)
    except ValueError as error:
        assert diagnostic in str(error), str(error)
    else:
        raise AssertionError(f"malformed contextual field accepted: {path}")
PY
assert_status "validate-terms: contextual parser rejects unconsumed fields" \
    0 "$?"

MALFORMED_CONTEXT_SOURCE="$TERMS_ROOT/malformed/i18n/zh/source.txt"
mkdir -p "$(dirname "$MALFORMED_CONTEXT_SOURCE")"
printf '%s\n' \
    '%%%%' 'status|Blood' '血甲' \
    '%%%%' 'ordinary key' '仍有魔窟。' \
    '%%%%' 'global key' '仍有遗留词。' \
    > "$MALFORMED_CONTEXT_SOURCE"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$NO_ARROW_CONTEXT_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
no_arrow_context_status=$?
set -e
assert_status "validate-terms: every no-arrow Context identity fails closed" \
    2 "$no_arrow_context_status"
assert_contains "validate-terms: bare Context identity diagnostic is explicit" \
    "D-D-930: contextual Rejected text matches an exact Context table key" \
    /tmp/actual_validate_terms.txt
assert_contains "validate-terms: mixed Context identity diagnostic is explicit" \
    "D-D-933: contextual Rejected text matches an exact Context table key" \
    /tmp/actual_validate_terms.txt
assert_contains "validate-terms: nonmatching pipe identity fails explicitly" \
    "D-D-941: pipe-qualified Rejected identity must use a backticked arrow" \
    /tmp/actual_validate_terms.txt
assert_contains "validate-terms: historical pipe identity cannot bypass syntax" \
    "D-D-944: pipe-qualified Rejected identity must use a backticked arrow" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$NO_CONTEXT_PIPE_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
no_context_pipe_status=$?
set -e
assert_status "validate-terms: no-Context pipe identities fail closed" \
    2 "$no_context_pipe_status"
assert_contains "validate-terms: no-Context pipe diagnostic is explicit" \
    "D-Z-946: pipe-qualified Rejected identity must use a backticked arrow" \
    /tmp/actual_validate_terms.txt

python3 "$SCAN_I18N" validate-terms \
    --glossary "$NO_CONTEXT_HISTORICAL_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: genuine no-pipe history remains explanation" \
    0 "$?"

python3 "$SCAN_I18N" validate-terms \
    --glossary "$HISTORICAL_NON_CONTEXT_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: nonmatching historical explanation stays narrow" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MISSING_CHOICE_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_choice_status=$?
set -e
assert_status "validate-terms: a global rejection without Choice fails closed" \
    2 "$missing_choice_status"
assert_contains "validate-terms: missing Choice diagnostic is explicit" \
    "global Rejected terms require a non-empty Choice" \
    /tmp/actual_validate_terms.txt

SINGLE_READ_DECISIONS="$TERMS_ROOT/single-read-decisions.md"
printf '%s\n' \
    '### D-Z-940 — single-read CLI fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: 遗留词' \
    > "$SINGLE_READ_DECISIONS"
SINGLE_READ_SOURCE="$TERMS_ROOT/single-read/i18n/zh/source.txt"
mkdir -p "$(dirname "$SINGLE_READ_SOURCE")"
printf '%s\n' '%%%%' 'single-read key' '这里使用正确词。' \
    > "$SINGLE_READ_SOURCE"
python3 - "$SCAN_I18N" "$SINGLE_READ_DECISIONS" \
    "$SINGLE_READ_SOURCE" <<'PY'
import builtins
import importlib.util
import io
import os
import types
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
glossary = os.path.abspath(sys.argv[2])
first_snapshot = """\
### D-Z-940 — first snapshot
- **Status**: active
- **Choice**: 正确词
- **Rejected**: 遗留词
"""
second_snapshot = """\
### D-Z-940 — second snapshot must never be observed
- **Status**: active
- **Rejected**: 遗留词
"""
real_open = builtins.open
reads = []
classifications = []
real_classify = module._classify_decision_rejections
metadata_reads = []
real_metadata = module._decision_metadata_fields

def alternating_open(path, *args, **kwargs):
    if os.path.abspath(os.fspath(path)) == glossary:
        reads.append(path)
        snapshot = first_snapshot if len(reads) == 1 else second_snapshot
        return io.StringIO(snapshot)
    return real_open(path, *args, **kwargs)

def counting_classify(decision_id, block, *args):
    classifications.append((decision_id, block))
    return real_classify(decision_id, block, *args)

def counting_metadata(block):
    metadata_reads.append(block)
    return real_metadata(block)

builtins.open = alternating_open
module._classify_decision_rejections = counting_classify
module._decision_metadata_fields = counting_metadata
try:
    status = module.cmd_validate_terms(types.SimpleNamespace(
        glossary=sys.argv[2],
        source_txt=sys.argv[3],
        zh_dirs=[],
        source_dir=None,
    ))
finally:
    builtins.open = real_open
    module._classify_decision_rejections = real_classify
    module._decision_metadata_fields = real_metadata
assert status == 0, status
assert len(reads) == 1, reads
assert metadata_reads == [first_snapshot], metadata_reads
assert [item[0] for item in classifications] == ["D-Z-940"], classifications
assert classifications[0][1] == first_snapshot, classifications
PY
assert_status "validate-terms: CLI reads and classifies one snapshot once" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$UNBACKTICKED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
unbackticked_context_status=$?
set -e
assert_status "validate-terms: unbackticked contextual mapping fails closed" \
    2 "$unbackticked_context_status"
assert_contains "validate-terms: unbackticked mapping diagnostic is explicit" \
    "contextual Rejected mapping must be enclosed in backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$MIXED_REJECTED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
mixed_rejected_status=$?
set -e
assert_status "validate-terms: mixed contextual/global field fails closed" \
    2 "$mixed_rejected_status"
assert_contains "validate-terms: mixed-field residual is explicit" \
    "unconsumed contextual Rejected text: '魔窟'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$GLOBAL_WITH_EXPLANATION" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
global_with_explanation_status=$?
set -e
assert_status "validate-terms: global survives ordinary arrow explanation" \
    1 "$global_with_explanation_status"
assert_contains "validate-terms: independent global term is still scanned" \
    "Rejected: '遗留词'" /tmp/actual_validate_terms.txt

for fused_arrow_decisions in \
    "$FUSED_PAREN_ARROW_EXPLANATION" \
    "$FUSED_QUOTED_ARROW_EXPLANATION"
do
    python3 - "$SCAN_I18N" "$fused_arrow_decisions" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
assert registry["rejected_map"] == {"遗留词": "正确词"}, registry
assert [
    item["kind"] for item in registry["classifications"]
] == ["global"], registry
PY
    fused_registry_status=$?
    assert_status \
        "validate-terms: fused arrow suffix preserves global registry" \
        0 "$fused_registry_status"

    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$fused_arrow_decisions" \
        --source-txt "$MALFORMED_CONTEXT_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    fused_arrow_status=$?
    set -e
    assert_status \
        "validate-terms: fused arrow suffix cannot hide global term" \
        1 "$fused_arrow_status"
    assert_contains \
        "validate-terms: fused arrow global reaches SourceDB scan" \
        "Rejected: '遗留词'" /tmp/actual_validate_terms.txt
done

for invalid_arrow_residuals in \
    "$MIDDLE_ARROW_BOTH_SIDES" \
    "$FUSED_ARROW_WITH_SUFFIX"
do
    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$invalid_arrow_residuals" \
        --source-txt "$MALFORMED_CONTEXT_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    invalid_arrow_residual_status=$?
    set -e
    assert_status \
        "validate-terms: arrow span cannot hide multiple residuals" \
        2 "$invalid_arrow_residual_status"
    assert_contains \
        "validate-terms: ambiguous arrow residuals fail explicitly" \
        "unconsumed Rejected text around arrow explanation" \
        /tmp/actual_validate_terms.txt
done

for leading_arrow_decisions in \
    "$LEADING_ARROW_GLOBAL" \
    "$MULTI_ARROW_GLOBAL"
do
    python3 - "$SCAN_I18N" "$leading_arrow_decisions" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
assert registry["rejected_map"] == {"遗留词": "正确词"}, registry
assert [
    item["kind"] for item in registry["classifications"]
] == ["global"], registry
PY
    leading_arrow_registry_status=$?
    assert_status \
        "validate-terms: leading arrow spans preserve one global" \
        0 "$leading_arrow_registry_status"

    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$leading_arrow_decisions" \
        --source-txt "$MALFORMED_CONTEXT_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    leading_arrow_status=$?
    set -e
    assert_status \
        "validate-terms: leading arrow spans cannot hide global term" \
        1 "$leading_arrow_status"
    assert_contains \
        "validate-terms: leading-arrow global reaches SourceDB scan" \
        "Rejected: '遗留词'" /tmp/actual_validate_terms.txt
done

python3 - "$SCAN_I18N" "$PURE_ARROW_EXPLANATIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
registry = module.parse_decision_registry(sys.argv[2])
assert registry["rejected_map"] == {}, registry
assert [
    item["kind"] for item in registry["classifications"]
] == ["explanation", "explanation", "explanation"], registry
PY
assert_status \
    "validate-terms: fully delimited historical arrows remain explanations" \
    0 "$?"

python3 "$SCAN_I18N" validate-terms \
    --glossary "$CONTEXT_WITH_EXPLANATION" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: contextual rule allows historical explanation" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_QUOTED_UNQUALIFIED" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_quoted_unqualified_status=$?
set -e
assert_status "validate-terms: table-bound quoted arrow needs marker" \
    2 "$table_quoted_unqualified_status"
assert_contains "validate-terms: quoted arrow cannot bypass table binding" \
    "matches an exact Context table key and must be enclosed in backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_MARKED_MATCHING_ARROW" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_marked_matching_status=$?
set -e
assert_status "validate-terms: marker cannot exempt matching Context key" \
    2 "$table_marked_matching_status"
assert_contains "validate-terms: matching historical arrow still needs code" \
    "matches an exact Context table key and must be enclosed in backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CONTEXT_BOUNDARY_PUNCTUATION" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_context_boundary_punctuation.txt 2>&1
context_boundary_punctuation_status=$?
set -e
assert_status "validate-terms: punctuation-delimited Context arrows fail closed" \
    2 "$context_boundary_punctuation_status"
for context_boundary_decision in "${CONTEXT_BOUNDARY_DECISION_IDS[@]}"; do
    assert_contains \
        "validate-terms: $context_boundary_decision needs a backticked arrow" \
        "$context_boundary_decision: contextual Rejected arrow matches an exact Context table key and must be enclosed in backticks" \
        /tmp/actual_context_boundary_punctuation.txt
done
if grep -Fq -- "OK: No active rejected-name decisions found" \
    /tmp/actual_context_boundary_punctuation.txt; then
    echo "  FAIL: punctuation-delimited Context arrows produced an empty-registry success"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: punctuation-delimited Context arrows cannot produce an empty-registry success"
    PASS=$((PASS + 1))
fi

python3 - "$SCAN_I18N" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
context_values = {
    module.compute_canonical_key("EXACT KEY"): {
        "key": "EXACT KEY",
        "value": "正确词",
    },
}
for prefix in ("A", "7", "_", "|"):
    assert not module._is_context_identity_boundary(prefix), prefix
    for token in (
        f'"历史说明{prefix}EXACT KEY → 遗留词"',
        f"（历史说明{prefix}EXACT KEY → 遗留词）",
    ):
        assert not module._outside_arrow_matches_context(
            token, context_values
        ), token
        assert not module._text_mentions_context_identity(
            token, context_values
        ), token
PY
assert_status \
    "validate-terms: identity substrings keep alnum/underscore/pipe controls" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$QUOTED_QUALIFIED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
quoted_qualified_status=$?
set -e
assert_status "validate-terms: quoted qualified mapping fails closed" \
    2 "$quoted_qualified_status"
assert_contains "validate-terms: quoted qualified diagnostic is explicit" \
    "pipe-qualified contextual mapping must use backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PAREN_QUALIFIED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
paren_qualified_status=$?
set -e
assert_status "validate-terms: parenthesized qualified mapping fails closed" \
    2 "$paren_qualified_status"
assert_contains "validate-terms: parentheses cannot exempt qualified mapping" \
    "pipe-qualified contextual mapping must use backticks" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$QUALIFIED_NO_TABLE_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
qualified_no_table_status=$?
set -e
assert_status "validate-terms: qualified mapping requires Context table" \
    2 "$qualified_no_table_status"
assert_contains "validate-terms: missing exact Context table is explicit" \
    "does not match an exact non-empty Context table key" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PREFIXED_ORDINARY_ARROW_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
prefixed_ordinary_arrow_status=$?
set -e
assert_status "validate-terms: ordinary arrow cannot hide global prefix" \
    2 "$prefixed_ordinary_arrow_status"
assert_contains "validate-terms: ordinary arrow prefix is unconsumed" \
    "unconsumed Rejected token prefix: '遗留词'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PAREN_PREFIXED_ORDINARY_ARROW" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
paren_prefixed_arrow_status=$?
set -e
assert_status "validate-terms: parenthesis cannot exempt arrow prefix" \
    2 "$paren_prefixed_arrow_status"
assert_contains "validate-terms: parenthetical prefix bypass is explicit" \
    "unconsumed Rejected token prefix: '遗留词'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$PAREN_SUFFIXED_ORDINARY_ARROW" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
paren_suffixed_arrow_status=$?
set -e
assert_status "validate-terms: parenthesis cannot absorb arrow suffix" \
    2 "$paren_suffixed_arrow_status"
assert_contains "validate-terms: parenthetical suffix bypass is explicit" \
    "unconsumed Rejected token suffix: '遗留词（历史说明）'" \
    /tmp/actual_validate_terms.txt

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$UNBALANCED_DECISIONS" \
    --source-txt "$MALFORMED_CONTEXT_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
unbalanced_status=$?
set -e
assert_status "validate-terms: unbalanced token delimiters fail closed" \
    2 "$unbalanced_status"
assert_contains "validate-terms: unclosed code span is explicit" \
    "D-Z-923: unbalanced delimiters" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: unclosed quote is explicit" \
    "D-Z-924: unbalanced delimiters" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: unclosed parenthesis is explicit" \
    "D-Z-925: unbalanced delimiters" /tmp/actual_validate_terms.txt

WHITESPACE_DECISIONS="$TERMS_ROOT/whitespace-decisions.md"
printf '%s\n' \
    '### D-A-046 — SourceDB whitespace identity fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| ` the pandemonium lord` | 万魔殿领主 |' \
    '| `One of the many lords of Pandemonium, ` | 万魔殿领主 |' \
    '- **Rejected**:' \
    '  - ` THE PANDEMONIUM LORD → 潘德莫尼姆`' \
    '  - `ONE OF THE MANY LORDS OF PANDEMONIUM,  → 潘神之域`' \
    > "$WHITESPACE_DECISIONS"
python3 - "$SCAN_I18N" "$WHITESPACE_DECISIONS" <<'PY'
import importlib.util
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rules = module.parse_contextual_decisions(sys.argv[2])
assert [rule["key"] for rule in rules] == [
    " the pandemonium lord",
    "One of the many lords of Pandemonium, ",
]
PY
assert_status "validate-terms: canonical binding preserves key whitespace" \
    0 "$?"

WHITESPACE_SOURCE="$TERMS_ROOT/whitespace/i18n/zh/source.txt"
mkdir -p "$(dirname "$WHITESPACE_SOURCE")"
printf '%s\n' \
    '%%%%' ' THE PANDEMONIUM LORD' '万魔殿领主' \
    '%%%%' 'ONE OF THE MANY LORDS OF PANDEMONIUM, ' '万魔殿领主' \
    > "$WHITESPACE_SOURCE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$WHITESPACE_DECISIONS" \
    --source-txt "$WHITESPACE_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: whitespace identities use production lowercase" \
    0 "$?"

printf '%s\n' \
    '%%%%' 'THE PANDEMONIUM LORD' '万魔殿领主' \
    '%%%%' 'ONE OF THE MANY LORDS OF PANDEMONIUM,' '万魔殿领主' \
    > "$WHITESPACE_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$WHITESPACE_DECISIONS" \
    --source-txt "$WHITESPACE_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
stripped_whitespace_status=$?
set -e
assert_status "validate-terms: stripped SourceDB whitespace fails closed" \
    2 "$stripped_whitespace_status"
assert_contains "validate-terms: stripped whitespace key is missing" \
    "is missing from the effective SourceDB" /tmp/actual_validate_terms.txt

TABLE_DUPLICATE_DECISIONS="$TERMS_ROOT/table-duplicate-decisions.md"
printf '%s\n' \
    '### D-D-005 — canonical duplicate Context rows fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '| `STATUS\|BLOOD` | 血甲 |' \
    '- **Rejected**: `status|blood → 嗜血`' \
    > "$TABLE_DUPLICATE_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_DUPLICATE_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_duplicate_status=$?
set -e
assert_status "validate-terms: canonical duplicate Context rows fail closed" \
    2 "$table_duplicate_status"
assert_contains "validate-terms: canonical table duplicate is explicit" \
    "duplicate Context table rows for normalized key 'status|blood'" \
    /tmp/actual_validate_terms.txt

TABLE_CONFLICT_DECISIONS="$TERMS_ROOT/table-conflict-decisions.md"
printf '%s\n' \
    '### D-D-005 — canonical conflicting Context rows fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '| `STATUS\|BLOOD` | 鲜血 |' \
    '- **Rejected**: `status|blood → 嗜血`' \
    > "$TABLE_CONFLICT_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$TABLE_CONFLICT_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
table_conflict_status=$?
set -e
assert_status "validate-terms: canonical conflicting Context rows fail closed" \
    2 "$table_conflict_status"
assert_contains "validate-terms: canonical table conflict is explicit" \
    "conflicting Context table rows for normalized key 'status|blood'" \
    /tmp/actual_validate_terms.txt

ORDINARY_ARROW_DECISIONS="$TERMS_ROOT/ordinary-arrow-decisions.md"
printf '%s\n' \
    '### D-B-015 — ordinary backticked arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 恶魔' \
    '- **Rejected**: `demon→魔`（普通术语说明，不是 SourceDB key）' \
    '### D-A-016 — ordinary explanatory arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 幼龙' \
    '- **Rejected**: 小龙（历史说明："Summon Drakes → 召唤小龙"）' \
    '### D-Z-927 — ordinary quoted arrow fixture' \
    '- **Status**: active' \
    '- **Choice**: 正确词' \
    '- **Rejected**: "legacy → 旧译"' \
    > "$ORDINARY_ARROW_DECISIONS"
printf '%s\n' '%%%%' 'ordinary key' '普通语境中的魔合法。' \
    > "$CANONICAL_SOURCE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$ORDINARY_ARROW_DECISIONS" \
    --source-txt "$CANONICAL_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: no-table ordinary arrow remains allowed" 0 "$?"

TERMS_SOURCE="$TERMS_ROOT/i18n/zh/source.txt"
TERMS_DESCRIPT="$TERMS_ROOT/descript/zh/fixture.txt"
TERMS_DATABASE="$TERMS_ROOT/database/zh/fixture.txt"
mkdir -p "$(dirname "$TERMS_SOURCE")" \
    "$(dirname "$TERMS_DESCRIPT")" "$(dirname "$TERMS_DATABASE")"

for rejected in 魔窟 弹飞弹 弹开飞弹 埃瑞博拉 宗古多克 宗古尔德罗克; do
    printf '%s\n' \
        '%%%%' 'fixture key' "包含${rejected}的残留。" \
        '%%%%' 'status|Blood' '血甲' \
        > "$TERMS_SOURCE"
    set +e
    python3 "$SCAN_I18N" validate-terms \
        --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
        > /tmp/actual_validate_terms.txt 2>&1
    terms_status=$?
    set -e
    assert_status "validate-terms: rejects global legacy term $rejected" \
        1 "$terms_status"
done

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '嗜血' > "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
context_status=$?
set -e
assert_status "validate-terms: rejects exact defensive status Blood mapping" \
    1 "$context_status"

printf '%s\n%s\n%s\n' '%%%%' 'STATUS|BLOOD' '前缀嗜血后缀' \
    > "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
case_substring_status=$?
set -e
assert_status "validate-terms: production lowercase and substring match" \
    1 "$case_substring_status"

printf '%s\n' \
    '%%%%' 'status|Blood' '血甲' \
    '%%%%' 'other|Blood' '前缀嗜血后缀' \
    > "$TERMS_SOURCE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: non-matching contextual scope is legal" 0 "$?"

printf '%s\n%s\n%s\n' '%%%%' 'STATUS|BLOOD' '源文件含嗜血' \
    > "$TERMS_SOURCE"
TERMS_OVERRIDE="$TERMS_ROOT/i18n/zh/a-override.txt"
printf '%s\n%s\n%s\n' '%%%%' 'status|blood' '血甲' > "$TERMS_OVERRIDE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: source.txt loads before sorted override files" \
    0 "$?"

TERMS_LAST="$TERMS_ROOT/i18n/zh/z-last.txt"
printf '%s\n%s\n%s\n' '%%%%' 'Status|Blood' '最后定义仍有嗜血' \
    > "$TERMS_LAST"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
last_definition_status=$?
set -e
assert_status "validate-terms: final sorted definition wins" \
    1 "$last_definition_status"
rm -f "$TERMS_LAST"

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '血甲' > "$TERMS_SOURCE"
TERMS_NODOT_EARLY="$TERMS_ROOT/i18n/zh/b-overridetxt"
TERMS_NODOT_LAST="$TERMS_ROOT/i18n/zh/z-overridetxt"
printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '早期嗜血覆盖' \
    > "$TERMS_NODOT_EARLY"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
nodot_early_status=$?
set -e
assert_status "validate-terms: production *txt suffix files are discovered" \
    1 "$nodot_early_status"
assert_contains "validate-terms: no-dot override reports its source file" \
    "b-overridetxt" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: no-dot override reports rejected term" \
    "Rejected: '嗜血'" /tmp/actual_validate_terms.txt

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '血甲' \
    > "$TERMS_NODOT_LAST"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: sorted no-dot last definition wins" 0 "$?"

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '后期嗜血覆盖' \
    > "$TERMS_NODOT_LAST"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
nodot_last_status=$?
set -e
assert_status "validate-terms: rejected no-dot last definition blocks" \
    1 "$nodot_last_status"
assert_contains "validate-terms: effective no-dot file is deterministic" \
    "z-overridetxt" /tmp/actual_validate_terms.txt
assert_contains "validate-terms: effective no-dot term is reported" \
    "Rejected: '嗜血'" /tmp/actual_validate_terms.txt
rm -f "$TERMS_NODOT_EARLY" "$TERMS_NODOT_LAST"

rm -f "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_source_status=$?
set -e
assert_status "validate-terms: missing source.txt fails closed" \
    2 "$missing_source_status"
assert_contains "validate-terms: missing source.txt diagnostic is explicit" \
    "required SourceDB source.txt does not exist" \
    /tmp/actual_validate_terms.txt
printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '血甲' > "$TERMS_SOURCE"

TERMS_INVALID="$TERMS_ROOT/i18n/zh/z-invalid.txt"
printf '%s\n%s\n' '%%%%' 'invalid UTF-8 fixture' > "$TERMS_INVALID"
printf '\377\n' >> "$TERMS_INVALID"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
invalid_sourcedb_status=$?
set -e
assert_status "validate-terms: invalid UTF-8 SourceDB file fails closed" \
    2 "$invalid_sourcedb_status"
assert_contains "validate-terms: invalid SourceDB diagnostic is explicit" \
    "cannot parse required TextDB file" /tmp/actual_validate_terms.txt
rm -f "$TERMS_INVALID"

rm -f "$TERMS_OVERRIDE"
printf '%s\n%s\n%s\n' '%%%%' 'other|Blood' '血甲' > "$TERMS_SOURCE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_context_status=$?
set -e
assert_status "validate-terms: missing contextual SourceDB key fails closed" \
    2 "$missing_context_status"
assert_contains "validate-terms: missing contextual key diagnostic is explicit" \
    "is missing from the effective SourceDB" /tmp/actual_validate_terms.txt
printf '%s\n%s\n%s\n' '%%%%' 'status|blood' '血甲' > "$TERMS_OVERRIDE"

INVALID_DECISIONS="$TERMS_ROOT/invalid-decisions.md"
printf '%s\n' \
    '### D-Q-910 — invalid contextual fixture' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|\|Blood` | 血甲 |' \
    '- **Rejected**: `status||Blood → 嗜血`' \
    > "$INVALID_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$INVALID_DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
invalid_context_status=$?
set -e
assert_status "validate-terms: invalid contextual rule fails closed" \
    2 "$invalid_context_status"
assert_contains "validate-terms: invalid contextual rule diagnostic is explicit" \
    "invalid contextual Rejected mapping" /tmp/actual_validate_terms.txt

DUPLICATE_DECISIONS="$TERMS_ROOT/duplicate-decisions.md"
printf '%s\n' \
    '### D-Q-911 — duplicate contextual fixture one' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`' \
    '### D-Q-912 — duplicate contextual fixture two' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `STATUS\|BLOOD` | 血甲 |' \
    '- **Rejected**: `STATUS|BLOOD → 嗜血`' \
    > "$DUPLICATE_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DUPLICATE_DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
duplicate_context_status=$?
set -e
assert_status "validate-terms: duplicate normalized contextual rule fails closed" \
    2 "$duplicate_context_status"
assert_contains "validate-terms: duplicate contextual diagnostic is explicit" \
    "duplicate contextual rules for normalized key" \
    /tmp/actual_validate_terms.txt

CONFLICT_DECISIONS="$TERMS_ROOT/conflict-decisions.md"
printf '%s\n' \
    '### D-Q-913 — conflicting contextual fixture one' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `status\|Blood` | 血甲 |' \
    '- **Rejected**: `status|Blood → 嗜血`' \
    '### D-Q-914 — conflicting contextual fixture two' \
    '- **Status**: active' \
    '| Context | ZH |' \
    '|---------|----|' \
    '| `STATUS\|BLOOD` | 鲜血 |' \
    '- **Rejected**: `STATUS|BLOOD → 血欲`' \
    > "$CONFLICT_DECISIONS"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$CONFLICT_DECISIONS" --source-txt "$TERMS_SOURCE" \
    > /tmp/actual_validate_terms.txt 2>&1
conflict_context_status=$?
set -e
assert_status "validate-terms: conflicting normalized contextual rule fails closed" \
    2 "$conflict_context_status"
assert_contains "validate-terms: conflicting contextual diagnostic is explicit" \
    "conflicting contextual rules for normalized key" \
    /tmp/actual_validate_terms.txt

printf '%s\n' \
    '%%%%' 'status|Blood' '血甲' \
    '%%%%' 'bloodlust flavour' '嗜血' \
    > "$TERMS_SOURCE"
printf '%s\n%s\n%s\n' '%%%%' 'descript fixture' '残留魔窟。' \
    > "$TERMS_DESCRIPT"
printf '%s\n%s\n%s\n' '%%%%' 'database fixture' '合法文本。' \
    > "$TERMS_DATABASE"
python3 - "$SCAN_I18N" "$TERMS_SOURCE" \
    "$TERMS_ROOT/i18n/zh" "$TERMS_ROOT/descript/zh" \
    "$TERMS_ROOT/database/zh" <<'PY'
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location("scan_i18n", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
files, errors, sourcedb = module._collect_zh_textdb_files(
    sys.argv[2], sys.argv[3:]
)
assert not errors
assert len(files) == 4
assert files.count(os.path.abspath(sys.argv[2])) == 1
assert sourcedb == [
    os.path.abspath(sys.argv[2]),
    os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])),
                 "a-override.txt"),
]
PY
assert_status "validate-terms: source.txt is deduplicated across explicit roots" \
    0 "$?"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
descript_status=$?
set -e
assert_status "validate-terms: rejects descript/zh legacy term" \
    1 "$descript_status"
assert_contains "validate-terms: reports descript/zh source file" \
    "$TERMS_DESCRIPT" /tmp/actual_validate_terms.txt

printf '%s\n%s\n%s\n' '%%%%' 'status|Blood' '嗜血' > "$TERMS_DESCRIPT"
printf '%s\n%s\n%s\n' '%%%%' 'database fixture' '残留宗古多克。' \
    > "$TERMS_DATABASE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
database_status=$?
set -e
assert_status "validate-terms: rejects database/zh legacy term" \
    1 "$database_status"
assert_contains "validate-terms: reports database/zh source file" \
    "$TERMS_DATABASE" /tmp/actual_validate_terms.txt

printf '%s\n%s\n%s\n' '%%%%' 'database fixture' '合法文本。' \
    > "$TERMS_DATABASE"
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
assert_status "validate-terms: exact context stays SourceDB-only and bloodlust is legal" \
    0 "$?"

set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/missing" \
    > /tmp/actual_validate_terms.txt 2>&1
missing_zh_dir_status=$?
set -e
assert_status "validate-terms: missing required ZH directory fails closed" \
    2 "$missing_zh_dir_status"

printf '%s\n%s\n' '%%%%' 'invalid UTF-8 fixture' > "$TERMS_DATABASE"
printf '\377\n' >> "$TERMS_DATABASE"
set +e
python3 "$SCAN_I18N" validate-terms \
    --glossary "$DECISIONS" --source-txt "$TERMS_SOURCE" \
    --zh-dir "$TERMS_ROOT/i18n/zh" \
    --zh-dir "$TERMS_ROOT/descript/zh" \
    --zh-dir "$TERMS_ROOT/database/zh" \
    > /tmp/actual_validate_terms.txt 2>&1
unreadable_zh_status=$?
set -e
assert_status "validate-terms: unreadable ZH TextDB fails closed" \
    2 "$unreadable_zh_status"
assert_contains "validate-terms: unreadable TextDB diagnostic is explicit" \
    "cannot parse required TextDB file" /tmp/actual_validate_terms.txt
rm -f /tmp/actual_validate_terms.txt
rm -rf "$TERMS_ROOT"

# ── check-gaps ──
echo "--- check-gaps ---"
python3 "$SCAN_I18N" check-gaps --source-txt "$FIXTURES/arg-mismatch/gap_source.txt" > /tmp/actual_gaps.txt 2>&1 || true
assert_output "check-gaps: finds positional gaps" \
    /tmp/actual_gaps.txt "$EXPECTED/check-gaps.txt"

# ── source-control-parity ──
echo "--- source-control-parity ---"
python3 "$SCRIPT_DIR/../source_control_parity.py" --source-txt "$FIXTURES/source-control-parity/source.txt" > /tmp/actual_scp.txt 2>&1 || true
assert_output "source-control-parity: detects missing \\n and \\t" \
    /tmp/actual_scp.txt "$EXPECTED/source-control-parity.txt"

# ── source-control-parity --semantic ──
echo "--- source-control-parity --semantic ---"
python3 "$SCRIPT_DIR/../source_control_parity.py" --source-txt "$FIXTURES/source-control-parity/source.txt" --semantic > /tmp/actual_scp_sem.txt 2>&1 || true
assert_output "source-control-parity: detects sequence order mismatch" \
    /tmp/actual_scp_sem.txt "$EXPECTED/source-control-parity-semantic.txt"

# ── lang-args ──
echo "--- lang-args ---"
python3 "$SCAN_I18N" lang-args "$FIXTURES/lang-args/" > /tmp/actual_lang.txt 2>&1 || true
assert_output "lang-args: finds language-dependent args" \
    /tmp/actual_lang.txt "$EXPECTED/lang-args.txt"

# ── varargs-string (Issue #42 UB) ──
echo "--- varargs-string ---"
set +e
python3 "$SCRIPT_DIR/test_scanner_completeness.py" \
    > /tmp/actual_scanner_completeness.txt 2>&1
scanner_completeness_status=$?
set -e
assert_status "scanner completeness: cross-scanner unit suite" 0 \
    "$scanner_completeness_status"
set +e
python3 "$SCRIPT_DIR/../scan_varargs_string.py" "$FIXTURES/varargs-string/" --include-warn > /tmp/actual_varargs.txt 2>&1
varargs_status=$?
set -e
assert_status "varargs-string: HIGH findings return blocking status" 1 "$varargs_status"
assert_output "varargs-string: maps ordinary/positional %s slots and ignores non-string slots" \
    /tmp/actual_varargs.txt "$EXPECTED/varargs-string.txt"

# ── persistent i18n lifetime ──
echo "--- i18n-lifetime ---"
set +e
python3 "$SCRIPT_DIR/test_scan_i18n_lifetime.py" \
    > /tmp/actual_i18n_lifetime.txt 2>&1
i18n_lifetime_status=$?
set -e
cat /tmp/actual_i18n_lifetime.txt
assert_status "i18n-lifetime: black-box unit suite" 0 "$i18n_lifetime_status"
assert_contains "source-db dedup: post-coder standalone coverage is conditional" \
    'ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE' \
    "$SCRIPT_DIR/../post-coder.sh"
assert_contains "source-db dedup: dispatcher marks nested domain scripts" \
    'env ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE=1' \
    "$SCRIPT_DIR/../verify_zh.sh"
assert_contains "i18n-lifetime: ci code-static runs the lifetime scanner" \
    'scan_i18n_lifetime.py' \
    "$SCRIPT_DIR/../post-coder.sh"
if grep -Fq -- '--profile review' "$SCRIPT_DIR/../verify_zh.sh"; then
    echo "  FAIL: verify_zh.sh must not accept the retired review profile"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: verify_zh.sh is free of the retired review profile"
    PASS=$((PASS + 1))
fi

# ── post-translator production wiring ──
# Execute the real aggregator with command shims. This verifies the complete
# argv seen at the production boundary and that each restored blocking check
# propagates a non-zero status through post-translator.sh.
POST_TRANSLATOR="$SCRIPT_DIR/../post-translator.sh"
POST_TRANSLATOR_HARNESS=$(mktemp -d)
POST_TRANSLATOR_CALL_LOG="$POST_TRANSLATOR_HARNESS/calls.txt"
POST_TRANSLATOR_OUTPUT="$POST_TRANSLATOR_HARNESS/output.txt"
mkdir -p "$POST_TRANSLATOR_HARNESS/bin"
printf '%s\n' \
    '#!/bin/bash' \
    'printf '\''%s\n'\'' "$*" >> "$POST_TRANSLATOR_CALL_LOG"' \
    'if [[ -n "${POST_TRANSLATOR_FAIL_MATCH:-}" && "$*" == *"$POST_TRANSLATOR_FAIL_MATCH"* ]]; then' \
    '    exit 17' \
    'fi' \
    'exit 0' \
    > "$POST_TRANSLATOR_HARNESS/bin/python3"
cp "$POST_TRANSLATOR_HARNESS/bin/python3" \
    "$POST_TRANSLATOR_HARNESS/bin/bash"
chmod +x "$POST_TRANSLATOR_HARNESS/bin/python3" \
    "$POST_TRANSLATOR_HARNESS/bin/bash"

set +e
(
    cd "$POST_TRANSLATOR_HARNESS"
    PATH="$POST_TRANSLATOR_HARNESS/bin:$PATH" \
        POST_TRANSLATOR_CALL_LOG="$POST_TRANSLATOR_CALL_LOG" \
        /bin/bash "$POST_TRANSLATOR"
) > "$POST_TRANSLATOR_OUTPUT" 2>&1
post_translator_wiring_status=$?
set -e
assert_status "post-translator: restored checks execute through production aggregator" \
    0 "$post_translator_wiring_status"
assert_contains "post-translator: validate-terms scans every production ZH root" \
    'scan_i18n.py validate-terms --glossary docs/decisions.md --source-txt crawl-ref/source/dat/i18n/zh/source.txt --zh-dir crawl-ref/source/dat/i18n/zh --zh-dir crawl-ref/source/dat/descript/zh --zh-dir crawl-ref/source/dat/database/zh' \
    "$POST_TRANSLATOR_CALL_LOG"
assert_contains "post-translator: cross-file scanner is restored" \
    'cross_file_terms.py crawl-ref/source/dat/i18n/zh/ --glossary docs/decisions.md' \
    "$POST_TRANSLATOR_CALL_LOG"
assert_contains "post-translator: consistency superset is restored once" \
    'check_consistency.sh --all --strict' "$POST_TRANSLATOR_CALL_LOG"
if grep -Eq -- 'check_consistency\.sh --(format|database|items) --strict' \
    "$POST_TRANSLATOR_CALL_LOG"; then
    echo "  FAIL: post-translator duplicates checks already covered by --all"
    FAIL=$((FAIL + 1))
else
    echo "  PASS: post-translator does not duplicate --all consistency modes"
    PASS=$((PASS + 1))
fi

for restored_check in \
    'scan_i18n.py validate-terms' \
    'cross_file_terms.py' \
    'check_consistency.sh --all --strict'
do
    : > "$POST_TRANSLATOR_CALL_LOG"
    set +e
    (
        cd "$POST_TRANSLATOR_HARNESS"
        PATH="$POST_TRANSLATOR_HARNESS/bin:$PATH" \
            POST_TRANSLATOR_CALL_LOG="$POST_TRANSLATOR_CALL_LOG" \
            POST_TRANSLATOR_FAIL_MATCH="$restored_check" \
            /bin/bash "$POST_TRANSLATOR"
    ) > "$POST_TRANSLATOR_OUTPUT" 2>&1
    post_translator_negative_status=$?
    set -e
    assert_status "post-translator: $restored_check failure blocks" \
        1 "$post_translator_negative_status"
done
rm -rf "$POST_TRANSLATOR_HARNESS"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
