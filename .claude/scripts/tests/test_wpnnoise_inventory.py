#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


CONTROL_ROOT = Path(__file__).resolve().parents[3]
ROOT = Path(os.environ.get("ZH_VERIFY_AUDIT_ROOT", CONTROL_ROOT))
SCRIPT = CONTROL_ROOT / ".claude/scripts/wpnnoise_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("wpnnoise_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

# Issue #60 frozen baseline boundary (immutable exact-Git OIDs, independent of
# branch depth).  The baseline is the pre-landing state (731 EN / 720 ZH with
# six asymmetric keys); the candidate is the approved landing commit 1de9250b
# (731/731) whose ZH differences are exactly the reviewed actions below plus
# the 48 reviewed replacement proposals.  The tool accepts --baseline-ref at
# runtime; the tests pin the boundary the inventory freezes.
BASELINE = "7b56bccf9ce06646b65acf056b1445ad2999512d"
CANDIDATE = "1de9250baabffad96f8c945caebde60c62e43000"

# Reviewed one-sided structural actions (kind + ordinal only; the bound texts
# are derived from the exact baseline/candidate artifacts by the fixtures):
# EN-only missing variants approved for addition (incl. the two kazoo
# positional realignments at ordinals 8/30), the ZH-only deus-vult orphan
# approved for removal at baseline ZH ordinal 1, and the single approved
# matched-slot protocol transition at _singing_no_tension_ baseline ordinal 5
# (random-site shape [2,2] -> [3,2] by restoring the EN empty random option).
APPROVED_ACTIONS = {
    "_instrumental_noises_": [("add", 8)],
    "weapon_noise": [("add", 30)],
    "_real_song_no_tension_": [("add", 19), ("add", 20)],
    "_scream_": [("add", 70)],
    "fungus thoughts": [("add", ordinal) for ordinal in range(7, 14)],
    "_speaking_high_tension_": [("remove", 1)],
    "_singing_no_tension_": [("protocol_transition", 5)],
}


def exact_artifact(oid: str, directory: str) -> dict:
    scoped = MODULE.shared._derive_scoped_dump(
        oid, directory, f"fixture {directory}",
        source_basename=MODULE.SOURCE_BASENAME,
    )
    return {
        "schema_version": 1,
        "database_name": "speak",
        "source_directory": directory,
        "sources": copy.deepcopy(scoped["sources"]),
        "entries": copy.deepcopy(scoped["entries"]),
    }


def derived_of(artifact: dict) -> dict:
    source = f"{artifact['source_directory']}{MODULE.SOURCE_BASENAME}"
    return {
        "sources": copy.deepcopy(artifact["sources"]),
        "entries": [
            copy.deepcopy(entry) for entry in artifact["entries"]
            if any(item["source_name"] == source
                   for item in entry["source_history"])
        ],
    }


def metadata_for(inventory: dict, counts: dict[str, int] | None = None) -> dict:
    counts = counts or {"keep": len(inventory["entries"])}
    return {
        "baseline": inventory["baseline_ref"],
        "chinese_production_dump_sha256":
            inventory["dumps"]["localized"]["artifact_sha256"],
        "en_lua_site_count": MODULE.EXPECTED_EN_LUA_SITES,
        "en_random_site_count": MODULE.EXPECTED_EN_RANDOM_SITES,
        "en_variant_count": MODULE.EXPECTED_EN_VARIANT_COUNT,
        "english_production_dump_sha256":
            inventory["dumps"]["english"]["artifact_sha256"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": len(inventory["entries"]),
        "inventory_sha256": inventory["inventory_sha256"],
        "terminal_conclusion_counts": dict(sorted(counts.items())),
        "zh_lua_site_count": MODULE.EXPECTED_ZH_LUA_SITES,
        "zh_random_site_count": MODULE.EXPECTED_ZH_RANDOM_SITES,
        "zh_variant_count": MODULE.EXPECTED_ZH_VARIANT_COUNT,
    }


def card_for(
    inventory: dict, entry: dict, conclusion: str = "keep",
    variant_override: dict[int, tuple[str, str]] | None = None,
) -> dict:
    """Synthetic strict review card bound to the exact baseline inventory."""
    variant_override = variant_override or {}
    frozen = MODULE._frozen_route_evidence(entry)
    current_en = [variant["raw_pattern"] for variant in entry["english_variants"]]
    current_zh = [variant["chinese"] for variant in entry["variants"]]
    proposed = list(current_zh)
    reviews = []
    for variant in entry["variants"]:
        ordinal = variant["locator"]["variant_ordinal"]
        override = variant_override.get(ordinal)
        variant_conclusion, variant_proposal = (
            override if override is not None else ("keep", variant["chinese"])
        )
        if variant_conclusion == "keep":
            variant_proposal = variant["chinese"]
        proposed[ordinal] = variant_proposal
        review = {
            "variant_ordinal": ordinal,
            "weight": variant["weight"],
            "control_prefix": variant["control_prefix"],
            "runtime_tokens": variant["runtime_tokens"],
            "random_site_counts": variant["random_site_counts"],
            "lua_site_count": variant["lua_site_count"],
            "lua_comparison_strings": variant["lua_comparison_strings"],
            "english": variant["english"],
            "current_chinese": variant["chinese"],
            "proposed_translation": variant_proposal,
            "terminal_conclusion": variant_conclusion,
            "rationale": "完整审阅并保留。" if variant_conclusion == "keep"
            else "已核对生产消费者语义并确认改译。",
        }
        if variant_conclusion in MODULE.DEFER_CONCLUSIONS:
            review.update({
                "deferral_owner": "translation-reviewer",
                "deferral_reason": "需要人工确认术语与语气。",
                "reentry_trigger": "术语裁定或上下文证据出现后重新审阅。",
            })
        reviews.append(review)
    card = {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": entry["lifecycle"],
        "terminal_conclusion": conclusion,
        "deferral_owner": None,
        "deferral_reason": None,
        "confidence": "high",
        "dependency_group": entry["dependency_group"],
        "glossary_authority": (
            f"{inventory['glossary']['path']}@{inventory['glossary']['sha256']}"
        ),
        "actual_behavior": frozen["actual_behavior"],
        "display_context": frozen["display_context"],
        "consumer": copy.deepcopy(frozen["consumer"]),
        "producers": copy.deepcopy(frozen["producers"]),
        "evidence_locations": list(entry["evidence_locations"]),
        "production_facts": MODULE._expected_production_facts(inventory, entry),
        "reentry_trigger": MODULE.REENTRY_TRIGGER,
        "rejected_alternatives": ["不改变 lookup、权重、控制、token 或拓扑协议。"],
        "reviewer_rationale": "已核对生产来源、消费者、变体与配对证据。",
        "reviewed_actions": [],
        "current_english": current_en,
        "current_chinese": current_zh,
        "proposed_translation": proposed,
        "variant_reviews": reviews,
    }
    if conclusion in MODULE.DEFER_CONCLUSIONS:
        card.update({
            "deferral_owner": "translation-reviewer",
            "deferral_reason": "需要人工确认术语与语气。",
        })
    return card


def _open_target(path: Path) -> str:
    """The exact lexical path AuditSnapshot.read passes to os.open.

    Production rewrites macOS's fixed /var -> /private/var (and
    /tmp -> /private/tmp) aliases through ``_known_system_temp_alias``
    before opening an external input, so an adversarial os.open hook must
    compare against this normalized form, never the raw supplied path.
    On non-Darwin platforms the helper is the identity and the open target
    equals the supplied path, exactly like production.
    """
    return os.fspath(MODULE.audit_inputs._known_system_temp_alias(
        Path(os.path.normpath(os.path.abspath(os.fspath(path))))
    ))


class WpnnoiseInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.en_artifact = exact_artifact(BASELINE, "database/")
        cls.zh_artifact = exact_artifact(BASELINE, "database/zh/")
        cls.en_path = cls.root / "en.json"
        cls.zh_path = cls.root / "zh.json"
        cls.en_path.write_text(
            json.dumps(cls.en_artifact, ensure_ascii=False), encoding="utf-8"
        )
        cls.zh_path.write_text(
            json.dumps(cls.zh_artifact, ensure_ascii=False), encoding="utf-8"
        )
        cls.inventory = MODULE.build_inventory(
            BASELINE, cls.en_path, cls.zh_path, ROOT / "docs/glossary.md"
        )
        # The exact approved candidate (pinned immutable OID): EN is
        # byte-identical to the baseline; ZH is 731/731 with the reviewed
        # actions and the 48 approved replacements applied.
        cls.candidate_en_artifact = exact_artifact(CANDIDATE, "database/")
        cls.candidate_zh_artifact = exact_artifact(CANDIDATE, "database/zh/")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def write_records(self, records: list[dict]) -> Path:
        path = self.root / f"results-{self.id().split('.')[-1]}.md"
        path.write_text(
            "fixture\n\n" + MODULE.STRICT_BEGIN + "\n```jsonl\n"
            + "\n".join(
                json.dumps(record, ensure_ascii=False, sort_keys=True)
                for record in records
            )
            + "\n```\n" + MODULE.STRICT_END + "\n",
            encoding="utf-8",
        )
        return path

    def validate(self, records: list[dict], candidate=None):
        return MODULE.validate_results(
            self.write_records(copy.deepcopy(records)), self.inventory,
            candidate, records=records,
        )

    def all_cards(self) -> list[dict]:
        return [card_for(self.inventory, entry) for entry in self.inventory["entries"]]

    def bind_rejected(self, artifact: dict, directory: str, contains: str):
        path = self.root / f"bad-{self.id().split('.')[-1]}.json"
        path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
        label = "fixture EN" if directory == "database/" else "fixture ZH"
        with self.assertRaisesRegex(MODULE.InventoryError, contains):
            dump, raw = MODULE.shared._load_dump(path, label, directory)
            MODULE._dump_binding(dump, raw, label)

    # ── exact-Git inventory shape ─────────────────────────────────────────

    def test_load_dump_safe_default_family_rejects_misc(self):
        # The hardened speak base must fail closed on a misc dump even when
        # expected_database is omitted (the default contract is 'speak'),
        # and must keep accepting a speak dump on the same default path.
        misc = copy.deepcopy(self.en_artifact)
        misc["database_name"] = "misc"
        path = self.root / f"misc-{self.id().split('.')[-1]}.json"
        path.write_text(json.dumps(misc, ensure_ascii=False), encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'speak'"):
            MODULE._load_dump_safe(path, "fixture EN", "database/")
        dump, raw = MODULE._load_dump_safe(
            self.en_path, "fixture EN", "database/"
        )
        self.assertEqual("speak", dump["database_name"])
        self.assertTrue(raw)

    def test_exact_git_inventory_binds_frozen_shape_and_is_deterministic(self):
        first = self.inventory
        second_en = self.root / "en2.json"
        second_zh = self.root / "zh2.json"
        second_en.write_bytes(self.en_path.read_bytes())
        second_zh.write_bytes(self.zh_path.read_bytes())
        rebuilt = MODULE.build_inventory(
            BASELINE, second_en, second_zh, ROOT / "docs/glossary.md"
        )
        self.assertEqual(first["inventory_sha256"], rebuilt["inventory_sha256"])
        # Fixture-bound digest: the docs-frozen digest 6b3e4d18... is bound to
        # the /tmp production dump bytes and rebuilds identically through the
        # CLI; the unit-test fixtures derive from exact Git with their own
        # deterministic byte layout, so they pin their own digest here.  The
        # digest changed from 1ca4369d... when the R2 fixes added the
        # complete ordered Lua-block fingerprint to every variant and the
        # per-language reachability closure/witness evidence to the hashed
        # inventory core (evidence-invalidating schema fact, reported with
        # the exact new digest).
        self.assertEqual(
            "68c9ef8c7e3449f05b5799977c04a54c28798c0c251e65faa38ae2118c373514",
            first["inventory_sha256"],
        )
        self.assertEqual(MODULE.EXPECTED_IDENTITY_COUNT, len(first["entries"]))
        self.assertEqual(
            MODULE.EXPECTED_EN_VARIANT_COUNT,
            sum(entry["en_variant_count"] for entry in first["entries"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_ZH_VARIANT_COUNT,
            sum(entry["zh_variant_count"] for entry in first["entries"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_EN_RANDOM_SITES,
            sum(len(variant["random_site_counts"])
                for entry in first["entries"]
                for variant in entry["english_variants"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_ZH_RANDOM_SITES,
            sum(len(variant["random_site_counts"])
                for entry in first["entries"]
                for variant in entry["variants"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_EN_LUA_SITES,
            sum(variant["lua_site_count"]
                for entry in first["entries"]
                for variant in entry["english_variants"]),
        )
        self.assertEqual(
            MODULE.EXPECTED_ZH_LUA_SITES,
            sum(variant["lua_site_count"]
                for entry in first["entries"]
                for variant in entry["variants"]),
        )
        roots = {
            entry["key"] for entry in first["entries"]
            if entry["lifecycle"] == "direct-production-root"
        }
        fragments = {
            entry["key"] for entry in first["entries"]
            if entry["lifecycle"] == "recursive-internal-fragment"
        }
        self.assertEqual(set(MODULE.ROOT_KEYS), roots)
        self.assertEqual(65, len(roots | fragments))
        self.assertTrue(fragments.isdisjoint(roots))
        for entry in first["entries"]:
            self.assertIn(entry["key"], MODULE.DEPENDENCY_GROUP)

    def test_lua_comparison_strings_are_frozen_protocol(self):
        comparisons = {
            comparison
            for entry in self.inventory["entries"]
            for variant in entry["variants"]
            for comparison in variant["lua_comparison_strings"]
        } | {
            comparison
            for entry in self.inventory["entries"]
            for variant in entry["english_variants"]
            for comparison in variant["lua_comparison_strings"]
        }
        self.assertEqual(set(MODULE.LUA_COMPARISON_STRINGS), comparisons)

    def test_asymmetric_and_one_sided_variants_are_frozen_facts(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        for key, (en_count, zh_count) in MODULE.ASYMMETRIC_VARIANT_KEYS.items():
            with self.subTest(key=key):
                entry = by_key[key]
                self.assertEqual(en_count, entry["en_variant_count"])
                self.assertEqual(zh_count, entry["zh_variant_count"])
        high = by_key["_speaking_high_tension_"]
        self.assertEqual([32], high["zh_only_variant_ordinals"])
        self.assertEqual([], high["en_only_variant_ordinals"])
        self.assertIsNone(high["variants"][32]["english"])
        self.assertEqual(0, high["variants"][32]["lua_site_count"])
        self.assertEqual([], high["variants"][32]["lua_comparison_strings"])
        self.assertEqual(1, high["variants"][1]["lua_site_count"])
        self.assertEqual(["No God"],
                         high["variants"][1]["lua_comparison_strings"])
        scream = by_key["_scream_"]
        self.assertEqual([70], scream["en_only_variant_ordinals"])
        self.assertEqual([], scream["zh_only_variant_ordinals"])
        fungus = by_key["fungus thoughts"]
        self.assertEqual(list(range(7, 14)), fungus["en_only_variant_ordinals"])
        self.assertEqual([], fungus["zh_only_variant_ordinals"])
        instrumental = by_key["_instrumental_noises_"]
        self.assertEqual([12], instrumental["en_only_variant_ordinals"])

    def test_recursive_closure_reachability_is_proven_not_assumed(self):
        """Real-tree reachability pass: closure and deterministic witnesses.

        The inventory traverses the directed recursive-token graph
        independently for EN and ZH from every ROOT_KEYS member and requires
        the complete non-root closure to equal the fragment set; every
        fragment therefore carries a deterministic root-to-fragment witness
        whose consecutive edges exist in that language's graph.
        """
        for entry in self.inventory["entries"]:
            if entry["lifecycle"] == "recursive-internal-fragment":
                sites = entry["referencing_sites"]
                self.assertTrue(
                    sites["english"] or sites["chinese"],
                    f"{entry['key']} fragment has no referencing site",
                )
        root_keys = {entry["key"] for entry in self.inventory["entries"]
                     if entry["lifecycle"] == "direct-production-root"}
        self.assertEqual(28, len(root_keys))
        fragments = {
            entry["key"] for entry in self.inventory["entries"]
            if entry["lifecycle"] == "recursive-internal-fragment"
        }
        self.assertEqual(37, len(fragments))
        self.assertEqual(65, len(root_keys | fragments))
        for language in ("english", "chinese"):
            with self.subTest(language=language):
                proof = self.inventory["reachability"][language]
                self.assertEqual(sorted(fragments),
                                 proof["non_root_closure"])
                self.assertEqual(sorted(fragments),
                                 sorted(proof["witnesses"]))
                for fragment, path in proof["witnesses"].items():
                    self.assertIn(path[0], root_keys)
                    self.assertEqual(fragment, path[-1])
                    for source, target in zip(path, path[1:]):
                        self.assertIn(target, proof["edges"][source])

    def test_reachability_rejects_disconnected_self_loop(self):
        """A disconnected self-loop leaves its fragment unreachable.

        The reviewer's exact fixture shape: all external references to
        _rhyme_word_ are replaced with a caller token in both artifacts and
        _rhyme_word_ gains a self-reference, so the union-of-destinations
        check would pass while an independent traversal from ROOT_KEYS
        proves the fragment unreachable.  The production build path is
        exercised (dump binding + real traversal), not a reimplementation.
        """
        en = copy.deepcopy(self.en_artifact)
        zh = copy.deepcopy(self.zh_artifact)
        for artifact in (en, zh):
            self.rewire_fragment(artifact, "_rhyme_word_",
                                 external=("_common_speaking_no_tension_",
                                           10))
            # Disconnected self-loop: only _rhyme_word_ references itself.
            self.add_token(artifact, "_rhyme_word_", 0, "@_rhyme_word_@")
        with self.assertRaisesRegex(
            MODULE.InventoryError, "unreachable from ROOT_KEYS.*_rhyme_word_"
        ):
            self.build_inventory_from(en, zh)

    def test_reachability_rejects_disconnected_cycle(self):
        """A disconnected cross-reference cycle fails the closure proof."""
        en = copy.deepcopy(self.en_artifact)
        zh = copy.deepcopy(self.zh_artifact)
        for artifact in (en, zh):
            self.rewire_fragment(
                artifact, "_rhyme_word_",
                external=("_common_speaking_no_tension_", 10))
            self.rewire_fragment(
                artifact, "_song_theme_",
                external=("_singing_no-low_tension_", 43),
                extra_external=("_singing_no-low_tension_", 44))
            # _rhyme_word_ <-> _song_theme_ two-cycle with no external edge.
            self.add_token(artifact, "_rhyme_word_", 0, "@_song_theme_@")
            self.add_token(artifact, "_song_theme_", 0, "@_rhyme_word_@")
        with self.assertRaisesRegex(
            MODULE.InventoryError, "unreachable from ROOT_KEYS"
        ):
            self.build_inventory_from(en, zh)

    def test_reachability_rejects_root_token_destination(self):
        """A fragment referencing a root key breaks the topology proof."""
        en = copy.deepcopy(self.en_artifact)
        zh = copy.deepcopy(self.zh_artifact)
        for artifact in (en, zh):
            self.add_token(artifact, "_rhyme_word_", 0,
                           "@noisy weapon@")
        with self.assertRaisesRegex(
            MODULE.InventoryError, "references root keys"
        ):
            self.build_inventory_from(en, zh)

    def rewire_fragment(
        self, artifact: dict, fragment: str,
        external: tuple[str, int], extra_external: tuple[str, int] | None = None,
    ) -> None:
        """Replace external references to a fragment with a caller token."""
        pairs = [external]
        if extra_external is not None:
            pairs.append(extra_external)
        for key, ordinal in pairs:
            entry = next(
                entry for entry in artifact["entries"]
                if entry["canonical_key"] == key
            )
            pattern = entry["variants"][ordinal]["raw_pattern"]
            entry["variants"][ordinal]["raw_pattern"] = pattern.replace(
                f"@{fragment}@", "@player_name@", 1)

    @staticmethod
    def add_token(artifact: dict, key: str, ordinal: int, token: str) -> None:
        entry = next(
            entry for entry in artifact["entries"]
            if entry["canonical_key"] == key
        )
        entry["variants"][ordinal]["raw_pattern"] = (
            entry["variants"][ordinal]["raw_pattern"] + token
        )

    def build_inventory_from(self, en: dict, zh: dict) -> dict:
        """Run the real build_inventory path on mutated artifacts.

        The exact-Git scoped derivation is faked with the mutated artifacts
        (the same driver pattern the candidate gate tests use), so dump
        binding, frozen-total checks and the reachability traversal all run
        as production code on the mutation.
        """
        en_path = self.root / f"reach-en-{self.id().split('.')[-1]}.json"
        zh_path = self.root / f"reach-zh-{self.id().split('.')[-1]}.json"
        en_path.write_text(json.dumps(en, ensure_ascii=False), encoding="utf-8")
        zh_path.write_text(json.dumps(zh, ensure_ascii=False), encoding="utf-8")

        def fake_derive(oid, directory, label, source_basename=None):
            artifact = en if directory == "database/" else zh
            return derived_of(artifact)

        with mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=fake_derive
        ):
            return MODULE.build_inventory(
                BASELINE, en_path, zh_path, ROOT / "docs/glossary.md"
            )

    # ── malicious refs, paths, types ─────────────────────────────────────

    def test_malicious_git_paths_and_refs_fail_closed(self):
        for bad in ("../database/wpnnoise.txt", "/etc/passwd",
                    "database/./wpnnoise.txt"):
            with self.subTest(path=bad):
                with self.assertRaisesRegex(MODULE.InventoryError, "unsafe Git path"):
                    MODULE.shared._git_blob_at_oid(BASELINE, bad, "fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "full lowercase OID"):
            MODULE.shared._validate_oid("ABCDEF" * 6 + "abcd", "fixture")
        with self.assertRaisesRegex(MODULE.InventoryError, "not a commit"):
            MODULE.shared._validate_oid("0" * 40, "fixture")

    def test_source_manifest_parsing_fails_closed(self):
        def tree_record(mode: bytes, kind: bytes, name: bytes) -> bytes:
            return mode + b" " + kind + b" " + b"1" * 40 + b"\t" + name + b"\0"

        tree = b"".join([
            tree_record(b"100644", b"blob", b"wpnnoise.txt"),
            tree_record(b"040000", b"tree", b"nested"),
            tree_record(b"120000", b"blob", b"linked.txt"),
        ])
        with mock.patch.object(MODULE.shared, "_git_output", return_value=tree):
            with self.assertRaisesRegex(MODULE.InventoryError, "unsupported tree"):
                MODULE.shared._localized_source_manifest(BASELINE, "ZH fixture")

        with mock.patch.object(
            MODULE.shared, "_git_blob_at_oid",
            return_value=b'TextDB("speak", "database/", { "a.txt", "a.txt", })',
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "duplicate SpeakDB"):
                MODULE.shared._english_source_manifest(BASELINE, "EN fixture")
        with mock.patch.object(
            MODULE.shared, "_git_blob_at_oid",
            return_value=b'TextDB("speak", "database/", { "evil.txt; rm -rf /" })',
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "unsafe SpeakDB"):
                MODULE.shared._english_source_manifest(BASELINE, "EN fixture")

    def test_artifact_objects_reject_unknown_fields_and_boolean_integers(self):
        cases = (
            ("unknown field", lambda value: value.__setitem__("unknown", None),
             "field set mismatch"),
            ("schema boolean",
             lambda value: value.__setitem__("schema_version", True),
             "must be an integer"),
            ("source index boolean",
             lambda value: value["sources"][0].__setitem__("load_index", False),
             "must be an integer"),
            ("variant ordinal boolean",
             lambda value: value["entries"][0]["variants"][0][
                 "locator"
             ].__setitem__("variant_ordinal", False),
             "must be an integer"),
            ("weight boolean",
             lambda value: value["entries"][0]["variants"][0].__setitem__(
                 "weight", True),
             "must be an integer"),
        )
        for name, mutate, message in cases:
            bad = copy.deepcopy(self.en_artifact)
            mutate(bad)
            with self.subTest(case=name):
                self.bind_rejected(bad, "database/", message)

    def test_override_provenance_parse_error_and_ordinal_gap_fail(self):
        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        other_prov = {"source_name": "database/insult.txt", "load_index": 4,
                      "definition_ordinal": 0}
        entry["source_history"].append(other_prov)
        entry["effective_provenance"] = other_prov
        for variant in entry["variants"]:
            variant["provenance"] = other_prov
        self.bind_rejected(bad, "database/", "overridden")

        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        entry["effective_provenance"]["definition_ordinal"] = 4
        for variant in entry["variants"]:
            variant["provenance"]["definition_ordinal"] = 4
        self.bind_rejected(bad, "database/", "not contiguous")

        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        entry["parse_error"] = "BUG, WEIGHT AT END OF ENTRY"
        entry["variants"] = []
        self.bind_rejected(bad, "database/", "parse error")

        bad = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "noisy weapon"
        )
        entry["variants"][0]["raw_pattern"] = "BOGUS:broken pattern"
        self.bind_rejected(bad, "database/", "unrecognized control")

        bad = copy.deepcopy(self.zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "_speaking_high_tension_"
        )
        entry["variants"][1]["raw_pattern"] = (
            entry["variants"][1]["raw_pattern"].replace("}}", "")
        )
        self.bind_rejected(bad, "database/zh/", "unbalanced Lua")

        bad = copy.deepcopy(self.zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "eel hand solo actions"
        )
        entry["variants"][0]["raw_pattern"] = (
            entry["variants"][0]["raw_pattern"].replace("]", "")
        )
        self.bind_rejected(bad, "database/zh/", "unbalanced random")

    def test_frozen_counts_drift_is_rejected(self):
        renamed = copy.deepcopy(self.en_artifact)
        entry = next(
            entry for entry in renamed["entries"]
            if entry["canonical_key"] == "weapon_noises"
        )
        entry["canonical_key"] = "weapon_noises_renamed"
        for variant in entry["variants"]:
            variant["locator"]["canonical_key"] = entry["canonical_key"]
        self.bind_rejected(renamed, "database/", "key set mismatch")

        trimmed = copy.deepcopy(self.zh_artifact)
        entry = next(
            entry for entry in trimmed["entries"]
            if entry["canonical_key"] == "_scream_"
        )
        entry["variants"].pop()
        self.bind_rejected(trimmed, "database/zh/", "variant count mismatch")

    # ── review results: completeness, conclusions, metadata ──────────────

    def test_completeness_equality_all_cards_pass(self):
        records = [metadata_for(self.inventory), *self.all_cards()]
        loaded = self.validate(records)
        self.assertEqual(65, len(loaded["cards"]))
        self.assertEqual(
            {"keep": 65}, loaded["metadata"]["terminal_conclusion_counts"]
        )

    def test_completeness_equality_rejects_missing_extra_and_duplicate_cards(self):
        cards = self.all_cards()
        with self.assertRaisesRegex(MODULE.InventoryError, "coverage mismatch"):
            self.validate([metadata_for(self.inventory), *cards[:-1]])
        with self.assertRaisesRegex(MODULE.InventoryError, "coverage mismatch"):
            self.validate([metadata_for(self.inventory), *cards,
                           copy.deepcopy(cards[0])])
        replaced = copy.deepcopy(cards)
        replaced[0]["identity"] = "wpnnoise:not a real key"
        replaced[0]["key"] = "not a real key"
        with self.assertRaisesRegex(MODULE.InventoryError, "identity set mismatch"):
            self.validate([metadata_for(self.inventory), *replaced])
        duplicate = [metadata_for(self.inventory), cards[0],
                     copy.deepcopy(cards[0]), *cards[2:]]
        with self.assertRaisesRegex(MODULE.InventoryError, "duplicate review card"):
            self.validate(duplicate)

    def test_review_card_order_and_field_set_fail_closed(self):
        cards = self.all_cards()
        cards[0], cards[1] = cards[1], cards[0]
        with self.assertRaisesRegex(MODULE.InventoryError, "identity order mismatch"):
            self.validate([metadata_for(self.inventory), *cards])
        cards = self.all_cards()
        del cards[5]["production_facts"]
        with self.assertRaisesRegex(MODULE.InventoryError, "production_facts"):
            self.validate([metadata_for(self.inventory), *cards])

    def test_review_metadata_bindings_fail_closed(self):
        metadata = metadata_for(self.inventory)
        metadata["baseline"] = "0" * 40
        with self.assertRaisesRegex(MODULE.InventoryError, "baseline mismatch"):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["inventory_sha256"] = "0" * 64
        with self.assertRaisesRegex(MODULE.InventoryError, "inventory_sha256"):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["english_production_dump_sha256"] = "0" * 64
        with self.assertRaisesRegex(
            MODULE.InventoryError, "english_production_dump_sha256"
        ):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["zh_variant_count"] += 1
        with self.assertRaisesRegex(MODULE.InventoryError, "variant counts"):
            self.validate([metadata, *self.all_cards()])
        metadata = metadata_for(self.inventory)
        metadata["terminal_conclusion_counts"] = {"keep": 64, "adjust": 1}
        with self.assertRaisesRegex(
            MODULE.InventoryError, "terminal_conclusion_counts"
        ):
            self.validate([metadata, *self.all_cards()])

    def test_review_conclusion_semantics_and_deferral_fields(self):
        cards = self.all_cards()
        cards[0]["variant_reviews"][0]["terminal_conclusion"] = "pending"
        with self.assertRaisesRegex(MODULE.InventoryError, "nonterminal"):
            self.validate([metadata_for(self.inventory), *cards])

        cards = self.all_cards()
        card = cards[0]
        card["terminal_conclusion"] = "adjust"
        card["variant_reviews"][0]["terminal_conclusion"] = "adjust"
        card["variant_reviews"][0]["proposed_translation"] += "（调整）"
        card["proposed_translation"][0] = (
            card["variant_reviews"][0]["proposed_translation"]
        )
        records = [metadata_for(self.inventory, {"keep": 64, "adjust": 1}), *cards]
        loaded = self.validate(records)
        self.assertEqual("adjust", loaded["cards"][0]["terminal_conclusion"])

        # adjust without a changed proposal is rejected.
        cards = self.all_cards()
        card = cards[0]
        card["terminal_conclusion"] = "adjust"
        card["variant_reviews"][0]["terminal_conclusion"] = "adjust"
        with self.assertRaisesRegex(MODULE.InventoryError, "must change"):
            self.validate([metadata_for(self.inventory), *cards])

        # defer terminology requires owner/reason/reentry at card and variant.
        cards = self.all_cards()
        card = cards[0]
        card["terminal_conclusion"] = "defer terminology"
        card["deferral_owner"] = "translation-reviewer"
        card["deferral_reason"] = "术语待裁定。"
        card["reentry_trigger"] = "术语裁定后重新审阅。"
        review = card["variant_reviews"][0]
        review["terminal_conclusion"] = "defer terminology"
        review.update({
            "deferral_owner": "translation-reviewer",
            "deferral_reason": "术语待裁定。",
            "reentry_trigger": "术语裁定后重新审阅。",
        })
        records = [metadata_for(
            self.inventory, {"keep": 64, "defer terminology": 1}), *cards]
        self.validate(records)
        del review["deferral_owner"]
        with self.assertRaisesRegex(MODULE.InventoryError, "deferral_owner"):
            self.validate([metadata_for(self.inventory), *cards])

    def test_variant_review_protocol_facts_fail_closed(self):
        cards = self.all_cards()
        card = next(card for card in cards if card["key"] == "noisy weapon")
        card["variant_reviews"][3]["weight"] = 21
        with self.assertRaisesRegex(MODULE.InventoryError, "weight mismatch"):
            self.validate([metadata_for(self.inventory), *cards])
        cards = self.all_cards()
        card = next(card for card in cards
                    if card["key"] == "singing sword silenced")
        card["variant_reviews"][0]["control_prefix"] = "SOUND"
        with self.assertRaisesRegex(MODULE.InventoryError, "control_prefix mismatch"):
            self.validate([metadata_for(self.inventory), *cards])
        cards = self.all_cards()
        card = next(card for card in cards
                    if card["key"] == "_speaking_high_tension_")
        card["variant_reviews"][32]["lua_comparison_strings"] = ["Zin"]
        with self.assertRaisesRegex(
            MODULE.InventoryError, "lua_comparison_strings mismatch"
        ):
            self.validate([metadata_for(self.inventory), *cards])

    def test_production_facts_cover_tokens_sites_lua_and_pairing(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        noisy = MODULE._expected_production_facts(self.inventory,
                                                  by_key["noisy weapon"])
        self.assertEqual([], noisy["caller_tokens"])
        for token in ("@_weapon_chatter_@", "@weapon_noises@",
                      "@_instrumental_noises_@", "@weapon_noise@"):
            self.assertIn(token, noisy["recursive_tokens"])
        self.assertEqual([None, None, None, "SOUND"],
                         noisy["control_prefixes"]["english"])

        noises = MODULE._expected_production_facts(self.inventory,
                                                   by_key["weapon_noises"])
        self.assertEqual(["@Your_weapon@"], noises["caller_tokens"])
        self.assertEqual([], noises["recursive_tokens"])
        self.assertEqual([], noises["en_only_variant_ordinals"])
        self.assertEqual(24, noises["en_variant_count"])
        self.assertEqual(24, noises["zh_variant_count"])
        self.assertEqual(noises["weights"]["english"],
                         noises["weights"]["chinese"])

        eel = MODULE._expected_production_facts(self.inventory,
                                                by_key["eel hand solo actions"])
        self.assertEqual([2], eel["random_site_counts"]["chinese"][0])
        self.assertEqual(20, eel["weights"]["chinese"][0])

        high = MODULE._expected_production_facts(
            self.inventory, by_key["_speaking_high_tension_"])
        self.assertIn("lua", high["pairing_protocol_differences"][3])
        self.assertIn("lua", high["pairing_protocol_differences"][4])
        self.assertEqual([], high["pairing_protocol_differences"][32])
        self.assertIn("@_godless_sorter_@", high["recursive_tokens"])
        self.assertIn("@player_god@", high["caller_tokens"])

    # ── candidate binding (pinned exact-Git candidate + reviewed actions) ──

    def add_candidate(self, en: dict, zh: dict, records: list[dict],
                      candidate_ref: str = CANDIDATE) -> list[dict]:
        en_path = self.root / f"candidate-en-{self.id().split('.')[-1]}.json"
        zh_path = self.root / f"candidate-zh-{self.id().split('.')[-1]}.json"
        en_path.write_text(json.dumps(en, ensure_ascii=False), encoding="utf-8")
        zh_path.write_text(json.dumps(zh, ensure_ascii=False), encoding="utf-8")
        real_derive = MODULE.shared._derive_scoped_dump

        def fake_derive(oid, directory, label, source_basename=None):
            if oid == candidate_ref:
                artifact = en if directory == "database/" else zh
                return derived_of(artifact)
            return real_derive(oid, directory, label,
                               source_basename=source_basename)

        with mock.patch.object(MODULE.shared, "_require_candidate_commit"), \
                mock.patch.object(
                    MODULE.shared, "_derive_scoped_dump", side_effect=fake_derive,
                ):
            return MODULE.add_candidate(self.inventory, candidate_ref,
                                        en_path, zh_path, records)

    @staticmethod
    def zh_variant(artifact: dict, key: str, ordinal: int) -> dict:
        entry = next(
            entry for entry in artifact["entries"]
            if entry["canonical_key"] == key
        )
        return entry["variants"][ordinal]

    def mutated_zh(self, key: str, ordinal: int, mutator) -> dict:
        artifact = copy.deepcopy(self.zh_artifact)
        mutator(self.zh_variant(artifact, key, ordinal))
        return artifact

    def review_records_for(
        self, candidate_zh: dict | None = None,
        actions_by_key: dict | None = None,
    ) -> list[dict]:
        """Synthetic strict review bound to a candidate ZH artifact.

        Proposals, action texts and conclusions are derived from the supplied
        candidate (default: the exact approved candidate) and the baseline
        artifacts, never hard-coded: matched positions take the candidate's
        text (adjust when it differs from the baseline, keep otherwise) and
        action texts are bound to the candidate's inserted variants or the
        baseline's removed orphan.  In-range add ordinals borrow the proposal
        slot (placeholder convention) exactly like the approved kazoo cards.
        """
        candidate_zh = candidate_zh or self.candidate_zh_artifact
        actions_by_key = actions_by_key or APPROVED_ACTIONS
        candidate_texts = {
            entry["canonical_key"]: [
                variant["raw_pattern"] for variant in entry["variants"]
            ]
            for entry in candidate_zh["entries"]
        }
        cards = []
        for entry in self.inventory["entries"]:
            key = entry["key"]
            actions = []
            overrides = {}
            for kind, ordinal in actions_by_key.get(key, []):
                if kind == "add":
                    text = candidate_texts[key][ordinal]
                    if ordinal < len(entry["variants"]):
                        # In-range add borrows the proposal slot.
                        overrides[ordinal] = ("adjust", text)
                elif kind == "remove":
                    text = entry["variants"][ordinal]["chinese"]
                else:
                    # protocol_transition: baseline protocol from the frozen
                    # baseline variant, text and new protocol from the
                    # candidate at the same ordinal (no add/remove on this
                    # card, so candidate ordinal == baseline ordinal).
                    baseline = entry["variants"][ordinal]
                    text = candidate_texts[key][ordinal]
                    actions.append({
                        "kind": kind,
                        "variant_ordinal": ordinal,
                        "baseline_protocol": {
                            "weight": baseline["weight"],
                            "control_prefix": baseline["control_prefix"],
                            "runtime_tokens": baseline["runtime_tokens"],
                            "random_site_counts":
                                baseline["random_site_counts"],
                            "lua_blocks": baseline["lua_blocks"],
                        },
                        "text": text,
                        "new_protocol": {
                            "weight": baseline["weight"],
                            "control_prefix": MODULE._derived_action_fact(
                                text, "control_prefix"),
                            "runtime_tokens": MODULE._derived_action_fact(
                                text, "runtime_tokens"),
                            "random_site_counts":
                                MODULE._derived_action_fact(
                                    text, "random_site_counts"),
                            "lua_blocks": MODULE._derived_action_fact(
                                text, "lua_blocks"),
                        },
                        "rationale": "已按严格台账核对的单边动作。",
                    })
                    continue
                actions.append({
                    "kind": kind,
                    "variant_ordinal": ordinal,
                    "text": text,
                    "rationale": "已按严格台账核对的单边动作。",
                })
            slots = MODULE._action_slots(len(entry["variants"]), actions)
            add_ordinals = {
                action["variant_ordinal"] for action in actions
                if action["kind"] == "add"
            }
            for slot in slots:
                if slot["kind"] != "match":
                    continue
                if slot["variant_ordinal"] in add_ordinals:
                    continue  # placeholder: the shifted variant stays current
                expected = candidate_texts[key][slot["candidate_ordinal"]]
                if expected != entry["variants"][
                    slot["variant_ordinal"]]["chinese"]:
                    overrides[slot["variant_ordinal"]] = ("adjust", expected)
            conclusions = [
                "adjust" if ordinal in overrides else "keep"
                for ordinal in range(len(entry["variants"]))
            ]
            card = card_for(
                self.inventory, entry,
                conclusion=MODULE._aggregate(conclusions),
                variant_override=overrides,
            )
            card["reviewed_actions"] = actions
            cards.append(card)
        counts: dict[str, int] = {}
        for card in cards:
            counts[card["terminal_conclusion"]] = (
                counts.get(card["terminal_conclusion"], 0) + 1
            )
        return [metadata_for(self.inventory, counts), *cards]

    def test_candidate_english_is_byte_identical_to_baseline(self):
        self.assertEqual(derived_of(self.en_artifact),
                         derived_of(self.candidate_en_artifact))

    def test_candidate_binds_exact_approved_candidate(self):
        # The exact approved landing: EN byte-identical to the baseline; ZH
        # 731/731 with differences exactly equal to the 48 reviewed
        # replacements + 12 reviewed additions + the reviewed orphan removal.
        records = self.review_records_for()
        candidate_entries = self.add_candidate(
            self.candidate_en_artifact, self.candidate_zh_artifact, records
        )
        loaded = self.validate(records, candidate_entries)
        self.assertEqual(65, len(loaded["cards"]))
        candidate = self.inventory["candidate"]
        self.assertEqual(CANDIDATE, candidate["candidate_ref"])
        self.assertEqual(
            731, sum(len(entry["variants"]) for entry in candidate["entries"])
        )
        by_key = {
            entry["identity"].removeprefix("wpnnoise:"): entry
            for entry in candidate["entries"]
        }
        for key in APPROVED_ACTIONS:
            self.assertIn(key, by_key)

    def test_candidate_exact_zh_binding_and_english_no_drift(self):
        identity = "wpnnoise:_speaking_high_tension_"
        entry = next(
            entry for entry in self.inventory["entries"]
            if entry["identity"] == identity
        )
        new_text = entry["variants"][0]["chinese"] + "（候选改译）"
        # Approved candidate shape (real candidate: actions applied, counts
        # equal) plus one reviewed replacement at ordinal 0.
        candidate_zh = copy.deepcopy(self.candidate_zh_artifact)
        self.zh_variant(candidate_zh, "_speaking_high_tension_", 0)[
            "raw_pattern"
        ] = new_text
        records = self.review_records_for(candidate_zh)
        candidate_entries = self.add_candidate(
            self.en_artifact, candidate_zh, records
        )
        candidate = next(
            entry for entry in candidate_entries
            if entry["identity"] == identity
        )
        self.assertEqual(new_text, candidate["variants"][0]["chinese"])
        self.assertEqual(32, len(candidate["variants"]))
        loaded = self.validate(records, candidate_entries)
        loaded_card = next(
            card for card in loaded["cards"] if card["identity"] == identity
        )
        self.assertEqual(new_text, loaded_card["proposed_translation"][0])

        # A proposal that disagrees with the exact candidate ZH fails.
        bad_records = copy.deepcopy(records)
        bad_card = next(
            card for card in bad_records[1:] if card["identity"] == identity
        )
        bad_card["proposed_translation"][0] = new_text + "不一致"
        bad_card["variant_reviews"][0]["proposed_translation"] = (
            new_text + "不一致"
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "candidate ZH dump"):
            self.validate(bad_records, candidate_entries)

    def test_candidate_english_drift_is_rejected(self):
        drift = copy.deepcopy(self.en_artifact)
        self.zh_variant(drift, "noisy weapon", 0)["raw_pattern"] += " drift"
        records = self.review_records_for()
        with self.assertRaisesRegex(MODULE.InventoryError, "English drift"):
            self.add_candidate(
                drift, copy.deepcopy(self.candidate_zh_artifact), records
            )

    def test_candidate_zh_protocol_drift_is_rejected(self):
        """Candidate and ledger jointly changing a protocol field fails.

        Every fixture mutates a matched slot of the approved candidate AND
        the review records are rebuilt from the mutated candidate, so the
        ledger proposal agrees with the candidate text and the rejection must
        come from the protocol binding itself, never from a text-drift
        mismatch.  Each protocol field is covered: control VISUAL->SOUND,
        token reorder/duplicate/remove (ordered, with multiplicity), random
        alternative count and site order, Lua operator drift (== -> ~=), Lua
        block multiplicity, Lua comparison strings, and weight.  Lua is bound
        as the complete ordered block bodies, so operator/statement/literal/
        multiplicity/order changes fail even when site counts and comparison
        strings stay identical.
        """

        def swap_first_two_tokens(variant):
            pattern = variant["raw_pattern"]
            tokens = re.findall(r"@[^@]+@", pattern)
            first0 = pattern.find(tokens[0])
            first1 = pattern.find(tokens[1])
            t0, t1 = tokens[0], tokens[1]
            if first0 > first1:
                t0, t1 = t1, t0
                first0, first1 = first1, first0
            variant["raw_pattern"] = (
                pattern[:first0] + t1
                + pattern[first0 + len(t0):first1] + t0
                + pattern[first1 + len(t1):]
            )

        def swap_bracket_groups(variant):
            pattern = variant["raw_pattern"]
            spans = [
                (match.start(), match.end())
                for match in re.finditer(r"\[[^\[\]]*\]", pattern)
            ]
            first, second = spans[0], spans[1]
            group_a = pattern[first[0]:first[1]]
            group_b = pattern[second[0]:second[1]]
            variant["raw_pattern"] = (
                pattern[:first[0]] + group_b
                + pattern[first[1]:second[0]] + group_a
                + pattern[second[1]:]
            )

        def set_pattern(variant, replacement):
            variant["raw_pattern"] = replacement(variant["raw_pattern"])

        def mutate_candidate(key, ordinal, mutator):
            artifact = copy.deepcopy(self.candidate_zh_artifact)
            mutator(self.zh_variant(artifact, key, ordinal))
            return artifact

        # All mutations sit at matched positions of the approved candidate
        # (orphan already removed, counts equal), so each must fail the gate
        # at the protocol binding itself, never at a count check.  The
        # Lua-bearing matched variant is candidate ordinal 3 of
        # _speaking_high_tension_ (= baseline ordinal 4); its frozen pairing
        # envelope is ZH (tokens 3, lua 1, cmp No God) / EN (tokens 1,
        # lua 0), so every mutation below leaves that envelope.
        cases = (
            ("control VISUAL to SOUND",
             lambda: mutate_candidate(
                 "singing sword silenced", 0,
                 lambda variant: set_pattern(
                     variant,
                     lambda text: re.sub(r"^VISUAL:", "SOUND:", text))),
             "control_prefix", "protocol drift.*control_prefix"),
            ("token reorder",
             lambda: mutate_candidate("_speaking_high_tension_", 3,
                                      swap_first_two_tokens),
             "runtime_tokens", "protocol drift.*runtime_tokens"),
            ("token duplicate",
             lambda: mutate_candidate(
                 "_speaking_high_tension_", 3,
                 lambda variant: set_pattern(
                     variant,
                     lambda text: text.replace(
                         "@The_weapon@", "@The_weapon@@The_weapon@", 1))),
             "runtime_tokens", "protocol drift.*runtime_tokens"),
            ("token remove",
             lambda: mutate_candidate(
                 "_speaking_high_tension_", 3,
                 lambda variant: set_pattern(
                     variant,
                     lambda text: text.replace("@_godless_sorter_@", "", 1))),
             "runtime_tokens", "protocol drift.*runtime_tokens"),
            ("random alternative count",
             lambda: mutate_candidate(
                 "eel hand solo actions", 0,
                 lambda variant: set_pattern(
                     variant,
                     lambda text: text.replace(
                         "[疯狂地|惆怅地]", "[疯狂地|惆怅地|焦虑地]"))),
             "random_site_counts", "protocol drift.*random_site_counts"),
            ("random site order",
             lambda: mutate_candidate(
                 "_common_speaking_no_tension_", 3,
                 swap_bracket_groups),
             "random_site_counts", "protocol drift.*random_site_counts"),
            # Lua operator drift: site count and comparison strings stay
            # identical, only the executable operator changes.
            ("lua operator drift (== to ~=)",
             lambda: mutate_candidate(
                 "_speaking_high_tension_", 3,
                 lambda variant: set_pattern(
                     variant,
                     lambda text: text.replace(
                         'you.god() == "No God"',
                         'you.god() ~= "No God"'))),
             "lua_blocks", "protocol drift.*lua_blocks"),
            ("lua block multiplicity",
             lambda: mutate_candidate(
                 "_speaking_high_tension_", 3,
                 lambda variant: set_pattern(
                     variant, lambda text: text + "{{ }}")),
             "lua_blocks", "protocol drift.*lua_blocks"),
            # The candidate gate rejects a comparison string outside the
            # frozen Lua identity set at dump binding (fail closed on the
            # protocol identity itself), while the ledger gate rejects the
            # same joint change at the proposal protocol check (lua_blocks).
            ("lua comparison string",
             lambda: mutate_candidate(
                 "_speaking_high_tension_", 3,
                 lambda variant: set_pattern(
                     variant,
                     lambda text: text.replace('"No God"', '"Zin"'))),
             "lua_blocks", "unknown Lua comparison string"),
            ("weight",
             lambda: mutate_candidate(
                 "eel hand solo actions", 0,
                 lambda variant: variant.__setitem__("weight", 30)),
             "weight", "protocol drift.*weight"),
        )
        for name, build, field, candidate_message in cases:
            mutated = build()
            records = self.review_records_for(mutated)
            with self.subTest(case=name, gate="candidate"):
                with self.assertRaisesRegex(
                    MODULE.InventoryError, candidate_message
                ):
                    self.add_candidate(self.candidate_en_artifact, mutated,
                                       records)
            if field == "weight":
                # Weight is variant metadata, not text-derived: the ledger
                # records the baseline weight and the candidate gate binds
                # the candidate weight to it.  The ledger text check has no
                # weight to derive, so validation alone stays clean.
                self.validate(records)
                continue
            with self.subTest(case=name, gate="ledger"):
                with self.assertRaisesRegex(
                    MODULE.InventoryError,
                    f"proposed text {field} does not match the baseline ZH "
                    f"protocol",
                ):
                    self.validate(records)

    def test_candidate_rejects_en_envelope_lua_graft_after_remove(self):
        """The reviewer's exact joint drift: EN-envelope side switch.

        Candidate _speaking_high_tension_ ordinal 2 (mapped from baseline ZH
        ordinal 3 after the remove@1 shift) is given the exact EN ordinal-3
        Lua block.  The old gate accepted it because it compared the slot
        against the EN tuple at the same baseline ordinal; matched slots now
        compare only against the mapped baseline ZH variant, so both the
        candidate gate and the ledger gate reject the graft even though the
        ledger proposal agrees with the candidate text.
        """
        en_entry = next(
            entry for entry in self.en_artifact["entries"]
            if entry["canonical_key"] == "_speaking_high_tension_"
        )
        en_lua_pattern = en_entry["variants"][3]["raw_pattern"]
        mutated = copy.deepcopy(self.candidate_zh_artifact)
        self.zh_variant(mutated, "_speaking_high_tension_", 2)[
            "raw_pattern"
        ] = en_lua_pattern
        records = self.review_records_for(mutated)
        with self.subTest(gate="candidate"):
            with self.assertRaisesRegex(
                MODULE.InventoryError, "protocol drift.*runtime_tokens"
            ):
                self.add_candidate(self.candidate_en_artifact, mutated,
                                   records)
        with self.subTest(gate="ledger"):
            with self.assertRaisesRegex(
                MODULE.InventoryError,
                "proposed text runtime_tokens does not match the baseline "
                "ZH protocol",
            ):
                self.validate(records)

    def test_candidate_rejects_lua_operator_drift(self):
        """Executable Lua ``==`` -> ``~=`` drift is bound by block bodies.

        The matched Lua slot (candidate ordinal 3, baseline ordinal 4) keeps
        its site count and comparison strings; only the operator changes.
        The complete ordered Lua-block fingerprint must catch it in both the
        candidate gate and the ledger gate.
        """
        mutated = copy.deepcopy(self.candidate_zh_artifact)
        self.zh_variant(mutated, "_speaking_high_tension_", 3)[
            "raw_pattern"
        ] = self.zh_variant(
            mutated, "_speaking_high_tension_", 3
        )["raw_pattern"].replace(
            'you.god() == "No God"', 'you.god() ~= "No God"'
        )
        records = self.review_records_for(mutated)
        with self.subTest(gate="candidate"):
            with self.assertRaisesRegex(
                MODULE.InventoryError, "protocol drift.*lua_blocks"
            ):
                self.add_candidate(self.candidate_en_artifact, mutated,
                                   records)
        with self.subTest(gate="ledger"):
            with self.assertRaisesRegex(
                MODULE.InventoryError,
                "proposed text lua_blocks does not match the baseline ZH "
                "protocol",
            ):
                self.validate(records)

    def test_lua_block_fingerprint_binds_operators_statements_order(self):
        block_a = (' if you.god() == "No God" then '
                   'return "@_godless_sorter_@"; end ')
        block_b = (' if you.god() == "No God" then '
                   'return "@player_god@"; end ')
        self.assertEqual([block_a, block_b],
                         MODULE._lua_blocks("{{" + block_a + "}}{{"
                                            + block_b + "}}"))
        self.assertNotEqual(
            MODULE._lua_blocks("{{" + block_a + "}}{{" + block_b + "}}"),
            MODULE._lua_blocks("{{" + block_b + "}}{{" + block_a + "}}"),
        )
        self.assertEqual([block_a, block_a],
                         MODULE._lua_blocks("{{" + block_a + "}}{{"
                                            + block_a + "}}"))
        self.assertNotEqual(
            MODULE._lua_blocks(
                '{{ if you.god() == "No God" then return "A"; end }}'),
            MODULE._lua_blocks(
                '{{ if you.god() ~= "No God" then return "A"; end }}'),
        )

    def test_protocol_transition_binds_exact_approved_landing(self):
        """The one approved matched-slot protocol move binds exactly.

        _singing_no_tension_ baseline ordinal 5 (random [2,2], weight 10)
        moves to [3,2] by restoring the EN empty random option; the card
        record carries the exact baseline protocol, the exact approved text
        and the exact new protocol, and the exact approved candidate binds.
        """
        records = self.review_records_for()
        candidate_entries = self.add_candidate(
            self.candidate_en_artifact, self.candidate_zh_artifact, records
        )
        loaded = self.validate(records, candidate_entries)
        card = next(
            card for card in loaded["cards"]
            if card["key"] == "_singing_no_tension_"
        )
        transition = next(
            action for action in card["reviewed_actions"]
            if action["kind"] == "protocol_transition"
        )
        self.assertEqual(5, transition["variant_ordinal"])
        self.assertEqual([2, 2],
                         transition["baseline_protocol"]["random_site_counts"])
        self.assertEqual(10, transition["baseline_protocol"]["weight"])
        self.assertEqual([3, 2],
                         transition["new_protocol"]["random_site_counts"])
        self.assertEqual(10, transition["new_protocol"]["weight"])
        self.assertEqual("adjust", card["terminal_conclusion"])

    def test_protocol_transition_schema_fails_closed(self):
        records = self.review_records_for()

        # A transition at an unapproved (key, ordinal) is rejected even when
        # its protocol records are internally consistent.
        bad = copy.deepcopy(records)
        card = next(c for c in bad[1:] if c["key"] == "_singing_no_tension_")
        card["reviewed_actions"][0]["variant_ordinal"] = 6
        with self.assertRaisesRegex(
            MODULE.InventoryError, "not an approved protocol transition"
        ):
            self.validate(bad)

        # An approved slot with drifted text is rejected before any protocol
        # comparison.
        bad = copy.deepcopy(records)
        card = next(c for c in bad[1:] if c["key"] == "_singing_no_tension_")
        card["reviewed_actions"][0]["text"] += "？"
        with self.assertRaisesRegex(MODULE.InventoryError, "approved text"):
            self.validate(bad)

        # baseline_protocol must equal the exact baseline ZH variant.
        bad = copy.deepcopy(records)
        card = next(c for c in bad[1:] if c["key"] == "_singing_no_tension_")
        card["reviewed_actions"][0]["baseline_protocol"][
            "random_site_counts"] = [3, 3]
        with self.assertRaisesRegex(
            MODULE.InventoryError, "baseline_protocol does not match"
        ):
            self.validate(bad)

        # new_protocol must be derived exactly from the approved text.
        bad = copy.deepcopy(records)
        card = next(c for c in bad[1:] if c["key"] == "_singing_no_tension_")
        card["reviewed_actions"][0]["new_protocol"][
            "random_site_counts"] = [2, 2]
        with self.assertRaisesRegex(
            MODULE.InventoryError, "new_protocol random_site_counts"
        ):
            self.validate(bad)

        # A transition may not change weight.
        bad = copy.deepcopy(records)
        card = next(c for c in bad[1:] if c["key"] == "_singing_no_tension_")
        card["reviewed_actions"][0]["new_protocol"]["weight"] = 20
        with self.assertRaisesRegex(
            MODULE.InventoryError, "must not change weight"
        ):
            self.validate(bad)

        # A transition record with the add/remove field set is malformed.
        bad = copy.deepcopy(records)
        card = next(c for c in bad[1:] if c["key"] == "_singing_no_tension_")
        card["reviewed_actions"][0] = {
            "kind": "protocol_transition", "variant_ordinal": 5,
            "text": "x", "rationale": "x",
        }
        with self.assertRaisesRegex(MODULE.InventoryError, "field set mismatch"):
            self.validate(bad)

        # A transition ordinal colliding with an add/remove action fails.
        bad = copy.deepcopy(records)
        card = next(
            c for c in bad[1:] if c["key"] == "_speaking_high_tension_"
        )
        card["reviewed_actions"].append({
            "kind": "protocol_transition", "variant_ordinal": 1,
            "baseline_protocol": {
                "weight": 10, "control_prefix": None, "runtime_tokens": [],
                "random_site_counts": [], "lua_blocks": [],
            },
            "text": "x", "new_protocol": {
                "weight": 10, "control_prefix": None, "runtime_tokens": [],
                "random_site_counts": [], "lua_blocks": [],
            },
            "rationale": "碰撞测试。",
        })
        with self.assertRaisesRegex(MODULE.InventoryError, "collides with"):
            self.validate(bad)

    def test_protocol_transition_slot_candidate_drift_is_rejected(self):
        """The approved transition slot cannot drift at the candidate gate.

        The review records stay bound to the approved text; a candidate that
        moves the slot back to the baseline [2,2] shape or to [3,3] fails
        against the approved new protocol even though the ledger agrees with
        itself.
        """
        records = self.review_records_for()
        for label, replacement in (
            ("revert to baseline",
             "@The_weapon@[几乎|很明显][奏出了|没奏出]音乐会音高。"),
            ("over-add",
             "@The_weapon@[几乎|很明显|][奏出了|没奏出|]音乐会音高。"),
        ):
            mutated = copy.deepcopy(self.candidate_zh_artifact)
            self.zh_variant(mutated, "_singing_no_tension_", 5)[
                "raw_pattern"
            ] = replacement
            with self.subTest(case=label):
                with self.assertRaisesRegex(
                    MODULE.InventoryError,
                    "protocol drift.*random_site_counts",
                ):
                    self.add_candidate(self.candidate_en_artifact, mutated,
                                       records)

    def test_candidate_variant_count_drift_is_rejected(self):
        records = self.review_records_for()
        trimmed = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in trimmed["entries"]
            if entry["canonical_key"] == "weapon_noises"
        )
        entry["variants"].pop()
        for ordinal, variant in enumerate(entry["variants"]):
            variant["locator"]["variant_ordinal"] = ordinal
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            self.add_candidate(self.candidate_en_artifact, trimmed, records)

    def test_candidate_rejects_malicious_insertions_and_deletions(self):
        records = self.review_records_for()

        def renumber(entry):
            for ordinal, variant in enumerate(entry["variants"]):
                variant["locator"]["variant_ordinal"] = ordinal
            return entry

        # Unreviewed extra insertion in a no-action key.
        bad = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "weapon_noises"
        )
        entry["variants"].insert(3, copy.deepcopy(entry["variants"][2]))
        renumber(entry)
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            self.add_candidate(self.candidate_en_artifact, bad, records)

        # Unreviewed insertion inside an action key at a non-action position.
        bad = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "_scream_"
        )
        entry["variants"].insert(5, copy.deepcopy(entry["variants"][5]))
        renumber(entry)
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            self.add_candidate(self.candidate_en_artifact, bad, records)

        # Unreviewed deletion of a matched variant.
        bad = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "weapon_noises"
        )
        entry["variants"].pop(3)
        renumber(entry)
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            self.add_candidate(self.candidate_en_artifact, bad, records)

        # The approved removal not applied: the orphan is retained.
        bad = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "_speaking_high_tension_"
        )
        orphan = copy.deepcopy(
            self.zh_variant(self.zh_artifact, "_speaking_high_tension_", 1)
        )
        entry["variants"].insert(1, orphan)
        renumber(entry)
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            self.add_candidate(self.candidate_en_artifact, bad, records)

    def test_candidate_rejects_reorder_and_add_text_drift(self):
        records = self.review_records_for()

        # Malicious reorder of two matched variants (patterns swapped).  The
        # swapped patterns carry each other's protocol tuples, so the gate
        # rejects the reorder at the protocol binding (random-site shape at
        # the first swapped ordinal) before any text comparison.
        bad = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "weapon_noises"
        )
        entry["variants"][1]["raw_pattern"], entry["variants"][2]["raw_pattern"] = (
            entry["variants"][2]["raw_pattern"], entry["variants"][1]["raw_pattern"]
        )
        for ordinal, variant in enumerate(entry["variants"]):
            variant["locator"]["variant_ordinal"] = ordinal
        with self.assertRaisesRegex(MODULE.InventoryError, "protocol drift"):
            self.add_candidate(self.candidate_en_artifact, bad, records)

        # Approved add slot text changed (protocol preserved).
        bad = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "_instrumental_noises_"
        )
        entry["variants"][8]["raw_pattern"] = (
            "@Your_weapon@发出像卡祖笛一样的嗡鸣声。"
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "text drift"):
            self.add_candidate(self.candidate_en_artifact, bad, records)

    def test_candidate_remove_at_wrong_ordinal_is_rejected(self):
        # The orphan removal applied at a different baseline position: counts
        # stay equal, but the walk must fail at the shifted matched position
        # (the orphan text carries a protocol tuple outside the frozen
        # pairing envelope of the slot it now occupies).
        records = self.review_records_for()
        bad = copy.deepcopy(self.candidate_zh_artifact)
        entry = next(
            entry for entry in bad["entries"]
            if entry["canonical_key"] == "_speaking_high_tension_"
        )
        orphan = copy.deepcopy(
            self.zh_variant(self.zh_artifact, "_speaking_high_tension_", 1)
        )
        entry["variants"].insert(1, orphan)
        entry["variants"].pop(2)
        for ordinal, variant in enumerate(entry["variants"]):
            variant["locator"]["variant_ordinal"] = ordinal
        with self.assertRaisesRegex(MODULE.InventoryError, "protocol drift"):
            self.add_candidate(self.candidate_en_artifact, bad, records)

    def test_review_actions_schema_fails_closed(self):
        # Missing field on a card.
        bad = copy.deepcopy(self.review_records_for())
        del bad[1]["reviewed_actions"]
        with self.assertRaisesRegex(MODULE.InventoryError, "field set mismatch"):
            self.validate(bad)

        # Unknown kind.
        bad = copy.deepcopy(self.review_records_for())
        card = next(card for card in bad[1:] if card["key"] == "_instrumental_noises_")
        card["reviewed_actions"][0]["kind"] = "move"
        with self.assertRaisesRegex(MODULE.InventoryError, "kind mismatch"):
            self.validate(bad)

        # Duplicate (kind, ordinal).
        bad = copy.deepcopy(self.review_records_for())
        card = next(card for card in bad[1:] if card["key"] == "_instrumental_noises_")
        card["reviewed_actions"].append(
            copy.deepcopy(card["reviewed_actions"][0])
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "duplicate reviewed action"):
            self.validate(bad)

        # Add ordinal beyond the EN variants.
        bad = copy.deepcopy(self.review_records_for())
        card = next(card for card in bad[1:] if card["key"] == "fungus thoughts")
        card["reviewed_actions"][0]["variant_ordinal"] = 14
        with self.assertRaisesRegex(MODULE.InventoryError, "exceeds EN variants"):
            self.validate(bad)

        # Remove ordinal beyond the ZH variants.
        bad = copy.deepcopy(self.review_records_for())
        card = next(
            card for card in bad[1:] if card["key"] == "_speaking_high_tension_"
        )
        card["reviewed_actions"][0]["variant_ordinal"] = 33
        with self.assertRaisesRegex(MODULE.InventoryError, "exceeds ZH variants"):
            self.validate(bad)

        # Remove text must equal the exact baseline orphan.
        bad = copy.deepcopy(self.review_records_for())
        card = next(
            card for card in bad[1:] if card["key"] == "_speaking_high_tension_"
        )
        card["reviewed_actions"][0]["text"] = "错误文本。"
        with self.assertRaisesRegex(MODULE.InventoryError, "remove action text"):
            self.validate(bad)

        # In-range add must borrow the proposal slot.
        bad = copy.deepcopy(self.review_records_for())
        card = next(card for card in bad[1:] if card["key"] == "_instrumental_noises_")
        card["proposed_translation"][8] = card["current_chinese"][8]
        card["variant_reviews"][8]["proposed_translation"] = (
            card["current_chinese"][8]
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "placeholder"):
            self.validate(bad)

        # Add text protocol must match the baseline EN variant.
        bad = copy.deepcopy(self.review_records_for())
        card = next(card for card in bad[1:] if card["key"] == "_instrumental_noises_")
        card["reviewed_actions"][0]["text"] = "BOGUS:发出声音。"
        with self.assertRaisesRegex(MODULE.InventoryError, "does not match the EN variant"):
            self.validate(bad)

        # Empty rationale.
        bad = copy.deepcopy(self.review_records_for())
        card = next(card for card in bad[1:] if card["key"] == "_scream_")
        card["reviewed_actions"][0]["rationale"] = ""
        with self.assertRaisesRegex(MODULE.InventoryError, "requires a rationale"):
            self.validate(bad)

        # A card with actions but an invalid action shape is rejected by the
        # candidate gate before any candidate is consumed.
        bad = copy.deepcopy(self.review_records_for())
        card = next(card for card in bad[1:] if card["key"] == "_scream_")
        card["reviewed_actions"][0]["variant_ordinal"] = -1
        with self.assertRaisesRegex(MODULE.InventoryError, "ordinal mismatch"):
            self.add_candidate(self.candidate_en_artifact,
                               copy.deepcopy(self.candidate_zh_artifact), bad)

    # ── audited input reads: no-follow descriptors, inode identity ──────

    def test_external_reads_reject_symlink_fifo_directory_and_socket(self):
        dump = self.root / "dump.json"
        dump.write_text("{}", encoding="utf-8")
        link = self.root / "dump-link.json"
        link.symlink_to(dump)
        with self.assertRaisesRegex(MODULE.InventoryError, "not a regular file"):
            MODULE._read_artifact_bytes(link, "fixture dump")

        fifo = self.root / "dump.fifo"
        os.mkfifo(fifo)
        # Rejected at inspection before any open, so a FIFO can never block
        # the read (an O_RDONLY open would hang forever).
        with self.assertRaisesRegex(MODULE.InventoryError, "not a regular file"):
            MODULE._read_artifact_bytes(fifo, "fixture dump")

        directory = self.root / "dump-dir"
        directory.mkdir()
        with self.assertRaisesRegex(MODULE.InventoryError, "not a regular file"):
            MODULE._read_artifact_bytes(directory, "fixture dump")

        sock = self.root / "dump.sock"
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(sock))
            with self.assertRaisesRegex(
                MODULE.InventoryError, "not a regular file"
            ):
                MODULE._read_artifact_bytes(sock, "fixture dump")

    def test_external_read_rejects_transient_substitution_before_open(self):
        path = self.root / "sub.json"
        replacement = self.root / "replacement.json"
        path.write_text("ORIGINAL\n", encoding="utf-8")
        replacement.write_text("REPLACEMENT\n", encoding="utf-8")
        real_open = os.open

        def swap_before_open(target, flags):
            if os.fspath(target) == _open_target(path):
                path.unlink()
                replacement.replace(path)
            return real_open(target, flags)

        with mock.patch.object(os, "open", side_effect=swap_before_open):
            with self.assertRaisesRegex(
                MODULE.InventoryError,
                "changed between inspection and open",
            ):
                MODULE._read_artifact_bytes(path, "substitution fixture")

    def test_external_read_rejects_concurrent_swap_and_restore(self):
        path = self.root / "swap.json"
        original = self.root / "original.json"
        replacement = self.root / "replacement.json"
        path.write_text("ORIGINAL\n", encoding="utf-8")
        replacement.write_text("REPLACEMENT\n", encoding="utf-8")
        real_open = os.open

        def swap_before_open_and_restore(target, flags):
            if os.fspath(target) != _open_target(path):
                return real_open(target, flags)
            path.replace(original)
            replacement.replace(path)
            try:
                return real_open(target, flags)
            finally:
                # Restore the original pathname before the caller resumes:
                # the read must already have been rejected on inode identity,
                # so a later clean-check cannot be evaded by a restored path.
                original.replace(path)

        with mock.patch.object(
            os, "open", side_effect=swap_before_open_and_restore
        ):
            with self.assertRaisesRegex(
                MODULE.InventoryError,
                "changed between inspection and open",
            ):
                MODULE._read_artifact_bytes(path, "swap fixture")
        self.assertEqual("ORIGINAL\n", path.read_text(encoding="utf-8"))

    def test_external_read_swap_hook_tracks_alias_normalized_target(self):
        """Darwin /var alias simulation: the hook matches the open target.

        AuditSnapshot.read rewrites macOS's fixed /var -> /private/var
        (and /tmp -> /private/tmp) aliases before os.open, so the
        adversarial swap hook must compare against the normalized form,
        never the raw supplied path.  Linux CI has no /var alias, so this
        regression reproduces the Darwin rewrite with a real symlink alias
        tree under the temp root plus a fake _known_system_temp_alias that
        rewrites exactly like Darwin, and proves the whole external-read
        path still rejects the substitution end-to-end.
        """
        alias_root = self.root / "alias-tree"
        private_root = alias_root / "private" / "var"
        var_link = alias_root / "var"
        private_root.mkdir(parents=True)
        var_link.symlink_to(private_root, target_is_directory=True)

        path = var_link / "sub.json"
        replacement = private_root / "replacement.json"
        path.write_text("ORIGINAL\n", encoding="utf-8")
        replacement.write_text("REPLACEMENT\n", encoding="utf-8")
        real_open = os.open
        real_alias = MODULE.audit_inputs._known_system_temp_alias
        alias_prefix = os.fspath(var_link) + os.sep
        private_prefix = os.fspath(private_root) + os.sep

        def darwin_style_alias(value):
            text = os.fspath(value)
            if text.startswith(alias_prefix):
                value = Path(private_prefix + text[len(alias_prefix):])
            # Keep the real platform normalization for the temp prefix
            # (a no-op on Linux, the /var -> /private/var rewrite on macOS).
            return real_alias(value)

        def swap_before_open(target, flags):
            if os.fspath(target) == _open_target(path):
                path.unlink()
                replacement.replace(path)
            return real_open(target, flags)

        with mock.patch.object(
            MODULE.audit_inputs, "_known_system_temp_alias",
            side_effect=darwin_style_alias,
        ), mock.patch.object(os, "open", side_effect=swap_before_open):
            with self.assertRaisesRegex(
                MODULE.InventoryError,
                "changed between inspection and open",
            ):
                MODULE._read_artifact_bytes(path, "darwin alias fixture")

    def test_candidate_tree_blob_reads_require_regular_files(self):
        ledger_bytes = MODULE._candidate_regular_blob(
            CANDIDATE, "docs/wpnnoise-review-results.md", "ledger fixture"
        )
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "show",
             f"{CANDIDATE}:docs/wpnnoise-review-results.md"],
        )
        self.assertEqual(raw, ledger_bytes)
        # A real tree entry is not a regular blob: rejected before any
        # content is consumed, so an unsupported Git object type can never
        # be parsed with checkout semantics.
        with self.assertRaisesRegex(MODULE.InventoryError, "not a regular file"):
            MODULE._candidate_regular_blob(
                CANDIDATE, "crawl-ref/source/dat/database", "ledger fixture"
            )

    def test_english_tree_mode_is_required(self):
        # The real frozen baseline passes the regular-file pre-flight for
        # both the English manifest chain and the localized tree.
        MODULE._require_regular_git_sources(BASELINE, "database/", "fixture EN")
        MODULE._require_regular_git_sources(
            BASELINE, "database/zh/", "fixture ZH")

        real_blob = MODULE.audit_inputs.read_regular_git_blob

        def symlink_manifest_entry(repo, ref, git_path, *, with_mode=False):
            if git_path == "crawl-ref/source/database.cc":
                raise MODULE.audit_inputs.AuditInputError(
                    f"Git entry is not a regular file: {ref}:{git_path}"
                )
            return real_blob(repo, ref, git_path, with_mode=with_mode)

        with mock.patch.object(
            MODULE.audit_inputs, "read_regular_git_blob",
            side_effect=symlink_manifest_entry,
        ):
            with self.assertRaisesRegex(
                MODULE.InventoryError, "not a regular blob"
            ):
                MODULE._require_regular_git_sources(
                    BASELINE, "database/", "fixture EN"
                )

        with self.assertRaisesRegex(MODULE.InventoryError, "not a regular blob"):
            MODULE._require_regular_git_blobs(
                BASELINE, ["crawl-ref/source/dat/database"], "fixture"
            )

    def test_repo_relative_git_path_rejects_escapes(self):
        self.assertEqual(
            "docs/wpnnoise-review-results.md",
            MODULE._repo_relative_git_path(
                ROOT / "docs/wpnnoise-review-results.md", "review results"
            ),
        )
        with self.assertRaisesRegex(
            MODULE.InventoryError, "inside the repository"
        ):
            MODULE._repo_relative_git_path(
                Path("/tmp/outside.md"), "review results"
            )
        with self.assertRaisesRegex(
            MODULE.InventoryError, "unsafe repository path"
        ):
            MODULE._repo_relative_git_path(
                ROOT / "docs" / ".." / "evil.md", "review results"
            )

    def test_exact_clean_check_precedes_candidate_ledger_read(self):
        calls: list[str] = []
        output = Path("/tmp") / f"wpnnoise-order-{id(self)}.json"
        arguments = [
            "--baseline-ref", BASELINE,
            "--english-dump", str(self.en_path),
            "--localized-dump", str(self.zh_path),
            "--glossary", str(ROOT / "docs/glossary.md"),
            "--review-results", str(ROOT / "docs/wpnnoise-review-results.md"),
            "--candidate-ref", CANDIDATE,
            "--candidate-english-dump", str(self.en_path),
            "--candidate-localized-dump", str(self.zh_path),
            "--inventory-output", str(output),
        ]

        def fake_clean(*_args, **_kwargs):
            calls.append("clean")

        def fake_blob(_ref, git_path, _label):
            calls.append(f"ledger:{git_path}")
            return b""

        with mock.patch.object(
            MODULE.shared, "_require_candidate_commit", side_effect=fake_clean
        ), mock.patch.object(
            MODULE, "_candidate_regular_blob", side_effect=fake_blob
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "strict begin"):
                MODULE.main(arguments)
        self.assertEqual(
            ["clean", "ledger:docs/wpnnoise-review-results.md"], calls
        )

    def test_cli_candidate_flow_reads_ledger_from_candidate_tree(self):
        # The candidate-flow inventory binds the glossary to the exact
        # candidate commit tree; the frozen worktree glossary is identical.
        cli_inventory = MODULE.build_inventory(
            BASELINE, self.en_path, self.zh_path,
            ROOT / "docs/glossary.md", glossary_ref=CANDIDATE,
        )
        self.assertEqual(self.inventory["inventory_sha256"],
                         cli_inventory["inventory_sha256"])
        self.assertEqual(self.inventory["glossary"]["sha256"],
                         cli_inventory["glossary"]["sha256"])

        records = self.review_records_for()
        ledger_text = (
            MODULE.STRICT_BEGIN + "\n```jsonl\n"
            + "\n".join(
                json.dumps(record, ensure_ascii=False, sort_keys=True)
                for record in records
            )
            + "\n```\n" + MODULE.STRICT_END + "\n"
        )
        ledger_bytes = ledger_text.encode("utf-8")
        en_path = self.root / f"cli-en-{id(self)}.json"
        zh_path = self.root / f"cli-zh-{id(self)}.json"
        en_path.write_text(
            json.dumps(self.candidate_en_artifact, ensure_ascii=False),
            encoding="utf-8",
        )
        zh_path.write_text(
            json.dumps(self.candidate_zh_artifact, ensure_ascii=False),
            encoding="utf-8",
        )
        output = Path("/tmp") / f"wpnnoise-cli-{id(self)}.json"
        output.unlink(missing_ok=True)
        arguments = [
            "--baseline-ref", BASELINE,
            "--english-dump", str(self.en_path),
            "--localized-dump", str(self.zh_path),
            "--glossary", str(ROOT / "docs/glossary.md"),
            "--review-results", str(ROOT / "docs/wpnnoise-review-results.md"),
            "--candidate-ref", CANDIDATE,
            "--candidate-english-dump", str(en_path),
            "--candidate-localized-dump", str(zh_path),
            "--inventory-output", str(output),
        ]
        captured = {}
        real_blob = MODULE._candidate_regular_blob

        def fake_blob(ref, git_path, label):
            if git_path == "docs/wpnnoise-review-results.md":
                captured["ledger_git_path"] = git_path
                return ledger_bytes
            return real_blob(ref, git_path, label)

        with mock.patch.object(
            MODULE.shared, "_require_candidate_commit"
        ), mock.patch.object(
            MODULE, "_candidate_regular_blob", side_effect=fake_blob
        ):
            self.assertEqual(0, MODULE.main(arguments))
        self.assertEqual("docs/wpnnoise-review-results.md",
                         captured["ledger_git_path"])
        self.assertTrue(output.exists())
        output.unlink()

    # ── CLI safe output ──────────────────────────────────────────────────

    def test_cli_exclusive_tmp_output(self):
        output = Path("/tmp") / f"wpnnoise-test-{id(self)}.json"
        arguments = [
            "--baseline-ref", BASELINE,
            "--english-dump", str(self.en_path),
            "--localized-dump", str(self.zh_path),
            "--glossary", str(ROOT / "docs/glossary.md"),
            "--inventory-output", str(output),
        ]
        derive = lambda _oid, directory, _label, **kwargs: derived_of(  # noqa: E731
            self.en_artifact if directory == "database/" else self.zh_artifact
        )
        with mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            self.assertEqual(0, MODULE.main(arguments))
            with self.assertRaisesRegex(MODULE.InventoryError, "exclusively create"):
                MODULE.main(arguments)
        output.unlink()

        outside = arguments[:-1] + [str(self.root / "out.json")]
        with mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "/tmp"):
                MODULE.main(outside)


if __name__ == "__main__":
    unittest.main()
