#!/usr/bin/env python3
"""Tests for the R2 card inventory tool (card_inventory.py).

Covers the three tool-side blockers of the R2 mechanical routing review:

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
"""

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

GLOSSARY = """\
# Fixture glossary for the card inventory tests.
"""


def fresh_output_path() -> Path:
    """A brand-new basename directly under the real OS temp root."""
    return Path(tempfile.gettempdir()) / (
        f"card-inventory-test-{os.getpid()}-{uuid.uuid4().hex}.json")


def make_repo(root: Path, decks_h: str = DECKS_H, decks_cc: str = DECKS_CC,
              source_txt: str = SOURCE_TXT) -> str:
    """Create a git fixture repo at `root` containing the tool inputs and
    the tool itself, committed at HEAD. Returns the HEAD SHA."""
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
    (root / "crawl-ref/source/dat/descript/zh/cards.txt").write_text(
        ZH_CARDS_TXT, encoding="utf-8")
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

    # -- R2-CODE-003: narrowed output writer --------------------------------

    def test_output_writer_rejects_nested_components(self):
        """A nested path below the temp root (the old parent-chain walk)
        must be rejected: there is no parent chain to pin, so a
        concurrently renamed parent can never relocate the write."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            nested = Path(tempfile.gettempdir()) / (
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
            out = Path(tempfile.gettempdir()) / (
                f"card-inventory-test-{uuid.uuid4().hex}") / "." / "out.json"
            result = run_tool(root, out)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nested components are rejected", result.stderr)

    def test_output_writer_rejects_dotdot_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            out = Path(tempfile.gettempdir()) / (
                f"card-inventory-test-{uuid.uuid4().hex}") / ".." / "out.json"
            result = run_tool(root, out)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("nested components are rejected", result.stderr)

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
            result = run_tool(root, Path(tempfile.gettempdir()))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("refusing to write to it", result.stderr)

    def test_output_writer_rejects_relative_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_repo(root)
            result = run_tool(root, Path("relative-out.json"))
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("relative path rejected", result.stderr)


if __name__ == "__main__":
    unittest.main()
