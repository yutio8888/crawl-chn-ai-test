#!/usr/bin/env python3
"""Build and audit the Issue #67 decorlines review inventory.

The inventory is derived from production ``textdb-phase0-dump`` artifacts of
the ``misc`` TextDB family and exact Git source snapshots.  It freezes all
132 decorlines identities (EN 209 / ZH 266 weighted variants at the baseline
OID), the exact 63 asymmetric key list (derived from the baseline itself,
never copied from prose), the random-site ([a|b] plus Lua) counts, the four
internal fragment tokens, the external TextDB dependency tokens and the
consumer-side post-processing tokens, and a complete reachability proof from
the consumed production root keys.

Consumer model (frozen): ``directn.cc::_walk_on_decor`` queries food-cache
keys (``<prefix> (fruit cache|meat cache|baked goods cache)`` where the
prefix is empty, a species name or a form wiz_name) and fountain keys
(``(<god>|default) (peaceful )?(fountain_blue|fountain_sparkling|
fountain_blood|fountain_eyes)`` plus the same shapes for ``dry_fountain``;
the plain ``default <fountain>`` slot is gated at runtime to non-dry
fountains, so ``default dry_fountain`` is a root key that can only be
reached by the default slot pattern, never displayed.  Everything else in
decorlines.txt is either one of the four internal fragments
(``_baked_good_and_reaction_``/``_fruit_and_reaction_``/
``_meat_and_reaction_``/``sparkling_message``) or one of the eleven diet
alias keys (carnivore/short/stone/inediate caches) that only recursion can
reach; the reachability proof requires every non-root key to be reached from
the root set, and the root set itself must exactly match the production query
patterns.  ``@any_colour@``/``@any_colour_pattern@``/``@any_graffiti@`` are
external MiscDB lookups resolved in the already-loaded colourname/graffiti
sources; ``@your_weapon@``/``@your_hands@`` are replaced by the consumer
after expansion.

The strict JSONL review ledger (one metadata record plus 132 cards) is the
issue #67 audit trail.  ``--scaffold-output`` generates the initial empty
ledger (exclusive create at ``docs/decorlines-review-results.md``, which
fails closed when a ledger already exists); the later zh-translator phase
fills the 132 cards, and ``--review-results`` plus the candidate parameters
bind every proposal to an exact-clean candidate commit.

Mutable artifacts (production dumps, review results, glossary) are read
through the hardened audited snapshot helpers (no-follow descriptor, regular
file, opened-inode identity).  In the candidate flow the review ledger and
glossary are read directly from the exact candidate commit tree as
regular-file blobs, and the exact-clean candidate boundary is proven before
any candidate data is consumed.  Generated evidence (``--inventory-output``)
may only be written to /tmp; the only repository write is the explicitly
scoped ledger scaffold.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

import wpnnoise_inventory as hardened


SCHEMA_VERSION = 1
SOURCE_BASENAME = "decorlines.txt"
STRICT_BEGIN = "<!-- BEGIN STRICT DECORLINES REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT DECORLINES REVIEW EVIDENCE v1 -->"
RESULTS_PATH = Path(__file__).resolve().parents[2] / "docs/decorlines-review-results.md"

# Frozen Issue #67 baseline shape (verified against the production dumps at
# the baseline OID; the asymmetric key list itself is derived from the
# baseline dumps below and only its count is frozen).
EXPECTED_IDENTITY_COUNT = 132
EXPECTED_BASELINE_EN_VARIANTS = 209
EXPECTED_BASELINE_ZH_VARIANTS = 266
EXPECTED_ASYMMETRY_COUNT = 63
EXPECTED_EN_RANDOM_SITES = 11
EXPECTED_ZH_RANDOM_SITES = 11
EXPECTED_EN_LUA_SITES = 5
EXPECTED_ZH_LUA_SITES = 5

# Keys that production (directn.cc::_walk_on_decor) never queries directly.
# The four fragments exist only as recursive targets; the diet aliases are
# referenced only by species/form cache keys.  Every remaining key must match
# one of the production query patterns below, which proves the derived root
# set is exactly the consumed set.
INTERNAL_FRAGMENT_KEYS = frozenset({
    "_baked_good_and_reaction_",
    "_fruit_and_reaction_",
    "_meat_and_reaction_",
    "sparkling_message",
})
DIET_ALIAS_KEYS = frozenset({
    "carnivore baked goods cache",
    "carnivore fruit cache",
    "inediate baked goods cache",
    "inediate fruit cache",
    "inediate meat cache",
    "short baked goods cache",
    "short fruit cache",
    "short meat cache",
    "stone baked goods cache",
    "stone fruit cache",
    "stone meat cache",
})
NON_CONSUMED_KEYS = INTERNAL_FRAGMENT_KEYS | DIET_ALIAS_KEYS

# External TextDB lookups resolved in the already-loaded MiscDB (colourname/
# graffiti sources of the same dump); these keys must be loaded.
EXTERNAL_TEXTDB_KEYS = frozenset({
    "any_colour",
    "any_colour_pattern",
    "any_graffiti",
})

# Replaced by directn.cc::_walk_on_decor after TextDB expansion.
POSTPROCESS_TOKENS = frozenset({
    "your_hands",
    "your_weapon",
})

# decorlines.txt defines "Jiyva peaceful fountain_blue" twice; DBM_REPLACE
# keeps the last definition while source_history records both.  This is the
# only overridden key in the scope.
OVERRIDDEN_KEYS = frozenset({"jiyva peaceful fountain_blue"})

# Production query shapes built by directn.cc::_walk_on_decor.
_FOUNTAIN_RE = re.compile(
    r"^(.+ )?(peaceful )?(fountain_blue|fountain_sparkling|"
    r"fountain_blood|fountain_eyes)$"
)
_DRY_FOUNTAIN_RE = re.compile(r"^(.+ )?(peaceful )?dry_fountain$")
_CACHE_RE = re.compile(r"^(.+ )?(fruit cache|meat cache|baked goods cache)$")
PRODUCTION_QUERY_PATTERNS = (_FOUNTAIN_RE, _DRY_FOUNTAIN_RE, _CACHE_RE)

# Frozen baseline constants that are filled in after the first exact-Git
# derivation; the inventory requires the derived facts to equal them.  The
# baseline ZH deliberately rewrites 57 variant bodies with a different token
# multiset (recorded in the scope as baseline_token_multiset_drift); there
# are no pure token-order differences (equal multiset, different order), so
# the ordered-exception gate stays empty and the strict candidate gate
# requires the review phase to align every drifted multiset.
EXPECTED_BASELINE_ORDERED_TOKEN_EXCEPTIONS: set[tuple[str, int]] = set()
EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT: set[tuple[str, int]] = {
    ("amphisbaena baked goods cache", 0),
    ("amphisbaena fruit cache", 0),
    ("amphisbaena meat cache", 0),
    ("bat baked goods cache", 0),
    ("bat fruit cache", 0),
    ("blade fruit cache", 1),
    ("blade meat cache", 1),
    ("death baked goods cache", 0),
    ("death fruit cache", 0),
    ("death meat cache", 0),
    ("default peaceful fountain_sparkling", 0),
    ("draconian fruit cache", 0),
    ("draconian fruit cache", 1),
    ("dragon fruit cache", 0),
    ("dragon fruit cache", 1),
    ("felid baked goods cache", 0),
    ("felid meat cache", 0),
    ("gargoyle baked goods cache", 0),
    ("gargoyle fruit cache", 0),
    ("gargoyle meat cache", 0),
    ("kobold baked goods cache", 0),
    ("kobold fruit cache", 0),
    ("kobold meat cache", 0),
    ("mummy baked goods cache", 0),
    ("mummy fruit cache", 0),
    ("mummy meat cache", 0),
    ("oni baked goods cache", 0),
    ("oni fruit cache", 0),
    ("pig baked goods cache", 0),
    ("pig fruit cache", 0),
    ("pig meat cache", 0),
    ("poltergeist baked goods cache", 0),
    ("poltergeist fruit cache", 0),
    ("poltergeist meat cache", 0),
    ("revenant baked goods cache", 0),
    ("revenant fruit cache", 0),
    ("revenant meat cache", 0),
    ("short baked goods cache", 0),
    ("short fruit cache", 0),
    ("short meat cache", 0),
    ("spriggan baked goods cache", 0),
    ("spriggan fruit cache", 0),
    ("statue baked goods cache", 0),
    ("statue fruit cache", 0),
    ("statue meat cache", 0),
    ("stone baked goods cache", 0),
    ("stone fruit cache", 0),
    ("stone meat cache", 0),
    ("storm fruit cache", 0),
    ("storm meat cache", 0),
    ("tengu baked goods cache", 0),
    ("tree baked goods cache", 0),
    ("tree fruit cache", 0),
    ("tree meat cache", 0),
    ("troll baked goods cache", 0),
    ("troll fruit cache", 0),
    ("vampire baked goods cache", 0),
}
EXPECTED_BASELINE_UNRESOLVED: dict[str, list[dict[str, Any]]] = {
    "english": [],
    "chinese": [],
}
EXPECTED_BASELINE_UNREACHABLE: dict[str, list[str]] = {
    "english": [],
    "chinese": [],
}

CONCLUSIONS = {
    "keep", "adjust", "retranslate", "defer implementation",
    "defer terminology",
}
DEFER_CONCLUSIONS = {"defer implementation", "defer terminology"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
METADATA_FIELDS = {
    "baseline", "chinese_production_dump_sha256", "en_variant_count",
    "english_production_dump_sha256", "glossary_sha256", "identity_count",
    "inventory_sha256", "terminal_conclusion_counts", "zh_variant_count",
}
CARD_FIELDS = {
    "confidence", "current_chinese_variants", "current_english_variants",
    "deferral_owner", "deferral_reason", "dependency_group",
    "display_context", "evidence_locations", "identity", "key", "lifecycle",
    "producer_consumer", "proposed_chinese_variants",
    "proposed_english_variants", "rationale", "reentry_trigger",
    "rejected_alternatives", "terminal_conclusion",
}
VARIANT_FIELDS = {"text", "weight"}

# Frozen consumer/producer evidence for the directn.cc::_walk_on_decor path.
FROZEN_PRODUCER_CONSUMER = {
    "loader": "crawl-ref/source/database.cc:143",
    "decor_consumer": "crawl-ref/source/directn.cc:3007",
    "possessive_context": 'C_("decor possessive", "your")',
}

InventoryError = hardened.InventoryError
_require = hardened._require
_sha256 = hardened._sha256
_canonical_json = hardened._canonical_json

_MISC_DB_RE = re.compile(
    r'\bTextDB\s*\(\s*"misc"\s*,\s*"database/"\s*,\s*\{(.*?)\}\s*\)',
    re.DOTALL,
)


def _group_for(key: str) -> str:
    if key in INTERNAL_FRAGMENT_KEYS:
        return "递归内部片段（食物反应/喷泉消息）"
    if key in DIET_ALIAS_KEYS:
        return "饮食别名片段（仅递归可达）"
    if key.endswith(" cache"):
        return "食物缓存消息"
    return "喷泉消息"


def _misc_source_manifest(oid: str, label: str) -> list[str]:
    """Parameterized copy of the hardened SpeakDB manifest reader, targeting
    the ``TextDB("misc", "database/", ...)`` initializer.  The original speak
    manifest parser in monflee_inventory stays untouched."""
    database = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/database.cc", label
        ),
        label,
    )
    matches = list(_MISC_DB_RE.finditer(database))
    _require(
        len(matches) == 1,
        f"{label} database.cc must have one literal MiscDB initializer",
    )
    body = matches[0].group(1)
    files: list[str] = []
    position = 0
    expect_value = True
    while True:
        while position < len(body):
            if body[position] in " \t\r\n\f\v":
                position += 1
            elif body.startswith("//", position):
                newline = body.find("\n", position + 2)
                position = len(body) if newline < 0 else newline + 1
            else:
                break
        if position == len(body):
            break
        if expect_value:
            _require(body[position] == '"',
                     f"{label} MiscDB initializer is not a literal list")
            end = body.find('"', position + 1)
            _require(end >= 0 and "\\" not in body[position + 1:end],
                     f"{label} MiscDB source literal is malformed")
            filename = body[position + 1:end]
            _require(bool(re.fullmatch(r"[A-Za-z0-9_]+\.txt", filename)),
                     f"{label} has unsafe MiscDB source {filename!r}")
            _require(filename not in files,
                     f"{label} has duplicate MiscDB source {filename!r}")
            files.append(filename)
            position = end + 1
            expect_value = False
        else:
            _require(body[position] == ',',
                     f"{label} MiscDB source literals must be comma separated")
            position += 1
            expect_value = True
    _require(bool(files), f"{label} MiscDB source manifest is empty")
    return [f"database/{filename}" for filename in files]


def _derive_scoped_misc_dump(
    oid: str, directory: str, label: str,
) -> dict[str, Any]:
    """Derive the decorlines-scoped dump from the exact Git baseline using the
    MiscDB input sequence (instead of the hardened SpeakDB sequence)."""
    manifest = (
        _misc_source_manifest(oid, label)
        if directory == "database/"
        else hardened.shared._localized_source_manifest(oid, label)
    )
    sources = [
        {
            "source_name": source_name,
            "load_index": load_index,
            "normalized_utf8": hardened.shared._source_snapshot_at_oid(
                oid, source_name, f"{label} {source_name}"
            ),
        }
        for load_index, source_name in enumerate(manifest)
    ]
    return hardened.shared._derive_scoped_from_sources(
        sources, directory, label, source_basename=SOURCE_BASENAME
    )


def _require_regular_misc_git_sources(
    ref: str, directory: str, label: str,
) -> None:
    """Bind the MiscDB derivation inputs to regular blobs at the exact OID."""
    if directory == "database/":
        manifest = _misc_source_manifest(ref, label)
    else:
        manifest = hardened.shared._localized_source_manifest(ref, label)
    hardened._require_regular_git_blobs(
        ref,
        ["crawl-ref/source/database.cc"]
        + [f"crawl-ref/source/dat/{name}" for name in manifest],
        label,
    )


def _definition_lines(source: str, label: str) -> dict[str, int]:
    """Source line of the first definition of every canonical decorlines key.

    decorlines.txt legally defines "Jiyva peaceful fountain_blue" twice, so
    unlike the wpnnoise helper the first occurrence wins and the duplicate
    is not an error (the override fact is frozen separately)."""
    try:
        definitions = hardened.shared.parse_db_keys(source, SOURCE_BASENAME)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
    lines: dict[str, int] = {}
    for definition in definitions:
        canonical = hardened.shared.lowercase_string(definition.raw_key)
        if canonical not in lines:
            lines[canonical] = definition.key_line
    return lines


def _read_glossary(path: Path, ref: str | None) -> bytes:
    if ref is None:
        return hardened._read_artifact_bytes(path, "glossary")
    return hardened._candidate_regular_blob(
        ref, hardened._repo_relative_git_path(path, "glossary"), "glossary"
    )


def _source_rows(artifact: dict[str, Any], directory: str, label: str) -> list[dict[str, Any]]:
    source_name = f"{directory}{SOURCE_BASENAME}"
    rows = [
        entry for entry in artifact["entries"]
        if any(item["source_name"] == source_name
               for item in entry["source_history"])
    ]
    _require(len(rows) == EXPECTED_IDENTITY_COUNT,
             f"{label} decorlines identity count mismatch")
    keys = [entry["canonical_key"] for entry in rows]
    _require(len(set(keys)) == len(keys), f"{label} duplicate decorlines key")
    overridden = {
        entry["canonical_key"] for entry in rows
        if len(entry["source_history"]) != 1
    }
    _require(overridden == OVERRIDDEN_KEYS,
             f"{label} overridden decorlines keys differ: "
             f"{sorted(overridden)!r}")
    for entry in rows:
        _require(entry["parse_error"] is None,
                 f"{label} parse error at {entry['canonical_key']!r}")
        _require(not entry["body_empty"],
                 f"{label} empty body at {entry['canonical_key']!r}")
        _require(entry["effective_provenance"]["source_name"] == source_name,
                 f"{label} key {entry['canonical_key']!r} is not effective "
                 f"from {SOURCE_BASENAME}")
    return sorted(rows, key=lambda entry: entry["canonical_key"])


def _variant(raw: dict[str, Any]) -> dict[str, Any]:
    text = raw["raw_pattern"]
    return {
        "variant_ordinal": raw["locator"]["variant_ordinal"],
        "weight": raw["weight"],
        "text": text,
        "runtime_tokens": hardened._runtime_tokens(text),
        "random_site_counts": hardened._random_site_counts(text),
        "lua_site_count": len(hardened._lua_sites(text)),
    }


def _classify_tokens(
    rows: list[dict[str, Any]], all_effective_keys: set[str],
) -> dict[str, Any]:
    key_set = {row["canonical_key"].lower() for row in rows}
    recursive: dict[str, list[dict[str, Any]]] = {key: [] for key in key_set}
    fragment_sites: list[dict[str, Any]] = []
    external_sites: list[dict[str, Any]] = []
    postprocess_sites: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    edges: dict[str, set[str]] = {key: set() for key in key_set}
    for row in rows:
        source = row["canonical_key"].lower()
        for raw in row["variants"]:
            ordinal = raw["locator"]["variant_ordinal"]
            for token in hardened._runtime_tokens(raw["raw_pattern"]):
                canonical = token[1:-1].lower()
                site = {"key": source, "variant_ordinal": ordinal,
                        "token": token}
                if canonical in key_set:
                    edges[source].add(canonical)
                    recursive[canonical].append(site)
                    if canonical in INTERNAL_FRAGMENT_KEYS:
                        fragment_sites.append(site)
                elif canonical in EXTERNAL_TEXTDB_KEYS:
                    _require(canonical in all_effective_keys,
                             f"external TextDB dependency {token!r} is not loaded")
                    external_sites.append(site)
                elif canonical in POSTPROCESS_TOKENS:
                    postprocess_sites.append(site)
                else:
                    unresolved.append(site)
    _require(
        {site["token"][1:-1].lower() for site in fragment_sites}
        == INTERNAL_FRAGMENT_KEYS,
        "frozen internal fragment token set differs from the four "
        "decorlines fragments",
    )
    return {
        "edges": {key: sorted(value) for key, value in sorted(edges.items())},
        "references": {
            key: sorted(value,
                        key=lambda item: (item["key"], item["variant_ordinal"],
                                          item["token"]))
            for key, value in sorted(recursive.items())
        },
        "fragment_sites": sorted(
            fragment_sites,
            key=lambda item: (item["key"], item["variant_ordinal"], item["token"]),
        ),
        "external_sites": sorted(
            external_sites,
            key=lambda item: (item["key"], item["variant_ordinal"], item["token"]),
        ),
        "postprocess_sites": sorted(
            postprocess_sites,
            key=lambda item: (item["key"], item["variant_ordinal"], item["token"]),
        ),
        "unresolved": sorted(
            unresolved,
            key=lambda item: (item["key"], item["variant_ordinal"], item["token"]),
        ),
    }


def _reachability(
    edges: dict[str, list[str]], root_keys: set[str],
) -> dict[str, Any]:
    reached = set(root_keys)
    queue: deque[tuple[str, tuple[str, ...]]] = deque(
        (key, (key,)) for key in sorted(root_keys)
    )
    witnesses: dict[str, list[str]] = {}
    while queue:
        source, path = queue.popleft()
        for target in sorted(edges[source]):
            if target in reached:
                continue
            reached.add(target)
            next_path = (*path, target)
            witnesses[target] = list(next_path)
            queue.append((target, next_path))
    missing = sorted(set(edges) - reached)
    return {
        "reachable": sorted(reached),
        "unreachable": missing,
        "witnesses": {key: witnesses[key] for key in sorted(witnesses)},
    }


def _dataset(
    artifact: dict[str, Any], raw: bytes, directory: str, label: str,
    role: str,
) -> dict[str, Any]:
    rows = _source_rows(artifact, directory, label)
    all_keys = {entry["canonical_key"].lower()
                for entry in artifact["entries"]}
    scoped_keys = {row["canonical_key"].lower() for row in rows}
    _require(NON_CONSUMED_KEYS <= scoped_keys,
             f"{label} frozen non-consumed decorlines keys are missing")
    root_keys = scoped_keys - NON_CONSUMED_KEYS
    _require(
        len(root_keys) == EXPECTED_IDENTITY_COUNT - len(NON_CONSUMED_KEYS),
        f"{label} derived root key count mismatch",
    )
    for key in sorted(root_keys):
        _require(
            any(pattern.fullmatch(key) for pattern in PRODUCTION_QUERY_PATTERNS),
            f"{label} root key {key!r} matches no production query pattern",
        )
    token_facts = _classify_tokens(rows, all_keys)
    reachability = _reachability(token_facts["edges"], root_keys)
    _require(not reachability["unreachable"],
             f"{label} has unreachable decorlines keys: "
             f"{reachability['unreachable']!r}")
    source_snapshot = next(
        source for source in artifact["sources"]
        if source["source_name"] == f"{directory}{SOURCE_BASENAME}"
    )
    lines = _definition_lines(source_snapshot["normalized_utf8"], label)
    entries = []
    for row in rows:
        key = row["canonical_key"]
        entries.append({
            "key": key,
            "definition_ordinal": row["effective_provenance"]["definition_ordinal"],
            "source_line": lines[key],
            "source_history_length": len(row["source_history"]),
            "variants": [_variant(variant) for variant in row["variants"]],
        })
    total = sum(len(entry["variants"]) for entry in entries)
    random_sites = sum(
        len(variant["random_site_counts"])
        for entry in entries for variant in entry["variants"]
    )
    lua_sites = sum(
        variant["lua_site_count"]
        for entry in entries for variant in entry["variants"]
    )
    if role == "baseline":
        expected_variants = (
            EXPECTED_BASELINE_EN_VARIANTS if directory == "database/"
            else EXPECTED_BASELINE_ZH_VARIANTS
        )
        _require(total == expected_variants,
                 f"{label} baseline variant count mismatch")
        expected_random = (
            EXPECTED_EN_RANDOM_SITES if directory == "database/"
            else EXPECTED_ZH_RANDOM_SITES
        )
        _require(random_sites == expected_random,
                 f"{label} baseline random-site count mismatch")
        expected_lua = (
            EXPECTED_EN_LUA_SITES if directory == "database/"
            else EXPECTED_ZH_LUA_SITES
        )
        _require(lua_sites == expected_lua,
                 f"{label} baseline Lua-site count mismatch")
    return {
        "artifact_sha256": _sha256(raw),
        "source_name": f"{directory}{SOURCE_BASENAME}",
        "source_sha256": _sha256(
            source_snapshot["normalized_utf8"].encode("utf-8")
        ),
        "entries": entries,
        "token_facts": token_facts,
        "reachability": reachability,
        "variant_count": total,
        "random_site_count": random_sites,
        "lua_site_count": lua_sites,
        "root_key_count": len(root_keys),
    }


def _load_dataset(
    ref: str, path: Path, directory: str, label: str, role: str,
) -> dict[str, Any]:
    hardened.shared._validate_oid(ref, label)
    _require_regular_misc_git_sources(ref, directory, label)
    artifact, raw = hardened._load_dump_safe(
        path, label, directory, expected_database="misc"
    )
    derived = _derive_scoped_misc_dump(ref, directory, label)
    hardened.shared._require_scoped_derivation(
        artifact, derived, label, source_basename=SOURCE_BASENAME
    )
    return _dataset(artifact, raw, directory, label, role)


def _pair_entries(
    en: dict[str, Any], zh: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(en_by_key.keys() == zh_by_key.keys(),
             "decorlines EN/ZH key sets differ")
    entries = []
    asymmetry: dict[str, list[int]] = {}
    for key in sorted(en_by_key):
        en_entry, zh_entry = en_by_key[key], zh_by_key[key]
        counts = (len(en_entry["variants"]), len(zh_entry["variants"]))
        if counts[0] != counts[1]:
            asymmetry[key] = list(counts)
        lifecycle = ("direct-production-root"
                     if key not in NON_CONSUMED_KEYS
                     else "recursive-internal-fragment")
        entries.append({
            "identity": f"decorlines:{key}",
            "key": key,
            "lifecycle": lifecycle,
            "dependency_group": _group_for(key),
            "english_definition_ordinal": en_entry["definition_ordinal"],
            "chinese_definition_ordinal": zh_entry["definition_ordinal"],
            "english_source_line": en_entry["source_line"],
            "chinese_source_line": zh_entry["source_line"],
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
            "english_referencing_sites": en["token_facts"]["references"][key],
            "chinese_referencing_sites": zh["token_facts"]["references"][key],
        })
    _require(len(asymmetry) == EXPECTED_ASYMMETRY_COUNT,
             f"baseline asymmetric key count mismatch: {len(asymmetry)}")
    multiset_drift: set[tuple[str, int]] = set()
    for entry in entries:
        key = entry["key"]
        for ordinal, (en_variant, zh_variant) in enumerate(
            zip(entry["english_variants"], entry["chinese_variants"])
        ):
            if (Counter(en_variant["runtime_tokens"])
                    != Counter(zh_variant["runtime_tokens"])):
                multiset_drift.add((key, ordinal))
    _require(multiset_drift == EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT,
             "baseline token-multiset drift facts changed")
    return entries, asymmetry


def build_inventory(
    baseline_ref: str, english_path: Path, localized_path: Path,
    glossary_path: Path, glossary_ref: str | None = None,
) -> dict[str, Any]:
    en = _load_dataset(baseline_ref, english_path, "database/",
                       "baseline EN", "baseline")
    zh = _load_dataset(baseline_ref, localized_path, "database/zh/",
                       "baseline ZH", "baseline")
    _require(en["token_facts"]["unresolved"]
             == EXPECTED_BASELINE_UNRESOLVED["english"],
             "baseline EN unresolved-token facts changed")
    _require(zh["token_facts"]["unresolved"]
             == EXPECTED_BASELINE_UNRESOLVED["chinese"],
             "baseline ZH unresolved-token facts changed")
    _require(en["reachability"]["unreachable"]
             == EXPECTED_BASELINE_UNREACHABLE["english"],
             "baseline EN reachability facts changed")
    _require(zh["reachability"]["unreachable"]
             == EXPECTED_BASELINE_UNREACHABLE["chinese"],
             "baseline ZH reachability facts changed")
    entries, asymmetry = _pair_entries(en, zh)
    scope = {
        "source_basename": SOURCE_BASENAME,
        "expected_identity_count": EXPECTED_IDENTITY_COUNT,
        "root_key_count": en["root_key_count"],
        "root_keys": sorted({entry["key"] for entry in entries
                             if entry["lifecycle"]
                             == "direct-production-root"}),
        "internal_fragment_keys": sorted(INTERNAL_FRAGMENT_KEYS),
        "diet_alias_keys": sorted(DIET_ALIAS_KEYS),
        "overridden_keys": sorted(OVERRIDDEN_KEYS),
        "external_textdb_keys": sorted(EXTERNAL_TEXTDB_KEYS),
        "postprocess_tokens": sorted(POSTPROCESS_TOKENS),
        "baseline_variant_counts": {
            "english": EXPECTED_BASELINE_EN_VARIANTS,
            "chinese": EXPECTED_BASELINE_ZH_VARIANTS,
        },
        "baseline_asymmetry": {
            key: asymmetry[key] for key in sorted(asymmetry)
        },
        "baseline_token_multiset_drift": [
            [key, ordinal]
            for key, ordinal in sorted(EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT)
        ],
        "baseline_random_sites": {
            "english": en["random_site_count"],
            "chinese": zh["random_site_count"],
        },
        "baseline_lua_sites": {
            "english": en["lua_site_count"],
            "chinese": zh["lua_site_count"],
        },
    }
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": scope,
        "scope_sha256": _sha256(_canonical_json(scope)),
        "glossary": {
            "path": "docs/glossary.md",
            "sha256": _sha256(_read_glossary(glossary_path, glossary_ref)),
        },
        "dumps": {
            "english": {key: value for key, value in en.items()
                        if key != "entries"},
            "localized": {key: value for key, value in zh.items()
                          if key != "entries"},
        },
        "entries": entries,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _strict_block_from_text(text: str) -> list[dict[str, Any]]:
    _require(text.count(STRICT_BEGIN) == 1,
             "review results require exactly one strict begin marker")
    _require(text.count(STRICT_END) == 1,
             "review results require exactly one strict end marker")
    body = text.split(STRICT_BEGIN, 1)[1].split(STRICT_END, 1)[0].strip()
    match = re.fullmatch(r"```jsonl\s*\n(.*?)\n```", body, re.DOTALL)
    _require(match is not None,
             "strict review evidence must be one fenced jsonl block")
    records = []
    for number, line in enumerate(match.group(1).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InventoryError(
                f"invalid review JSONL line {number}: {exc}") from exc
        _require(isinstance(value, dict),
                 f"review JSONL line {number} must be an object")
        records.append(value)
    return records


def _strict_block(path: Path) -> list[dict[str, Any]]:
    raw = hardened._read_artifact_bytes(path, "review results")
    try:
        return _strict_block_from_text(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise InventoryError("cannot decode review results") from exc


def _variant_review_shape(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"weight": variant["weight"], "text": variant["text"]}
            for variant in variants]


def _validate_variant_list(value: Any, context: str) -> None:
    _require(isinstance(value, list), f"{context} must be a list")
    for ordinal, variant in enumerate(value):
        _require(isinstance(variant, dict) and set(variant) == VARIANT_FIELDS,
                 f"{context} ordinal {ordinal} fields mismatch")
        _require(isinstance(variant["weight"], int)
                 and not isinstance(variant["weight"], bool)
                 and variant["weight"] > 0,
                 f"{context} ordinal {ordinal} weight mismatch")
        _require(isinstance(variant["text"], str) and bool(variant["text"]),
                 f"{context} ordinal {ordinal} text mismatch")
        hardened._random_site_counts(variant["text"])
        # Lua blocks are legitimate decorlines content; this call fails
        # closed on unbalanced markers instead of rejecting them.
        hardened._lua_sites(variant["text"])


def _expected_metadata(
    inventory: dict[str, Any], cards: list[dict[str, Any]],
) -> dict[str, Any]:
    conclusions = [
        card["terminal_conclusion"] for card in cards
        if card["terminal_conclusion"] is not None
    ]
    return {
        "baseline": inventory["baseline_ref"],
        "chinese_production_dump_sha256":
            inventory["dumps"]["localized"]["artifact_sha256"],
        "en_variant_count": EXPECTED_BASELINE_EN_VARIANTS,
        "english_production_dump_sha256":
            inventory["dumps"]["english"]["artifact_sha256"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": EXPECTED_IDENTITY_COUNT,
        "inventory_sha256": inventory["inventory_sha256"],
        "terminal_conclusion_counts": dict(sorted(Counter(conclusions).items())),
        "zh_variant_count": EXPECTED_BASELINE_ZH_VARIANTS,
    }


def validate_results(
    path: Path, inventory: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    records = records if records is not None else _strict_block(path)
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review results require one metadata record and 132 cards")
    metadata, cards = records[0], records[1:]
    _require(set(metadata) == METADATA_FIELDS, "review metadata fields mismatch")
    _require(metadata == _expected_metadata(inventory, cards),
             "review metadata mismatch")
    by_identity = {entry["identity"]: entry for entry in inventory["entries"]}
    _require(len({card.get("identity") for card in cards}) == len(cards),
             "duplicate review identity")
    _require([card.get("identity") for card in cards] == sorted(by_identity),
             "review cards must cover every identity in deterministic order")
    proposals: dict[str, dict[str, Any]] = {}
    for card in cards:
        identity = card["identity"]
        entry = by_identity[identity]
        _require(set(card) == CARD_FIELDS, f"review card {identity} fields mismatch")
        _require(card["key"] == entry["key"], f"review card {identity} key mismatch")
        _require(card["lifecycle"] == entry["lifecycle"],
                 f"review card {identity} lifecycle mismatch")
        _require(card["dependency_group"] == entry["dependency_group"],
                 f"review card {identity} group mismatch")
        current_en = _variant_review_shape(entry["english_variants"])
        current_zh = _variant_review_shape(entry["chinese_variants"])
        _require(card["current_english_variants"] == current_en,
                 f"review card {identity} current EN mismatch")
        _require(card["current_chinese_variants"] == current_zh,
                 f"review card {identity} current ZH mismatch")
        _validate_variant_list(card["proposed_english_variants"],
                               f"review card {identity} proposed EN")
        _validate_variant_list(card["proposed_chinese_variants"],
                               f"review card {identity} proposed ZH")
        conclusion = card["terminal_conclusion"]
        _require(conclusion in CONCLUSIONS,
                 f"review card {identity} conclusion mismatch")
        changed = (card["proposed_english_variants"] != current_en
                   or card["proposed_chinese_variants"] != current_zh)
        _require(changed == (conclusion in {"adjust", "retranslate"}),
                 f"review card {identity} conclusion/change mismatch")
        for field in ("rationale", "display_context", "reentry_trigger"):
            _require(isinstance(card[field], str) and bool(card[field].strip()),
                     f"review card {identity} requires {field}")
        _require(card["confidence"] in CONFIDENCE_LEVELS,
                 f"review card {identity} confidence mismatch")
        _require(isinstance(card["evidence_locations"], list)
                 and card["evidence_locations"],
                 f"review card {identity} requires evidence locations")
        _require(isinstance(card["rejected_alternatives"], list)
                 and card["rejected_alternatives"],
                 f"review card {identity} requires rejected alternatives")
        _require(isinstance(card["producer_consumer"], dict)
                 and card["producer_consumer"],
                 f"review card {identity} requires producer/consumer evidence")
        if conclusion in DEFER_CONCLUSIONS:
            _require(isinstance(card["deferral_owner"], str)
                     and card["deferral_owner"].strip(),
                     f"review card {identity} deferred conclusion requires owner")
            _require(isinstance(card["deferral_reason"], str)
                     and card["deferral_reason"].strip(),
                     f"review card {identity} deferred conclusion requires reason")
        else:
            _require(card["deferral_owner"] is None
                     and card["deferral_reason"] is None,
                     f"review card {identity} non-deferred conclusion "
                     f"forbids deferral fields")
        proposals[entry["key"]] = {
            "english": card["proposed_english_variants"],
            "chinese": card["proposed_chinese_variants"],
        }
    if candidate is not None:
        candidate_by_key = {entry["key"]: entry for entry in candidate["entries"]}
        _require(candidate_by_key.keys() == proposals.keys(),
                 "candidate key set differs from review ledger")
        for key in sorted(proposals):
            actual = candidate_by_key[key]
            _require(_variant_review_shape(actual["english_variants"])
                     == proposals[key]["english"],
                     f"candidate EN drift at {key!r}")
            _require(_variant_review_shape(actual["chinese_variants"])
                     == proposals[key]["chinese"],
                     f"candidate ZH drift at {key!r}")
    return {"metadata": metadata, "cards": cards}


def _pair_candidate(en: dict[str, Any], zh: dict[str, Any]) -> list[dict[str, Any]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(en_by_key.keys() == zh_by_key.keys(),
             "candidate EN/ZH key sets differ")
    entries = []
    ordered_differences: set[tuple[str, int]] = set()
    for key in sorted(en_by_key):
        en_entry, zh_entry = en_by_key[key], zh_by_key[key]
        _require(len(en_entry["variants"]) == len(zh_entry["variants"]),
                 f"candidate variant count differs at {key!r}")
        _require([v["weight"] for v in en_entry["variants"]]
                 == [v["weight"] for v in zh_entry["variants"]],
                 f"candidate weight order differs at {key!r}")
        for ordinal, (en_variant, zh_variant) in enumerate(
            zip(en_entry["variants"], zh_entry["variants"])
        ):
            _require(
                Counter(en_variant["runtime_tokens"])
                == Counter(zh_variant["runtime_tokens"]),
                f"candidate recursive/postprocess token multiset differs at "
                f"{key!r} ordinal {ordinal}",
            )
            if en_variant["runtime_tokens"] != zh_variant["runtime_tokens"]:
                ordered_differences.add((key, ordinal))
            _require(
                en_variant["random_site_counts"]
                == zh_variant["random_site_counts"],
                f"candidate random-site topology differs at {key!r} ordinal "
                f"{ordinal}",
            )
            _require(
                en_variant["lua_site_count"] == zh_variant["lua_site_count"],
                f"candidate Lua-site count differs at {key!r} ordinal "
                f"{ordinal}",
            )
        entries.append({
            "identity": f"decorlines:{key}", "key": key,
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
        })
    expected_ordered_differences = {
        locator for locator in EXPECTED_BASELINE_ORDERED_TOKEN_EXCEPTIONS
        if locator[0] in en_by_key
    }
    _require(
        ordered_differences == expected_ordered_differences,
        "candidate ordered-token grammar exceptions differ: "
        f"{sorted(ordered_differences)!r}",
    )
    return entries


def add_candidate(
    inventory: dict[str, Any], baseline_ref: str, candidate_ref: str,
    english_path: Path, localized_path: Path,
) -> dict[str, Any]:
    hardened.shared._require_candidate_commit(
        baseline_ref, candidate_ref, exact_clean_checkout=True
    )
    en = _load_dataset(candidate_ref, english_path, "database/",
                       "candidate EN", "candidate")
    zh = _load_dataset(candidate_ref, localized_path, "database/zh/",
                       "candidate ZH", "candidate")
    _require(not en["token_facts"]["unresolved"],
             "candidate EN contains unresolved token")
    _require(not zh["token_facts"]["unresolved"],
             "candidate ZH contains unresolved token")
    _require(not en["reachability"]["unreachable"],
             "candidate EN has unreachable decorlines keys")
    _require(not zh["reachability"]["unreachable"],
             "candidate ZH has unreachable decorlines keys")
    entries = _pair_candidate(en, zh)
    candidate = {
        "candidate_ref": candidate_ref,
        "dumps": {
            "english": {key: value for key, value in en.items()
                        if key != "entries"},
            "localized": {key: value for key, value in zh.items()
                          if key != "entries"},
        },
        "entries": entries,
    }
    candidate["candidate_sha256"] = _sha256(_canonical_json(candidate))
    inventory["candidate"] = candidate
    return candidate


def _proposal_dataset(
    path: Path, directory: str, label: str,
) -> dict[str, Any]:
    """Load a mutable production dump for scaffolding only.

    This is never final evidence.  It must nevertheless match the current
    worktree source byte-for-byte after newline normalization; the exact
    candidate audit later re-derives the same data from the committed Git
    object and rejects any mismatch."""
    artifact, raw = hardened._load_dump_safe(
        path, label, directory, expected_database="misc"
    )
    source_name = f"{directory}{SOURCE_BASENAME}"
    snapshot = next(
        source for source in artifact["sources"]
        if source["source_name"] == source_name
    )
    source_path = (Path(__file__).resolve().parents[2]
                   / "crawl-ref/source/dat" / source_name)
    current = hardened._read_artifact_bytes(source_path,
                                            f"{label} worktree source")
    try:
        normalized = (current.decode("utf-8")
                      .replace("\r\n", "\n").replace("\r", "\n"))
    except UnicodeDecodeError as exc:
        raise InventoryError(f"cannot decode {label} worktree source") from exc
    _require(snapshot["normalized_utf8"] == normalized,
             f"{label} dump does not match the current worktree source")
    dataset = _dataset(artifact, raw, directory, label, "candidate")
    _require(not dataset["token_facts"]["unresolved"],
             f"{label} proposal contains unresolved token")
    _require(not dataset["reachability"]["unreachable"],
             f"{label} proposal has unreachable decorlines keys")
    return dataset


def _skeleton_card(
    inventory: dict[str, Any], entry: dict[str, Any],
) -> dict[str, Any]:
    """One empty ledger card bound to the frozen baseline facts.

    The zh-translator phase fills proposed_* variants, terminal_conclusion,
    confidence, rationale and reentry_trigger; the schema is shared with the
    final strict review ledger so the completed file validates unchanged."""
    current_en = _variant_review_shape(entry["english_variants"])
    current_zh = _variant_review_shape(entry["chinese_variants"])
    lifecycle = entry["lifecycle"]
    if lifecycle == "direct-production-root":
        display_context = (
            "directn.cc::_walk_on_decor 直接查询的根键；展开后经 "
            "maybe_pick_random_substring、@your_weapon@/@your_hands@ 与 "
            "do_mon_name_replacements 处理，以 MSGCH_DECOR_FLAVOUR 显示。"
        )
    else:
        display_context = (
            "仅由 decorlines 根键闭包递归展开的内部片段；不能脱离调用点"
            "独立解释。"
        )
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": lifecycle,
        "dependency_group": entry["dependency_group"],
        "display_context": display_context,
        "producer_consumer": dict(FROZEN_PRODUCER_CONSUMER),
        "evidence_locations": [
            f"crawl-ref/source/dat/database/decorlines.txt:"
            f"{entry['english_source_line']}",
            f"crawl-ref/source/dat/database/zh/decorlines.txt:"
            f"{entry['chinese_source_line']}",
            *(f"recursive-ref:{site['key']}:{site['variant_ordinal']}"
              for site in entry["english_referencing_sites"]),
            *(f"recursive-ref-zh:{site['key']}:{site['variant_ordinal']}"
              for site in entry["chinese_referencing_sites"]),
        ],
        "current_english_variants": current_en,
        "current_chinese_variants": current_zh,
        "proposed_english_variants": None,
        "proposed_chinese_variants": None,
        "terminal_conclusion": None,
        "confidence": None,
        "rationale": "",
        "rejected_alternatives": [],
        "reentry_trigger": "",
        "deferral_owner": None,
        "deferral_reason": None,
    }


def _same_directory_identity(fd_a: int, fd_b: int) -> bool:
    """True when both descriptors refer to the same directory inode."""
    info_a = os.fstat(fd_a)
    info_b = os.fstat(fd_b)
    return (info_a.st_dev, info_a.st_ino) == (info_b.st_dev, info_b.st_ino)


def _require_pinned_chain(
    absolute: str, components: list[str], pinned: list[int],
) -> None:
    """Require the approved absolute pathname to still resolve to the pinned
    descriptor chain, re-walking from the filesystem root with O_NOFOLLOW.

    Every component must open without following a symlink and must match the
    pinned descriptor's (st_dev, st_ino) identity.  A symlink, a missing
    component, a non-directory or a renamed/replaced directory raises
    InventoryError, so a concurrent path replacement is detected both before
    and after the exclusive create."""
    probe: list[int] = []
    try:
        try:
            probe.append(os.open(
                os.sep, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            ))
        except OSError as exc:
            raise InventoryError(
                f"scaffold chain verification cannot pin the filesystem root "
                f"for {absolute}: {exc}"
            ) from exc
        _require(_same_directory_identity(probe[0], pinned[0]),
                 f"scaffold filesystem root of {absolute} changed identity "
                 f"during creation; refusing to write")
        for index, component in enumerate(components[:-1]):
            try:
                probe.append(os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=probe[-1],
                ))
            except OSError as exc:
                raise InventoryError(
                    f"scaffold parent component {component!r} of {absolute} "
                    f"cannot be re-opened without following a symlink: {exc}"
                ) from exc
            _require(
                _same_directory_identity(probe[-1], pinned[index + 1]),
                f"scaffold parent component {component!r} of {absolute} "
                f"changed identity during creation; refusing to write",
            )
    finally:
        for fd in probe:
            os.close(fd)


def _rollback_created_file(
    file_fd: int, parent_fd: int, basename: str,
) -> None:
    """Roll back an exclusively created file in the canonical order.

    Every failure path after a successful O_EXCL create must remove the
    created file in exactly this order:

    1. close the file descriptor, so the inode is unlinked cleanly and no
       descriptor outlives the failed transaction;
    2. unlink the exact basename through the pinned parent descriptor, so a
       renamed or replaced parent can never trap the file outside the
       approved location;
    3. fsync the pinned parent descriptor after the unlink, so the removal
       is durable and a crash cannot resurrect a stale partial ledger.

    Each step is best-effort: an OSError is swallowed and the remaining
    steps still run.  The caller always re-raises the original error and
    must not close ``file_fd`` again after this helper returns (the caller
    should invalidate it, e.g. reset it to -1, before the outer finally
    runs).
    """
    try:
        os.close(file_fd)
    except OSError:
        pass
    try:
        os.unlink(basename, dir_fd=parent_fd)
    except OSError:
        pass
    try:
        os.fsync(parent_fd)
    except OSError:
        pass


def _openat_exclusive_create(path: Path) -> tuple[int, int, str]:
    """Exclusively create one regular file through a fully pinned openat
    chain and return ``(file_fd, parent_dir_fd, basename)``.

    The supplied pathname is decomposed lexically (``os.path.abspath``
    normalizes ``.``/``..`` without resolving symlinks) and every ancestor
    component is opened with ``O_RDONLY|O_DIRECTORY|O_NOFOLLOW`` relative
    to the previously pinned descriptor, starting from the filesystem
    root.  All ancestor descriptors stay open for the whole operation, so
    a concurrent path replacement cannot redirect the write: the final
    element is created with ``O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW`` against
    the pinned parent descriptor, which means an existing ledger (regular
    file, hardlink or symlink) is rejected with EEXIST/ELOOP and never
    followed, truncated or overwritten.

    Identity is verified twice against the approved pathname, immediately
    before the exclusive create and immediately after it: the pathname is
    re-walked from the pinned root without following symlinks and every
    component must resolve to the same ``(st_dev, st_ino)`` identity as the
    pinned descriptor.  A symlink anywhere in the chain fails closed (ELOOP
    or ENOTDIR depending on platform/component type), a missing component
    fails with ENOENT (directories are never auto-created), and a
    non-directory fails with ENOTDIR.  If the post-create verification
    fails, the created file is rolled back with the same canonical cleanup
    order as a publish failure (close file, unlink through the pinned
    parent, fsync the parent; see _rollback_created_file) and the operation
    fails closed, so a renamed or replaced parent can never trap the ledger
    outside the approved location.

    The caller owns both returned descriptors and must fsync the file
    content and then the containing directory before closing them.  The
    returned basename is the exact final pathname component created
    through the pinned parent; if publishing fails after the exclusive
    create, the caller must remove it with
    ``os.unlink(basename, dir_fd=parent_dir_fd)`` and fsync the parent
    again, so a retry never trips EEXIST on a stale partial file."""
    absolute = os.path.abspath(os.fspath(path))
    if not absolute.startswith(os.sep):
        raise InventoryError(
            f"scaffold path must be an absolute POSIX pathname: {path}"
        )
    components = [component for component in absolute.split(os.sep)
                  if component not in ("", ".")]
    pinned: list[int] = []
    file_fd = -1
    retained_file = False
    retained_parent = False
    try:
        try:
            pinned.append(os.open(
                os.sep, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            ))
        except OSError as exc:
            raise InventoryError(
                f"cannot pin the filesystem root for scaffold {absolute}: {exc}"
            ) from exc
        for component in components[:-1]:
            try:
                pinned.append(os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=pinned[-1],
                ))
            except OSError as exc:
                raise InventoryError(
                    f"scaffold parent component {component!r} of {absolute} "
                    f"cannot be opened without following a symlink: {exc}"
                ) from exc
        parent_fd = pinned[-1]
        _require_pinned_chain(absolute, components, pinned)
        try:
            file_fd = os.open(
                components[-1],
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent_fd,
            )
        except OSError as exc:
            raise InventoryError(
                f"cannot exclusively create scaffold {absolute}: {exc}"
            ) from exc
        try:
            _require_pinned_chain(absolute, components, pinned)
        except InventoryError:
            # Post-create identity verification failed: the file was already
            # created through the pinned parent, so it must be rolled back
            # with the exact same cleanup order as a publish failure in
            # scaffold_results (close file, unlink through the pinned
            # parent, fsync the parent).  The helper closes file_fd; reset
            # it so the outer finally cannot close it twice.
            _rollback_created_file(file_fd, parent_fd, components[-1])
            file_fd = -1
            raise
        retained_file = True
        retained_parent = True
        return file_fd, parent_fd, components[-1]
    finally:
        if file_fd >= 0 and not retained_file:
            os.close(file_fd)
        if retained_parent:
            for fd in pinned[:-1]:
                os.close(fd)
        else:
            for fd in pinned:
                os.close(fd)


def scaffold_results(
    path: Path, inventory: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate the initial empty strict JSONL ledger (exclusive create).

    Fails closed when the ledger already exists, so an existing review ledger
    can never be overwritten or reopened, and when any pathname component
    (parent directories included) is a symlink, so a path replacement cannot
    redirect the write outside the pinned ledger location."""
    cards = [_skeleton_card(inventory, entry)
             for entry in inventory["entries"]]
    records = [_expected_metadata(inventory, cards), *cards]
    text = (
        "# Decorlines 全量审核结果（Issue #67）\n\n"
        "本文件的严格 JSONL 块是 132 个 frozen identity 的完整审核账本。"
        "每张卡绑定基线 EN/ZH 变体；zh-translator 阶段填写提案、结论与"
        "理由后，候选审计只接受逐字等于提案的提交。\n\n"
        f"{STRICT_BEGIN}\n```jsonl\n"
        + "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True)
                    for record in records)
        + f"\n```\n{STRICT_END}\n"
    )
    resolved = path.resolve(strict=False)
    _require(resolved == RESULTS_PATH.resolve(strict=False),
             f"scaffold output must be {RESULTS_PATH}")
    fd, parent_fd, basename = _openat_exclusive_create(path)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent_fd)
    except BaseException:
        # Publish transaction: any failure after the O_EXCL create (fdopen,
        # write, flush, file fsync or directory fsync) must roll back the
        # already-created ledger, or a retry fails with EEXIST on a stale
        # partial file.  The canonical cleanup order (close file, unlink
        # through the pinned parent, fsync the parent) is shared with the
        # post-create verification failure inside _openat_exclusive_create;
        # cleanup is best-effort and the original exception is re-raised.
        _rollback_created_file(fd, parent_fd, basename)
        raise
    finally:
        os.close(parent_fd)
    return records


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--english-dump", required=True, type=Path)
    parser.add_argument("--localized-dump", required=True, type=Path)
    parser.add_argument("--inventory-output", required=True, type=Path)
    parser.add_argument("--review-results", type=Path)
    parser.add_argument("--candidate-ref")
    parser.add_argument("--candidate-english-dump", type=Path)
    parser.add_argument("--candidate-localized-dump", type=Path)
    parser.add_argument("--scaffold-output", type=Path)
    parser.add_argument(
        "--glossary", type=Path,
        default=Path(__file__).resolve().parents[2] / "docs/glossary.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    candidate_values = (args.candidate_ref, args.candidate_english_dump,
                        args.candidate_localized_dump)
    if any(value is not None for value in candidate_values):
        _require(all(value is not None for value in candidate_values),
                 "candidate ref and both candidate dumps must be supplied together")
        _require(args.review_results is not None,
                 "candidate validation requires review results")
    _require(args.scaffold_output is None
             or (args.review_results is None and args.candidate_ref is None),
             "scaffolding cannot be combined with review/candidate validation")
    records = None
    if args.candidate_ref is not None:
        hardened.shared._require_candidate_commit(
            args.baseline_ref, args.candidate_ref, exact_clean_checkout=True
        )
        ledger = hardened._candidate_regular_blob(
            args.candidate_ref,
            hardened._repo_relative_git_path(args.review_results,
                                             "review results"),
            "review results",
        )
        records = _strict_block_from_text(ledger.decode("utf-8"))
    inventory = build_inventory(
        args.baseline_ref, args.english_dump, args.localized_dump,
        args.glossary,
        glossary_ref=args.candidate_ref if args.candidate_ref else None,
    )
    candidate = None
    if args.scaffold_output is not None:
        scaffold_results(args.scaffold_output, inventory)
    if args.candidate_ref is not None:
        candidate = add_candidate(
            inventory, args.baseline_ref, args.candidate_ref,
            args.candidate_english_dump, args.candidate_localized_dump,
        )
    if args.review_results is not None:
        inventory["review_evidence"] = validate_results(
            args.review_results, inventory, candidate, records=records
        )
    hardened.shared._safe_output(args.inventory_output, inventory)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"decorlines_inventory.py: {exc}", file=sys.stderr)
        raise SystemExit(2)
