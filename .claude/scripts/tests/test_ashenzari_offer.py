#!/usr/bin/env python3
"""Execute the production offer formatter with a synthetic EN/ZH catalog.

The catalog owner supplies the real translations later. This fixture uses the
requested full-sentence shape and a deliberately unsuitable shared ' of '
translation to prove the skill slot can be reordered without that fragment.
Catch2 separately exercises the production TextDB lookup/fallback.
"""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_god_inventory import exact_function_body

ROOT = Path(__file__).resolve().parents[3]


class AshenzariOfferTests(unittest.TestCase):
    def test_complete_sentences_in_both_languages(self):
        compiler = shutil.which("c++")
        self.assertIsNotNone(compiler, "C++ compiler required")
        text = (ROOT / "crawl-ref/source/god-abil.cc").read_text()
        body = exact_function_body(text, r"\bstring\s+format_ashenzari_curse_offer")
        consumer = exact_function_body(text, r"\bvoid\s+ashenzari_offer_new_curse")
        self.assertIn("format_ashenzari_curse_offer(curse_names)", consumer)
        source = r'''
#include <cassert>
#include <cstdarg>
#include <cstdio>
#include <string>
using namespace std;
bool zh = false;
int shared_fragment_lookups = 0;
const char *T_(const char *key) {
    if (string(key) == " of ") {
        ++shared_fragment_lookups;
        return zh ? "，信仰" : key;
    }
    if (!zh) return key;
    if (string(key) == "Ashenzari invites you to chain yourself with knowledge of %s.")
        return "艾申扎利邀你以%s方面的知识铸成枷锁束缚自己。";
    if (string(key) == "Ashenzari invites you to chain yourself with knowledge.")
        return "EMPTY_KNOWLEDGE_OFFER";
    return key;
}
string make_stringf(const char *format, ...) {
    char buffer[2048];
    va_list args;
    va_start(args, format);
    vsnprintf(buffer, sizeof(buffer), format, args);
    va_end(args);
    return buffer;
}
string format_ashenzari_curse_offer(const string &curse_names) {
''' + body + r'''
}
int main() {
    assert(format_ashenzari_curse_offer("") ==
           "Ashenzari invites you to chain yourself with knowledge.");
    for (const string list : {"cunning", "cunning and fortitude", "SKILL_%s"})
        assert(format_ashenzari_curse_offer(list) ==
               "Ashenzari invites you to chain yourself with knowledge of " + list + ".");
    zh = true;
    assert(format_ashenzari_curse_offer("") == "EMPTY_KNOWLEDGE_OFFER");
    for (const string list : {"SKILL_A", "SKILL_A、SKILL_B", "SKILL_%s"})
        assert(format_ashenzari_curse_offer(list) ==
               "艾申扎利邀你以" + list + "方面的知识铸成枷锁束缚自己。");
    assert(shared_fragment_lookups == 0);
}
'''
        with tempfile.TemporaryDirectory(prefix="ashenzari-offer-") as tmp:
            path = Path(tmp)
            (path / "test.cc").write_text(source)
            build = subprocess.run(
                [compiler, "-std=c++11", "-Wall", "-Wextra", "-Werror",
                 str(path / "test.cc"), "-o", str(path / "test")],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(0, build.returncode, build.stdout + build.stderr)
            run = subprocess.run([str(path / "test")], capture_output=True,
                                 text=True, timeout=10)
            self.assertEqual(0, run.returncode, run.stdout + run.stderr)


if __name__ == "__main__":
    unittest.main()
