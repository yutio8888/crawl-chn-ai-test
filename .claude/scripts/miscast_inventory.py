#!/usr/bin/env python3
"""Build and audit the Issue #56 miscast inventory from production dumps.

The production dump remains the artifact under review.  This narrow entry
reuses ``monflee_inventory`` for exact-Git source discovery, TextDB parsing,
weighted-variant derivation, artifact validation, hashing, and safe output.
Only miscast's consumer-specific invariants and strict ledger schema live here.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import monflee_inventory as shared


SCHEMA_VERSION = 1
SOURCE_BASENAME = "miscast.txt"
STRICT_BEGIN = "<!-- BEGIN STRICT MISCAST REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT MISCAST REVIEW EVIDENCE v1 -->"
SCHOOLS = (
    "conjuration", "hexes", "summoning", "necromancy", "translocation",
    "fire", "ice", "air", "earth", "alchemy", "forgecraft",
)
TARGET_ROLES = ("player", "monster", "unseen")
EXPECTED_KEYS = tuple(
    f"{school} miscast {target}"
    for school in SCHOOLS
    for target in TARGET_ROLES
)
EXPECTED_IDENTITY_COUNT = 33
EXPECTED_VARIANT_COUNT = 193
EXPECTED_CHOICE_SITE_COUNT = 25
RECURSIVE_TOKENS = (
    "@any_colour@", "@any_colour_pattern@", "@any_glowing_colour@",
)
CALLER_TOKENS = (
    "@The_monster@", "@The_monster_possessive@", "@hand_conj@",
    "@hands@", "@possessive@", "@the_monster@",
    "@the_monster_possessive@",
)
ALLOWED_TOKENS = set(RECURSIVE_TOKENS) | set(CALLER_TOKENS)
GRAMMAR_EXCEPTION = {
    "english_only_token": "@hand_conj@",
    "identity": "miscast:ice miscast player",
    "reason": (
        "English singular/plural verb inflection; the ZH template intentionally "
        "omits it and _do_msg only replaces tokens that are present."
    ),
    "variant_ordinal": 2,
}
BODY_NEUTRAL_LOCATORS = {
    ("hexes miscast monster", 4),
    ("hexes miscast monster", 5),
    ("fire miscast monster", 2),
    ("ice miscast monster", 1),
    ("alchemy miscast monster", 6),
}
DAMAGING_SCHOOLS = {
    "conjuration", "necromancy", "fire", "ice", "air", "earth",
}
WEAK_PUNCTUATION = "attack_strength_punctuation(0): '.'."
DAMAGE_PUNCTUATION = (
    "attack_strength_punctuation(final_damage): '.' for weak/zero damage, "
    "otherwise one or more '!'."
)
UNSEEN_GATE = (
    "you.see_cell(target.pos()) must be true; unseen means target entity is "
    "not visible, not that the cell is unseen."
)
BODY_POSTPROCESSING = (
    "The five EN body/skin propositions are rendered in ZH as 周身/外表; "
    "candidate output does not contain 的身体/的皮肤, so English literal "
    "cleanup is not required."
)
CONSUMER = {
    "final_punctuation": "crawl-ref/source/spl-miscast.cc:72",
    "hand_substitution": "crawl-ref/source/spl-miscast.cc:49",
    "lookup_and_visibility": "crawl-ref/source/spl-miscast.cc:34",
    "monster_and_choice_materialization": "crawl-ref/source/spl-miscast.cc:59",
    "speakdb_loader": "crawl-ref/source/database.cc:120",
}
PRODUCERS = [{
    "location": "crawl-ref/source/spl-miscast.cc:39",
    "mode": "spelltype_long_name_en school + target visibility/type",
}]
DISPLAY_CONTEXTS = {
    "player": "目标是玩家；仅当玩家能看见目标格时显示 player key。",
    "monster": "目标为玩家可见怪物；仅当玩家能看见目标格时显示 monster key，并展开怪物槽。",
    "unseen": "目标位于可见格但实体不可见；选择 unseen key；若目标格不可见则完全不显示。",
}
DEPENDENCY_GROUPS = {
    "conjuration": "咒法系：能量冲击、爆炸与直接伤害",
    "hexes": "诅咒系：感官扰动、颜色与减速",
    "summoning": "召唤系：异象与无名恐怖召唤",
    "necromancy": "死灵术：恐惧、腐朽与负能量",
    "translocation": "传送系：空间扭曲与随机选择语法",
    "fire": "火焰魔法：余烬、热流与烈焰",
    "ice": "寒冰魔法：寒冷、冰霜与语言专用屈折",
    "air": "空气魔法：气流、火花与放电",
    "earth": "大地魔法：沙砾、岩石与碎片",
    "alchemy": "炼金术：物质、颜色、烟尘与外表变化",
    "forgecraft": "锻造术：结构完整性、金属与腐蚀",
}
SCHOOL_EFFECTS = {
    "conjuration": "BEAM_MMISSILE 魔法伤害；消息标点使用抗性调整后的伤害。",
    "hexes": "无直接消息伤害；消息后施加 slow_down，标点固定为句号。",
    "summoning": "无直接消息伤害；随后尝试在目标处生成敌对无名恐怖，标点固定为句号。",
    "necromancy": "BEAM_NEG 负能量伤害；消息标点使用抗性调整后的伤害。",
    "translocation": "无直接消息伤害；玩家获得维度锚定/无动量，怪物获得维度锚定，标点固定为句号。",
    "fire": "BEAM_FIRE 火焰伤害；消息标点使用抗性调整后的伤害。",
    "ice": "BEAM_COLD 寒冷伤害；消息标点使用抗性调整后的伤害。",
    "air": "BEAM_ELECTRICITY 电击伤害；消息标点使用抗性调整后的伤害。",
    "earth": "三倍 AC 检定后的 BEAM_FRAG 物理碎片伤害；标点使用最终伤害。",
    "alchemy": "无直接消息伤害；随后施加中毒，消息标点固定为句号。",
    "forgecraft": "无直接消息伤害；随后施加腐蚀，消息标点固定为句号。",
}
ACTUAL_BEHAVIOR_PREFIX = (
    "_do_msg uses spelltype_long_name_en(which) plus player/monster/unseen to "
    "build the stable English key; getSpeakString performs production weighted "
    "selection. It replaces hand slots, then uses do_mon_str_replacements for "
    "monster targets or maybe_pick_random_substring for players. "
)
ACTUAL_BEHAVIOR_SUFFIX = (
    " The selected asset pattern contains no terminal punctuation; _do_msg "
    "appends it."
)
REENTRY_TRIGGER = (
    "英文或中文 TextDB source、production key/variant/weight/choice/token topology、"
    "_do_msg lookup/substitution/visibility/punctuation、school effect、body "
    "semantics、grammar exception 或 docs/glossary.md 权威发生变化时重新审阅。"
)
METADATA_FIELDS = {
    "baseline", "chinese_production_dump_sha256", "choice_site_count",
    "english_production_dump_sha256", "glossary_sha256",
    "grammar_exceptions", "identity_count", "terminal_conclusion_counts",
    "variant_count",
}
CARD_FIELDS = {
    "actual_behavior", "confidence", "consumer", "current_chinese",
    "current_english", "deferral_owner", "deferral_reason",
    "dependency_group", "display_context", "evidence_locations",
    "glossary_authority", "identity", "key", "lifecycle", "producers",
    "production_facts", "proposed_translation", "reentry_trigger",
    "rejected_alternatives", "reviewer_rationale", "terminal_conclusion",
    "variant_reviews",
}
PRODUCTION_FACT_FIELDS = {
    "body_skin_postprocessing", "choice_site_counts", "effective_provenance",
    "english_source", "final_punctuation", "localized_source", "parse_error",
    "runtime_tokens_chinese_baseline", "runtime_tokens_chinese_candidate",
    "runtime_tokens_english", "source_history_length", "target_role",
    "unseen_gate", "variant_count", "weights",
}
VARIANT_FIELDS = {
    "body_skin_strategy", "current_chinese", "english",
    "final_message_punctuation", "grammar_exception", "proposal_type",
    "proposed_translation", "rationale", "runtime_tokens", "selection_sites",
    "terminal_conclusion", "variant_ordinal", "weight",
}
TERMINAL_CONCLUSIONS = {"keep", "adjust", "retranslate"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}


InventoryError = shared.InventoryError
_require = shared._require
_sha256 = shared._sha256
_canonical_json = shared._canonical_json
_runtime_tokens = shared._runtime_tokens
_is_int = shared._is_int
_nonempty_string = shared._nonempty_string
_require_exact_fields = shared._require_exact_fields


def _selection_sites(pattern: str) -> list[dict[str, Any]]:
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
        nested = pattern.find("[", opening + 1, closing)
        _require(nested < 0,
                 f"nested random substring marker at offset {nested}")
        contents = pattern[opening + 1:closing]
        raw = pattern[opening:closing + 1]
        alternatives = contents.split("|")
        _require(len(alternatives) >= 2,
                 f"random substring at offset {opening} has no choice")
        sites.append({
            "raw": raw,
            "alternatives": alternatives,
            "alternative_count": len(alternatives),
        })
        position = closing + 1
    trailing = pattern.find("]", position)
    _require(trailing < 0,
             f"unbalanced random substring marker at offset {trailing}")
    return sites


def _source_expectations(directory: str) -> tuple[str, int, str, int]:
    if directory == "database/":
        return (
            "database/miscast.txt", 9,
            "database/colourname.txt", 7,
        )
    return (
        "database/zh/miscast.txt", 9,
        "database/zh/colourname.txt", 1,
    )


def _dependency_binding(
    artifact: dict[str, Any], label: str,
) -> list[dict[str, Any]]:
    _miscast_source, _miscast_index, colour_source, colour_index = (
        _source_expectations(artifact["source_directory"])
    )
    entries = {entry["canonical_key"]: entry for entry in artifact["entries"]}
    dependencies = []
    for token in RECURSIVE_TOKENS:
        key = token[1:-1]
        _require(key in entries,
                 f"{label} recursive token {token} has no effective TextDB key")
        entry = entries[key]
        _require(entry["parse_error"] is None,
                 f"{label} recursive token {token} has a parse error")
        _require(not entry["body_empty"],
                 f"{label} recursive token {token} has an empty definition")
        _require(len(entry["source_history"]) == 1,
                 f"{label} recursive token {token} is overridden")
        provenance = entry["effective_provenance"]
        _require(
            provenance["source_name"] == colour_source
            and provenance["load_index"] == colour_index,
            f"{label} recursive token {token} is not effective from the exact "
            "colourname source/order",
        )
        dependencies.append({"token": token, "key": key,
                             "effective_provenance": provenance})
    for token in CALLER_TOKENS:
        _require(token[1:-1].lower() not in entries,
                 f"{label} caller token {token} unexpectedly resolves in SpeakDB")
    return dependencies


def _definition_line(source: str, key: str, label: str) -> int:
    matches = list(re.finditer(
        rf"(?m)^%%%%\n{re.escape(key)}\n", source
    ))
    _require(len(matches) == 1,
             f"{label} cannot bind a unique source line for {key!r}")
    return source.count("\n", 0, matches[0].start()) + 2


def _dump_binding(
    artifact: dict[str, Any], raw: bytes, label: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    expected_source, expected_index, _colour_source, _colour_index = (
        _source_expectations(artifact["source_directory"])
    )
    matching_sources = [
        source for source in artifact["sources"]
        if source["source_name"] == expected_source
    ]
    _require(len(matching_sources) == 1,
             f"{label} dump must contain exactly one {expected_source!r}")
    _require(matching_sources[0]["load_index"] == expected_index,
             f"{label} miscast source order must be index {expected_index}")
    source_snapshot = matching_sources[0]["normalized_utf8"]
    touching = [
        entry for entry in artifact["entries"]
        if any(item["source_name"] == expected_source
               for item in entry["source_history"])
    ]
    for entry in touching:
        key = entry["canonical_key"]
        _require(entry["parse_error"] is None,
                 f"{label} key {key!r} has parse error")
        _require(not entry["body_empty"],
                 f"{label} key {key!r} has an empty body")
        _require(len(entry["source_history"]) == 1,
                 f"{label} key {key!r} is overridden")
        provenance = entry["effective_provenance"]
        _require(
            provenance["source_name"] == expected_source
            and provenance["load_index"] == expected_index,
            f"{label} key {key!r} is not effective from exact miscast source/order",
        )

    actual_keys = {entry["canonical_key"] for entry in touching}
    _require(actual_keys == set(EXPECTED_KEYS),
             f"{label} miscast key set mismatch")
    by_ordinal = sorted(
        touching, key=lambda entry: entry["effective_provenance"]["definition_ordinal"]
    )
    actual_order = [entry["canonical_key"] for entry in by_ordinal]
    _require(actual_order == list(EXPECTED_KEYS),
             f"{label} miscast definition identity/order mismatch")

    rows = []
    for definition_ordinal, entry in enumerate(by_ordinal):
        _require(entry["effective_provenance"]["definition_ordinal"]
                 == definition_ordinal,
                 f"{label} definition ordinals are not contiguous from zero")
        variants = []
        for expected_ordinal, variant in enumerate(entry["variants"]):
            locator = variant["locator"]
            _require(
                locator == {
                    "canonical_key": entry["canonical_key"],
                    "variant_ordinal": expected_ordinal,
                },
                f"{label} duplicate, extra, or missing variant locator for "
                f"{entry['canonical_key']!r}",
            )
            pattern = variant["raw_pattern"]
            tokens = _runtime_tokens(pattern)
            unknown = [token for token in tokens if token not in ALLOWED_TOKENS]
            _require(not unknown,
                     f"{label} unknown runtime tokens {unknown!r}")
            _require(shared._control_prefix(pattern) is None,
                     f"{label} miscast patterns forbid control prefixes")
            _require(not re.search(r"[.!?。！？]\s*$", pattern),
                     f"{label} miscast pattern has terminal punctuation")
            variants.append({
                "locator": {"key": entry["canonical_key"],
                            "variant_ordinal": expected_ordinal},
                "weight": variant["weight"],
                "runtime_tokens": tokens,
                "selection_sites": _selection_sites(pattern),
                "raw_pattern": pattern,
            })
        rows.append({
            "key": entry["canonical_key"],
            "effective_provenance": entry["effective_provenance"],
            "source_line": _definition_line(
                source_snapshot, entry["canonical_key"], label
            ),
            "source_history_length": len(entry["source_history"]),
            "variants": variants,
        })

    _require(len(rows) == EXPECTED_IDENTITY_COUNT,
             f"{label} identity count must be {EXPECTED_IDENTITY_COUNT}")
    _require(sum(len(row["variants"]) for row in rows) == EXPECTED_VARIANT_COUNT,
             f"{label} variant count must be {EXPECTED_VARIANT_COUNT}")
    _require(
        sum(len(variant["selection_sites"])
            for row in rows for variant in row["variants"])
        == EXPECTED_CHOICE_SITE_COUNT,
        f"{label} choice-site count must be {EXPECTED_CHOICE_SITE_COUNT}",
    )
    binding = {
        "artifact_sha256": _sha256(raw),
        "database_name": artifact["database_name"],
        "source_directory": artifact["source_directory"],
        "source_snapshots": [{
            "source_name": source["source_name"],
            "load_index": source["load_index"],
            "normalized_utf8_sha256": _sha256(
                source["normalized_utf8"].encode("utf-8")
            ),
        } for source in artifact["sources"]],
        "effective_miscast_source": expected_source,
        "recursive_dependencies": _dependency_binding(artifact, label),
    }
    return binding, rows


def _expected_zh_tokens(key: str, ordinal: int, english: list[str]) -> list[str]:
    if (f"miscast:{key}", ordinal) == (
        GRAMMAR_EXCEPTION["identity"], GRAMMAR_EXCEPTION["variant_ordinal"]
    ):
        _require(english == ["@hands@", "@hand_conj@"],
                 "grammar exception English token shape drifted")
        return ["@hands@"]
    return english


def _pair_rows(
    en_rows: list[dict[str, Any]], zh_rows: list[dict[str, Any]], label: str,
) -> list[dict[str, Any]]:
    _require([row["key"] for row in en_rows] == [row["key"] for row in zh_rows],
             f"{label} EN/ZH identity order differs")
    entries = []
    for en, zh in zip(en_rows, zh_rows):
        key = en["key"]
        _require(len(en["variants"]) == len(zh["variants"]),
                 f"{label} variant count differs for {key!r}")
        variants = []
        for en_variant, zh_variant in zip(en["variants"], zh["variants"]):
            ordinal = en_variant["locator"]["variant_ordinal"]
            _require(en_variant["locator"] == zh_variant["locator"],
                     f"{label} variant locator differs for {key!r}")
            _require(en_variant["weight"] == zh_variant["weight"],
                     f"{label} weight/order differs for {key!r} variant {ordinal}")
            _require(
                [site["alternative_count"] for site in en_variant["selection_sites"]]
                == [site["alternative_count"]
                    for site in zh_variant["selection_sites"]],
                f"{label} choice topology differs for {key!r} variant {ordinal}",
            )
            expected_tokens = _expected_zh_tokens(
                key, ordinal, en_variant["runtime_tokens"]
            )
            _require(zh_variant["runtime_tokens"] == expected_tokens,
                     f"{label} token case/order/count differs for {key!r} "
                     f"variant {ordinal}")
            variants.append({
                "locator": en_variant["locator"],
                "weight": en_variant["weight"],
                "runtime_tokens_english": en_variant["runtime_tokens"],
                "runtime_tokens_chinese": zh_variant["runtime_tokens"],
                "selection_sites_english": en_variant["selection_sites"],
                "selection_sites_chinese": zh_variant["selection_sites"],
                "english": en_variant["raw_pattern"],
                "chinese": zh_variant["raw_pattern"],
            })
        entries.append({
            "identity": f"miscast:{key}",
            "key": key,
            "english_provenance": en["effective_provenance"],
            "chinese_provenance": zh["effective_provenance"],
            "english_source_line": en["source_line"],
            "chinese_source_line": zh["source_line"],
            "source_history_length": {
                "english": en["source_history_length"],
                "chinese": zh["source_history_length"],
            },
            "variants": variants,
        })
    return entries


def _load_bound_pair(
    ref: str, english_path: Path, localized_path: Path, phase: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    artifacts = {
        "english": (*shared._load_dump(
            english_path, f"{phase} EN", "database/"
        ), "database/", f"{phase} EN"),
        "localized": (*shared._load_dump(
            localized_path, f"{phase} ZH", "database/zh/"
        ), "database/zh/", f"{phase} ZH"),
    }
    rows = {}
    bindings = {}
    for language, (artifact, raw, directory, label) in artifacts.items():
        for source_basename in (SOURCE_BASENAME, "colourname.txt"):
            derived = shared._derive_scoped_dump(
                ref, directory, label, source_basename=source_basename
            )
            shared._require_scoped_derivation(
                artifact, derived, label, source_basename=source_basename
            )
        bindings[language], rows[language] = _dump_binding(
            artifact, raw, label
        )
    return bindings, _pair_rows(
        rows["english"], rows["localized"], phase
    )


def build_inventory(
    baseline_ref: str, english_path: Path, localized_path: Path,
    glossary_path: Path,
) -> dict[str, Any]:
    shared._validate_oid(baseline_ref, "baseline")
    bindings, entries = _load_bound_pair(
        baseline_ref, english_path, localized_path, "baseline"
    )
    try:
        glossary_sha256 = _sha256(glossary_path.read_bytes())
    except OSError as exc:
        raise InventoryError(f"cannot read glossary {glossary_path}: {exc}") from exc
    scope = {
        "source_basename": SOURCE_BASENAME,
        "schools": list(SCHOOLS),
        "target_roles": list(TARGET_ROLES),
        "recursive_tokens": list(RECURSIVE_TOKENS),
        "caller_tokens": list(CALLER_TOKENS),
        "grammar_exception": GRAMMAR_EXCEPTION,
        "body_neutral_locators": [
            {"key": key, "variant_ordinal": ordinal}
            for key, ordinal in sorted(BODY_NEUTRAL_LOCATORS)
        ],
    }
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": scope,
        "scope_sha256": _sha256(_canonical_json(scope)),
        "glossary": {"path": "docs/glossary.md", "sha256": glossary_sha256},
        "dumps": bindings,
        "entries": entries,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _strict_block(path: Path) -> list[dict[str, Any]]:
    return shared._strict_block(path, STRICT_BEGIN, STRICT_END)


def _punctuation_for(key: str) -> str:
    school = key.split(" miscast ", 1)[0]
    return DAMAGE_PUNCTUATION if school in DAMAGING_SCHOOLS else WEAK_PUNCTUATION


def _validate_proposed_variant(
    key: str, baseline: dict[str, Any], proposed: str,
) -> tuple[list[str], list[dict[str, Any]]]:
    ordinal = baseline["locator"]["variant_ordinal"]
    tokens = _runtime_tokens(proposed)
    unknown = [token for token in tokens if token not in ALLOWED_TOKENS]
    _require(not unknown, f"miscast:{key} variant {ordinal} unknown proposed token")
    _require(tokens == _expected_zh_tokens(
        key, ordinal, baseline["runtime_tokens_english"]
    ), f"miscast:{key} variant {ordinal} proposed token topology mismatch")
    sites = _selection_sites(proposed)
    _require(
        [site["alternative_count"] for site in sites]
        == [site["alternative_count"]
            for site in baseline["selection_sites_english"]],
        f"miscast:{key} variant {ordinal} proposed choice topology mismatch",
    )
    _require(not re.search(r"[.!?。！？]\s*$", proposed),
             f"miscast:{key} variant {ordinal} proposed terminal punctuation")
    if (key, ordinal) in BODY_NEUTRAL_LOCATORS:
        _require("身体" not in proposed and "皮肤" not in proposed,
                 f"miscast:{key} variant {ordinal} must be body-neutral")
    _require(not re.search(
        r"@(The_monster_possessive|the_monster_possessive|possessive)@的",
        proposed,
    ), f"miscast:{key} variant {ordinal} duplicates possessive 的")
    return tokens, sites


def _expected_facts(
    inventory: dict[str, Any], entry: dict[str, Any], proposed: list[str],
) -> dict[str, Any]:
    variants = entry["variants"]
    proposed_data = [
        _validate_proposed_variant(entry["key"], variant, pattern)
        for variant, pattern in zip(variants, proposed)
    ]
    has_body = any(
        (entry["key"], variant["locator"]["variant_ordinal"])
        in BODY_NEUTRAL_LOCATORS
        for variant in variants
    )
    return {
        "body_skin_postprocessing": (
            BODY_POSTPROCESSING if has_body else "not applicable"
        ),
        "choice_site_counts": {
            "chinese_baseline": sum(
                len(variant["selection_sites_chinese"]) for variant in variants
            ),
            "chinese_candidate": sum(len(data[1]) for data in proposed_data),
            "english": sum(
                len(variant["selection_sites_english"]) for variant in variants
            ),
        },
        "effective_provenance": {
            "chinese": entry["chinese_provenance"],
            "english": entry["english_provenance"],
        },
        "english_source": inventory["dumps"]["english"]["effective_miscast_source"],
        "final_punctuation": _punctuation_for(entry["key"]),
        "localized_source": inventory["dumps"]["localized"]["effective_miscast_source"],
        "parse_error": None,
        "runtime_tokens_chinese_baseline": [
            variant["runtime_tokens_chinese"] for variant in variants
        ],
        "runtime_tokens_chinese_candidate": [data[0] for data in proposed_data],
        "runtime_tokens_english": [
            variant["runtime_tokens_english"] for variant in variants
        ],
        "source_history_length": entry["source_history_length"],
        "target_role": entry["key"].rsplit(" ", 1)[1],
        "unseen_gate": UNSEEN_GATE,
        "variant_count": len(variants),
        "weights": [variant["weight"] for variant in variants],
    }


def _validate_card(
    card: dict[str, Any], inventory: dict[str, Any], entry: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> None:
    identity = entry["identity"]
    _require_exact_fields(card, CARD_FIELDS, identity)
    _require(card["identity"] == identity, f"{identity} identity mismatch")
    _require(card["key"] == entry["key"], f"{identity} key mismatch")
    _require(card["terminal_conclusion"] in TERMINAL_CONCLUSIONS,
             f"{identity} has nonterminal conclusion")
    _require(card["confidence"] in CONFIDENCE_LEVELS,
             f"{identity} confidence mismatch")
    _require(card["deferral_owner"] is None and card["deferral_reason"] is None,
             f"{identity} terminal card forbids deferral fields")
    _require(card["lifecycle"] == "current-player-visible",
             f"{identity} lifecycle mismatch")
    _require(card["consumer"] == CONSUMER, f"{identity} consumer mismatch")
    _require(card["producers"] == PRODUCERS, f"{identity} producers mismatch")
    school, target = entry["key"].split(" miscast ", 1)
    _require(
        card["actual_behavior"]
        == ACTUAL_BEHAVIOR_PREFIX + SCHOOL_EFFECTS[school]
        + ACTUAL_BEHAVIOR_SUFFIX,
        f"{identity} actual_behavior mismatch",
    )
    _require(card["dependency_group"] == DEPENDENCY_GROUPS[school],
             f"{identity} dependency_group mismatch")
    _require(card["display_context"] == DISPLAY_CONTEXTS[target],
             f"{identity} display_context mismatch")
    _require(card["reentry_trigger"] == REENTRY_TRIGGER,
             f"{identity} reentry_trigger mismatch")
    _require(_nonempty_string(card["reviewer_rationale"]),
             f"{identity} requires reviewer_rationale")
    expected_locations = [
        f"crawl-ref/source/dat/database/miscast.txt:{entry['english_source_line']}",
        f"crawl-ref/source/dat/database/zh/miscast.txt:{entry['chinese_source_line']}",
        "crawl-ref/source/spl-miscast.cc:34",
        "crawl-ref/source/spl-miscast.cc:145",
        "crawl-ref/source/database.cc:120",
    ]
    _require(
        card["evidence_locations"] == expected_locations,
        f"{identity} evidence_locations mismatch",
    )
    _require(card["glossary_authority"] == (
        f"{inventory['glossary']['path']}@{inventory['glossary']['sha256']}"
    ), f"{identity} glossary_authority mismatch")
    _require(
        isinstance(card["rejected_alternatives"], list)
        and bool(card["rejected_alternatives"])
        and all(_nonempty_string(item) for item in card["rejected_alternatives"]),
        f"{identity} rejected_alternatives mismatch",
    )
    baseline_en = [variant["english"] for variant in entry["variants"]]
    baseline_zh = [variant["chinese"] for variant in entry["variants"]]
    _require(card["current_english"] == baseline_en,
             f"{identity} current_english mismatch")
    _require(card["current_chinese"] == baseline_zh,
             f"{identity} current_chinese mismatch")
    proposed = card["proposed_translation"]
    _require(
        isinstance(proposed, list)
        and len(proposed) == len(entry["variants"])
        and all(isinstance(item, str) for item in proposed),
        f"{identity} proposed_translation coverage mismatch",
    )
    facts = card["production_facts"]
    _require(isinstance(facts, dict), f"{identity} production_facts must be object")
    _require_exact_fields(facts, PRODUCTION_FACT_FIELDS,
                          f"{identity} production_facts")
    for field in ("variant_count",):
        _require(_is_int(facts[field]), f"{identity} {field} must be integer")
    _require(
        isinstance(facts["weights"], list)
        and all(_is_int(weight) for weight in facts["weights"]),
        f"{identity} weights must be integer array",
    )
    _require(
        isinstance(facts["choice_site_counts"], dict)
        and set(facts["choice_site_counts"])
        == {"chinese_baseline", "chinese_candidate", "english"},
        f"{identity} choice_site_counts field set mismatch",
    )
    for count in facts["choice_site_counts"].values():
        _require(_is_int(count), f"{identity} choice count must be integer")
    expected_facts = _expected_facts(inventory, entry, proposed)
    _require(facts == expected_facts, f"{identity} production_facts mismatch")

    reviews = card["variant_reviews"]
    _require(isinstance(reviews, list)
             and len(reviews) == len(entry["variants"]),
             f"{identity} variant_reviews coverage mismatch")
    ordinals = [review.get("variant_ordinal")
                for review in reviews if isinstance(review, dict)]
    _require(len(ordinals) == len(reviews)
             and all(_is_int(ordinal) for ordinal in ordinals),
             f"{identity} variant ordinals must be integers")
    _require(ordinals == list(range(len(reviews))),
             f"{identity} duplicate, extra, missing, or unordered variant locator")
    conclusions = []
    for baseline, review, proposal in zip(entry["variants"], reviews, proposed):
        ordinal = baseline["locator"]["variant_ordinal"]
        context = f"{identity} variant {ordinal}"
        _require_exact_fields(review, VARIANT_FIELDS, context)
        _require(_is_int(review["weight"]), f"{context} weight must be integer")
        _require(review["terminal_conclusion"] in TERMINAL_CONCLUSIONS,
                 f"{context} has nonterminal conclusion")
        expected_tokens, expected_sites = _validate_proposed_variant(
            entry["key"], baseline, proposal
        )
        grammar = None
        if identity == GRAMMAR_EXCEPTION["identity"] \
                and ordinal == GRAMMAR_EXCEPTION["variant_ordinal"]:
            grammar = (
                "ZH intentionally omits the EN-only @hand_conj@ inflection "
                "token; no literal 's' is generated."
            )
        body_locator = (entry["key"], ordinal) in BODY_NEUTRAL_LOCATORS
        _require((review["body_skin_strategy"] is not None) == body_locator,
                 f"{context} body_skin_strategy mismatch")
        if body_locator:
            _require(_nonempty_string(review["body_skin_strategy"]),
                     f"{context} body_skin_strategy must be nonempty")
        expected = {
            "current_chinese": baseline["chinese"],
            "english": baseline["english"],
            "final_message_punctuation": _punctuation_for(entry["key"]),
            "grammar_exception": grammar,
            "proposal_type": "textdb-pattern",
            "proposed_translation": proposal,
            "runtime_tokens": {
                "chinese_baseline": baseline["runtime_tokens_chinese"],
                "chinese_candidate": expected_tokens,
                "english": baseline["runtime_tokens_english"],
            },
            "selection_sites": {
                "chinese_baseline": baseline["selection_sites_chinese"],
                "chinese_candidate": expected_sites,
                "english": baseline["selection_sites_english"],
            },
            "variant_ordinal": ordinal,
            "weight": baseline["weight"],
        }
        for field, value in expected.items():
            _require(review[field] == value, f"{context} {field} mismatch")
        _require(_nonempty_string(review["rationale"]),
                 f"{context} requires rationale")
        conclusion = review["terminal_conclusion"]
        if conclusion == "keep":
            _require(proposal == baseline["chinese"],
                     f"{context} keep must preserve Chinese")
        else:
            _require(proposal != baseline["chinese"],
                     f"{context} changed conclusion must change Chinese")
        conclusions.append(conclusion)
    if card["terminal_conclusion"] == "keep":
        _require(set(conclusions) == {"keep"},
                 f"{identity} keep conflicts with variants")
    elif card["terminal_conclusion"] == "adjust":
        _require("adjust" in conclusions and "retranslate" not in conclusions,
                 f"{identity} adjust conflicts with variants")
    else:
        _require("retranslate" in conclusions,
                 f"{identity} retranslate conflicts with variants")
    if candidate is not None:
        candidate_zh = [variant["chinese"] for variant in candidate["variants"]]
        _require(proposed == candidate_zh,
                 f"{identity} proposal does not match candidate ZH dump")


def validate_results(
    path: Path, inventory: dict[str, Any],
    candidate_entries: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    records = _strict_block(path)
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review evidence metadata/card coverage mismatch")
    metadata, cards = records[0], records[1:]
    _require_exact_fields(metadata, METADATA_FIELDS, "review metadata")
    for field in ("choice_site_count", "identity_count", "variant_count"):
        _require(_is_int(metadata[field]),
                 f"review metadata {field} must be integer")
    counts = metadata["terminal_conclusion_counts"]
    _require(isinstance(counts, dict)
             and set(counts) == {"adjust", "defer", "keep", "retranslate"}
             and all(_is_int(value) for value in counts.values()),
             "review metadata terminal_conclusion_counts mismatch")
    expected_metadata = {
        "baseline": inventory["baseline_ref"],
        "chinese_production_dump_sha256": (
            inventory["dumps"]["localized"]["artifact_sha256"]
        ),
        "choice_site_count": EXPECTED_CHOICE_SITE_COUNT,
        "english_production_dump_sha256": (
            inventory["dumps"]["english"]["artifact_sha256"]
        ),
        "glossary_sha256": inventory["glossary"]["sha256"],
        "grammar_exceptions": [GRAMMAR_EXCEPTION],
        "identity_count": EXPECTED_IDENTITY_COUNT,
        "variant_count": EXPECTED_VARIANT_COUNT,
    }
    for field, value in expected_metadata.items():
        _require(metadata[field] == value,
                 f"review metadata {field} mismatch")
    expected_identities = [entry["identity"] for entry in inventory["entries"]]
    actual_identities = [card.get("identity") for card in cards]
    _require(actual_identities == expected_identities,
             "review card duplicate, extra, missing, or order mismatch")
    candidate_by_identity = (
        {entry["identity"]: entry for entry in candidate_entries}
        if candidate_entries is not None else {}
    )
    for card, entry in zip(cards, inventory["entries"]):
        _validate_card(card, inventory, entry,
                       candidate_by_identity.get(entry["identity"]))
    actual_counts = {"adjust": 0, "defer": 0, "keep": 0, "retranslate": 0}
    for card in cards:
        actual_counts[card["terminal_conclusion"]] += 1
    _require(counts == actual_counts,
             "review metadata terminal_conclusion_counts does not match cards")
    proposed_choice_count = sum(
        len(review["selection_sites"]["chinese_candidate"])
        for card in cards for review in card["variant_reviews"]
    )
    _require(proposed_choice_count == EXPECTED_CHOICE_SITE_COUNT,
             "candidate proposal choice-site coverage mismatch")
    return {"metadata": metadata, "cards": cards}


def add_candidate(
    inventory: dict[str, Any], candidate_ref: str, english_path: Path,
    localized_path: Path,
) -> list[dict[str, Any]]:
    shared._require_candidate_commit(
        inventory["baseline_ref"], candidate_ref, exact_clean_checkout=True
    )
    bindings, entries = _load_bound_pair(
        candidate_ref, english_path, localized_path, "candidate"
    )
    baseline_en = {
        entry["identity"]: [variant["english"] for variant in entry["variants"]]
        for entry in inventory["entries"]
    }
    for entry in entries:
        _require(
            [variant["english"] for variant in entry["variants"]]
            == baseline_en[entry["identity"]],
            f"candidate English drift for {entry['identity']}",
        )
    inventory["candidate"] = {
        "candidate_ref": candidate_ref,
        "dumps": bindings,
        "entries": entries,
    }
    inventory["candidate"]["candidate_sha256"] = _sha256(
        _canonical_json(inventory["candidate"])
    )
    return entries


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
        args.baseline_ref, args.english_dump, args.localized_dump, args.glossary
    )
    candidate_entries = None
    if args.candidate_ref is not None:
        candidate_entries = add_candidate(
            inventory, args.candidate_ref,
            args.candidate_english_dump, args.candidate_localized_dump,
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
