#!/usr/bin/env python3

from __future__ import annotations

import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/decorlines_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("decorlines_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASELINE = "306d9099ae08a94a64f051d487dfed0a9675e178"
PRE_FIX = "4859eb33f1d2a4dc597273c7e11daa0c310b3602"
FIXED = "a65287716072a3c73874c44b08a276ff6b39b4da"


def _git_plumbing(arguments: list, input_text: str | None = None) -> str:
    """Run a git plumbing command in the repository without touching the
    worktree, index or refs (mirrors the monspell fixture helper)."""
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "decorlines test",
        "GIT_AUTHOR_EMAIL": "decorlines-test@example.invalid",
        "GIT_COMMITTER_NAME": "decorlines test",
        "GIT_COMMITTER_EMAIL": "decorlines-test@example.invalid",
    }
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *arguments], input=input_text,
        check=True, capture_output=True, text=True, env=env,
    )
    return completed.stdout.strip()


def fixture_commit_with_directn(directn_source: str) -> str:
    """Dangling commit whose tree mirrors the FIXED commit's producer
    sources with ``crawl-ref/source/directn.cc`` replaced by
    ``directn_source``.

    Created purely through plumbing (hash-object/mktree/commit-tree), so
    the working tree, index and refs are never touched.  This is the
    exact-source negative fixture for I67-CODE-008: the derivation reads
    the mutated consumer expression from the same kind of exact Git OID
    the candidate audit uses."""

    def listing(git_path: str) -> dict:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", FIXED, "--",
             git_path],
            check=True, capture_output=True, text=True,
        ).stdout
        entries = {}
        for line in out.splitlines():
            meta, name = line.split("\t", 1)
            mode, kind, oid = meta.split(" ")
            entries[Path(name).name] = (mode, kind, oid)
        return entries

    def mktree(entries: dict) -> str:
        text = "".join(
            f"{mode} {kind} {oid}\t{name}\n"
            for name, (mode, kind, oid) in sorted(entries.items())
        )
        return _git_plumbing(["mktree"], input_text=text)

    directn_blob = _git_plumbing(
        ["hash-object", "-w", "--stdin"], input_text=directn_source)
    species_tree = mktree(listing("crawl-ref/source/dat/species"))
    forms_tree = mktree(listing("crawl-ref/source/dat/forms"))
    source_entries = {
        "dat": ("040000", "tree", mktree({
            "species": ("040000", "tree", species_tree),
            "forms": ("040000", "tree", forms_tree),
        })),
        "directn.cc": ("100644", "blob", directn_blob),
    }
    for name in ("religion.cc", "terrain.cc", "feature-data.h",
                 "tag-version.h"):
        source_entries[name] = listing(f"crawl-ref/source/{name}")[name]
    source_tree = mktree(source_entries)
    crawl_ref_tree = mktree({"source": ("040000", "tree", source_tree)})
    root_tree = mktree({"crawl-ref": ("040000", "tree", crawl_ref_tree)})
    return _git_plumbing(
        ["commit-tree", root_tree, "-m",
         "decorlines exact-source negative fixture"]
    )


def exact_artifact(oid: str, directory: str) -> dict:
    """Rebuild the full misc TextDB dump from exact Git inputs with the
    production load order, DBM_REPLACE merge and weighted-variant parse."""
    shared = MODULE.hardened.shared
    if directory == "database/":
        manifest = MODULE._misc_source_manifest(oid, f"fixture {directory}")
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
        "database_name": "misc",
        "source_directory": directory,
        "sources": sources,
        "entries": sorted(entries, key=lambda entry: entry["canonical_key"]),
    }


def review_variant(variant: dict) -> dict:
    return {"weight": variant["weight"], "text": variant["text"]}


def card_for(entry: dict) -> dict:
    current_en = [review_variant(variant)
                  for variant in entry["english_variants"]]
    current_zh = [review_variant(variant)
                  for variant in entry["chinese_variants"]]
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": entry["lifecycle"],
        "dependency_group": entry["dependency_group"],
        "display_context": "由 directn.cc::_walk_on_decor 消费的 decorlines 消息。",
        "producer_consumer": {
            "loader": "crawl-ref/source/database.cc:143",
            "decor_consumer": "crawl-ref/source/directn.cc:3007",
        },
        "evidence_locations": [
            f"crawl-ref/source/dat/database/decorlines.txt:"
            f"{entry['english_source_line']}",
            f"crawl-ref/source/dat/database/zh/decorlines.txt:"
            f"{entry['chinese_source_line']}",
        ],
        "current_english_variants": current_en,
        "current_chinese_variants": current_zh,
        "proposed_english_variants": copy.deepcopy(current_en),
        "proposed_chinese_variants": copy.deepcopy(current_zh),
        "terminal_conclusion": "keep",
        "confidence": "high",
        "rationale": "逐变体核对语义、权重、token 与组合语序后保持现状。",
        "rejected_alternatives": ["不改变随机权重或递归身份。"],
        "reentry_trigger": "decorlines source、消费者、加载顺序或术语权威变化时重审。",
        "deferral_owner": None,
        "deferral_reason": None,
    }


class DecorlinesInventoryTests(unittest.TestCase):
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

    def records(self) -> list[dict]:
        cards = [card_for(entry) for entry in self.inventory["entries"]]
        return [MODULE._expected_metadata(self.inventory, cards), *cards]

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

    def test_exact_git_inventory_freezes_complete_baseline(self):
        self.assertEqual(132, len(self.inventory["entries"]))
        self.assertEqual(117, self.inventory["scope"]["root_key_count"])
        self.assertEqual(209,
                         self.inventory["dumps"]["english"]["variant_count"])
        self.assertEqual(266,
                         self.inventory["dumps"]["localized"]["variant_count"])
        self.assertEqual({"english": 11, "chinese": 11},
                         self.inventory["scope"]["baseline_random_sites"])
        self.assertEqual({"english": 5, "chinese": 5},
                         self.inventory["scope"]["baseline_lua_sites"])
        self.assertEqual(63, len(self.inventory["scope"]["baseline_asymmetry"]))
        self.assertEqual(57, len(
            self.inventory["scope"]["baseline_token_multiset_drift"]))
        self.assertEqual([], self.inventory["dumps"]["english"]["token_facts"]["unresolved"])
        self.assertEqual([], self.inventory["dumps"]["localized"]["token_facts"]["unresolved"])
        self.assertEqual([], self.inventory["dumps"]["english"]["reachability"]["unreachable"])
        self.assertEqual([], self.inventory["dumps"]["localized"]["reachability"]["unreachable"])
        self.assertEqual(
            sorted(MODULE.INTERNAL_FRAGMENT_KEYS),
            sorted({site["token"][1:-1]
                    for site in self.inventory["dumps"]["english"]["token_facts"]["fragment_sites"]}),
        )

    def test_root_keys_derive_from_exact_git_producers(self):
        facts = MODULE._derivable_facts(BASELINE, "fixture", role="baseline")
        self.assertEqual(47, len(facts["species"]))
        self.assertEqual(27, len(facts["gods"]))
        self.assertEqual(35, len(facts["forms"]))
        self.assertEqual(sorted(MODULE.EXPECTED_FOUNTAIN_LOOKUPS),
                         facts["fountains"])
        self.assertEqual(sorted(MODULE.EXPECTED_CACHE_LOOKUPS),
                         facts["caches"])
        self.assertEqual(531, len(facts["keys"]))
        # The derivable root set covers exactly the 117 direct roots.
        roots = set(self.inventory["scope"]["root_keys"])
        self.assertTrue(roots <= facts["keys"])

    def test_inventory_output_schema_stays_byte_stable(self):
        # The frozen review ledger binds inventory_sha256 to the historical
        # output schema; the production-derived classification must not
        # change the hashed inventory shape.
        legacy_keys = {"artifact_sha256", "lua_site_count",
                       "random_site_count", "reachability",
                       "root_key_count", "source_name", "source_sha256",
                       "token_facts", "variant_count"}
        self.assertEqual(legacy_keys, set(self.inventory["dumps"]["english"]))
        self.assertEqual(legacy_keys, set(self.inventory["dumps"]["localized"]))
        # Byte-identical hash to the pre-derivation inventory on the same
        # fixture inputs (verified against the historical module); the
        # production ledger-bound hash is re-checked by the CLI candidate
        # audit against docs/decorlines-review-results.md.
        self.assertEqual(
            "065d8c6064f287c2c4aa7d77755029417d61a27dea814160d49a6c69c705c0fd",
            self.inventory["inventory_sha256"],
        )

    def test_producer_derivation_uses_raw_english_identities(self):
        facts = MODULE._derivable_facts(BASELINE, "fixture", role="baseline")
        self.assertIn("spriggan", facts["species"])
        self.assertIn("felid", facts["species"])
        self.assertIn("kobold", facts["species"])
        self.assertIn("maw", facts["forms"])
        self.assertIn("bat swarm", facts["forms"])
        self.assertIn("zin", facts["gods"])
        self.assertIn("the shining one", facts["gods"])
        # Raw English names only: a localized display name is never a
        # valid lookup prefix producer (I67-CODE-006).
        self.assertNotIn("小精灵", facts["species"])
        self.assertNotIn("小精灵 fruit cache", facts["keys"])
        self.assertIn("spriggan fruit cache", facts["keys"])

    def test_localized_species_producers_fail_closed(self):
        # Regression guard for I67-CODE-006: if the species prefix were
        # localized (species::name() without raw=true returns the ZH display
        # name under lang_t::ZH), the canonical English species cache keys
        # would stop being derivable and the classification must reject the
        # file instead of silently reclassifying them.
        derivable = MODULE._derivable_facts(
            BASELINE, "negative localize", role="baseline")
        mutated = dict(derivable)
        keys = set(derivable["keys"])
        keys -= {f"spriggan {cache}" for cache in derivable["caches"]}
        keys |= {f"小精灵 {cache}" for cache in derivable["caches"]}
        mutated["keys"] = frozenset(keys)
        scoped = {entry["canonical_key"].lower()
                  for entry in self.en["entries"]}
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "neither derivable"):
            MODULE._classify_root_keys(scoped, mutated, "negative")

    def test_misspelled_derived_key_fails_closed(self):
        # A derived key that stops being derivable (misspelled prefix in the
        # file, renamed producer, ...) must fail closed: it is neither a
        # production root nor one of the frozen recursive aliases.
        derivable = MODULE._derivable_facts(
            BASELINE, "negative misspell", role="baseline")
        mutated = dict(derivable)
        keys = set(derivable["keys"])
        keys.discard("spriggan fruit cache")
        mutated["keys"] = frozenset(keys)
        scoped = {entry["canonical_key"].lower()
                  for entry in self.en["entries"]}
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "neither derivable"):
            MODULE._classify_root_keys(scoped, mutated, "negative")

    def test_misspelled_key_in_file_fails_closed(self):
        # End-to-end: a misspelled derived key inside the decorlines source
        # itself must be rejected by the full dataset pipeline.
        mutated = copy.deepcopy(self.en)
        for entry in mutated["entries"]:
            if entry["canonical_key"] == "spriggan fruit cache":
                entry["canonical_key"] = "spriggan fruit cche"
        raw = json.dumps(mutated, ensure_ascii=False).encode("utf-8")
        derivable = MODULE._derivable_facts(
            BASELINE, "negative file", role="baseline")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "neither derivable"):
            MODULE._dataset(mutated, raw, "database/", "negative EN",
                            "candidate", derivable)

    def test_deleted_derived_key_fails_closed(self):
        # Removing one derived key from the file breaks the frozen identity
        # count before classification can even run.
        mutated = copy.deepcopy(self.en)
        mutated["entries"] = [
            entry for entry in mutated["entries"]
            if entry["canonical_key"] != "spriggan fruit cache"
        ]
        raw = json.dumps(mutated, ensure_ascii=False).encode("utf-8")
        derivable = MODULE._derivable_facts(
            BASELINE, "negative delete", role="baseline")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "identity count mismatch"):
            MODULE._dataset(mutated, raw, "database/", "negative EN",
                            "candidate", derivable)

    def _fixed_directn_source(self) -> str:
        return MODULE.hardened.shared._decode_utf8(
            MODULE.hardened.shared._git_blob_at_oid(
                FIXED, "crawl-ref/source/directn.cc", "fixture"),
            "fixture",
        )

    def test_walk_on_decor_shape_rejects_localized_species_call(self):
        # I67-CODE-008 exact-source negative (source variant): mutating the
        # fixed consumer's raw=true to raw=false - or dropping the raw
        # argument entirely - localizes the species prefix under ZH and
        # must be rejected by the same parser the full derivation uses,
        # before any key is derived.
        source = self._fixed_directn_source()
        self.assertIn("species::SPNAME_PLAIN,", source)
        raw_false = re.sub(
            r"species::name\(you\.species,\s*species::SPNAME_PLAIN,"
            r"\s*true\)",
            "species::name(you.species, species::SPNAME_PLAIN, false)",
            source,
        )
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "species cache prefix"):
            MODULE._walk_on_decor_shape(raw_false, "negative raw=false")
        localized = re.sub(
            r"species::name\(you\.species,\s*species::SPNAME_PLAIN,"
            r"\s*true\)",
            "species::name(you.species)",
            source,
        )
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "species cache prefix"):
            MODULE._walk_on_decor_shape(localized, "negative localized")

    def test_pre_fix_commit_localized_species_call_fails_derivation(self):
        # I67-CODE-008: the pre-fix parent commit (4859eb33f1) constructs
        # the species prefix with the localized species::name(you.species)
        # call.  The full exact-source derivation must reject it - the
        # round-7 blocker was that this commit still passed with 117 roots
        # / 15 aliases because the derivation never read the expression.
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "species cache prefix"):
            MODULE._derivable_facts(
                PRE_FIX, "negative pre-fix commit", role="candidate")

    def test_fixture_commit_with_localized_species_call_fails_derivation(self):
        # I67-CODE-008 exact-source negative (fixture commit): build a
        # dangling commit whose tree is the FIXED producer tree with
        # directn.cc's raw=true reverted to the localized call; the full
        # derivation path (exact-Git blob -> shape parser -> key
        # construction) must reject it.  This is not a post-derived set
        # mutation: the fixture is a real Git OID the derivation reads.
        source = self._fixed_directn_source()
        mutated = re.sub(
            r"species::name\(you\.species,\s*species::SPNAME_PLAIN,"
            r"\s*true\)",
            "species::name(you.species)",
            source,
        )
        fixture = fixture_commit_with_directn(mutated)
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "species cache prefix"):
            MODULE._derivable_facts(
                fixture, "negative fixture", role="candidate")

    def test_baseline_role_records_pre_fix_species_shape(self):
        # The frozen data baseline OID predates the consumer fix and
        # carries the abbreviated pre-fix call; the baseline derivation
        # records that shape as evidence and still derives the frozen
        # model's raw English prefixes (the exact prefixes the fix
        # restores for ZH).
        facts = MODULE._derivable_facts(
            BASELINE, "fixture", role="baseline")
        self.assertEqual("pre-fix-abbreviated", facts["species_shape"])
        self.assertIn("spriggan fruit cache", facts["keys"])

    def test_fixed_commit_passes_strict_species_shape(self):
        facts = MODULE._derivable_facts(FIXED, "fixture")
        self.assertEqual("raw-plain-fixed", facts["species_shape"])
        self.assertIn("spriggan fruit cache", facts["keys"])

    def test_worktree_head_passes_strict_species_shape(self):
        # The current production structure resolves the food chain through
        # the decor_cache_lookup() helper shared with the catch2 tests;
        # the strict derivation must accept it and record the fixed shape.
        head = MODULE.hardened.shared._git_output(
            ["rev-parse", "HEAD"], "worktree HEAD"
        ).decode("ascii").strip()
        facts = MODULE._derivable_facts(head, "fixture")
        self.assertEqual("raw-plain-fixed", facts["species_shape"])
        self.assertIn("spriggan fruit cache", facts["keys"])

    def test_complete_keep_ledger_passes(self):
        evidence = self.validate(self.records())
        self.assertEqual(132, len(evidence["cards"]))

    def test_missing_identity_and_current_text_drift_fail_closed(self):
        records = self.records()
        records.pop()
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError, "132 cards"):
            self.validate(records)

        records = self.records()
        records[1]["current_english_variants"][0]["text"] += " drift"
        with self.assertRaisesRegex(MODULE.InventoryError, "current EN mismatch"):
            self.validate(records)

    def test_unreviewed_proposal_and_deferral_metadata_fail_closed(self):
        records = self.records()
        records[1]["proposed_chinese_variants"][0]["text"] += "改"
        with self.assertRaisesRegex(MODULE.InventoryError, "conclusion/change mismatch"):
            self.validate(records)

        records = self.records()
        records[1]["terminal_conclusion"] = "defer terminology"
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError, "requires owner"):
            self.validate(records)

    def test_token_classification_and_reachability(self):
        facts = self.inventory["dumps"]["english"]["token_facts"]
        self.assertIn("@any_graffiti@", {site["token"]
                                         for site in facts["external_sites"]})
        self.assertIn("@any_colour@", {site["token"]
                                       for site in facts["external_sites"]})
        self.assertIn("@your_weapon@", {site["token"]
                                        for site in facts["postprocess_sites"]})
        self.assertIn("@sparkling_message@", {site["token"]
                                              for site in facts["fragment_sites"]})
        roots = set(self.inventory["scope"]["root_keys"])
        reached = set(self.inventory["dumps"]["english"]["reachability"]["reachable"])
        self.assertEqual(132, len(reached))
        non_root = {entry["key"] for entry in self.inventory["entries"]
                    if entry["lifecycle"] != "direct-production-root"}
        self.assertTrue(non_root <= reached)
        self.assertEqual(117, len(roots))

    def test_asymmetry_and_drift_facts_are_frozen(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        for key, counts in list(self.inventory["scope"]["baseline_asymmetry"].items())[:5]:
            self.assertEqual(
                counts,
                [len(by_key[key]["english_variants"]),
                 len(by_key[key]["chinese_variants"])],
            )
        self.assertEqual(
            set(tuple(item) for item in
                self.inventory["scope"]["baseline_token_multiset_drift"]),
            MODULE.EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT,
        )

    def test_candidate_pair_rejects_weight_or_count_drift(self):
        variants = [{
            "weight": 10, "text": "x", "runtime_tokens": [],
            "random_site_counts": [], "lua_site_count": 0,
        }]
        en = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        zh = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        self.assertEqual(1, len(MODULE._pair_candidate(en, zh)))
        zh["entries"][0]["variants"][0]["weight"] = 2
        with self.assertRaisesRegex(MODULE.InventoryError, "weight order"):
            MODULE._pair_candidate(en, zh)
        zh["entries"][0]["variants"] = []
        with self.assertRaisesRegex(MODULE.InventoryError, "variant count"):
            MODULE._pair_candidate(en, zh)

    def test_candidate_pair_rejects_token_or_random_topology_drift(self):
        variants = [{
            "weight": 10, "text": "@a@[x|y]", "runtime_tokens": ["@a@"],
            "random_site_counts": [2], "lua_site_count": 0,
        }]
        en = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        zh = {"entries": [{"key": "k", "variants": copy.deepcopy(variants)}]}
        zh["entries"][0]["variants"][0]["runtime_tokens"] = ["@b@"]
        with self.assertRaisesRegex(MODULE.InventoryError, "token multiset"):
            MODULE._pair_candidate(en, zh)
        zh["entries"][0]["variants"][0]["runtime_tokens"] = ["@a@"]
        zh["entries"][0]["variants"][0]["random_site_counts"] = [3]
        with self.assertRaisesRegex(MODULE.InventoryError, "random-site"):
            MODULE._pair_candidate(en, zh)

    def test_dump_family_misc_is_enforced_on_all_load_paths(self):
        # A speak-family dump must never be accepted on a decorlines (misc)
        # path: baseline/candidate loads and the proposal/scaffold load all
        # fail closed with the family mismatch.
        speak_en = copy.deepcopy(self.en)
        speak_en["database_name"] = "speak"
        speak_path = self.root / "speak-en.json"
        speak_path.write_text(json.dumps(speak_en, ensure_ascii=False),
                              encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'misc'"):
            MODULE._load_dataset(BASELINE, speak_path, "database/",
                                 "baseline EN", "baseline")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'misc'"):
            MODULE._proposal_dataset(speak_path, "database/", "proposal EN")
        speak_zh = copy.deepcopy(self.zh)
        speak_zh["database_name"] = "speak"
        speak_zh_path = self.root / "speak-zh.json"
        speak_zh_path.write_text(json.dumps(speak_zh, ensure_ascii=False),
                                 encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'misc'"):
            MODULE._load_dataset(BASELINE, speak_zh_path, "database/zh/",
                                 "baseline ZH", "baseline")

    def test_misc_dump_is_rejected_when_speak_family_is_expected(self):
        # The shared validator refuses a misc dump wherever a speak family
        # is expected, so a misc artifact can never satisfy a speak caller.
        with self.assertRaisesRegex(MODULE.hardened.ArtifactError,
                                    "database_name must be 'speak'"):
            MODULE.hardened.validate_artifact(
                self.en, "fixture EN", expected_database="speak"
            )
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'speak'"):
            MODULE.hardened._load_dump_safe(
                self.en_path, "fixture EN", "database/",
                expected_database="speak",
            )

    def _external_key_mutated_load(
        self, mutate, error_regex: str,
    ):
        """Run the full baseline load path on a dump whose external
        TextDB dependency key was mutated by ``mutate``; the exact-Git
        closure check must reject it."""
        mutated = copy.deepcopy(self.en)
        mutate(mutated)
        path = self.root / f"{self.id().split('.')[-1]}.json"
        path.write_text(json.dumps(mutated, ensure_ascii=False),
                        encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError, error_regex):
            MODULE._load_dataset(BASELINE, path, "database/",
                                 "negative EN", "baseline")

    def test_external_key_closure_binds_exact_git_entries(self):
        # I67-CODE-009 positive: the three external MiscDB dependency keys
        # (any_colour/any_colour_pattern/any_graffiti) are derived from
        # the exact-Git sources and must be selectable, parse-clean,
        # non-empty and verbatim-equal to the dump entries.
        derived = MODULE._derive_scoped_misc_dump(
            BASELINE, "database/", "fixture EN")
        external = MODULE._derive_external_entries(derived, "fixture EN")
        self.assertEqual(set(MODULE.EXTERNAL_TEXTDB_KEYS), set(external))
        for key, entry in external.items():
            self.assertIsNone(entry["parse_error"], key)
            self.assertFalse(entry["body_empty"], key)
            self.assertTrue(entry["variants"], key)
        MODULE._require_external_key_closure(self.en, derived, "fixture EN")

    def test_external_key_remove_fails_closed(self):
        # I67-CODE-009 mutation 1: removing an external dependency key from
        # the dump must fail the full load path.
        def mutate(artifact):
            artifact["entries"] = [
                entry for entry in artifact["entries"]
                if entry["canonical_key"] != "any_graffiti"
            ]
        self._external_key_mutated_load(
            mutate, "missing external TextDB key")

    def test_external_key_empty_fails_closed(self):
        # I67-CODE-009 mutation 2: emptying an external dependency key
        # (empty body, no variants) must fail the full load path.
        def mutate(artifact):
            for entry in artifact["entries"]:
                if entry["canonical_key"] == "any_colour":
                    entry["raw_body"] = ""
                    entry["body_empty"] = True
                    entry["variants"] = []
        self._external_key_mutated_load(
            mutate, "does not match the exact Git derivation")

    def test_external_key_forged_fails_closed(self):
        # I67-CODE-009 mutation 3: a forged external dependency key (body
        # and variant text replaced with valid-looking content) must fail
        # the full load path: the forged entry passes artifact validation
        # but differs from the exact-Git derivation.
        def mutate(artifact):
            for entry in artifact["entries"]:
                if entry["canonical_key"] == "any_colour_pattern":
                    entry["raw_body"] = "forged replacement body"
                    entry["variants"] = [
                        dict(entry["variants"][0],
                             raw_pattern="forged replacement text")
                    ]
        self._external_key_mutated_load(
            mutate, "does not match the exact Git derivation")

    def test_scaffold_rejects_symlinked_path_components(self):
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "real-dir"
        real_dir.mkdir()
        link_dir = self.root / "link-dir"
        link_dir.symlink_to(real_dir, target_is_directory=True)
        scaffold_path = link_dir / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = real_dir / "decorlines-review-results.md"
        try:
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "without following a symlink"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertFalse((real_dir / "decorlines-review-results.md")
                             .exists())
        finally:
            MODULE.RESULTS_PATH = original

    def _scaffold_with_parent_swap(
        self, scaffold_path: Path, swap_after_create: bool,
        swap_action, error_regex: str,
    ) -> tuple[list[tuple], int, int]:
        """Run scaffold_results while the parent directory is swapped away
        exactly when the O_EXCL create is in flight, recording the rollback
        cleanup syscalls.

        ``swap_action`` renames/replaces the approved parent directory and
        runs either right before or right after the O_EXCL open returns
        (``swap_after_create``); either way the created file lands in the
        pinned, now relocated parent and the post-create chain verification
        must fail with ``error_regex``.

        Returns ``(events, file_fd, parent_fd)`` where ``events`` records
        every rollback cleanup call in call order as ``("close", fd)``,
        ``("unlink", name, dir_fd)`` and ``("fsync", fd)`` tuples; the
        created file and pinned parent descriptors are captured from the
        open hook so the assertions do not depend on fd reuse."""
        real_open = MODULE.os.open
        real_close = MODULE.os.close
        real_unlink = MODULE.os.unlink
        real_fsync = MODULE.os.fsync
        events: list[tuple] = []
        captured: dict[str, int] = {}

        def swapped_open(path, flags, *args, **kwargs):
            if flags & os.O_CREAT and "file_fd" not in captured:
                if not swap_after_create:
                    swap_action()
                fd = real_open(path, flags, *args, **kwargs)
                captured["file_fd"] = fd
                if swap_after_create:
                    swap_action()
                return fd
            if (flags & os.O_DIRECTORY and path == "parent"
                    and "parent_fd" not in captured):
                # First O_DIRECTORY open of the parent component is the
                # pinned ancestor; the later verification probe must not
                # overwrite the captured descriptor.
                fd = real_open(path, flags, *args, **kwargs)
                captured["parent_fd"] = fd
                return fd
            return real_open(path, flags, *args, **kwargs)

        def recording_close(fd):
            if fd == captured.get("file_fd"):
                events.append(("close", fd))
            return real_close(fd)

        def recording_unlink(name, **kwargs):
            events.append(("unlink", name, kwargs.get("dir_fd")))
            return real_unlink(name, **kwargs)

        def recording_fsync(fd):
            events.append(("fsync", fd))
            return real_fsync(fd)

        with mock.patch.object(MODULE.os, "open", new=swapped_open), \
                mock.patch.object(MODULE.os, "close",
                                  new=recording_close), \
                mock.patch.object(MODULE.os, "unlink",
                                  new=recording_unlink), \
                mock.patch.object(MODULE.os, "fsync",
                                  new=recording_fsync):
            with self.assertRaisesRegex(MODULE.InventoryError, error_regex):
                MODULE.scaffold_results(scaffold_path, self.inventory)
        return events, captured["file_fd"], captured["parent_fd"]

    def test_scaffold_rejects_parent_renamed_between_verify_and_create(self):
        # Swap the parent away between the pre-create chain verification and
        # the exclusive create: the helper must fail closed and the ledger
        # must never survive in the relocated directory.  The rollback must
        # run in the canonical order: close the created file, unlink the
        # exact basename through the pinned parent and fsync that parent.
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "rename-away"
        real_dir.mkdir()
        parent = real_dir / "parent"
        parent.mkdir()
        moved = real_dir / "moved-parent"
        scaffold_path = parent / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        try:
            events, file_fd, parent_fd = self._scaffold_with_parent_swap(
                scaffold_path,
                swap_after_create=False,
                swap_action=lambda: os.rename(parent, moved),
                error_regex="re-opened",
            )
            self.assertEqual(
                [("close", file_fd),
                 ("unlink", scaffold_path.name, parent_fd),
                 ("fsync", parent_fd)],
                events,
            )
            self.assertFalse((moved / scaffold_path.name).exists())
            self.assertFalse(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rejects_parent_replaced_between_verify_and_create(self):
        # Replace the parent with a fresh directory at the approved pathname
        # between the pre-create chain verification and the exclusive create:
        # identity re-verification must detect the swap, remove the file
        # created through the pinned (relocated) parent and fsync that parent
        # after the unlink, leaving neither the relocated nor the fresh
        # directory with a residual ledger.
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "replace-dir"
        real_dir.mkdir()
        parent = real_dir / "parent"
        parent.mkdir()
        moved = real_dir / "moved-parent"
        scaffold_path = parent / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path

        def replace_parent():
            os.rename(parent, moved)
            parent.mkdir()

        try:
            events, file_fd, parent_fd = self._scaffold_with_parent_swap(
                scaffold_path,
                swap_after_create=False,
                swap_action=replace_parent,
                error_regex="changed identity",
            )
            self.assertEqual(
                [("close", file_fd),
                 ("unlink", scaffold_path.name, parent_fd),
                 ("fsync", parent_fd)],
                events,
            )
            self.assertFalse((moved / scaffold_path.name).exists())
            self.assertFalse((parent / scaffold_path.name).exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rejects_parent_renamed_after_create(self):
        # A parent swap that happens after the exclusive create but before
        # the post-create chain verification must also fail closed and must
        # unlink the file already created through the pinned parent, closing
        # the file descriptor first and fsyncing the pinned parent after the
        # unlink (canonical rollback order).
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "rename-after"
        real_dir.mkdir()
        parent = real_dir / "parent"
        parent.mkdir()
        moved = real_dir / "moved-parent"
        scaffold_path = parent / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        try:
            events, file_fd, parent_fd = self._scaffold_with_parent_swap(
                scaffold_path,
                swap_after_create=True,
                swap_action=lambda: os.rename(parent, moved),
                error_regex="re-opened",
            )
            self.assertEqual(
                [("close", file_fd),
                 ("unlink", scaffold_path.name, parent_fd),
                 ("fsync", parent_fd)],
                events,
            )
            self.assertFalse((moved / scaffold_path.name).exists())
            self.assertFalse(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def _scaffold_with_injected_failure(
        self, scaffold_path: Path, *,
        fstat_hook=None, write_hook=None, fsync_hook=None,
        error_regex: str, error_type=OSError,
    ) -> tuple[list[tuple], int, int]:
        """Run scaffold_results while a post-create syscall hook sabotages
        one transaction step, recording the rollback cleanup syscalls.

        Exactly one of ``fstat_hook``/``write_hook``/``fsync_hook`` fires
        on its step (os.fstat on the created file, os.write, os.fsync on
        the file or the directory) and raises an exception matched by
        ``error_type``/``error_regex`` (OSError by default; pass
        ``error_type=KeyboardInterrupt`` for BaseException-injection
        tests).  Hooks receive the affected descriptor and the
        captured-fd dict ``(fd, captured)`` (``write_hook`` additionally
        receives the payload as ``(fd, data, captured)``), where
        ``captured["file_fd"]`` is the descriptor created by the O_EXCL
        open; every other call must fall back to the real syscall.

        Returns ``(events, file_fd, parent_fd)`` like
        _scaffold_with_parent_swap: events records every rollback cleanup
        call in call order as ``("close", fd)``, ``("unlink", name,
        dir_fd)`` and ``("fsync", fd)`` tuples; ``parent_fd`` is captured
        from the pinned ancestor open when the scaffold path has a parent
        component and is -1 otherwise (the unlink event then carries the
        authoritative pinned parent descriptor)."""
        real_open = MODULE.os.open
        real_close = MODULE.os.close
        real_unlink = MODULE.os.unlink
        real_fsync = MODULE.os.fsync
        real_fstat = MODULE.os.fstat
        real_write = MODULE.os.write
        events: list[tuple] = []
        captured: dict[str, int] = {}

        def capturing_open(path, flags, *args, **kwargs):
            fd = real_open(path, flags, *args, **kwargs)
            if flags & os.O_CREAT and "file_fd" not in captured:
                captured["file_fd"] = fd
            if (flags & os.O_DIRECTORY and path == "parent"
                    and "parent_fd" not in captured):
                # First O_DIRECTORY open of the parent component is the
                # pinned ancestor; verification probes must not overwrite
                # the captured descriptor.
                captured["parent_fd"] = fd
            return fd

        def recording_close(fd):
            if fd == captured.get("file_fd"):
                events.append(("close", fd))
            return real_close(fd)

        def recording_unlink(name, **kwargs):
            events.append(("unlink", name, kwargs.get("dir_fd")))
            return real_unlink(name, **kwargs)

        def recording_fsync(fd):
            events.append(("fsync", fd))
            if fsync_hook is not None:
                return fsync_hook(fd, captured)
            return real_fsync(fd)

        def recording_fstat(fd):
            if fstat_hook is not None:
                return fstat_hook(fd, captured)
            return real_fstat(fd)

        def recording_write(fd, data):
            if write_hook is not None:
                return write_hook(fd, data, captured)
            return real_write(fd, data)

        with mock.patch.object(MODULE.os, "open", new=capturing_open), \
                mock.patch.object(MODULE.os, "close",
                                  new=recording_close), \
                mock.patch.object(MODULE.os, "unlink",
                                  new=recording_unlink), \
                mock.patch.object(MODULE.os, "fsync",
                                  new=recording_fsync), \
                mock.patch.object(MODULE.os, "fstat",
                                  new=recording_fstat), \
                mock.patch.object(MODULE.os, "write",
                                  new=recording_write):
            with self.assertRaisesRegex(error_type, error_regex):
                MODULE.scaffold_results(scaffold_path, self.inventory)
        return events, captured.get("file_fd", -1), \
            captured.get("parent_fd", -1)

    def _assert_canonical_rollback(
        self, events: list[tuple], file_fd: int, basename: str,
    ) -> int:
        """Assert the recorded cleanup events contain the canonical
        rollback sequence close(file) -> unlink(basename, dir_fd) ->
        fsync(dir_fd) with nothing interleaved; the unlink and the
        trailing fsync must share the pinned parent descriptor.  Returns
        that parent descriptor."""
        unlink_events = [event for event in events
                         if event[0] == "unlink" and event[1] == basename]
        self.assertEqual(
            1, len(unlink_events),
            f"expected exactly one unlink of {basename!r}, got {events}",
        )
        parent_fd = unlink_events[0][2]
        index = events.index(unlink_events[0])
        self.assertGreaterEqual(
            index, 1,
            f"close must precede the unlink, got {events}",
        )
        self.assertLess(
            index + 1, len(events),
            f"fsync must follow the unlink, got {events}",
        )
        self.assertEqual(
            ("close", file_fd), events[index - 1],
            f"unlink was not preceded by close({file_fd}): {events}",
        )
        self.assertEqual(
            ("fsync", parent_fd), events[index + 1],
            f"unlink was not followed by fsync({parent_fd}): {events}",
        )
        return parent_fd

    def _assert_no_ledger_survives(self, scaffold_path: Path):
        """Assert the ledger exists nowhere: neither at the approved path
        nor relocated anywhere else under the temporary root."""
        self.assertFalse(scaffold_path.exists())
        self.assertEqual(
            [], [path for path in self.root.rglob(scaffold_path.name)],
            f"ledger {scaffold_path.name!r} survived outside the approved "
            f"path",
        )

    def test_scaffold_rolls_back_when_post_create_fstat_fails(self):
        # Blocker A (I67-CODE-004): a native OSError from os.fstat during
        # the post-create identity check must trigger the canonical
        # rollback exactly like an InventoryError chain mismatch, so no
        # exception type can leave a stale partial ledger that makes a
        # retry trip EEXIST.
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "post-create-fstat-fail.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_fstat = MODULE.os.fstat

        def fstat_hook(fd, captured):
            if fd == captured.get("file_fd"):
                raise OSError("injected post-create fstat failure")
            return real_fstat(fd)

        try:
            events, file_fd, _parent_fd = self._scaffold_with_injected_failure(
                scaffold_path, fstat_hook=fstat_hook,
                error_regex="injected post-create fstat failure",
            )
            self._assert_canonical_rollback(
                events, file_fd, scaffold_path.name)
            self._assert_no_ledger_survives(scaffold_path)
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertEqual(133, len(records))
            self.assertTrue(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rolls_back_partial_file_when_write_fails(self):
        # The payload is written with os.write in a partial-write loop; an
        # injected short write followed by an OSError on the retry must
        # roll back the partial file in the canonical order and the retry
        # must succeed without EEXIST.
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "write-fail.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_write = MODULE.os.write
        calls = []

        def write_hook(fd, data, captured):
            calls.append(fd)
            if len(calls) == 1:
                # Consume half the payload as a partial write, then fail
                # on the retry with a native OSError.
                half = len(data) // 2
                real_write(fd, data[:half])
                return half
            raise OSError("injected write failure")

        try:
            events, file_fd, _parent_fd = self._scaffold_with_injected_failure(
                scaffold_path, write_hook=write_hook,
                error_regex="injected write failure",
            )
            self._assert_canonical_rollback(
                events, file_fd, scaffold_path.name)
            self._assert_no_ledger_survives(scaffold_path)
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertEqual(133, len(records))
            self.assertTrue(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rolls_back_partial_file_when_file_fsync_fails(self):
        # The file fsync (first fsync call) fails; cleanup must unlink the
        # partial ledger in the canonical order (close -> unlink -> fsync
        # dir) and the retry must succeed without EEXIST.
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "file-fsync-fail.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_fsync = MODULE.os.fsync
        calls = []

        def fsync_hook(fd, captured):
            calls.append(fd)
            if len(calls) == 1:
                raise OSError("injected file fsync failure")
            return real_fsync(fd)

        try:
            events, file_fd, _parent_fd = self._scaffold_with_injected_failure(
                scaffold_path, fsync_hook=fsync_hook,
                error_regex="injected file fsync failure",
            )
            self._assert_canonical_rollback(
                events, file_fd, scaffold_path.name)
            self._assert_no_ledger_survives(scaffold_path)
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertEqual(133, len(records))
            self.assertTrue(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rolls_back_partial_file_when_directory_fsync_fails(self):
        # The directory fsync (second fsync call) fails after the file
        # content was fully written and fsynced; the ledger entry must
        # still be removed in the canonical order and the directory
        # fsynced again before the error propagates.
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "dir-fsync-fail.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_fsync = MODULE.os.fsync
        calls = []

        def fsync_hook(fd, captured):
            calls.append(fd)
            if len(calls) == 2:
                raise OSError("injected directory fsync failure")
            return real_fsync(fd)

        try:
            events, file_fd, _parent_fd = self._scaffold_with_injected_failure(
                scaffold_path, fsync_hook=fsync_hook,
                error_regex="injected directory fsync failure",
            )
            self._assert_canonical_rollback(
                events, file_fd, scaffold_path.name)
            self._assert_no_ledger_survives(scaffold_path)
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertEqual(133, len(records))
            self.assertTrue(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rolls_back_zero_byte_ledger_on_keyboard_interrupt(self):
        # I67-CODE-010: KeyboardInterrupt is a BaseException, not an
        # Exception.  An injected KeyboardInterrupt from os.write must
        # follow the same rollback path as any OSError: the zero-byte
        # ledger is unlinked in the canonical order and a retry succeeds
        # without EEXIST.
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "keyboard-interrupt.md"
        MODULE.RESULTS_PATH = scaffold_path

        def write_hook(fd, data, captured):
            raise KeyboardInterrupt("injected KeyboardInterrupt")

        try:
            events, file_fd, _parent_fd = self._scaffold_with_injected_failure(
                scaffold_path, write_hook=write_hook,
                error_regex="injected KeyboardInterrupt",
                error_type=KeyboardInterrupt,
            )
            self._assert_canonical_rollback(
                events, file_fd, scaffold_path.name)
            self._assert_no_ledger_survives(scaffold_path)
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertEqual(133, len(records))
            self.assertTrue(scaffold_path.exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_ignores_post_publish_ancestor_close_error(self):
        # I67-CODE-010: phase 4 closes the file first, then the pinned
        # chain in reverse (parent first, then ancestors).  A close error
        # on an ancestor after the parent already closed must not turn the
        # published ledger into a failure: the descriptor cleanup after
        # the publish fsync is best-effort, so the call succeeds, the
        # ledger keeps its complete payload and the committed state is
        # durable (a retry fails closed with EEXIST instead of a partial
        # residue).
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "ancestor-close-dir"
        real_dir.mkdir()
        parent = real_dir / "parent"
        parent.mkdir()
        scaffold_path = parent / "ancestor-close-fail.md"
        MODULE.RESULTS_PATH = scaffold_path
        real_open = MODULE.os.open
        real_close = MODULE.os.close
        real_fsync = MODULE.os.fsync
        captured: dict = {}
        state = {"armed": False, "failed": False}

        def capturing_open(path, flags, *args, **kwargs):
            fd = real_open(path, flags, *args, **kwargs)
            if flags & os.O_CREAT and "file_fd" not in captured:
                captured["file_fd"] = fd
            if (flags & os.O_DIRECTORY and path == "parent"
                    and "parent_fd" not in captured):
                captured["parent_fd"] = fd
            return fd

        def arming_fsync(fd):
            if fd == captured.get("parent_fd"):
                state["armed"] = True
            return real_fsync(fd)

        def sabotaging_close(fd):
            # After the publish fsync, the first close of a pinned
            # ancestor (i.e. not the created file, not the parent itself)
            # fails with a native OSError; the transaction must swallow it
            # as best-effort cleanup of the committed ledger.
            if (state["armed"] and not state["failed"]
                    and fd != captured.get("file_fd")
                    and fd != captured.get("parent_fd")):
                state["failed"] = True
                raise OSError(
                    "injected post-publish ancestor close failure")
            return real_close(fd)

        with mock.patch.object(MODULE.os, "open", new=capturing_open), \
                mock.patch.object(MODULE.os, "fsync", new=arming_fsync), \
                mock.patch.object(MODULE.os, "close",
                                  new=sabotaging_close):
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
        self.assertTrue(state["failed"],
                        "the ancestor close error was not injected")
        self.assertEqual(133, len(records))
        self.assertEqual(records, MODULE._strict_block(scaffold_path))
        # The published ledger is durable and complete: a retry fails
        # closed on the existing file rather than tripping over a partial
        # residue or overwriting the committed result.
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "exclusively create"):
            MODULE.scaffold_results(scaffold_path, self.inventory)

    def test_cli_rejects_speak_dump_on_decorlines_path(self):
        # The real decorlines CLI must fail closed when a speak-family dump
        # is supplied on a misc load path.
        speak = copy.deepcopy(self.en)
        speak["database_name"] = "speak"
        speak_path = self.root / "cli-speak-en.json"
        speak_path.write_text(json.dumps(speak, ensure_ascii=False),
                              encoding="utf-8")
        output = self.root / "cli-out.json"
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--baseline-ref", BASELINE,
             "--english-dump", str(speak_path),
             "--localized-dump", str(self.zh_path),
             "--inventory-output", str(output)],
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(2, result.returncode)
        self.assertIn("database_name must be 'misc'", result.stderr)
        self.assertFalse(output.exists())

    def test_scaffold_generates_empty_ledger_and_refuses_overwrite(self):
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "decorlines-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        try:
            records = MODULE.scaffold_results(scaffold_path, self.inventory)
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "exclusively create"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
        finally:
            MODULE.RESULTS_PATH = original
        self.assertEqual(133, len(records))
        metadata, cards = records[0], records[1:]
        self.assertEqual(132, len(cards))
        self.assertEqual(0, len(metadata["terminal_conclusion_counts"]))
        self.assertEqual("decorlines:" + self.inventory["entries"][0]["key"],
                         cards[0]["identity"])
        self.assertIsNone(cards[0]["proposed_chinese_variants"])
        self.assertIsNone(cards[0]["terminal_conclusion"])
        self.assertEqual(
            MODULE._expected_metadata(self.inventory, cards),
            metadata,
        )


if __name__ == "__main__":
    unittest.main()
