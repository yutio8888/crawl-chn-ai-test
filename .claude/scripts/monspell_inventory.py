#!/usr/bin/env python3
"""Build and audit the Issue #59 monspell inventory from production dumps.

The supplied ``textdb-phase0-dump`` artifacts (EN and ZH) remain the artifacts
under review. This narrow entry reuses ``monflee_inventory`` for exact-Git
source discovery, TextDB parsing, weighted-variant derivation, artifact
validation, hashing, and safe output, and ``audit_monspell_phase0`` for the
semantic-fingerprint binding of the EN dump to the checked-in phase0
inventory.  Only monspell's consumer-specific invariants and strict ledger
schema live here.

Legacy topology note: the baseline ZH ``monspell.txt`` is NOT variant- or
token-identical to the EN file (357 vs 355 variants; two keys differ in
variant count; 86 paired variants differ in token usage while the ZH token
vocabulary stays a subset of EN's).  The strict ledger therefore asserts what
the production data actually guarantees: identical key sets, contiguous
definition ordinals, monspell.txt-only provenance without overrides or parse
errors, weight and control-prefix parity on every paired ordinal, a ZH token
vocabulary that is a subset of the EN vocabulary, frozen variant/token/site
counts, and a frozen two-key asymmetry.  Per-variant EN==ZH token equality is
not asserted (the plan's literal formulation does not hold on baseline data).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import Any

import monflee_inventory as shared
from audit_monspell_phase0 import (
    ArtifactError,
    build_inventory as build_phase0_inventory,
)
from command_inventory import parse_db_keys
from generate_message_overlay import ManifestError, _normalise_manifest, load_manifest
from i18n_shared import lowercase_string


SCHEMA_VERSION = 1
PHASE0_SCHEMA_VERSION = 1
SOURCE_BASENAME = "monspell.txt"
STRICT_BEGIN = "<!-- BEGIN STRICT MONSPELL REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT MONSPELL REVIEW EVIDENCE v1 -->"
DOMAIN = "monspell"
ANCHOR_DOMAIN = "monspell_candidate_lookup"
MANIFEST_FRAGMENT_GLOB = "monspell/*.json"
EXPECTED_CANDIDATE_ANCHOR_SHA256 = (
    "9eb63d334f31c1dfb608c7c742f2ce4046a711f7450d6de0ac516033baf3c083"
)
EXPECTED_SEMANTIC_FINGERPRINT = (
    "7031515a931079c2c58c792d5c7ddc44d8fb391c2814aa371fa3c417298db94b"
)
EXPECTED_SOURCE_FINGERPRINT = (
    "49ef2b9eb42f55312a4cf3965487af07c82b555f5b6720c3c1fa43903828a054"
)
EXPECTED_IDENTITY_COUNT = 262
EXPECTED_REACHABLE_COUNT = 251
EXPECTED_UNREACHABLE_COUNT = 11
EXPECTED_EN_VARIANT_COUNT = 355
EXPECTED_ZH_VARIANT_COUNT = 357
EXPECTED_EN_TOKEN_SITES = 605
EXPECTED_ZH_TOKEN_SITES = 529
EXPECTED_RANDOM_SUBSTRING_SITES = 12
EXPECTED_LUA_SITES = 0
EXPECTED_VISUAL_PREFIXES = 10
EXPECTED_MODE_COUNTS = {
    "CANDIDATE": 250,
    "LEGACY_ONLY": 10,
    "CLOSURE_ONLY": 2,
}
EXPECTED_ROUTE_COUNTS = {"STRUCTURED": 245, "LEGACY": 12, "SUPPRESSED": 5}
EXPECTED_PRIMARY_POLICY_COUNTS = {
    "NONE": 233,
    "CASE_MAP": 8,
    "CAPTURE_SLOT": 1,
    "RECURSIVE_CASE_MAP": 10,
    "LEGACY_ONLY": 10,
}
EXPECTED_MIXED_POLICY_KEYS = {
    "orb of entropy cast": ["CASE_MAP", "NONE", "NONE", "NONE"],
    "orb of winter cast": ["NONE", "NONE", "CASE_MAP"],
    "vanquished vanguard nergalle cast": ["CAPTURE_SLOT", "NONE"],
}
EXPECTED_SUPPRESSED_KEYS = {
    "avatar song cast",
    "blink away revenant cast",
    "blink magical cast",
    "seal doors cast",
    "siren song cast",
}
EXPECTED_NO_ZH_ENTRY_COUNT = 15
EXPECTED_STRUCTURED_TEMPLATE_COUNT = 582
EXPECTED_STRUCTURED_RELATION_COUNTS = {
    "AT": 115, "NEXT_TO": 115, "PAST": 115, "NONE": 237,
}
EXPECTED_LINE_METADATA_RELATION_COUNTS = {
    "AT": 111, "NEXT_TO": 111, "PAST": 111, "NONE": 206,
}
EXPECTED_CASE_RELATION_COUNTS = {
    "AT": 4, "NEXT_TO": 4, "PAST": 4, "NONE": 31,
}
EXPECTED_SENSORY_COUNTS = {"PLAIN": 342, "VISUAL": 10}
ASYMMETRIC_VARIANT_KEYS = {
    "guardian serpent cast": (1, 4),
    "guardian serpent cast targeted": (3, 2),
}
ROUTES = {"STRUCTURED", "LEGACY", "SUPPRESSED"}
ENTRY_MODES = {"CANDIDATE", "LEGACY_ONLY", "CLOSURE_ONLY"}
POLICIES = {
    "NONE", "CASE_MAP", "RECURSIVE_CASE_MAP", "CAPTURE_SLOT", "LEGACY_ONLY",
}
CASE_POLICIES = {"CASE_MAP", "RECURSIVE_CASE_MAP"}
SENSORY_ALLOWED = {"PLAIN", "VISUAL"}
ALLOWED_CONTROLS = {None, "VISUAL"}
PRODUCTION_ZH_SOURCE = {
    "STRUCTURED": "catalog",
    "LEGACY": "zh/monspell.txt",
    "SUPPRESSED": "none",
}
DEFER_CONCLUSIONS = {"defer terminology", "defer implementation"}
TERMINAL_CONCLUSIONS = {"keep", "adjust", "retranslate", *DEFER_CONCLUSIONS}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
METADATA_FIELDS = {
    "baseline", "glossary_sha256", "identity_count", "inventory_sha256",
}
CARD_FIELDS = {
    "actual_behavior", "confidence", "consumer", "current_chinese",
    "current_english", "current_structured_zh", "deferral_owner",
    "deferral_reason", "dependency_group", "display_context", "entry_mode",
    "evidence_locations", "fallback_zh_source", "glossary_authority",
    "identity", "key", "legacy_variant_reviews", "lifecycle",
    "primary_materialization_policy", "producers", "production_facts",
    "production_zh_source", "proposed_structured_zh", "proposed_translation",
    "reentry_trigger", "rejected_alternatives", "reviewer_rationale",
    "route", "runtime_evidence", "structured_template_reviews",
    "terminal_conclusion",
}
PRODUCTION_FACT_FIELDS = {
    "control_prefixes", "legacy_variant_count", "materialization_policies",
    "runtime_tokens", "structured_relations", "structured_template_count",
    "weights",
}
STRUCTURED_TEMPLATE_REVIEW_FIELDS = {
    "current_pattern_zh", "locator", "materialization_policy", "pattern_en",
    "proposed_pattern_zh", "rationale", "relation", "sensory",
    "terminal_conclusion",
}
LEGACY_VARIANT_REVIEW_FIELDS = {
    "control_prefix", "current_chinese", "english", "fallback",
    "proposed_translation", "rationale", "runtime_tokens",
    "terminal_conclusion", "variant_ordinal", "weight",
}
DEFERRAL_FIELDS = {"deferral_owner", "deferral_reason", "reentry_trigger"}
FROZEN_CONSUMER = {
    "route_decision": "crawl-ref/source/fork-message-overlay.cc:1704",
    "overlay_covers": "crawl-ref/source/fork-message-overlay.cc:1676",
    "candidate_search": "crawl-ref/source/mon-cast.cc:9291",
    "candidate_search_definition": "crawl-ref/source/fork-message-overlay.cc:1748",
    "materialize": "crawl-ref/source/fork-message-overlay.cc:1779",
    "render": "crawl-ref/source/fork-message-overlay.cc:2400",
    "legacy_getspeakstring": "crawl-ref/source/database.cc:2307",
}
FROZEN_PRODUCERS = [{
    "location": "crawl-ref/source/mon-cast.cc:8764",
    "mode": "_speech_keys → build_key_recipe",
}]
FROZEN_ACTUAL_BEHAVIOR = {
    "STRUCTURED": (
        "route_monspell_message 在 overlay 启用且 covers(key) 时返回 STRUCTURED"
        "（fork-message-overlay.cc:1704/1676）；mon-cast.cc:9291 调用 "
        "search_message_candidate（定义 fork-message-overlay.cc:1748）查找候选，"
        "materialize_monspell_candidate（fork-message-overlay.cc:1779）按 "
        "materialization_policy 实例化模板，render_materialized_candidate（:2400）"
        "以当前语言渲染；STRUCTURED 失败永不回退 LEGACY。"
    ),
    "LEGACY": (
        "route_monspell_message 在 overlay 未启用或不 covers(key) 时返回 LEGACY；"
        "getSpeakString（database.cc:2307）以生产权重选择正文并展开 token，VISUAL "
        "前缀正文路由至 MSGCH_TALK_VISUAL。"
    ),
    "SUPPRESSED": (
        "english_snapshot 为 __NONE 的 CANDIDATE：模板被抑制，任何语言都不产生 "
        "emission，亦不回退 LEGACY。"
    ),
}
FROZEN_DISPLAY_CONTEXT = {
    "STRUCTURED": "怪物施法时经结构化模板渲染、仅玩家可见时显示的玩家可见消息。",
    "LEGACY": "怪物施法时由 legacy SpeakDB 加权选择并展开 token 的玩家可见消息。",
    "SUPPRESSED": "抑制消息：任何语言、任何可见性下都不显示。",
}
FROZEN_LIFECYCLE = {
    "STRUCTURED": "structured-overlay-emission",
    "LEGACY": "legacy-speakdb-emission",
    "SUPPRESSED": "suppressed-no-emission",
}
UNREACHABLE_RATIONALE_MARKER = "仅 phase0 静态定义审阅，无 candidate dump 运行时证据"
LEGACY_SYNC_MARKER = "与 structured 模板同步"
SCOPE = {
    "source_basename": SOURCE_BASENAME,
    "identity_count": EXPECTED_IDENTITY_COUNT,
    "reachable_count": EXPECTED_REACHABLE_COUNT,
    "unreachable_count": EXPECTED_UNREACHABLE_COUNT,
    "en_variant_count": EXPECTED_EN_VARIANT_COUNT,
    "zh_variant_count": EXPECTED_ZH_VARIANT_COUNT,
    "en_token_sites": EXPECTED_EN_TOKEN_SITES,
    "zh_token_sites": EXPECTED_ZH_TOKEN_SITES,
    "random_substring_sites": EXPECTED_RANDOM_SUBSTRING_SITES,
    "lua_sites": EXPECTED_LUA_SITES,
    "visual_prefixes": EXPECTED_VISUAL_PREFIXES,
    "mode_counts": EXPECTED_MODE_COUNTS,
    "route_counts": EXPECTED_ROUTE_COUNTS,
    "primary_policy_counts": EXPECTED_PRIMARY_POLICY_COUNTS,
    "mixed_policy_keys": EXPECTED_MIXED_POLICY_KEYS,
    "suppressed_keys": sorted(EXPECTED_SUPPRESSED_KEYS),
    "no_zh_entry_count": EXPECTED_NO_ZH_ENTRY_COUNT,
    "structured_template_count": EXPECTED_STRUCTURED_TEMPLATE_COUNT,
    "structured_relation_counts": EXPECTED_STRUCTURED_RELATION_COUNTS,
    "line_metadata_relation_counts": EXPECTED_LINE_METADATA_RELATION_COUNTS,
    "case_relation_counts": EXPECTED_CASE_RELATION_COUNTS,
    "sensory_counts": EXPECTED_SENSORY_COUNTS,
    "asymmetric_variant_keys": ASYMMETRIC_VARIANT_KEYS,
    "candidate_anchor_sha256": EXPECTED_CANDIDATE_ANCHOR_SHA256,
    "semantic_fingerprint": EXPECTED_SEMANTIC_FINGERPRINT,
    "source_fingerprint": EXPECTED_SOURCE_FINGERPRINT,
}


InventoryError = shared.InventoryError
_require = shared._require
_sha256 = shared._sha256
_canonical_json = shared._canonical_json
_is_int = shared._is_int
_nonempty_string = shared._nonempty_string
_require_exact_fields = shared._require_exact_fields


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot read {label} {path}: {exc}") from exc
    _require(isinstance(value, dict), f"{label} {path} must contain an object")
    return value


def _random_sites(pattern: str) -> list[dict[str, Any]]:
    sites: list[dict[str, Any]] = []
    position = 0
    while position < len(pattern):
        opening = pattern.find("[", position)
        stray_closing = pattern.find("]", position)
        if stray_closing >= 0 and (opening < 0 or stray_closing < opening):
            raise InventoryError(
                f"unbalanced random substring marker at offset {stray_closing}"
            )
        if opening < 0:
            break
        closing = pattern.find("]", opening + 1)
        _require(closing >= 0,
                 f"unbalanced random substring marker at offset {opening}")
        _require(pattern.find("[", opening + 1, closing) < 0,
                 f"nested random substring marker at offset {opening}")
        sites.append({"start": opening, "end": closing + 1,
                      "raw": pattern[opening + 1:closing]})
        position = closing + 1
    return sites


_LUA_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)


def _lua_sites(pattern: str) -> list[dict[str, Any]]:
    sites = [{"start": match.start(), "end": match.end()}
             for match in _LUA_RE.finditer(pattern)]
    _require(pattern.count("{{") == len(sites),
             f"unbalanced Lua site in pattern {pattern!r}")
    return sites


def _definition_lines(source: str, label: str) -> dict[str, int]:
    """Bind every canonical key to its raw-key source line (1-indexed).

    Mirrors production ``parse_db_keys`` header detection exactly: after a
    ``%%%%`` separator, comment and blank lines are skipped until the first
    non-empty trimmed line becomes the raw key (monspell.txt contains
    comment-led sections whose keys are not the immediate next line).
    """
    try:
        definitions = parse_db_keys(source, SOURCE_BASENAME)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
    lines: dict[str, int] = {}
    for definition in definitions:
        canonical = lowercase_string(definition.raw_key)
        _require(canonical not in lines,
                 f"{label} duplicate raw key {canonical!r} in monspell.txt")
        lines[canonical] = definition.key_line
    return lines


def _dump_binding(
    artifact: dict[str, Any], raw: bytes, label: str,
    expected_keys: set[str],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    directory = artifact["source_directory"]
    expected_source = f"{directory}{SOURCE_BASENAME}"
    matching_sources = [
        source for source in artifact["sources"]
        if source["source_name"] == expected_source
    ]
    _require(len(matching_sources) == 1,
             f"{label} dump must contain exactly one {expected_source!r}")
    source_snapshot = matching_sources[0]["normalized_utf8"]
    touching = [
        entry for entry in artifact["entries"]
        if any(item["source_name"] == expected_source
               for item in entry["source_history"])
    ]
    for entry in touching:
        key = entry["canonical_key"]
        _require(entry["parse_error"] is None, f"{label} key {key!r} has parse error")
        _require(not entry["body_empty"], f"{label} key {key!r} has an empty body")
        _require(len(entry["source_history"]) == 1,
                 f"{label} key {key!r} is overridden")
        _require(
            entry["effective_provenance"]["source_name"] == expected_source,
            f"{label} key {key!r} is not effective from {expected_source}",
        )

    actual_keys = {entry["canonical_key"] for entry in touching}
    _require(actual_keys == set(expected_keys),
             f"{label} monspell key set mismatch: expected {len(expected_keys)!r} "
             f"keys, got {len(actual_keys)!r}")
    ordinals = sorted(
        entry["effective_provenance"]["definition_ordinal"]
        for entry in touching
    )
    _require(ordinals == list(range(len(ordinals))),
             f"{label} monspell definition ordinals are not contiguous from zero")

    definition_lines = _definition_lines(source_snapshot, label)
    rows: list[dict[str, Any]] = []
    for entry in sorted(touching, key=lambda item: item["canonical_key"]):
        variants = []
        for expected_ordinal, variant in enumerate(entry["variants"]):
            locator = variant["locator"]
            _require(locator["variant_ordinal"] == expected_ordinal,
                     f"{label} ordinal gap for {entry['canonical_key']!r}")
            pattern = variant["raw_pattern"]
            prefix = shared._control_prefix(pattern)
            _require(prefix in ALLOWED_CONTROLS,
                     f"{label} unrecognized control prefix {prefix!r}")
            variants.append({
                "locator": {"key": entry["canonical_key"],
                            "variant_ordinal": expected_ordinal},
                "weight": variant["weight"],
                "control_prefix": prefix,
                "runtime_tokens": shared._runtime_tokens(pattern),
                "random_substring_sites": _random_sites(pattern),
                "lua_sites": _lua_sites(pattern),
                "raw_pattern": pattern,
            })
        key = entry["canonical_key"]
        _require(key in definition_lines,
                 f"{label} cannot bind a source line for {key!r}")
        rows.append({
            "key": key,
            "effective_source": expected_source,
            "definition_ordinal": entry["effective_provenance"]["definition_ordinal"],
            "source_line": definition_lines[key],
            "variants": variants,
        })

    is_english = directory == "database/"
    _require(
        sum(len(row["variants"]) for row in rows)
        == (EXPECTED_EN_VARIANT_COUNT if is_english else EXPECTED_ZH_VARIANT_COUNT),
        f"{label} monspell variant count mismatch",
    )
    _require(
        sum(len(variant["runtime_tokens"])
            for row in rows for variant in row["variants"])
        == (EXPECTED_EN_TOKEN_SITES if is_english else EXPECTED_ZH_TOKEN_SITES),
        f"{label} monspell runtime token site count mismatch",
    )
    _require(
        sum(len(variant["random_substring_sites"])
            for row in rows for variant in row["variants"])
        == EXPECTED_RANDOM_SUBSTRING_SITES,
        f"{label} monspell random substring site count mismatch",
    )
    _require(
        sum(len(variant["lua_sites"])
            for row in rows for variant in row["variants"])
        == EXPECTED_LUA_SITES,
        f"{label} monspell Lua site count mismatch",
    )
    _require(
        sum(variant["control_prefix"] == "VISUAL"
            for row in rows for variant in row["variants"])
        == EXPECTED_VISUAL_PREFIXES,
        f"{label} monspell VISUAL control prefix count mismatch",
    )
    binding = {
        "artifact_sha256": _sha256(raw),
        "database_name": artifact["database_name"],
        "source_directory": directory,
        "source_snapshots": [
            {
                "source_name": source["source_name"],
                "load_index": source["load_index"],
                "normalized_utf8_sha256": _sha256(
                    source["normalized_utf8"].encode("utf-8")
                ),
            }
            for source in artifact["sources"]
        ],
        "effective_monspell_source": expected_source,
    }
    return binding, rows


def _paired_entries(
    en_rows: list[dict[str, Any]], zh_rows: list[dict[str, Any]], label: str,
) -> list[dict[str, Any]]:
    en_by_key = {row["key"]: row for row in en_rows}
    zh_by_key = {row["key"]: row for row in zh_rows}
    _require(en_by_key.keys() == zh_by_key.keys(), f"{label} EN/ZH key sets differ")
    en_vocabulary = {
        token
        for row in en_rows for variant in row["variants"]
        for token in variant["runtime_tokens"]
    }
    zh_vocabulary = {
        token
        for row in zh_rows for variant in row["variants"]
        for token in variant["runtime_tokens"]
    }
    _require(zh_vocabulary <= en_vocabulary,
             f"{label} ZH token vocabulary is not a subset of the EN vocabulary")
    entries = []
    for key in sorted(en_by_key):
        en = en_by_key[key]
        zh = zh_by_key[key]
        en_count = len(en["variants"])
        zh_count = len(zh["variants"])
        if en_count != zh_count:
            frozen = ASYMMETRIC_VARIANT_KEYS.get(key)
            _require(
                frozen == (en_count, zh_count),
                f"{label} variant count differs for {key!r}: EN {en_count} "
                f"vs ZH {zh_count} (expected frozen {frozen!r})",
            )
        for ordinal in range(min(en_count, zh_count)):
            en_variant = en["variants"][ordinal]
            zh_variant = zh["variants"][ordinal]
            _require(en_variant["weight"] == zh_variant["weight"],
                     f"{label} weight differs for {key!r} variant {ordinal}")
            _require(
                en_variant["control_prefix"] == zh_variant["control_prefix"],
                f"{label} control prefix differs for {key!r} variant {ordinal}",
            )
        variants = []
        for ordinal, en_variant in enumerate(en["variants"]):
            zh_pattern = (
                zh["variants"][ordinal]["raw_pattern"]
                if ordinal < zh_count else None
            )
            variants.append({
                "locator": {"key": key, "variant_ordinal": ordinal},
                "weight": en_variant["weight"],
                "control_prefix": en_variant["control_prefix"],
                "runtime_tokens": en_variant["runtime_tokens"],
                "english": en_variant["raw_pattern"],
                "chinese": zh_pattern,
            })
        entries.append({
            "identity": f"monspell:{key}",
            "key": key,
            "english_source_line": en["source_line"],
            "chinese_source_line": zh["source_line"],
            "variants": variants,
            "unpaired_zh_variants": [
                {
                    "locator": {"key": key, "variant_ordinal": ordinal},
                    "weight": zh["variants"][ordinal]["weight"],
                    "control_prefix": zh["variants"][ordinal]["control_prefix"],
                    "runtime_tokens": zh["variants"][ordinal]["runtime_tokens"],
                    "chinese": zh["variants"][ordinal]["raw_pattern"],
                }
                for ordinal in range(en_count, zh_count)
            ] if zh_count > en_count else [],
        })
    return entries


def _template_records(
    key: str, variant: dict[str, Any], case_id: str,
    metadata: dict[str, Any], policy: str,
) -> list[dict[str, Any]]:
    _require(metadata.get("sensory") in SENSORY_ALLOWED,
             f"{key} variant {variant['variant_ordinal']} has disallowed sensory "
             f"{metadata.get('sensory')!r}")
    _require(metadata.get("channel") is None,
             f"{key} variant {variant['variant_ordinal']} has a non-None channel")
    by_language: dict[str, dict[str, str]] = {}
    templates = metadata.get("templates", [])
    _require(isinstance(templates, list) and templates,
             f"{key} variant {variant['variant_ordinal']} has empty templates")
    for template in templates:
        language = template.get("language")
        relation = template.get("relation")
        pattern = template.get("pattern")
        _require(isinstance(language, str) and isinstance(relation, str)
                 and isinstance(pattern, str),
                 f"{key} template record is malformed")
        by_language.setdefault(language, {})[relation] = pattern
    _require(set(by_language.get("en", {})) == set(by_language.get("zh", {})),
             f"{key} variant {variant['variant_ordinal']} case {case_id!r} "
             "has an en/zh relation parity mismatch")
    records = []
    for relation in sorted(by_language["en"]):
        records.append({
            "locator": {
                "key": key,
                "variant_ordinal": variant["variant_ordinal"],
                "case_id": case_id,
                "relation": relation,
            },
            "pattern_en": by_language["en"][relation],
            "pattern_zh": by_language["zh"][relation],
            "relation": relation,
            "sensory": metadata["sensory"],
            "channel": metadata["channel"],
            "frame": variant["frame"],
            "slot_schema": variant["slot_schema"],
            "binding": variant["binding"],
            "materialization_policy": policy,
        })
    return records


def _structured_templates(entry: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract per-variant zh/en template records from a catalog entry.

    CASE_MAP/RECURSIVE_CASE_MAP variants materialize through
    ``materialization_cases`` (locator carries the case_id); every other
    policy materializes from ``line_metadata`` (locator case_id is "root").
    """
    key = entry["canonical_key"]
    records: list[dict[str, Any]] = []
    for variant in entry["variants"]:
        policy = variant["materialization_policy"]
        cases = variant.get("materialization_cases", [])
        metadata_items = variant.get("line_metadata", [])
        if policy in CASE_POLICIES:
            _require(bool(cases),
                     f"{key} variant {variant['variant_ordinal']} policy {policy} "
                     "has no materialization_cases")
            for case in sorted(cases, key=lambda item: str(item.get("case_id", ""))):
                case_id = str(case.get("case_id", ""))
                _require(bool(case_id),
                         f"{key} variant {variant['variant_ordinal']} has an empty case_id")
                for metadata in case.get("line_metadata", []):
                    records.extend(_template_records(
                        key, variant, case_id, metadata, policy))
        else:
            _require(not cases,
                     f"{key} variant {variant['variant_ordinal']} policy {policy} "
                     "unexpectedly has materialization_cases")
            for metadata in metadata_items:
                records.extend(_template_records(
                    key, variant, "root", metadata, policy))
    return records


def _route_for(entry_mode: str, variants: list[dict[str, Any]]) -> str:
    if entry_mode == "CANDIDATE":
        first = variants[0]
        if first.get("english_snapshot") == "__NONE" \
                or ".suppress.v1" in first.get("stable_id", ""):
            return "SUPPRESSED"
        return "STRUCTURED"
    return "LEGACY"


def _catalog_binding(
    manifest: dict[str, Any], expected_keys: set[str], label: str,
) -> dict[str, dict[str, Any]]:
    by_key = {entry["canonical_key"]: entry for entry in manifest["entries"]}
    _require(set(by_key) == set(expected_keys),
             f"{label} catalog key set mismatch")
    binding: dict[str, dict[str, Any]] = {}
    for key in sorted(expected_keys):
        entry = by_key[key]
        mode = entry.get("mode")
        _require(mode in ENTRY_MODES,
                 f"{label} {key!r} has unknown entry mode {mode!r}")
        variants = entry.get("variants")
        _require(isinstance(variants, list) and variants,
                 f"{label} {key!r} has no variants")
        ordinals = [variant.get("variant_ordinal") for variant in variants]
        _require(all(_is_int(ordinal) for ordinal in ordinals)
                 and ordinals == list(range(len(variants))),
                 f"{label} {key!r} variant ordinals must be contiguous from zero")
        policies = []
        for variant in variants:
            policy = variant.get("materialization_policy")
            _require(policy in POLICIES,
                     f"{label} {key!r} has unknown materialization policy {policy!r}")
            policies.append(policy)
        binding[key] = {
            "entry_mode": mode,
            "primary_policy": policies[0],
            "policies": policies,
            "variants": variants,
        }
    return binding


def _identity_entry(
    key: str, catalog: dict[str, Any], templates: list[dict[str, Any]],
    legacy: dict[str, Any], unreachable: set[str],
) -> dict[str, Any]:
    route = _route_for(catalog["entry_mode"], catalog["variants"])
    return {
        "identity": f"monspell:{key}",
        "key": key,
        "route": route,
        "entry_mode": catalog["entry_mode"],
        "primary_materialization_policy": catalog["primary_policy"],
        "policies": catalog["policies"],
        "runtime_evidence": key not in unreachable,
        "production_zh_source": PRODUCTION_ZH_SOURCE[route],
        "fallback_zh_source": "zh/monspell.txt" if route == "STRUCTURED" else None,
        "structured_templates": templates if route == "STRUCTURED" else [],
        "legacy_variants": legacy["variants"],
        "unpaired_zh_variants": legacy["unpaired_zh_variants"],
        "source_lines": {
            "english": legacy["english_source_line"],
            "chinese": legacy["chinese_source_line"],
        },
    }


def _expected_evidence_locations(entry: dict[str, Any]) -> list[str]:
    en_source = (
        f"crawl-ref/source/dat/database/monspell.txt:"
        f"{entry['source_lines']['english']}"
    )
    zh_source = (
        f"crawl-ref/source/dat/database/zh/monspell.txt:"
        f"{entry['source_lines']['chinese']}"
    )
    route = entry["route"]
    if route == "STRUCTURED":
        return [
            en_source, zh_source,
            "crawl-ref/source/fork-message-overlay.cc:1704",
            "crawl-ref/source/fork-message-overlay.cc:1676",
            "crawl-ref/source/mon-cast.cc:9291",
            "crawl-ref/source/fork-message-overlay.cc:1748",
            "crawl-ref/source/fork-message-overlay.cc:1779",
            "crawl-ref/source/fork-message-overlay.cc:2400",
        ]
    if route == "LEGACY":
        return [
            en_source, zh_source,
            "crawl-ref/source/database.cc:2307",
            "crawl-ref/source/fork-message-overlay.cc:1704",
            "crawl-ref/source/fork-message-overlay.cc:1676",
        ]
    return [
        en_source,
        "crawl-ref/source/fork-message-overlay.cc:1704",
        "crawl-ref/source/fork-message-overlay.cc:1676",
    ]


def _expected_production_facts(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "structured_template_count": len(entry["structured_templates"]),
        "structured_relations": sorted({
            template["relation"]
            for template in entry["structured_templates"]
        }),
        "legacy_variant_count": len(entry["legacy_variants"]),
        "weights": [variant["weight"] for variant in entry["legacy_variants"]],
        "control_prefixes": [
            variant["control_prefix"] for variant in entry["legacy_variants"]
        ],
        "runtime_tokens": [
            variant["runtime_tokens"] for variant in entry["legacy_variants"]
        ],
        "materialization_policies": entry["policies"],
    }


def _current_structured_zh(entry: dict[str, Any]) -> list[dict[str, Any]]:
    return [{
        "locator": template["locator"],
        "pattern_en": template["pattern_en"],
        "pattern_zh": template["pattern_zh"],
        "relation": template["relation"],
        "materialization_policy": template["materialization_policy"],
    } for template in entry["structured_templates"]]


def _aggregate(conclusions: list[str]) -> str:
    if "retranslate" in conclusions:
        return "retranslate"
    if "adjust" in conclusions:
        return "adjust"
    for conclusion in DEFER_CONCLUSIONS:
        if conclusion in conclusions:
            return conclusion
    return "keep"


def _validate_deferral(record: dict[str, Any], context: str) -> None:
    conclusion = record.get("terminal_conclusion")
    if conclusion in DEFER_CONCLUSIONS:
        for field in ("deferral_owner", "deferral_reason", "reentry_trigger"):
            _require(_nonempty_string(record.get(field)),
                     f"{context} deferred conclusion requires {field}")
    else:
        for field in ("deferral_owner", "deferral_reason"):
            _require(record.get(field) is None,
                     f"{context} non-deferred conclusion forbids {field}")


def _validate_card(
    card: dict[str, Any], inventory: dict[str, Any], entry: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> None:
    identity = entry["identity"]
    route = entry["route"]
    _require_exact_fields(card, CARD_FIELDS, identity)
    _require(card["identity"] == identity, f"{identity} identity mismatch")
    _require(card["key"] == entry["key"], f"{identity} key mismatch")
    _require(card["route"] == route, f"{identity} route mismatch")
    _require(card["entry_mode"] == entry["entry_mode"],
             f"{identity} entry_mode mismatch")
    _require(card["primary_materialization_policy"]
             == entry["primary_materialization_policy"],
             f"{identity} primary_materialization_policy mismatch")
    _require(card["runtime_evidence"] == entry["runtime_evidence"],
             f"{identity} runtime_evidence mismatch")
    _require(card["production_zh_source"] == entry["production_zh_source"],
             f"{identity} production_zh_source mismatch")
    _require(card["fallback_zh_source"] == entry["fallback_zh_source"],
             f"{identity} fallback_zh_source mismatch")
    conclusion = card["terminal_conclusion"]
    _require(conclusion in TERMINAL_CONCLUSIONS,
             f"{identity} has nonterminal conclusion {conclusion!r}")
    _require(card["confidence"] in CONFIDENCE_LEVELS,
             f"{identity} confidence mismatch")
    _require(card["lifecycle"] == FROZEN_LIFECYCLE[route],
             f"{identity} lifecycle mismatch")
    _require(card["actual_behavior"] == FROZEN_ACTUAL_BEHAVIOR[route],
             f"{identity} actual_behavior mismatch")
    _require(card["display_context"] == FROZEN_DISPLAY_CONTEXT[route],
             f"{identity} display_context mismatch")
    _require(card["consumer"] == FROZEN_CONSUMER,
             f"{identity} consumer mismatch")
    _require(card["producers"] == FROZEN_PRODUCERS,
             f"{identity} producers mismatch")
    _require(card["dependency_group"]
             == f"{entry['key']} 怪物施法消息路由与本地化",
             f"{identity} dependency_group mismatch")
    _require(card["glossary_authority"] == (
        f"{inventory['glossary']['path']}@{inventory['glossary']['sha256']}"
    ), f"{identity} glossary_authority mismatch")
    _require(card["evidence_locations"] == _expected_evidence_locations(entry),
             f"{identity} evidence_locations mismatch")
    _require(_nonempty_string(card["reentry_trigger"]),
             f"{identity} requires a nonempty reentry_trigger")
    alternatives = card["rejected_alternatives"]
    _require(
        isinstance(alternatives, list) and bool(alternatives)
        and all(_nonempty_string(alternative) for alternative in alternatives),
        f"{identity} rejected_alternatives must be a nonempty string array",
    )
    _require(_nonempty_string(card["reviewer_rationale"]),
             f"{identity} requires a nonempty reviewer_rationale")
    if not entry["runtime_evidence"]:
        _require(UNREACHABLE_RATIONALE_MARKER in card["reviewer_rationale"],
                 f"{identity} unreachable identity requires the phase0 "
                 "static-review rationale")
    _validate_deferral(card, identity)

    facts = card["production_facts"]
    _require(isinstance(facts, dict), f"{identity} production_facts must be an object")
    _require_exact_fields(facts, PRODUCTION_FACT_FIELDS,
                          f"{identity} production_facts")
    _require(facts == _expected_production_facts(entry),
             f"{identity} production_facts mismatch")

    current_chinese = [variant["chinese"] for variant in entry["legacy_variants"]]
    current_english = [variant["english"] for variant in entry["legacy_variants"]]
    _require(card["current_english"] == current_english,
             f"{identity} current_english mismatch")
    _require(card["current_chinese"] == current_chinese,
             f"{identity} current_chinese mismatch")
    current_structured = _current_structured_zh(entry)
    _require(card["current_structured_zh"] == current_structured,
             f"{identity} current_structured_zh mismatch")

    proposed = card["proposed_translation"]
    _require(
        isinstance(proposed, list)
        and len(proposed) == len(entry["legacy_variants"])
        and all(item is None or isinstance(item, str) for item in proposed),
        f"{identity} proposed_translation coverage mismatch",
    )
    proposed_structured = card["proposed_structured_zh"]
    _require(
        isinstance(proposed_structured, list)
        and len(proposed_structured) == len(entry["structured_templates"]),
        f"{identity} proposed_structured_zh coverage mismatch",
    )

    reviews = card["structured_template_reviews"]
    _require(
        isinstance(reviews, list)
        and len(reviews) == len(entry["structured_templates"]),
        f"{identity} structured_template_reviews coverage mismatch",
    )
    structured_conclusions: list[str] = []
    for template, review, proposal in zip(
        entry["structured_templates"], reviews, proposed_structured
    ):
        context = f"{identity} template {template['locator']!r}"
        _require(isinstance(review, dict) and isinstance(proposal, dict),
                 f"{context} review/proposal must be objects")
        review_conclusion = review.get("terminal_conclusion")
        expected_fields = (
            STRUCTURED_TEMPLATE_REVIEW_FIELDS | DEFERRAL_FIELDS
            if review_conclusion in DEFER_CONCLUSIONS
            else STRUCTURED_TEMPLATE_REVIEW_FIELDS
        )
        _require_exact_fields(review, expected_fields, context)
        _require(review_conclusion in TERMINAL_CONCLUSIONS,
                 f"{context} has nonterminal conclusion {review_conclusion!r}")
        for field in ("locator", "pattern_en", "relation", "sensory",
                      "materialization_policy"):
            _require(review[field] == template[field],
                     f"{context} {field} mismatch")
        _require(review["current_pattern_zh"] == template["pattern_zh"],
                 f"{context} current_pattern_zh mismatch")
        if review["materialization_policy"] in CASE_POLICIES:
            _require(review["locator"]["case_id"] != "root",
                     f"{context} case-map review must carry a case_id")
        for field, expected in (
            ("locator", template["locator"]),
            ("pattern_en", template["pattern_en"]),
            ("relation", template["relation"]),
            ("materialization_policy", template["materialization_policy"]),
        ):
            _require(proposal.get(field) == expected,
                     f"{context} proposed {field} mismatch")
        _require(proposal.get("pattern_zh") == review["proposed_pattern_zh"],
                 f"{context} proposed pattern_zh mismatch")
        _require(_nonempty_string(review["rationale"]),
                 f"{context} requires a rationale")
        if template["materialization_policy"] in CASE_POLICIES:
            _require(template["locator"]["case_id"] != "root",
                     f"{context} case-map template must carry a case_id")
        if review_conclusion == "keep":
            _require(review["proposed_pattern_zh"] == template["pattern_zh"],
                     f"{context} keep must preserve current ZH")
        elif review_conclusion in {"adjust", "retranslate"}:
            _require(review["proposed_pattern_zh"] != template["pattern_zh"],
                     f"{context} {review_conclusion} must change current ZH")
        else:
            _validate_deferral(review, context)
            _require(review["proposed_pattern_zh"] == template["pattern_zh"],
                     f"{context} deferred conclusion must preserve current ZH")
        structured_conclusions.append(review_conclusion)

    legacy_reviews = card["legacy_variant_reviews"]
    _require(
        isinstance(legacy_reviews, list)
        and len(legacy_reviews) == len(entry["legacy_variants"]),
        f"{identity} legacy_variant_reviews coverage mismatch",
    )
    legacy_conclusions: list[str] = []
    for variant, review, proposal in zip(
        entry["legacy_variants"], legacy_reviews, proposed
    ):
        ordinal = variant["locator"]["variant_ordinal"]
        context = f"{identity} legacy variant {ordinal}"
        _require(isinstance(review, dict), f"{context} review must be an object")
        review_conclusion = review.get("terminal_conclusion")
        expected_fields = (
            LEGACY_VARIANT_REVIEW_FIELDS | DEFERRAL_FIELDS
            if review_conclusion in DEFER_CONCLUSIONS
            else LEGACY_VARIANT_REVIEW_FIELDS
        )
        _require_exact_fields(review, expected_fields, context)
        _require(review_conclusion in TERMINAL_CONCLUSIONS,
                 f"{context} has nonterminal conclusion {review_conclusion!r}")
        _require(_is_int(review["variant_ordinal"])
                 and review["variant_ordinal"] == ordinal,
                 f"{context} variant_ordinal mismatch")
        _require(_is_int(review["weight"]) and review["weight"] == variant["weight"],
                 f"{context} weight mismatch")
        for field, expected in (
            ("control_prefix", variant["control_prefix"]),
            ("runtime_tokens", variant["runtime_tokens"]),
            ("english", variant["english"]),
            ("current_chinese", variant["chinese"]),
            ("proposed_translation", proposal),
        ):
            _require(review[field] == expected, f"{context} {field} mismatch")
        _require(review["fallback"] == (route != "LEGACY"),
                 f"{context} fallback mismatch")
        _require(_nonempty_string(review["rationale"]),
                 f"{context} requires a rationale")
        if variant["chinese"] is None:
            _require(review_conclusion == "keep" and proposal is None,
                     f"{context} unpaired EN variant must keep None")
        elif review_conclusion == "keep":
            _require(proposal == variant["chinese"],
                     f"{context} keep must preserve current Chinese")
        elif review_conclusion in {"adjust", "retranslate"}:
            _require(proposal != variant["chinese"],
                     f"{context} {review_conclusion} must change current Chinese")
        else:
            _validate_deferral(review, context)
            _require(proposal == variant["chinese"],
                     f"{context} deferred conclusion must preserve current Chinese")
        legacy_conclusions.append(review_conclusion)

    if route == "SUPPRESSED":
        _require(reviews == [],
                 f"{identity} suppressed identity forbids structured reviews")
        _require(proposed_structured == [],
                 f"{identity} suppressed identity forbids proposed_structured_zh")
        _require(conclusion == "keep",
                 f"{identity} suppressed identity must keep")
        _require(all(item == "keep" for item in legacy_conclusions),
                 f"{identity} suppressed legacy reviews must keep")
    elif route == "STRUCTURED":
        _require(all(item in {"keep", "adjust"} for item in legacy_conclusions),
                 f"{identity} fallback legacy reviews allow only keep or adjust")
        _require(conclusion == _aggregate(structured_conclusions),
                 f"{identity} structured conclusion aggregation mismatch")
        if conclusion == "retranslate":
            for review, item in zip(legacy_reviews, legacy_conclusions):
                if item == "adjust":
                    _require(LEGACY_SYNC_MARKER in review["rationale"],
                             f"{identity} legacy adjust on structured "
                             "retranslate must cite the sync marker")
    else:
        _require(reviews == [],
                 f"{identity} legacy identity forbids structured reviews")
        _require(proposed_structured == [],
                 f"{identity} legacy identity forbids proposed_structured_zh")
        _require(conclusion == _aggregate(legacy_conclusions),
                 f"{identity} legacy conclusion aggregation mismatch")

    if route == "LEGACY":
        production_current = current_chinese
        production_proposed = proposed
    else:
        production_current = current_structured
        production_proposed = proposed_structured
    if conclusion == "keep":
        _require(production_proposed == production_current,
                 f"{identity} keep must preserve the production proposal")
    elif conclusion in {"adjust", "retranslate"}:
        _require(production_proposed != production_current,
                 f"{identity} {conclusion} must change the production proposal")
    else:
        _require(production_proposed == production_current,
                 f"{identity} deferred conclusion must preserve the "
                 "production proposal")

    if candidate is not None:
        candidate_zh = [variant["chinese"]
                        for variant in candidate["legacy_variants"]]
        _require(proposed == candidate_zh,
                 f"{identity} proposal does not match candidate ZH dump")
        candidate_structured = {
            _locator_key(item["locator"]): item["pattern_zh"]
            for item in candidate["structured_zh"]
        }
        for item in proposed_structured:
            _require(
                item["pattern_zh"]
                == candidate_structured.get(_locator_key(item["locator"])),
                f"{identity} proposed structured zh does not match "
                "candidate manifest",
            )


def _locator_key(locator: dict[str, Any]) -> tuple[Any, ...]:
    return (
        locator["key"], locator["variant_ordinal"],
        locator["case_id"], locator["relation"],
    )


def _strict_block(path: Path) -> list[dict[str, Any]]:
    return shared._strict_block(path, STRICT_BEGIN, STRICT_END)


def validate_results(
    path: Path, inventory: dict[str, Any],
    candidate_entries: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    records = _strict_block(path)
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review evidence metadata/card coverage mismatch")
    metadata, cards = records[0], records[1:]
    _require_exact_fields(metadata, METADATA_FIELDS, "review metadata")
    _require(metadata["baseline"] == inventory["baseline_ref"],
             "review metadata baseline mismatch")
    _require(metadata["glossary_sha256"] == inventory["glossary"]["sha256"],
             "review metadata glossary_sha256 mismatch")
    _require(_is_int(metadata["identity_count"])
             and metadata["identity_count"] == EXPECTED_IDENTITY_COUNT,
             "review metadata identity_count mismatch")
    _require(metadata["inventory_sha256"] == inventory["inventory_sha256"],
             "review metadata inventory_sha256 mismatch")

    expected_entries = {entry["identity"]: entry for entry in inventory["entries"]}
    seen: dict[str, dict[str, Any]] = {}
    for card in cards:
        _require(isinstance(card, dict), "review card must be an object")
        identity = card.get("identity")
        _require(isinstance(identity, str),
                 "review card identity must be a string")
        _require(identity not in seen, f"duplicate review card {identity!r}")
        seen[identity] = card
    _require(seen.keys() == expected_entries.keys(),
             f"review card identity set mismatch: expected "
             f"{sorted(expected_entries)!r}, got {sorted(seen)!r}")
    _require([card["identity"] for card in cards]
             == [entry["identity"] for entry in inventory["entries"]],
             "review card identity order mismatch")

    candidate_by_identity = (
        {entry["identity"]: entry for entry in candidate_entries}
        if candidate_entries is not None else {}
    )
    for entry in inventory["entries"]:
        _validate_card(seen[entry["identity"]], inventory, entry,
                       candidate_by_identity.get(entry["identity"]))
    return {"metadata": metadata, "cards": cards}


def build_inventory(
    baseline_ref: str,
    english_path: Path,
    localized_path: Path,
    phase0_inventory_path: Path,
    manifest_path: Path,
    behavior_report_path: Path,
    candidate_anchor_path: Path,
    glossary_path: Path,
) -> dict[str, Any]:
    shared._validate_oid(baseline_ref, "baseline")
    en_dump, en_raw = shared._load_dump(english_path, "baseline EN", "database/")
    zh_dump, zh_raw = shared._load_dump(
        localized_path, "baseline ZH", "database/zh/"
    )
    shared._require_scoped_derivation(
        en_dump, shared._derive_scoped_dump(
            baseline_ref, "database/", "baseline EN",
            source_basename=SOURCE_BASENAME,
        ), "baseline EN", source_basename=SOURCE_BASENAME,
    )
    shared._require_scoped_derivation(
        zh_dump, shared._derive_scoped_dump(
            baseline_ref, "database/zh/", "baseline ZH",
            source_basename=SOURCE_BASENAME,
        ), "baseline ZH", source_basename=SOURCE_BASENAME,
    )

    phase0 = _load_json(phase0_inventory_path, "phase0 inventory")
    _require(_is_int(phase0.get("schema_version"))
             and phase0["schema_version"] == PHASE0_SCHEMA_VERSION,
             "phase0 inventory schema_version mismatch")
    _require(phase0.get("speakdb_directory") == "database/",
             "phase0 inventory speakdb_directory must be 'database/'")
    try:
        recomputed = build_phase0_inventory(en_dump)
    except ArtifactError as exc:
        raise InventoryError(f"baseline EN phase0 rebuild failed: {exc}") from exc
    _require(recomputed["semantic_fingerprint"] == EXPECTED_SEMANTIC_FINGERPRINT,
             "baseline EN semantic fingerprint drifted from the frozen value")
    _require(phase0["semantic_fingerprint"] == EXPECTED_SEMANTIC_FINGERPRINT,
             "phase0 inventory semantic_fingerprint mismatch")
    _require(phase0["source_fingerprint"] == EXPECTED_SOURCE_FINGERPRINT
             and recomputed["source_fingerprint"] == EXPECTED_SOURCE_FINGERPRINT,
             "phase0 inventory source_fingerprint mismatch")
    _require(recomputed["summary"] == phase0["summary"],
             "phase0 inventory summary does not match the EN dump rebuild")
    expected_keys = {entry["key"] for entry in phase0["entries"]}
    _require(len(expected_keys) == EXPECTED_IDENTITY_COUNT,
             "phase0 inventory identity count mismatch")
    _require(phase0["summary"]["monspell_keys"] == EXPECTED_IDENTITY_COUNT,
             "phase0 inventory monspell_keys mismatch")

    try:
        manifest = load_manifest(manifest_path)
    except ManifestError as exc:
        raise InventoryError(f"cannot load manifest {manifest_path}: {exc}") from exc
    _require(manifest.get("domain") == DOMAIN,
             "manifest domain must be 'monspell'")
    _require(manifest.get("supported_languages") == ["en", "zh"],
             "manifest supported_languages mismatch")
    _require(manifest.get("inventory_semantic_fingerprint")
             == EXPECTED_SEMANTIC_FINGERPRINT,
             "manifest inventory_semantic_fingerprint mismatch")

    report = _load_json(behavior_report_path, "behavior report")
    _require(report.get("domain") == DOMAIN,
             "behavior report domain must be 'monspell'")
    _require(report.get("phase2_ready") is True,
             "behavior report phase2_ready must be true")
    _require(report.get("phase2_blockers") == [],
             "behavior report phase2_blockers must be empty")
    coverage = report.get("coverage", {})
    _require(coverage.get("catalog_coverage_complete") is True,
             "behavior report catalog_coverage_complete must be true")
    _require(coverage.get("en_zh_behavior_parity_proven") is True,
             "behavior report en_zh_behavior_parity_proven must be true")
    universe = report.get("universe", {})
    _require(universe.get("candidate_key_containment_proven") is True,
             "behavior report candidate_key_containment_proven must be true")
    for field in ("locale_presence_mismatch", "locale_behavior_mismatch",
                  "locale_behavior_inconclusive"):
        _require(report.get(field) == [],
                 f"behavior report {field} must be empty")
    _require(universe.get("inventory_root_count") == EXPECTED_IDENTITY_COUNT,
             "behavior report inventory_root_count mismatch")
    reachable = set(universe.get("runtime_roots", []))
    unreachable = set(universe.get("inventory_unreachable_roots", []))
    _require(len(reachable) == EXPECTED_REACHABLE_COUNT,
             "behavior report reachable root count mismatch")
    _require(len(unreachable) == EXPECTED_UNREACHABLE_COUNT,
             "behavior report unreachable root count mismatch")
    _require(reachable.isdisjoint(unreachable),
             "behavior report reachable/unreachable roots overlap")
    hits = report.get("candidate_lookup", {})
    _require(hits.get("en", {}).get("hit_count") == EXPECTED_REACHABLE_COUNT
             and hits.get("zh", {}).get("hit_count") == EXPECTED_REACHABLE_COUNT,
             "behavior report candidate lookup hit counts mismatch")
    _require(report["inputs"]["inventory"]["semantic_fingerprint"]
             == EXPECTED_SEMANTIC_FINGERPRINT,
             "behavior report inventory semantic fingerprint binding mismatch")

    anchor = _load_json(candidate_anchor_path, "candidate anchor")
    _require(_is_int(anchor.get("schema_version"))
             and anchor["schema_version"] == PHASE0_SCHEMA_VERSION,
             "candidate anchor schema_version mismatch")
    _require(anchor.get("domain") == ANCHOR_DOMAIN,
             "candidate anchor domain mismatch")
    _require(anchor.get("artifact_sha256") == EXPECTED_CANDIDATE_ANCHOR_SHA256,
             "candidate anchor artifact_sha256 mismatch")
    _require(report["inputs"]["candidate_anchor"]["artifact_sha256"]
             == EXPECTED_CANDIDATE_ANCHOR_SHA256,
             "behavior report candidate anchor binding mismatch")

    catalog = _catalog_binding(manifest, expected_keys, "baseline manifest")
    _require(reachable | unreachable == set(expected_keys),
             "behavior report reachability partition does not cover the catalog")
    _require(len(catalog) == EXPECTED_IDENTITY_COUNT,
             "catalog identity count mismatch")
    mode_counts: dict[str, int] = {}
    route_counts: dict[str, int] = {}
    primary_counts: dict[str, int] = {}
    mixed: dict[str, list[str]] = {}
    for key, binding in catalog.items():
        mode_counts[binding["entry_mode"]] = mode_counts.get(
            binding["entry_mode"], 0) + 1
        primary_counts[binding["primary_policy"]] = primary_counts.get(
            binding["primary_policy"], 0) + 1
        if len(set(binding["policies"])) > 1:
            mixed[key] = binding["policies"]
        route = _route_for(binding["entry_mode"], binding["variants"])
        route_counts[route] = route_counts.get(route, 0) + 1
    _require(mode_counts == EXPECTED_MODE_COUNTS,
             f"catalog entry mode counts mismatch: {mode_counts!r}")
    suppressed_keys = {
        key for key, binding in catalog.items()
        if _route_for(binding["entry_mode"], binding["variants"]) == "SUPPRESSED"
    }
    _require(suppressed_keys == EXPECTED_SUPPRESSED_KEYS,
             "catalog suppressed key set mismatch")
    _require(route_counts == EXPECTED_ROUTE_COUNTS,
             f"catalog route counts mismatch: {route_counts!r}")
    _require(primary_counts == EXPECTED_PRIMARY_POLICY_COUNTS,
             f"catalog primary policy counts mismatch: {primary_counts!r}")
    _require(mixed == EXPECTED_MIXED_POLICY_KEYS,
             f"catalog mixed-policy keys mismatch: {mixed!r}")

    templates_by_key: dict[str, list[dict[str, Any]]] = {}
    no_zh_keys: set[str] = set()
    relation_counts: dict[str, int] = {}
    line_metadata_relation_counts: dict[str, int] = {}
    case_relation_counts: dict[str, int] = {}
    sensory_counts: dict[str, int] = {}
    for key, binding in catalog.items():
        templates = _structured_templates({
            "canonical_key": key,
            "variants": binding["variants"],
        })
        templates_by_key[key] = templates
        if not templates:
            no_zh_keys.add(key)
        for template in templates:
            relation_counts[template["relation"]] = relation_counts.get(
                template["relation"], 0) + 1
            if template["locator"]["case_id"] == "root":
                line_metadata_relation_counts[template["relation"]] = (
                    line_metadata_relation_counts.get(template["relation"], 0) + 1
                )
            else:
                case_relation_counts[template["relation"]] = (
                    case_relation_counts.get(template["relation"], 0) + 1
                )
        # Sensory counts are per line_metadata item (a multi-relation item
        # carries one sensory), matching the frozen PLAIN/VISUAL distribution.
        for variant in binding["variants"]:
            metadata_items = variant.get("line_metadata", [])
            if variant.get("materialization_cases"):
                metadata_items = [
                    item
                    for case in variant["materialization_cases"]
                    for item in case.get("line_metadata", [])
                ]
            for metadata in metadata_items:
                sensory_counts[metadata["sensory"]] = sensory_counts.get(
                    metadata["sensory"], 0) + 1
    _require(sum(len(templates) for templates in templates_by_key.values())
             == EXPECTED_STRUCTURED_TEMPLATE_COUNT,
             "catalog structured zh template count mismatch")
    _require(relation_counts == EXPECTED_STRUCTURED_RELATION_COUNTS,
             f"catalog structured relation counts mismatch: {relation_counts!r}")
    _require(line_metadata_relation_counts == EXPECTED_LINE_METADATA_RELATION_COUNTS,
             f"catalog line_metadata relation counts mismatch: "
             f"{line_metadata_relation_counts!r}")
    _require(case_relation_counts == EXPECTED_CASE_RELATION_COUNTS,
             f"catalog materialization_cases relation counts mismatch: "
             f"{case_relation_counts!r}")
    _require(sensory_counts == EXPECTED_SENSORY_COUNTS,
             f"catalog sensory counts mismatch: {sensory_counts!r}")
    _require(len(no_zh_keys) == EXPECTED_NO_ZH_ENTRY_COUNT,
             "catalog no-zh entry count mismatch")
    legacy_only_keys = {
        key for key, binding in catalog.items()
        if binding["entry_mode"] == "LEGACY_ONLY"
    }
    _require(no_zh_keys == legacy_only_keys | suppressed_keys,
             "catalog no-zh entries must be exactly LEGACY_ONLY plus suppressed")

    en_binding, en_rows = _dump_binding(
        en_dump, en_raw, "baseline EN", expected_keys
    )
    zh_binding, zh_rows = _dump_binding(
        zh_dump, zh_raw, "baseline ZH", expected_keys
    )
    legacy_entries = _paired_entries(en_rows, zh_rows, "baseline")
    legacy_by_key = {entry["key"]: entry for entry in legacy_entries}

    try:
        glossary_sha256 = _sha256(glossary_path.read_bytes())
    except OSError as exc:
        raise InventoryError(f"cannot read glossary {glossary_path}: {exc}") from exc

    entries = [
        _identity_entry(
            key, catalog[key], templates_by_key[key], legacy_by_key[key],
            unreachable,
        )
        for key in sorted(expected_keys)
    ]
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": SCOPE,
        "scope_sha256": _sha256(_canonical_json(SCOPE)),
        "glossary": {"path": "docs/glossary.md", "sha256": glossary_sha256},
        "dumps": {"english": en_binding, "localized": zh_binding},
        "phase0": {
            "semantic_fingerprint": phase0["semantic_fingerprint"],
            "source_fingerprint": phase0["source_fingerprint"],
            "summary": phase0["summary"],
        },
        "manifest": {
            "inventory_semantic_fingerprint":
                manifest["inventory_semantic_fingerprint"],
            "domain": manifest["domain"],
            "supported_languages": manifest["supported_languages"],
            "fragment_glob": manifest.get("fragment_glob"),
        },
        "behavior_report": {
            "phase2_ready": True,
            "phase2_blockers": [],
            "reachable_root_count": len(reachable),
            "unreachable_roots": sorted(unreachable),
        },
        "candidate_anchor": {
            "artifact_sha256": anchor["artifact_sha256"],
        },
        "entries": entries,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _git_fragment_glob(
    oid: str, manifest_git_dir: PurePosixPath, fragment_glob: str, label: str,
) -> list[PurePosixPath]:
    path = PurePosixPath(fragment_glob)
    _require(not path.is_absolute() and ".." not in path.parts
             and all(part not in {"", "."} for part in path.parts),
             f"{label} fragment_glob must be a repository-relative pattern")
    pattern_name = path.name
    _require(bool(pattern_name) and "/" not in pattern_name,
             f"{label} fragment_glob has a malformed final pattern")
    directory = PurePosixPath(*path.parts[:-1]) if len(path.parts) > 1 \
        else PurePosixPath(".")
    _require(all(not any(character in part for character in "*?[")
                 for part in directory.parts),
             f"{label} fragment_glob directory part must be literal")
    tree_dir = manifest_git_dir / directory
    raw = shared._git_output(
        ["ls-tree", "-z", f"{oid}:{tree_dir.as_posix()}"],
        f"{label} fragment tree",
    )
    names: list[str] = []
    for record in raw.split(b"\0"):
        if not record:
            continue
        header, separator, encoded_name = record.partition(b"\t")
        fields = header.split(b" ")
        _require(separator == b"\t" and len(fields) == 3,
                 f"{label} has malformed Git tree evidence")
        mode, object_type, object_id = fields
        _require(object_type == b"blob" and mode in {b"100644", b"100755"},
                 f"{label} has unsupported tree object {record!r}")
        _require(bool(re.fullmatch(rb"[0-9a-f]{40}", object_id)),
                 f"{label} has malformed Git object id")
        name = shared._decode_utf8(encoded_name, label)
        _require(name not in {"", ".", ".."} and "/" not in name,
                 f"{label} has unsafe fragment name {name!r}")
        if fnmatch(name, pattern_name):
            names.append(name)
    names.sort()
    _require(bool(names), f"{label} fragment_glob matched no fragments")
    return [(directory / name) if len(path.parts) > 1
            else PurePosixPath(name) for name in names]


def _manifest_snapshot_at_oid(
    oid: str, manifest_path: Path, label: str,
) -> dict[str, Any]:
    """Reload the catalog header plus fragments from exact Git blobs."""
    repository = Path(__file__).resolve().parents[2]
    resolved = manifest_path.resolve()
    _require(resolved.is_relative_to(repository),
             f"{label} manifest escapes the repository")
    relative = PurePosixPath(resolved.relative_to(repository).as_posix())
    header_raw = shared._git_blob_at_oid(oid, relative.as_posix(), label)
    try:
        header = json.loads(shared._decode_utf8(header_raw, label))
    except json.JSONDecodeError as exc:
        raise InventoryError(f"{label} header is not valid JSON: {exc}") from exc
    _require(isinstance(header, dict), f"{label} header must be an object")
    fragments = header.get("fragments")
    fragment_glob = header.get("fragment_glob")
    _require((fragments is None) != (fragment_glob is None),
             f"{label} must use exactly one of fragments or fragment_glob")
    if fragment_glob is not None:
        _require(isinstance(fragment_glob, str) and fragment_glob,
                 f"{label} fragment_glob must be a non-empty string")
        fragment_names = _git_fragment_glob(oid, relative.parent, fragment_glob, label)
    else:
        _require(
            isinstance(fragments, list) and fragments
            and all(isinstance(item, str) and item for item in fragments)
            and len(set(fragments)) == len(fragments),
            f"{label} fragments must resolve to unique non-empty paths",
        )
        fragment_names = []
        for name in fragments:
            item = PurePosixPath(name)
            _require(
                not item.is_absolute()
                and all(part not in {"", ".", ".."} for part in item.parts),
                f"{label} has an unsafe fragment path {name!r}",
            )
            fragment_names.append(item)
    _require("entries" not in header and "tombstones" not in header,
             f"{label} fragment header must not contain entries or tombstones")
    catalog_order = header.get("catalog_order", [])
    _require(isinstance(catalog_order, list),
             f"{label} catalog_order must be a list")
    aggregate = {key: value for key, value in header.items()
                 if key not in {"fragments", "fragment_glob", "catalog_order"}}
    aggregate["entries"] = []
    aggregate["tombstones"] = []
    for name in fragment_names:
        git_path = (relative.parent / name).as_posix()
        raw = shared._git_blob_at_oid(oid, git_path, label)
        try:
            fragment = json.loads(shared._decode_utf8(raw, label))
        except json.JSONDecodeError as exc:
            raise InventoryError(f"{label} fragment {name!r} is not valid "
                                 f"JSON: {exc}") from exc
        _require(isinstance(fragment, dict)
                 and set(fragment) == {"entries", "tombstones"},
                 f"{label} fragment {name!r} must contain entries and tombstones only")
        _require(isinstance(fragment["entries"], list)
                 and isinstance(fragment["tombstones"], list),
                 f"{label} fragment {name!r} entries/tombstones must be lists")
        aggregate["entries"].extend(fragment["entries"])
        aggregate["tombstones"].extend(fragment["tombstones"])
    try:
        return _normalise_manifest(aggregate, catalog_order)
    except ManifestError as exc:
        raise InventoryError(f"{label} manifest normalization failed: {exc}") from exc


def add_candidate(
    inventory: dict[str, Any], candidate_ref: str, english_path: Path,
    localized_path: Path, manifest_path: Path,
) -> list[dict[str, Any]]:
    shared._require_candidate_commit(
        inventory["baseline_ref"], candidate_ref, exact_clean_checkout=True
    )
    expected_keys = {entry["key"] for entry in inventory["entries"]}
    en_dump, en_raw = shared._load_dump(english_path, "candidate EN", "database/")
    zh_dump, zh_raw = shared._load_dump(
        localized_path, "candidate ZH", "database/zh/"
    )
    shared._require_scoped_derivation(
        en_dump, shared._derive_scoped_dump(
            candidate_ref, "database/", "candidate EN",
            source_basename=SOURCE_BASENAME,
        ), "candidate EN", source_basename=SOURCE_BASENAME,
    )
    shared._require_scoped_derivation(
        zh_dump, shared._derive_scoped_dump(
            candidate_ref, "database/zh/", "candidate ZH",
            source_basename=SOURCE_BASENAME,
        ), "candidate ZH", source_basename=SOURCE_BASENAME,
    )
    en_binding, en_rows = _dump_binding(
        en_dump, en_raw, "candidate EN", expected_keys
    )
    zh_binding, zh_rows = _dump_binding(
        zh_dump, zh_raw, "candidate ZH", expected_keys
    )
    entries = _paired_entries(en_rows, zh_rows, "candidate")
    baseline_en = {
        entry["identity"]: [variant["english"]
                            for variant in entry["legacy_variants"]]
        for entry in inventory["entries"]
    }
    for entry in entries:
        _require(
            [variant["english"] for variant in entry["variants"]]
            == baseline_en[entry["identity"]],
            f"candidate English drift for {entry['identity']}",
        )

    candidate_manifest = _manifest_snapshot_at_oid(
        candidate_ref, manifest_path, "candidate manifest"
    )
    _require(candidate_manifest.get("domain") == DOMAIN,
             "candidate manifest domain must be 'monspell'")
    _require(candidate_manifest.get("inventory_semantic_fingerprint")
             == EXPECTED_SEMANTIC_FINGERPRINT,
             "candidate manifest inventory_semantic_fingerprint mismatch")
    candidate_keys = {
        entry["canonical_key"] for entry in candidate_manifest["entries"]
    }
    _require(candidate_keys == set(expected_keys),
             "candidate manifest key set mismatch")
    candidate_by_key = {
        entry["canonical_key"]: entry for entry in candidate_manifest["entries"]
    }
    structured_by_identity: dict[str, list[dict[str, Any]]] = {}
    for entry in inventory["entries"]:
        candidate_templates = _structured_templates(candidate_by_key[entry["key"]])
        # The ledger models the structured side only for STRUCTURED (and
        # trivially empty SUPPRESSED) routes; CLOSURE_ONLY catalog templates
        # are facts, not production templates, so their locators are not
        # compared against the modeled side.
        if entry["route"] != "LEGACY":
            _require(
                [template["locator"] for template in candidate_templates]
                == [template["locator"] for template in entry["structured_templates"]],
                f"candidate structured locator drift for {entry['identity']}",
            )
        structured_by_identity[entry["identity"]] = candidate_templates

    candidate_legacy_by_identity = {
        entry["identity"]: entry["variants"] for entry in entries
    }
    candidate = {
        "candidate_ref": candidate_ref,
        "dumps": {"english": en_binding, "localized": zh_binding},
        "entries": [{
            "identity": entry["identity"],
            "legacy_variants": [
                {"locator": variant["locator"], "chinese": variant["chinese"]}
                for variant in candidate_legacy_by_identity[entry["identity"]]
            ],
            "structured_zh": [
                {"locator": template["locator"], "pattern_zh": template["pattern_zh"]}
                for template in structured_by_identity[entry["identity"]]
            ] if entry["route"] == "STRUCTURED" else [],
        } for entry in inventory["entries"]],
    }
    candidate["candidate_sha256"] = _sha256(_canonical_json(candidate))
    inventory["candidate"] = candidate
    return candidate["entries"]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--english-dump", required=True, type=Path)
    parser.add_argument("--localized-dump", required=True, type=Path)
    parser.add_argument("--phase0-inventory", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--behavior-report", required=True, type=Path)
    parser.add_argument("--candidate-anchor", required=True, type=Path)
    parser.add_argument("--inventory-output", required=True, type=Path)
    parser.add_argument("--review-results", type=Path)
    parser.add_argument("--candidate-ref")
    parser.add_argument("--candidate-english-dump", type=Path)
    parser.add_argument("--candidate-localized-dump", type=Path)
    parser.add_argument(
        "--glossary", type=Path,
        default=Path(__file__).resolve().parents[2] / "docs/glossary.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    candidate_values = (
        args.candidate_ref, args.candidate_english_dump,
        args.candidate_localized_dump,
    )
    if any(value is not None for value in candidate_values):
        _require(all(value is not None for value in candidate_values),
                 "candidate ref and both candidate dumps must be supplied together")
        _require(args.review_results is not None,
                 "candidate validation requires --review-results")
    inventory = build_inventory(
        args.baseline_ref, args.english_dump, args.localized_dump,
        args.phase0_inventory, args.manifest, args.behavior_report,
        args.candidate_anchor, args.glossary,
    )
    candidate_entries = None
    if args.candidate_ref is not None:
        candidate_entries = add_candidate(
            inventory, args.candidate_ref, args.candidate_english_dump,
            args.candidate_localized_dump, args.manifest,
        )
    if args.review_results is not None:
        inventory["review_evidence"] = validate_results(
            args.review_results, inventory, candidate_entries
        )
    shared._safe_output(args.inventory_output, inventory)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
