#!/usr/bin/env python3
"""Run production display methods against a deliberately distinct test catalog."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_god_inventory import exact_function_body, _matching_brace, _strip_cpp_comments

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "crawl-ref/source"


class TrunkDisplayTests(unittest.TestCase):
    def test_form_and_curse_display_boundaries_in_both_languages(self):
        transform = _strip_cpp_comments((SRC / "transform.cc").read_text())
        methods = []
        for signature in ("string Form::get_short_name() const",
                          "string Form::get_uc_attack_name(string default_name) const",
                          "string Form::get_description(bool past_tense) const",
                          "string Form::player_prayer_action() const"):
            start = transform.index("{", transform.index(signature))
            body = transform[start + 1:_matching_brace(transform, start)]
            methods.append(signature + " {" + body + "}")
        ability = exact_function_body((SRC / "ability.cc").read_text(),
                                      r"static string _curse_desc")
        item = exact_function_body((SRC / "describe.cc").read_text(),
                                   r"static string _describe_item_curse")
        source = r'''
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <sstream>
#include <string>
#include <vector>
using namespace std;
bool zh = false;
const char *T_(const char *key) {
    if (!zh) return key;
    const string k(key);
    if (k == ".") return "。";
    if (k == "Jade") return "玉";
    if (k == "ATTACK") return "UC_TRANSLATED";
    if (k == "PRAY") return "PRAYER_TRANSLATED";
    if (k == "You are %s") return "PRESENT_%s";
    if (k == "You were %s") return "PAST_%s";
    if (k == "DESCRIPTION") return "FORM_TRANSLATED";
    return key;
}
const char *C_(const char *context, const char *key) {
    if (zh && string(context) == "status" && string(key) == "Jade") return "玉晶";
    return T_(key);
}
string make_stringf(const char *format, ...) {
    char buffer[2048]; va_list args; va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args); va_end(args); return buffer;
}
const int FC_ENABLE = 1;
struct Form {
    string short_name = "Jade", uc_attack = "ATTACK", prayer_action = "PRAY";
    int can_fly = 0;
    int get_uc_brand() const { return 0; }
    string get_transform_description() const { return "DESCRIPTION"; }
    string get_short_name() const;
    string get_uc_attack_name(string) const;
    string get_description(bool) const;
    string player_prayer_action() const;
};
string _brand_suffix(int) { return " BRAND"; }
using CrawlVector = vector<int>;
struct Value { CrawlVector values = {1}; const CrawlVector &get_vector() const { return values; } };
struct Props {
    Value value;
    bool exists(const char *) const { return true; }
    const Value &operator[](const char *) const { return value; }
};
struct Player { Props props; int species = 0; bool airborne() const { return false; } } you;
struct item_def { Props props; };
const char *CURSE_KNOWLEDGE_KEY = "curse_knowledge";
string desc_curse_skills(const CrawlVector &) { return "SKILL_%s"; }
namespace species { string prayer_action(int) { return "DEFAULT_PRAYER"; } }
''' + "\n".join(methods) + "\nstring ability_curse() {" + ability + "}\nstring item_curse(const item_def &item) {" + item + r'''}
int main() {
    Form form;
    const item_def item;
    for (bool language : {false, true}) {
        zh = language;
        assert(form.get_short_name() == (zh ? "玉晶" : "Jade"));
        assert(form.short_name == "Jade");
        assert(form.get_uc_attack_name("DEFAULT") == (zh ? "UC_TRANSLATED BRAND" : "ATTACK BRAND"));
        assert(form.get_description(false) == (zh ? "PRESENT_FORM_TRANSLATED" : "You are DESCRIPTION"));
        assert(form.get_description(true) == (zh ? "PAST_FORM_TRANSLATED" : "You were DESCRIPTION"));
        for (int flight : {0, FC_ENABLE}) {
            form.can_fly = flight;
            assert(form.player_prayer_action() == (zh ? "PRAYER_TRANSLATED" : "PRAY"));
        }
        assert(ability_curse() == string("\nIf you bind an item with this ritual Ashenzari will enhance the following skills:\nSKILL_%s") + (zh ? "。" : "."));
        assert(item_curse(item) == string("\nIt bears a divine curse which improves your skill at SKILL_%s") + (zh ? "。" : "."));
    }
    form.uc_attack.clear();
    assert(form.get_uc_attack_name("DEFAULT_TRANSLATED") == "DEFAULT_TRANSLATED BRAND");
}
'''
        compiler = shutil.which("c++")
        self.assertIsNotNone(compiler)
        with tempfile.TemporaryDirectory(prefix="trunk-display-") as tmp:
            path = Path(tmp)
            (path / "test.cc").write_text(source)
            build = subprocess.run([compiler, "-std=c++11", "-Wall", "-Wextra", "-Werror",
                                    str(path / "test.cc"), "-o", str(path / "test")],
                                   capture_output=True, text=True, timeout=30)
            self.assertEqual(0, build.returncode, build.stdout + build.stderr)
            run = subprocess.run([str(path / "test")], capture_output=True, text=True, timeout=10)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)

    def test_chardump_and_existing_tag_title_consumers(self):
        dump = (SRC / "chardump.cc").read_text()
        self.assertNotIn("->short_name", dump)
        self.assertEqual(2, dump.count("->get_short_name()"))
        tags = (SRC / "tags.cc").read_text()
        self.assertIn("monster_info(&m, MILEV_NAME).title_name().c_str()", tags)
        self.assertIn("monster_info(&**mi2, MILEV_NAME).title_name().c_str()", tags)


if __name__ == "__main__":
    unittest.main()
