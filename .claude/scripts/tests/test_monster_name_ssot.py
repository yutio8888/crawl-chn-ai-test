#!/usr/bin/env python3
"""Regression tests for the complete monster-name SSOT audit."""

from __future__ import annotations

import contextlib
import io
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = REPO_ROOT / ".claude" / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import monster_name_ssot as audit


def _write_textdb(path: Path, entries: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    blocks = [f"%%%%\n{key}\n{value}\n" for key, value in entries.items()]
    path.write_text("".join(blocks), encoding="utf-8")


class Fixture:
    def __init__(self, root: Path) -> None:
        self.source_dir = root / "source"
        self.mons_dir = self.source_dir / "dat" / "mons"
        self.mons_dir.mkdir(parents=True)
        self.source_txt = (
            self.source_dir / "dat" / "i18n" / "zh" / "source.txt"
        )
        self.zh_names: dict[str, str] = {}
        self.montitles: dict[str, str] = {}
        self.en_monsters: dict[str, str] = {}
        self.zh_monsters: dict[str, str] = {}
        self.en_quotes: dict[str, str] = {}
        self.zh_quotes: dict[str, str] = {}

    def monster(self, filename: str, name: str, zh_name: str,
                *, unique: bool = False) -> None:
        flags = "unique" if unique else ""
        (self.mons_dir / filename).write_text(
            f'name: "{name}"\nflags: [{flags}]\n', encoding="utf-8"
        )
        self.zh_names[name] = zh_name

    def flush(self) -> None:
        _write_textdb(self.source_txt, self.zh_names)
        _write_textdb(
            self.source_dir / "dat" / "database" / "zh" / "montitle.txt",
            {"__fixture_title__": "fixture", **self.montitles},
        )
        _write_textdb(
            self.source_dir / "dat" / "descript" / "monsters.txt",
            {"__fixture_monster__": "fixture", **self.en_monsters},
        )
        _write_textdb(
            self.source_dir / "dat" / "descript" / "zh" / "monsters.txt",
            {"__fixture_monster__": "fixture", **self.zh_monsters},
        )
        _write_textdb(
            self.source_dir / "dat" / "descript" / "quotes.txt",
            {"__fixture_quote__": "fixture", **self.en_quotes},
        )
        _write_textdb(
            self.source_dir / "dat" / "descript" / "zh" / "quotes.txt",
            {"__fixture_quote__": "fixture", **self.zh_quotes},
        )

    def audit(self, *, quote_exceptions=None, reverse_exceptions=None):
        self.flush()
        return audit.audit_repository(
            str(self.source_dir),
            str(self.source_txt),
            quote_exceptions={} if quote_exceptions is None else quote_exceptions,
            reverse_dup_exceptions=(
                {} if reverse_exceptions is None else reverse_exceptions
            ),
        )


class MonsterNameSsotTests(unittest.TestCase):
    def test_textdb_separator_prefix_matches_production_parser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text(
                "ignored before first separator\n"
                "%%%% suffix accepted by database.cc\n"
                "  Mixed Case Key  \n"
                "first line   \n"
                "# comment omitted\n"
                "second line\n",
                encoding="utf-8",
            )
            entries = audit._parse_required_textdb(str(path))
        self.assertEqual(
            {"mixed case key": "first line\nsecond line\n\n"}, entries
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.txt"
            path.write_text("%%%% source\n  Untrimmed Key  \nvalue\n", encoding="utf-8")
            entries = audit._parse_required_textdb(str(path), trim_keys=False)
        self.assertIn("  untrimmed key  ", entries)

    def test_empty_required_textdb_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.txt"
            path.write_text("# comments and whitespace only\n\n", encoding="utf-8")
            with self.assertRaises(audit.AuditInputError):
                audit._parse_required_textdb(str(path))

    def test_real_repository_passes_complete_inventory(self) -> None:
        source_dir = REPO_ROOT / "crawl-ref" / "source"
        result = audit.audit_repository(
            str(source_dir),
            str(source_dir / "dat" / "i18n" / "zh" / "source.txt"),
        )
        self.assertEqual(671, result.definition_count)
        self.assertEqual(667, result.monster_count)
        self.assertEqual((), result.findings)

    def test_issue_24_inventory_cross_checks_production_enum(self) -> None:
        payload = audit.build_inventory()
        enum_identities = audit._active_monster_enum_identities()
        rows = payload["rows"]
        self.assertEqual(len(enum_identities), payload["count"])
        self.assertEqual(
            {f"monster:{identity}" for identity in enum_identities},
            {row["identity"] for row in rows},
        )
        self.assertEqual(
            payload["definition_count"] + payload["compatibility_count"],
            payload["count"],
        )
        self.assertFalse(audit.inventory_has_violations(payload))
        compatibility_rows = [
            row for row in rows
            if row["lifecycle"] == "compatibility_enum"
        ]
        self.assertTrue(compatibility_rows)
        for row in compatibility_rows:
            self.assertIsNone(row["english_source_name"])
            self.assertIsNone(row["current_chinese_name"])
            self.assertIsNone(row["english_description"])
            self.assertIsNone(row["chinese_description"])

    def test_active_enum_excludes_aliases_and_post_num_sentinels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "monster-type.h"
            path.write_text(
                "enum monster_type {\n"
                " MONS_ALPHA,\n"
                " MONS_0 = MONS_ALPHA,\n"
                " MONS_BETA,\n"
                " NUM_MONSTERS,\n"
                " MONS_NO_MONSTER = 1000,\n"
                "};\n",
                encoding="utf-8",
            )
            identities = audit._active_monster_enum_identities(path)
        self.assertEqual(["MONS_ALPHA", "MONS_BETA"], identities)

    def test_review_coverage_fails_closed_on_any_artifact_mutation(self) -> None:
        payload = audit.build_inventory()
        baseline = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
        ).strip()
        rendered = audit.render_review_results(payload, baseline)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.md"
            inventory = Path(tmp) / "inventory.json"

            def cli_result() -> int:
                with (
                    contextlib.redirect_stdout(io.StringIO()),
                    contextlib.redirect_stderr(io.StringIO()),
                ):
                    return audit.main([
                        "--inventory-output", str(inventory),
                        "--review-results", str(path),
                    ])

            path.write_text(rendered, encoding="utf-8")
            result = audit.review_coverage(payload, path)
            self.assertTrue(result["coverage_equal"])
            self.assertTrue(result["artifact_exact"])
            self.assertEqual(0, cli_result())

            path.write_text(
                rendered.replace(
                    "current; exposure=internal_or_special;",
                    "CORRUPTED EVIDENCE;",
                    1,
                ),
                encoding="utf-8",
            )
            result = audit.review_coverage(payload, path)
            self.assertFalse(result["coverage_equal"])
            self.assertFalse(result["artifact_exact"])
            self.assertEqual(1, cli_result())

            path.write_text(
                rendered.replace(
                    payload["glossary_sha256"],
                    "0" * 64,
                    1,
                ),
                encoding="utf-8",
            )
            result = audit.review_coverage(payload, path)
            self.assertFalse(result["coverage_equal"])
            self.assertFalse(result["artifact_exact"])
            self.assertEqual(1, cli_result())

            path.write_text(
                rendered
                + "| `monster:NOT_A_VALID_ENUM` | forged | keep |\n",
                encoding="utf-8",
            )
            result = audit.review_coverage(payload, path)
            self.assertFalse(result["coverage_equal"])
            self.assertFalse(result["artifact_exact"])
            self.assertEqual(1, cli_result())

    def test_reverse_duplicate_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.monster("alpha.yaml", "alpha", "同名")
            fixture.monster("beta.yaml", "beta", "同名")
            result = fixture.audit()
        self.assertTrue(any("reverse duplicate" in item for item in result.findings))

    def test_reverse_exception_is_exact_and_rejects_a_third_member(self) -> None:
        exception = {frozenset({"alpha", "beta"}): "intentional pair"}
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.monster("alpha.yaml", "alpha", "同名")
            fixture.monster("beta.yaml", "beta", "同名")
            self.assertEqual(
                (), fixture.audit(reverse_exceptions=exception).findings
            )
            fixture.monster("gamma.yaml", "gamma", "同名")
            result = fixture.audit(reverse_exceptions=exception)
        self.assertTrue(any("reverse duplicate" in item for item in result.findings))
        self.assertTrue(any("actual complete group" in item for item in result.findings))

    def test_nonunique_monsters_body_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.monster("boggart.yaml", "boggart", "博加特")
            fixture.en_monsters["boggart"] = "A boggart hides here."
            fixture.zh_monsters["boggart"] = "有个东西藏在这里。"
            result = fixture.audit()
        self.assertTrue(any(
            "monsters.txt mismatch" in item and "boggart" in item
            and "博加特" in item
            for item in result.findings
        ))

    def test_monster_name_inside_longer_english_word_does_not_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.monster("adder.yaml", "adder", "蝰蛇")
            fixture.en_monsters["adder"] = (
                "It climbs a ladder beside an adderstone with ease."
            )
            fixture.zh_monsters["adder"] = "它可以轻松爬上梯子，经过一块石头。"
            result = fixture.audit()
        self.assertEqual((), result.findings)

    def test_unexcepted_quote_mismatch_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.monster("boggart.yaml", "boggart", "博加特")
            fixture.en_quotes["boggart"] = "The boggart came closer."
            fixture.zh_quotes["boggart"] = "那东西走近了。"
            result = fixture.audit()
        self.assertTrue(any(
            "quotes.txt mismatch" in item and "博加特" in item
            for item in result.findings
        ))

    def test_valid_quote_exception_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.monster("jackal.yaml", "jackal", "豺狼")
            fixture.en_quotes["jackal"] = "A jackal was observed."
            fixture.zh_quotes["jackal"] = "有人观察到胡狼。"
            result = fixture.audit(
                quote_exceptions={"jackal": "natural-history animal name"}
            )
        self.assertEqual((), result.findings)

    def test_empty_and_stale_quote_exceptions_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = Fixture(Path(tmp))
            fixture.monster("jackal.yaml", "jackal", "豺狼")
            fixture.en_quotes["jackal"] = "A jackal was observed."
            fixture.zh_quotes["jackal"] = "有人观察到胡狼。"
            empty_reason = fixture.audit(quote_exceptions={"jackal": "  "})
            self.assertTrue(any(
                "reason is empty" in item for item in empty_reason.findings
            ))

            fixture.zh_quotes["jackal"] = "有人观察到豺狼。"
            no_longer_needed = fixture.audit(
                quote_exceptions={"jackal": "natural-history animal name"}
            )
            self.assertTrue(any(
                "now contains SSOT name" in item
                for item in no_longer_needed.findings
            ))

            absent_key = fixture.audit(
                quote_exceptions={"missing monster": "historical usage"}
            )
            self.assertTrue(any(
                "absent from monster inventory" in item
                for item in absent_key.findings
            ))

    def test_malformed_yaml_inventory_fails_closed(self) -> None:
        bad_contents = {
            "missing": "flags: []\n",
            "ambiguous": 'name: "first"\nname: "second"\nflags: []\n',
            "malformed flags": 'name: "first"\nflags: unique\n',
        }
        for label, content in bad_contents.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                source_dir = Path(tmp) / "source"
                mons_dir = source_dir / "dat" / "mons"
                mons_dir.mkdir(parents=True)
                (mons_dir / "bad.yaml").write_text(content, encoding="utf-8")
                with self.assertRaises(audit.AuditInputError):
                    audit._load_monster_definitions(str(source_dir))


if __name__ == "__main__":
    unittest.main(verbosity=2)
