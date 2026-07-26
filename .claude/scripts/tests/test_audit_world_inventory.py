#!/usr/bin/env python3

import importlib.util
import tempfile
import unittest
from pathlib import Path


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "audit_world_inventory.py"
SPEC = importlib.util.spec_from_file_location("audit_world_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def review_header():
    return (
        "| " + " | ".join(MODULE.REVIEW_COLUMNS) + " |\n"
        + "|" + "|".join("---" for _ in MODULE.REVIEW_COLUMNS) + "|\n"
    )


def review_card(identity, conclusion="keep", overrides=None):
    card = {column: "reviewed evidence" for column in MODULE.REVIEW_COLUMNS}
    card.update({
        "identity": f"`{identity}`",
        "lifecycle": "current",
        "en": "English",
        "zh": "中文",
        "proposed_translation": "候选译文",
        "adopted_translation": "采用译文",
        "rejected_alternatives": "not applicable",
        "confidence": "high: direct production evidence",
        "deferred_follow_up": "not applicable",
        "re_entry_conditions": "not applicable",
        "conclusion": conclusion,
    })
    card.update(overrides or {})
    return "| " + " | ".join(
        card[column] for column in MODULE.REVIEW_COLUMNS
    ) + " |\n"


class WorldInventoryUnitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = MODULE.build_inventory()

    def write_des(self, text):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "fixture.des"
        path.write_text(text, encoding="utf-8")
        return path

    def test_active_enums_exclude_aliases_and_keep_sentinels(self):
        branches, branch_aliases = MODULE.enum_identities(
            MODULE.BRANCH_ENUM, "branch_type", "BRANCH_", "NUM_BRANCHES"
        )
        features, feature_aliases = MODULE.enum_identities(
            MODULE.FEATURE_ENUM, "dungeon_feature_type",
            "DNGN_", "NUM_FEATURES"
        )
        branch_ids = {row["identity"] for row in branches}
        feature_ids = {row["identity"] for row in features}
        self.assertNotIn("BRANCH_FIRST_NON_DUNGEON", branch_ids)
        self.assertTrue(branch_aliases)
        self.assertIn("DNGN_UNSEEN", feature_ids)
        self.assertNotIn("NUM_FEATURES", feature_ids)
        self.assertIsInstance(feature_aliases, list)

    def test_branch_and_feature_set_order_proofs_are_complete(self):
        proof = self.payload["proof"]
        self.assertEqual(
            proof["branches"]["enum_order"], proof["branches"]["data_order"]
        )
        self.assertEqual(
            set(proof["features"]["enum_order"]),
            set(proof["features"]["data_order"]),
        )
        self.assertEqual(
            len(proof["features"]["data_order"]),
            len(set(proof["features"]["data_order"])),
        )
        self.assertFalse(
            self.payload["violations"]["branch_enum_data_set_drift"]
        )
        self.assertFalse(
            self.payload["violations"]["feature_enum_data_set_drift"]
        )

    def test_shared_feature_names_and_vaultnames_do_not_merge_identities(self):
        features = [
            row for row in self.payload["rows"]
            if row["category"] == "feature"
        ]
        shared = [
            row for row in features
            if len(row["name_alias_group"]) > 1
            or len(row["vaultname_alias_group"]) > 1
        ]
        self.assertTrue(shared)
        self.assertEqual(
            len(features), len({row["identity"] for row in features})
        )

    def test_physical_textdb_reports_duplicate_and_stale_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "db.txt"
            path.write_text(
                "%%%%\nKnown\n甲\n%%%%\nStale\n乙\n%%%%\nKnown\n丙\n",
                encoding="utf-8",
            )
            db = MODULE.physical_db(path)
        self.assertEqual(["known"], db["duplicates"])
        self.assertEqual({"Known", "Stale"}, set(db["raw"]))

    def test_all_supported_des_producer_classes_are_extracted(self):
        path = self.write_des(
            """lua {{
function demo()
  crawl.mpr("mpr")
  crawl.formatted_mpr("formatted")
  crawl.yesno("yes?")
  crawl.take_note("note")
  local a = timed_msg {
    initmsg = {"init one", "init two"},
    finalmsg = "final",
    ranges = {"near", "far"},
    messages = {"message"},
    range_msg_fmt = "hear {distance}",
    verb = "ringing", noisemaker = "bell"
  }
  local b = timed_marker { disappear = "gone", entity = "gate",
                           desc = "portal description" }
  local c = portal_desc { desc = "marker description",
                          toll_desc = "at a toll" }
  set_feature_name("rock_wall", "renamed wall")
end
}}
"""
        )
        rows = MODULE.scan_des_file(path, {})
        kinds = {row["sink_kind"] for row in rows}
        self.assertTrue({
            "crawl.mpr", "crawl.formatted_mpr", "crawl.yesno",
            "crawl.take_note", "initmsg", "finalmsg", "ranges", "messages",
            "range_msg_fmt", "verb", "noisemaker", "disappear", "entity",
            "desc", "toll_desc", "feature_rename",
        } <= kinds)

    def test_anchor_and_ordinal_are_stable_across_line_insertions(self):
        body = """{prefix}lua {{
function stable_anchor()
  crawl.mpr("one")
  crawl.mpr("two")
end
}}
"""
        first = MODULE.scan_des_file(self.write_des(body.format(prefix="")), {})
        second = MODULE.scan_des_file(
            self.write_des(body.format(prefix="\n\n# comment\n")), {}
        )
        first_suffixes = [
            row["identity"].split(":function:stable_anchor:", 1)[1]
            for row in first
        ]
        second_suffixes = [
            row["identity"].split(":function:stable_anchor:", 1)[1]
            for row in second
        ]
        self.assertEqual(first_suffixes, second_suffixes)
        self.assertEqual([1, 2], [
            int(row["identity"].rsplit(":", 1)[1]) for row in first
        ])

    def test_dynamic_unknown_and_protocol_boundaries_fail_visible(self):
        path = self.write_des(
            """lua {{
function boundary()
  NAME = "protocol"
  MARKER = "schema"
  crawl.mpr(runtime_message)
  crawl.message("unknown display sink")
end
}}
"""
        )
        rows = MODULE.scan_des_file(path, {})
        self.assertFalse(any(
            row.get("static_english") in {"protocol", "schema"} for row in rows
        ))
        unsupported = {row.get("unsupported") for row in rows}
        self.assertIn("dynamic direct display expression", unsupported)
        self.assertIn(
            "unknown display-like crawl sink: message", unsupported
        )

    def test_persistent_translation_and_untranslated_titles_fail_visible(self):
        path = self.write_des(
            """lua {{
function boundary()
  crawl.take_note(crawl.t_("Entered ") .. destination)
  crawl.mpr(string.format(crawl.t_("Welcome to %s!"), destination_title))
  crawl.mpr(string.format(crawl.t_("Found %s!"),
                           crawl.t_(translated_name)))
end
}}
"""
        )
        rows = MODULE.scan_des_file(path, {
            "entered ": "进入了",
            "welcome to %s!": "欢迎来到%s！",
            "found %s!": "发现了%s！",
        })
        note, untranslated, translated = rows
        self.assertIn("before storage", note["protocol_boundary_issue"])
        self.assertEqual(
            ["destination_title"],
            untranslated["untranslated_display_title_parameters"],
        )
        self.assertIn(
            "lacks late translation",
            untranslated["protocol_boundary_issue"],
        )
        self.assertEqual(
            ["translated_name"],
            translated["translated_dynamic_parameters"],
        )
        self.assertEqual(
            [], translated["untranslated_display_title_parameters"]
        )
        self.assertNotIn("protocol_boundary_issue", translated)
        empty_db = {"raw": {}, "duplicates": []}
        violations = MODULE.inventory_violations(
            rows,
            {"enum_order": [], "data_order": []},
            {"enum_order": [], "data_order": []},
            (empty_db, empty_db),
            (empty_db, empty_db),
        )
        self.assertEqual(
            {note["identity"], untranslated["identity"]},
            set(violations["protocol_display_boundary_issues"]),
        )

    def test_inner_crawl_translation_and_concatenated_field_use_exact_keys(self):
        source = {
            "translated key": "已翻译",
            "two fragments": "两段",
        }
        path = self.write_des(
            """lua {{
function exact()
  crawl.mpr(crawl.t_("translated key"))
  local p = timed_marker { disappear = "two " .. "fragments" }
end
}}
"""
        )
        rows = MODULE.scan_des_file(path, source)
        by_en = {row["static_english"]: row for row in rows}
        self.assertTrue(by_en["translated key"]["source_exact_match"])
        self.assertEqual("crawl.t_", by_en["translated key"][
            "late_translation_consumer"
        ])
        self.assertTrue(by_en["two fragments"]["source_exact_match"])
        self.assertEqual(["two ", "fragments"],
                         by_en["two fragments"]["literal_fragments"])

    def test_translation_wrapper_preserves_direct_sink_identity(self):
        raw = self.write_des(
            """lua {{
function same_slots()
  crawl.mpr("message")
  crawl.god_speaks("Ashenzari", "vision")
  crawl.mpr("round " .. round)
end
}}
"""
        )
        wrapped = self.write_des(
            """lua {{
function same_slots()
  crawl.mpr(crawl.t_("message"))
  crawl.god_speaks("Ashenzari", crawl.t_("vision"))
  crawl.mpr(string.format(crawl.t_("round %s"), round))
end
}}
"""
        )
        source = {"message": "消息", "vision": "幻象", "round %s": "第%s轮"}
        raw_rows = MODULE.scan_des_file(raw, source)
        wrapped_rows = MODULE.scan_des_file(wrapped, source)
        self.assertEqual(
            [row["identity"].split(":function:", 1)[1] for row in raw_rows],
            [row["identity"].split(":function:", 1)[1]
             for row in wrapped_rows],
        )
        self.assertEqual(
            [row["static_english"] for row in raw_rows[:2]],
            [row["static_english"] for row in wrapped_rows[:2]],
        )
        self.assertEqual(
            [None, None, None],
            [row["late_translation_consumer"] for row in raw_rows],
        )
        self.assertEqual(
            ["crawl.t_", "crawl.t_", "crawl.t_"],
            [row["late_translation_consumer"] for row in wrapped_rows],
        )
        self.assertEqual("round %s", wrapped_rows[2]["static_english"])
        self.assertIsNone(raw_rows[2]["static_english"])
        self.assertIn("round", wrapped_rows[2]["dynamic_parameters"])

    def test_exact_key_miss_and_placeholder_macro_drift(self):
        path = self.write_des(
            """lua {{
function drift()
  crawl.mpr("missing")
  crawl.mpr("Hello %s {entity}")
end
}}
"""
        )
        rows = MODULE.scan_des_file(
            path, {"hello %s {entity}": "你好 %d"}
        )
        by_en = {row["static_english"]: row for row in rows}
        self.assertFalse(by_en["missing"]["source_exact_match"])
        self.assertTrue(by_en["Hello %s {entity}"]["token_drift"])

    def test_diagnostic_slots_are_classified_exclusions(self):
        path = self.write_des(
            """lua {{
function validate()
  crawl.mpr("Error: invalid vault")
end
}}
"""
        )
        exclusions = []
        rows = MODULE.scan_des_file(path, {}, exclusions)
        self.assertEqual([], rows)
        self.assertEqual("diagnostic/error output", exclusions[0]["reason"])

    def test_translation_cleanup_and_runtime_key_parity_are_visible(self):
        violations = self.payload["violations"]
        self.assertEqual(
            [], violations["unexpected_zh_branch_description_keys"]
        )
        self.assertEqual(
            [], violations["unexpected_zh_feature_description_keys"]
        )
        for identity in (
            "branch:BRANCH_PANDEMONIUM:entry_message",
            "branch:BRANCH_VESTIBULE:entry_message",
            "branch:BRANCH_ZOT:entry_message",
        ):
            self.assertNotIn(
                identity, violations["missing_display_translations"]
            )
        bazaar = [
            row for row in self.payload["rows"]
            if row.get("static_english") == "flickering gateway to a bazaar"
        ]
        self.assertEqual(1, len(bazaar))
        self.assertTrue(bazaar[0]["source_exact_match"])

    def test_trim_fallback_and_initmsg_concatenation_match_runtime(self):
        path = self.write_des(
            """lua {{
function portal()
  local p = timed_msg {
    initmsg = {"first " .. "second", "trailing "},
    finalmsg = "done"
  }
end
}}
"""
        )
        rows = MODULE.scan_des_file(path, {
            "first second": "合并",
            "trailing": "去尾空白",
            "done": "完成",
        })
        by_en = {row["static_english"]: row for row in rows}
        self.assertEqual(
            {"first second", "trailing ", "done"}, set(by_en)
        )
        self.assertTrue(by_en["first second"]["source_exact_match"])
        self.assertTrue(by_en["trailing "]["source_exact_match"])
        self.assertTrue(by_en["trailing "]["source_trim_fallback"])

    def test_portal_desc_uses_feature_description_database(self):
        path = self.write_des(
            """lua {{
function portal()
  local marker = portal_desc { desc = "An open sea?" }
end
}}
"""
        )
        rows = MODULE.scan_des_file(
            path, {}, feature_desc_exact={"an open sea?": "一片开阔海域？"}
        )
        self.assertEqual(1, len(rows))
        self.assertTrue(rows[0]["source_exact_match"])
        self.assertEqual("一片开阔海域？", rows[0]["current_chinese"])

    def test_mechanics_and_protocol_paths_are_reviewable(self):
        branches = [row for row in self.payload["rows"]
                    if row["category"] == "branch"]
        features = [row for row in self.payload["rows"]
                    if row["category"] == "feature"]
        for row in branches:
            self.assertTrue(row["raw_producer"])
            self.assertTrue({
                "parent", "mindepth", "maxdepth", "numlevels", "flags",
                "entry_feature", "exit_feature", "escape_feature", "runes",
                "noise", "descent_parents",
            } <= set(row["mechanics"]))
            self.assertTrue(row["shortname_paths"]["required_consumer_refs"])
        for row in features:
            self.assertTrue(row["flags"])
            self.assertTrue(row["minimap"])
            self.assertTrue(row["behavior_evidence_refs"])
            self.assertTrue(
                row["protocol_identity"]["required_consumer_refs"]
            )

    def test_des_producer_universe_classifies_special_owners(self):
        universe = {
            row["producer"]: row
            for row in self.payload["scope"]["producer_universe"]
        }
        self.assertEqual(
            "included_player_display",
            universe["crawl.god_speaks"]["classification"],
        )
        for producer in ("tutorial_msg", "tutorial_hint"):
            self.assertEqual(
                "excluded_lookup_protocol_owned",
                universe[producer]["classification"],
            )
        self.assertFalse(
            self.payload["violations"]["unknown_des_producers"]
        )

    def test_every_portal_file_has_a_family_row_without_fixed_count(self):
        expected = {
            f"portal_family:{path.stem}"
            for path in (MODULE.DES_ROOT / "portals").glob("*.des")
        }
        actual = {
            row["identity"] for row in self.payload["rows"]
            if row["category"] == "portal_family"
        }
        self.assertEqual(expected, actual)

    def test_review_coverage_requires_bijection_and_terminal_conclusion(self):
        fixture = {"inventory_sha256": "a" * 64, "rows": [
            {"identity": "branch:BRANCH_A"},
            {"identity": "feature:DNGN_A"},
        ]}
        header = review_header()
        card_a = review_card("branch:BRANCH_A", "保留：正确")
        card_b = review_card("feature:DNGN_A", "adjust wording")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.md"
            path.write_text(
                f"Inventory-SHA256: {'a' * 64}\n\n"
                + header + card_a + card_b,
                encoding="utf-8",
            )
            coverage = MODULE.review_coverage(fixture, path)
            self.assertTrue(coverage["coverage_equal"])
            path.write_text(
                f"Inventory-SHA256: {'a' * 64}\n\n"
                + header + card_a
                + review_card(
                    "feature:DNGN_A", "insufficient evidence",
                    {
                        "proposed_translation": MODULE.PENDING_REVIEW,
                        "adopted_translation": MODULE.PENDING_REVIEW,
                        "rejected_alternatives": MODULE.PENDING_REVIEW,
                        "confidence": MODULE.PENDING_REVIEW,
                        "deferred_follow_up": MODULE.PENDING_REVIEW,
                        "re_entry_conditions": MODULE.PENDING_REVIEW,
                    },
                ),
                encoding="utf-8",
            )
            pending = MODULE.review_coverage(fixture, path)
            self.assertFalse(pending["coverage_equal"])
            self.assertEqual(
                ["feature:DNGN_A"],
                pending["invalid_terminal_conclusions"],
            )
            for column in coverage["required_columns"][1:]:
                broken_card = review_card(
                    "branch:BRANCH_A", "keep", {column: ""}
                )
                path.write_text(
                    f"Inventory-SHA256: {'a' * 64}\n\n"
                    + header + broken_card + card_b,
                    encoding="utf-8",
                )
                broken_field = MODULE.review_coverage(fixture, path)
                self.assertFalse(
                    broken_field["coverage_equal"], msg=column
                )
                self.assertIn(
                    "branch:BRANCH_A",
                    broken_field["missing_required_fields"],
                    msg=column,
                )
            for column in MODULE.REVIEW_DECISION_FIELDS:
                pending_card = review_card(
                    "branch:BRANCH_A", "keep",
                    {column: MODULE.PENDING_REVIEW},
                )
                path.write_text(
                    f"Inventory-SHA256: {'a' * 64}\n\n"
                    + header + pending_card + card_b,
                    encoding="utf-8",
                )
                pending_field = MODULE.review_coverage(fixture, path)
                self.assertFalse(pending_field["coverage_equal"], msg=column)
                self.assertIn(
                    column,
                    pending_field["invalid_decision_fields"][
                        "branch:BRANCH_A"
                    ],
                )
            path.write_text(
                f"Inventory-SHA256: {'a' * 64}\n\n"
                + header
                + review_card(
                    "branch:BRANCH_A", "keep",
                    {"confidence": "not applicable"},
                )
                + card_b,
                encoding="utf-8",
            )
            invalid_confidence = MODULE.review_coverage(fixture, path)
            self.assertFalse(invalid_confidence["coverage_equal"])
            self.assertEqual(
                ["branch:BRANCH_A"],
                invalid_confidence["invalid_confidence"],
            )
            path.write_text(
                f"Inventory-SHA256: {'b' * 64}\n\n"
                + header + card_a + card_a,
                encoding="utf-8",
            )
            broken = MODULE.review_coverage(fixture, path)
            self.assertFalse(broken["inventory_digest_matches"])
            self.assertEqual(["branch:BRANCH_A"],
                             broken["duplicate_evidence_cards"])
            self.assertEqual(["feature:DNGN_A"],
                             broken["missing_evidence_cards"])

    def test_complete_review_results_prefills_strict_pending_cards(self):
        fixture = {
            "inventory_sha256": "c" * 64,
            "rows": [{
                "identity": "portal_family:test",
                "category": "portal_family",
                "lifecycle": "current",
                "file": "dat/des/portals/test.des",
                "evidence": {"file": "dat/des/portals/test.des"},
            }],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "review.md"
            path.write_text(
                "preserve me\n\n| unrelated | table |\n|---|---|\n"
                "| value | value |\n",
                encoding="utf-8",
            )
            MODULE.complete_review_results(fixture, path)
            first = path.read_text(encoding="utf-8")
            MODULE.complete_review_results(fixture, path)
            second = path.read_text(encoding="utf-8")
            coverage = MODULE.review_coverage(fixture, path)
        self.assertEqual(first, second)
        self.assertIn("preserve me", second)
        self.assertIn("insufficient evidence", second)
        for column in (
            "lifecycle",
            "proposed_translation",
            "adopted_translation",
            "rejected_alternatives",
            "confidence",
            "glossary_decision_authority",
            "shared_dependency_group",
            "evidence_locations",
            "deferred_follow_up",
            "re_entry_conditions",
        ):
            self.assertIn(column, second)
        self.assertGreaterEqual(
            second.count(MODULE.PENDING_REVIEW),
            len(MODULE.REVIEW_DECISION_FIELDS),
        )
        self.assertNotIn("| keep |", second)
        self.assertNotIn("| high:", second)
        self.assertFalse(coverage["coverage_equal"])
        self.assertTrue(coverage["inventory_digest_matches"])
        self.assertFalse(coverage["missing_required_fields"])


if __name__ == "__main__":
    unittest.main()
