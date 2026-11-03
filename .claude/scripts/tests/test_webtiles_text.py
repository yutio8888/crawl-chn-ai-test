#!/usr/bin/env python3
"""Exercise WebTiles' text renderer and protocol/display consumers."""
import json
import re
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


# Load real AMD consumers and the real map delta merge. The doubles below only
# replace browser DOM/canvas, transport registration and user option storage.
FRONTEND_HARNESS = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const nodes = new Map(), events = [], handlers = {}, errors = [];
const document = {};
class Node {
    constructor() {
        this.classes = new Set(); this.attrs = {}; this.styles = {};
        this.appended = []; this.found = new Map(); this.value = "";
        this.length = 1;
        this[0] = {style: {}};
    }
    text(v) { if (v === undefined) return this.value; this.value = v; return this; }
    html(v) { if (v === undefined) return this.value; this.value = v; this.appended = []; return this; }
    attr(k,v) { if (v === undefined) return this.attrs[k]; this.attrs[k] = v; return this; }
    css(k,v) { if (typeof k === "object") Object.assign(this.styles,k); else this.styles[k]=v; return this; }
    addClass(c) { if (c) c.split(/\s+/).forEach(x => this.classes.add(x)); return this; }
    removeClass(c) { if (c) c.split(/\s+/).forEach(x => this.classes.delete(x)); else this.classes.clear(); return this; }
    toggleClass(c,on) { if (on) this.classes.add(c); else this.classes.delete(c); return this; }
    append(...c) { this.appended.push(...c); return this; }
    find(k) { if (!this.found.has(k)) this.found.set(k,new Node()); return this.found.get(k); }
    children(k) { return this.find("children:"+k); }
    eq(i) { return this.find("eq:"+i); }
    filter(k) { return this.find("filter:"+k); }
    clone() { return new Node(); } index() { return 0; }
    hasClass(c) { return this.classes.has(c); }
    empty() { this.appended=[]; return this; }
    show() { return this; } hide() { return this; } remove() { return this; }
    width() { return this; } height() { return this; } size() { return 0; }
    each() { return this; } trigger() { return this; } triggerHandler() { return this; }
    off() { return this; }
    on(name,fn) { if (this === docNode) events.push([name,fn]); return this; }
    bind(name,fn) { return this.on(name,fn); }
}
const docNode = new Node();
function $(selector) {
    if (selector === document) return docNode;
    if (selector instanceof Node) return selector;
    if (selector.startsWith("<")) return new Node();
    if (!nodes.has(selector)) nodes.set(selector,new Node());
    return nodes.get(selector);
}
$.extend = Object.assign;
$.each = (obj,fn) => Object.keys(obj).forEach(key => fn(key,obj[key]));
const options = {
    get(key) {
        if (key.endsWith("_colour")) return [];
        if (key === "tile_display_mode") return "tiles";
        if (key.endsWith("_family")) return "";
        return false;
    },
    add_listener() {}
};
function load(name, deps) {
    let result;
    vm.runInNewContext(fs.readFileSync(path.join(process.argv[1],name+".js"),"utf8"), {
        document, console:{log:error=>errors.push(error)},
        define(names, factory) { result = factory(...names.map(dep => deps[dep])); }
    }, {filename:name+".js"});
    return result;
}
const util = load("util",{});
util.init_canvas = (canvas,w,h) => { canvas.style.width=w; canvas.style.height=h; };
const enums = {prepare_bg_flags: flags => typeof flags === "object" ? flags : {}};
const map = load("map_knowledge", {jquery:$,"./enums":enums,"./util":util});
const player = load("player", {
    jquery:$, comm:{register_handlers:h=>Object.assign(handlers,h)},
    client:{is_watching:()=>false}, "./enums":enums, "./map_knowledge":map,
    "./messages":{new_command(){}}, "./options":options,"./util":util
});
class Renderer {
    constructor() { this.cell_width=32; this.cell_height=32; }
    set_cell_size(w,h) { this.cell_width=w; this.cell_height=h; }
    init() {} render_cell() {} draw_main() {} draw_from_texture() {}
}
const list = load("monster_list", {
    jquery:$,"./map_knowledge":map,"./cell_renderer":{DungeonCellRenderer:Renderer},
    "./dungeon_renderer":{cell_width:32,cell_height:32},"./options":options,
    "./util":util,"./player":player,"./tileinfo-main":{}
});
events.filter(([name])=>name.split(".")[0]==="game_init").forEach(([,fn])=>fn());
function receive(status) {
    handlers.player({status, hp:10,hp_max:10,real_hp_max:10,mp:5,mp_max:5,
        str:10,str_max:10,int:10,int_max:10,dex:10,dex_max:10,
        doom:0,quiver_desc:"",adjusted_noise:700});
}
function mergeMonster(id, diff) {
    map.merge([{x:id,y:1,t:{bg:0},mon:{id,...diff}}]);
    list.update_loc({x:id,y:1}); list.update(false);
}
function listed() { return list.get().flatMap(group => group.monsters.map(entry=>entry.mon.id)).sort(); }
'''


class WebTilesTextTests(unittest.TestCase):
    def run_renderer(self, script):
        self.assertIsNotNone(shutil.which("node"), "Node.js is required for WebTiles checks")
        result = subprocess.run(
            ["node", "-e", HARNESS + script, str(UTIL)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


    def run_frontend(self, script):
        self.assertIsNotNone(shutil.which("node"), "Node.js is required for WebTiles checks")
        result = subprocess.run(
            ["node", "-e", FRONTEND_HARNESS + script, str(UTIL.parent)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_status_protocol_keys_drive_real_player_message_hud_in_both_languages(self):
        self.run_frontend(r'''
for (const zh of [false,true,false]) {
    receive([
        {key:"silenced",text:zh ? "显示甲" : "silenced",light:zh ? "甲" : "Sil",col:4},
        {key:"lost strength",text:zh ? "显示乙" : "lost strength"},
        {key:"vitalised",text:zh ? "显示丙" : "vitalised"},
        {key:"divinely vigorous",text:zh ? "显示丁" : "divinely vigorous"},
        {key:"gold aura",text:zh ? "显示戊" : "gold aura"}
    ]);
    assert.equal($("#stats_noise").attrs["data-level"],"blank");
    assert.equal($("#stats_noise_bar_full").styles.width,"0%");
    assert.ok($("#stats_str").value.classes.has("zero_stat"));
    assert.ok($("#stats_int").value.classes.has("boosted_stat"));
    assert.ok($("#stats_dex").value.classes.has("boosted_stat"));
    assert.ok($("#stats_hp").classes.has("boosted_stat"));
    assert.ok($("#stats_mp").classes.has("boosted_stat"));
    assert.ok($("#stats_gozag_gold").classes.has("boosted_stat"));
    assert.equal($("#stats_status_lights").appended[0].value,zh ? "甲" : "Sil");
}
// Unknown current statuses are explicit empty keys, even if their display
// happens to contain every English substring the client knows.
receive([{key:"",text:"silenced lost str vitalised divinely vigorous berserking gold aura"}]);
assert.equal($("#stats_noise").attrs["data-level"],"veryloud");
assert.equal($("#stats_str").value.classes.size,0);
assert.equal($("#stats_hp").classes.size,0);
assert.equal($("#stats_mp").classes.size,0);
assert.equal($("#stats_gozag_gold").classes.size,0);
// Old servers remain supported through their English text, only when key is absent.
receive([{text:"silenced"},{text:"berserking"},{text:"gold aura"}]);
assert.equal($("#stats_noise").attrs["data-level"],"blank");
assert.ok($("#stats_hp").classes.has("boosted_stat"));
assert.ok($("#stats_gozag_gold").classes.has("boosted_stat"));
''')

    def test_hud_captions_follow_server_labels_with_english_fallback(self):
        self.run_frontend(r'''
handlers.player({hud_labels:{"*WIZARD*":"*巫师*","*EXPLORE*":"*探索*",
    "Health:":"生命:","Turn:":"回合:","Silenced":"沉默","Gold:":"金币:"},
    wizard:true, explore:false, hp:10,hp_max:10,real_hp_max:10,
    mp:5,mp_max:5,str:10,str_max:10,int:10,int_max:10,dex:10,dex_max:10,
    doom:0,quiver_desc:"",adjusted_noise:700,god:"Gozag",gold:42});
assert.equal($("#stats_wizmode").value,"*巫师*");
assert.equal($("#stats_hpline > .stats_caption").value,"生命:");
assert.equal($("#stats_time_caption").value,"回合:");
assert.equal($("#stats_gozag_gold_label").value," 金币: ");
// The silenced noise label is a HUD caption, not a status light.
handlers.player({status:[{key:"silenced",text:"显示",light:"Sil",col:4}]});
assert.equal($("#stats_noise_status").value,"沉默");
// Older servers send no labels: English captions remain the fallback.
handlers.player({hud_labels:{},wizard:false,explore:true,status:[],
    hp:10,hp_max:10,real_hp_max:10,mp:5,mp_max:5,
    str:10,str_max:10,int:10,int_max:10,dex:10,dex_max:10,
    doom:0,quiver_desc:"",adjusted_noise:700});
assert.equal($("#stats_wizmode").value,"*EXPLORE*");
assert.equal($("#stats_hpline > .stats_caption").value,"Health:");
assert.equal($("#stats_time_caption").value,"Turn:");
assert.equal($("#stats_noise_status").value,"");
// A silenced status without labels still uses the English HUD caption.
handlers.player({status:[{key:"silenced",text:"显示",light:"Sil",col:4}]});
assert.equal($("#stats_noise_status").value,"Silenced");
''')

    def test_hud_caption_contract_covers_html_js_and_server(self):
        source = ROOT / "crawl-ref/source"
        cpp = (source / "tileweb.cc").read_text(encoding="utf-8")
        block = cpp.split(
            "static const char * const captions[] = {", 1)[1].split("};", 1)[0]
        server = set(re.findall(r'N_\("([^"]+)"\)', block)) | {"Silenced"}
        self.assertIn('C_("webtiles_hud", "Silenced")', cpp)
        html = (source / "webserver/game_data/templates/game.html").read_text(
            encoding="utf-8")
        captions = set(re.findall(r'data-caption="([^"]+)"', html))
        js = (source / "webserver/game_data/static/player.js").read_text(
            encoding="utf-8")
        asked = set(re.findall(r'hud_caption\("([^"]+)"\)', js))
        self.assertTrue(captions)
        self.assertTrue(asked)
        self.assertEqual(set(), captions - server)
        self.assertEqual(set(), asked - server)
        self.assertIn('$("#stats .stats_caption[data-caption]")', js)

    def test_expiring_suffix_uses_the_producer_translation(self):
        # status.cc::_mark_expiring appends T_(" (expiring)") to short_text, so
        # the WebTiles tooltip must compare against that same translated value.
        source = ROOT / "crawl-ref/source"
        producer = (source / "status.cc").read_text(encoding="utf-8")
        consumer = (source / "tileweb.cc").read_text(encoding="utf-8")
        required = json.loads(
            (ROOT.parent / "stable-trunk-fixes/frontend-required-keys.json")
            .read_text(encoding="utf-8")
            if (ROOT.parent / "stable-trunk-fixes/frontend-required-keys.json").exists()
            else '{"required_keys": []}')

        producer_suffix = re.search(
            r'inf\.short_text\s*\+=\s*T_\("([^"]*)"\)', producer)
        self.assertIsNotNone(producer_suffix)
        suffix = producer_suffix.group(1)
        self.assertEqual(" (expiring)", suffix)

        # The consumer must derive the suffix from T_ and use a suffix match.
        self.assertIn(f'T_("{suffix}")', consumer)
        self.assertIn("ends_with(inf.short_text, expiring_suffix)", consumer)
        # A hardcoded English search would stop working once the key is
        # translated; the producer value must be the only criterion.
        self.assertNotIn(f'find("{suffix}")', consumer)

        # Model the consumer expression for the three real cases.
        def shows_suffix(short_text, translated):
            value = translated if translated else suffix
            return bool(value) and short_text.endswith(value)

        self.assertTrue(shows_suffix("Haste " + suffix, None))
        self.assertFalse(shows_suffix("Haste", None))
        zh = "（即将结束）"
        self.assertTrue(shows_suffix("迅捷" + zh, zh))
        self.assertFalse(shows_suffix("迅捷", zh))
        # The replaced English-only check could not see a translated suffix.
        self.assertNotIn(suffix, "迅捷" + zh)

        keys = {entry["key"] for entry in required["required_keys"]}
        if keys:
            self.assertIn(suffix, keys)

    def test_species_identity_and_display_name_stay_separate(self):
        self.run_frontend(r'''
handlers.player({species:"Human", species_display_name:"人类",
    god:"Zin", god_display_name:"辛", hud_labels:{" of ":" 的 "},
    piety_rank:0, penance:false, ostracism_pips:0,
    hp:10,hp_max:10,real_hp_max:10,mp:5,mp_max:5,
    str:10,str_max:10,int:10,int_max:10,dex:10,dex_max:10,
    doom:0,quiver_desc:"",adjusted_noise:700});
// data-species drives client-side keys, so it must stay the canonical name.
assert.equal($("#stats").attrs["data-species"],"Human");
assert.equal($("#stats_species_god").value,"人类 的 辛");
// English (and older servers without the display field) are unchanged.
handlers.player({species_display_name:"",god_display_name:"",hud_labels:{},
    piety_rank:0, penance:false, ostracism_pips:0,
    hp:10,hp_max:10,real_hp_max:10,mp:5,mp_max:5,
    str:10,str_max:10,int:10,int_max:10,dex:10,dex_max:10,
    doom:0,quiver_desc:"",adjusted_noise:700});
assert.equal($("#stats_species_god").value,"Human of Zin");
''')

    def test_status_queries_keep_regex_and_colour_semantics_with_canonical_keys(self):
        self.run_frontend(r'''
for (const key of ["paralysed","petrified","sleeping","confused"]) {
    receive([{key,text:"显示"}]);
    assert.ok(player.incapacitated());
}
receive([{key:"held",text:"显示",col:4}]);
assert.ok(player.has_status("held",4));
assert.ok(player.incapacitated());
receive([{key:"held",text:"held",col:2}]);
assert.equal(player.has_status("held",4),false);
assert.equal(player.incapacitated(),false);
receive([{key:"",text:"paralysed sleeping held",col:4}]);
assert.equal(player.incapacitated(),false);
for (const stat of ["strength","intelligence","dexterity"]) {
    receive([{key:"lost "+stat,text:"显示"}]);
    assert.ok($("#stats_"+stat.slice(0,3)).value.classes.has("zero_stat"));
}
// Durations may be expiring in display; their raw base identity stays stable.
receive([{key:"berserking",text:"显示（即将结束）"}]);
assert.ok($("#stats_hp").classes.has("boosted_stat"));
assert.equal($("#stats_mp").classes.size,0);
''')

    def test_monster_list_uses_native_membership_through_map_deltas(self):
        self.run_frontend(r'''
list.set_max_rows(20);
const base = {type:1,att:0,threat:0,typedata:{avghp:10,no_exp:true}};
// Current native decisions: inactive/active ballistomycetes both give XP;
// kraken/starspawn tentacles have no XP but are list exceptions; eldritch
// tentacles and the ordinary monster give XP; segments/vines/spores do not.
const excluded = [false,false,false,false,false,true,true,true,false];
const noExp = [false,false,true,true,false,true,true,true,false];
for (let i=0;i<excluded.length;i++)
    mergeMonster(i+1,{...base,type:i+1,typedata:{avghp:10,no_exp:noExp[i]},
        list_excluded:excluded[i],name:"显示"+i,plural:"复数"+i});
assert.equal(JSON.stringify(listed()),JSON.stringify([1,2,3,4,5,9]));
// A language change and misleading English display names cannot override flags.
for (let i=0;i<excluded.length;i++)
    mergeMonster(i+1,{name:excluded[i] ? "active ballistomycete" : "ordinary fungus"});
assert.equal(JSON.stringify(listed()),JSON.stringify([1,2,3,4,5,9]));
// Synthetic same-type deltas verify that the real map cache merges explicit
// booleans in either direction without reusing typedata or interpreting names.
mergeMonster(6,{list_excluded:false});
mergeMonster(2,{list_excluded:true});
assert.equal(JSON.stringify(listed()),JSON.stringify([1,3,4,5,6,9]));
// Legacy missing-field payloads retain their old English fallback.
list.clear(); map.clear();
mergeMonster(1,{...base,name:"active ballistomycete"});
mergeMonster(2,{...base,name:"starspawn tentacle"});
mergeMonster(3,{...base,name:"tentacle segment"});
mergeMonster(4,{...base,name:"snaplasher vine"});
mergeMonster(5,{...base,name:"ballistomycete"});
assert.equal(JSON.stringify(listed()),JSON.stringify([1,2]));
''')

    def test_god_powers_popup_preserves_localized_rows_costs_and_colours(self):
        self.run_frontend(r'''
let shown;
load("ui-layouts", {
    jquery:$,comm:{register_handlers:h=>Object.assign(handlers,h)},client:{},
    "./ui":{show_popup:popup=>{shown=popup;}},"./enums":enums,
    "./cell_renderer":{DungeonCellRenderer:Renderer},"./util":util,
    "./scroller":()=>({}),"./tileinfo-main":{},"./tileinfo-gui":{},
    "./tileinfo-player":{},"./options":options
});
function showRows(rows,extra="") {
    handlers["ui-push"]({type:"describe-god",extra,name:"fixture",colour:14,
        tile:{t:0,tex:0},is_altar:false,description:"",title:"",favour:"",
        powers_list:"<lightgrey>\n\nheader\n"+rows.map(line=>line+"\n").join(""),
        powers:"",info_table:"",wrath:"",service_fee:""});
    assert.equal(errors.length,0,String(errors));
    return shown.children(".body").children(".pane").eq(0).find(".god-powers").appended;
}
function row(colour,power,cost="") {
    return "<div class='power fg"+colour+"'><div>"
        +util.formatted_string_to_html(power)+"</div><div>"
        +util.formatted_string_to_html(cost)+"</div></div>";
}
for (const zh of [false,true,false]) {
    // ZH punctuation is copied from the existing None./life-protection assets;
    // opaque cost labels also exercise fullwidth and nested parentheses.
    const protection = zh ? "甲守护你的生命。" : "Fixture protects your life.";
    const noCost = zh ? "无。" : "None.";
    const cost = zh ? "（费用甲（乙））" : "(Permanent MP (4 remaining))";
    const rows = showRows([
        "<darkgrey>"+protection,
        noCost,
        "<yellow>"+protection+"          "+cost,
        protection+" (unclosed",
        "<darkgrey>"+protection+" (0)"
    ], zh ? "extra pane" : "");
    assert.equal(JSON.stringify(rows),JSON.stringify([
        row(8,protection),row(8,noCost),row(14,protection,cost),
        row(14,protection+" (unclosed"),row(8,protection,"(0)")
    ]));
}
// Native ordinary costs use ASCII outer parentheses in either language, and
// may meet the sentence directly when the native 80-column padding is zero.
assert.equal(showRows(["<yellow>无。(甲)"])[0],row(14,"无。","(甲)"));
// Unsupported/malformed suffixes and escaped colour-like text remain visible.
assert.equal(showRows(["<darkgrey>No final punctuation"])[0],row(8,"No final punctuation"));
assert.equal(showRows(["<<red>literal (unfinished"])[0],row(14,"<<red>literal (unfinished"));
assert.equal(showRows([]).length,0);
''')

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
