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
SCRIPT = ROOT / ".claude/scripts/shout_inventory.py"
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("shout_inventory", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
BASELINE = "3d67767ee477f543c4e6db9a17981aae40a75307"


def _git_plumbing(arguments: list, input_text: str | None = None) -> str:
    """Run a git plumbing command in the repository without touching the
    worktree, index or refs (mirrors the decorlines fixture helper)."""
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "shout test",
        "GIT_AUTHOR_EMAIL": "shout-test@example.invalid",
        "GIT_COMMITTER_NAME": "shout test",
        "GIT_COMMITTER_EMAIL": "shout-test@example.invalid",
    }
    completed = subprocess.run(
        ["git", "-C", str(ROOT), *arguments], input=input_text,
        check=True, capture_output=True, text=True, env=env,
    )
    return completed.stdout.strip()


def fixture_commit_with_shoutcc(shoutcc_source: str) -> str:
    """Dangling commit whose tree mirrors the baseline's shout producer
    sources with ``crawl-ref/source/shout.cc`` replaced by
    ``shoutcc_source``.  Created purely through plumbing, so the working
    tree, index and refs are never touched."""

    def listing(git_path: str) -> dict:
        out = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", BASELINE, "--",
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

    shoutcc_blob = _git_plumbing(
        ["hash-object", "-w", "--stdin"], input_text=shoutcc_source)
    mons_tree = mktree(listing("crawl-ref/source/dat/mons"))
    jobs_tree = mktree(listing("crawl-ref/source/dat/jobs"))
    source_entries = {
        "dat": ("040000", "tree", mktree({
            "mons": ("040000", "tree", mons_tree),
            "jobs": ("040000", "tree", jobs_tree),
        })),
        "shout.cc": ("100644", "blob", shoutcc_blob),
    }
    for name in ("transform.cc", "database.cc", "mon-util.cc"):
        source_entries[name] = listing(f"crawl-ref/source/{name}")[name]
    source_entries["util"] = ("040000", "tree", mktree({
        "mon-gen": ("040000", "tree", mktree({
            "header.txt": listing(
                "crawl-ref/source/util/mon-gen")["header.txt"],
        })),
    }))
    source_tree = mktree(source_entries)
    crawl_ref_tree = mktree({"source": ("040000", "tree", source_tree)})
    root_tree = mktree({"crawl-ref": ("040000", "tree", crawl_ref_tree)})
    return _git_plumbing(
        ["commit-tree", root_tree, "-m",
         "shout exact-source negative fixture"]
    )


def committed_source(oid: str, git_path: str) -> str:
    """UTF-8 text of one committed file at the exact OID."""
    return MODULE.hardened.shared._decode_utf8(
        MODULE.hardened.shared._git_blob_at_oid(oid, git_path, "fixture"),
        "fixture",
    )


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
         "shout exact-source negative fixture"]
    )


def exact_artifact(oid: str, directory: str) -> dict:
    """Rebuild the full shout TextDB dump from exact Git inputs with the
    production load order, DBM_REPLACE merge and weighted-variant parse."""
    shared = MODULE.hardened.shared
    if directory == "database/":
        manifest = MODULE._shoutdb_source_manifest(oid, f"fixture {directory}")
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
        "database_name": "shout",
        "source_directory": directory,
        "sources": sources,
        "entries": sorted(entries, key=lambda entry: entry["canonical_key"]),
    }


def review_variant(variant: dict) -> dict:
    return {"weight": variant["weight"], "text": variant["text"]}


def aligned_zh_source(zh_text: str, en_text: str) -> str:
    """The ZH TextDB source with every identity body replaced by the EN
    body (so per-key variant counts, weights, tokens and parse shape equal
    EN exactly), except the __BUGGY sentinel block, which keeps the ZH
    body byte-identical to the baseline derivation because the sentinel
    audit is role-independent and content-frozen.  insult.txt has no
    sentinel, so its aligned form is the EN file verbatim."""
    if "__BUGGY" not in zh_text:
        return en_text
    start = zh_text.index("__BUGGY")
    end = zh_text.index("%%%%", start) + len("%%%%")
    sentinel = zh_text[start:end]
    en_start = en_text.index("__BUGGY")
    en_end = en_text.index("%%%%", en_start) + len("%%%%")
    return en_text[:en_start] + sentinel + en_text[en_end:]


def aligned_candidate_artifacts(en_shout, en_insult, zh_shout, zh_insult):
    """Fixture commit whose ZH shout/insult sources are EN-shaped (the
    __BUGGY sentinel preserved from ZH) plus the derived EN/ZH dumps."""
    fixture = fixture_commit_with_replaced_blobs({
        "crawl-ref/source/dat/database/zh/shout.txt":
            aligned_zh_source(zh_shout, en_shout),
        "crawl-ref/source/dat/database/zh/insult.txt":
            aligned_zh_source(zh_insult, en_insult),
    })
    return (fixture, exact_artifact(fixture, "database/"),
            exact_artifact(fixture, "database/zh/"))


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
        "display_context": "由 shout.cc::monster_shout / transform.cc 消费的喊叫消息。",
        "producer_consumer": MODULE._card_producer_consumer(
            entry, MODULE.FROZEN_PRODUCER_CONSUMER),
        "evidence_locations": MODULE._evidence_locations(
            entry, MODULE.FROZEN_PRODUCER_CONSUMER),
        "current_english_variants": current_en,
        "current_chinese_variants": current_zh,
        "proposed_english_variants": copy.deepcopy(current_en),
        "proposed_chinese_variants": copy.deepcopy(current_zh),
        "terminal_conclusion": "keep",
        "confidence": "high",
        "rationale": "逐变体核对语义、权重、token 与组合语序后保持现状。",
        "rejected_alternatives": ["不改变随机权重或递归身份。"],
        "reentry_trigger": "shout/insult source、消费者、加载顺序或术语权威变化时重审。",
        "deferral_owner": None,
        "deferral_reason": None,
    }


class ShoutInventoryTests(unittest.TestCase):
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
        cards.sort(key=lambda card: card["identity"])
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
        self.assertEqual(124, len(self.inventory["entries"]))
        self.assertEqual(91 + 33,
                         self.inventory["scope"]["expected_identity_counts"]["total"])
        self.assertEqual(85, self.inventory["scope"]["root_key_count"])
        self.assertEqual(
            {"english": {"shout.txt": 118, "insult.txt": 557},
             "chinese": {"shout.txt": 118, "insult.txt": 532}},
            self.inventory["scope"]["baseline_variant_counts"],
        )
        self.assertEqual(
            {"english": {"shout.txt": 119, "insult.txt": 557},
             "chinese": {"shout.txt": 119, "insult.txt": 532}},
            self.inventory["scope"]["baseline_dump_variant_totals"],
        )
        self.assertEqual(8, len(self.inventory["scope"]["baseline_asymmetry"]))
        self.assertEqual(17, len(
            self.inventory["scope"]["baseline_token_multiset_drift"]))
        self.assertEqual({"english": 0, "chinese": 0},
                         self.inventory["scope"]["baseline_random_sites"])
        self.assertEqual({"english": 0, "chinese": 0},
                         self.inventory["scope"]["baseline_lua_sites"])
        self.assertEqual([], self.inventory["dumps"]["english"]["token_facts"]["unresolved"])
        self.assertEqual([], self.inventory["dumps"]["localized"]["token_facts"]["unresolved"])
        self.assertEqual(["player sphinx riddle lines"],
                         self.inventory["scope"]["title_block_artifacts"]["english"])
        self.assertEqual([], self.inventory["scope"]["title_block_artifacts"]["chinese"])
        self.assertEqual(["__buggy"], self.inventory["scope"]["sentinel_keys"])
        self.assertEqual(["giant slug"], self.inventory["scope"]["legacy_keys"])

    def test_inventory_output_schema_stays_byte_stable(self):
        # The frozen review ledger binds inventory_sha256 to the output
        # schema; the production-derived classification must not change the
        # hashed inventory shape.
        legacy_keys = {"artifact_sha256", "identity_count", "lua_site_count",
                       "per_file_identity_counts", "per_file_variant_counts",
                       "random_site_count", "reachability", "root_key_count",
                       "source_name", "source_sha256", "token_facts",
                       "variant_count"}
        self.assertEqual(legacy_keys, set(self.inventory["dumps"]["english"]))
        self.assertEqual(legacy_keys, set(self.inventory["dumps"]["localized"]))
        # The frozen ledger binds inventory_sha256 to the output schema; the
        # I69-R3-CODE-001 database-role-aware consumers changed the scope's
        # producer_consumer facts and SpeakDB graph keys, so the hash is
        # mechanically updated together with the regenerated ledger.
        self.assertEqual(
            "2dcec4bc250d2b6fd7318039580a9bdba93bb38ab5eb6166aafaab22c693ae33",
            self.inventory["inventory_sha256"],
        )

    def test_title_block_parse_and_derived_layers_agree(self):
        # The "#### Player sphinx riddle lines" comment title block: the
        # parse layer (production parse_db_keys) and the derived layer (the
        # dump) must both produce exactly one zero-body artifact and the
        # title must never become an identity.
        shared = MODULE.hardened.shared
        snapshot = MODULE._derive_scoped_shout_dump(
            BASELINE, "database/", "fixture EN")
        shout_source = next(source for source in snapshot["sources"]
                            if source["source_name"] == "database/shout.txt")
        definitions = shared.parse_db_keys(
            shout_source["normalized_utf8"], "database/shout.txt")
        raw_keys = {shared.lowercase_string(d.raw_key) for d in definitions}
        dump_keys = {
            entry["canonical_key"] for entry in self.en["entries"]
            if any(item["source_name"] == "database/shout.txt"
                   for item in entry["source_history"])
        }
        self.assertEqual(raw_keys, dump_keys)
        self.assertIn("player sphinx riddle lines", raw_keys)
        artifact = next(entry for entry in self.en["entries"]
                        if entry["canonical_key"]
                        == "player sphinx riddle lines")
        self.assertTrue(artifact["body_empty"])
        self.assertEqual("BUG, EMPTY ENTRY", artifact["parse_error"])
        self.assertEqual([], artifact["variants"])
        identities = {entry["key"] for entry in self.inventory["entries"]}
        self.assertNotIn("player sphinx riddle lines", identities)
        # A zero-body key outside the frozen artifact set fails closed.
        mutated = copy.deepcopy(self.en)
        ghost = next(entry for entry in mutated["entries"]
                     if entry["canonical_key"] == "fighter player ghost")
        ghost["raw_body"] = ""
        ghost["body_empty"] = True
        ghost["variants"] = []
        ghost["parse_error"] = "BUG, EMPTY ENTRY"
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "parse error or empty body"):
            MODULE._source_rows(mutated, "database/", "negative EN")

    def test_double_load_provenance_is_checked_per_db(self):
        # insult.txt is loaded by ShoutDB (index 1) and SpeakDB (index 4);
        # both manifests are bound to exact Git and recorded separately.
        manifest = MODULE._shoutdb_source_manifest(BASELINE, "fixture")
        self.assertEqual(["database/shout.txt", "database/insult.txt"],
                         manifest)
        self.assertEqual(4, MODULE._speakdb_insult_provenance(
            BASELINE, "fixture"))
        self.assertEqual(
            {"shoutdb": {"shout.txt": 0, "insult.txt": 1},
             "speakdb": {"insult.txt": 4}},
            self.inventory["scope"]["provenance"],
        )

    def test_speakdb_insult_parity_binds_dump_to_speakdb_load(self):
        # Every insult.txt entry of the ShoutDB dump must match the
        # SpeakDB-scoped derivation verbatim after the load-index remap.
        MODULE._require_speakdb_insult_parity(self.en, BASELINE, "fixture EN")
        derived = MODULE.hardened.shared._derive_scoped_dump(
            BASELINE, "database/", "fixture EN", source_basename="insult.txt")
        self.assertEqual(33, len(derived["entries"]))

    def test_speakdb_insult_parity_rejects_tampered_entries(self):
        # I69-CODE-003 mutation: forging one SpeakDB-only insult key in the
        # ShoutDB dump must fail the double-load parity check.
        mutated = copy.deepcopy(self.en)
        for entry in mutated["entries"]:
            if entry["canonical_key"] == "insult general noun":
                entry["raw_body"] = "forged body\n"
                entry["variants"] = [dict(entry["variants"][0],
                                          raw_pattern="forged body")]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "double-load parity"):
            MODULE._require_speakdb_insult_parity(mutated, BASELINE,
                                                  "negative EN")

    def test_speakdb_insult_parity_rejects_removed_key(self):
        mutated = copy.deepcopy(self.en)
        mutated["entries"] = [
            entry for entry in mutated["entries"]
            if entry["canonical_key"] != "small_food"
        ]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "SpeakDB insult key set differs"):
            MODULE._require_speakdb_insult_parity(mutated, BASELINE,
                                                  "negative EN")

    def test_root_derivation_binds_exact_git_producers(self):
        facts = MODULE._derivable_root_facts(BASELINE, "fixture")
        self.assertEqual(26, len(facts["default_keys"]))
        self.assertEqual(tuple(facts["default_keys"]),
                         MODULE.DEFAULT_MSG_KEYS)
        self.assertGreater(len(facts["monsters"]), 600)
        self.assertIn("moth of wrath", facts["monsters"])
        self.assertIn("polyphemus", facts["monsters"])
        self.assertIn("player ghost", facts["monsters"])
        self.assertIn("giant slug", facts["axed"])
        self.assertEqual(26, len(facts["jobs"]))
        self.assertIn("fighter", facts["jobs"])
        self.assertIn("wanderer", facts["jobs"])

    def test_mutated_default_msg_keys_fail_closed(self):
        # I69-CODE-004 exact-source negative: dropping one entry from the
        # default_msg_keys map in a real Git fixture commit must fail the
        # derivation instead of silently reclassifying the roots.
        source = MODULE.hardened.shared._decode_utf8(
            MODULE.hardened.shared._git_blob_at_oid(
                BASELINE, "crawl-ref/source/shout.cc", "fixture"),
            "fixture",
        )
        mutated = source.replace('{ S_LAUGH,          "__LAUGH" },', "")
        fixture = fixture_commit_with_shoutcc(mutated)
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "default_msg_keys differ"):
            MODULE._derivable_root_facts(fixture, "negative fixture")

    def test_classification_is_exactly_one_of_five_classes(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        lifecycles = {}
        for entry in self.inventory["entries"]:
            lifecycles.setdefault(entry["lifecycle"], set()).add(entry["key"])
        self.assertEqual(85, len(lifecycles["direct-production-root"]))
        self.assertEqual(set(MODULE.FRAGMENT_KEYS),
                         lifecycles["recursive-shoutdb-fragment"])
        self.assertEqual({"giant slug"},
                         lifecycles["legacy-axed-monster"])
        self.assertEqual(
            set(self.inventory["scope"]["shoutdb_recursion_insult_keys"]),
            lifecycles["recursive-shoutdb-insult"],
        )
        self.assertEqual(
            set(self.inventory["scope"]["speakdb_postprocess_keys"]),
            lifecycles["speakdb-postprocessing-insult"],
        )
        # Every identity key is exactly one of the five classes.
        self.assertEqual(124, sum(len(keys) for keys in lifecycles.values()))

    def test_reachability_is_proven_not_assumed(self):
        facts = self.inventory["dumps"]["english"]["reachability"]
        seeds = set(self.inventory["scope"]["closure_seeds"])
        self.assertEqual(32, len(seeds))
        roots = set(self.inventory["scope"]["root_keys"])
        insult = set(self.inventory["scope"]["shoutdb_recursion_insult_keys"])
        # Full closure from every direct root: the roots themselves plus all
        # ShoutDB-recursion non-roots (5 fragments + 20 insult keys).
        self.assertEqual(
            roots | set(MODULE.FRAGMENT_KEYS) | insult,
            set(facts["full"]["reachable"]),
        )
        # The imp chain is monster-root-driven, not seed-driven.
        self.assertEqual(sorted(MODULE.MONSTER_DRIVEN_NON_ROOTS),
                         facts["monster_driven_non_roots"])
        self.assertTrue(
            set(MODULE.MONSTER_DRIVEN_NON_ROOTS).isdisjoint(
                facts["seed_non_roots"])
        )
        # Seed-driven non-roots: the 4 riddle fragments plus the 18
        # demon-taunt insult chain keys (incl. the general species keys).
        self.assertEqual(
            (set(MODULE.FRAGMENT_KEYS) - MODULE.MONSTER_DRIVEN_NON_ROOTS)
            | (insult - MODULE.MONSTER_DRIVEN_NON_ROOTS),
            set(facts["seed_non_roots"]),
        )
        # SpeakDB-only keys are never ShoutDB-reachable; every non-root key
        # is reachable through one of the two paths.
        non_roots = {entry["key"] for entry in self.inventory["entries"]
                     if entry["lifecycle"] != "direct-production-root"}
        speakdb_only = set(self.inventory["scope"]["speakdb_postprocess_keys"])
        shoutdb_reached = set(facts["full"]["reachable"])
        self.assertEqual(39, len(non_roots))
        self.assertEqual(13, len(speakdb_only))
        # The legacy AXED_MON key is exempt from the reachability proof;
        # every other non-root key is ShoutDB-reachable or SpeakDB-only.
        self.assertTrue(
            non_roots - speakdb_only - MODULE.EXPECTED_LEGACY_KEYS
            <= shoutdb_reached
        )
        self.assertFalse(speakdb_only & shoutdb_reached)
        self.assertNotIn("giant slug", shoutdb_reached)

    def test_asymmetry_and_drift_facts_are_frozen(self):
        by_key = {entry["key"]: entry for entry in self.inventory["entries"]}
        for key, counts in self.inventory["scope"]["baseline_asymmetry"].items():
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
        en = {"entries": [{"key": "k", "source_basename": "shout.txt",
                           "variants": copy.deepcopy(variants)}]}
        zh = {"entries": [{"key": "k", "source_basename": "shout.txt",
                           "variants": copy.deepcopy(variants)}]}
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
        en = {"entries": [{"key": "k", "source_basename": "shout.txt",
                           "variants": copy.deepcopy(variants)}]}
        zh = {"entries": [{"key": "k", "source_basename": "shout.txt",
                           "variants": copy.deepcopy(variants)}]}
        zh["entries"][0]["variants"][0]["runtime_tokens"] = ["@b@"]
        with self.assertRaisesRegex(MODULE.InventoryError, "token multiset"):
            MODULE._pair_candidate(en, zh)
        zh["entries"][0]["variants"][0]["runtime_tokens"] = ["@a@"]
        zh["entries"][0]["variants"][0]["random_site_counts"] = [3]
        with self.assertRaisesRegex(MODULE.InventoryError, "random-site"):
            MODULE._pair_candidate(en, zh)

    def test_dump_family_shout_is_enforced_on_all_load_paths(self):
        # A speak-family dump must never be accepted on a shout path.
        speak_en = copy.deepcopy(self.en)
        speak_en["database_name"] = "speak"
        speak_path = self.root / "speak-en.json"
        speak_path.write_text(json.dumps(speak_en, ensure_ascii=False),
                              encoding="utf-8")
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "database_name must be 'shout'"):
            MODULE._load_dataset(BASELINE, speak_path, "database/",
                                 "baseline EN", "baseline")

    def test_shout_dump_is_rejected_when_speak_family_is_expected(self):
        with self.assertRaisesRegex(MODULE.hardened.ArtifactError,
                                    "database_name must be 'speak'"):
            MODULE.hardened.validate_artifact(
                self.en, "fixture EN", expected_database="speak"
            )

    def test_complete_keep_ledger_passes(self):
        evidence = self.validate(self.records())
        self.assertEqual(124, len(evidence["cards"]))
        self.assertEqual(
            self.inventory["inventory_sha256"],
            evidence["metadata"]["inventory_sha256"],
        )

    def test_missing_identity_and_current_text_drift_fail_closed(self):
        records = self.records()
        records.pop()
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError, "124 cards"):
            self.validate(records)

        records = self.records()
        records[1]["current_english_variants"][0]["text"] += " drift"
        with self.assertRaisesRegex(MODULE.InventoryError, "current EN mismatch"):
            self.validate(records)

    def test_unreviewed_proposal_and_deferral_metadata_fail_closed(self):
        records = self.records()
        records[1]["proposed_chinese_variants"][0]["text"] += "改"
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "conclusion/change mismatch"):
            self.validate(records)

        records = self.records()
        records[1]["terminal_conclusion"] = "defer terminology"
        records[0] = MODULE._expected_metadata(self.inventory, records[1:])
        with self.assertRaisesRegex(MODULE.InventoryError, "requires owner"):
            self.validate(records)

    def test_scaffold_generates_empty_ledger_and_refuses_overwrite(self):
        original = MODULE.RESULTS_PATH
        scaffold_path = self.root / "shout-review-results.md"
        MODULE.RESULTS_PATH = scaffold_path
        try:
            records = MODULE.scaffold_results(scaffold_path,
                                              self.inventory)
            self.assertEqual(125, len(records))
            self.assertTrue(scaffold_path.exists())
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "exclusively create"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
            # The scaffolded ledger sorts cards by identity (insult: first,
            # then shout:), matching the strict validation order.
            text = scaffold_path.read_text(encoding="utf-8")
            first_card = records[1]
            self.assertEqual("insult:", first_card["identity"][:7])
            self.assertIn(MODULE.STRICT_BEGIN, text)
            self.assertIn(MODULE.STRICT_END, text)
        finally:
            MODULE.RESULTS_PATH = original

    def test_scaffold_rejects_symlinked_path_components(self):
        original = MODULE.RESULTS_PATH
        real_dir = self.root / "real-dir"
        real_dir.mkdir()
        link_dir = self.root / "link-dir"
        link_dir.symlink_to(real_dir, target_is_directory=True)
        scaffold_path = link_dir / "shout-review-results.md"
        MODULE.RESULTS_PATH = real_dir / "shout-review-results.md"
        try:
            with self.assertRaisesRegex(MODULE.InventoryError,
                                        "without following a symlink"):
                MODULE.scaffold_results(scaffold_path, self.inventory)
            self.assertFalse((real_dir / "shout-review-results.md")
                             .exists())
        finally:
            MODULE.RESULTS_PATH = original

    def test_identity_row_mutations_fail_closed(self):
        # Removing a live monster identity breaks the frozen counts.
        mutated = copy.deepcopy(self.en)
        mutated["entries"] = [
            entry for entry in mutated["entries"]
            if entry["canonical_key"] != "moth of wrath"
        ]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "identity count mismatch"):
            MODULE._source_rows(mutated, "database/", "negative EN")

        # Promoting the title artifact to a real body fails the identity
        # count too (the artifact must stay zero-body).
        mutated = copy.deepcopy(self.en)
        for entry in mutated["entries"]:
            if entry["canonical_key"] == "player sphinx riddle lines":
                entry["raw_body"] = "x\n"
                entry["body_empty"] = False
                entry["parse_error"] = None
                entry["variants"] = [{
                    "locator": {"canonical_key":
                                "player sphinx riddle lines",
                                "variant_ordinal": 0},
                    "provenance": entry["effective_provenance"],
                    "weight": 10, "raw_pattern": "x",
                }]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "must be a zero-body entry"):
            MODULE._source_rows(mutated, "database/", "negative EN")

    def test_sentinel_and_runtime_values_classification(self):
        # __buggy is the only in-file sentinel; the runtime fallback values
        # must never be ShoutDB keys.  The guard compares in the canonical
        # lowercase key space (scoped_keys is lowercase_string), so each of
        # __DEFAULT/__NEXT/__NONE is rejected by the classifier and the
        # isdisjoint probe is not vacuous.
        shared = MODULE.hardened.shared
        snapshot = MODULE._derive_scoped_shout_dump(
            BASELINE, "database/", "fixture EN")
        shout_source = next(source for source in snapshot["sources"]
                            if source["source_name"] == "database/shout.txt")
        definitions = shared.parse_db_keys(
            shout_source["normalized_utf8"], "database/shout.txt")
        raw_keys = {shared.lowercase_string(d.raw_key) for d in definitions}
        self.assertIn("__buggy", raw_keys)
        self.assertTrue(raw_keys.isdisjoint(MODULE.RUNTIME_SENTINEL_VALUES))
        family = {"database/shout.txt", "database/insult.txt"}
        scoped_keys = {
            entry["canonical_key"].lower() for entry in self.en["entries"]
            if any(item["source_name"] in family
                   for item in entry["source_history"])
        }
        self.assertEqual(126, len(scoped_keys))
        rows, _per_file = MODULE._source_rows(self.en, "database/",
                                              "fixture EN")
        shout_rows = [row for row in rows
                      if any(item["source_name"] == "database/shout.txt"
                             for item in row["source_history"])]
        insult_rows = [row for row in rows
                       if any(item["source_name"] == "database/insult.txt"
                              for item in row["source_history"])]
        derivable = MODULE._derivable_root_facts(BASELINE, "fixture")
        for key in ("__default", "__next", "__none"):
            with self.subTest(key=key):
                with self.assertRaisesRegex(MODULE.InventoryError,
                                            "runtime sentinel values"):
                    MODULE._classify_keys(
                        scoped_keys | {key}, shout_rows, insult_rows,
                        derivable, "negative EN")

    def test_candidate_runtime_sentinel_key_mutation_rejected(self):
        # I69-R2-CODE-003: a reviewed commit adding any runtime fallback
        # value as a ShoutDB key must be rejected by the runtime-sentinel
        # guard in the candidate audit (checked in the canonical lowercase
        # key space before the identity-count gate).
        source = committed_source(
            BASELINE, "crawl-ref/source/dat/database/shout.txt")
        for key in ("__DEFAULT", "__NEXT", "__NONE"):
            with self.subTest(key=key):
                mutated = source + f"\n{key}\n\nSOUND:x\n%%%%\n"
                fixture = fixture_commit_with_replaced_blobs({
                    "crawl-ref/source/dat/database/shout.txt": mutated,
                })
                with self.assertRaisesRegex(MODULE.InventoryError,
                                            "runtime sentinel values"):
                    self.add_candidate_mocked(
                        copy.deepcopy(self.inventory), fixture,
                        exact_artifact(fixture, "database/"),
                        exact_artifact(fixture, "database/zh/"),
                    )

    def test_candidate_sentinel_two_variant_mutation_rejected(self):
        # I69-R2-CODE-003: the sentinel must keep exactly one variant per
        # language; a candidate doubling the __buggy value line must be
        # rejected by the sentinel-count check (role-independent).
        source = committed_source(
            BASELINE, "crawl-ref/source/dat/database/shout.txt")
        start = source.index("__BUGGY")
        separator = source.index("%%%%", start)
        mutated = (source[:separator]
                   + "\nSOUND:You hear doubly buggy behaviour!\n"
                   + source[separator:])
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/shout.txt": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "sentinel variant count mismatch"):
            self.add_candidate_mocked(
                copy.deepcopy(self.inventory), fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"),
            )

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
            return MODULE.add_candidate(inventory, BASELINE, candidate_ref,
                                        en_path, zh_path)

    def test_candidate_sentinel_unchanged_passes(self):
        # Sentinel positive control with the approved aligned shape: a
        # candidate whose __buggy entry is byte-identical to the baseline
        # ZH derivation and whose identity data is aligned to EN (insult
        # dump total 557) passes the candidate _load_dataset gate,
        # including the role-aware dump totals and the sentinel audit.
        # The full add_candidate + validate_results gate is covered by
        # test_candidate_aligned_dump_audit_passes.
        fixture, en, zh = aligned_candidate_artifacts(
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/shout.txt"),
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/insult.txt"),
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/zh/shout.txt"),
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/zh/insult.txt"),
        )
        en_path = self.root / f"{self.id().split('.')[-1]}-en.json"
        zh_path = self.root / f"{self.id().split('.')[-1]}-zh.json"
        en_path.write_text(json.dumps(en, ensure_ascii=False),
                           encoding="utf-8")
        zh_path.write_text(json.dumps(zh, ensure_ascii=False),
                           encoding="utf-8")
        approved = {"shout.txt": 119, "insult.txt": 557}
        MODULE._load_dataset(fixture, en_path, "database/",
                             "candidate EN", "candidate",
                             sentinel_baseline=MODULE._derived_sentinel_entry(
                                 BASELINE, "database/",
                                 "baseline sentinel EN"),
                             expected_dump_variants=approved)
        MODULE._load_dataset(fixture, zh_path, "database/zh/",
                             "candidate ZH", "candidate",
                             sentinel_baseline=MODULE._derived_sentinel_entry(
                                 BASELINE, "database/zh/",
                                 "baseline sentinel ZH"),
                             expected_dump_variants=approved)

    def test_candidate_aligned_dump_audit_passes(self):
        # I69-R2-CODE-001 positive control: a candidate whose ZH dump
        # aligns every identity key to the EN shape (insult.txt dump total
        # 557 = the approved aligned total, no token drift, no unresolved
        # tokens) passes the complete candidate gate: add_candidate with
        # role-aware dump totals plus validate_results against a ledger
        # whose proposals match the aligned dump verbatim.  The baseline
        # path keeps the frozen 532 total (test_exact_git_inventory_...
        # and the baseline build cover it); the candidate path requires
        # the approved 557.
        fixture, en, zh = aligned_candidate_artifacts(
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/shout.txt"),
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/insult.txt"),
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/zh/shout.txt"),
            committed_source(BASELINE,
                             "crawl-ref/source/dat/database/zh/insult.txt"),
        )
        candidate = self.add_candidate_mocked(
            copy.deepcopy(self.inventory), fixture, en, zh)
        aligned_by_key = {
            entry["canonical_key"]: [
                {"weight": variant["weight"],
                 "text": variant["raw_pattern"]}
                for variant in entry["variants"]
            ]
            for entry in zh["entries"]
            if entry["canonical_key"] not in MODULE.SENTINEL_KEYS
            and entry["canonical_key"] not in MODULE.TITLE_BLOCK_ARTIFACTS
        }
        cards = []
        for entry in self.inventory["entries"]:
            card = card_for(entry)
            aligned = aligned_by_key[entry["key"]]
            card["proposed_chinese_variants"] = aligned
            card["terminal_conclusion"] = (
                "adjust" if aligned != card["current_chinese_variants"]
                else "keep")
            cards.append(card)
        cards.sort(key=lambda card: card["identity"])
        records = [MODULE._expected_metadata(self.inventory, cards), *cards]
        evidence = MODULE.validate_results(
            self.write_records(records), self.inventory, candidate=candidate)
        self.assertEqual(124, len(evidence["cards"]))
        self.assertEqual(
            {"shout.txt": 119, "insult.txt": 557},
            MODULE._proposal_dump_totals(records),
        )

    def test_candidate_sentinel_content_mutation_rejected(self):
        # I69-CODE-001: the sentinel is outside the 124-card ledger and the
        # identity rows, so a candidate commit that rewrites the __buggy
        # body (same variant count, frozen dump totals still hold) must be
        # rejected against the baseline derivation.
        source = committed_source(
            BASELINE, "crawl-ref/source/dat/database/shout.txt")
        mutated = source.replace(
            "SOUND:You hear doubly buggy behaviour!",
            "SOUND:You hear triply buggy behaviour!",
        )
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/shout.txt": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "sentinel content differs"):
            self.add_candidate_mocked(
                copy.deepcopy(self.inventory), fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"),
            )

    def test_candidate_sentinel_deletion_rejected(self):
        # I69-CODE-001: deleting the __buggy key from the candidate commit
        # must fail the candidate audit (sentinel presence is role-
        # independent).
        source = committed_source(
            BASELINE, "crawl-ref/source/dat/database/shout.txt")
        start = source.index("__BUGGY")
        end = source.index("%%%%", start) + len("%%%%")
        mutated = source[:start] + source[end:]
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/shout.txt": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "exactly one sentinel entry"):
            self.add_candidate_mocked(
                copy.deepcopy(self.inventory), fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"),
            )

    def test_producer_consumer_facts_derived_from_exact_git(self):
        # I69-R2-CODE-002: the five anchors are derived with snippet checks
        # from the exact baseline Git sources and equal the frozen facts:
        # the ShoutDB initializer at database.cc:134, the actual
        # getShoutString(key, suffix) lookup at shout.cc:176, the Sphinx
        # riddle call at transform.cc:2541, _get_species_insult at
        # mon-util.cc:4275 and the SpeakDB insult.txt literal at
        # database.cc:125 (none of them a default_msg_keys line or a
        # neighbouring DB initializer).
        facts = MODULE._producer_consumer_facts(BASELINE, "fixture")
        self.assertEqual(MODULE.FROZEN_PRODUCER_CONSUMER, facts)
        self.assertEqual("crawl-ref/source/database.cc:134",
                         facts["loader"])
        self.assertEqual("crawl-ref/source/shout.cc:176",
                         facts["shout_consumer"])
        self.assertEqual(facts, self.inventory["scope"]["producer_consumer"])
        by_identity = {entry["identity"]: entry
                       for entry in self.inventory["entries"]}
        sphinx = next(entry for entry in self.inventory["entries"]
                      if entry["key"] in MODULE.SPHINX_RIDDLE_KEYS)
        self.assertEqual(
            {"loader": facts["loader"],
             "riddle_consumer": facts["riddle_consumer"]},
            MODULE._card_producer_consumer(sphinx, facts),
        )
        legacy = next(entry for entry in self.inventory["entries"]
                      if entry["lifecycle"] == "legacy-axed-monster")
        self.assertEqual({"loader": facts["loader"]},
                         MODULE._card_producer_consumer(legacy, facts))
        species = next(entry for entry in self.inventory["entries"]
                       if entry["lifecycle"]
                       == "speakdb-postprocessing-insult")
        self.assertEqual(
            {"insult_postprocessing": facts["insult_postprocessing"],
             "loader": facts["loader"],
             "speakdb_double_load": facts["speakdb_double_load"]},
            MODULE._card_producer_consumer(species, facts),
        )

    def test_speakdb_monspeak_closure_reaches_all_dual_keys(self):
        # I69-R3-CODE-001: the SpeakDB-side consumption of the
        # ShoutDB-recursion insult chain is derived from the complete
        # exact-Git SpeakDB graph: the three monspeak seeds reference
        # @demon_taunt@ / @imp_taunt@ and their token closure reaches
        # exactly the 20 recursive-shoutdb-insult keys (dual-DB
        # reachability).  The monspeak seed sites and the secondary
        # SpeakDB / localized override definition lines equal the frozen
        # facts.
        speakdb = MODULE._speakdb_monspeak_facts(BASELINE, "fixture")
        self.assertEqual(
            MODULE.FROZEN_PRODUCER_CONSUMER["speakdb_monspeak_consumer"],
            speakdb["monspeak_consumer_sites"],
        )
        self.assertEqual(
            MODULE.FROZEN_PRODUCER_CONSUMER["speakdb_secondary_definition"],
            speakdb["secondary_definition_sites"],
        )
        self.assertEqual(
            MODULE.FROZEN_PRODUCER_CONSUMER["localized_override_source"],
            speakdb["localized_override_sites"],
        )
        dual = [entry["key"] for entry in self.inventory["entries"]
                if entry["lifecycle"] == "recursive-shoutdb-insult"]
        self.assertEqual(20, len(dual))
        self.assertEqual(sorted(MODULE.SPEAKDB_MONSPEAK_CLOSURE_KEYS),
                         sorted(dual))

    def test_general_fallback_and_dual_db_consumers_on_cards(self):
        # I69-R3-CODE-001: every recursive-shoutdb-insult card records the
        # SpeakDB consumption path (monspeak seeds) next to the ShoutDB
        # lookup; the three insult general keys additionally record the
        # _get_species_insult SpeakDB fallback consumer; the seven
        # cross-DB override keys record their secondary EN SpeakDB
        # definition and the localized zh/monspeak.txt override source in
        # producer_consumer and evidence_locations.
        facts = MODULE.FROZEN_PRODUCER_CONSUMER
        by_key = {entry["key"]: entry
                  for entry in self.inventory["entries"]}
        for key in sorted(MODULE.SPEAKDB_MONSPEAK_CLOSURE_KEYS):
            card = MODULE._card_producer_consumer(by_key[key], facts)
            self.assertEqual(facts["speakdb_monspeak_consumer"],
                             card["speakdb_monspeak_consumer"])
            self.assertEqual(facts["shout_consumer"],
                             card["shout_consumer"])
            self.assertEqual(facts["speakdb_double_load"],
                             card["speakdb_double_load"])
            evidence = MODULE._evidence_locations(by_key[key], facts)
            for site in facts["speakdb_monspeak_consumer"]:
                self.assertIn(f"speakdb-monspeak:{site}", evidence)
        for key in sorted(MODULE.INSULT_GENERAL_FALLBACK_KEYS):
            card = MODULE._card_producer_consumer(by_key[key], facts)
            self.assertEqual(facts["insult_postprocessing"],
                             card["insult_postprocessing"])
            self.assertEqual(facts["species_insult_fallback"],
                             card["species_insult_fallback"])
            self.assertIn(
                f"speakdb-fallback:{facts['species_insult_fallback']}",
                MODULE._evidence_locations(by_key[key], facts))
        for key in sorted(MODULE.CROSS_DB_OVERRIDE_KEYS):
            card = MODULE._card_producer_consumer(by_key[key], facts)
            self.assertEqual(
                facts["speakdb_secondary_definition"][key],
                card["speakdb_secondary_definition"])
            self.assertEqual(
                facts["localized_override_source"][key],
                card["localized_override_source"])
            evidence = MODULE._evidence_locations(by_key[key], facts)
            self.assertIn(
                f"speakdb-override:"
                f"{facts['speakdb_secondary_definition'][key]}",
                evidence)
            self.assertIn(
                f"localized-override:"
                f"{facts['localized_override_source'][key]}",
                evidence)

    def test_speakdb_monspeak_edge_mutation_rejected(self):
        # I69-R3-CODE-001: removing the @demon_taunt@ edge from the
        # _demon_taunt_ seed must fail closed instead of silently
        # dropping the SpeakDB consumption path of the 20 dual keys.
        source = committed_source(BASELINE,
                                  "crawl-ref/source/dat/database/"
                                  "monspeak.txt")
        mutated = source.replace(
            '_demon_taunt_\n\n@The_monster@ @says@ @to_foe@, '
            '"@demon_taunt@"',
            '_demon_taunt_\n\n@The_monster@ @says@ @to_foe@, '
            '"@give_up@"', 1)
        self.assertNotEqual(source, mutated)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/monspeak.txt": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "monspeak seed .* edge differs"):
            MODULE._speakdb_monspeak_facts(fixture, "negative fixture")

    def test_species_insult_fallback_mutation_rejected(self):
        # I69-R3-CODE-001: moving the _get_species_insult SpeakDB fallback
        # query (mon-util.cc "insult general " + type) shifts the derived
        # anchor and must fail closed.
        source = committed_source(BASELINE, "crawl-ref/source/mon-util.cc")
        mutated = source.replace(
            "    if (insult.empty()) // Species too specific?",
            "\n    if (insult.empty()) // Species too specific?", 1)
        self.assertNotEqual(source, mutated)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/mon-util.cc": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "anchors drifted"):
            MODULE._producer_consumer_facts(fixture, "negative fixture")

    def test_cross_db_override_binding_mutation_rejected(self):
        # I69-R3-CODE-001: deleting a secondary SpeakDB definition (the
        # Polyphemus key of EN monspeak.txt) must fail closed instead of
        # leaving the cross-DB override cards unbound.
        source = committed_source(BASELINE,
                                  "crawl-ref/source/dat/database/"
                                  "monspeak.txt")
        mutated = source.replace(
            "Polyphemus\n\n@_Polyphemus_common_@",
            "PolyphemusX\n\n@_Polyphemus_common_@", 1)
        self.assertNotEqual(source, mutated)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/monspeak.txt": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "misses SpeakDB definitions"):
            MODULE._speakdb_monspeak_facts(fixture, "negative fixture")

    def test_producer_consumer_source_anchor_mutation_rejected(self):
        # I69-R2-CODE-002: moving the ShoutDB initializer in a real Git
        # fixture commit shifts the derived loader anchor and must fail
        # closed instead of re-anchoring the ledger evidence.
        source = committed_source(BASELINE, "crawl-ref/source/database.cc")
        mutated = source.replace(
            '    TextDB("shout", "database/",',
            '\n    TextDB("shout", "database/",', 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/database.cc": mutated,
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "anchors drifted"):
            MODULE._producer_consumer_facts(fixture, "negative fixture")

    def test_candidate_producer_consumer_source_mutation_rejected(self):
        # I69-R2-CODE-002: a reviewed commit that moves the shout.cc
        # consumer lookup must be rejected by the candidate audit (the
        # candidate anchors are derived from the exact candidate Git
        # sources and must equal the frozen baseline facts).
        source = committed_source(BASELINE, "crawl-ref/source/shout.cc")
        mutated = source.replace(
            "    string message = getShoutString(key, suffix);",
            "\n    string message = getShoutString(key, suffix);", 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/shout.cc": mutated,
            "crawl-ref/source/dat/database/zh/shout.txt": aligned_zh_source(
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/zh/shout.txt"),
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/shout.txt")),
            "crawl-ref/source/dat/database/zh/insult.txt": aligned_zh_source(
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/zh/insult.txt"),
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/insult.txt")),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "anchors drifted"):
            self.add_candidate_mocked(
                copy.deepcopy(self.inventory), fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"),
            )

    def test_candidate_speakdb_edge_mutation_rejected(self):
        # I69-R3-CODE-001: a reviewed commit that drops the
        # _demon_taunt_ -> demon_taunt SpeakDB edge must be rejected by
        # the candidate audit (the candidate SpeakDB graph is derived
        # from the exact candidate Git sources and must reproduce the
        # frozen SpeakDB consumption facts).
        source = committed_source(BASELINE,
                                  "crawl-ref/source/dat/database/"
                                  "monspeak.txt")
        mutated = source.replace(
            '_demon_taunt_\n\n@The_monster@ @says@ @to_foe@, '
            '"@demon_taunt@"',
            '_demon_taunt_\n\n@The_monster@ @says@ @to_foe@, '
            '"@give_up@"', 1)
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/database/monspeak.txt": mutated,
            "crawl-ref/source/dat/database/zh/shout.txt": aligned_zh_source(
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/zh/shout.txt"),
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/shout.txt")),
            "crawl-ref/source/dat/database/zh/insult.txt": aligned_zh_source(
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/zh/insult.txt"),
                committed_source(
                    BASELINE, "crawl-ref/source/dat/database/insult.txt")),
        })
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "monspeak seed .* edge differs"):
            self.add_candidate_mocked(
                copy.deepcopy(self.inventory), fixture,
                exact_artifact(fixture, "database/"),
                exact_artifact(fixture, "database/zh/"),
            )

    def test_forged_producer_consumer_is_rejected(self):
        # I69-CODE-002: the producer/consumer evidence of every card must
        # equal the mechanically derived per-card value, not merely be a
        # non-empty dict.
        records = self.records()
        records[1]["producer_consumer"] = {
            "loader": "crawl-ref/source/database.cc:1",
            "shout_consumer": "crawl-ref/source/shout.cc:1",
        }
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "producer/consumer evidence mismatch"):
            self.validate(records)

    def test_producer_consumer_anchor_value_mutation_rejected(self):
        # I69-R2-CODE-002: changing one derived anchor value in a ledger
        # card must be rejected against the derived per-card facts.
        records = self.records()
        records[1]["producer_consumer"] = dict(
            records[1]["producer_consumer"])
        records[1]["producer_consumer"]["loader"] = \
            "crawl-ref/source/database.cc:999"
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "producer/consumer evidence mismatch"):
            self.validate(records)

    def test_forged_evidence_locations_are_rejected(self):
        # I69-CODE-002: evidence_locations must equal the mechanically
        # derived list (definition sites plus recursive reference sites)
        # verbatim; a plausible-looking partial list is rejected.
        records = self.records()
        records[1]["evidence_locations"] = [
            "crawl-ref/source/dat/database/insult.txt:186",
        ]
        with self.assertRaisesRegex(MODULE.InventoryError,
                                    "evidence locations mismatch"):
            self.validate(records)

    def test_git_tree_yamls_ignores_nested_directories(self):
        # I69-CODE-003: mon-gen.py/job-gen.py iterate
        # sorted(os.listdir(datadir)) and never descend, so a nested
        # dat/mons/*.yaml must not enter the exact-Git derivation (a
        # recursive ls-tree would miscount it).
        fixture = fixture_commit_with_replaced_blobs({
            "crawl-ref/source/dat/mons/nested/extra.yaml":
                "name: 'nested monster'\n",
        })
        baseline_yamls = MODULE._git_tree_yamls(
            BASELINE, "crawl-ref/source/dat/mons", "fixture")
        fixture_yamls = MODULE._git_tree_yamls(
            fixture, "crawl-ref/source/dat/mons", "fixture")
        self.assertEqual(baseline_yamls, fixture_yamls)
        self.assertNotIn("crawl-ref/source/dat/mons/nested/extra.yaml",
                         fixture_yamls)


if __name__ == "__main__":
    unittest.main()
