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
        error_regex: str,
    ) -> tuple[list[tuple], int, int]:
        """Run scaffold_results while a post-create syscall hook sabotages
        one transaction step, recording the rollback cleanup syscalls.

        Exactly one of ``fstat_hook``/``write_hook``/``fsync_hook`` fires
        on its step (os.fstat on the created file, os.write, os.fsync on
        the file or the directory) and raises an OSError matched by
        ``error_regex``.  Hooks receive the affected descriptor and the
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
            with self.assertRaisesRegex(OSError, error_regex):
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
