#!/usr/bin/env python3
"""Exercise the production WebTiles account handlers without a browser/server."""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CLIENT = ROOT / "crawl-ref/source/webserver/static/scripts/client.js"

# jQuery is a display/event recorder here, not a replacement DOM implementation.
# Actual template rendering and layout are checked separately in Chromium.
HARNESS = r'''
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const elements = new Map(), handlers = {}, sent = [];
let ready;
function $(key) {
    if (!elements.has(key)) {
        const e = {length: 1, value: "", content: "", events: {}, mode: null};
        for (const method of ["show", "hide", "focus", "blur", "stop", "css", "trigger"])
            e[method] = () => e;
        e.ready = callback => { ready = callback; return e; };
        e.bind = e.on = (event, callback) => { e.events[event] = callback; return e; };
        e.click = callback => e.bind("click", callback);
        e.resize = callback => e.bind("resize", callback);
        e.fadeIn = (time, callback) => { if (callback) callback(); return e; };
        e.width = e.outerWidth = e.outerHeight = () => 100;
        e.height = value => value === undefined ? 600 : e;
        e.offset = value => value === undefined ? {left: 0, top: 0} : e;
        e.val = value => { if (value === undefined) return e.value; e.value = value; return e; };
        for (const mode of ["text", "html"])
            e[mode] = value => {
                if (value === undefined) return e.content;
                e.content = value; e.mode = mode; return e;
            };
        e.append = value => { e.content += value; return e; };
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
            register_immediate_handlers() {},
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


if __name__ == "__main__":
    unittest.main()
