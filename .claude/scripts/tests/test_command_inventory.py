#!/usr/bin/env python3
"""Tests for the R3 command inventory tool (command_inventory.py).

Covers the tool-side safety baselines replicated from the R2 card
inventory (card_inventory.py):

  - Identity source: the command_type enum in command-type.h is parsed
    with a strict fail-closed grammar (duplicate members, unknown
    tokens, malformed member shapes, unpaired preprocessor frames,
    missing/incorrect sentinels all abort); the first member must be
    CMD_NO_CMD and the last CMD_MAX_CMD.

  - Name mapping: `_cmds_to_names`/`_names_to_cmds` in macro.cc are
    populated from the generated `#include "cmd-name.h"`, which is
    produced at build time by util/cmd-name.pl from command-type.h (the
    generated header is NOT tracked in Git). The tool reproduces that
    deterministic transformation exactly from the baseline enum blob:
    every member from CMD_NO_CMD up to (excluding) CMD_DISABLE_MORE is
    mapped to its own name, CMD_MIN_*/CMD_MAX_* aliases are skipped, and
    every name must match the CMD_[A-Z0-9_]+ shape. The macro.cc
    regions that consume the table (the include, the two map
    declarations, the exact name_to_command()/command_to_name() bodies
    with their CMD_NO_CMD fallbacks) are verified with exact fail-closed
    patterns.

  - Description keys: commands.txt (EN) and zh/commands.txt (ZH) are
    parsed with the production database.cc `_parse_text_db` semantics:
    entries begin only after the first `%%%%` (a file-header prelude
    before it never becomes an entry), comment lines are the only
    skipped lines, blank lines inside a value are preserved, value lines
    are right-trimmed per C++ rules, at flush only leading newlines are
    trimmed, and the canonical key space is lowercase_string of the
    C++-trimmed key line. DBM_REPLACE last-wins overrides (including an
    in-file duplicate, which the baseline EN file contains for
    CMD_EXPLORE_NO_REST) are reported as override facts, never silently
    dropped; a malformed CMD_-shaped key aborts.

  - Key -> member back-reference uses name_to_command() semantics: keys
    whose base name is absent from the reverse table (e.g. a stale
    ZH-only CMD_SHOW_KEYBOARD verbose key, which names no enum member)
    are reported truthfully in unresolved_keys / stale_keys instead of
    being silently passed -- the baseline itself contains such a key.

  - SourceDB key space: dat/i18n/zh/source.txt is parsed with the
    production trim_keys=false semantics (physical keys verbatim,
    canonical keys lowercased); a duplicate canonical key is a
    fail-closed error, and any source.txt canonical key in the `cmd_*`
    command-name space is reported as a cross-domain collision.

  - Output writer: --inventory-output must be a single brand-new
    basename directly under the canonical non-renamable /tmp root
    (root-owned, sticky); nested components, '.', '..', an existing
    target, a symlinked target, the temp root itself and relative paths
    are all rejected, while a fresh direct basename is accepted.

  - Git reads: every git subprocess runs under the shared trusted git
    environment (GIT_NO_REPLACE_OBJECTS=1), so a `git replace A B` ref
    cannot substitute B's blobs for the exact baseline A.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOL = ROOT / ".claude/scripts/command_inventory.py"
SHARED = ROOT / ".claude/scripts/i18n_shared.py"

# ---------------------------------------------------------------------------
# Fixture content (minimal but complete: enum, macro.cc name machinery,
# EN/ZH commands.txt, source.txt, glossary).
# ---------------------------------------------------------------------------

# The fixture enum exercises every generator rule: the CMD_NO_CMD anchor,
# the CMD_NO_CMD_DEFAULT hack member, current commands with description
# keys, CMD_MIN_*/CMD_MAX_* aliases (skipped by the generator), a
# USE_TILE conditional block (included by the generator), the
# CMD_DISABLE_MORE stop marker, the synthetic tail and the CMD_MAX_CMD
# sentinel (last, no trailing comma).
COMMAND_TYPE_H = """\
#pragma once

enum command_type
{
    CMD_NO_CMD = 2000,
    CMD_NO_CMD_DEFAULT, // hack to allow assignment of keys to CMD_NO_CMD
    CMD_REST,
    CMD_EXPLORE,
    CMD_MIN_MENU = CMD_REST,
    CMD_MAX_MENU = CMD_EXPLORE,
#ifdef USE_TILE
    CMD_ZOOM_IN,
    CMD_ZOOM_OUT,
#endif
    CMD_DISABLE_MORE,
    CMD_ENABLE_MORE,
    CMD_UNWIELD_WEAPON,
    CMD_NEXT_CMD,
    CMD_MAX_CMD
};
"""

# macro.cc: the exact name-map machinery regions the tool verifies.
MACRO_CC = """\
#include "macro.h"

struct command_name
{
    command_type cmd;
    const char*  name;
};

static command_name _command_name_list[] =
{
#include "cmd-name.h"
};

static name_to_cmd_map _names_to_cmds;
static cmd_to_name_map _cmds_to_names;

command_type name_to_command(string name)
{
    return static_cast<command_type>(lookup(_names_to_cmds, name, CMD_NO_CMD));
}

string command_to_name(command_type cmd)
{
    return lookup(_cmds_to_names, cmd, "CMD_NO_CMD");
}
"""

# EN descriptions: CMD_REST terse+verbose, CMD_EXPLORE terse+verbose,
# CMD_ZOOM_IN terse only (verbose falls back to terse + ".").
COMMANDS_TXT = """\
%%%%
CMD_REST

Rest and heal
%%%%
CMD_REST verbose

Rests while your health and magic regenerate.
%%%%
CMD_EXPLORE

Autoexplore the current level
%%%%
CMD_EXPLORE verbose

Automatically explores the current level.
%%%%
CMD_ZOOM_IN

Zoom in
%%%%
"""

# ZH descriptions: CMD_REST complete, CMD_EXPLORE terse only (the
# verbose key is missing -> missing_t ["verbose_zh"] and the display
# falls back to the terse value plus "."), CMD_ZOOM_IN terse only.
ZH_COMMANDS_TXT = """\
%%%%
CMD_REST

休息并回血
%%%%
CMD_REST verbose

恢复你的健康和魔力。
%%%%
CMD_EXPLORE

自动探索当前楼层
%%%%
CMD_ZOOM_IN

放大
%%%%
"""

# Stale-key fixture: a ZH-only verbose key naming a command that does
# not exist in the enum (mirrors the baseline CMD_SHOW_KEYBOARD verbose
# key). Must be reported, not silently passed.
ZH_COMMANDS_TXT_STALE = ZH_COMMANDS_TXT + """\
%%%%
CMD_SHOW_KEYBOARD verbose

显示键盘。
%%%%
"""

# EN duplicate fixture: the CMD_REST terse key is defined twice; the
# production DBM_REPLACE last-wins semantics keep the later definition
# and the tool records the override fact (mirrors the baseline
# CMD_EXPLORE_NO_REST duplicate).
COMMANDS_TXT_DUP = """\
%%%%
CMD_REST

Rest and heal
%%%%
CMD_REST

Rest and heal again
%%%%
CMD_REST verbose

Rests while your health and magic regenerate.
%%%%
CMD_EXPLORE

Autoexplore the current level
%%%%
CMD_EXPLORE verbose

Automatically explores the current level.
%%%%
CMD_ZOOM_IN

Zoom in
%%%%
"""

# Bad-name-shape fixture: a CMD_-prefixed description key with lowercase
# letters violates the CMD_[A-Z0-9_]+( verbose)? shape and must abort.
COMMANDS_TXT_BAD_SHAPE = COMMANDS_TXT.replace(
    "%%%%\nCMD_REST\n\nRest and heal\n",
    "%%%%\nCMD_rest\n\nRest and heal\n")

# Prelude fixture: a file-header comment and a bare line before the
# first `%%%%`. Production `_parse_text_db` keeps in_entry false until
# the first separator, so the bare line must NEVER become a key.
COMMANDS_TXT_PRELUDE = ("# 文件头注释\n"
                        "文件头正文不得成为条目。\n"
                        + COMMANDS_TXT)

SOURCE_TXT = """\
%%%%
Rest
休息
%%%%
Zoom in
放大
%%%%
"""

# SourceDB cross-domain fixture: a command identity authored into the
# translatable SourceDB must be reported as a cmd-shape collision.
SOURCE_TXT_CMD_KEY = SOURCE_TXT.replace(
    "%%%%\nRest\n休息\n%%%%\n",
    "%%%%\nRest\n休息\n%%%%\nCMD_REST\n命令名\n%%%%\n")

# Duplicate-canonical-key fixture: `Rest` and `rest` share the canonical
# key `rest`; the SourceDB parse must fail closed.
SOURCE_TXT_DUP = SOURCE_TXT.replace(
    "%%%%\nRest\n休息\n%%%%\n",
    "%%%%\nRest\n休息\n%%%%\nrest\n休息二\n%%%%\n")

GLOSSARY = """\
# Fixture glossary for the command inventory tests.
"""


def fresh_output_path() -> Path:
    """A brand-new basename directly under the canonical /tmp root."""
    return Path("/tmp") / (
        f"command-inventory-test-{os.getpid()}-{uuid.uuid4().hex}.json")


def make_repo(root: Path, command_type_h: str = COMMAND_TYPE_H,
              macro_cc: str = MACRO_CC,
              commands_txt: str = COMMANDS_TXT,
              zh_commands_txt: str = ZH_COMMANDS_TXT,
              source_txt: str = SOURCE_TXT) -> str:
    """Create a git fixture repo at `root` containing the tool inputs and
    the tool itself, committed at HEAD. Returns the HEAD SHA."""
    scripts = root / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(TOOL, scripts / "command_inventory.py")
    shutil.copy(SHARED, scripts / "i18n_shared.py")
    (root / "crawl-ref/source/dat/descript/zh").mkdir(parents=True)
    (root / "crawl-ref/source/dat/i18n/zh").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "crawl-ref/source/command-type.h").write_text(
        command_type_h, encoding="utf-8")
    (root / "crawl-ref/source/macro.cc").write_text(macro_cc,
                                                    encoding="utf-8")
    (root / "crawl-ref/source/dat/descript/commands.txt").write_text(
        commands_txt, encoding="utf-8")
    (root / "crawl-ref/source/dat/descript/zh/commands.txt").write_text(
        zh_commands_txt, encoding="utf-8")
    (root / "crawl-ref/source/dat/i18n/zh/source.txt").write_text(
        source_txt, encoding="utf-8")
    (root / "docs/glossary.md").write_text(GLOSSARY, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"],
                   cwd=str(root), check=True)
    subprocess.run(["git", "config", "user.name", "test"],
                   cwd=str(root), check=True)
    subprocess.run(["git", "add", "-A"], cwd=str(root), check=True)
    subprocess.run(["git", "commit", "-qm", "fixture"], cwd=str(root),
                   check=True)
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(root),
                          capture_output=True, text=True, check=True
                          ).stdout.strip()


def run_tool(root: Path, output: Path) -> subprocess.CompletedProcess:
    """Run the (copied) command_inventory.py inside the fixture repo."""
    return subprocess.run(
        [sys.executable,
         str(root / ".claude/scripts/command_inventory.py"),
         "--baseline-ref", "HEAD",
         "--inventory-output", str(output)],
        capture_output=True, text=True, cwd=str(root), timeout=60)


# ---------------------------------------------------------------------------
# Unit-level parser tests (direct module import; no git needed).
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import command_inventory as ci  # noqa: E402


class CommandEnumParserTest(unittest.TestCase):
    def test_unit_enum_members_order_and_anchors(self):
        members = ci.parse_command_enum(COMMAND_TYPE_H)
        self.assertEqual(members[0], "CMD_NO_CMD")
        self.assertEqual(members[-1], "CMD_MAX_CMD")
        self.assertEqual(len(members), 13)
        self.assertIn("CMD_NO_CMD_DEFAULT", members)
        self.assertIn("CMD_MIN_MENU", members)
        self.assertIn("CMD_ZOOM_IN", members)
        self.assertIn("CMD_DISABLE_MORE", members)

    def test_unit_name_table_generator_semantics(self):
        """util/cmd-name.pl semantics: from CMD_NO_CMD up to (excluding)
        CMD_DISABLE_MORE, skipping CMD_MIN_*/CMD_MAX_* aliases; every
        name is the member's own identifier."""
        members = ci.parse_command_enum(COMMAND_TYPE_H)
        table = ci.generate_name_table(members)
        self.assertEqual(
            list(table),
            ["CMD_NO_CMD", "CMD_NO_CMD_DEFAULT", "CMD_REST",
             "CMD_EXPLORE", "CMD_ZOOM_IN", "CMD_ZOOM_OUT"])
        for member, name in table.items():
            self.assertEqual(member, name)
        # The synthetic tail and the aliases are not mapped.
        for unmapped in ("CMD_MIN_MENU", "CMD_MAX_MENU", "CMD_DISABLE_MORE",
                         "CMD_ENABLE_MORE", "CMD_UNWIELD_WEAPON",
                         "CMD_NEXT_CMD", "CMD_MAX_CMD"):
            self.assertNotIn(unmapped, table)

    def test_unit_parse_db_keys_production_semantics(self):
        """_parse_text_db (trim_keys=true): entries begin after the first
        %%%%; the key is the C++-trimmed first line; value lines are
        right-trimmed per C++ rules; internal blank lines are preserved;
        at flush only leading newlines are trimmed; the loader's
        trailing-newline artifact is retained."""
        entries = ci.parse_db_keys(COMMANDS_TXT, "commands.txt")
        keys = {e.raw_key for e in entries}
        self.assertEqual(
            keys,
            {"CMD_REST", "CMD_REST verbose", "CMD_EXPLORE",
             "CMD_EXPLORE verbose", "CMD_ZOOM_IN"})
        rest = next(e for e in entries if e.raw_key == "CMD_REST")
        self.assertEqual(rest.value, "Rest and heal\n")
        rest_v = next(e for e in entries if e.raw_key == "CMD_REST verbose")
        self.assertEqual(rest_v.value,
                         "Rests while your health and magic regenerate.\n")

    def test_unit_parse_db_keys_prelude_never_a_key(self):
        """Content before the first %%%% never becomes an entry."""
        entries = ci.parse_db_keys(COMMANDS_TXT_PRELUDE, "commands.txt")
        keys = {e.raw_key for e in entries}
        self.assertNotIn("文件头正文不得成为条目。", keys)
        self.assertEqual(len(entries), 5)


# ---------------------------------------------------------------------------
# CLI-level tests against fixture repos (git-blob inputs).
# ---------------------------------------------------------------------------

class CommandInventoryToolTest(unittest.TestCase):
    """CLI-level tests against fixture repos (git-blob inputs)."""

    def _assert_rejected(self, root, mutation_name, needle=None):
        out = fresh_output_path()
        try:
            result = run_tool(root, out)
        finally:
            if out.exists():
                out.unlink()
        self.assertNotEqual(
            result.returncode, 0,
            f"mutation {mutation_name} must fail; stdout={result.stdout!r} "
            f"stderr={result.stderr!r}")
        if needle is not None:
            self.assertIn(needle, result.stderr + result.stdout)

    # -- Positive fixtures ------------------------------------------------

    def test_fixture_fallback_chain_and_lifecycle(self):
        """Positive fixture: the full get_command_description() chain is
        modeled per member. CMD_REST has terse+verbose in both languages;
        CMD_EXPLORE misses the ZH verbose key (missing_t ['verbose_zh'],
        verbose_display_zh falls back to the terse value plus '.'); a
        command with only a terse key falls back to terse + '.' for the
        verbose display in both languages; members without any
        commands.txt key are 'unused' and display the command_to_name()
        key-name fallback. The fixture counts mirror the tool contract:
        enum 13, name map 6, unmapped 7, EN 5 key lines, ZH 4."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            head = make_repo(root)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(payload["baseline"], head)
                self.assertEqual(len(payload["enum_members"]), 13)
                self.assertEqual(payload["sentinel"], "CMD_MAX_CMD")
                self.assertEqual(len(payload["name_map"]), 6)
                self.assertEqual(len(payload["unmapped_members"]), 7)
                self.assertEqual(payload["commands_en"]["key_lines"], 5)
                self.assertEqual(payload["commands_zh"]["key_lines"], 4)
                self.assertEqual(payload["commands_en"]["terse"],
                                 ["cmd_explore", "cmd_rest", "cmd_zoom_in"])
                self.assertEqual(payload["commands_en"]["verbose"],
                                 ["cmd_explore verbose", "cmd_rest verbose"])
                self.assertEqual(payload["en_only_keys"],
                                 {"terse": [],
                                  "verbose": ["cmd_explore verbose"]})
                self.assertEqual(payload["zh_only_keys"],
                                 {"terse": [], "verbose": []})
                self.assertEqual(payload["missing_zh_keys"],
                                 ["cmd_explore verbose"])
                self.assertEqual(payload["unresolved_keys"], [])
                self.assertEqual(payload["stale_keys"], [])
                self.assertEqual(len(payload["inventory"]),
                                 len(payload["enum_members"]))
                self.assertTrue(payload["inventory_sha256"])
                # Every mapped member has exactly one name; reverse
                # lookup identity holds.
                self.assertEqual(
                    payload["name_map"],
                    {m: m for m in payload["enum_members"]
                     if m not in payload["unmapped_members"]})

                by_id = {e["identity"]: e for e in payload["inventory"]}
                rest = by_id["command:CMD_REST"]
                self.assertEqual(rest["lifecycle"], "current")
                self.assertEqual(rest["terse_en"], "Rest and heal\n")
                self.assertEqual(rest["terse_zh"], "休息并回血\n")
                self.assertEqual(rest["terse_display_en"], "Rest and heal")
                self.assertEqual(rest["terse_display_zh"], "休息并回血")
                self.assertEqual(rest["verbose_display_en"],
                                 "Rests while your health and magic "
                                 "regenerate.")
                self.assertEqual(rest["verbose_display_zh"], "恢复你的健康和魔力。")
                self.assertEqual(rest["missing_t"], [])

                explore = by_id["command:CMD_EXPLORE"]
                self.assertEqual(explore["lifecycle"], "current")
                self.assertIsNone(explore["verbose_zh"])
                self.assertEqual(explore["missing_t"], ["verbose_zh"])
                self.assertEqual(explore["verbose_display_en"],
                                 "Automatically explores the current level.")
                # verbose -> terse (+ ".") fallback chain in ZH.
                self.assertEqual(explore["verbose_display_zh"],
                                 "自动探索当前楼层.")

                zoom = by_id["command:CMD_ZOOM_IN"]
                self.assertEqual(zoom["lifecycle"], "current")
                self.assertIsNone(zoom["verbose_en"])
                self.assertIsNone(zoom["verbose_zh"])
                self.assertEqual(zoom["verbose_display_en"], "Zoom in.")
                self.assertEqual(zoom["verbose_display_zh"], "放大.")
                self.assertEqual(zoom["missing_t"], [])

                unused = by_id["command:CMD_NO_CMD_DEFAULT"]
                self.assertEqual(unused["lifecycle"], "unused")
                self.assertIsNone(unused["terse_en"])
                # CMD_NO_CMD_DEFAULT is in the generated name table (it
                # is a real command identity before CMD_DISABLE_MORE), so
                # its display fallback is its own name.
                self.assertEqual(unused["terse_display_en"],
                                 "CMD_NO_CMD_DEFAULT")
                self.assertEqual(unused["verbose_display_en"],
                                 "CMD_NO_CMD_DEFAULT")
                self.assertEqual(unused["missing_t"], [])

                # A member excluded from the name table (CMD_MIN_*/CMD_MAX_*
                # alias) has command_to_name()'s NO_CMD fallback name.
                alias = by_id["command:CMD_MIN_MENU"]
                self.assertFalse(alias["name_in_map"])
                self.assertEqual(alias["lookup_name"], "CMD_NO_CMD")
                self.assertEqual(alias["terse_display_en"], "CMD_NO_CMD")
                self.assertEqual(alias["verbose_display_en"], "CMD_NO_CMD")
                self.assertEqual(alias["lifecycle"], "unused")

                sentinel = by_id["command:CMD_MAX_CMD"]
                self.assertFalse(sentinel["name_in_map"])
                self.assertEqual(sentinel["lookup_name"], "CMD_NO_CMD")
                self.assertEqual(sentinel["lifecycle"], "unused")
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_stale_key_reported_truthfully(self):
        """A ZH-only description key whose base name is not in the enum
        (name_to_command() would return CMD_NO_CMD) must be reported in
        zh_only_keys / unresolved_keys / stale_keys, never silently
        passed; the run still succeeds because the baseline itself
        contains such a key."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, zh_commands_txt=ZH_COMMANDS_TXT_STALE)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(payload["zh_only_keys"],
                                 {"terse": [],
                                  "verbose": ["cmd_show_keyboard verbose"]})
                self.assertEqual(payload["unresolved_keys"],
                                 ["cmd_show_keyboard verbose"])
                self.assertEqual(payload["stale_keys"],
                                 ["cmd_show_keyboard"])
                # No enum member exists for the stale key, so it has no
                # inventory record.
                by_id = {e["identity"]: e for e in payload["inventory"]}
                self.assertNotIn("command:CMD_SHOW_KEYBOARD", by_id)
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_en_duplicate_key_dbm_replace_fact(self):
        """An in-file duplicate canonical description key is modeled with
        production DBM_REPLACE last-wins semantics: the effective value
        is the later definition and the override fact is recorded
        (never silently dropped), mirroring the baseline EN
        CMD_EXPLORE_NO_REST duplicate."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, commands_txt=COMMANDS_TXT_DUP)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(payload["commands_en"]["duplicate_keys"],
                                 ["CMD_REST"])
                self.assertEqual(payload["commands_en_overrides"], [{
                    "canonical_key": "cmd_rest",
                    "winner": {"file": "commands.txt",
                                "raw_key": "CMD_REST",
                                "key_line": 6},
                    "superseded": [{"file": "commands.txt",
                                    "raw_key": "CMD_REST",
                                    "key_line": 2}],
                }])
                by_id = {e["identity"]: e for e in payload["inventory"]}
                rest = by_id["command:CMD_REST"]
                self.assertEqual(rest["terse_en"], "Rest and heal again\n")
                self.assertEqual(rest["terse_display_en"],
                                 "Rest and heal again")
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_prelude_before_first_separator_ignored(self):
        """Content before the first %%%% (a file-header comment and a
        bare line) must never become a description key; the real keys
        still resolve with production values."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, commands_txt=COMMANDS_TXT_PRELUDE)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                keys = (payload["commands_en"]["terse"]
                        + payload["commands_en"]["verbose"])
                self.assertNotIn("文件头正文不得成为条目。", keys)
                self.assertEqual(payload["commands_en"]["key_lines"], 5)
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_source_txt_cmd_key_collision_reported(self):
        """A command identity authored into the translatable SourceDB is
        a cross-domain hazard (command names are identity strings, never
        T_() keys); the tool reports it as a cmd-shape collision."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, source_txt=SOURCE_TXT_CMD_KEY)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(payload["source_keys"]
                                 ["cmd_shape_collisions"], ["cmd_rest"])
                self.assertIn("source.txt",
                              payload["inputs"])
            finally:
                if out.exists():
                    out.unlink()

    def test_deterministic_rebuild(self):
        """Two runs of the tool over the same baseline produce byte-identical
        payloads (no timestamps or random content) and the same
        inventory_sha256."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out1 = fresh_output_path()
            out2 = fresh_output_path()
            try:
                result1 = run_tool(root, out1)
                self.assertEqual(result1.returncode, 0, result1.stderr)
                result2 = run_tool(root, out2)
                self.assertEqual(result2.returncode, 0, result2.stderr)
                p1 = json.loads(out1.read_text(encoding="utf-8"))
                p2 = json.loads(out2.read_text(encoding="utf-8"))
                self.assertEqual(p1, p2)
                self.assertEqual(p1["inventory_sha256"],
                                 p2["inventory_sha256"])
            finally:
                for out in (out1, out2):
                    if out.exists():
                        out.unlink()

    # -- Rejected mutations (fail-closed parsers) -------------------------

    def test_mutation_duplicate_member_rejected(self):
        """A duplicate enum member would produce two name-table entries
        for one command (production init_keybindings ASSERTs on the
        duplicate); it must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace(
                "    CMD_REST,\n", "    CMD_REST,\n    CMD_REST,\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "duplicate member",
                                  "duplicate member CMD_REST")

    def test_mutation_bad_name_shape_rejected(self):
        """A member violating the CMD_[A-Z0-9_]+ shape (lowercase
        letters) must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace("    CMD_REST,\n",
                                             "    CMD_rest,\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "bad member shape",
                                  "unexpected token")

    def test_mutation_unknown_enum_token_rejected(self):
        """A non-CMD identifier inside the enum must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace("    CMD_REST,\n",
                                             "    FOO_BAR,\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "unknown enum token",
                                  "unexpected token")

    def test_mutation_unpaired_endif_rejected(self):
        """An open preprocessor frame (unclosed #ifdef) must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace(
                "    CMD_ZOOM_OUT,\n#endif\n",
                "    CMD_ZOOM_OUT,\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "unpaired #endif", "unclosed #if")

    def test_mutation_stray_endif_rejected(self):
        """An unmatched #endif must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace(
                "    CMD_ZOOM_OUT,\n#endif\n",
                "    CMD_ZOOM_OUT,\n#endif\n#endif\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "stray #endif", "unmatched #endif")

    def test_mutation_duplicate_else_rejected(self):
        """A second #else in one conditional block (a C constraint
        violation) must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace(
                "    CMD_ZOOM_OUT,\n#endif\n",
                "    CMD_ZOOM_OUT,\n#else\n#else\n#endif\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "duplicate #else",
                                  "duplicate #else")

    def test_mutation_elif_after_else_rejected(self):
        """An #elif after #else (a C constraint violation) must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace(
                "    CMD_ZOOM_OUT,\n#endif\n",
                "    CMD_ZOOM_OUT,\n#else\n#elif USE_TILE\n#endif\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "#elif after #else",
                                  "#elif after #else")

    def test_mutation_missing_stop_marker_rejected(self):
        """CMD_DISABLE_MORE is the util/cmd-name.pl name-table stop
        marker; a tree without it must abort (the generator would run to
        EOF and the synthetic tail would leak into the name table)."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace("    CMD_DISABLE_MORE,\n", "")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "missing stop marker",
                                  "must contain CMD_DISABLE_MORE")

    def test_mutation_wrong_sentinel_rejected(self):
        """The enum sentinel must be the last member CMD_MAX_CMD."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = COMMAND_TYPE_H.replace(
                "    CMD_NEXT_CMD,\n    CMD_MAX_CMD\n",
                "    CMD_NEXT_CMD\n")
            self.assertNotEqual(mutated, COMMAND_TYPE_H)
            make_repo(root, command_type_h=mutated)
            self._assert_rejected(root, "wrong sentinel",
                                  "must end with the sentinel CMD_MAX_CMD")

    def test_mutation_macro_cc_include_removed_rejected(self):
        """A macro.cc without the `#include "cmd-name.h"` initializer
        region must abort: the audit can no longer verify the source of
        the name tables."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = MACRO_CC.replace('#include "cmd-name.h"\n', "")
            self.assertNotEqual(mutated, MACRO_CC)
            make_repo(root, macro_cc=mutated)
            self._assert_rejected(root, "missing cmd-name.h include",
                                  "exactly one _command_name_list[]")

    def test_mutation_macro_cc_fallback_changed_rejected(self):
        """Changing the name_to_command() CMD_NO_CMD fallback must
        abort: command_to_name()/name_to_command() are the consumers the
        description lookup and hint expansion depend on."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = MACRO_CC.replace(
                "lookup(_names_to_cmds, name, CMD_NO_CMD)",
                "lookup(_names_to_cmds, name, CMD_MAX_CMD)")
            self.assertNotEqual(mutated, MACRO_CC)
            make_repo(root, macro_cc=mutated)
            self._assert_rejected(
                root, "changed name_to_command fallback",
                "exactly one name_to_command()")

    def test_mutation_bad_description_key_shape_rejected(self):
        """A CMD_-prefixed description key violating the
        CMD_[A-Z0-9_]+( verbose)? shape must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, commands_txt=COMMANDS_TXT_BAD_SHAPE)
            self._assert_rejected(root, "bad description key shape",
                                  "violates the CMD_[A-Z0-9_]+")

    def test_mutation_duplicate_canonical_source_key_rejected(self):
        """Two physical source.txt keys sharing one canonical key must
        abort instead of silently last-wins."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, source_txt=SOURCE_TXT_DUP)
            self._assert_rejected(root, "duplicate canonical source key",
                                  "canonical key collision")

    # -- Output writer (fail-closed /tmp-only) ----------------------------

    def test_output_writer_rejects_renamable_temp_root(self):
        """A renamable root (the OS user temp dir, user-owned 0700) must
        be rejected up front. When the OS temp dir IS the canonical /tmp
        root there is no renamable root to reject and the test is
        skipped."""
        if os.path.realpath(tempfile.gettempdir()) == os.path.realpath("/tmp"):
            self.skipTest("OS temp dir is the canonical /tmp root")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = Path(tempfile.gettempdir()) / (
                f"command-inventory-test-{uuid.uuid4().hex}.json")
            try:
                result = run_tool(root, out)
            finally:
                if out.exists():
                    out.unlink()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("renamable roots such as the OS user temp dir",
                          result.stderr)

    def test_output_writer_rejects_nested_components(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            nested = Path("/tmp") / (
                f"command-inventory-test-{uuid.uuid4().hex}") / "out.json"
            try:
                result = run_tool(root, nested)
            finally:
                shutil.rmtree(nested.parent, ignore_errors=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nested components are rejected",
                          result.stderr)

    def test_output_writer_rejects_dot_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            raw = f"/tmp/command-inventory-test-{uuid.uuid4().hex}/./out.json"
            result = run_tool(root, raw)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not contain '.' or '..' path components",
                          result.stderr)

    def test_output_writer_rejects_dotdot_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = Path("/tmp") / (
                f"command-inventory-test-{uuid.uuid4().hex}") / ".." / "out.json"
            result = run_tool(root, out)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not contain '.' or '..' path components",
                          result.stderr)

    def test_output_writer_rejects_existing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = fresh_output_path()
            try:
                out.write_text("pre-existing", encoding="utf-8")
                result = run_tool(root, out)
            finally:
                if out.exists():
                    out.unlink()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("already exists", result.stderr)

    def test_output_writer_rejects_symlink_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = fresh_output_path()
            try:
                out.symlink_to("somewhere-else")
                result = run_tool(root, out)
            finally:
                if out.exists() or out.is_symlink():
                    out.unlink()
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(
                "without following a symlink" in result.stderr
                or "already exists" in result.stderr,
                result.stderr)

    def test_output_writer_rejects_temp_root_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            result = run_tool(root, Path("/tmp"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to write to it", result.stderr)

    def test_output_writer_rejects_relative_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            result = run_tool(root, Path("relative-out.json"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("relative path rejected", result.stderr)

    # -- Trusted git reads ------------------------------------------------

    def test_git_replace_ref_ignored(self):
        """A `git replace A B` ref must never substitute B's blobs for
        the exact baseline A: the tool runs every git subprocess under
        the trusted git environment (GIT_NO_REPLACE_OBJECTS=1), so
        --baseline-ref A reads A's original blobs and the payload
        baseline stays A."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = make_repo(root)
            (root / "crawl-ref/source/dat/descript/zh/commands.txt"
             ).write_text(
                ZH_COMMANDS_TXT.replace("休息并回血", "休息并回血被替换"),
                encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=str(root), check=True)
            subprocess.run(["git", "commit", "-qm", "replacement"],
                           cwd=str(root), check=True)
            b = subprocess.run(["git", "rev-parse", "HEAD"],
                               cwd=str(root), capture_output=True, text=True,
                               check=True).stdout.strip()
            self.assertNotEqual(a, b)
            subprocess.run(["git", "replace", a, b], cwd=str(root),
                           check=True)
            try:
                out = fresh_output_path()
                try:
                    result = subprocess.run(
                        [sys.executable,
                         str(root / ".claude/scripts/command_inventory.py"),
                         "--baseline-ref", a,
                         "--inventory-output", str(out)],
                        capture_output=True, text=True, cwd=str(root),
                        timeout=60)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(out.read_text(encoding="utf-8"))
                    self.assertEqual(payload["baseline"], a)
                    by_id = {e["identity"]: e
                             for e in payload["inventory"]}
                    rest = by_id["command:CMD_REST"]
                    self.assertEqual(rest["terse_zh"], "休息并回血\n")
                    zh_digest = payload["inputs"]["commands_zh"]["sha256"]
                    self.assertEqual(
                        zh_digest,
                        hashlib.sha256(
                            ZH_COMMANDS_TXT.encode("utf-8")).hexdigest())
                finally:
                    if out.exists():
                        out.unlink()
            finally:
                # Remove the temporary replace ref (the temp repo is
                # deleted afterwards; the explicit removal is per the
                # trusted-git test contract).
                subprocess.run(["git", "replace", "-d", a],
                               cwd=str(root), capture_output=True)


if __name__ == "__main__":
    unittest.main()
