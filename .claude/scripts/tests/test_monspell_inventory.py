#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/monspell_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
from audit_monspell_phase0 import build_inventory as build_phase0_inventory  # noqa: E402

SPEC = importlib.util.spec_from_file_location("monspell_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BASELINE = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD^"],
    check=True, text=True, capture_output=True,
).stdout.strip()
CANDIDATE = subprocess.run(
    ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
    check=True, text=True, capture_output=True,
).stdout.strip()


def _git_plumbing(arguments: list[str], input_text: str | None = None) -> str:
    """Run a Git plumbing command in ROOT and return its trimmed stdout."""
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "monspell test",
        "GIT_AUTHOR_EMAIL": "monspell-test@example.invalid",
        "GIT_COMMITTER_NAME": "monspell test",
        "GIT_COMMITTER_EMAIL": "monspell-test@example.invalid",
    }
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *arguments], input=input_text,
        check=True, capture_output=True, text=True, env=env,
    )
    return completed.stdout.strip()


def commit_manifest_dir(directory: Path) -> str:
    """Create a dangling commit whose tree contains the manifest fixture.

    The commit is created purely through plumbing (hash-object/mktree/
    commit-tree), so the working tree, index, and refs are never touched.
    The tree nests the fixture at ``directory``'s repository-relative path,
    matching the exact-Git snapshot reads of ``_manifest_snapshot_at_oid``.
    The returned OID is used as the synthetic baseline for build_inventory
    so that the exact-Git manifest snapshot path is exercised for real.
    """

    def tree_for(prefix: Path) -> str:
        entries = []
        for child in sorted(prefix.iterdir(), key=lambda item: item.name):
            if child.is_dir():
                oid = tree_for(child)
                kind, mode = "tree", "040000"
            else:
                oid = _git_plumbing(["hash-object", "-w", str(child)])
                kind, mode = "blob", "100644"
            entries.append(f"{mode} {kind} {oid}\t{child.name}\n")
        return _git_plumbing(["mktree"], "".join(entries))

    tree = tree_for(directory)
    relative = directory.resolve().relative_to(ROOT.resolve())
    for part in reversed(relative.parts):
        tree = _git_plumbing(["mktree"], f"040000 tree {tree}\t{part}\n")
    return _git_plumbing(
        ["commit-tree", tree, "-m", "monspell fixture manifest"]
    )

KEYS = [
    "alpha strike cast",
    "beta beam cast",
    "gamma gaze cast",
    "delta orb cast",
    "epsilon chant cast",
    "zeta summon cast",
    "eta word cast",
    "theta flee cast",
    "iota glyph cast",
    "kappa rune cast",
    "lambda shield cast",
    "mu ward cast",
]
SORTED_KEYS = sorted(KEYS)
UNREACHABLE = {"eta word cast", "theta flee cast"}
REACHABLE = [key for key in KEYS if key not in UNREACHABLE]

EN_PATTERNS = {
    "alpha strike cast": ["@The_monster@ alpha strike.", "@The_monster@ alpha barrage."],
    "beta beam cast": ["@The_monster@ emits @beam@ at @target@."],
    "gamma gaze cast": ["VISUAL:@The_monster@ glows [brightly|dimly].",
                        "@The_monster@ waves."],
    "delta orb cast": ["@The_monster@ [pulses|vibrates].", "@The_monster@ glows."],
    "epsilon chant cast": ["@The_monster@ chants."],
    "zeta summon cast": ["@The_monster@ summons.", "@The_monster@ calls."],
    "eta word cast": ["You hear a word."],
    "theta flee cast": ["@The_monster@ casts a spell."],
    "iota glyph cast": ["@The_monster@ inscribes."],
    "kappa rune cast": ["@The_monster@ carves a rune."],
    "lambda shield cast": ["@The_monster@ raises a shield.", "@The_monster@ braces."],
    "mu ward cast": ["@The_monster@ wards."],
}
ZH_PATTERNS = {
    "alpha strike cast": ["@The_monster@阿尔法突击。", "@The_monster@阿尔法齐射。"],
    "beta beam cast": ["@The_monster@朝@target@发射@beam@。"],
    "gamma gaze cast": ["VISUAL:@The_monster@发出[明亮|暗淡]的光芒。",
                        "@The_monster@挥了挥手。"],
    "delta orb cast": ["@The_monster@[脉动|振动]。", "@The_monster@发光。"],
    "epsilon chant cast": ["@The_monster@吟唱。"],
    "zeta summon cast": ["@The_monster@召唤。", "@The_monster@呼唤。"],
    "eta word cast": ["你听到一个词。"],
    "theta flee cast": ["@The_monster@施法。"],
    "iota glyph cast": ["@The_monster@铭刻。"],
    "kappa rune cast": ["@The_monster@雕刻符文。"],
    "lambda shield cast": ["@The_monster@架起盾牌。"],
    "mu ward cast": ["@The_monster@防护。", "@The_monster@警戒。"],
}


def dump_source(language: str) -> str:
    patterns_by_key = EN_PATTERNS if language == "en" else ZH_PATTERNS
    blocks = []
    for key in SORTED_KEYS:
        blocks.append("%%%%")
        blocks.append(key)
        blocks.append("")
        blocks.extend(patterns_by_key[key])
        blocks.append("")
    return "\n".join(blocks) + "\n"


def make_dump(language: str) -> dict:
    directory = "database/" if language == "en" else "database/zh/"
    source_name = f"{directory}monspell.txt"
    patterns_by_key = EN_PATTERNS if language == "en" else ZH_PATTERNS
    entries = []
    for ordinal, key in enumerate(SORTED_KEYS):
        provenance = {
            "source_name": source_name,
            "load_index": 0,
            "definition_ordinal": ordinal,
        }
        patterns = patterns_by_key[key]
        entries.append({
            "canonical_key": key,
            "effective_provenance": provenance,
            "raw_body": "\n\n".join(patterns) + "\n",
            "source_history": [provenance],
            "variants": [
                {
                    "locator": {"canonical_key": key, "variant_ordinal": index},
                    "provenance": provenance,
                    "weight": 10,
                    "raw_pattern": pattern,
                }
                for index, pattern in enumerate(patterns)
            ],
            "parse_error": None,
            "body_empty": False,
        })
    return {
        "schema_version": 1,
        "database_name": "speak",
        "source_directory": directory,
        "sources": [{
            "source_name": source_name,
            "load_index": 0,
            "normalized_utf8": dump_source(language),
        }],
        "entries": entries,
    }


def line_metadata(sensory: str, relations: dict) -> list[dict]:
    templates = []
    for relation, (en_pattern, zh_pattern) in relations.items():
        templates.append({"language": "en", "relation": relation,
                          "pattern": en_pattern})
        templates.append({"language": "zh", "relation": relation,
                          "pattern": zh_pattern})
    return [{
        "sensory": sensory,
        "channel": None,
        "behavior": {"implies_gesture": False, "audible": False},
        "templates": templates,
    }]


def catalog_variant(
    key: str, ordinal: int, policy: str = "NONE", *,
    line_metadata_items: list[dict] | None = None,
    cases: list[dict] | None = None,
    english_snapshot: str | None = None,
    stable_id: str | None = None,
) -> dict:
    return {
        "stable_id": stable_id or f"mon.cast.fixture.{key.replace(' ', '_')}.v{ordinal}",
        "tombstone": False,
        "variant_ordinal": ordinal,
        "upstream_variant_fingerprint": f"fixture-upstream-{key}-{ordinal}",
        "upstream_weight": 10,
        "english_snapshot": english_snapshot
        if english_snapshot is not None
        else EN_PATTERNS[key][ordinal],
        "frame": "DIRECT_EFFECT",
        "binding": {"resolves_target": False},
        "applicability": {
            "requires_player": False, "requires_foe": False,
            "requires_named_foe": False, "requires_god": False,
            "requires_caster_visible": False,
        },
        "materialization_policy": policy,
        "slot_schema": [],
        "required_arguments": [],
        "line_metadata": line_metadata_items or [],
        "materialization_cases": cases or [],
        "recursive_dependency_fingerprints": {},
    }


def catalog_entry(key: str, mode: str, variants: list[dict]) -> dict:
    return {
        "canonical_key": key,
        "canonical_fingerprint": f"fnv1a64:fixture-{key}",
        "selection_graph_fingerprint": f"fnv1a64:selection-{key}",
        "mode": mode,
        "variants": variants,
    }


def fixture_catalog_entries() -> list[dict]:
    entries = []
    # alpha: STRUCTURED, two NONE templates
    entries.append(catalog_entry("alpha strike cast", "CANDIDATE", [
        catalog_variant("alpha strike cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("@The_monster@ alpha strike.",
                                     "@The_monster@阿尔法突击。")})),
        catalog_variant("alpha strike cast", 1,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("@The_monster@ alpha barrage.",
                                     "@The_monster@阿尔法齐射。")})),
    ]))
    # beta: STRUCTURED, AT/NEXT_TO/PAST
    entries.append(catalog_entry("beta beam cast", "CANDIDATE", [
        catalog_variant("beta beam cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "AT": ("${actor} emits ${beam} at ${target}.",
                                   "${actor}朝${target}发射${beam}。"),
                            "NEXT_TO": ("${actor} emits ${beam} next to ${target}.",
                                        "${actor}朝${target}旁边发射${beam}。"),
                            "PAST": ("${actor} emits ${beam} past ${target}.",
                                     "${actor}发射${beam}，掠过${target}。")})),
    ]))
    # gamma: STRUCTURED, VISUAL sensory template + VISUAL legacy prefix
    entries.append(catalog_entry("gamma gaze cast", "CANDIDATE", [
        catalog_variant("gamma gaze cast", 0,
                        line_metadata_items=line_metadata("VISUAL", {
                            "NONE": ("${actor} glows [brightly|dimly].",
                                     "${actor}发出[明亮|暗淡]的光芒。")})),
        catalog_variant("gamma gaze cast", 1,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} waves.",
                                     "${actor}挥了挥手。")})),
    ]))
    # delta: STRUCTURED, mixed policy [CASE_MAP, NONE]
    delta_cases = [
        {"case_id": "mon.cast.delta_orb.pulses.v1",
         "signature": "materialization-v1|fixture",
         "line_metadata": line_metadata("PLAIN", {
             "NONE": ("${actor} pulses.", "${actor}脉动。")})},
        {"case_id": "mon.cast.delta_orb.vibrates.v1",
         "signature": "materialization-v1|fixture",
         "line_metadata": line_metadata("PLAIN", {
             "NONE": ("${actor} vibrates.", "${actor}振动。")})},
    ]
    entries.append(catalog_entry("delta orb cast", "CANDIDATE", [
        catalog_variant("delta orb cast", 0, "CASE_MAP", cases=delta_cases),
        catalog_variant("delta orb cast", 1,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} glows.", "${actor}发光。")})),
    ]))
    # epsilon: SUPPRESSED (CANDIDATE with __NONE)
    entries.append(catalog_entry("epsilon chant cast", "CANDIDATE", [
        catalog_variant("epsilon chant cast", 0, "NONE",
                        english_snapshot="__NONE",
                        stable_id="mon.cast.epsilon_chant.suppress.v1"),
    ]))
    # zeta: LEGACY_ONLY, no catalog templates
    entries.append(catalog_entry("zeta summon cast", "LEGACY_ONLY", [
        catalog_variant("zeta summon cast", 0, "LEGACY_ONLY"),
    ]))
    # eta: CLOSURE_ONLY, catalog zh template exists but route is LEGACY
    entries.append(catalog_entry("eta word cast", "CLOSURE_ONLY", [
        catalog_variant("eta word cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("You hear a word.", "你听到一个词。")})),
    ]))
    # theta: STRUCTURED but unreachable in the candidate dump
    entries.append(catalog_entry("theta flee cast", "CANDIDATE", [
        catalog_variant("theta flee cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} casts a spell.",
                                     "${actor}施法。")})),
    ]))
    # iota / kappa: STRUCTURED single templates
    entries.append(catalog_entry("iota glyph cast", "CANDIDATE", [
        catalog_variant("iota glyph cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} inscribes.", "${actor}铭刻。")})),
    ]))
    entries.append(catalog_entry("kappa rune cast", "CANDIDATE", [
        catalog_variant("kappa rune cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} carves a rune.", "${actor}雕刻符文。")})),
    ]))
    # lambda: STRUCTURED with frozen EN/ZH legacy asymmetry (2, 1)
    entries.append(catalog_entry("lambda shield cast", "CANDIDATE", [
        catalog_variant("lambda shield cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} raises a shield.",
                                     "${actor}架起盾牌。")})),
        catalog_variant("lambda shield cast", 1,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} braces.", "${actor}稳住身形。")})),
    ]))
    # mu: STRUCTURED with frozen EN/ZH legacy asymmetry (1, 2)
    entries.append(catalog_entry("mu ward cast", "CANDIDATE", [
        catalog_variant("mu ward cast", 0,
                        line_metadata_items=line_metadata("PLAIN", {
                            "NONE": ("${actor} wards.", "${actor}防护。")})),
    ]))
    return entries


def fixture_manifest(phase0_semantic: str) -> tuple[dict, dict[str, list[dict]]]:
    entries = fixture_catalog_entries()
    header = {
        "schema_version": 1,
        "domain": "monspell",
        "supported_languages": ["en", "zh"],
        "inventory_semantic_fingerprint": phase0_semantic,
        "catalog_order": list(KEYS),
        "fragment_glob": "monspell/*.json",
    }
    fragments = {
        "monspell/000-a.json": {"entries": entries[:5], "tombstones": []},
        "monspell/001-b.json": {"entries": entries[5:], "tombstones": []},
    }
    return header, fragments


def fixture_phase0(en_dump: dict) -> dict:
    return build_phase0_inventory(en_dump)


def fixture_report(phase0_semantic: str, anchor_sha: str) -> dict:
    return {
        "schema_version": 1,
        "domain": "monspell",
        "phase2_ready": True,
        "phase2_blockers": [],
        "coverage": {
            "catalog_coverage_complete": True,
            "en_zh_behavior_parity_proven": True,
        },
        "universe": {
            "candidate_key_containment_proven": True,
            "inventory_root_count": len(KEYS),
            "inventory_reachable_root_count": len(REACHABLE),
            "inventory_unreachable_root_count": len(UNREACHABLE),
            "runtime_roots": list(REACHABLE),
            "inventory_unreachable_roots": sorted(UNREACHABLE),
        },
        "candidate_lookup": {
            "en": {"hit_count": len(REACHABLE)},
            "zh": {"hit_count": len(REACHABLE)},
        },
        "locale_presence_mismatch": [],
        "locale_behavior_mismatch": [],
        "locale_behavior_inconclusive": [],
        "inputs": {
            "inventory": {"semantic_fingerprint": phase0_semantic},
            "candidate_anchor": {"artifact_sha256": anchor_sha},
        },
    }


def fixture_anchor() -> dict:
    return {
        "schema_version": 1,
        "domain": "monspell_candidate_lookup",
        "artifact_sha256": MODULE.EXPECTED_CANDIDATE_ANCHOR_SHA256,
    }


class MonspellInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.glossary = cls.root / "glossary.md"
        cls.glossary.write_text("glossary fixture\n", encoding="utf-8")
        cls.en_dump = make_dump("en")
        cls.zh_dump = make_dump("zh")
        cls.phase0 = fixture_phase0(cls.en_dump)
        header, fragments = fixture_manifest(cls.phase0["semantic_fingerprint"])
        cls.fixture_tmp = tempfile.TemporaryDirectory(
            dir=ROOT / ".claude/scripts/tests"
        )
        cls.manifest_dir = Path(cls.fixture_tmp.name)
        (cls.manifest_dir / "monspell").mkdir()
        (cls.manifest_dir / "monspell.json").write_text(
            json.dumps(header, ensure_ascii=False), encoding="utf-8"
        )
        for name, fragment in fragments.items():
            (cls.manifest_dir / name).write_text(
                json.dumps(fragment, ensure_ascii=False), encoding="utf-8"
            )
        cls.manifest_path = cls.manifest_dir / "monspell.json"
        cls.fixture_baseline = commit_manifest_dir(cls.manifest_dir)
        cls.report = fixture_report(
            cls.phase0["semantic_fingerprint"],
            MODULE.EXPECTED_CANDIDATE_ANCHOR_SHA256,
        )
        cls.anchor = fixture_anchor()

    @classmethod
    def tearDownClass(cls):
        cls.fixture_tmp.cleanup()
        cls.temp.cleanup()

    @contextlib.contextmanager
    def patched(self):
        overrides = {
            "EXPECTED_IDENTITY_COUNT": len(KEYS),
            "EXPECTED_REACHABLE_COUNT": len(REACHABLE),
            "EXPECTED_UNREACHABLE_COUNT": len(UNREACHABLE),
            "EXPECTED_EN_VARIANT_COUNT": 17,
            "EXPECTED_ZH_VARIANT_COUNT": 17,
            "EXPECTED_EN_TOKEN_SITES": 18,
            "EXPECTED_ZH_TOKEN_SITES": 18,
            "EXPECTED_RANDOM_SUBSTRING_SITES": 2,
            "EXPECTED_LUA_SITES": 0,
            "EXPECTED_VISUAL_PREFIXES": 1,
            "EXPECTED_MODE_COUNTS": {
                "CANDIDATE": 10, "LEGACY_ONLY": 1, "CLOSURE_ONLY": 1,
            },
            "EXPECTED_ROUTE_COUNTS": {
                "STRUCTURED": 9, "LEGACY": 2, "SUPPRESSED": 1,
            },
            "EXPECTED_PRIMARY_POLICY_COUNTS": {
                "NONE": 10, "CASE_MAP": 1, "LEGACY_ONLY": 1,
            },
            "EXPECTED_MIXED_POLICY_KEYS": {
                "delta orb cast": ["CASE_MAP", "NONE"],
            },
            "EXPECTED_SUPPRESSED_KEYS": {"epsilon chant cast"},
            "EXPECTED_NO_ZH_ENTRY_COUNT": 2,
            "EXPECTED_STRUCTURED_TEMPLATE_COUNT": 17,
            "EXPECTED_STRUCTURED_RELATION_COUNTS": {
                "AT": 1, "NEXT_TO": 1, "PAST": 1, "NONE": 14,
            },
            "EXPECTED_LINE_METADATA_RELATION_COUNTS": {
                "AT": 1, "NEXT_TO": 1, "PAST": 1, "NONE": 12,
            },
            "EXPECTED_CASE_RELATION_COUNTS": {"NONE": 2},
            "EXPECTED_SENSORY_COUNTS": {"PLAIN": 14, "VISUAL": 1},
            "ASYMMETRIC_VARIANT_KEYS": {
                "lambda shield cast": (2, 1), "mu ward cast": (1, 2),
            },
            "EXPECTED_SEMANTIC_FINGERPRINT": self.phase0["semantic_fingerprint"],
            "EXPECTED_SOURCE_FINGERPRINT": self.phase0["source_fingerprint"],
        }
        with mock.patch.multiple(MODULE, **overrides):
            yield

    def write(self, name: str, value: dict) -> Path:
        path = self.root / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def make_manifest_dir(self, name: str) -> Path:
        """Create a repository-internal manifest fixture directory."""
        manifest_dir = Path(self.fixture_tmp.name) / name
        manifest_dir.mkdir(exist_ok=True)
        (manifest_dir / "monspell").mkdir(exist_ok=True)
        return manifest_dir

    @staticmethod
    def derived(value: dict) -> dict:
        source = f"{value['source_directory']}monspell.txt"
        return {
            "sources": copy.deepcopy(value["sources"]),
            "entries": [
                copy.deepcopy(entry) for entry in value["entries"]
                if any(item["source_name"] == source
                       for item in entry["source_history"])
            ],
        }

    def build(self, en=None, zh=None, phase0=None, report=None, anchor=None,
               manifest_path=None, baseline_ref=None):
        en_value = en or self.en_dump
        zh_value = zh or self.zh_dump
        en_path = self.write("en.json", en_value)
        zh_path = self.write("zh.json", zh_value)
        phase0_path = self.write("phase0.json", phase0 or self.phase0)
        report_path = self.write("report.json", report or self.report)
        anchor_path = self.write("anchor.json", anchor or self.anchor)
        with self.patched(), mock.patch.object(
            MODULE.shared, "_derive_scoped_dump",
            side_effect=[self.derived(en_value), self.derived(zh_value)],
        ):
            return MODULE.build_inventory(
                baseline_ref or self.fixture_baseline, en_path, zh_path,
                phase0_path,
                manifest_path or self.manifest_path,
                report_path, anchor_path, self.glossary,
            )

    def write_results(self, records: list[dict]) -> Path:
        path = self.root / f"results-{self.id().split('.')[-1]}.md"
        path.write_text(
            "fixture\n\n" + MODULE.STRICT_BEGIN + "\n```jsonl\n"
            + "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True)
                         for record in records)
            + "\n```\n" + MODULE.STRICT_END + "\n",
            encoding="utf-8",
        )
        return path

    def validate(self, records: list[dict], candidate=None):
        with self.patched():
            return MODULE.validate_results(
                self.write_results(records), self.inventory, candidate
            )

    def assert_rejected(self, message: str, **kwargs):
        with self.assertRaises(MODULE.InventoryError) as raised:
            self.build(**kwargs)
        self.assertIn(message, str(raised.exception))

    # ------------------------------------------------------------- fixtures

    def entry(self, key: str) -> dict:
        return next(
            entry for entry in self.inventory["entries"]
            if entry["key"] == key
        )

    def card_for(self, entry: dict, conclusion: str = "keep") -> dict:
        route = entry["route"]
        card = {
            "identity": entry["identity"],
            "key": entry["key"],
            "route": route,
            "entry_mode": entry["entry_mode"],
            "primary_materialization_policy": entry["primary_materialization_policy"],
            "runtime_evidence": entry["runtime_evidence"],
            "production_zh_source": entry["production_zh_source"],
            "fallback_zh_source": entry["fallback_zh_source"],
            "lifecycle": MODULE.FROZEN_LIFECYCLE[route],
            "actual_behavior": MODULE.FROZEN_ACTUAL_BEHAVIOR[route],
            "display_context": MODULE.FROZEN_DISPLAY_CONTEXT[route],
            "consumer": copy.deepcopy(MODULE.FROZEN_CONSUMER),
            "producers": copy.deepcopy(MODULE.FROZEN_PRODUCERS),
            "dependency_group": f"{entry['key']} 怪物施法消息路由与本地化",
            "glossary_authority": (
                f"{self.inventory['glossary']['path']}@"
                f"{self.inventory['glossary']['sha256']}"
            ),
            "evidence_locations": MODULE._expected_evidence_locations(entry),
            "production_facts": MODULE._expected_production_facts(entry),
            "current_english": [v["english"] for v in entry["legacy_variants"]],
            "current_chinese": [v["chinese"] for v in entry["legacy_variants"]],
            "current_structured_zh": MODULE._current_structured_zh(entry),
            "terminal_conclusion": conclusion,
            "confidence": "high",
            "deferral_owner": None,
            "deferral_reason": None,
            "reentry_trigger": "源、结构或生产路由变化时重新审阅。",
            "rejected_alternatives": ["不改变 lookup、权重或通道协议。"],
            "reviewer_rationale": "已核对生产来源、消费者与所有变体。" + (
                MODULE.UNREACHABLE_RATIONALE_MARKER
                if not entry["runtime_evidence"] else ""
            ),
            "structured_template_reviews": [],
            "legacy_variant_reviews": [],
            "proposed_translation": [],
            "proposed_structured_zh": [],
        }
        structured_reviews = []
        for template in entry["structured_templates"]:
            structured_reviews.append({
                "locator": copy.deepcopy(template["locator"]),
                "pattern_en": template["pattern_en"],
                "current_pattern_zh": template["pattern_zh"],
                "proposed_pattern_zh": template["pattern_zh"],
                "relation": template["relation"],
                "sensory": template["sensory"],
                "materialization_policy": template["materialization_policy"],
                "terminal_conclusion": "keep",
                "rationale": "完整审阅并保留。",
            })
        card["structured_template_reviews"] = structured_reviews
        card["proposed_structured_zh"] = [
            {
                "locator": template["locator"],
                "pattern_en": template["pattern_en"],
                "pattern_zh": review["proposed_pattern_zh"],
                "relation": template["relation"],
                "materialization_policy": template["materialization_policy"],
            }
            for template, review in zip(
                entry["structured_templates"], structured_reviews
            )
        ]
        legacy_reviews = []
        for variant in entry["legacy_variants"]:
            legacy_reviews.append({
                "variant_ordinal": variant["locator"]["variant_ordinal"],
                "weight": variant["weight"],
                "control_prefix": variant["control_prefix"],
                "runtime_tokens": variant["runtime_tokens"],
                "english": variant["english"],
                "current_chinese": variant["chinese"],
                "proposed_translation": variant["chinese"],
                "fallback": route != "LEGACY",
                "terminal_conclusion": "keep",
                "rationale": "完整审阅并保留。",
            })
        card["legacy_variant_reviews"] = legacy_reviews
        card["proposed_translation"] = [
            review["proposed_translation"] for review in legacy_reviews
        ]
        return card

    def ledger(self) -> list[dict]:
        return [
            {"baseline": self.inventory["baseline_ref"],
             "glossary_sha256": self.inventory["glossary"]["sha256"],
             "identity_count": len(self.inventory["entries"]),
             "inventory_sha256": self.inventory["inventory_sha256"]},
            *[self.card_for(entry) for entry in self.inventory["entries"]],
        ]

    def setUp(self):
        self.inventory = self.build()

    # ------------------------------------------------------------- build

    def test_build_binds_catalog_phase0_and_legacy(self):
        first = self.inventory
        second = self.build()
        self.assertEqual(first["inventory_sha256"], second["inventory_sha256"])
        self.assertEqual(12, len(first["entries"]))
        self.assertEqual(
            {entry["identity"] for entry in first["entries"]},
            {f"monspell:{key}" for key in KEYS},
        )
        by_key = {entry["key"]: entry for entry in first["entries"]}
        self.assertEqual("STRUCTURED", by_key["alpha strike cast"]["route"])
        self.assertEqual("SUPPRESSED", by_key["epsilon chant cast"]["route"])
        self.assertEqual("LEGACY", by_key["zeta summon cast"]["route"])
        self.assertEqual("LEGACY", by_key["eta word cast"]["route"])
        self.assertFalse(by_key["eta word cast"]["runtime_evidence"])
        self.assertTrue(by_key["alpha strike cast"]["runtime_evidence"])
        self.assertEqual("catalog", by_key["alpha strike cast"]["production_zh_source"])
        self.assertEqual("zh/monspell.txt",
                         by_key["alpha strike cast"]["fallback_zh_source"])
        self.assertEqual("zh/monspell.txt",
                         by_key["zeta summon cast"]["production_zh_source"])
        self.assertIsNone(by_key["zeta summon cast"]["fallback_zh_source"])
        self.assertEqual("none", by_key["epsilon chant cast"]["production_zh_source"])
        self.assertEqual(["CASE_MAP", "NONE"],
                         by_key["delta orb cast"]["policies"])
        self.assertEqual(2, len(by_key["lambda shield cast"]["legacy_variants"]))
        self.assertIsNone(by_key["lambda shield cast"]["legacy_variants"][1]["chinese"])
        self.assertEqual(0, len(by_key["lambda shield cast"]["unpaired_zh_variants"]))
        self.assertEqual(1, len(by_key["mu ward cast"]["unpaired_zh_variants"]))
        self.assertEqual(2, len(by_key["alpha strike cast"]["structured_templates"]))
        self.assertEqual([], by_key["zeta summon cast"]["structured_templates"])
        self.assertEqual([], by_key["eta word cast"]["structured_templates"])
        self.assertEqual(
            1, sum(len(entry["unpaired_zh_variants"])
                   for entry in first["entries"])
        )
        self.assertEqual("9eb63d334f31c1dfb608c7c742f2ce4046a711f7450d6de0ac516033baf3c083",
                         first["candidate_anchor"]["artifact_sha256"])
        self.assertEqual(10, first["behavior_report"]["reachable_root_count"])
        self.assertEqual(sorted(UNREACHABLE),
                         first["behavior_report"]["unreachable_roots"])

    def test_build_ignores_working_tree_manifest_mutation(self):
        # The baseline catalog manifest must be derived from exact Git blobs
        # at the baseline OID; a diverged working-tree copy at the same path
        # must not leak into entries or inventory_sha256 (Refs #59).
        manifest_dir = self.make_manifest_dir("manifest-git-regression")
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        (manifest_dir / "monspell.json").write_text(
            json.dumps(header, ensure_ascii=False), encoding="utf-8")
        for name, fragment in fragments.items():
            (manifest_dir / name).write_text(
                json.dumps(fragment, ensure_ascii=False), encoding="utf-8")
        baseline = commit_manifest_dir(manifest_dir)
        manifest_path = manifest_dir / "monspell.json"
        pristine = self.build(baseline_ref=baseline, manifest_path=manifest_path)

        # Diverging working-tree fragment: same path, different zh templates.
        fragment_path = manifest_dir / "monspell" / "000-a.json"
        mutated = copy.deepcopy(fragments["monspell/000-a.json"])
        alpha = next(e for e in mutated["entries"]
                     if e["canonical_key"] == "alpha strike cast")
        for variant in alpha["variants"]:
            for metadata in variant["line_metadata"]:
                for template in metadata["templates"]:
                    if template["language"] == "zh":
                        template["pattern"] = "${actor}工作区篡改。"
        fragment_path.write_text(
            json.dumps(mutated, ensure_ascii=False), encoding="utf-8")

        rebuilt = self.build(baseline_ref=baseline, manifest_path=manifest_path)
        self.assertEqual(pristine["inventory_sha256"],
                         rebuilt["inventory_sha256"])
        rebuilt_alpha = next(e for e in rebuilt["entries"]
                             if e["key"] == "alpha strike cast")
        self.assertTrue(rebuilt_alpha["structured_templates"])
        for template in rebuilt_alpha["structured_templates"]:
            self.assertNotEqual(template["pattern_zh"], "${actor}工作区篡改。")
        clean_alpha = next(e for e in self.inventory["entries"]
                           if e["key"] == "alpha strike cast")
        self.assertEqual(clean_alpha["structured_templates"],
                         rebuilt_alpha["structured_templates"])

    def test_consistency_assertions_fail_closed(self):
        # 1. catalog key set must equal phase0 keys
        manifest_dir = self.make_manifest_dir("manifest-drift")
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        fragments["monspell/000-a.json"]["entries"] = [
            entry for entry in fragments["monspell/000-a.json"]["entries"]
            if entry["canonical_key"] != "alpha strike cast"
        ]
        header["catalog_order"] = [
            key for key in KEYS if key != "alpha strike cast"
        ]
        (manifest_dir / "monspell.json").write_text(
            json.dumps(header, ensure_ascii=False), encoding="utf-8")
        for name, fragment in fragments.items():
            (manifest_dir / name).write_text(
                json.dumps(fragment, ensure_ascii=False), encoding="utf-8")
        drift_baseline = commit_manifest_dir(manifest_dir)
        self.assert_rejected("catalog key set mismatch",
                             manifest_path=manifest_dir / "monspell.json",
                             baseline_ref=drift_baseline)

        # 2. phase2 readiness
        report = copy.deepcopy(self.report)
        report["phase2_ready"] = False
        self.assert_rejected("phase2_ready", report=report)
        report = copy.deepcopy(self.report)
        report["phase2_blockers"] = ["candidate artifact stale"]
        self.assert_rejected("phase2_blockers", report=report)

        # 3. coverage flags
        for field in ("catalog_coverage_complete", "en_zh_behavior_parity_proven"):
            report = copy.deepcopy(self.report)
            report["coverage"][field] = False
            self.assert_rejected(field, report=report)

        # 4. universe containment
        report = copy.deepcopy(self.report)
        report["universe"]["candidate_key_containment_proven"] = False
        self.assert_rejected("candidate_key_containment_proven", report=report)

        # 5. manifest fingerprint binding
        manifest_dir = self.make_manifest_dir("manifest-fp")
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        header["inventory_semantic_fingerprint"] = "0" * 64
        (manifest_dir / "monspell.json").write_text(
            json.dumps(header, ensure_ascii=False), encoding="utf-8")
        for name, fragment in fragments.items():
            (manifest_dir / name).write_text(
                json.dumps(fragment, ensure_ascii=False), encoding="utf-8")
        fingerprint_baseline = commit_manifest_dir(manifest_dir)
        self.assert_rejected("inventory_semantic_fingerprint",
                             manifest_path=manifest_dir / "monspell.json",
                             baseline_ref=fingerprint_baseline)

        # 6. candidate anchor binding
        anchor = copy.deepcopy(self.anchor)
        anchor["artifact_sha256"] = "0" * 64
        self.assert_rejected("artifact_sha256", anchor=anchor)

        # 7. locale mismatch lists
        for field in ("locale_presence_mismatch", "locale_behavior_mismatch",
                      "locale_behavior_inconclusive"):
            report = copy.deepcopy(self.report)
            report[field] = ["unexpected drift"]
            self.assert_rejected(field, report=report)

        # phase0 semantic fingerprint binding
        phase0 = copy.deepcopy(self.phase0)
        phase0["semantic_fingerprint"] = "0" * 64
        self.assert_rejected("semantic_fingerprint", phase0=phase0)
        phase0 = copy.deepcopy(self.phase0)
        phase0["summary"]["variants"] = 99
        self.assert_rejected("summary", phase0=phase0)

        # reachability partition
        report = copy.deepcopy(self.report)
        report["universe"]["runtime_roots"] = [
            "extra root" if key == REACHABLE[0] else key
            for key in REACHABLE
        ]
        self.assert_rejected("reachability partition", report=report)
        report = copy.deepcopy(self.report)
        report["universe"]["inventory_unreachable_roots"] = ["extra root"]
        self.assert_rejected("unreachable root count", report=report)

        # candidate lookup hit counts
        report = copy.deepcopy(self.report)
        report["candidate_lookup"]["en"]["hit_count"] = 8
        self.assert_rejected("hit counts", report=report)

    def test_legacy_binding_fail_closed(self):
        expected_keys = {entry["key"] for entry in self.phase0["entries"]}

        def en_binding(value):
            with self.patched():
                return MODULE._dump_binding(value, b"fixture", "fixture EN",
                                            expected_keys)

        # EN key set drift
        en = copy.deepcopy(self.en_dump)
        en["entries"].pop(0)
        with self.assertRaisesRegex(MODULE.InventoryError, "key set mismatch"):
            en_binding(en)

        # ordinal gap
        en = copy.deepcopy(self.en_dump)
        en["entries"][1]["effective_provenance"]["definition_ordinal"] = 5
        with self.assertRaisesRegex(MODULE.InventoryError, "not contiguous"):
            en_binding(en)

        # provenance drift
        en = copy.deepcopy(self.en_dump)
        other = {"source_name": "database/other.txt", "load_index": 0,
                 "definition_ordinal": 0}
        en["entries"][2]["effective_provenance"] = other
        with self.assertRaisesRegex(MODULE.InventoryError, "not effective"):
            en_binding(en)

        # override
        en = copy.deepcopy(self.en_dump)
        en["entries"][3]["source_history"].append(
            copy.deepcopy(en["entries"][3]["effective_provenance"])
        )
        with self.assertRaisesRegex(MODULE.InventoryError, "overridden"):
            en_binding(en)

        # parse error
        en = copy.deepcopy(self.en_dump)
        en["entries"][4]["parse_error"] = "BUG, EMPTY ENTRY"
        en["entries"][4]["variants"] = []
        with self.assertRaisesRegex(MODULE.InventoryError, "parse error"):
            en_binding(en)

        # global token site count
        en = copy.deepcopy(self.en_dump)
        en["entries"][0]["variants"][0]["raw_pattern"] += "@extra@"
        with self.assertRaisesRegex(MODULE.InventoryError, "token site count"):
            en_binding(en)

        # unexpected variant-count asymmetry (frozen keys only)
        with self.patched():
            _en_binding, en_rows = MODULE._dump_binding(
                self.en_dump, b"fixture", "fixture EN", expected_keys
            )
            _zh_binding, zh_rows = MODULE._dump_binding(
                self.zh_dump, b"fixture", "fixture ZH", expected_keys
            )
        zeta_en = next(row for row in en_rows if row["key"] == "zeta summon cast")
        zeta_en["variants"].append({
            "locator": {"key": "zeta summon cast", "variant_ordinal": 2},
            "weight": 10, "control_prefix": None,
            "runtime_tokens": ["@The_monster@"],
            "random_substring_sites": [], "lua_sites": [],
            "raw_pattern": "@The_monster@ howls.",
        })
        with self.patched():
            with self.assertRaisesRegex(MODULE.InventoryError, "variant count differs"):
                MODULE._paired_entries(en_rows, zh_rows, "fixture")

        # weight drift on a paired ordinal
        zh = copy.deepcopy(self.zh_dump)
        zh["entries"][0]["variants"][0]["weight"] = 11
        self.assert_rejected("weight differs", zh=zh)

        # control prefix drift (pairing layer)
        with self.patched():
            _en_binding, en_rows = MODULE._dump_binding(
                self.en_dump, b"fixture", "fixture EN", expected_keys
            )
            _zh_binding, zh_rows = MODULE._dump_binding(
                self.zh_dump, b"fixture", "fixture ZH", expected_keys
            )
        alpha_zh = next(row for row in zh_rows
                        if row["key"] == "alpha strike cast")
        alpha_zh["variants"][0]["control_prefix"] = "VISUAL"
        with self.patched():
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "control prefix differs"):
                MODULE._paired_entries(en_rows, zh_rows, "fixture")

        # ZH token vocabulary escapes the EN vocabulary (pairing layer)
        with self.patched():
            _en_binding, en_rows = MODULE._dump_binding(
                self.en_dump, b"fixture", "fixture EN", expected_keys
            )
            _zh_binding, zh_rows = MODULE._dump_binding(
                self.zh_dump, b"fixture", "fixture ZH", expected_keys
            )
        eta_zh = next(row for row in zh_rows if row["key"] == "eta word cast")
        eta_zh["variants"][0]["runtime_tokens"] = ["@mystery@"]
        with self.patched():
            with self.assertRaisesRegex(MODULE.InventoryError, "not a subset"):
                MODULE._paired_entries(en_rows, zh_rows, "fixture")

        # ZH global VISUAL prefix count
        zh = copy.deepcopy(self.zh_dump)
        zh["entries"][0]["variants"][0]["raw_pattern"] = "VISUAL:@The_monster@前缀漂移。"
        self.assert_rejected("VISUAL control prefix count", zh=zh)

    def test_route_derivation_uses_snapshot_and_stable_id(self):
        def write_manifest(fragments):
            manifest_dir = self.make_manifest_dir("manifest-suppress")
            header, _ = fixture_manifest(self.phase0["semantic_fingerprint"])
            (manifest_dir / "monspell.json").write_text(
                json.dumps(header, ensure_ascii=False), encoding="utf-8")
            for name, fragment in fragments.items():
                (manifest_dir / name).write_text(
                    json.dumps(fragment, ensure_ascii=False), encoding="utf-8")
            return manifest_dir / "monspell.json", commit_manifest_dir(manifest_dir)

        # Remove both suppress signals: the key must no longer be SUPPRESSED
        # and the build must fail closed on the frozen suppressed set.
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        epsilon = next(
            entry for entry in fragments["monspell/000-a.json"]["entries"]
            if entry["canonical_key"] == "epsilon chant cast"
        )
        epsilon["variants"][0]["english_snapshot"] = "@The_monster@ chants."
        epsilon["variants"][0]["stable_id"] = "mon.cast.epsilon_chant.v1"
        manifest_path, baseline = write_manifest(fragments)
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "suppressed key set mismatch"):
            self.build(manifest_path=manifest_path, baseline_ref=baseline)

        # The stable_id .suppress.v1 marker alone is sufficient even when the
        # english_snapshot is not __NONE.
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        epsilon = next(
            entry for entry in fragments["monspell/000-a.json"]["entries"]
            if entry["canonical_key"] == "epsilon chant cast"
        )
        epsilon["variants"][0]["english_snapshot"] = "@The_monster@ chants."
        manifest_path, baseline = write_manifest(fragments)
        with self.patched(), mock.patch.object(
            MODULE.shared, "_derive_scoped_dump",
            side_effect=[self.derived(self.en_dump), self.derived(self.zh_dump)],
        ):
            inventory = MODULE.build_inventory(
                baseline,
                self.write("en.json", self.en_dump),
                self.write("zh.json", self.zh_dump),
                self.write("phase0.json", self.phase0),
                manifest_path,
                self.write("report.json", self.report),
                self.write("anchor.json", self.anchor),
                self.glossary,
            )
        epsilon_entry = next(
            entry for entry in inventory["entries"]
            if entry["key"] == "epsilon chant cast"
        )
        self.assertEqual("SUPPRESSED", epsilon_entry["route"])

    def test_structured_template_extraction_fail_closed(self):
        manifest_dir = self.make_manifest_dir("manifest-parity")
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        (manifest_dir / "monspell.json").write_text(
            json.dumps(header, ensure_ascii=False), encoding="utf-8")
        for name, fragment in fragments.items():
            (manifest_dir / name).write_text(
                json.dumps(fragment, ensure_ascii=False), encoding="utf-8")

        # en/zh relation parity violation
        bad = copy.deepcopy(fragments)
        entry = next(e for e in bad["monspell/000-a.json"]["entries"]
                     if e["canonical_key"] == "beta beam cast")
        templates = entry["variants"][0]["line_metadata"][0]["templates"]
        templates[:] = [t for t in templates if t["language"] != "zh"]
        for name, fragment in bad.items():
            (manifest_dir / name).write_text(
                json.dumps(fragment, ensure_ascii=False), encoding="utf-8")
        parity_baseline = commit_manifest_dir(manifest_dir)
        with self.assertRaisesRegex(MODULE.InventoryError, "relation parity"):
            self.build(manifest_path=manifest_dir / "monspell.json",
                       baseline_ref=parity_baseline)

        # CASE_MAP variant without cases
        bad = copy.deepcopy(fragments)
        entry = next(e for e in bad["monspell/000-a.json"]["entries"]
                     if e["canonical_key"] == "delta orb cast")
        entry["variants"][0]["materialization_cases"] = []
        for name, fragment in bad.items():
            (manifest_dir / name).write_text(
                json.dumps(fragment, ensure_ascii=False), encoding="utf-8")
        parity_baseline = commit_manifest_dir(manifest_dir)
        with self.assertRaisesRegex(MODULE.InventoryError, "no materialization_cases"):
            self.build(manifest_path=manifest_dir / "monspell.json",
                       baseline_ref=parity_baseline)

    # ------------------------------------------------------------- ledger

    def test_valid_ledger_passes_with_route_counts(self):
        records = self.ledger()
        loaded = self.validate(records)
        self.assertEqual(12, len(loaded["cards"]))
        self.assertEqual(12, loaded["metadata"]["identity_count"])
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        for card in loaded["cards"]:
            entry = by_key[card["key"]]
            self.assertEqual(entry["route"], card["route"])
            if card["route"] == "STRUCTURED":
                self.assertGreater(len(card["structured_template_reviews"]), 0)
                self.assertTrue(all(
                    review["fallback"] for review in card["legacy_variant_reviews"]
                ))
            elif card["route"] == "SUPPRESSED":
                self.assertEqual([], card["structured_template_reviews"])
            else:
                self.assertEqual([], card["structured_template_reviews"])
                self.assertTrue(all(
                    not review["fallback"] for review in card["legacy_variant_reviews"]
                ))

    def test_ledger_coverage_duplicate_extra_missing_order_fail(self):
        records = self.ledger()
        def swap_first_two(rows):
            rows[1], rows[2] = rows[2], rows[1]

        for mutate, message in (
            (lambda rows: rows.pop(), "metadata/card coverage mismatch"),
            (lambda rows: rows.append(copy.deepcopy(rows[-1])),
             "metadata/card coverage mismatch"),
            (swap_first_two, "identity order mismatch"),
        ):
            rows = copy.deepcopy(records)
            mutate(rows)
            with self.subTest(mutation=message):
                with self.assertRaisesRegex(MODULE.InventoryError, message):
                    self.validate(rows)

        for mutate, message in (
            (lambda card: card["structured_template_reviews"].pop(),
             "coverage mismatch"),
            (lambda card: card["legacy_variant_reviews"].pop(),
             "coverage mismatch"),
        ):
            rows = copy.deepcopy(records)
            mutate(rows[1])
            with self.subTest(mutation=message):
                with self.assertRaisesRegex(MODULE.InventoryError, message):
                    self.validate(rows)

    def test_metadata_bindings_fail_closed(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        rows[0]["identity_count"] = 10
        with self.assertRaisesRegex(MODULE.InventoryError, "identity_count"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[0]["inventory_sha256"] = "0" * 64
        with self.assertRaisesRegex(MODULE.InventoryError, "inventory_sha256"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[0]["baseline"] = "0" * 40
        with self.assertRaisesRegex(MODULE.InventoryError, "baseline"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[0]["glossary_sha256"] = "0" * 64
        with self.assertRaisesRegex(MODULE.InventoryError, "glossary_sha256"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[0]["unknown"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "unknown"):
            self.validate(rows)

    def test_card_unknown_fields_and_nonterminal_fail(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        rows[1]["unknown"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "unknown"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["production_facts"]["unknown"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "unknown"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["structured_template_reviews"][0]["unknown"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "unknown"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["legacy_variant_reviews"][0]["unknown"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "unknown"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["terminal_conclusion"] = "pending"
        with self.assertRaisesRegex(MODULE.InventoryError, "nonterminal"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["structured_template_reviews"][0][
            "terminal_conclusion"
        ] = "pending"
        with self.assertRaisesRegex(MODULE.InventoryError, "nonterminal"):
            self.validate(rows)

    def test_boolean_integer_fields_fail_closed(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        rows[0]["identity_count"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "identity_count"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["legacy_variant_reviews"][0]["variant_ordinal"] = False
        with self.assertRaisesRegex(MODULE.InventoryError, "variant_ordinal"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["legacy_variant_reviews"][0]["weight"] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "weight"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        rows[1]["production_facts"]["weights"][0] = True
        with self.assertRaisesRegex(MODULE.InventoryError, "production_facts"):
            self.validate(rows)

    def test_frozen_behavior_evidence_fail_closed(self):
        records = self.ledger()
        mutations = []
        rows = copy.deepcopy(records)
        rows[1]["actual_behavior"] += " drift"
        mutations.append(rows)
        rows = copy.deepcopy(records)
        rows[1]["consumer"]["route_decision"] = "wrong:1"
        mutations.append(rows)
        rows = copy.deepcopy(records)
        rows[1]["evidence_locations"].pop()
        mutations.append(rows)
        rows = copy.deepcopy(records)
        rows[1]["glossary_authority"] = "docs/glossary.md@" + "0" * 64
        mutations.append(rows)
        rows = copy.deepcopy(records)
        rows[1]["current_chinese"][0] += "漂移"
        mutations.append(rows)
        rows = copy.deepcopy(records)
        rows[1]["current_structured_zh"][0]["pattern_zh"] += "漂移"
        mutations.append(rows)
        rows = copy.deepcopy(records)
        rows[1]["production_facts"]["control_prefixes"][0] = "VISUAL"
        mutations.append(rows)
        rows = copy.deepcopy(records)
        rows[1]["route"] = "LEGACY"
        mutations.append(rows)
        for index, rows in enumerate(mutations):
            with self.subTest(drift=index):
                with self.assertRaises(MODULE.InventoryError):
                    self.validate(rows)

    def test_suppressed_route_requires_keep_with_fallback_only(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        epsilon = next(card for card in rows[1:]
                       if card["key"] == "epsilon chant cast")
        epsilon["structured_template_reviews"] = [{
            "locator": {"key": "epsilon chant cast", "variant_ordinal": 0,
                        "case_id": "root", "relation": "NONE"},
            "pattern_en": "x", "current_pattern_zh": "y",
            "proposed_pattern_zh": "y", "relation": "NONE",
            "sensory": "PLAIN", "materialization_policy": "NONE",
            "terminal_conclusion": "keep", "rationale": "drift",
        }]
        epsilon["proposed_structured_zh"] = [{"locator": {}, "pattern_en": "x",
                                              "pattern_zh": "y", "relation": "NONE",
                                              "materialization_policy": "NONE"}]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "proposed_structured_zh coverage"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        epsilon = next(card for card in rows[1:]
                       if card["key"] == "epsilon chant cast")
        epsilon["terminal_conclusion"] = "adjust"
        with self.assertRaisesRegex(MODULE.InventoryError, "must keep"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        epsilon = next(card for card in rows[1:]
                       if card["key"] == "epsilon chant cast")
        epsilon["legacy_variant_reviews"][0]["terminal_conclusion"] = "adjust"
        epsilon["legacy_variant_reviews"][0]["proposed_translation"] = "漂移"
        epsilon["proposed_translation"] = ["漂移"]
        with self.assertRaisesRegex(MODULE.InventoryError, "legacy reviews must keep"):
            self.validate(rows)

    def test_structured_aggregation_and_legacy_fallback_rules(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        alpha = next(card for card in rows[1:] if card["key"] == "alpha strike cast")
        # keep conflicts with a structured adjust
        alpha["structured_template_reviews"][0]["terminal_conclusion"] = "adjust"
        alpha["structured_template_reviews"][0]["proposed_pattern_zh"] = "新译。"
        alpha["proposed_structured_zh"][0]["pattern_zh"] = "新译。"
        with self.assertRaisesRegex(MODULE.InventoryError, "aggregation"):
            self.validate(rows)

        # adjust aggregate passes
        alpha["terminal_conclusion"] = "adjust"
        self.validate(rows)

        # legacy retranslate is forbidden on the fallback path
        rows = copy.deepcopy(records)
        alpha = next(card for card in rows[1:] if card["key"] == "alpha strike cast")
        alpha["legacy_variant_reviews"][0]["terminal_conclusion"] = "retranslate"
        alpha["legacy_variant_reviews"][0]["proposed_translation"] = "新译。"
        alpha["proposed_translation"][0] = "新译。"
        with self.assertRaisesRegex(MODULE.InventoryError, "only keep or adjust"):
            self.validate(rows)

        # structured retranslate with legacy adjust requires the sync marker
        rows = copy.deepcopy(records)
        alpha = next(card for card in rows[1:] if card["key"] == "alpha strike cast")
        for review in alpha["structured_template_reviews"]:
            review["terminal_conclusion"] = "retranslate"
            review["proposed_pattern_zh"] = "重译。"
        for item in alpha["proposed_structured_zh"]:
            item["pattern_zh"] = "重译。"
        alpha["terminal_conclusion"] = "retranslate"
        alpha["legacy_variant_reviews"][0]["terminal_conclusion"] = "adjust"
        alpha["legacy_variant_reviews"][0]["proposed_translation"] = "旧译同步。"
        alpha["proposed_translation"][0] = "旧译同步。"
        with self.assertRaisesRegex(MODULE.InventoryError, "sync marker"):
            self.validate(rows)
        alpha["legacy_variant_reviews"][0]["rationale"] = (
            "与 structured 模板同步。"
        )
        self.validate(rows)

        # identity keep requires unchanged production proposal
        rows = copy.deepcopy(records)
        alpha = next(card for card in rows[1:] if card["key"] == "alpha strike cast")
        alpha["proposed_structured_zh"][0]["pattern_zh"] += "漂移"
        alpha["structured_template_reviews"][0]["proposed_pattern_zh"] += "漂移"
        with self.assertRaisesRegex(MODULE.InventoryError, "aggregation|keep must"):
            self.validate(rows)

    def test_legacy_route_aggregation_and_structured_forbidden(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        zeta = next(card for card in rows[1:] if card["key"] == "zeta summon cast")
        zeta["structured_template_reviews"] = [{"locator": {}, "pattern_en": "x",
                                                "current_pattern_zh": "y",
                                                "proposed_pattern_zh": "y",
                                                "relation": "NONE",
                                                "sensory": "PLAIN",
                                                "materialization_policy": "NONE",
                                                "terminal_conclusion": "keep",
                                                "rationale": "drift"}]
        zeta["proposed_structured_zh"] = [{"locator": {}, "pattern_en": "x",
                                           "pattern_zh": "y", "relation": "NONE",
                                           "materialization_policy": "NONE"}]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "proposed_structured_zh coverage"):
            self.validate(rows)

        # retranslate is allowed on the production legacy path
        rows = copy.deepcopy(records)
        zeta = next(card for card in rows[1:] if card["key"] == "zeta summon cast")
        zeta["terminal_conclusion"] = "retranslate"
        zeta["legacy_variant_reviews"][0]["terminal_conclusion"] = "retranslate"
        zeta["legacy_variant_reviews"][0]["proposed_translation"] = "重译。"
        zeta["proposed_translation"][0] = "重译。"
        self.validate(rows)

        # keep conflicts with a legacy adjust
        rows = copy.deepcopy(records)
        zeta = next(card for card in rows[1:] if card["key"] == "zeta summon cast")
        zeta["legacy_variant_reviews"][0]["terminal_conclusion"] = "adjust"
        zeta["legacy_variant_reviews"][0]["proposed_translation"] = "调整。"
        zeta["proposed_translation"][0] = "调整。"
        with self.assertRaisesRegex(MODULE.InventoryError, "aggregation"):
            self.validate(rows)

        # CLOSURE_ONLY identity is LEGACY: no structured reviews expected
        rows = copy.deepcopy(records)
        eta = next(card for card in rows[1:] if card["key"] == "eta word cast")
        self.assertEqual([], eta["structured_template_reviews"])
        self.assertEqual([], eta["current_structured_zh"])
        self.validate(rows)

    def test_case_map_reviews_carry_case_id_and_cover_cases(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        delta = next(card for card in rows[1:] if card["key"] == "delta orb cast")
        self.assertEqual("CASE_MAP", delta["primary_materialization_policy"])
        self.assertTrue(all(
            review["locator"]["case_id"] != "root"
            for review in delta["structured_template_reviews"]
            if review["materialization_policy"] == "CASE_MAP"
        ))
        rows = copy.deepcopy(records)
        delta = next(card for card in rows[1:] if card["key"] == "delta orb cast")
        review = next(
            review for review in delta["structured_template_reviews"]
            if review["materialization_policy"] == "CASE_MAP"
        )
        review["materialization_policy"] = "NONE"
        with self.assertRaisesRegex(MODULE.InventoryError, "materialization_policy"):
            self.validate(rows)

    def test_unreachable_identities_require_static_review_rationale(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        eta = next(card for card in rows[1:] if card["key"] == "eta word cast")
        eta["reviewer_rationale"] = "已核对。"
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "static-review rationale"):
            self.validate(rows)
        rows = copy.deepcopy(records)
        eta = next(card for card in rows[1:] if card["key"] == "eta word cast")
        self.assertFalse(eta["runtime_evidence"])
        self.assertTrue(MODULE.UNREACHABLE_RATIONALE_MARKER
                        in eta["reviewer_rationale"])
        self.validate(rows)

    def test_unpaired_en_variant_must_keep_none(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        lam = next(card for card in rows[1:] if card["key"] == "lambda shield cast")
        unpaired = lam["legacy_variant_reviews"][1]
        self.assertIsNone(unpaired["current_chinese"])
        self.assertIsNone(unpaired["proposed_translation"])
        unpaired["terminal_conclusion"] = "adjust"
        unpaired["proposed_translation"] = "新译。"
        lam["proposed_translation"][1] = "新译。"
        with self.assertRaisesRegex(MODULE.InventoryError, "unpaired EN variant"):
            self.validate(rows)

    def test_deferral_fields_are_required_and_forbidden(self):
        records = self.ledger()
        rows = copy.deepcopy(records)
        theta = next(card for card in rows[1:] if card["key"] == "theta flee cast")
        theta["terminal_conclusion"] = "defer terminology"
        theta.update({"deferral_owner": "owner", "deferral_reason": "reason",
                      "reentry_trigger": "trigger"})
        review = theta["structured_template_reviews"][0]
        review["terminal_conclusion"] = "defer terminology"
        review.update({"deferral_owner": "owner", "deferral_reason": "reason",
                       "reentry_trigger": "trigger"})
        self.validate(rows)
        del review["deferral_owner"]
        with self.assertRaisesRegex(MODULE.InventoryError, "deferral_owner"):
            self.validate(rows)

        rows = copy.deepcopy(records)
        theta = next(card for card in rows[1:] if card["key"] == "theta flee cast")
        theta["deferral_owner"] = "unexpected"
        with self.assertRaisesRegex(MODULE.InventoryError, "forbids"):
            self.validate(rows)

    def test_mixed_policy_entry_production_facts(self):
        records = self.ledger()
        delta = next(card for card in records[1:]
                     if card["key"] == "delta orb cast")
        self.assertEqual(["CASE_MAP", "NONE"],
                         delta["production_facts"]["materialization_policies"])
        self.assertEqual(["NONE"], delta["production_facts"]["structured_relations"])
        rows = copy.deepcopy(records)
        delta = next(card for card in rows[1:] if card["key"] == "delta orb cast")
        delta["production_facts"]["materialization_policies"] = ["NONE", "NONE"]
        with self.assertRaisesRegex(MODULE.InventoryError, "production_facts"):
            self.validate(rows)

    # ------------------------------------------------------------- candidate

    def candidate_dumps(self, alpha_zh: str | None = None) -> tuple[dict, dict]:
        zh = copy.deepcopy(self.zh_dump)
        if alpha_zh is not None:
            entry = next(e for e in zh["entries"]
                         if e["canonical_key"] == "alpha strike cast")
            entry["raw_body"] = alpha_zh + "\n\n" + entry["raw_body"].split(
                "\n\n", 1)[1]
            entry["variants"][0]["raw_pattern"] = alpha_zh
        return copy.deepcopy(self.en_dump), zh

    def candidate_manifest(self, alpha_zh: str = "新译。") -> dict:
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        header["catalog_order"] = list(KEYS)
        aggregate = {key: value for key, value in header.items()
                     if key not in {"fragment_glob", "catalog_order"}}
        aggregate["entries"] = []
        for fragment in fragments.values():
            aggregate["entries"].extend(fragment["entries"])
        manifest = MODULE._normalise_manifest(aggregate, header["catalog_order"])
        if alpha_zh is not None:
            alpha = next(e for e in manifest["entries"]
                         if e["canonical_key"] == "alpha strike cast")
            template = alpha["variants"][0]["line_metadata"][0]["templates"]
            for item in template:
                if item["language"] == "zh":
                    item["pattern"] = alpha_zh
        return manifest

    def add_candidate(self, en, zh, candidate_manifest=None,
                      candidate_ref=CANDIDATE):
        en_path = self.write("candidate-en.json", en)
        zh_path = self.write("candidate-zh.json", zh)
        with self.patched(), \
                mock.patch.object(MODULE.shared, "_require_candidate_commit"), \
                mock.patch.object(
                    MODULE.shared, "_derive_scoped_dump",
                    side_effect=[self.derived(en), self.derived(zh)],
                ), \
                mock.patch.object(
                    MODULE, "_manifest_snapshot_at_oid",
                    return_value=candidate_manifest or self.candidate_manifest(),
                ):
            return MODULE.add_candidate(
                self.inventory, candidate_ref, en_path, zh_path, self.manifest_path
            )

    def test_candidate_binding_matches_proposals(self):
        candidate_en, candidate_zh = self.candidate_dumps(
            "@The_monster@阿尔法新译。"
        )
        candidate_entries = self.add_candidate(candidate_en, candidate_zh)

        records = self.ledger()
        rows = copy.deepcopy(records)
        alpha = next(card for card in rows[1:] if card["key"] == "alpha strike cast")
        alpha["terminal_conclusion"] = "adjust"
        review = alpha["structured_template_reviews"][0]
        review["terminal_conclusion"] = "adjust"
        review["proposed_pattern_zh"] = "新译。"
        alpha["proposed_structured_zh"][0]["pattern_zh"] = "新译。"
        alpha["legacy_variant_reviews"][0]["terminal_conclusion"] = "adjust"
        alpha["legacy_variant_reviews"][0]["proposed_translation"] = (
            "@The_monster@阿尔法新译。"
        )
        alpha["proposed_translation"][0] = "@The_monster@阿尔法新译。"
        self.validate(rows, candidate_entries)

        # a legacy proposal that does not match the candidate dump fails
        rows = copy.deepcopy(records)
        alpha = next(card for card in rows[1:] if card["key"] == "alpha strike cast")
        alpha["terminal_conclusion"] = "adjust"
        review = alpha["structured_template_reviews"][0]
        review["terminal_conclusion"] = "adjust"
        review["proposed_pattern_zh"] = "新译。"
        alpha["proposed_structured_zh"][0]["pattern_zh"] = "新译。"
        alpha["legacy_variant_reviews"][0]["terminal_conclusion"] = "adjust"
        alpha["legacy_variant_reviews"][0]["proposed_translation"] = "候选不一致。"
        alpha["proposed_translation"][0] = "候选不一致。"
        with self.assertRaisesRegex(MODULE.InventoryError, "candidate ZH dump"):
            self.validate(rows, candidate_entries)

        # a structured proposal that does not match the candidate manifest fails
        rows = copy.deepcopy(records)
        alpha = next(card for card in rows[1:] if card["key"] == "alpha strike cast")
        alpha["terminal_conclusion"] = "adjust"
        review = alpha["structured_template_reviews"][0]
        review["terminal_conclusion"] = "adjust"
        review["proposed_pattern_zh"] = "结构化不一致。"
        alpha["proposed_structured_zh"][0]["pattern_zh"] = "结构化不一致。"
        alpha["legacy_variant_reviews"][0]["terminal_conclusion"] = "adjust"
        alpha["legacy_variant_reviews"][0]["proposed_translation"] = (
            "@The_monster@阿尔法新译。"
        )
        alpha["proposed_translation"][0] = "@The_monster@阿尔法新译。"
        with self.assertRaisesRegex(MODULE.InventoryError, "candidate manifest"):
            self.validate(rows, candidate_entries)

    def test_candidate_english_drift_is_rejected(self):
        candidate_en = copy.deepcopy(self.en_dump)
        candidate_en["entries"][0]["variants"][0]["raw_pattern"] += " changed"
        with self.assertRaisesRegex(MODULE.InventoryError, "English drift"):
            self.add_candidate(candidate_en, copy.deepcopy(self.zh_dump))

    def test_candidate_manifest_drift_is_rejected(self):
        manifest = self.candidate_manifest()
        manifest["entries"] = [
            entry for entry in manifest["entries"]
            if entry["canonical_key"] != "alpha strike cast"
        ]
        with self.assertRaisesRegex(MODULE.InventoryError, "key set mismatch"):
            self.add_candidate(copy.deepcopy(self.en_dump),
                               copy.deepcopy(self.zh_dump),
                               candidate_manifest=manifest)

        manifest = self.candidate_manifest()
        entry = next(e for e in manifest["entries"]
                     if e["canonical_key"] == "beta beam cast")
        entry["variants"][0]["line_metadata"][0]["templates"].extend([
            {"language": "en", "relation": "NONE",
             "pattern": "${actor} emits ${beam}."},
            {"language": "zh", "relation": "NONE",
             "pattern": "${actor}额外模板。"},
        ])
        with self.assertRaisesRegex(MODULE.InventoryError, "locator drift"):
            self.add_candidate(copy.deepcopy(self.en_dump),
                               copy.deepcopy(self.zh_dump),
                               candidate_manifest=manifest)

    def test_manifest_snapshot_at_oid_reads_exact_git_blobs(self):
        header, fragments = fixture_manifest(self.phase0["semantic_fingerprint"])
        header_bytes = json.dumps(header, ensure_ascii=False).encode("utf-8")
        fragment_bytes = {
            Path(name).name: json.dumps(fragment, ensure_ascii=False).encode("utf-8")
            for name, fragment in fragments.items()
        }
        tree = b"".join(
            b"100644 blob " + b"1" * 40 + b"\t" + Path(name).name.encode("utf-8") + b"\0"
            for name in sorted(fragment_bytes)
        )

        def blob(oid, git_path, label):
            if git_path.endswith("monspell.json"):
                return header_bytes
            return fragment_bytes[Path(git_path).name]

        with mock.patch.object(MODULE.shared, "_git_blob_at_oid",
                               side_effect=blob), \
                mock.patch.object(MODULE.shared, "_git_output",
                                  return_value=tree):
            loaded = MODULE._manifest_snapshot_at_oid(
                CANDIDATE,
                ROOT / ".claude/data/message-overlay/monspell.json",
                "fixture",
            )
        self.assertEqual(12, len(loaded["entries"]))
        self.assertEqual("monspell", loaded["domain"])

        with mock.patch.object(MODULE.shared, "_git_blob_at_oid",
                               side_effect=blob), \
                mock.patch.object(MODULE.shared, "_git_output",
                                  return_value=tree):
            with self.assertRaisesRegex(MODULE.InventoryError, "escapes"):
                MODULE._manifest_snapshot_at_oid(
                    CANDIDATE, self.root.parent / "outside.json", "fixture"
                )
        with mock.patch.object(MODULE.shared, "_git_blob_at_oid",
                               side_effect=blob), \
                mock.patch.object(MODULE.shared, "_git_output",
                                  return_value=tree):
            bad_header = copy.deepcopy(header)
            bad_header["fragment_glob"] = "../monspell/*.json"
            with mock.patch.object(
                MODULE.shared, "_git_blob_at_oid",
                side_effect=lambda _oid, _path, _label: json.dumps(
                    bad_header, ensure_ascii=False).encode("utf-8"),
            ):
                with self.assertRaisesRegex(MODULE.InventoryError, "repository-relative"):
                    MODULE._manifest_snapshot_at_oid(
                        CANDIDATE,
                        ROOT / ".claude/data/message-overlay/monspell.json",
                        "fixture",
                    )

        # Explicit fragments list: unsafe relative paths must be rejected.
        bad_header = copy.deepcopy(header)
        del bad_header["fragment_glob"]
        bad_header["fragments"] = ["../evil.json"]
        with mock.patch.object(
            MODULE.shared, "_git_blob_at_oid",
            side_effect=lambda _oid, _path, _label: json.dumps(
                bad_header, ensure_ascii=False).encode("utf-8"),
        ), mock.patch.object(MODULE.shared, "_git_output", return_value=tree):
            with self.assertRaisesRegex(MODULE.InventoryError, "unsafe fragment path"):
                MODULE._manifest_snapshot_at_oid(
                    CANDIDATE,
                    ROOT / ".claude/data/message-overlay/monspell.json",
                    "fixture",
                )

    def test_candidate_commit_gate_fails_closed(self):
        ancestor = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        clean = subprocess.CompletedProcess([], 0, stdout="", stderr="")
        exact = subprocess.CompletedProcess([], 0, stdout="f" * 40 + "\n",
                                            stderr="")
        with mock.patch.object(MODULE.shared, "_validate_oid"), \
                mock.patch.object(
                    MODULE.shared.subprocess, "run",
                    side_effect=[ancestor, exact, clean],
                ):
            MODULE.shared._require_candidate_commit(
                BASELINE, "f" * 40, exact_clean_checkout=True
            )
        dirty = subprocess.CompletedProcess([], 0, stdout=" M candidate\n",
                                            stderr="")
        with mock.patch.object(MODULE.shared, "_validate_oid"), \
                mock.patch.object(
                    MODULE.shared.subprocess, "run",
                    side_effect=[ancestor, exact, dirty],
                ):
            with self.assertRaisesRegex(MODULE.InventoryError, "clean"):
                MODULE.shared._require_candidate_commit(
                    BASELINE, "f" * 40, exact_clean_checkout=True
                )
        wrong = subprocess.CompletedProcess([], 0, stdout="e" * 40 + "\n",
                                            stderr="")
        with mock.patch.object(MODULE.shared, "_validate_oid"), \
                mock.patch.object(
                    MODULE.shared.subprocess, "run",
                    side_effect=[ancestor, wrong],
                ):
            with self.assertRaisesRegex(MODULE.InventoryError, "exact"):
                MODULE.shared._require_candidate_commit(
                    BASELINE, "f" * 40, exact_clean_checkout=True
                )
        with mock.patch.object(MODULE.shared, "_validate_oid"):
            with self.assertRaisesRegex(MODULE.InventoryError, "must differ"):
                MODULE.shared._require_candidate_commit(
                    "f" * 40, "f" * 40
                )

    # ------------------------------------------------------------- CLI

    def test_cli_exclusive_tmp_output(self):
        en_path = self.write("cli-en.json", self.en_dump)
        zh_path = self.write("cli-zh.json", self.zh_dump)
        phase0_path = self.write("cli-phase0.json", self.phase0)
        report_path = self.write("cli-report.json", self.report)
        anchor_path = self.write("cli-anchor.json", self.anchor)
        output = Path("/tmp") / f"monspell-test-{id(self)}.json"
        arguments = [
            "--baseline-ref", self.fixture_baseline,
            "--english-dump", str(en_path), "--localized-dump", str(zh_path),
            "--phase0-inventory", str(phase0_path),
            "--manifest", str(self.manifest_path),
            "--behavior-report", str(report_path),
            "--candidate-anchor", str(anchor_path),
            "--glossary", str(self.glossary),
            "--inventory-output", str(output),
        ]
        derive = lambda _oid, directory, _label, source_basename=None: (  # noqa: E731
            self.derived(self.en_dump if directory == "database/" else self.zh_dump)
        )
        with self.patched(), mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            self.assertEqual(0, MODULE.main(arguments))
            with self.assertRaisesRegex(MODULE.InventoryError, "exclusively create"):
                MODULE.main(arguments)
        output.unlink()

        outside = arguments[:-1] + [str(self.root / "out.json")]
        with self.patched(), mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            with self.assertRaisesRegex(MODULE.InventoryError, "/tmp"):
                MODULE.main(outside)

    def test_cli_candidate_and_review_validation(self):
        en_path = self.write("cli-en.json", self.en_dump)
        zh_path = self.write("cli-zh.json", self.zh_dump)
        phase0_path = self.write("cli-phase0.json", self.phase0)
        report_path = self.write("cli-report.json", self.report)
        anchor_path = self.write("cli-anchor.json", self.anchor)
        output = Path("/tmp") / f"monspell-test-{id(self)}-full.json"
        arguments = [
            "--baseline-ref", self.fixture_baseline,
            "--english-dump", str(en_path), "--localized-dump", str(zh_path),
            "--phase0-inventory", str(phase0_path),
            "--manifest", str(self.manifest_path),
            "--behavior-report", str(report_path),
            "--candidate-anchor", str(anchor_path),
            "--glossary", str(self.glossary),
            "--inventory-output", str(output),
            "--review-results", str(self.write_results(self.ledger())),
        ]
        derive = lambda _oid, directory, _label, source_basename=None: (  # noqa: E731
            self.derived(self.en_dump if directory == "database/" else self.zh_dump)
        )
        with self.patched(), mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            self.assertEqual(0, MODULE.main(arguments))
        output.unlink()

        partial_output = Path("/tmp") / f"monspell-test-{id(self)}-partial.json"
        partial = list(arguments[:-2]) + [
            "--inventory-output", str(partial_output),
            "--candidate-ref", CANDIDATE,
            "--candidate-english-dump", str(en_path),
        ]
        derive = lambda _oid, directory, _label, source_basename=None: (  # noqa: E731
            self.derived(self.en_dump if directory == "database/" else self.zh_dump)
        )
        with self.patched(), mock.patch.object(
            MODULE.shared, "_derive_scoped_dump", side_effect=derive,
        ):
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "must be supplied together"):
                MODULE.main(partial)


if __name__ == "__main__":
    unittest.main()
