#!/usr/bin/env python3
"""Exercise the production WebTiles account handlers without a browser/server."""
import ast
import collections
import json
import shutil
import subprocess
import types
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLIENT = ROOT / "crawl-ref/source/webserver/static/scripts/client.js"
SERVER = ROOT / "crawl-ref/source/webserver/webtiles/ws_handler.py"
GAME_LINKS = ROOT / "crawl-ref/source/webserver/templates/game_links.html"

# jQuery is a display/event recorder here, not a replacement DOM implementation.
# Actual template rendering and layout are checked separately in Chromium.
HARNESS = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const elements = new Map(), handlers = {}, sent = [];
let ready;
function $(key) {
    if (key && key.testNode) return key;
    if (!elements.has(key)) {
        const e = {testNode: true, length: 1, value: "", content: "", events: {}, mode: null,
                   appended: [], attributes: {}, dataset: {}, styles: {}, found: new Map(),
                   0: {config: null}};
        for (const method of ["show", "hide", "focus", "blur", "stop", "css", "trigger"])
            e[method] = () => e;
        e.ready = callback => { ready = callback; return e; };
        e.bind = e.on = (event, callback) => { e.events[event] = callback; return e; };
        e.click = callback => e.bind("click", callback);
        e.resize = callback => e.bind("resize", callback);
        e.fadeIn = (time, callback) => { if (callback) callback(); return e; };
        e.width = e.outerWidth = e.outerHeight = () => 100;
        e.height = value => value === undefined ? 600 : e;
        e.css = (key, value) => { e.styles[key] = value; return e; };
        e.attr = (key, value) => {
            if (value === undefined) return e.attributes[key];
            e.attributes[key] = value; return e;
        };
        e.data = (key, value) => {
            if (value === undefined) return e.dataset[key];
            e.dataset[key] = value; return e;
        };
        e.find = selector => {
            if (!e.found.has(selector)) {
                const child = $({});
                if (selector.startsWith("#game-")) child.length = 0;
                e.found.set(selector, child);
            }
            return e.found.get(selector);
        };
        e.clone = () => $({});
        e.addClass = e.removeClass = e.replaceWith = () => e;
        e.tablesorter = opts => { e.sortOptions = opts; return e; };
        e.offset = value => value === undefined ? {left: 0, top: 0} : e;
        e.val = value => { if (value === undefined) return e.value; e.value = value; return e; };
        for (const mode of ["text", "html"])
            e[mode] = value => {
                if (value === undefined) return e.content;
                e.content = value; e.mode = mode; e.appended = []; return e;
            };
        e.empty = () => { e.content = ""; e.appended = []; return e; };
        e.append = value => { e.content += value; e.appended.push(value); return e; };
        elements.set(key, e);
    }
    return elements.get(key);
}
$.cookie = () => null;
$.browser = {};
$.each = (values, callback) => values.forEach((value, index) => callback(index, value));
const context = {
    console, document: {}, requirejs: {}, location: {hash: "#lobby"},
    Blob, Uint8Array, setTimeout, clearTimeout, setInterval: () => 0, socket_server: "ws://fixture/socket",
    WebSocket: class {},
    define(dependencies, factory) {
        factory({}, $, {reset_keycodes() {}}, {reset_visibility() {}, clear() {}}, {
            send_message: (msg, data) => sent.push({msg, data}),
            register_handlers: values => Object.assign(handlers, values),
            register_immediate_handlers: values => Object.assign(handlers, values),
        });
    },
};
context.window = context;
vm.runInNewContext(fs.readFileSync(process.argv[1], "utf8"), context);
function submit(selector) { return $(selector).events.submit(); }
function plain(value) { return JSON.parse(JSON.stringify(value)); }
'''


class WebTilesLoginTests(unittest.TestCase):
    def run_client(self, script):
        self.assertIsNotNone(shutil.which("node"), "Node.js is required for WebTiles checks")
        result = subprocess.run(
            ["node", "-e", HARNESS + script, str(CLIENT)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_account_errors_translate_at_display_and_preserve_wire_data(self):
        self.run_client(r'''
for (const [event, reason, selector, expected] of [
    ["login_fail", "Account is disabled.", "#login_message", "账号已停用。"],
    ["register_fail", "User already exists!", "#register_message", "用户名已被使用！"],
    ["change_email_fail", "Invalid email address", "#chem_message", "电子邮箱格式无效。"],
    ["forgot_password_fail", "Email address can't be empty", "#forgot_message", "电子邮箱不能为空。"],
    ["reset_password_fail", "Expired token", "#reset_pw_message", "密码重置令牌已过期。"],
]) {
    const data = {msg: event, reason};
    handlers[event](data);
    assert.equal($(selector).content, expected);
    assert.equal($(selector).mode, "text");
    assert.deepEqual(data, {msg: event, reason});
}
handlers.login_fail({});
assert.equal($("#login_message").content, "登录失败。");
handlers.change_password_fail({reason: "Your password didn't match."});
assert.equal($("#ok_message_content").content, "密码修改失败！ 当前密码不正确。");
''')

    def test_unknown_server_reason_is_literal_text_not_html_or_object_property(self):
        self.run_client(r'''
for (const reason of ["<img src=x onerror=alert(1)>", "Custom server policy", "__proto__", "constructor"]) {
    handlers.register_fail({reason});
    assert.equal($("#register_message").content, reason);
    assert.equal($("#register_message").mode, "text");
}
handlers.change_email_done({email: "<b>example</b>@example.test"});
assert.equal($("#ok_message_content").mode, "text");
assert.ok($("#ok_message_content").content.includes("<b>example</b>@example.test"));
''')

    def test_translated_forms_preserve_commands_fields_and_input(self):
        self.run_client(r'''
ready();
$("#username").val("Player"); $("#password").val("secret");
assert.equal(submit("#login_form"), false);
assert.equal($("#login_message").content, "登录中……");
assert.deepEqual(plain(sent.pop()), {msg: "login", data: {username: "Player", password: "secret"}});
$("#reg_username").val("bad name");
submit("#register_form");
assert.equal($("#register_message").content, "用户名不能包含空格。");
assert.equal(sent.length, 0);
$("#reg_username").val("Player");
$("#reg_password").val("secret"); $("#reg_repeat_password").val("different");
submit("#register_form");
assert.equal($("#register_message").content, "两次输入的密码不一致。");
assert.equal(sent.length, 0);
$("#reg_repeat_password").val("secret"); $("#reg_email").val("p@example.test");
submit("#register_form");
assert.deepEqual(plain(sent.pop()), {msg: "register", data: {username: "Player", password: "secret", email: "p@example.test"}});
$("#forgot_email").val("p@example.test");
submit("#forgot_form");
assert.deepEqual(plain(sent.pop()), {msg: "forgot_password", data: {email: "p@example.test"}});
$("#reset_pw_token").val("unchanged-token");
$("#reset_pw_password").val("new-secret"); $("#reset_pw_repeat_password").val("new-secret");
submit("#reset_pw_form");
assert.deepEqual(plain(sent.pop()), {msg: "reset_password", data: {token: "unchanged-token", password: "new-secret"}});
''')

    def test_server_rendered_token_error_is_localized_before_dialog_opens(self):
        self.run_client(r'''
$("#reset_token_error").text("Invalid token");
ready();
assert.equal($("#reset_token_error").content, "密码重置令牌无效。");
assert.equal($("#reset_token_error").mode, "text");
''')

    def test_close_handler_translates_only_known_plain_text_errors(self):
        self.run_client(r'''
const reason = "Could not initialize your rc and morgue!<br>"
    + "This probably means there is something wrong with the server configuration.";
const data = Object.freeze({reason});
assert.equal(handlers.close(data),true);
const crt = $("#crt");
assert.equal(crt.appended.length,2);
assert.equal(crt.appended[0].mode,"text");
assert.equal(crt.appended[0].content,"无法初始化你的配置文件和角色档案！\n这可能是服务器配置有误所致。");
assert.equal(crt.appended[0].styles["white-space"],"pre-line");
assert.equal(crt.appended[1],"<br><br>");
assert.equal(data.reason,reason);
const capacity = Object.freeze({reason:"The maximum number of connections has been reached, sorry :("});
assert.equal(handlers.close(capacity),true);
assert.equal(crt.appended[0].mode,"text");
assert.equal(crt.appended[0].content,"连接数已达到上限，抱歉。");
assert.equal(capacity.reason,"The maximum number of connections has been reached, sorry :(");
// Shutdown HTML, arbitrary diagnostics and near-matches retain the existing
// HTML path. Do not globally translate/textify server close reasons.
for (const unknown of ["<b>Server shutdown</b>","Unknown reason",reason+" ","Account is disabled."]) {
    assert.equal(handlers.close(Object.freeze({reason:unknown})),true);
    assert.equal(crt.mode,"html");
    assert.equal(crt.content,unknown+"<br><br>");
}
''')

    def test_lobby_account_hold_label_keeps_raw_watch_logic_and_sort_key(self):
        self.run_client(r'''
let id=1;
for (const [username,display,watchable] of [
    ["[account hold] Player","[账号审核中] Player",false],
    ["OrdinaryPlayer","OrdinaryPlayer",true],
    ["prefix [account hold] Player","prefix [account hold] Player",true],
    ["[account hold]Player","[account hold]Player",false],
    ["[unknown] Player","[unknown] Player",true]
]) {
    handlers.lobby_clear();
    const data = Object.freeze({id:id++,username,game_id:"raw-game-id",xl:1,
        char:"HuFi",place:"D:1",title:"fixture",idle_time:0,milestone:""});
    handlers.lobby_entry(data);
    const entry = [...elements.values()].find(e=>e.attributes.id==="game-"+data.id);
    assert.ok(entry);
    const cell = entry.find(".username");
    const label = cell.content;
    assert.equal(label.mode,"text");
    assert.equal(label.content,display);
    assert.equal(label,$(watchable ? "<a href='#watch-"+username+"'></a>" : "<b></b>"));
    assert.equal(cell.data("sort"),username);
    handlers.lobby_complete();
    const table = [...elements.values()].filter(e=>e.sortOptions).at(-1);
    assert.equal(table.sortOptions.textExtraction(cell),username);
    assert.equal(data.username,username);
    assert.equal(entry.find(".game_id").content,"raw-game-id");
}
''')


class WebTilesServerDisplayTests(unittest.TestCase):
    def test_capacity_close_is_a_json_message_flushed_before_close(self):
        tree = ast.parse(SERVER.read_text(encoding="utf-8"))
        websocket = next(node for node in tree.body
                         if isinstance(node, ast.ClassDef) and node.name == "CrawlWebSocket")
        names = {"open", "send_message", "append_message", "flush_messages"}
        methods = [node for node in websocket.body
                   if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual(names, {node.name for node in methods})
        for limit, over_capacity in ((0, True), (1, False)):
            with self.subTest(limit=limit):
                namespace = {"tornado": types.SimpleNamespace(websocket=types.SimpleNamespace()),
                             "config": {"max_connections": limit, "dgl_mode": True},
                             "sockets": set(), "shutting_down": False,
                             "json_encode": json.dumps}
                exec(compile(ast.Module(body=methods, type_ignores=[]), str(SERVER), "exec"), namespace)
                socket_type = type("Socket", (), {name: namespace[name] for name in names})
                socket = socket_type()
                socket.client_closed = False
                socket.message_queue = []
                socket.subprotocol = "no-compression"
                socket.request = types.SimpleNamespace(remote_ip="127.0.0.1")
                socket.ws_connection = types.SimpleNamespace(stream=types.SimpleNamespace(
                    socket=types.SimpleNamespace(fileno=lambda: 1)))
                socket.logger = types.SimpleNamespace(info=lambda *args: None)
                socket.reset_idle_timeouts = lambda: None
                events = []
                socket._send_raw_message = lambda frame: events.append(("frame", json.loads(frame)))
                socket.close = lambda: events.append(("close", None))
                socket.send_lobby = lambda: events.append(("lobby", None))
                socket.open()
                self.assertIn(socket, namespace["sockets"])
                if over_capacity:
                    self.assertEqual(events, [("frame", {"msgs": [{"msg": "close", "reason":
                        "The maximum number of connections has been reached, sorry :("}]}),
                        ("close", None)])
                    self.assertEqual([], socket.message_queue)
                else:
                    self.assertEqual(events, [("lobby", None)])

    def test_real_game_links_template_keeps_raw_save_state_and_disabled_links(self):
        try:
            from tornado.template import Template
        except ImportError:
            self.skipTest("Tornado from webserver/requirements/base.py3.txt required for server template test")

        # Execute the real methods without importing unrelated DB/socket
        # infrastructure. Only transport, game configuration and async save
        # collection are doubles; Tornado renders the actual production file.
        tree = ast.parse(SERVER.read_text(encoding="utf-8"))
        websocket = next(node for node in tree.body
                         if isinstance(node, ast.ClassDef) and node.name == "CrawlWebSocket")
        names = {"update_save_info", "invalidate_saveslot_cache", "send_lobby_html"}
        methods = [node for node in websocket.body
                   if isinstance(node, ast.FunctionDef) and node.name in names]
        self.assertEqual(names, {node.name for node in methods})

        class Game(dict):
            def templated_dict(self, username):
                return dict(self)

        class Config:
            games = collections.OrderedDict(
                (key, Game(name=key, rcfile_path=rc, show_save_info=True))
                for key, rc in [("first", "shared.rc"), ("shared", "shared.rc"),
                                ("ordinary", "own.rc"), ("unknown", "unknown.rc"),
                                ("playing", "playing.rc"), ("escaped", "escaped.rc")])
            binaries_to_games = {"binary": ["first", "shared"]}
            game_modes = {"first": "normal", "shared": "normal"}

        class Socket:
            pass

        socket = Socket()
        namespace = {"collections": collections, "config": Config,
                     "sockets": {socket}, "json_decode": json.loads,
                     "to_unicode": lambda value: value.decode("utf-8")}
        code = ast.Module(body=methods, type_ignores=[])
        exec(compile(code, str(SERVER), "exec"), namespace)
        socket.username = "Player"
        socket.ui = {}
        socket.save_info = {"ordinary": "", "unknown": "[slot full] suffix",
                            "playing": "[playing]", "escaped": "<b>custom</b>"}
        namespace["update_save_info"](socket, "binary", json.dumps({
            "normal": {"loadable": True, "game_type": "other"}}))
        self.assertEqual("[slot full]", socket.save_info["first"])
        self.assertEqual("[slot full]", socket.save_info["shared"])
        raw = dict(socket.save_info)
        rendered_args = []

        def render_string(name, **kwargs):
            if name == "banner.html":
                return b"banner fixture"
            self.assertEqual("game_links.html", name)
            self.assertIs(kwargs["save_info"], socket.save_info)
            self.assertTrue(kwargs["disabled"]("[slot full]"))
            self.assertFalse(kwargs["disabled"]("[存档位已占用]"))
            self.assertFalse(kwargs["disabled"]("[slot full] suffix"))
            rendered_args.append(kwargs)
            return Template(GAME_LINKS.read_bytes(), name=str(GAME_LINKS)).generate(**kwargs)

        sent = []
        socket.render_string = render_string
        socket.game_id_allowed = lambda game_id: True
        socket.queue_message = lambda *args, **kwargs: None
        socket.send_message = lambda message, **kwargs: sent.append((message, kwargs))
        socket.collect_save_info = lambda callback: callback()
        socket.logger = type("Logger", (), {"warning": lambda *args, **kwargs: self.fail(str(args))})()
        namespace["send_lobby_html"](socket)
        self.assertEqual(raw, socket.save_info)
        self.assertEqual(1, len(rendered_args))
        self.assertEqual(1, len(sent))
        self.assertEqual("set_game_links", sent[0][0])
        html = sent[0][1]["content"]
        self.assertEqual(2, html.count("[存档位已占用]"))  # unique and shared-rc branches
        self.assertNotIn('href="#play-first"', html)
        self.assertNotIn('href="#play-shared"', html)
        for game_id in ("ordinary", "unknown", "playing", "escaped"):
            self.assertIn('href="#play-' + game_id + '"', html)
        self.assertIn("[slot full] suffix", html)
        self.assertIn("[游戏进行中]", html)
        self.assertEqual("[playing]", socket.save_info["playing"])
        self.assertIn("&lt;b&gt;custom&lt;/b&gt;", html)
        for game_id in ("first", "ordinary"):
            self.assertIn('data-game_id="' + game_id + '"', html)

        # The existing ASCII cache comparison remains effective after display.
        namespace["invalidate_saveslot_cache"](socket, "first")
        self.assertIsNone(socket.save_info["first"])
        self.assertIsNone(socket.save_info["shared"])
        self.assertEqual(raw["unknown"], socket.save_info["unknown"])


if __name__ == "__main__":
    unittest.main()
