#!/usr/bin/env python3

import json
import copy
import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / ".claude/scripts"
sys.path.insert(0, str(SCRIPTS))

from audit_monspell_behavior import (  # noqa: E402
    AuditError,
    CANDIDATE_INPUT_DOMAIN,
    CANDIDATE_PRODUCER_CONTRACT,
    EXPECTED_CANDIDATE_SCENARIOS,
    analyze_language,
    build_report,
    effective_entries,
    load_candidate_artifact,
)
from audit_monspell_phase0 import load_artifact  # noqa: E402


AUDIT = SCRIPTS / "audit_monspell_behavior.py"
TRACKED_REPORT = (
    ROOT / ".claude/data/message-overlay/monspell-behavior-report.json")


class MonspellBehaviorAuditTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.en_path = self.root / "en.json"
        self.zh_path = self.root / "zh.json"
        self.inventory_path = self.root / "inventory.json"
        self.manifest_path = self.root / "manifest.json"
        self.candidate_path = self.root / "candidate.json"
        self.candidate_anchor_path = self.root / "candidate-anchor.json"
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
            "cross domain cast": [" Gesture"],
            "fire beam  cast": ["VISUAL:effect"],
            "unreachable cast": [" Gesture"],
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
            "cross domain cast": [" Gesture"],
            "fire beam  cast": ["VISUAL:effect"],
            "unreachable cast": [" Gesture"],
            "zh only cast": ["手势"],
            "gesture fragment": [" ges"],
            "visual fragment": ["UAL:effect"],
            "gesture word": ["gesture"],
            "cycle child": ["@cycle cast@"],
        }
        self.unreachable_roots = {"unreachable cast"}
        self.roots = sorted(key for key in self.en if key.endswith(" cast"))
        self._write_inputs()

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def _artifact(entries, localized=False, source_overrides=None):
        directory = "database/zh/" if localized else "database/"
        default_source = directory + "monspell.txt"
        source_overrides = source_overrides or {}
        source_names = sorted({
            source_overrides.get(key, default_source) for key in entries
        })
        source_indexes = {
            source: index for index, source in enumerate(source_names)
        }
        artifact_entries = []
        for ordinal, key in enumerate(sorted(entries)):
            source = source_overrides.get(key, default_source)
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
                        "load_index": source_indexes[source],
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
                "load_index": source_indexes[source],
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
            "sources": [
                {
                    "source_name": source,
                    "load_index": index,
                    "normalized_utf8": "fixture",
                }
                for index, source in enumerate(source_names)
            ],
            "entries": artifact_entries,
        }

    @staticmethod
    def _candidate_artifact(base_expressions):
        bases = sorted(set(base_expressions))
        lookup = {}
        for base in bases:
            canonical = base.lower()
            lookup.setdefault(canonical, set()).update(
                {"normal", "silent_unprefixed_fallback"})
            lookup.setdefault("unseen " + canonical, set()).add("unseen")
            lookup.setdefault("silent " + canonical, set()).add(
                "silent_prefixed")
        records = [
            {"expression": expression, "attempts": sorted(attempts)}
            for expression, attempts in sorted(lookup.items())
        ]
        return {
            "schema_version": 1,
            "domain": "monspell_candidate_lookup",
            "completeness": "closed_world_upper_bound",
            "valid": True,
            "diagnostic": None,
            "input_domain": dict(CANDIDATE_INPUT_DOMAIN),
            "counts": {
                "monster_types": 1,
                "spells": 1,
                "monster_tuples": 1,
                "monster_spell_tuples": 1,
                "scenarios": len(EXPECTED_CANDIDATE_SCENARIOS),
                "base_expressions": len(bases),
                "lookup_expressions": len(records),
                "lookup_attempts": sum(
                    len(record["attempts"]) for record in records),
            },
            "scenarios": copy.deepcopy(list(EXPECTED_CANDIDATE_SCENARIOS)),
            "base_expressions": bases,
            "lookup_expressions": records,
        }

    def _write_inputs(self):
        self.roots = sorted(key for key in self.en if key.endswith(" cast"))
        self.en_path.write_text(json.dumps(self._artifact(
            self.en, source_overrides={
                "cross domain cast": "database/shouts.txt",
            })), encoding="utf-8")
        self.zh_path.write_text(
            json.dumps(self._artifact(
                self.zh, localized=True, source_overrides={
                    "cross domain cast": "database/zh/shouts.txt",
                }), ensure_ascii=False),
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
        candidate_bases = [
            key for key in sorted(set(self.roots) | {"zh only cast"})
            if key not in self.unreachable_roots
            and key != "fire beam  cast"
        ]
        candidate_bases.append("${beam_short_name} beam  cast")
        candidate = self._candidate_artifact(candidate_bases)
        self.candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        self.candidate_anchor_path.write_text(json.dumps({
            "schema_version": 1,
            "domain": "monspell_candidate_lookup",
            "artifact_sha256": hashlib.sha256(
                self.candidate_path.read_bytes()).hexdigest(),
            "counts": candidate["counts"],
            "producer_contract": CANDIDATE_PRODUCER_CONTRACT,
        }), encoding="utf-8")

    def report(self):
        return build_report(self.en_path, self.zh_path, self.inventory_path,
                            self.manifest_path, self.candidate_path,
                            self.candidate_anchor_path)

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
        self.assertEqual(report["analysis_completeness"],
                         "SOUND_CLOSED_WORLD_UPPER_BOUND")
        self.assertTrue(report["universe"]["candidate_key_containment_proven"])
        self.assertTrue(report["universe"]["runtime_reachability_proven"])
        self.assertEqual(report["universe"]["reachability_kind"],
                         "SOUND_UPPER_BOUND_NOT_EXACT")
        self.assertFalse(report["phase2_ready"])
        self.assertNotIn("candidate key containment is not proven",
                         report["phase2_blockers"])
        self.assertNotIn("runtime reachability is not proven",
                         report["phase2_blockers"])
        self.assertEqual(report["phase2_ready"],
                         not report["phase2_blockers"])

    def test_candidate_join_reports_unreachable_cross_domain_symbol_and_presence(self):
        report = self.report()
        universe = report["universe"]
        self.assertIn("unreachable cast",
                      universe["inventory_unreachable_roots"])
        self.assertNotIn("unreachable cast", universe["runtime_roots"])
        self.assertIn("fire beam  cast", universe["runtime_roots"])

        candidate = report["candidate_lookup"]
        self.assertEqual(
            [item["canonical_key"]
             for item in candidate["language_only_hits"]["zh_only"]],
            ["zh only cast"])
        self.assertEqual(candidate["language_only_hits"]["en_only"], [])
        self.assertFalse(candidate["presence_parity_proven"])
        self.assertTrue(candidate["source_parity_proven"])
        self.assertEqual(candidate["source_parity_mismatch"], [])

        for language in ("en", "zh"):
            cross = candidate[language]["cross_domain_hits"]
            self.assertEqual(
                [item["canonical_key"] for item in cross],
                ["cross domain cast"])
            self.assertEqual(cross[0]["source"], "database/shouts.txt")
            symbols = candidate[language]["symbol_matches"]
            self.assertEqual(len(symbols), 1)
            self.assertEqual(symbols[0]["matched_keys"], ["fire beam  cast"])
            self.assertEqual(symbols[0]["attempts"],
                             ["normal", "silent_unprefixed_fallback"])
            self.assertEqual(candidate[language]["symbol_match_key_count"], 1)

        self.assertEqual(
            [item["requested_root"]
             for item in report["locale_presence_mismatch"]],
            ["zh only cast"])
        self.assertIn("EN/ZH behavior parity is not proven",
                      report["phase2_blockers"])

    def test_candidate_validator_rejects_malformed_order_counts_markers_attempts(self):
        base = json.loads(self.candidate_path.read_text(encoding="utf-8"))
        cases = {}

        malformed = copy.deepcopy(base)
        malformed["scenarios"][0]["category_bits"] = 999
        cases["scenario category"] = malformed

        malformed = copy.deepcopy(base)
        del malformed["scenarios"][-1]
        malformed["counts"]["scenarios"] -= 1
        cases["scenario deleted"] = malformed

        malformed = copy.deepcopy(base)
        malformed["scenarios"][0], malformed["scenarios"][1] = (
            malformed["scenarios"][1], malformed["scenarios"][0])
        cases["scenario replaced order"] = malformed

        malformed = copy.deepcopy(base)
        malformed["scenarios"][0]["visible_beam"] = False
        cases["scenario boolean downgrade"] = malformed

        malformed = copy.deepcopy(base)
        malformed["base_expressions"] = list(
            reversed(malformed["base_expressions"]))
        cases["base sorting"] = malformed

        malformed = copy.deepcopy(base)
        malformed["lookup_expressions"] = list(
            reversed(malformed["lookup_expressions"]))
        cases["lookup sorting"] = malformed

        malformed = copy.deepcopy(base)
        malformed["counts"]["lookup_expressions"] += 1
        cases["lookup count"] = malformed

        malformed = self._candidate_artifact(
            ["${beam_short_name}${beam_short_name} cast"])
        cases["duplicate marker"] = malformed

        malformed = copy.deepcopy(base)
        malformed["lookup_expressions"][0]["attempts"] = ["unknown"]
        malformed["counts"]["lookup_attempts"] = sum(
            len(record["attempts"])
            for record in malformed["lookup_expressions"])
        cases["unknown attempt"] = malformed

        malformed = copy.deepcopy(base)
        record = next(
            item for item in malformed["lookup_expressions"]
            if len(item["attempts"]) == 2)
        record["attempts"].reverse()
        cases["attempt sorting"] = malformed

        malformed = copy.deepcopy(base)
        malformed["lookup_expressions"][0]["expression"] = "Uppercase cast"
        cases["production lowercase"] = malformed

        malformed = copy.deepcopy(base)
        malformed["input_domain"]["spells"] = {"unexpected": True}
        cases["input domain"] = malformed

        for name, artifact in cases.items():
            with self.subTest(name=name):
                path = self.root / f"malformed-{name.replace(' ', '-')}.json"
                path.write_text(json.dumps(artifact), encoding="utf-8")
                with self.assertRaises(AuditError):
                    load_candidate_artifact(path)

    def test_candidate_validator_proves_base_to_lookup_closure(self):
        base = json.loads(self.candidate_path.read_text(encoding="utf-8"))
        cases = {}

        malformed = copy.deepcopy(base)
        del malformed["lookup_expressions"][0]
        malformed["counts"]["lookup_expressions"] -= 1
        malformed["counts"]["lookup_attempts"] = sum(
            len(record["attempts"])
            for record in malformed["lookup_expressions"])
        cases["single lookup deleted with counts"] = malformed

        malformed = copy.deepcopy(base)
        malformed["lookup_expressions"].append({
            "expression": "zzzz extra cast",
            "attempts": ["normal"],
        })
        malformed["counts"]["lookup_expressions"] += 1
        malformed["counts"]["lookup_attempts"] += 1
        cases["extra lookup with counts"] = malformed

        malformed = copy.deepcopy(base)
        record = malformed["lookup_expressions"][0]
        record["attempts"] = ["unseen"]
        malformed["counts"]["lookup_attempts"] = sum(
            len(item["attempts"])
            for item in malformed["lookup_expressions"])
        cases["legal but wrong attempt"] = malformed

        for name, artifact in cases.items():
            with self.subTest(name=name):
                path = self.root / f"closure-{name.replace(' ', '-')}.json"
                path.write_text(json.dumps(artifact), encoding="utf-8")
                with self.assertRaises(AuditError):
                    load_candidate_artifact(path)

        collision = self._candidate_artifact(["foo", "silent foo"])
        collision_path = self.root / "collision.json"
        collision_path.write_text(json.dumps(collision), encoding="utf-8")
        loaded = load_candidate_artifact(collision_path)
        record = next(
            item for item in loaded.lookup_expressions
            if item["expression"] == "silent foo")
        self.assertEqual(
            record["attempts"],
            ["normal", "silent_prefixed", "silent_unprefixed_fallback"])

        collision["lookup_expressions"][
            collision["lookup_expressions"].index(record)
        ]["attempts"] = ["normal", "silent_unprefixed_fallback"]
        collision["counts"]["lookup_attempts"] -= 1
        collision_path.write_text(json.dumps(collision), encoding="utf-8")
        with self.assertRaises(AuditError):
            load_candidate_artifact(collision_path)

    def test_candidate_anchor_rejects_self_consistent_truncation(self):
        candidate = json.loads(
            self.candidate_path.read_text(encoding="utf-8"))
        removed_base = next(
            expression for expression in candidate["base_expressions"]
            if not expression.startswith(("silent ", "unseen ")))
        candidate["base_expressions"].remove(removed_base)
        candidate["lookup_expressions"] = [
            record for record in candidate["lookup_expressions"]
            if record["expression"] not in {
                removed_base.lower(),
                "silent " + removed_base.lower(),
                "unseen " + removed_base.lower(),
            }
        ]
        candidate["counts"]["base_expressions"] -= 1
        candidate["counts"]["lookup_expressions"] = len(
            candidate["lookup_expressions"])
        candidate["counts"]["lookup_attempts"] = sum(
            len(record["attempts"])
            for record in candidate["lookup_expressions"])
        self.candidate_path.write_text(json.dumps(candidate), encoding="utf-8")
        load_candidate_artifact(self.candidate_path)
        with self.assertRaisesRegex(
                AuditError, "does not match tracked anchor"):
            self.report()

    def test_candidate_anchor_schema_and_digest_are_strict(self):
        base = json.loads(
            self.candidate_anchor_path.read_text(encoding="utf-8"))
        cases = {}

        malformed = copy.deepcopy(base)
        malformed["unknown"] = True
        cases["unknown field"] = malformed

        malformed = copy.deepcopy(base)
        malformed["producer_contract"] = "different producer"
        cases["producer contract"] = malformed

        malformed = copy.deepcopy(base)
        malformed["counts"]["base_expressions"] += 1
        cases["count mismatch"] = malformed

        malformed = copy.deepcopy(base)
        malformed["artifact_sha256"] = "0" * 64
        cases["digest mismatch"] = malformed

        for name, anchor in cases.items():
            with self.subTest(name=name):
                self.candidate_anchor_path.write_text(
                    json.dumps(anchor), encoding="utf-8")
                with self.assertRaises(AuditError):
                    self.report()

    def test_source_parity_mismatch_is_reported(self):
        self.zh_path.write_text(
            json.dumps(self._artifact(
                self.zh, localized=True, source_overrides={
                    "cross domain cast": "database/zh/godspeak.txt",
                }), ensure_ascii=False),
            encoding="utf-8")
        report = self.report()
        self.assertFalse(report["candidate_lookup"]["source_parity_proven"])
        self.assertEqual(
            [item["canonical_key"] for item in
             report["candidate_lookup"]["source_parity_mismatch"]],
            ["cross domain cast"])

    def test_structured_runtime_uses_metadata_and_covers_negative_variants(self):
        en = load_artifact(self.en_path)
        zh = load_artifact(self.zh_path)
        catalog = {
            ("locale mismatch cast", 0): {
                "_entry_mode": "CANDIDATE",
                "stable_id": "fixture.gesture",
                "line_metadata": [{
                    "sensory": "PLAIN",
                    "behavior": {
                        "implies_gesture": True,
                        "audible": False,
                    },
                }],
                "materialization_cases": [],
            },
            ("locale mismatch cast", 1): {
                "_entry_mode": "CANDIDATE",
                "stable_id": "fixture.negative-one",
                "line_metadata": [{
                    "sensory": "PLAIN",
                    "behavior": {
                        "implies_gesture": False,
                        "audible": False,
                    },
                }],
                "materialization_cases": [],
            },
            ("locale mismatch cast", 2): {
                "_entry_mode": "CANDIDATE",
                "stable_id": "fixture.negative-two",
                "line_metadata": [{
                    "sensory": "PLAIN",
                    "behavior": {
                        "implies_gesture": False,
                        "audible": False,
                    },
                }],
                "materialization_cases": [],
            },
            ("none cast", 0): {
                "_entry_mode": "CANDIDATE",
                "stable_id": "fixture.negative",
                "line_metadata": [
                    {
                        "sensory": "PLAIN",
                        "behavior": {
                            "implies_gesture": False,
                            "audible": False,
                        },
                    },
                    {
                        "sensory": "VISUAL",
                        "behavior": {
                            "implies_gesture": False,
                            "audible": False,
                        },
                    },
                ],
                "materialization_cases": [],
            },
        }
        roots = ["locale mismatch cast", "none cast"]
        en_runtime = analyze_language(
            "en", roots, effective_entries(en, None, "en"), catalog)
        zh_runtime = analyze_language(
            "zh", roots, effective_entries(en, zh, "zh"), catalog)
        self.assertEqual(
            en_runtime["predicate_roots"]["GESTURE"],
            ["locale mismatch cast"])
        self.assertEqual(
            zh_runtime["predicate_roots"]["GESTURE"],
            ["locale mismatch cast"])
        self.assertEqual(
            [item["variant_ordinal"] for item in
             en_runtime["structured_variant_metadata"]
             if item["requested_root"] == "locale mismatch cast"],
            [0, 1, 2])
        self.assertEqual(
            [item["variant_ordinal"] for item in
             zh_runtime["structured_variant_metadata"]
             if item["requested_root"] == "locale mismatch cast"],
            [0, 1, 2])
        self.assertTrue(all(
            item["complete"]
            for item in en_runtime["structured_variant_metadata"]))
        expected_occurrences = {
            ("locale mismatch cast", 0, "GESTURE"),
            ("none cast", 0, "VISUAL_APPLICABILITY"),
            ("none cast", 0, "VISUAL_CHANNEL"),
        }
        for runtime in (en_runtime, zh_runtime):
            structured_roots = {"locale mismatch cast", "none cast"}
            effective = [
                item for item in runtime["occurrences"]
                if item["requested_root"] in structured_roots
                and item["behavior"] != "UNANALYSABLE"
            ]
            self.assertEqual(len(effective), 3)
            self.assertTrue(all(
                item["phase"] == "STRUCTURED_METADATA"
                for item in effective))
            self.assertEqual({
                (item["requested_root"],
                 item["top_locator"]["variant_ordinal"],
                 item["behavior"])
                for item in effective
            }, expected_occurrences)
            self.assertEqual(
                sum(item["behavior"] == "GESTURE" for item in effective), 1)
            self.assertEqual(
                sum(item["behavior"] != "GESTURE" for item in effective), 2)
            self.assertEqual(len(runtime["structured_variant_metadata"]), 4)
        self.assertIn(
            "none cast",
            en_runtime["predicate_roots"]["VISUAL_APPLICABILITY"])
        self.assertIn(
            "none cast", en_runtime["predicate_roots"]["VISUAL_CHANNEL"])

    def test_deterministic_output_and_check(self):
        command = [
            sys.executable, str(AUDIT),
            "--english-artifact", str(self.en_path),
            "--localized-artifact", str(self.zh_path),
            "--inventory", str(self.inventory_path),
            "--manifest", str(self.manifest_path),
            "--candidate-artifact", str(self.candidate_path),
            "--candidate-anchor", str(self.candidate_anchor_path),
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

    def test_tracked_phase2_coverage_contract(self):
        report = json.loads(TRACKED_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(
            report["coverage"]["canonical_structured_variant_metadata_units"],
            49)
        self.assertEqual(
            report["coverage"][
                "canonical_structured_variant_metadata_complete"],
            49)
        self.assertEqual(
            report["coverage"][
                "per_language_structured_variant_verification_units"],
            98)
        self.assertEqual(
            report["coverage"][
                "per_language_structured_variant_verification_complete"],
            98)
        self.assertEqual(
            report["coverage"]["remaining_legacy_behavior_occurrences"],
            0)
        self.assertEqual(report["locale_behavior_mismatch"], [])
        self.assertEqual(
            [item["requested_root"]
             for item in report["locale_behavior_inconclusive"]],
            ["vanquished vanguard nergalle cast"])


if __name__ == "__main__":
    unittest.main()
