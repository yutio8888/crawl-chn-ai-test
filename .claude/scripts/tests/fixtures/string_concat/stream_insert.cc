// Test fixture: stream insertion (<<) patterns
#include <sstream>

void test_stream_insert() {
    std::ostringstream text;
    std::ostringstream debug_out;

    // BARE — should be reported
    text << "Looks like " << god_name << "!";
    text << "hello";
    text << "This ability costs: ";

    // WRAPPED — should be skipped by default
    text << T_("hello");
    text << T_("You hit ") << name << T_("!");

    // Excluded — no alpha
    text << "!";
    text << ", ";

    // LOW risk — debug stream
    debug_out << "debug: " << value;
}

void test_stream_chained() {
    std::ostringstream text;
    text << "You hit " << monster << " with " << weapon;
    text << "The " << item_name << " glows " << colour << ".";
}
