#include "positional_format.h"
#include <cstdio>
#include <cstring>
#include <cassert>

int failures = 0;
void test(const char *name, const char *expected, const char *fmt, ...) {
    va_list args;
    va_start(args, fmt);
    std::string result = vmake_stringf_p(fmt, args);
    va_end(args);
    if (result == expected) {
        printf("  PASS: %s\n", name);
    } else {
        printf("  FAIL: %s\n", name);
        printf("    expected: [%s]\n", expected);
        printf("    got:      [%s]\n", result.c_str());
        failures++;
    }
}

int main() {
    printf("=== Basic positional ===\n");
    test("reorder %2$s %1$d", "hello 42", "%2$s %1$d", 42, "hello");
    test("throw.cc pattern", "你在困惑时无法用你的弓射击。",
         "你在%2$s时无法用你的%1$s射击。", "弓", "困惑");
    test("3-str reorder", "C A B", "%3$s %1$s %2$s", "A", "B", "C");

    printf("\n=== Same arg referenced multiple times ===\n");
    test("same arg twice", "你 喝下药水，你 感觉好多了",
         "%1$s 喝下药水，%1$s 感觉好多了", "你");

    printf("\n=== Mixed types ===\n");
    test("int+double+llong", "火球 造成了 12.5 点伤害（9000 总计）",
         "%1$s 造成了 %2$.1f 点伤害（%3$lld 总计）", "火球", 12.5, 9000LL);

    printf("\n=== Non-positional fast path ===\n");
    test("plain %%s %%d", "Tom loves 3 apples", "%s loves %d apples", "Tom", 3);

    printf("\n=== Empty/literal ===\n");
    test("empty fmt", "", "");
    test("literal only", "hello world", "hello world");

    printf("\n=== Null string arg ===\n");
    test("null string", "(null)", "%1$s", (const char*)nullptr);

    printf("\n=== Flags, width, precision ===\n");
    test("zero-pad", "000042", "%1$06d", 42);
    test("left-align", "hello     ", "%1$-10s", "hello");
    test("precision", "3.14", "%1$.2f", 3.14159);

    printf("\n=== Double %% escape ===\n");
    test("percent", "100% sure", "100%% sure");

    printf("\n=== Long long types ===\n");
    test("min llong", "-9223372036854775808", "%1$lld",
         -9223372036854775807LL - 1);
    test("max ullong", "18446744073709551615", "%1$llu",
         18446744073709551615ULL);

    printf("\n=== DCSS combat pattern ===\n");
    test("combat reorder", "你 用水晶矛 击中了 狗头人。",
         "你 用%2$s 击中了 %1$s。", "狗头人", "水晶矛");

    printf("\n=== Unsigned int ===\n");
    test("uint", "42 255", "%1$u %2$x", 42U, 255U);

    printf("\n--- %d failures ---\n", failures);
    return failures;
}
