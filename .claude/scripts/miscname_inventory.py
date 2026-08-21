#!/usr/bin/env python3
"""Build and audit the Issue #87 miscname review inventory.

The inventory is derived from production ``textdb-phase0-dump`` artifacts
for MiscDB and exact Git snapshots of ``database.cc``, ``miscname.txt`` and
all four consumers.  Membership comes from the effective definitions whose
winning source is miscname.txt; no prose count or hand-maintained key list is
used as the inventory source.

The baseline records the historical localized lookup alias
``SHT_int_loss`` for the English identity ``summon_horrible_things``.  That
alias is not accepted in a candidate: the production consumer queries the
English key and TextDB falls back to the English parent when the localized
key is absent.  Candidate validation also requires exact EN/ZH key equality,
variant/weight equality, recursive-token topology and Lua-site parity.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

import decorlines_inventory as misc_shared
import wpnnoise_inventory as hardened


SCHEMA_VERSION = 1
SOURCE_BASENAME = "miscname.txt"
STRICT_BEGIN = "<!-- BEGIN STRICT MISCNAME REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT MISCNAME REVIEW EVIDENCE v1 -->"
RESULTS_PATH = Path(__file__).resolve().parents[2] / "docs/miscname-review-results.md"

# Historical alias present only in the frozen baseline ZH source.  Stable
# inventory identities always use the English production lookup key.
BASELINE_ZH_ALIASES = {"summon_horrible_things": "sht_int_loss"}

INTERNAL_FRAGMENT_KEYS = frozenset({
    "_great_adj_", "_halloween_things_", "_lowly_",
})
DIRECT_ROOT_KEYS = frozenset({
    "summon_horrible_things",
    "harlequin_trap_lines",
    "welcome_spam",
    "welcome_spam dungeon descent",
    "welcome_spam halloween",
    "hell_effect_quiet",
    "hell_effect_noisy",
})
EXPECTED_MISSING_LOOKUPS = frozenset({"welcome_spam hints"})
CONSUMER_GIT_FILES = (
    "crawl-ref/source/database.cc",
    "crawl-ref/source/main.cc",
    "crawl-ref/source/stairs.cc",
    "crawl-ref/source/spl-summoning.cc",
    "crawl-ref/source/traps.cc",
)

CONCLUSIONS = {
    "keep", "adjust", "retranslate", "defer implementation",
    "defer terminology",
}
DEFER_CONCLUSIONS = {"defer implementation", "defer terminology"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
METADATA_FIELDS = {
    "baseline", "english_production_dump_sha256",
    "chinese_production_dump_sha256", "glossary_sha256",
    "identity_count", "english_variant_count", "chinese_variant_count",
    "inventory_sha256", "terminal_conclusion_counts",
}
CARD_FIELDS = {
    "identity", "key", "baseline_chinese_key", "lifecycle",
    "dependency_group", "display_context", "producer_consumer",
    "evidence_locations", "current_english_variants_sha256",
    "current_chinese_variants_sha256", "proposed_english_variants_sha256",
    "proposed_chinese_variants_sha256", "terminal_conclusion", "confidence",
    "rationale", "rejected_alternatives", "reentry_trigger",
    "deferral_owner", "deferral_reason",
}


class InventoryError(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _variant_shape(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"weight": item["weight"], "text": item["text"]}
            for item in variants]


def _variant_digest(variants: list[dict[str, Any]]) -> str:
    return _sha256(_canonical_json(_variant_shape(variants)))


def _derive_scoped_dump(oid: str, directory: str, label: str) -> dict[str, Any]:
    manifest = (
        misc_shared._misc_source_manifest(oid, label)
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


def _require_regular_inputs(ref: str, directory: str, label: str) -> None:
    manifest = (
        misc_shared._misc_source_manifest(ref, label)
        if directory == "database/"
        else hardened.shared._localized_source_manifest(ref, label)
    )
    hardened._require_regular_git_blobs(
        ref,
        list(CONSUMER_GIT_FILES)
        + [f"crawl-ref/source/dat/{name}" for name in manifest],
        label,
    )


def _read_exact(ref: str, path: str, label: str) -> str:
    return hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(ref, path, label), label
    )


def _consumer_facts(ref: str, label: str) -> dict[str, Any]:
    database = _read_exact(ref, "crawl-ref/source/database.cc", label)
    main = _read_exact(ref, "crawl-ref/source/main.cc", label)
    stairs = _read_exact(ref, "crawl-ref/source/stairs.cc", label)
    summoning = _read_exact(ref, "crawl-ref/source/spl-summoning.cc", label)
    traps = _read_exact(ref, "crawl-ref/source/traps.cc", label)

    _require(misc_shared._misc_source_manifest(ref, label)[0]
             == "database/miscname.txt",
             f"{label} miscname.txt is no longer first in MiscDB")
    _require(summoning.count('getMiscString("summon_horrible_things")') == 1,
             f"{label} summon_horrible_things consumer changed")
    _require(traps.count('getMiscString("harlequin_trap_lines")') == 1,
             f"{label} harlequin_trap_lines consumer changed")
    _require(re.search(
        r'getMiscString\(loud\s*\?\s*"hell_effect_noisy"\s*:\s*'
        r'"hell_effect_quiet"\)', stairs
    ) is not None, f"{label} hell effect consumer changed")
    _require(main.count('getMiscString("welcome_spam" + type)') == 1,
             f"{label} welcome_spam consumer changed")
    suffix_match = re.search(
        r'static string _welcome_spam_suffix\(\)\s*\{(?P<body>.*?)\n\}',
        main, re.DOTALL,
    )
    _require(suffix_match is not None,
             f"{label} welcome_spam suffix producer is missing")
    suffix_body = suffix_match.group("body")
    for literal in ('return " Hints";', 'return " " + type;',
                    'return " Halloween";', 'return "";'):
        _require(suffix_body.count(literal) == 1,
                 f"{label} welcome_spam suffix shape changed at {literal!r}")

    # Bind the legacy lookup used by getMiscString itself, rather than the
    # later recipe-replay helper: both the suffixed attempt and its unsuffixed
    # fallback must query the localized child first and the English parent
    # second.  Slicing between two exact declarations prevents an unrelated
    # helper with similar fetch code from satisfying this check.
    lookup_start = database.find(
        "static weighted_lookup_result _getWeightedSelection(\n"
    )
    lookup_end = database.find("template <typename Lookup>", lookup_start)
    _require(lookup_start >= 0 and lookup_end > lookup_start,
             f"{label} production weighted lookup is missing")
    lookup_body = database[lookup_start:lookup_end]
    _require(lookup_body.count("canonical_key = key + suffix;") == 1
             and lookup_body.count("canonical_key = key;") == 1
             and lookup_body.count("if (!base_only && db.translation)") == 2
             and lookup_body.count(
                 "_database_fetch(db.translation->get(), canonical_key)") == 2
             and lookup_body.count(
                 "_database_fetch(db.get(), canonical_key)") == 2,
             f"{label} localized MiscDB fallback semantics changed")
    return {
        "loader": "database.cc:TextDB(misc)",
        "fallback": "localized-key-then-english-parent",
        "summon_consumer": "spl-summoning.cc:cast_summon_horrible_things",
        "trap_consumer": "traps.cc:harlequin trap message",
        "welcome_consumer": "main.cc:_announce_goal_message",
        "hell_consumer": "stairs.cc:_hell_effects",
        "direct_root_keys": sorted(DIRECT_ROOT_KEYS),
        "known_missing_lookups": sorted(EXPECTED_MISSING_LOOKUPS),
    }


def _definition_lines(source: str, label: str) -> dict[str, int]:
    try:
        definitions = hardened.shared.parse_db_keys(source, SOURCE_BASENAME)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
    result: dict[str, int] = {}
    for definition in definitions:
        key = hardened.shared.lowercase_string(definition.raw_key)
        _require(key not in result, f"{label} duplicate physical key {key!r}")
        result[key] = definition.key_line
    return result


def _source_rows(artifact: dict[str, Any], directory: str,
                 label: str) -> list[dict[str, Any]]:
    source_name = f"{directory}{SOURCE_BASENAME}"
    rows = [
        entry for entry in artifact["entries"]
        if any(history["source_name"] == source_name
               for history in entry["source_history"])
    ]
    keys = [entry["canonical_key"] for entry in rows]
    _require(len(keys) == len(set(keys)), f"{label} duplicate effective key")
    for entry in rows:
        key = entry["canonical_key"]
        _require(entry["parse_error"] is None,
                 f"{label} parse error at {key!r}")
        _require(not entry["body_empty"], f"{label} empty body at {key!r}")
        _require(entry["effective_provenance"]["source_name"] == source_name,
                 f"{label} key {key!r} is overridden outside miscname.txt")
        _require(len(entry["source_history"]) == 1,
                 f"{label} key {key!r} has an unexpected override")
    return sorted(rows, key=lambda item: item["canonical_key"])


def _variant(raw: dict[str, Any]) -> dict[str, Any]:
    text = raw["raw_pattern"]
    return {
        "variant_ordinal": raw["locator"]["variant_ordinal"],
        "weight": raw["weight"],
        "text": text,
        "runtime_tokens": hardened._runtime_tokens(text),
        "random_site_counts": hardened._random_site_counts(text),
        "lua_site_count": len(hardened._lua_sites(text)),
        "lua_topology": _lua_topology(text),
    }


_LUA_RETURN_LITERAL_RE = re.compile(
    r'(\breturn[ \t]+)"(?:\\.|[^"\\])*"'
)


def _lua_topology(text: str) -> list[str]:
    """Return display-string-neutral Lua control-flow fingerprints.

    miscname owns one narrow Lua grammar: each block has two translated
    ``return "display"`` literals around the ``you.can_smell()`` branch.
    Replacing only those literals preserves every operator, call, keyword,
    statement, order and whitespace byte-for-byte.  Requiring exactly two
    replacements per site fails closed if the grammar changes instead of
    silently reducing topology to a site count.
    """
    result = []
    for block in hardened._lua_blocks(text):
        normalized, count = _LUA_RETURN_LITERAL_RE.subn(
            r'\1"<display>"', block
        )
        _require(count == 2,
                 "miscname Lua site must contain exactly two display returns")
        _require('"' not in normalized.replace('"<display>"', ''),
                 "miscname Lua site contains an unclassified string literal")
        result.append(normalized)
    return result


def _token_facts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    keys = {row["canonical_key"] for row in rows}
    edges = {key: set() for key in keys}
    refs = {key: [] for key in keys}
    unresolved = []
    for row in rows:
        source = row["canonical_key"]
        for raw in row["variants"]:
            ordinal = raw["locator"]["variant_ordinal"]
            for token in hardened._runtime_tokens(raw["raw_pattern"]):
                target = token[1:-1].lower()
                site = {"key": source, "variant_ordinal": ordinal,
                        "token": token}
                if target in keys:
                    edges[source].add(target)
                    refs[target].append(site)
                else:
                    unresolved.append(site)
    return {
        "edges": {key: sorted(value) for key, value in sorted(edges.items())},
        "references": {key: sorted(value, key=lambda item: (
            item["key"], item["variant_ordinal"], item["token"]))
            for key, value in sorted(refs.items())},
        "unresolved": sorted(unresolved, key=lambda item: (
            item["key"], item["variant_ordinal"], item["token"])),
    }


def _reachability(edges: dict[str, list[str]], roots: set[str]) -> dict[str, Any]:
    reached = set(roots)
    queue = deque((key, (key,)) for key in sorted(roots))
    witnesses: dict[str, list[str]] = {}
    while queue:
        source, path = queue.popleft()
        for target in edges[source]:
            if target in reached:
                continue
            reached.add(target)
            next_path = (*path, target)
            witnesses[target] = list(next_path)
            queue.append((target, next_path))
    return {
        "reachable": sorted(reached),
        "unreachable": sorted(set(edges) - reached),
        "witnesses": witnesses,
    }


def _dataset(ref: str, path: Path, directory: str, label: str,
             candidate: bool) -> dict[str, Any]:
    hardened.shared._validate_oid(ref, label)
    _require_regular_inputs(ref, directory, label)
    artifact, raw = hardened._load_dump_safe(
        path, label, directory, expected_database="misc"
    )
    derived = _derive_scoped_dump(ref, directory, label)
    hardened.shared._require_scoped_derivation(
        artifact, derived, label, source_basename=SOURCE_BASENAME
    )
    rows = _source_rows(artifact, directory, label)
    source_name = f"{directory}{SOURCE_BASENAME}"
    source = next(item["normalized_utf8"] for item in artifact["sources"]
                  if item["source_name"] == source_name)
    lines = _definition_lines(source, label)
    entries = []
    for row in rows:
        entries.append({
            "key": row["canonical_key"],
            "source_line": lines[row["canonical_key"]],
            "variants": [_variant(item) for item in row["variants"]],
        })
    facts = _token_facts(rows)
    physical_keys = {entry["key"] for entry in entries}
    if candidate or directory == "database/":
        roots = DIRECT_ROOT_KEYS
        fragments = INTERNAL_FRAGMENT_KEYS
    else:
        roots = {
            BASELINE_ZH_ALIASES.get(key, key) for key in DIRECT_ROOT_KEYS
        }
        fragments = INTERNAL_FRAGMENT_KEYS
    _require(physical_keys == roots | fragments,
             f"{label} miscname membership differs: "
             f"missing={sorted((roots | fragments) - physical_keys)!r} "
             f"extra={sorted(physical_keys - (roots | fragments))!r}")
    _require(not facts["unresolved"],
             f"{label} has unresolved recursive tokens: {facts['unresolved']!r}")
    reachability = _reachability(facts["edges"], set(roots))
    _require(not reachability["unreachable"],
             f"{label} has unreachable keys: {reachability['unreachable']!r}")
    missing_lookups = sorted(EXPECTED_MISSING_LOOKUPS & physical_keys)
    _require(not missing_lookups,
             f"{label} unexpected dedicated Hints lookup appeared")
    total = sum(len(entry["variants"]) for entry in entries)
    return {
        "artifact_sha256": _sha256(raw),
        "source_name": source_name,
        "source_sha256": _sha256(source.encode("utf-8")),
        "entries": entries,
        "variant_count": total,
        "random_site_count": sum(
            len(variant["random_site_counts"])
            for entry in entries for variant in entry["variants"]
        ),
        "lua_site_count": sum(
            variant["lua_site_count"]
            for entry in entries for variant in entry["variants"]
        ),
        "token_facts": facts,
        "reachability": reachability,
    }


def _read_glossary(path: Path, ref: str | None) -> bytes:
    if ref is None:
        return hardened._read_artifact_bytes(path, "glossary")
    return hardened._candidate_regular_blob(
        ref, hardened._repo_relative_git_path(path, "glossary"), "glossary"
    )


def _pair_baseline(en: dict[str, Any], zh: dict[str, Any]) -> list[dict[str, Any]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    expected_zh = {
        BASELINE_ZH_ALIASES.get(key, key) for key in en_by_key
    }
    _require(set(zh_by_key) == expected_zh,
             "baseline miscname EN/ZH identity mapping differs")
    entries = []
    for key in sorted(en_by_key):
        zh_key = BASELINE_ZH_ALIASES.get(key, key)
        en_entry, zh_entry = en_by_key[key], zh_by_key[zh_key]
        lifecycle = ("recursive-internal-fragment"
                     if key in INTERNAL_FRAGMENT_KEYS
                     else "direct-production-root")
        entries.append({
            "identity": f"miscname:{key}",
            "key": key,
            "baseline_chinese_key": zh_key,
            "lifecycle": lifecycle,
            "dependency_group": _group_for(key),
            "english_source_line": en_entry["source_line"],
            "chinese_source_line": zh_entry["source_line"],
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
            "english_referencing_sites": en["token_facts"]["references"][key],
            "chinese_referencing_sites": zh["token_facts"]["references"][zh_key],
        })
    return entries


def _group_for(key: str) -> str:
    if key in {"_great_adj_", "welcome_spam",
               "welcome_spam dungeon descent"}:
        return "开场与佐特宝珠"
    if key in {"_halloween_things_", "_lowly_", "welcome_spam halloween"}:
        return "万圣节开场"
    if key.startswith("hell_effect_"):
        return "地狱氛围消息"
    if key == "summon_horrible_things":
        return "召唤骇物精神损耗"
    return "丑角陷阱前缀"


def build_inventory(baseline_ref: str, english_path: Path,
                    localized_path: Path, glossary_path: Path,
                    glossary_ref: str | None = None) -> dict[str, Any]:
    en = _dataset(baseline_ref, english_path, "database/", "baseline EN", False)
    zh = _dataset(baseline_ref, localized_path, "database/zh/", "baseline ZH", False)
    entries = _pair_baseline(en, zh)
    facts = _consumer_facts(baseline_ref, "baseline")
    asymmetry = {
        entry["key"]: [len(entry["english_variants"]),
                       len(entry["chinese_variants"])]
        for entry in entries
        if len(entry["english_variants"]) != len(entry["chinese_variants"])
    }
    scope = {
        "source_basename": SOURCE_BASENAME,
        "identity_keys": [entry["key"] for entry in entries],
        "baseline_chinese_aliases": BASELINE_ZH_ALIASES,
        "direct_root_keys": sorted(DIRECT_ROOT_KEYS),
        "internal_fragment_keys": sorted(INTERNAL_FRAGMENT_KEYS),
        "known_missing_lookups": sorted(EXPECTED_MISSING_LOOKUPS),
        "baseline_asymmetry": asymmetry,
        "consumer_facts": facts,
    }
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": scope,
        "scope_sha256": _sha256(_canonical_json(scope)),
        "glossary": {"path": "docs/glossary.md",
                     "sha256": _sha256(_read_glossary(glossary_path, glossary_ref))},
        "dumps": {
            "english": {key: value for key, value in en.items()
                        if key != "entries"},
            "localized": {key: value for key, value in zh.items()
                          if key != "entries"},
        },
        "entries": entries,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _pair_candidate(en: dict[str, Any], zh: dict[str, Any]) -> list[dict[str, Any]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(set(en_by_key) == set(zh_by_key),
             "candidate miscname EN/ZH key sets differ")
    _require(set(en_by_key) == DIRECT_ROOT_KEYS | INTERNAL_FRAGMENT_KEYS,
             "candidate miscname key set differs from production identities")
    entries = []
    for key in sorted(en_by_key):
        en_entry, zh_entry = en_by_key[key], zh_by_key[key]
        en_variants, zh_variants = en_entry["variants"], zh_entry["variants"]
        _require(len(en_variants) == len(zh_variants),
                 f"candidate variant count differs at {key!r}")
        _require([item["weight"] for item in en_variants]
                 == [item["weight"] for item in zh_variants],
                 f"candidate weight order differs at {key!r}")
        for ordinal, (en_variant, zh_variant) in enumerate(zip(en_variants, zh_variants)):
            _require(en_variant["runtime_tokens"] == zh_variant["runtime_tokens"],
                     f"candidate token order differs at {key!r} ordinal {ordinal}")
            _require(en_variant["random_site_counts"]
                     == zh_variant["random_site_counts"],
                     f"candidate random topology differs at {key!r} ordinal {ordinal}")
            _require(en_variant["lua_site_count"] == zh_variant["lua_site_count"],
                     f"candidate Lua topology differs at {key!r} ordinal {ordinal}")
            _require(en_variant["lua_topology"] == zh_variant["lua_topology"],
                     f"candidate Lua control flow differs at {key!r} ordinal {ordinal}")
        entries.append({"identity": f"miscname:{key}", "key": key,
                        "english_variants": en_variants,
                        "chinese_variants": zh_variants})
    return entries


def add_candidate(inventory: dict[str, Any], baseline_ref: str,
                  candidate_ref: str, english_path: Path,
                  localized_path: Path) -> dict[str, Any]:
    hardened.shared._require_candidate_commit(
        baseline_ref, candidate_ref, exact_clean_checkout=True
    )
    en = _dataset(candidate_ref, english_path, "database/", "candidate EN", True)
    zh = _dataset(candidate_ref, localized_path, "database/zh/", "candidate ZH", True)
    _require(_consumer_facts(candidate_ref, "candidate")
             == inventory["scope"]["consumer_facts"],
             "candidate miscname consumer contract drifted")
    entries = _pair_candidate(en, zh)
    candidate = {
        "candidate_ref": candidate_ref,
        "dumps": {
            "english": {key: value for key, value in en.items() if key != "entries"},
            "localized": {key: value for key, value in zh.items() if key != "entries"},
        },
        "entries": entries,
    }
    candidate["candidate_sha256"] = _sha256(_canonical_json(candidate))
    inventory["candidate"] = candidate
    return candidate


def _strict_block_from_text(text: str) -> list[dict[str, Any]]:
    _require(text.count(STRICT_BEGIN) == 1 and text.count(STRICT_END) == 1,
             "review results require exactly one strict marker pair")
    body = text.split(STRICT_BEGIN, 1)[1].split(STRICT_END, 1)[0].strip()
    match = re.fullmatch(r"```jsonl\s*\n(.*?)\n```", body, re.DOTALL)
    _require(match is not None, "strict review evidence must be one JSONL fence")
    records = []
    for number, line in enumerate(match.group(1).splitlines(), 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InventoryError(f"invalid JSONL record {number}: {exc}") from exc
        _require(isinstance(value, dict), f"JSONL record {number} must be an object")
        records.append(value)
    return records


def _strict_block(path: Path) -> list[dict[str, Any]]:
    return _strict_block_from_text(
        hardened._read_artifact_bytes(path, "review results").decode("utf-8")
    )


def _expected_metadata(inventory: dict[str, Any],
                       cards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "baseline": inventory["baseline_ref"],
        "english_production_dump_sha256":
            inventory["dumps"]["english"]["artifact_sha256"],
        "chinese_production_dump_sha256":
            inventory["dumps"]["localized"]["artifact_sha256"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": len(inventory["entries"]),
        "english_variant_count":
            inventory["dumps"]["english"]["variant_count"],
        "chinese_variant_count":
            inventory["dumps"]["localized"]["variant_count"],
        "inventory_sha256": inventory["inventory_sha256"],
        "terminal_conclusion_counts": dict(sorted(Counter(
            card["terminal_conclusion"] for card in cards
        ).items())),
    }


def validate_results(path: Path, inventory: dict[str, Any],
                     candidate: dict[str, Any] | None = None,
                     records: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    records = records if records is not None else _strict_block(path)
    _require(len(records) == len(inventory["entries"]) + 1,
             "review results require one metadata record and one card per identity")
    metadata, cards = records[0], records[1:]
    _require(set(metadata) == METADATA_FIELDS, "review metadata fields mismatch")
    _require(metadata == _expected_metadata(inventory, cards),
             "review metadata mismatch")
    expected = {entry["identity"]: entry for entry in inventory["entries"]}
    _require([card.get("identity") for card in cards] == sorted(expected),
             "review cards must cover every identity once in deterministic order")
    candidate_by_identity = ({entry["identity"]: entry
                              for entry in candidate["entries"]}
                             if candidate else {})
    for card in cards:
        identity = card["identity"]
        entry = expected[identity]
        _require(set(card) == CARD_FIELDS, f"review card {identity} fields mismatch")
        for field in ("key", "baseline_chinese_key", "lifecycle",
                      "dependency_group"):
            _require(card[field] == entry[field],
                     f"review card {identity} {field} mismatch")
        _require(card["current_english_variants_sha256"]
                 == _variant_digest(entry["english_variants"]),
                 f"review card {identity} current EN digest mismatch")
        _require(card["current_chinese_variants_sha256"]
                 == _variant_digest(entry["chinese_variants"]),
                 f"review card {identity} current ZH digest mismatch")
        _require(card["proposed_english_variants_sha256"]
                 == card["current_english_variants_sha256"],
                 f"review card {identity} may not change English")
        conclusion = card["terminal_conclusion"]
        _require(conclusion in CONCLUSIONS,
                 f"review card {identity} conclusion mismatch")
        _require(card["confidence"] in CONFIDENCE_LEVELS,
                 f"review card {identity} confidence mismatch")
        for field in ("display_context", "rationale", "reentry_trigger"):
            _require(isinstance(card[field], str) and card[field].strip(),
                     f"review card {identity} requires {field}")
        _require(isinstance(card["producer_consumer"], dict)
                 and card["producer_consumer"],
                 f"review card {identity} requires producer/consumer")
        _require(isinstance(card["evidence_locations"], list)
                 and card["evidence_locations"],
                 f"review card {identity} requires evidence locations")
        _require(isinstance(card["rejected_alternatives"], list)
                 and card["rejected_alternatives"],
                 f"review card {identity} requires rejected alternatives")
        if conclusion in DEFER_CONCLUSIONS:
            _require(isinstance(card["deferral_owner"], str)
                     and card["deferral_owner"].strip()
                     and isinstance(card["deferral_reason"], str)
                     and card["deferral_reason"].strip(),
                     f"review card {identity} deferred fields missing")
        else:
            _require(card["deferral_owner"] is None
                     and card["deferral_reason"] is None,
                     f"review card {identity} forbids deferral fields")
        if candidate:
            actual = candidate_by_identity[identity]
            actual_en = _variant_digest(actual["english_variants"])
            actual_zh = _variant_digest(actual["chinese_variants"])
            _require(actual_en == card["proposed_english_variants_sha256"],
                     f"candidate EN drift at {identity}")
            _require(actual_zh == card["proposed_chinese_variants_sha256"],
                     f"candidate ZH differs from approved proposal at {identity}")
            changed = actual_zh != card["current_chinese_variants_sha256"]
            _require(changed == (conclusion in {"adjust", "retranslate"}),
                     f"review card {identity} conclusion/change mismatch")
    return {"metadata": metadata, "cards": cards}


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
    parser.add_argument("--glossary", type=Path,
                        default=Path(__file__).resolve().parents[2]
                        / "docs/glossary.md")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    values = (args.candidate_ref, args.candidate_english_dump,
              args.candidate_localized_dump)
    if any(value is not None for value in values):
        _require(all(value is not None for value in values),
                 "candidate ref and both candidate dumps must be supplied together")
        _require(args.review_results is not None,
                 "candidate validation requires review results")
        hardened.shared._require_candidate_commit(
            args.baseline_ref, args.candidate_ref, exact_clean_checkout=True
        )
        ledger = hardened._candidate_regular_blob(
            args.candidate_ref,
            hardened._repo_relative_git_path(args.review_results, "review results"),
            "review results",
        )
        records = _strict_block_from_text(ledger.decode("utf-8"))
    else:
        records = None
    inventory = build_inventory(
        args.baseline_ref, args.english_dump, args.localized_dump,
        args.glossary, glossary_ref=args.candidate_ref if args.candidate_ref else None,
    )
    candidate = None
    if args.candidate_ref:
        candidate = add_candidate(
            inventory, args.baseline_ref, args.candidate_ref,
            args.candidate_english_dump, args.candidate_localized_dump,
        )
    if args.review_results:
        inventory["review_evidence"] = validate_results(
            args.review_results, inventory, candidate, records=records
        )
    hardened.shared._safe_output(args.inventory_output, inventory)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"miscname inventory error: {exc}", file=sys.stderr)
        raise SystemExit(1)
