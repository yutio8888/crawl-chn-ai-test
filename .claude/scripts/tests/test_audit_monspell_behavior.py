#!/usr/bin/env python3

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude/scripts"
sys.path.insert(0, str(SCRIPTS))

from audit_monspell_behavior import build_report  # noqa: E402


AUDIT = SCRIPTS / "audit_monspell_behavior.py"


class MonspellBehaviorAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.en_path = self.root / "en.json"
        self.zh_path = self.root / "zh.json"
        self.inventory_path = self.root / "inventory.json"
        self.manifest_path = self.root / "manifest.json"
        self.output_path = self.root / "report.json"

        self.en = {
            "boundary gesture cast": ["@gesture fragment@tures."],
            "boundary visual cast": ["VIS@visual fragment@"],
            "duplicate marker cast": ["@gesture word@ and @gesture word@"],
            "random gesture cast": ["[Gesture|chant]"],
            "random channel cast": ["[VISUAL|SOUND]:effect"],
            "empty fallback cast": [" gestures."],
            "localized only cast": ["plain"],
            "none cast": ["__NONE"],
            "lua cast": ["{{ return 'gesture' }}"],
            "cycle cast": ["@cycle child@"],
            "dynamic prefix cast": ["@channel@:effect"],
            "corrupt cast": "CORRUPT",
            "locale mismatch cast": [" gestures."],
            "gesture fragment": [" ges"],
            "visual fragment": ["UAL:effect"],
            "gesture word": ["gesture"],
            "cycle child": ["@cycle cast@"],
        }
        self.zh = {
            "boundary gesture cast": ["@gesture fragment@tures."],
            "boundary visual cast": ["VIS@visual fragment@"],
            "duplicate marker cast": ["@gesture word@ and @gesture word@"],
            "random gesture cast": ["[Gesture|chant]"],
            "random channel cast": ["[VISUAL|SOUND]:effect"],
            "empty fallback cast": None,
            "localized only cast": ["@localized gesture@"],
            "localized gesture": ["手势"],
            "none cast": ["__NONE"],
            "lua cast": ["{{ return '手势' }}"],
            "cycle cast": ["@cycle child@"],
            "dynamic prefix cast": ["@channel@:effect"],
            "corrupt cast": "CORRUPT",
            "locale mismatch cast": ["吟唱。"],
            "gesture fragment": [" ges"],
            "visual fragment": ["UAL:effect"],
            "gesture word": ["gesture"],
            "cycle child": ["@cycle cast@"],
        }
        self.roots = sorted(key for key in self.en if key.endswith(" cast"))
        self._write_inputs()

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _artifact(entries, localized=False):
        directory = "database/zh/" if localized else "database/"
        source = directory + "monspell.txt"
        artifact_entries = []
        for ordinal, key in enumerate(sorted(entries)):
            patterns = entries[key]
            empty = patterns is None
            corrupt = patterns == "CORRUPT"
            weighted_patterns = [] if empty or corrupt else [
                item if isinstance(item, tuple) else (10, item)
                for item in patterns
            ]
            variants = [] if empty or corrupt else [
                {
                    "locator": {"canonical_key": key, "variant_ordinal": index},
                    "provenance": {
                        "source_name": source,
                        "load_index": 0,
                        "definition_ordinal": ordinal,
                    },
                    "weight": weight,
                    "raw_pattern": pattern,
                }
                for index, (weight, pattern) in enumerate(weighted_patterns)
            ]
            raw_body = "" if empty else (
                "broken\n" if corrupt else "\n\n".join(
                    ((f"w:{weight}\n" if weight != 10 else "") + pattern)
                    for weight, pattern in weighted_patterns) + "\n")
            provenance = {
                "source_name": source,
                "load_index": 0,
                "definition_ordinal": ordinal,
            }
            artifact_entries.append({
                "canonical_key": key,
                "effective_provenance": provenance,
                "raw_body": raw_body,
                "source_history": [provenance],
                "variants": variants,
                "parse_error": "fixture parse error" if corrupt else None,
                "body_empty": empty,
            })
        return {
            "schema_version": 1,
            "database_name": "speak",
            "source_directory": directory,
            "sources": [{
                "source_name": source,
                "load_index": 0,
                "normalized_utf8": "fixture",
            }],
            "entries": artifact_entries,
        }

    def _write_inputs(self):
        self.roots = sorted(key for key in self.en if key.endswith(" cast"))
        self.en_path.write_text(json.dumps(self._artifact(self.en)), encoding="utf-8")
        self.zh_path.write_text(
            json.dumps(self._artifact(self.zh, localized=True), ensure_ascii=False),
            encoding="utf-8")
        inventory_entries = [
            {
                "key": key,
                "defined_in_monspell": True,
                "variants": [],
                "entry_text_fingerprint": f"fixture-{index}",
            }
            for index, key in enumerate(self.roots)
        ]
        self.inventory_path.write_text(json.dumps({
            "schema_version": 1,
            "semantic_fingerprint": "fixture-semantic",
            "entries": inventory_entries,
            "closure": {"additional_nodes": []},
        }), encoding="utf-8")
        self.manifest_path.write_text(json.dumps({
            "schema_version": 1,
            "domain": "monspell",
            "inventory_semantic_fingerprint": "fixture-semantic",
            "supported_languages": ["en", "zh"],
            "entries": [],
            "tombstones": [],
        }), encoding="utf-8")

    def report(self):
        return build_report(self.en_path, self.zh_path, self.inventory_path,
                            self.manifest_path)

    @staticmethod
    def _behaviors(report, language, root):
        return {
            item["behavior"] for item in report["languages"][language]["occurrences"]
            if item["requested_root"] == root
        }

    def test_recursive_parent_child_boundaries_and_duplicate_markers(self):
        report = self.report()
        self.assertIn("GESTURE", self._behaviors(
            report, "en", "boundary gesture cast"))
        self.assertIn("VISUAL_APPLICABILITY", self._behaviors(
            report, "en", "boundary visual cast"))
        self.assertIn("VISUAL_CHANNEL", self._behaviors(
            report, "en", "boundary visual cast"))
        occurrence = next(
            item for item in report["languages"]["en"]["occurrences"]
            if item["requested_root"] == "duplicate marker cast"
            and item["behavior"] == "GESTURE")
        self.assertEqual(occurrence["recursive_provenance"], [
            {"canonical_key": "gesture word", "variant_ordinal": 0},
        ])

    def test_random_phase_separation(self):
        report = self.report()
        self.assertIn("GESTURE", self._behaviors(
            report, "en", "random gesture cast"))
        channel = self._behaviors(report, "en", "random channel cast")
        self.assertTrue({"VISUAL_APPLICABILITY", "VISUAL_CHANNEL",
                         "SOUND_LIKE_CHANNEL"}.issubset(channel))

    def test_effective_merge_empty_fallback_and_localized_only_child(self):
        report = self.report()
        self.assertIn("GESTURE", self._behaviors(
            report, "zh", "empty fallback cast"))
        self.assertIn("GESTURE", self._behaviors(
            report, "zh", "localized only cast"))
        counts = report["languages"]["zh"]["effective_source_counts"]
        self.assertEqual(counts["english_fallback"], 1)

    def test_none_lua_cycle_and_dynamic_prefix_fail_closed(self):
        report = self.report()
        self.assertEqual(self._behaviors(report, "en", "none cast"), set())
        for key in ("lua cast", "cycle cast", "dynamic prefix cast",
                    "corrupt cast"):
            self.assertEqual(self._behaviors(report, "en", key), {"UNANALYSABLE"})

    def test_weight_reachability_matches_cumulative_production_bounds(self):
        self.en.update({
            "negative leading cast": [(-5, " Gesture"), (10, "plain")],
            "zero boundary cast": [(5, "plain"), (0, " Gesture")],
            "negative dip cast": [(10, "plain"), (-9, " Gesture"),
                                  (10, " Point")],
            "nonpositive total cast": [(-1, " Gesture"), (1, "plain")],
            "recursive weight cast": ["@weighted child@"],
            "recursive nonpositive cast": ["@nonpositive child@"],
            "weighted child": [(-5, " Gesture"), (10, "plain")],
            "nonpositive child": [(-1, " Gesture"), (1, "plain")],
        })
        self._write_inputs()
        report = self.report()
        self.assertNotIn("GESTURE", self._behaviors(
            report, "en", "negative leading cast"))
        self.assertNotIn("GESTURE", self._behaviors(
            report, "en", "zero boundary cast"))
        dip = [item for item in report["languages"]["en"]["occurrences"]
               if item["requested_root"] == "negative dip cast"
               and item["behavior"] == "GESTURE"]
        self.assertEqual([item["top_locator"]["variant_ordinal"] for item in dip], [2])
        self.assertEqual(self._behaviors(
            report, "en", "nonpositive total cast"), {"UNANALYSABLE"})
        self.assertNotIn("GESTURE", self._behaviors(
            report, "en", "recursive weight cast"))
        self.assertEqual(self._behaviors(
            report, "en", "recursive nonpositive cast"), {"UNANALYSABLE"})

    def test_marker_balance_depth_and_replacement_limits_fail_closed(self):
        self.en["unbalanced cast"] = ["before @broken"]
        self.en["replacement boundary cast"] = ["@slot@" * 100]
        self.en["replacement limit cast"] = ["@slot@" * 101]
        self.en["depth limit cast"] = ["@depth 1@"]
        for depth in range(1, 10):
            self.en[f"depth {depth}"] = [f"@depth {depth + 1}@"]
        self.en["depth 10"] = ["plain"]
        self.en["missing leaf depth cast"] = ["@missing depth 1@"]
        for depth in range(1, 9):
            self.en[f"missing depth {depth}"] = [f"@missing depth {depth + 1}@"]
        self.en["missing depth 9"] = ["@actor@"]
        self.en["missing leaf boundary cast"] = ["@safe depth 1@"]
        for depth in range(1, 8):
            self.en[f"safe depth {depth}"] = [f"@safe depth {depth + 1}@"]
        self.en["safe depth 8"] = ["@actor@"]
        self._write_inputs()
        report = self.report()
        for key in ("unbalanced cast", "replacement limit cast",
                    "depth limit cast", "missing leaf depth cast"):
            self.assertEqual(self._behaviors(report, "en", key),
                             {"UNANALYSABLE"})
        self.assertNotIn("UNANALYSABLE", self._behaviors(
            report, "en", "replacement boundary cast"))
        self.assertNotIn("UNANALYSABLE", self._behaviors(
            report, "en", "missing leaf boundary cast"))

    def test_dynamic_prefix_fragments_and_random_rescan_fail_closed(self):
        self.en.update({
            "mixed dynamic prefix cast": ["@channel@X:effect"],
            "boundary dynamic prefix cast": ["@channel fragment@:effect"],
            "repeated dynamic prefix cast": ["@channel fragment@@channel fragment@:effect"],
            "channel fragment": ["@channel@X"],
            "random rescan cast": ["[[VISUAL|SOUND]|plain]:effect"],
        })
        self._write_inputs()
        report = self.report()
        for key in ("mixed dynamic prefix cast", "boundary dynamic prefix cast",
                    "repeated dynamic prefix cast", "random rescan cast"):
            self.assertEqual(self._behaviors(report, "en", key),
                             {"UNANALYSABLE"})

    def test_unanalysable_locale_is_inconclusive_not_confirmed_mismatch(self):
        self.en["inconclusive cast"] = [" Gesture"]
        self.zh["inconclusive cast"] = ["@channel@X:正文"]
        self._write_inputs()
        report = self.report()
        confirmed = {item["requested_root"]
                     for item in report["locale_behavior_mismatch"]}
        inconclusive = {item["requested_root"]
                        for item in report["locale_behavior_inconclusive"]}
        self.assertNotIn("inconclusive cast", confirmed)
        self.assertIn("inconclusive cast", inconclusive)

    def test_locale_mismatch_and_phase2_gate(self):
        report = self.report()
        mismatch = {item["requested_root"]: item
                    for item in report["locale_behavior_mismatch"]}
        self.assertIn("locale mismatch cast", mismatch)
        self.assertEqual(mismatch["locale mismatch cast"]["en_predicates"],
                         ["GESTURE"])
        self.assertEqual(mismatch["locale mismatch cast"]["zh_predicates"], [])
        self.assertEqual(report["analysis_completeness"], "LOWER_BOUND")
        self.assertFalse(report["universe"]["candidate_key_containment_proven"])
        self.assertFalse(report["phase2_ready"])

    def test_deterministic_output_and_check(self):
        command = [
            sys.executable, str(AUDIT),
            "--english-artifact", str(self.en_path),
            "--localized-artifact", str(self.zh_path),
            "--inventory", str(self.inventory_path),
            "--manifest", str(self.manifest_path),
            "--output", str(self.output_path),
        ]
        generated = subprocess.run(command, text=True, capture_output=True,
                                   check=False)
        self.assertEqual(generated.returncode, 0, generated.stderr)
        first = self.output_path.read_bytes()
        checked = subprocess.run(command + ["--check"], text=True,
                                 capture_output=True, check=False)
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertEqual(first, self.output_path.read_bytes())
        self.output_path.write_text("{}\n", encoding="utf-8")
        drift = subprocess.run(command + ["--check"], text=True,
                               capture_output=True, check=False)
        self.assertEqual(drift.returncode, 1)
        self.assertIn("report drift", drift.stderr)


if __name__ == "__main__":
    unittest.main()
