#!/usr/bin/env python3
"""Tests for the R2 card inventory tool (card_inventory.py).

Covers the tool-side blockers of the two R2 mechanical routing review
rounds.

First round (R2-CODE-001..003):

  R2-CODE-001 (production SourceDB model): source.txt is parsed with the
    production semantics of database.cc (`_parse_text_db` with
    trim_keys=false + `i18n_source_lookup`): physical key lines preserved
    verbatim, canonical keys lowercased, T_/C_ lookup with context-first
    and plain-key fallback, empty values treated as misses, duplicate
    canonical keys fail-closed. The passing CLI fixture proves that a
    baseline `T_("Wrath")` (no context key) resolves through the
    lowercase-canonical collision with the weapon-inscription key
    `wrath` -> 狂怒 (name_zh="狂怒", canonical_collision=true,
    exact_case_key=false), and the HEAD form resolves the context key
    `card name|Wrath` -> 神怒.

  R2-CODE-002 (fail-closed parsers): every audited region (card_type
    enum, card_name_en/card_name/card_is_removed switches, fallthrough
    tail, deck tables) has a strict grammar; any unconsumed non-comment
    token aborts with a non-zero exit. Minimal rejected mutations:
    unknown switch return form, unpaired #endif, duplicate case, deck
    table referencing an unknown enum member, duplicate canonical
    source.txt key, and a boolean-expression return.

  R2-CODE-003 (narrowed output writer): --inventory-output must be a
    single brand-new basename directly under the OS temp root; nested
    components, '.', '..', an existing target, a symlinked target and
    the temp root itself are all rejected, while a fresh direct
    basename is accepted.

Second round (R2-CODE2-001..003):

  R2-CODE2-001 (production value normalization): parsed source.txt
    values are normalized exactly like database.cc `_parse_text_db` +
    `i18n_source_lookup` (leading blank lines stripped, loader
    trailing-newline artifact removed, i18n escapes decoded via
    i18n_shared.runtime_normalize_value). Positive fixtures prove a
    leading blank line plus a \\n escape in a value, an empty C_()
    context string behaving like T_(), and the plain-key fallback when a
    context key has an empty value; the negative fixture proves an empty
    value is a miss that falls back to English.

  R2-CODE2-002 (fail-closed parse state machines): duplicate case
    labels are rejected even when both still sit in the pending run
    before a shared return; in card_is_removed() a case after the
    TAG-34 `return true;` is rejected (every removed case must belong
    to the pending run consumed by that return); duplicate #else and
    #elif after #else are rejected by the preprocessor frame tracker.

  R2-CODE2-003 (non-renamable output root): --inventory-output must be
    a single brand-new basename directly under the canonical
    non-renamable /tmp root (root-owned, sticky); the renamable OS user
    temp dir and every nested/'.'/‘..'/relative/symlinked form are
    rejected, while a fresh direct basename is accepted.

Third round (R2-CODE3-001..003):

  R2-CODE3-001 (complete input sequence + DBM_REPLACE modeling): the
    SourceDB and DescriptionDB input sequences are discovered from the
    baseline Git tree exactly like database.cc (TextDB child
    constructor: dat/i18n/zh/*.txt sorted with source.txt first;
    dat/descript/zh/*.txt via the source.txt-present directory scan or
    the parent's fixed list fallback; dat/descript/*.txt in the fixed
    parent order). Every unique blob is read once and the payload binds
    the discovery manifest, per-file digests and input sequences. A
    later-loaded file's definition of a canonical key overrides an
    earlier one (DBM_REPLACE) and every override is reported as an
    override fact; a tree without source.txt fails instead of silently
    producing an empty SourceDB.

  R2-CODE3-002 (narrowed card_is_removed() grammar): only the exact
    canonical shape is accepted -- single top-level `#if
    TAG_MAJOR_VERSION == 34`, one pending case run, the single `return
    true;` of that branch, `#endif`, then `default: return false;`
    outside the block. A nested conditional (e.g. `return true;`
    wrapped in `#if UNRELATED_BUILD_FLAG`, which the real preprocessor
    would evaluate as false) is rejected at CLI level.

  R2-CODE3-003 (no-replace git reads): every git subprocess runs under
    the shared trusted git environment (GIT_NO_REPLACE_OBJECTS=1), so a
    `git replace A B` ref cannot substitute B's blobs for the exact
    baseline A: the payload baseline stays A and A's original blob is
    read.

Fourth round (R2-CODE4-001):

  R2-CODE4-001 (production DescriptionDB parse): parse_db_keys mirrors
    database.cc `_parse_text_db` with trim_keys=true exactly. Entries
    begin only after the first `%%%%` separator (a file-header prelude
    before it never becomes an entry); comment lines (first char '#') are
    the only skipped lines; blank lines inside a value are preserved;
    value lines are right-trimmed per C++ rules (" \t\n\r" only, blank
    lines stay blank); at flush only leading newlines are trimmed, so the
    loader's trailing-newline artifact and internal blank lines are
    retained in the reported production DB values; and the canonical key
    space is the production lowercase (lowercase_string) of the
    C++-trimmed key line. Positive fixture: a two-paragraph description
    keeps its internal blank line (with C++ right-trim and flush-time
    leading-newline trimming locked by exact value equality). Difference
    fixture: a bare line before the first `%%%%` must not surface as a
    description key.
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
TOOL = ROOT / ".claude/scripts/card_inventory.py"
SHARED = ROOT / ".claude/scripts/i18n_shared.py"

# ---------------------------------------------------------------------------
# Fixture content (minimal but complete: enum, switches, removed switch,
# four deck tables, descriptions, source.txt, glossary).
# ---------------------------------------------------------------------------

DECKS_H = """\
#pragma once

enum card_type
{
    CARD_VELOCITY,
    CARD_WRATH,
#if TAG_MAJOR_VERSION == 34
    CARD_SHAFT_REMOVED,
#endif
    NUM_CARDS
};
"""

DECKS_CC = """\
#include "decks.h"

typedef map<card_type, int> deck_archetype;

deck_archetype deck_of_escape =
{
    { CARD_VELOCITY, 5 },
};

deck_archetype deck_of_destruction =
{
    { CARD_WRATH, 5 },
};

deck_archetype deck_of_summoning =
{
};

deck_archetype deck_of_punishment =
{
};

const char* card_name_en(card_type card)
{
    switch (card)
    {
    case CARD_VELOCITY:        return "Velocity";
    case CARD_WRATH:           return "Wrath";
#if TAG_MAJOR_VERSION == 34
    case CARD_SHAFT_REMOVED:
#endif
    case NUM_CARDS:            return "a buggy card";
    }
    return "a very buggy card";
}

const char* card_name(card_type card)
{
    switch (card)
    {
    case CARD_VELOCITY:        return T_("Velocity");
    case CARD_WRATH:           return T_("Wrath");
#if TAG_MAJOR_VERSION == 34
    case CARD_SHAFT_REMOVED:
#endif
    case NUM_CARDS:            return T_("a buggy card");
    }
    return T_("a very buggy card");
}

bool card_is_removed(card_type card)
{
    switch (card)
    {
#if TAG_MAJOR_VERSION == 34
    case CARD_SHAFT_REMOVED:
        return true;
#endif
    default:
        return false;
    }
}
"""

# Baseline-form source.txt: the card key `Wrath` has no context key and no
# exact physical key; the lowercase canonical `wrath` hits the weapon-brand
# key, exactly like the real baseline (9fb8e5dd22).
SOURCE_TXT = """\
%%%%
Velocity
速度
%%%%
wrath
狂怒
%%%%
a buggy card
有 bug 的卡牌
%%%%
a very buggy card
非常有 bug 的卡牌
%%%%
"""

# HEAD-form source.txt: the card name gets its own context key.
SOURCE_TXT_CTX = SOURCE_TXT.replace(
    "%%%%\nwrath\n狂怒\n", "%%%%\nwrath\n狂怒\n%%%%\ncard name|Wrath\n神怒\n")

# HEAD-form decks.cc: card_name() uses the C_ context key for CARD_WRATH.
DECKS_CC_CTX = DECKS_CC.replace(
    '    case CARD_WRATH:           return T_("Wrath");\n',
    '    case CARD_WRATH:           return C_("card name", "Wrath");\n')

# R2-CODE2-001 normalization fixture: the Velocity value has a leading
# blank line and a literal \\n escape; production must display
# `速度\n卡牌` (leading blank stripped, escape decoded), not the raw
# physical parse `\n速度\\n卡牌`.
SOURCE_TXT_NORM = SOURCE_TXT.replace(
    "%%%%\nVelocity\n速度\n%%%%\n",
    "%%%%\nVelocity\n\n速度\\n卡牌\n%%%%\n")

# R2-CODE2-001 empty-context fixture: the context key `card name|Wrath`
# exists but has an EMPTY value, so C_() must fall back to the plain
# `wrath` key (production only accepts a non-empty fetched value).
SOURCE_TXT_EMPTY_CTX = SOURCE_TXT.replace(
    "%%%%\na very buggy card\n非常有 bug 的卡牌\n%%%%\n",
    "%%%%\na very buggy card\n非常有 bug 的卡牌\n%%%%\n"
    "%%%%\ncard name|Wrath\n%%%%\n")

# R2-CODE2-001 negative fixture: the plain `wrath` key has an empty
# value, so T_("Wrath") is a miss and falls back to English.
SOURCE_TXT_EMPTY_PLAIN = SOURCE_TXT.replace(
    "%%%%\nwrath\n狂怒\n",
    "%%%%\nwrath\n%%%%\n")

# R2-CODE2-001 empty-context-string fixture: C_("", "Wrath") must behave
# exactly like T_("Wrath") (production treats `ctx && ctx[0]` as no
# context).
DECKS_CC_EMPTY_CTX = DECKS_CC.replace(
    '    case CARD_WRATH:           return T_("Wrath");\n',
    '    case CARD_WRATH:           return C_("", "Wrath");\n')

CARDS_TXT = """\
%%%%
Velocity card
Velocity card description.
%%%%
Wrath card
Wrath card description.
%%%%
a buggy card
buggy card description.
%%%%
a very buggy card
very buggy card description.
%%%%
the Shaft card
the Shaft card description.
%%%%
"""

ZH_CARDS_TXT = """\
%%%%
Velocity card
速度卡牌描述。
%%%%
Wrath card
狂怒卡牌描述。
%%%%
a buggy card
有 bug 的卡牌描述。
%%%%
a very buggy card
非常有 bug 的卡牌描述。
%%%%
the Shaft card
the Shaft card 描述。
%%%%
"""

# R2-CODE4-001 positive fixture: the ZH Velocity card description has a
# leading blank line after the key (stripped at flush -- only leading
# newlines), a blank line between two paragraphs (PRESERVED), and trailing
# spaces/tab on the first paragraph line (right-trimmed per C++ rules,
# " \t\n\r" only). Production value: "第一段。\n\n第二段。\n" with the
# loader's trailing-newline artifact retained.
ZH_CARDS_TXT_PARAGRAPHS = ZH_CARDS_TXT.replace(
    "%%%%\nVelocity card\n速度卡牌描述。\n%%%%\n",
    "%%%%\nVelocity card\n\n速度卡牌描述。第一段。  \t\n"
    "\n速度卡牌描述。第二段。\n%%%%\n")

# R2-CODE4-001 difference fixture: a file-header comment and a bare line
# before the first `%%%%`. Production `_parse_text_db` keeps in_entry
# false until the first separator, so the bare line must NEVER become an
# entry; the old parser (no in_entry gate) made it a description key.
CARDS_TXT_PRELUDE = ("# 文件头注释\n"
                     "文件头正文不得成为条目。\n"
                     + CARDS_TXT)

GLOSSARY = """\
# Fixture glossary for the card inventory tests.
"""


def fresh_output_path() -> Path:
    """A brand-new basename directly under the canonical /tmp root."""
    return Path("/tmp") / (
        f"card-inventory-test-{os.getpid()}-{uuid.uuid4().hex}.json")


# database.cc AllDBs[0] ("descriptions") fixed English input list: the
# fixture tree must contain every mandatory EN file (production croaks
# on a missing one), so make_repo writes all of them.
EN_DESCRIPT_FILES = (
    "features.txt", "items.txt", "unident.txt", "unrand.txt",
    "monsters.txt", "spells.txt", "gods.txt", "branches.txt",
    "skills.txt", "ability.txt", "cards.txt", "commands.txt",
    "clouds.txt", "status.txt", "monstatus.txt", "mutations.txt",
    "passives.txt",
)


def make_repo(root: Path, decks_h: str = DECKS_H, decks_cc: str = DECKS_CC,
              source_txt: str = SOURCE_TXT,
              extra_i18n: dict[str, str] | None = None,
              extra_desc_zh: dict[str, str] | None = None) -> str:
    """Create a git fixture repo at `root` containing the tool inputs and
    the tool itself, committed at HEAD. Returns the HEAD SHA.

    `extra_i18n` maps an extra .txt basename to content written under
    dat/i18n/zh/ (a domain file loaded after source.txt);
    `extra_desc_zh` does the same under dat/descript/zh/.
    """
    scripts = root / ".claude" / "scripts"
    scripts.mkdir(parents=True)
    shutil.copy(TOOL, scripts / "card_inventory.py")
    shutil.copy(SHARED, scripts / "i18n_shared.py")
    (root / "crawl-ref/source").mkdir(parents=True)
    (root / "crawl-ref/source/dat/descript/zh").mkdir(parents=True)
    (root / "crawl-ref/source/dat/i18n/zh").mkdir(parents=True)
    (root / "docs").mkdir(parents=True)
    (root / "crawl-ref/source/decks.h").write_text(decks_h, encoding="utf-8")
    (root / "crawl-ref/source/decks.cc").write_text(decks_cc, encoding="utf-8")
    (root / "crawl-ref/source/dat/descript/cards.txt").write_text(
        CARDS_TXT, encoding="utf-8")
    for name in EN_DESCRIPT_FILES:
        if name != "cards.txt":
            (root / "crawl-ref/source/dat/descript" / name).write_text(
                "# placeholder\n", encoding="utf-8")
    (root / "crawl-ref/source/dat/descript/zh/cards.txt").write_text(
        ZH_CARDS_TXT, encoding="utf-8")
    (root / "crawl-ref/source/dat/i18n/zh/source.txt").write_text(
        source_txt, encoding="utf-8")
    for name, content in (extra_i18n or {}).items():
        (root / f"crawl-ref/source/dat/i18n/zh/{name}").write_text(
            content, encoding="utf-8")
    for name, content in (extra_desc_zh or {}).items():
        (root / f"crawl-ref/source/dat/descript/zh/{name}").write_text(
            content, encoding="utf-8")
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
    """Run the (copied) card_inventory.py inside the fixture repo."""
    return subprocess.run(
        [sys.executable,
         str(root / ".claude/scripts/card_inventory.py"),
         "--baseline-ref", "HEAD",
         "--inventory-output", str(output)],
        capture_output=True, text=True, cwd=str(root), timeout=60)


class CardInventoryToolTest(unittest.TestCase):
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

    def test_passing_fixture_production_collision(self):
        """R2-CODE-001: baseline-form fixture. `T_("Wrath")` must resolve
        through the lowercase-canonical collision with the weapon-brand
        key `wrath` -> 狂怒 (name_zh, canonical_collision, exact_case_key
        false), never a null / missing translation."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(payload["baseline"],
                                 subprocess.run(
                                     ["git", "rev-parse", "HEAD"],
                                     cwd=str(root), capture_output=True,
                                     text=True, check=True).stdout.strip())
                self.assertTrue(payload["inventory_sha256"])
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                wrath = by_identity["card:CARD_WRATH"]
                self.assertEqual(wrath["name_zh"], "狂怒")
                self.assertFalse(wrath["name_display_fallback"])
                self.assertTrue(wrath["canonical_collision"])
                self.assertFalse(wrath["exact_case_key"])
                self.assertIsNone(wrath["context_key"])
                self.assertEqual(
                    wrath["resolution"],
                    "T_('Wrath') -> canonical 'wrath' hit "
                    "(physical key 'wrath')")
                self.assertEqual(payload["canonical_collisions"],
                                 ["card:CARD_WRATH"])
                self.assertEqual(payload["t_unresolved_keys"], [])
                velocity = by_identity["card:CARD_VELOCITY"]
                self.assertEqual(velocity["name_zh"], "速度")
                self.assertFalse(velocity["canonical_collision"])
                self.assertTrue(velocity["exact_case_key"])
                self.assertEqual(velocity["lifecycle"], "current")
                shaft = by_identity["card:CARD_SHAFT_REMOVED"]
                self.assertEqual(shaft["lifecycle"], "removed")
                self.assertEqual(shaft["desc_key"], "the Shaft card")
                self.assertTrue(shaft["desc_en"] and shaft["desc_zh"])
            finally:
                if out.exists():
                    out.unlink()
    def test_fixture_context_key_form(self):
        """R2-CODE-001: HEAD form. CARD_WRATH uses C_("card name",
        "Wrath") and the context key resolves to 神怒 with no collision;
        the weapon-brand plain key `wrath` is untouched."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, decks_cc=DECKS_CC_CTX, source_txt=SOURCE_TXT_CTX)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                wrath = by_identity["card:CARD_WRATH"]
                self.assertEqual(wrath["name_zh"], "神怒")
                self.assertFalse(wrath["canonical_collision"])
                self.assertTrue(wrath["exact_case_key"])
                self.assertTrue(wrath["context_key"])
                self.assertEqual(payload["canonical_collisions"], [])
                self.assertEqual(payload["t_unresolved_keys"], [])
            finally:
                if out.exists():
                    out.unlink()

    # -- R2-CODE2-001: production value normalization ---------------------

    def test_fixture_value_normalization_leading_blank_and_escape(self):
        """R2-CODE2-001: source.txt values are normalized exactly like
        production `_parse_text_db` + `i18n_source_lookup`: leading blank
        lines are stripped (the flush-time _trim_leading_newlines), the
        loader's trailing-newline artifact is removed, and `\\n` escapes
        become real newlines (i18n_unescape_value). The raw physical
        parse would report '\\n速度\\n卡牌'; the display value is
        '速度\n卡牌'."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, source_txt=SOURCE_TXT_NORM)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                velocity = by_identity["card:CARD_VELOCITY"]
                self.assertEqual(velocity["name_zh"], "速度\n卡牌")
                self.assertFalse(velocity["name_display_fallback"])
                self.assertTrue(velocity["exact_case_key"])
                self.assertFalse(velocity["canonical_collision"])
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_empty_context_string_is_plain_lookup(self):
        """R2-CODE2-001: an empty C_() context string behaves exactly
        like T_() (production i18n_source_lookup treats `ctx && ctx[0]`
        as no context), so `C_("", "Wrath")` resolves the plain
        canonical key `wrath` -> 狂怒 with a canonical collision, exactly
        like the baseline T_("Wrath") form."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, decks_cc=DECKS_CC_EMPTY_CTX)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                wrath = by_identity["card:CARD_WRATH"]
                self.assertEqual(wrath["name_zh"], "狂怒")
                self.assertFalse(wrath["name_display_fallback"])
                self.assertIsNone(wrath["context_key"])
                self.assertTrue(wrath["canonical_collision"])
                self.assertEqual(payload["t_unresolved_keys"], [])
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_context_key_empty_value_plain_fallback(self):
        """R2-CODE2-001: a context key that exists with an EMPTY value
        is a miss and falls back to the plain key (production
        i18n_source_lookup only accepts a non-empty fetched value), so
        `C_("card name", "Wrath")` displays the plain `wrath` value
        狂怒 -- never an empty string."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, decks_cc=DECKS_CC_CTX,
                      source_txt=SOURCE_TXT_EMPTY_CTX)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                wrath = by_identity["card:CARD_WRATH"]
                self.assertEqual(wrath["name_zh"], "狂怒")
                self.assertFalse(wrath["name_display_fallback"])
                self.assertTrue(wrath["context_key"])
                self.assertTrue(wrath["canonical_collision"])
                self.assertEqual(payload["t_unresolved_keys"], [])
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_empty_plain_value_is_miss_english_fallback(self):
        """R2-CODE2-001 negative: a plain key with an empty value is a
        miss after normalization (never an empty display), so production
        falls back to the English key: name_zh is null,
        name_display_fallback is true and the key is reported in
        t_unresolved_keys."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, source_txt=SOURCE_TXT_EMPTY_PLAIN)
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                wrath = by_identity["card:CARD_WRATH"]
                self.assertIsNone(wrath["name_zh"])
                self.assertTrue(wrath["name_display_fallback"])
                self.assertFalse(wrath["canonical_collision"])
                self.assertEqual(payload["t_unresolved_keys"], ["Wrath"])
            finally:
                if out.exists():
                    out.unlink()

    def test_mutation_unknown_return_form_rejected(self):
        """R2-CODE-002: an unknown return form in the localized switch
        (make_stringf instead of T_/C_) must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_CC.replace(
                '    case CARD_WRATH:           return T_("Wrath");\n',
                '    case CARD_WRATH:           return make_stringf("Wrath");\n')
            self.assertNotEqual(mutated, DECKS_CC)
            make_repo(root, decks_cc=mutated)
            self._assert_rejected(root, "unknown return form",
                                  "unconsumed token")

    def test_mutation_unpaired_endif_rejected(self):
        """R2-CODE-002: an unpaired #endif (open TAG-34 block) in the
        enum must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_H.replace("    CARD_SHAFT_REMOVED,\n#endif\n",
                                      "    CARD_SHAFT_REMOVED,\n")
            self.assertNotEqual(mutated, DECKS_H)
            make_repo(root, decks_h=mutated)
            self._assert_rejected(root, "unpaired #endif", "unclosed #if")

    def test_mutation_duplicate_case_rejected(self):
        """R2-CODE-002: a duplicate case label in card_name() must
        abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_CC.replace(
                '    case CARD_WRATH:           return T_("Wrath");\n',
                '    case CARD_WRATH:           return T_("Wrath");\n'
                '    case CARD_WRATH:           return T_("Wrath");\n')
            self.assertEqual(mutated.count('return T_("Wrath");'), 2)
            make_repo(root, decks_cc=mutated)
            self._assert_rejected(root, "duplicate case",
                                  "duplicate case CARD_WRATH")

    def test_mutation_consecutive_duplicate_case_rejected(self):
        """R2-CODE2-002: two consecutive case labels for the same card
        (both still in the pending run before the shared return) must
        abort; the duplicate check covers pending labels, not only
        already-committed values."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_CC.replace(
                '    case CARD_WRATH:           return T_("Wrath");\n',
                '    case CARD_WRATH:\n'
                '    case CARD_WRATH:           return T_("Wrath");\n')
            self.assertNotEqual(mutated, DECKS_CC)
            make_repo(root, decks_cc=mutated)
            self._assert_rejected(root, "consecutive duplicate case",
                                  "duplicate case CARD_WRATH")

    def test_mutation_case_after_return_true_rejected(self):
        """R2-CODE2-002: a removed case after the TAG-34 `return true;`
        (outside the pending run consumed by that return) must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_CC.replace(
                "    case CARD_SHAFT_REMOVED:\n        return true;\n",
                "    case CARD_SHAFT_REMOVED:\n        return true;\n"
                "    case CARD_VELOCITY:\n")
            self.assertNotEqual(mutated, DECKS_CC)
            make_repo(root, decks_cc=mutated)
            self._assert_rejected(root, "case after return true",
                                  "case after the TAG-34 `return true;`")

    def test_mutation_duplicate_else_rejected(self):
        """R2-CODE2-002: a second #else in one conditional block (a C
        constraint violation) must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_H.replace(
                "    CARD_SHAFT_REMOVED,\n#endif\n",
                "    CARD_SHAFT_REMOVED,\n#else\n#else\n#endif\n")
            self.assertNotEqual(mutated, DECKS_H)
            make_repo(root, decks_h=mutated)
            self._assert_rejected(root, "duplicate #else",
                                  "duplicate #else")

    def test_mutation_elif_after_else_rejected(self):
        """R2-CODE2-002: an #elif after #else (a C constraint violation)
        must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_H.replace(
                "    CARD_SHAFT_REMOVED,\n#endif\n",
                "    CARD_SHAFT_REMOVED,\n#else\n"
                "#elif TAG_MAJOR_VERSION == 34\n#endif\n")
            self.assertNotEqual(mutated, DECKS_H)
            make_repo(root, decks_h=mutated)
            self._assert_rejected(root, "#elif after #else",
                                  "#elif after #else")

    def test_mutation_deck_table_unknown_member_rejected(self):
        """R2-CODE-002: a deck table referencing a card that is not a
        card_type enum member must abort."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_CC.replace(
                "    { CARD_VELOCITY, 5 },\n",
                "    { CARD_FOO, 5 },\n")
            self.assertNotEqual(mutated, DECKS_CC)
            make_repo(root, decks_cc=mutated)
            self._assert_rejected(root, "unknown deck member",
                                  "references CARD_FOO which is not a")

    def test_mutation_duplicate_canonical_source_key_rejected(self):
        """R2-CODE-001: two physical keys sharing one canonical key (e.g.
        `Wrath` and `wrath`) must abort instead of silently last-wins."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = SOURCE_TXT.replace(
                "%%%%\nwrath\n狂怒\n",
                "%%%%\nWrath\n神怒\n%%%%\nwrath\n狂怒\n")
            self.assertNotEqual(mutated, SOURCE_TXT)
            make_repo(root, source_txt=mutated)
            self._assert_rejected(root, "duplicate canonical key",
                                  "canonical key collision")

    def test_mutation_bool_expression_return_rejected(self):
        """R2-CODE-002: a boolean-expression return (`return 1;`) in
        card_is_removed() must abort (boolean literals must be exact)."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_CC.replace("        return true;\n",
                                       "        return 1;\n")
            self.assertNotEqual(mutated, DECKS_CC)
            make_repo(root, decks_cc=mutated)
            self._assert_rejected(root, "boolean expression return",
                                  "unconsumed token")

    # -- R2-CODE2-003: narrowed output writer ------------------------------

    def test_output_writer_rejects_renamable_temp_root(self):
        """R2-CODE2-003 race fixture: a renamable root (the OS user
        temp dir, e.g. /var/folders/... on macOS, user-owned 0700) must
        be rejected up front, so a concurrent rename/replace of an
        already opened root can never relocate the write out of the
        trusted root. When the OS temp dir IS the canonical /tmp root
        there is no renamable root to reject and the test is skipped."""
        if os.path.realpath(tempfile.gettempdir()) == os.path.realpath("/tmp"):
            self.skipTest("OS temp dir is the canonical /tmp root")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = Path(tempfile.gettempdir()) / (
                f"card-inventory-test-{uuid.uuid4().hex}.json")
            try:
                result = run_tool(root, out)
            finally:
                if out.exists():
                    out.unlink()
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("renamable roots such as the OS user temp dir",
                          result.stderr)

    def test_output_writer_rejects_nested_components(self):
        """A nested path below the temp root (the old parent-chain walk)
        must be rejected: there is no parent chain to pin, so a
        concurrently renamed parent can never relocate the write."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            nested = Path("/tmp") / (
                f"card-inventory-test-{uuid.uuid4().hex}") / "out.json"
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
            # Plain string: pathlib would collapse the '.' component.
            raw = f"/tmp/card-inventory-test-{uuid.uuid4().hex}/./out.json"
            result = run_tool(root, raw)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not contain '.' or '..' path components",
                          result.stderr)

    def test_output_writer_rejects_dotdot_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = Path("/tmp") / (
                f"card-inventory-test-{uuid.uuid4().hex}") / ".." / "out.json"
            result = run_tool(root, out)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("must not contain '.' or '..' path components",
                          result.stderr)

    def test_output_writer_rejects_existing_target(self):
        """O_EXCL: an existing target (even a hardlink to a shared inode)
        is never truncated or overwritten."""
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
        """O_NOFOLLOW: writing through a symlinked target must fail."""
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
            # O_EXCL wins on some platforms: an existing symlink reports
            # EEXIST ("already exists") instead of ELOOP; either way the
            # target is rejected and nothing is written through it.
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

    # -- R2-CODE3-001: complete input sequence + DBM_REPLACE ------------

    def test_extra_source_txt_overrides_effective_value(self):
        """R2-CODE3-001 positive: a domain file loaded after source.txt
        (directory discovery order, source.txt first) overrides a
        canonical key with DBM_REPLACE semantics; the effective display
        value is the overriding one, the override fact is reported
        (never silent), and the extra file is part of the inputs
        manifest with its own digest."""
        zz = "%%%%\nVelocity\n速度覆盖\n%%%%\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, extra_i18n={"zz-cards.txt": zz})
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(payload["source_input_sequence"],
                                 ["source.txt", "zz-cards.txt"])
                self.assertIn(
                    "crawl-ref/source/dat/i18n/zh/zz-cards.txt",
                    {v["path"] for v in payload["inputs"].values()})
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                velocity = by_identity["card:CARD_VELOCITY"]
                self.assertEqual(velocity["name_zh"], "速度覆盖")
                self.assertFalse(velocity["name_display_fallback"])
                self.assertEqual(
                    velocity["resolution"],
                    "T_('Velocity') -> canonical 'velocity' hit "
                    "(physical key 'Velocity' in zz-cards.txt)")
                self.assertEqual(payload["source_overrides"], [{
                    "canonical_key": "velocity",
                    "winner": {"file": "zz-cards.txt",
                                "raw_key": "Velocity",
                                "key_line": 2},
                    "superseded": [{"file": "source.txt",
                                     "raw_key": "Velocity",
                                     "key_line": 2}],
                }])
            finally:
                if out.exists():
                    out.unlink()

    def test_mutation_missing_source_txt_fails(self):
        """R2-CODE3-001 rejection: an unenumerable/empty source
        directory must not silently produce an empty SourceDB. A tree
        without dat/i18n/zh/source.txt (production's check file for the
        localized SourceDB dir scan and the tool's required input)
        aborts the run."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            (root / "crawl-ref/source/dat/i18n/zh/source.txt").unlink()
            subprocess.run(["git", "add", "-A"], cwd=str(root), check=True)
            subprocess.run(["git", "commit", "-qm", "drop source"],
                           cwd=str(root), check=True)
            self._assert_rejected(root, "missing source.txt",
                                  "contains no source.txt")

    def test_desc_zh_dir_scan_when_source_present(self):
        """R2-CODE3-001: the localized DescriptionDB discovery mirrors
        database.cc's child-constructor conditional. When
        dat/descript/zh/source.txt exists (production's check file), the
        directory scan applies: every .txt is discovered with source.txt
        first, and a later file overrides description keys (DBM_REPLACE)
        with the override fact reported and the effective value used."""
        zh_source = "%%%%\nsource marker\n值\n%%%%\n"
        zz = "%%%%\nVelocity card\n描述覆盖\n%%%%\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, extra_desc_zh={
                "source.txt": zh_source, "zz-cards.txt": zz})
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                seq = payload["desc_zh_input_sequence"]
                self.assertEqual(seq[0], "source.txt")
                self.assertIn("cards.txt", seq)
                self.assertIn("zz-cards.txt", seq)
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                velocity = by_identity["card:CARD_VELOCITY"]
                self.assertTrue(velocity["desc_zh"])
                self.assertEqual(velocity["desc_zh_value"], "描述覆盖\n")
                recs = [r for r in payload["desc_zh_overrides"]
                        if r["canonical_key"] == "velocity card"]
                self.assertEqual(len(recs), 1)
                self.assertEqual(recs[0]["winner"]["file"], "zz-cards.txt")
                self.assertEqual(
                    recs[0]["superseded"][0]["file"], "cards.txt")
            finally:
                if out.exists():
                    out.unlink()

    def test_desc_zh_fixed_order_fallback_without_source(self):
        """R2-CODE3-001: without dat/descript/zh/source.txt the
        localized DescriptionDB inherits the parent's fixed input list
        (database.cc child constructor); a file not in that list (e.g.
        zz-cards.txt) is NOT part of the production sequence, and the
        manifest shows exactly the effective sequence instead of
        pretending to load it."""
        zz = "%%%%\nVelocity card\n描述覆盖\n%%%%\n"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, extra_desc_zh={"zz-cards.txt": zz})
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(payload["desc_zh_input_sequence"],
                                 ["cards.txt"])
                paths = {v["path"] for v in payload["inputs"].values()}
                self.assertNotIn(
                    "crawl-ref/source/dat/descript/zh/zz-cards.txt", paths)
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                velocity = by_identity["card:CARD_VELOCITY"]
                self.assertTrue(velocity["desc_zh"])
                self.assertEqual(velocity["desc_zh_value"],
                                 "速度卡牌描述。\n")
            finally:
                if out.exists():
                    out.unlink()

    # -- R2-CODE4-001: production DescriptionDB parse -----------------

    def test_fixture_desc_paragraph_blank_lines_preserved(self):
        """R2-CODE4-001 positive: parse_db_keys mirrors database.cc
        `_parse_text_db` (trim_keys=true) exactly. A blank line between
        two paragraphs of a description is PRESERVED in the reported
        value; trailing spaces/tab on a value line are right-trimmed per
        C++ rules (" \t\n\r" only); the leading blank line after the
        key is stripped at flush (only leading newlines are trimmed); and
        the loader's trailing-newline artifact is retained -- desc values
        are the exact production DB values, not display-normalized."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, extra_desc_zh={
                "cards.txt": ZH_CARDS_TXT_PARAGRAPHS})
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                velocity = by_identity["card:CARD_VELOCITY"]
                self.assertTrue(velocity["desc_zh"])
                self.assertEqual(
                    velocity["desc_zh_value"],
                    "速度卡牌描述。第一段。\n\n速度卡牌描述。第二段。\n")
            finally:
                if out.exists():
                    out.unlink()

    def test_fixture_desc_prelude_before_first_separator_ignored(self):
        """R2-CODE4-001 difference fixture: content before the first
        `%%%%` (a file-header comment and a bare line) must never become
        an entry. Production `_parse_text_db` keeps in_entry=false until
        the first separator, so the bare line is skipped entirely; the
        old parser made it a key that surfaced in the desc-only key
        lists. The real keys still resolve with production values."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root, extra_desc_zh={
                "cards.txt": CARDS_TXT_PRELUDE})
            out = fresh_output_path()
            try:
                result = run_tool(root, out)
                self.assertEqual(result.returncode, 0, result.stderr)
                payload = json.loads(out.read_text(encoding="utf-8"))
                self.assertNotIn("文件头正文不得成为条目。",
                                 payload["en_only_desc_keys"])
                self.assertNotIn("文件头正文不得成为条目。",
                                 payload["zh_only_desc_keys"])
                by_identity = {e["identity"]: e
                               for e in payload["inventory"]}
                velocity = by_identity["card:CARD_VELOCITY"]
                self.assertTrue(velocity["desc_en"])
                self.assertTrue(velocity["desc_zh"])
                self.assertEqual(velocity["desc_en_value"],
                                 "Velocity card description.\n")
            finally:
                if out.exists():
                    out.unlink()

    # -- R2-CODE3-002: narrowed card_is_removed() grammar ---------------

    def test_mutation_nested_conditional_in_removed_switch_rejected(self):
        """R2-CODE3-002: wrapping `return true;` in a nested
        `#if UNRELATED_BUILD_FLAG` (which the real preprocessor would
        evaluate as false, sending the case to `default: return false;`)
        must be rejected: card_is_removed() accepts only the single
        top-level `#if TAG_MAJOR_VERSION == 34` / `#endif` pair -- no
        nested conditionals, extra branches or repeated #if/#else/#endif
        forms."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mutated = DECKS_CC.replace(
                "    case CARD_SHAFT_REMOVED:\n        return true;\n#endif\n",
                "    case CARD_SHAFT_REMOVED:\n#if UNRELATED_BUILD_FLAG\n"
                "        return true;\n#endif\n#endif\n")
            self.assertNotEqual(mutated, DECKS_CC)
            make_repo(root, decks_cc=mutated)
            self._assert_rejected(
                root, "nested conditional in removed switch",
                "the TAG-34 block is the only conditional")

    # -- R2-CODE3-003: no-replace git reads -----------------------------

    def test_git_replace_ref_ignored(self):
        """R2-CODE3-003: a `git replace A B` ref must never substitute
        B's blobs for the exact baseline A. The tool runs every git
        subprocess under the trusted git environment
        (GIT_NO_REPLACE_OBJECTS=1), so --baseline-ref A reads A's
        original blobs (name_zh from A's source.txt, digest of A's
        blob) and the payload baseline stays A."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            a = make_repo(root)
            (root / "crawl-ref/source/dat/i18n/zh/source.txt").write_text(
                SOURCE_TXT.replace("速度", "速度被替换"), encoding="utf-8")
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
                         str(root / ".claude/scripts/card_inventory.py"),
                         "--baseline-ref", a,
                         "--inventory-output", str(out)],
                        capture_output=True, text=True, cwd=str(root),
                        timeout=60)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(out.read_text(encoding="utf-8"))
                    self.assertEqual(payload["baseline"], a)
                    by_identity = {e["identity"]: e
                                   for e in payload["inventory"]}
                    velocity = by_identity["card:CARD_VELOCITY"]
                    self.assertEqual(velocity["name_zh"], "速度")
                    src_digest = payload["inputs"]["i18n/source.txt"]["sha256"]
                    self.assertEqual(
                        src_digest,
                        hashlib.sha256(SOURCE_TXT.encode("utf-8")).hexdigest())
                finally:
                    if out.exists():
                        out.unlink()
            finally:
                # Remove the temporary replace ref (the temp repo is
                # deleted afterwards; the explicit removal is per the
                # R2-CODE3-003 test contract).
                subprocess.run(["git", "replace", "-d", a],
                               cwd=str(root), capture_output=True)


if __name__ == "__main__":
    unittest.main()
