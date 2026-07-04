// Test fixture: basic compound assignment (+=) patterns
#include <string>

void test_compound_assign() {
    std::string desc;
    std::string debug;
    std::string path;

    // BARE — should be reported
    desc += " (if damage dealt)";
    desc += "text" + some_var + "more text";
    desc += "HP";

    // WRAPPED — should be skipped by default
    desc += T_("open ");
    desc += T_("close");

    // LOW risk — debug var, no prose
    debug += "some debug info";

    // Excluded — file path
    path += "/path/to/file.txt";

    // Excluded — no alpha
    desc += ", ";
    desc += "\n";

    // Excluded — single char (LOW risk, still reported without --skip-low)
    desc += "a";

    // Multi-line
    desc +=
        " (if damage dealt)";
}
