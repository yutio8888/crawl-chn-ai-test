#!/usr/bin/env python3
"""Exercise WebTiles' production colour/terminal-cell HTML renderer."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
UTIL = ROOT / "crawl-ref/source/webserver/game_data/static/util.js"

HARNESS = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
let util;
vm.runInNewContext(fs.readFileSync(process.argv[1], "utf8"), {
    define(deps, factory) { util = factory(); }
});
const wide = text => '<span class="webtiles-wide">' + text + '</span>';
const render = text => util.formatted_string_to_html(text, true);
'''


class WebTilesTextTests(unittest.TestCase):
    def run_renderer(self, script):
        self.assertIsNotNone(shutil.which("node"), "Node.js is required for WebTiles checks")
        result = subprocess.run(
            ["node", "-e", HARNESS + script, str(UTIL)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cjk_menu_columns_keep_ascii_padding_and_double_width_glyphs(self):
        self.run_renderer(r'''
assert.equal(render(" a - 火球术          17%   5"),
    " a - " + wide("火") + wide("球") + wide("术") + "          17%   5");
assert.equal(render(" a - Fireball        17%   5"),
    " a - Fireball        17%   5");
assert.equal(render("全角：Ａ！　かな한𠀀"),
    [..."全角：Ａ！　かな한𠀀"].map(wide).join(""));
// Ordinary flowing text retains its font's natural advances.
assert.equal(util.formatted_string_to_html("火球术"), "火球术");
''')

    def test_nonspacing_marks_stay_with_wide_base_and_halfwidth_stays_narrow(self):
        self.run_renderer(r'''
for (const text of ["中\u0301", "か\u3099", "中\uFE00", "𠀀\u{E0100}"])
    assert.equal(render(text), wide(text));
for (const text of ["e\u0301", "\u302A", "\u3099", "\u303F", "ｶﾅ"])
    assert.equal(render(text), text);
''')

    def test_colour_nesting_and_escaped_text_survive_cell_rendering(self):
        self.run_renderer(r'''
assert.equal(render("<red>中<blue>文</blue>字</red>"),
    "<span class='fg4'>" + wide("中") + "</span><span class='fg1'>"
    + wide("文") + "</span><span class='fg4'>" + wide("字") + "</span>");
assert.equal(render("<red>中<bg:blue>文</bg:blue></red>"),
    "<span class='fg4'>" + wide("中") + "</span><span class='bg1'>"
    + "<span class='fg4'>" + wide("文") + "</span></span>");
const html = render("<<red>中</red> & <img src=x onerror=alert(1)>");
assert.ok(html.startsWith("&lt;red&gt;" + wide("中")));
assert.ok(html.includes("&amp;"));
assert.ok(html.includes("&lt;img src=x onerror=alert(1)&gt;"));
assert.ok(!html.includes("<img"));
''')

    def test_scroller_highlights_are_preserved_after_matching_chinese(self):
        self.run_renderer(r'''
const html = util.formatted_string_to_html("法术  1\n能力  2\n").replace(
    /[^\n]*(法术)[^\n]*\n?/g, line => '<span class=highlight>' + line + '</span>');
assert.equal(util.terminal_cell_html(html), '<span class=highlight>'
    + wide("法") + wide("术") + "  1\n</span>"
    + wide("能") + wide("力") + "  2\n");
''')


if __name__ == "__main__":
    unittest.main()
