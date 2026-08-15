#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/monspeak_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("monspeak_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
SCAN_SPEC = importlib.util.spec_from_file_location(
    "scan_i18n", SCRIPT.parent / "scan_i18n.py")
assert SCAN_SPEC and SCAN_SPEC.loader
SCAN = importlib.util.module_from_spec(SCAN_SPEC)
SCAN_SPEC.loader.exec_module(SCAN)
BASELINE = "b3ad4425053c2175284d32441d67218df97035b0"


def _git_plumbing(arguments: list, input_text: str | None = None) -> str:
    """Run a git plumbing command in the repository without touching the
    worktree, index or refs (mirrors the shout fixture helper)."""
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "monspeak test",
        "GIT_AUTHOR_EMAIL": "monspeak-test@example.invalid",
        "GIT_COMMITTER_NAME": "monspeak test",
        "GIT_COMMITTER_EMAIL": "monspeak-test@example.invalid",
    }
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *arguments], input=input_text,
        check=True, capture_output=True, text=True, env=env,
    )
    return completed.stdout.strip()


def fixture_commit_with_replaced_blobs(replacements: dict[str, str]) -> str:
    """Dangling commit whose tree mirrors the baseline
    ``crawl-ref/source`` tree with the given repo-relative paths replaced
    by new blob content.  Created purely through plumbing, so the working
    tree, index and refs are never touched."""
    listing = subprocess.run(
        ["git", "-C", str(ROOT), "ls-tree", "-r", BASELINE, "--",
         "crawl-ref/source"],
        check=True, capture_output=True, text=True,
    ).stdout
    nodes: dict = {}
    for line in listing.splitlines():
        meta, relpath = line.split("\t", 1)
        parts = relpath.split("/")
        node = nodes
        for part in parts[2:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = tuple(meta.split(" "))
    for relpath, content in replacements.items():
        prefix = "crawl-ref/source/"
        if not relpath.startswith(prefix):
            raise AssertionError(
                f"fixture replacement outside source tree: {relpath}")
        parts = relpath[len(prefix):].split("/")
        node = nodes
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = (
            "100644", "blob",
            _git_plumbing(["hash-object", "-w", "--stdin"],
                          input_text=content),
        )

    def build_tree(children: dict) -> str:
        text = "".join(
            f"{mode} {kind} {oid}\t{name}\n"
            for name, (mode, kind, oid) in sorted(children.items())
        )
        return _git_plumbing(["mktree"], input_text=text)

    def build_recursive(children: dict) -> str:
        entries = {}
        for name, value in children.items():
            if isinstance(value, dict):
                entries[name] = ("040000", "tree", build_recursive(value))
            else:
                entries[name] = value
        return build_tree(entries)

    source_tree = build_recursive(nodes)
    root_tree = build_tree({
        "crawl-ref": (
            "040000", "tree",
            build_tree({"source": ("040000", "tree", source_tree)}),
        ),
    })
    return _git_plumbing(
        ["commit-tree", root_tree, "-m",
         "monspeak exact-source negative fixture"]
    )


def exact_artifact(oid: str, directory: str) -> dict:
    """Rebuild the full speak TextDB dump from exact Git inputs with the
    production load order, DBM_REPLACE merge and weighted-variant parse."""
    shared = MODULE.hardened.shared
    if directory == "database/":
        manifest = shared._english_source_manifest(oid, f"fixture {directory}")
    else:
        manifest = shared._localized_source_manifest(oid, f"fixture {directory}")
    sources = []
    for load_index, source_name in enumerate(manifest):
        sources.append({
            "source_name": source_name,
            "load_index": load_index,
            "normalized_utf8": shared._source_snapshot_at_oid(
                oid, source_name, f"fixture {directory} {source_name}"),
        })
    parsed = []
    provenance_by_entry: dict[int, dict] = {}
    histories: dict[str, list[dict]] = {}
    for source in sources:
        definitions = shared.parse_db_keys(source["normalized_utf8"],
                                           source["source_name"])
        for ordinal, definition in enumerate(definitions):
            provenance = {
                "source_name": source["source_name"],
                "load_index": source["load_index"],
                "definition_ordinal": ordinal,
            }
            parsed.append(definition)
            provenance_by_entry[id(definition)] = provenance
            histories.setdefault(
                shared.lowercase_string(definition.raw_key), []
            ).append(provenance)
    effective, _overrides = shared.merge_desc_sequence(parsed)
    entries = []
    for canonical_key in sorted(effective):
        winner = effective[canonical_key]
        provenance = provenance_by_entry[id(winner)]
        variants, parse_error = shared._parse_weighted_entry(
            winner.value, provenance, canonical_key)
        entries.append({
            "canonical_key": canonical_key,
            "effective_provenance": provenance,
            "raw_body": winner.value,
            "source_history": histories[canonical_key],
            "variants": variants,
            "parse_error": parse_error,
            "body_empty": winner.value == "",
        })
    return {
        "schema_version": 1,
        "database_name": "speak",
        "source_directory": directory,
        "sources": sources,
        "entries": sorted(entries, key=lambda entry: entry["canonical_key"]),
    }


def review_variant(variant: dict) -> dict:
    return {"weight": variant["weight"], "text": variant["text"]}


def fixed_genus_source() -> str:
    """The baseline mon-speak.cc with the genus fallback switched to the
    canonical English accessor (the I70 candidate-role identity shape).

    The baseline OID predates the consumer fix, so every candidate fixture
    must explicitly carry the fixed mon-speak.cc: the candidate-role
    identity shape checks reject the baseline's localized mons_type_name
    call, mirroring the real review gate."""
    return (ROOT / "crawl-ref/source/mon-speak.cc").read_text(
        encoding="utf-8").replace(
        "mons_type_name(mons_genus(mons->type), DESC_DBNAME),",
        "mons_type_name_en(mons_genus(mons->type), DESC_DBNAME),")


def aligned_zh_source(zh_text: str, en_text: str) -> str:
    """The ZH monspeak source with every paired identity body replaced by
    the EN body (so per-key variant counts, weights, tokens and parse
    shape equal EN exactly), keeping the two ZH-only keys with their ZH
    bodies.  The EN ``_laughs_`` double definition is preserved because
    the dump identity layer resolves it the same way in both languages."""
    shared = MODULE.hardened.shared

    def bodies(text: str) -> dict[str, str]:
        definitions = shared.parse_db_keys(text, "fixture source")
        return {shared.lowercase_string(d.raw_key): d.value
                for d in definitions}

    zh_bodies = bodies(zh_text)
    en_bodies = bodies(en_text)
    aligned = []
    for definition in shared.parse_db_keys(en_text, "fixture source"):
        aligned.append(definition.raw_key + "\n\n"
                       + en_bodies[shared.lowercase_string(
                           definition.raw_key)])
    for key in sorted(MODULE.ZH_ONLY_KEYS):
        aligned.append("\n" + key + "\n\n" + zh_bodies[key])
    # The production parser never turns content before the first %%%
    # separator into an entry, so the aligned file starts with one.
    return "%%%%\n" + "\n%%%%\n".join(aligned) + "\n%%%%\n"


def aligned_candidate_artifacts(en_zh, zh_zh):
    """Fixture commit whose ZH monspeak is EN-shaped plus the derived EN/ZH
    dumps.  The fixture also carries the fixed mon-speak.cc consumer (the
    canonical English genus accessor)."""
    fixture = fixture_commit_with_replaced_blobs({
        "crawl-ref/source/dat/database/zh/monspeak.txt": aligned_zh_source(
            zh_zh, en_zh),
        "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
    })
    return (fixture, exact_artifact(fixture, "database/"),
            exact_artifact(fixture, "database/zh/"))


class MonspeakInventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        cls.en = exact_artifact(BASELINE, "database/")
        cls.zh = exact_artifact(BASELINE, "database/zh/")
        cls.en_path = cls.root / "en.json"
        cls.zh_path = cls.root / "zh.json"
        cls.en_path.write_text(json.dumps(cls.en, ensure_ascii=False),
                               encoding="utf-8")
        cls.zh_path.write_text(json.dumps(cls.zh, ensure_ascii=False),
                               encoding="utf-8")
        cls.inventory = MODULE.build_inventory(
            BASELINE, cls.en_path, cls.zh_path, ROOT / "docs/glossary.md"
        )

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def cards(self, inventory=None) -> list[dict]:
        inventory = inventory or self.inventory
        cards = []
        for entry in inventory["entries"]:
            facts = MODULE._card_facts(inventory)
            current_en = [review_variant(variant)
                          for variant in entry["english_variants"]]
            current_zh = [review_variant(variant)
                          for variant in entry["chinese_variants"]]
            cards.append({
                "identity": entry["identity"],
                "key": entry["key"],
                "lifecycle": entry["lifecycle"],
                "dependency_group": entry["dependency_group"],
                "display_context": "由 mon-speak.cc / 固定消费点消费的怪物语音。",
                "producer_consumer": MODULE._card_producer_consumer(
                    entry, facts),
                "evidence_locations": MODULE._evidence_locations(entry, facts),
                "current_english_variants": current_en,
                "current_chinese_variants": current_zh,
                "proposed_english_variants": copy.deepcopy(current_en),
                "proposed_chinese_variants": copy.deepcopy(current_zh),
                "terminal_conclusion": "keep",
                "confidence": "high",
                "rationale": "逐变体核对语义、权重、token 与组合语序后保持现状。",
                "rejected_alternatives": ["不改变随机权重或递归身份。"],
                "reentry_trigger": "monspeak source、消费者、加载顺序或术语权威变化时重审。",
                "deferral_owner": None,
                "deferral_reason": None,
            })
        cards.sort(key=lambda card: card["identity"])
        return cards

    def records(self, inventory=None) -> list[dict]:
        cards = self.cards(inventory)
        return [MODULE._expected_metadata(inventory or self.inventory, cards),
                *cards]

    def write_records(self, records: list[dict]) -> Path:
        path = self.root / f"{self.id().split('.')[-1]}.md"
        path.write_text(
            MODULE.STRICT_BEGIN + "\n```jsonl\n"
            + "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True)
                        for record in records)
            + "\n```\n" + MODULE.STRICT_END + "\n",
            encoding="utf-8",
        )
        return path

    def validate(self, records: list[dict]):
        return MODULE.validate_results(self.write_records(records),
                                       self.inventory)

    def add_candidate_mocked(self, inventory, candidate_ref, en, zh):
        en_path = self.root / f"{self.id().split('.')[-1]}-en.json"
        zh_path = self.root / f"{self.id().split('.')[-1]}-zh.json"
        en_path.write_text(json.dumps(en, ensure_ascii=False),
                           encoding="utf-8")
        zh_path.write_text(json.dumps(zh, ensure_ascii=False),
                           encoding="utf-8")
        with mock.patch.object(MODULE.hardened.shared,
                               "_require_candidate_commit",
                               return_value=None):
            return MODULE.add_candidate(
                inventory, BASELINE, candidate_ref, en_path, zh_path)

    def test_exact_git_inventory_freezes_complete_baseline(self):
        self.assertEqual(733, len(self.inventory["entries"]))
        self.assertEqual(
            {"english": 731, "chinese": 733, "total": 733},
            self.inventory["scope"]["expected_identity_counts"],
        )
        self.assertEqual(
            {"english": 3429, "chinese": 3407},
            self.inventory["scope"]["baseline_variant_counts"],
        )
        self.assertEqual(
            {"english": 47, "chinese": 38},
            self.inventory["scope"]["baseline_random_sites"],
        )
        self.assertEqual(
            {"english": 18, "chinese": 5},
            self.inventory["scope"]["baseline_lua_sites"],
        )
        self.assertEqual(
            {"english": 0, "chinese": 191},
            self.inventory["scope"]["baseline_empty_variants"],
        )
        self.assertEqual(14, len(
            self.inventory["scope"]["split_lua_fragments"]))
        self.assertEqual(213, len(
            self.inventory["scope"]["baseline_asymmetry"]))
        self.assertEqual(459, self.inventory["scope"]["root_key_count"])
        self.assertEqual(257, self.inventory["scope"]["fragment_key_count"])
        self.assertEqual({"english": 15, "chinese": 39},
                         self.inventory["scope"]["orphan_key_count"])
        self.assertEqual(["_jory_rare_", "default 'j'"],
                         self.inventory["scope"]["zh_only_keys"])
        self.assertEqual(
            sorted(MODULE.CROSS_DB_OVERRIDE_KEYS),
            self.inventory["scope"]["override_keys"])
        self.assertEqual([], self.inventory["dumps"]["english"]["token_facts"]["unresolved"])
        self.assertEqual([], self.inventory["dumps"]["localized"]["token_facts"]["unresolved"])

    def test_inventory_output_schema_stays_byte_stable(self):
        hashed_keys = {
            "artifact_sha256", "empty_variant_count", "fragment_key_count",
            "identity_count", "lua_site_count", "orphan_key_count",
            "random_site_count", "reachability", "root_key_count",
            "source_name", "source_sha256", "split_lua_fragments",
            "token_facts", "variant_count",
        }
        self.assertEqual(hashed_keys, set(self.inventory["dumps"]["english"]))
        self.assertEqual(hashed_keys, set(self.inventory["dumps"]["localized"]))
        self.assertEqual(
            "aafc34844ef4544580871fdd613317885937d8c016a4b0ef622a26482cb397bc",
            self.inventory["inventory_sha256"],
        )

    def test_zh_only_keys_classification(self):
        zh_only = [entry for entry in self.inventory["entries"]
                   if entry["lifecycle"] == "zh-only"]
        self.assertEqual(["_jory_rare_", "default 'j'"],
                         [entry["key"] for entry in zh_only])
        for entry in zh_only:
            self.assertEqual([], entry["english_variants"])
            self.assertEqual(1, len(entry["chinese_variants"]))
            self.assertIsNone(entry["english_source_line"])
            self.assertGreater(entry["chinese_source_line"], 0)
            self.assertEqual(
                {"loader": MODULE.FROZEN_PRODUCER_CONSUMER["loader"]},
                MODULE._card_producer_consumer(
                    entry, MODULE._card_facts(self.inventory)))

    def test_override_keys_keep_raw_monspeak_bodies(self):
        # The seven shout-family keys are shadowed by zh/shout.txt in the
        # effective localized merge; their review identities must carry the
        # raw zh/monspeak.txt bodies, not the shout winners.
        overridden = [entry for entry in self.inventory["entries"]
                      if entry["key"] in MODULE.CROSS_DB_OVERRIDE_KEYS]
        self.assertEqual(7, len(overridden))
        zh_dump = self.zh
        for entry in overridden:
            dump_entry = next(e for e in zh_dump["entries"]
                              if e["canonical_key"] == entry["key"])
            self.assertFalse(dump_entry["effective_provenance"][
                "source_name"].endswith("monspeak.txt"))
            self.assertNotEqual(
                [v["raw_pattern"] for v in dump_entry["variants"]],
                [v["text"] for v in entry["chinese_variants"]],
            )

    def test_split_lua_and_empty_variant_facts(self):
        fragments = self.inventory["scope"]["split_lua_fragments"]
        self.assertEqual(14, len(fragments))
        for key, ordinal in fragments:
            self.assertIn(key, ("friendly shoals hound", "nekomata",
                                "sprozz", "sprozz triumphant", "xak'krixis"))
        self.assertEqual(191, sum(
            1 for entry in self.inventory["entries"]
            for variant in entry["chinese_variants"]
            if variant["text"] == ""))

    def test_orphan_classification_is_frozen(self):
        self.assertEqual(
            sorted(MODULE.EXPECTED_EN_ORPHANS),
            self.inventory["scope"]["orphan_keys"]["english"])
        self.assertEqual(
            sorted(MODULE.EXPECTED_EN_ORPHANS
                   | MODULE.EXPECTED_ZH_EXTRA_ORPHANS),
            self.inventory["scope"]["orphan_keys"]["chinese"])
        orphan_entries = [entry for entry in self.inventory["entries"]
                          if entry["lifecycle"] == "legacy-orphaned"]
        self.assertEqual(15, len(orphan_entries))
        # The imp-greeting chain is orphaned end to end.
        self.assertIn("_friendly_imp_greeting",
                      [entry["key"] for entry in orphan_entries])

    def test_root_derivation_binds_exact_git_producers(self):
        # Removing a live prefix from the mon-speak.cc literal space must
        # fail the root derivation: "friendly boris timeout" is only a root
        # because "friendly" is a derived prefix.
        mutated = fixed_genus_source().replace(
            'prefixes.emplace_back("friendly");', "")
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/mon-speak.cc": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "static prefix derivation differs"):
            MODULE._load_dataset(fixture, self.en_path, "database/",
                                 "negative EN", "candidate")

    def test_genus_localized_producer_rejected(self):
        # The candidate role requires the canonical English genus accessor;
        # the baseline's localized mons_type_name call must be rejected.
        fixture = fixture_commit_with_replaced_blobs({})
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "must use mons_type_name_en"):
            MODULE._load_dataset(fixture, self.en_path, "database/",
                                 "negative EN", "candidate")

    def test_identity_row_mutations_fail_closed(self):
        mutated = copy.deepcopy(self.zh)
        mutated["entries"] = [
            entry for entry in mutated["entries"]
            if entry["canonical_key"] != "jory"
        ]
        derived = MODULE._derive_scoped_monspeak_dump(
            BASELINE, "database/zh/", "negative ZH")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "scoped history/raw_body"):
            MODULE._require_scoped_derivation(mutated, derived,
                                              "negative ZH")

    def test_asymmetry_facts_are_frozen(self):
        # One ZH variant removed from a frozen asymmetric key must fail the
        # exact 213-entry comparison in the pair layer.
        en_ds = MODULE._load_dataset(BASELINE, self.en_path, "database/",
                                     "fixture EN", "baseline")
        zh_ds = MODULE._load_dataset(BASELINE, self.zh_path, "database/zh/",
                                     "fixture ZH", "baseline")
        mutated = copy.deepcopy(zh_ds)
        for entry in mutated["entries"]:
            if entry["key"] == "crypt donald":
                entry["variants"] = entry["variants"][:-1]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "asymmetric key facts changed"):
            MODULE._pair_entries(en_ds, mutated)

    def test_complete_keep_ledger_passes(self):
        records = self.records()
        self.assertEqual(734, len(records))
        result = self.validate(records)
        self.assertEqual(733, len(result["cards"]))
        self.assertEqual(
            {"keep": 733},
            result["metadata"]["terminal_conclusion_counts"])

    def test_missing_identity_and_current_text_drift_fail_closed(self):
        records = self.records()
        records = records[:1] + records[2:]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "one metadata record and 733 cards"):
            self.validate(records)
        records = self.records()
        records[1]["current_chinese_variants"] = []
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "current ZH mismatch"):
            self.validate(records)

    def test_unreviewed_proposal_and_deferral_metadata_fail_closed(self):
        records = self.records()
        records[1]["proposed_chinese_variants"] = [
            {"weight": 5, "text": "未审核的新译文。"}
        ]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "conclusion/change mismatch"):
            self.validate(records)
        records = self.records()
        records[1]["terminal_conclusion"] = "defer terminology"
        records[1]["deferral_owner"] = None
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "deferred conclusion requires owner"):
            self.validate(records)

    def test_scaffold_generates_empty_ledger_and_refuses_overwrite(self):
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "monspeak-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        try:
            records = MODULE.scaffold_results(scaffold_path,
                                              self.inventory)
            self.assertEqual(734, len(records))
            self.assertTrue(scaffold_path.exists())
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "exclusively create"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
            text = scaffold_path.read_text(encoding="utf-8")
            self.assertIn(MODULE.STRICT_BEGIN, text)
            self.assertIn(MODULE.STRICT_END, text)
            first_card = records[1]
            self.assertEqual("monspeak:", first_card["identity"][:9])
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rejects_symlinked_path_components(self):
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "real-dir"
        real_dir.mkdir()
        link_dir = self.root / "link-dir"
        link_dir.symlink_to(real_dir, target_is_directory=True)
        scaffold_path = link_dir / "monspeak-review-results.md"
        MODULE.RESULTS_PATH = real_dir / "monspeak-review-results.md"
        try:
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "without following a symlink"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertFalse((real_dir / "monspeak-review-results.md")
                             .exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_candidate_aligned_audit_passes(self):
        fixture, en_art, zh_art = aligned_candidate_artifacts(
            (ROOT / "crawl-ref/source/dat/database/monspeak.txt")
            .read_text(encoding="utf-8"),
            (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt")
            .read_text(encoding="utf-8"),
        )
        en_path = self.root / "candidate-en.json"
        zh_path = self.root / "candidate-zh.json"
        en_path.write_text(json.dumps(en_art, ensure_ascii=False),
                           encoding="utf-8")
        zh_path.write_text(json.dumps(zh_art, ensure_ascii=False),
                           encoding="utf-8")
        # The ledger proposals must match the aligned candidate verbatim:
        # every paired key proposes the aligned EN shape for both sides
        # (the candidate ZH identity rows carry the EN bodies, including
        # the seven override keys whose raw monspeak bodies are the review
        # identities) and the ZH-only keys keep their single-sided ZH
        # variants.
        cards = []
        for entry in self.inventory["entries"]:
            card = {
                "identity": entry["identity"],
                "key": entry["key"],
                "lifecycle": entry["lifecycle"],
                "dependency_group": entry["dependency_group"],
                "display_context": "由 mon-speak.cc / 固定消费点消费的怪物语音。",
                "producer_consumer": MODULE._card_producer_consumer(
                    entry, MODULE._card_facts(self.inventory)),
                "evidence_locations": MODULE._evidence_locations(
                    entry, MODULE._card_facts(self.inventory)),
                "current_english_variants": [
                    review_variant(variant)
                    for variant in entry["english_variants"]],
                "current_chinese_variants": [
                    review_variant(variant)
                    for variant in entry["chinese_variants"]],
                "proposed_english_variants": [],
                "proposed_chinese_variants": [],
                "terminal_conclusion": "keep",
                "confidence": "high",
                "rationale": "对齐 EN 结构后保持现状。",
                "rejected_alternatives": ["不改变随机权重或递归身份。"],
                "reentry_trigger": "monspeak source、消费者或术语权威变化时重审。",
                "deferral_owner": None,
                "deferral_reason": None,
            }
            if entry["lifecycle"] == "zh-only":
                card["proposed_chinese_variants"] = [
                    review_variant(variant)
                    for variant in entry["chinese_variants"]]
            else:
                aligned_en = card["current_english_variants"]
                card["proposed_english_variants"] = copy.deepcopy(aligned_en)
                card["proposed_chinese_variants"] = copy.deepcopy(aligned_en)
                if aligned_en != card["current_chinese_variants"]:
                    card["terminal_conclusion"] = "adjust"
            cards.append(card)
        cards.sort(key=lambda card: card["identity"])
        records = [MODULE._expected_metadata(self.inventory, cards), *cards]
        candidate = self.add_candidate_mocked(
            self.inventory, fixture, en_art, zh_art)
        self.assertEqual(733, len(candidate["entries"]))
        result = MODULE.validate_results(
            self.write_records(records), self.inventory, candidate,
            records=records)
        self.assertEqual(733, len(result["cards"]))

    def test_candidate_pair_rejects_weight_or_count_drift(self):
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh)
        # Drop one variant of the aligned Crypt Donald ZH body: the
        # candidate ZH total drops below the approved proposal totals.
        block = "Crypt Donald\n\n"
        start = aligned.index(block)
        end = aligned.index("\n%%%%\n", start)
        body = aligned[start + len(block):end]
        trimmed = body.rstrip()
        last = trimmed.rfind("\n\n")
        assert last > 0
        mutated = (aligned[:start + len(block)] + trimmed[:last]
                   + aligned[end:])
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": mutated,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        en_art = exact_artifact(fixture, "database/")
        zh_art = exact_artifact(fixture, "database/zh/")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "candidate variant count differs"):
            self.add_candidate_mocked(
                self.inventory, fixture, en_art, zh_art)

    def test_candidate_unresolved_token_rejected(self):
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh)
        # Inject a bogus token into one aligned body.
        aligned = aligned.replace(
            "VISUAL:@The_monster@ looks [rattled|scared stiff|petrified].",
            "VISUAL:@The_monster@ looks @bogus_token@.",
            1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "unresolved token"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_candidate_triple_brace_lua_rejected(self):
        # CR-002/CR-006: a candidate ``{{{`` Lua site (stray brace inside
        # the ``{{...}}`` boundary) must be rejected even though the
        # ``{{``/``}}`` substring counts balance and the site count matches
        # EN.  The CR-006 boundary freeze catches it at the site level
        # before the block protocol runs.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh).replace(
            "{{ return you.race() }}", "{{{ return you.race() }}}", 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "stray brace outside"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_lua_sites_strict_rejects_stray_close_brace(self):
        # CR-006: ``{{ ... }}}`` balances the ``{{``/``}}`` substring counts
        # and the regex extraction never sees the third ``}`` outside the
        # boundary; the exact boundary invariant must fail closed.
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "stray brace outside"):
            MODULE._lua_sites_strict("{{ return evil() }}}")

    def test_lua_block_protocol_rejects_arbitrary_return_expression(self):
        # CR-006: ``return evil()`` is not translatable display text; it
        # must stay byte-exact (protocol-bound) and fail closed instead of
        # being normalized to the display marker.
        protocol = MODULE._lua_block_protocol("return evil()")
        self.assertIn("unsupported return expression", protocol["error"])
        self.assertEqual("return evil()", protocol["skeleton"])
        protocol = MODULE._lua_block_protocol(
            'return "legitimate display text"')
        self.assertIsNone(protocol["error"])
        self.assertEqual("return " + MODULE._LUA_RETURN_MARKER,
                         protocol["skeleton"])

    def test_candidate_stray_close_brace_lua_rejected(self):
        # CR-006: the reviewer probe ``{{ return evil() }}}`` (and any
        # candidate with a stray ``}`` outside a ``{{...}}`` site) must be
        # rejected even though the ``{{``/``}}`` counts and the variant
        # total stay unchanged.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh).replace(
            "{{ return you.race() }}", "{{ return you.race() }}}", 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "stray brace outside"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_candidate_arbitrary_return_expression_rejected(self):
        # CR-006: an arbitrary/illegal return expression (``evil()``) must
        # not be masked as translatable display text; the candidate gate
        # fails closed on the malformed block.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh).replace(
            "{{ return you.race() }}", "{{ return evil() }}", 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "malformed Lua sites"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_candidate_lua_gate_requires_luac(self):
        # CR-006: the candidate executable-syntax gate fails closed when
        # luac is unavailable; a missing compiler must never silently pass
        # a candidate that contains Lua blocks.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        fixture, en_art, zh_art = aligned_candidate_artifacts(en_zh, zh_zh)
        original_which = MODULE.shutil.which

        def fake_which(cmd, *args, **kwargs):
            if cmd == "luac":
                return None
            return original_which(cmd, *args, **kwargs)

        with mock.patch.object(MODULE.shutil, "which",
                               side_effect=fake_which):
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "luac not found"):
                self.add_candidate_mocked(self.inventory, fixture,
                                          en_art, zh_art)

    def test_candidate_zh_only_empty_variant_rejected(self):
        # CR-007: the dataset-level candidate invariants cover the ZH-only
        # keys, not only the shared keys of the pair loop: `_jory_rare_`
        # with a ``w:10``-followed-by-empty pattern keeps the frozen 3431
        # variant total but must fail the no-empty-variant invariant.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh).replace(
            "_jory_rare_\n\n@The_monster@ 说：\"我的妻子抛弃了我，"
            "但我已经报了仇。\"",
            "_jory_rare_\n\nw:10", 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "empty variants"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_candidate_zh_only_split_lua_rejected(self):
        # CR-007: `default 'j'` introducing an unbalanced ``{{`` (split-Lua
        # fragment) keeps the frozen variant total but must fail the
        # dataset-level no-split-Lua invariant.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh).replace(
            "default 'j'\n\nVISUAL:@The_monster@ 颤动着。",
            "default 'j'\n\nVISUAL:@The_monster@ 颤动着。 {{", 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "split Lua fragments"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_issue16_joint_visual_swap_rejected(self):
        # CR-008: swapping the `_Sigmund_common_` ordinal 0/1 lines in BOTH
        # EN and ZH keeps the VISUAL total at 496 and satisfies the
        # per-position ZH channel check (both files swap together), but the
        # frozen complete (canonical key, variant ordinal) identity set must
        # reject the EN drift.
        def swap_sigmund_lines(text: str) -> str:
            en_pair = ("w:20\n@The_monster@ laughs darkly.\n\n"
                       "VISUAL:@The_monster@ looks at you with fury.")
            zh_pair = ("w:20\n@The_monster@ 阴沉地笑着。\n\n"
                       "VISUAL:@The_monster@ 愤怒地看着你。")
            pair = zh_pair if text.count(zh_pair) else en_pair
            swapped = "w:20\nVISUAL:@The_monster@ " + ("愤怒地看着你。"
                        if pair == zh_pair else "looks at you with fury.") \
                + "\n\n@The_monster@ " + ("阴沉地笑着。"
                        if pair == zh_pair else "laughs darkly.")
            mutated = text.replace(pair, swapped, 1)
            if mutated == text:
                raise AssertionError("swap target not found")
            return mutated

        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "crawl-ref" / "source"
            en_path = root / "dat" / "database" / "monspeak.txt"
            zh_path = root / "dat" / "database" / "zh" / "monspeak.txt"
            en_path.parent.mkdir(parents=True)
            zh_path.parent.mkdir(parents=True)
            en_path.write_text(
                swap_sigmund_lines(
                    (ROOT / "crawl-ref/source/dat/database/monspeak.txt")
                    .read_text(encoding="utf-8")),
                encoding="utf-8")
            zh_path.write_text(
                swap_sigmund_lines(
                    (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt")
                    .read_text(encoding="utf-8")),
                encoding="utf-8")
            findings = SCAN.protocol_boundary_findings(
                str(root), "issue16-monspeak-channels")
            self.assertTrue(findings)
            self.assertTrue(any(
                contract == "issue16-monspeak-channels"
                and artifact == "dat/database/monspeak.txt"
                and "VISUAL position set drifted" in detail
                for contract, artifact, detail in findings))
            self.assertFalse(any(
                "VISUAL channel prefix lost" in detail
                for _contract, _artifact, detail in findings))

    def test_lua_block_protocol_multi_line_literal_stays_normalized(self):
        # CR-006: a multi-line ``[[ ]]`` display literal normalizes to the
        # marker (its continuation lines are consumed into the expression)
        # while blank lines outside the literal keep the skeleton line
        # structure, so EN/ZH skeletons stay comparable byte-for-byte.
        block = ('return [[a\nb]]\n\n'
                 'if x then\n    return "b"\nend')
        protocol = MODULE._lua_block_protocol(block)
        self.assertIsNone(protocol["error"])
        self.assertEqual(
            ["return " + MODULE._LUA_RETURN_MARKER, "", "if x then",
             "return " + MODULE._LUA_RETURN_MARKER, "end"],
            protocol["skeleton"].split("\n"))
        self.assertEqual(["[[a\nb]]", '"b"'], protocol["return_strings"])

    def test_candidate_translated_comparison_literal_rejected(self):
        # CR-002: the non-translatable Lua comparison literals ("Mummy" is
        # a lookup identity, not display text) must stay byte-identical to
        # EN; translating one fails the protocol gate.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh).replace(
            'you.race() == "Mummy"', 'you.race() == "木乃伊"')
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "comparison literals differ"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_candidate_lua_operator_drift_rejected(self):
        # CR-002: control-flow/operator drift inside a Lua block (``>=``
        # changed to ``>``) must fail the skeleton comparison even though
        # site counts and comparison literals stay identical.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        aligned = aligned_zh_source(zh_zh, en_zh).replace(
            'you.skill("Spellcasting") >= 5',
            'you.skill("Spellcasting") > 5')
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "control skeleton/operators differ"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_candidate_frozen_totals_reject_joint_add_remove(self):
        # CR-003: the candidate totals are frozen (EN 3429 / ZH 3431) and
        # never derived from the editable ledger, so an EN+ZH+ledger joint
        # variant addition (which the old proposal-derived totals accepted)
        # must fail closed against the frozen counts.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        mutated_en = en_zh.replace(
            "@The_monster@ hisses menacingly.",
            "@The_monster@ hisses menacingly.\n\n"
            "@The_monster@ hisses again.", 1)
        aligned = aligned_zh_source(zh_zh, mutated_en)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/monspeak.txt": mutated_en,
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "candidate variant count differs"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_candidate_en_source_snapshot_hard_bound_to_baseline(self):
        # CR-003: an EN edit that keeps every count identical (one glyph
        # line reworded) must fail the source-snapshot/entries binding, so
        # the candidate EN is byte-frozen to the baseline EN.
        en_zh = (ROOT / "crawl-ref/source/dat/database/monspeak.txt") \
            .read_text(encoding="utf-8")
        zh_zh = (ROOT / "crawl-ref/source/dat/database/zh/monspeak.txt") \
            .read_text(encoding="utf-8")
        mutated_en = en_zh.replace(
            "@The_monster@ hisses menacingly.",
            "@The_monster@ hisses softly.", 1)
        aligned = aligned_zh_source(zh_zh, mutated_en)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/monspeak.txt": mutated_en,
            "crawl-ref/source/dat/database/zh/monspeak.txt": aligned,
            "crawl-ref/source/mon-speak.cc": fixed_genus_source(),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "source snapshot must equal"):
            self.add_candidate_mocked(
                self.inventory, fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"))

    def test_frozen_candidate_totals_are_3429_and_3431(self):
        # CR-003 positive: the frozen candidate totals are EN 3429 (baseline
        # EN bytes) and ZH 3431 (3429 shared EN-aligned variants plus the
        # two single-variant ZH-only keys).
        self.assertEqual(3429, MODULE.EXPECTED_CANDIDATE_EN_VARIANT_COUNT)
        self.assertEqual(3431, MODULE.EXPECTED_CANDIDATE_ZH_VARIANT_COUNT)
        zh_only_variants = sum(
            1 for entry in self.inventory["entries"]
            if entry["lifecycle"] == "zh-only"
            for _variant in entry["chinese_variants"])
        self.assertEqual(2, zh_only_variants)
        self.assertEqual(
            3429 + zh_only_variants,
            MODULE.EXPECTED_CANDIDATE_ZH_VARIANT_COUNT)

    def test_review_card_proposed_en_must_equal_baseline_en(self):
        # CR-003: every review card is bound to the baseline EN variants;
        # editing an EN proposal (even with a matching candidate) fails.
        records = self.records()
        records[1]["proposed_english_variants"] = \
            records[1]["proposed_english_variants"][:-1]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "proposed EN must equal"):
            self.validate(records)

    def test_producer_consumer_anchor_value_mutation_rejected(self):
        mutated = fixed_genus_source().replace(
            'msg = getSpeakString(prefix + key);',
            '// shifted anchor\n    msg = getSpeakString(prefix + key);')
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/mon-speak.cc": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "anchors drifted"):
            MODULE._producer_consumer_facts(fixture, "negative anchors")


if __name__ == "__main__":
    unittest.main()
