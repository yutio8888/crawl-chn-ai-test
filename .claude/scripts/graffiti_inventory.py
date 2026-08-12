#!/usr/bin/env python3
"""Build and audit the complete Issue #66 graffiti review inventory.

The inventory is derived from production ``textdb-phase0-dump`` artifacts
and exact Git source snapshots.  It freezes all 58 graffiti identities, every
weighted variant, recursive dependency, external TextDB dependency and
post-processing token.  A strict JSONL review card is required for every
identity.  Candidate validation then proves that both language files equal
the reviewed proposals byte-for-byte and that the resulting recursive graph
is complete and contains no unresolved token.
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
SOURCE_BASENAME = "graffiti.txt"
ROOT_KEY = "any_graffiti"
STRICT_BEGIN = "<!-- BEGIN STRICT GRAFFITI REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT GRAFFITI REVIEW EVIDENCE v1 -->"
EXPECTED_IDENTITY_COUNT = 58
EXPECTED_BASELINE_EN_VARIANTS = 404
EXPECTED_BASELINE_ZH_VARIANTS = 403
EXPECTED_CANDIDATE_VARIANTS = 404
EXPECTED_RANDOM_SITES = 52
RESULTS_PATH = Path(__file__).resolve().parents[2] / "docs/graffiti-review-results.md"
EXPECTED_BASELINE_ASYMMETRY = {
    "_graffiti_hailed_god_": (5, 4),
    "_graffiti_happened_reason_": (26, 25),
    "any_graffiti": (15, 16),
}
EXPECTED_BASELINE_UNRESOLVED = {
    "english": [{
        "key": "_graffiti_vengeance_",
        "variant_ordinal": 1,
        "token": "@graffiti_author_any@",
    }],
    "chinese": [],
}
EXPECTED_BASELINE_UNREACHABLE = {
    "english": [],
    "chinese": ["_graffiti_unreadable_"],
}

# Chinese possession places the owner before the possessed noun, so the
# short-saying form “A loves B's relative/quality” cannot preserve the EN
# recursive lookup order without becoming unnatural.  The token multiset,
# weight and random-site shape remain identical, and the real MiscDB display
# test proves language-neutral RNG state/count over 4096 fixed seeds.
ORDERED_TOKEN_EXCEPTIONS = {("_graffiti_short_saying_", 2)}

# These are looked up recursively in the already-loaded SpeakDB/MiscDB.
EXTERNAL_TEXTDB_KEYS = {
    "ancestor name", "any orc name", "any_colour", "any_colour_pattern",
    "any_glowing_colour", "any_glowing_colour_pattern", "bland name",
}

# These are replaced by ``do_mon_name_replacements`` after TextDB expansion.
POSTPROCESS_TOKENS = {
    "randgen", "random_god", "random_god_chaotic", "random_god_evil",
    "random_god_good", "random_skill", "random_skill_magic",
    "random_skill_mundane",
}

CONCLUSIONS = {
    "keep", "adjust", "retranslate", "defer implementation",
    "defer terminology",
}
DEFER_CONCLUSIONS = {"defer implementation", "defer terminology"}
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

CHANGE_RATIONALES = {
    "_graffiti_advertisement_": "恢复七个广告语义分支的 canonical 顺序与 10/10/10/2/1/1/1 权重，移除英文不存在的可选署名，恢复 unrestricted author，并修正 Dungeon 与商品修饰关系。",
    "_graffiti_author_orc_": "将英语姓名后置结构改为自然的“兽人+姓名”，避免“那兽人”错义与裸空格。",
    "_graffiti_changed_names_": "恢复普通、兽人、稀有名与佐姆改名四分支的 author pool 以及 10/2/2/1 权重。",
    "_graffiti_changed_or_compared_religions_": "恢复 unrestricted author pool，并修正改信、神祇身份与比较句语法；保留全部 god postprocess token。",
    "_graffiti_class_any_": "按英文语义顺序恢复补习课默认权重与大师课 w:2。",
    "_graffiti_class_master_": "恢复匿名艺术课 w:1，并按现行术语修正 ogre、oni 与 felid。",
    "_graffiti_class_remedial_": "恢复五个专门技能补习分支的 w:2，不改变技能 token 或教授组合。",
    "_graffiti_fight_": "移除英文不存在的可选署名，恢复 unrestricted author 与两条专门争斗 w:2，并采用暗影/暗影食尸鬼权威名称。",
    "_graffiti_hailed_god_": "把错误的完整句/self-cycle 恢复为五个名词片段：佐姆、未知神、沃格、奶酪之力和煎饼车，权重为 10/2/1/1/1。",
    "_graffiti_happened_reason_": "补回遗漏的 unnecessary，并恢复 coincidence 的 unrestricted author；修正 undeserved 组合语义。",
    "_graffiti_image_": "把图像恢复为由根统一组合的纯内容片段，重新获得可选署名，并修正 human、oni、deep elf、tengu、felid 等现行术语。",
    "_graffiti_loves_or_hates_": "将不能直接带宾语的“辩护”改为“维护”，保证短句组合语法成立。",
    "_graffiti_mass_meeting_ordinary_": "修正地牢、可激活物品、技师俱乐部、独自作战与治疗他人的术语/语序。",
    "_graffiti_mass_meeting_religious_": "修复 Nemelex 随机选项量词组合，并修正独自作战与治疗他人的语序。",
    "_graffiti_obscenities_": "移除英文不存在的 non-orc 可选署名，让根用 canonical 无署名涂鸦类型统一组合。",
    "_graffiti_religion_better_or_worse_": "去掉重复比较成分，使 outer A比B 与四个比较片段自然组合。",
    "_graffiti_religion_non-orc_": "恢复纯宗教内容片段；non-orc 署名资格由 any_graffiti 根唯一施加。",
    "_graffiti_religion_not_non-orc_or_orc_": "恢复纯宗教内容片段，润色 Nemelex 等不自然句式；神祇身份与 random_god token 保持不变。",
    "_graffiti_religion_orc_": "恢复纯兽人宗教内容片段；orc 署名资格由 any_graffiti 根唯一施加。",
    "_graffiti_rumour_": "恢复纯传闻片段，修正 unlife 与地牢语境，并由根统一提供可选署名。",
    "_graffiti_short_saying_": "恢复 unrestricted author、changed-names w:2 与 canonical 无署名组合；修复货物品质双“的”，由根统一加引号。",
    "_graffiti_species_": "恢复纯物种评论片段，并按现行权威修正 wield、oni 与一般时态。",
    "_graffiti_type_": "恢复“书写样式+涂鸦”的 canonical 角色，避免把 writing noun 重复嵌入类型。",
    "_graffiti_unique_comment_": "恢复纯评论片段并修正多处生硬语序、Dungeon 术语，由根统一提供可选署名。",
    "_graffiti_unreadable_": "恢复四个完整不可读片段、10/10/1/1 权重与 unrestricted author，并消除冗余“署名的签名”。",
    "_graffiti_vengeance_": "修复英文悬空 @graffiti_author_any@，并恢复五个兽人复仇目标的 unrestricted author pool。",
    "_graffiti_vengeance_reason_": "恢复五个具名复仇原因的 unrestricted author pool，不改变其十个语义分支。",
    "_pattern_type_": "移除中文额外拼接的随机 writing style，恢复颜色图案与发光颜色图案两个 canonical 片段。",
    "_rare_graffiti_author_ordinary_": "按现行 oni→鬼术语将“鬼妖夫尼布”修正为“鬼夫尼布”。",
    "_writing_noun_": "按英文 15 项概念逐项恢复 binary code、cuneiform、glyphs、print-out、sigils 等缺失书写名词。",
    "_writing_style_": "恢复颜色、形容词+颜色、发光颜色三种样式，不再混入 writing noun 或虚构无颜色分支。",
    "_writing_type_": "恢复“书写样式+书写名词”组合，使 writing type 与 graffiti type 职责分离。",
    "any_graffiti": "恢复 15 分支 canonical 根：接回 unreadable、删除多余 hailed-god 分支、恢复三条宗教 w:2，并把类型/署名在根统一组合。",
}

ADJUST_KEYS = {
    "_graffiti_changed_names_", "_graffiti_class_any_",
    "_graffiti_class_remedial_", "_graffiti_religion_non-orc_",
    "_graffiti_religion_orc_", "_graffiti_vengeance_",
    "_graffiti_vengeance_reason_", "_pattern_type_", "any_graffiti",
}

InventoryError = hardened.InventoryError
_require = hardened._require
_sha256 = hardened._sha256
_canonical_json = hardened._canonical_json


def _group_for(key: str) -> str:
    if key == ROOT_KEY:
        return "生产根与递归闭包"
    if "religion" in key or "god" in key:
        return "宗教与神祇"
    if "author" in key or "changed_names" in key or "duplicate" in key:
        return "署名与姓名"
    if key in {"_graffiti_type_", "_graffiti_type_with_signature_maybe_",
               "_graffiti_type_with_signature_maybe_non-orc_",
               "_graffiti_type_with_signature_maybe_orc_", "_pattern_type_",
               "_writing_style_", "_writing_type_", "_graffiti_unreadable_"}:
        return "书写材质、样式与可读性"
    if "class" in key or "professor" in key:
        return "课程与教授"
    return "涂鸦叙事内容"


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
        if entry["effective_provenance"]["source_name"] == source_name
    ]
    _require(len(rows) == EXPECTED_IDENTITY_COUNT,
             f"{label} graffiti identity count mismatch")
    keys = [entry["canonical_key"] for entry in rows]
    _require(len(set(keys)) == len(keys), f"{label} duplicate graffiti key")
    for entry in rows:
        _require(entry["parse_error"] is None,
                 f"{label} parse error at {entry['canonical_key']!r}")
        _require(not entry["body_empty"],
                 f"{label} empty body at {entry['canonical_key']!r}")
        _require(len(entry["source_history"]) == 1,
                 f"{label} overridden graffiti key {entry['canonical_key']!r}")
    return sorted(rows, key=lambda entry: entry["canonical_key"])


def _variant(raw: dict[str, Any]) -> dict[str, Any]:
    text = raw["raw_pattern"]
    _require(not hardened._lua_sites(text),
             f"graffiti variant unexpectedly embeds Lua: {text!r}")
    return {
        "variant_ordinal": raw["locator"]["variant_ordinal"],
        "weight": raw["weight"],
        "text": text,
        "runtime_tokens": hardened._runtime_tokens(text),
        "random_site_counts": hardened._random_site_counts(text),
    }


def _classify_tokens(rows: list[dict[str, Any]], all_effective_keys: set[str]) -> dict[str, Any]:
    key_set = {row["canonical_key"].lower() for row in rows}
    recursive: dict[str, list[dict[str, Any]]] = {key: [] for key in key_set}
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
                site = {"key": source, "variant_ordinal": ordinal, "token": token}
                if canonical in key_set:
                    edges[source].add(canonical)
                    recursive[canonical].append(site)
                elif canonical in EXTERNAL_TEXTDB_KEYS:
                    _require(canonical in all_effective_keys,
                             f"external TextDB dependency {token!r} is not loaded")
                    external_sites.append(site)
                elif canonical in POSTPROCESS_TOKENS:
                    postprocess_sites.append(site)
                else:
                    unresolved.append(site)
    return {
        "edges": {key: sorted(value) for key, value in sorted(edges.items())},
        "references": {
            key: sorted(value, key=lambda item: (item["key"], item["variant_ordinal"], item["token"]))
            for key, value in sorted(recursive.items())
        },
        "external_sites": sorted(external_sites, key=lambda item: (item["key"], item["variant_ordinal"], item["token"])),
        "postprocess_sites": sorted(postprocess_sites, key=lambda item: (item["key"], item["variant_ordinal"], item["token"])),
        "unresolved": sorted(unresolved, key=lambda item: (item["key"], item["variant_ordinal"], item["token"])),
    }


def _reachability(edges: dict[str, list[str]]) -> dict[str, Any]:
    reached = {ROOT_KEY}
    queue: deque[tuple[str, tuple[str, ...]]] = deque([(ROOT_KEY, (ROOT_KEY,))])
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
    all_keys = {entry["canonical_key"].lower() for entry in artifact["entries"]}
    token_facts = _classify_tokens(rows, all_keys)
    reachability = _reachability(token_facts["edges"])
    entries = []
    source_snapshot = next(
        source for source in artifact["sources"]
        if source["source_name"] == f"{directory}{SOURCE_BASENAME}"
    )
    lines = hardened._definition_lines(source_snapshot["normalized_utf8"], label)
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
    if role == "baseline":
        expected = (EXPECTED_BASELINE_EN_VARIANTS if directory == "database/"
                    else EXPECTED_BASELINE_ZH_VARIANTS)
        _require(total == expected, f"{label} baseline variant count mismatch")
        _require(random_sites == EXPECTED_RANDOM_SITES,
                 f"{label} baseline random-site count mismatch")
    else:
        _require(total == EXPECTED_CANDIDATE_VARIANTS,
                 f"{label} candidate variant count mismatch")
        _require(random_sites == EXPECTED_RANDOM_SITES,
                 f"{label} candidate random-site count mismatch")
    return {
        "artifact_sha256": _sha256(raw),
        "source_name": f"{directory}{SOURCE_BASENAME}",
        "source_sha256": _sha256(source_snapshot["normalized_utf8"].encode("utf-8")),
        "entries": entries,
        "token_facts": token_facts,
        "reachability": reachability,
        "variant_count": total,
        "random_site_count": random_sites,
    }


def _load_dataset(ref: str, path: Path, directory: str, label: str, role: str) -> dict[str, Any]:
    hardened.shared._validate_oid(ref, label)
    hardened._require_regular_git_sources(ref, directory, label)
    artifact, raw = hardened._load_dump_safe(path, label, directory)
    derived = hardened.shared._derive_scoped_dump(
        ref, directory, label, source_basename=SOURCE_BASENAME
    )
    hardened.shared._require_scoped_derivation(
        artifact, derived, label, source_basename=SOURCE_BASENAME
    )
    return _dataset(artifact, raw, directory, label, role)


def _pair_entries(en: dict[str, Any], zh: dict[str, Any]) -> list[dict[str, Any]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(en_by_key.keys() == zh_by_key.keys(), "graffiti EN/ZH key sets differ")
    entries = []
    for key in sorted(en_by_key):
        en_entry, zh_entry = en_by_key[key], zh_by_key[key]
        counts = (len(en_entry["variants"]), len(zh_entry["variants"]))
        if counts[0] != counts[1]:
            _require(EXPECTED_BASELINE_ASYMMETRY.get(key) == counts,
                     f"unexpected baseline asymmetry for {key!r}: {counts!r}")
        else:
            _require(key not in EXPECTED_BASELINE_ASYMMETRY,
                     f"frozen asymmetric key {key!r} unexpectedly aligned")
        lifecycle = "direct-production-root" if key == ROOT_KEY else "recursive-internal-fragment"
        entries.append({
            "identity": f"graffiti:{key}",
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
    return entries


def build_inventory(
    baseline_ref: str, english_path: Path, localized_path: Path,
    glossary_path: Path, glossary_ref: str | None = None,
) -> dict[str, Any]:
    en = _load_dataset(baseline_ref, english_path, "database/", "baseline EN", "baseline")
    zh = _load_dataset(baseline_ref, localized_path, "database/zh/", "baseline ZH", "baseline")
    _require(en["token_facts"]["unresolved"] == EXPECTED_BASELINE_UNRESOLVED["english"],
             "baseline EN unresolved-token facts changed")
    _require(zh["token_facts"]["unresolved"] == EXPECTED_BASELINE_UNRESOLVED["chinese"],
             "baseline ZH unresolved-token facts changed")
    _require(en["reachability"]["unreachable"] == EXPECTED_BASELINE_UNREACHABLE["english"],
             "baseline EN reachability facts changed")
    _require(zh["reachability"]["unreachable"] == EXPECTED_BASELINE_UNREACHABLE["chinese"],
             "baseline ZH reachability facts changed")
    entries = _pair_entries(en, zh)
    scope = {
        "source_basename": SOURCE_BASENAME,
        "root_key": ROOT_KEY,
        "expected_identity_count": EXPECTED_IDENTITY_COUNT,
        "baseline_variant_counts": {
            "english": EXPECTED_BASELINE_EN_VARIANTS,
            "chinese": EXPECTED_BASELINE_ZH_VARIANTS,
        },
        "baseline_asymmetry": {key: list(value) for key, value in sorted(EXPECTED_BASELINE_ASYMMETRY.items())},
        "external_textdb_keys": sorted(EXTERNAL_TEXTDB_KEYS),
        "postprocess_tokens": sorted(POSTPROCESS_TOKENS),
        "ordered_token_exceptions": [
            {"key": key, "variant_ordinal": ordinal}
            for key, ordinal in sorted(ORDERED_TOKEN_EXCEPTIONS)
        ],
    }
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": scope,
        "scope_sha256": _sha256(_canonical_json(scope)),
        "glossary": {"path": "docs/glossary.md", "sha256": _sha256(_read_glossary(glossary_path, glossary_ref))},
        "dumps": {"english": {key: value for key, value in en.items() if key != "entries"},
                  "localized": {key: value for key, value in zh.items() if key != "entries"}},
        "entries": entries,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _strict_block_from_text(text: str) -> list[dict[str, Any]]:
    _require(text.count(STRICT_BEGIN) == 1, "review results require exactly one strict begin marker")
    _require(text.count(STRICT_END) == 1, "review results require exactly one strict end marker")
    body = text.split(STRICT_BEGIN, 1)[1].split(STRICT_END, 1)[0].strip()
    match = re.fullmatch(r"```jsonl\s*\n(.*?)\n```", body, re.DOTALL)
    _require(match is not None, "strict review evidence must be one fenced jsonl block")
    records = []
    for number, line in enumerate(match.group(1).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InventoryError(f"invalid review JSONL line {number}: {exc}") from exc
        _require(isinstance(value, dict), f"review JSONL line {number} must be an object")
        records.append(value)
    return records


def _strict_block(path: Path) -> list[dict[str, Any]]:
    raw = hardened._read_artifact_bytes(path, "review results")
    try:
        return _strict_block_from_text(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise InventoryError("cannot decode review results") from exc


def _variant_review_shape(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"weight": variant["weight"], "text": variant["text"]} for variant in variants]


def _validate_variant_list(value: Any, context: str) -> None:
    _require(isinstance(value, list), f"{context} must be a list")
    for ordinal, variant in enumerate(value):
        _require(isinstance(variant, dict) and set(variant) == VARIANT_FIELDS,
                 f"{context} ordinal {ordinal} fields mismatch")
        _require(isinstance(variant["weight"], int) and not isinstance(variant["weight"], bool)
                 and variant["weight"] > 0, f"{context} ordinal {ordinal} weight mismatch")
        _require(isinstance(variant["text"], str) and bool(variant["text"]),
                 f"{context} ordinal {ordinal} text mismatch")
        hardened._random_site_counts(variant["text"])
        _require(not hardened._lua_sites(variant["text"]),
                 f"{context} ordinal {ordinal} unexpectedly embeds Lua")


def _expected_metadata(inventory: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "baseline": inventory["baseline_ref"],
        "chinese_production_dump_sha256": inventory["dumps"]["localized"]["artifact_sha256"],
        "en_variant_count": EXPECTED_BASELINE_EN_VARIANTS,
        "english_production_dump_sha256": inventory["dumps"]["english"]["artifact_sha256"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": EXPECTED_IDENTITY_COUNT,
        "inventory_sha256": inventory["inventory_sha256"],
        "terminal_conclusion_counts": dict(sorted(Counter(card["terminal_conclusion"] for card in cards).items())),
        "zh_variant_count": EXPECTED_BASELINE_ZH_VARIANTS,
    }


def validate_results(
    path: Path, inventory: dict[str, Any], candidate: dict[str, Any] | None = None,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    records = records if records is not None else _strict_block(path)
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review results require one metadata record and 58 cards")
    metadata, cards = records[0], records[1:]
    _require(set(metadata) == METADATA_FIELDS, "review metadata fields mismatch")
    _require(metadata == _expected_metadata(inventory, cards), "review metadata mismatch")
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
        _require(card["lifecycle"] == entry["lifecycle"], f"review card {identity} lifecycle mismatch")
        _require(card["dependency_group"] == entry["dependency_group"], f"review card {identity} group mismatch")
        current_en = _variant_review_shape(entry["english_variants"])
        current_zh = _variant_review_shape(entry["chinese_variants"])
        _require(card["current_english_variants"] == current_en,
                 f"review card {identity} current EN mismatch")
        _require(card["current_chinese_variants"] == current_zh,
                 f"review card {identity} current ZH mismatch")
        _validate_variant_list(card["proposed_english_variants"], f"review card {identity} proposed EN")
        _validate_variant_list(card["proposed_chinese_variants"], f"review card {identity} proposed ZH")
        conclusion = card["terminal_conclusion"]
        _require(conclusion in CONCLUSIONS, f"review card {identity} conclusion mismatch")
        changed = (card["proposed_english_variants"] != current_en
                   or card["proposed_chinese_variants"] != current_zh)
        _require(changed == (conclusion in {"adjust", "retranslate"}),
                 f"review card {identity} conclusion/change mismatch")
        for field in ("rationale", "display_context", "reentry_trigger"):
            _require(isinstance(card[field], str) and bool(card[field].strip()),
                     f"review card {identity} requires {field}")
        _require(card["confidence"] in {"high", "medium", "low"},
                 f"review card {identity} confidence mismatch")
        _require(isinstance(card["evidence_locations"], list) and card["evidence_locations"],
                 f"review card {identity} requires evidence locations")
        _require(isinstance(card["rejected_alternatives"], list) and card["rejected_alternatives"],
                 f"review card {identity} requires rejected alternatives")
        _require(isinstance(card["producer_consumer"], dict) and card["producer_consumer"],
                 f"review card {identity} requires producer/consumer evidence")
        if conclusion in DEFER_CONCLUSIONS:
            _require(isinstance(card["deferral_owner"], str) and card["deferral_owner"].strip(),
                     f"review card {identity} deferred conclusion requires owner")
            _require(isinstance(card["deferral_reason"], str) and card["deferral_reason"].strip(),
                     f"review card {identity} deferred conclusion requires reason")
        else:
            _require(card["deferral_owner"] is None and card["deferral_reason"] is None,
                     f"review card {identity} non-deferred conclusion forbids deferral fields")
        proposals[entry["key"]] = {
            "english": card["proposed_english_variants"],
            "chinese": card["proposed_chinese_variants"],
        }
    if candidate is not None:
        candidate_by_key = {entry["key"]: entry for entry in candidate["entries"]}
        _require(candidate_by_key.keys() == proposals.keys(), "candidate key set differs from review ledger")
        for key in sorted(proposals):
            actual = candidate_by_key[key]
            _require(_variant_review_shape(actual["english_variants"]) == proposals[key]["english"],
                     f"candidate EN drift at {key!r}")
            _require(_variant_review_shape(actual["chinese_variants"]) == proposals[key]["chinese"],
                     f"candidate ZH drift at {key!r}")
    return {"metadata": metadata, "cards": cards}


def add_candidate(
    inventory: dict[str, Any], baseline_ref: str, candidate_ref: str,
    english_path: Path, localized_path: Path,
) -> dict[str, Any]:
    hardened.shared._require_candidate_commit(
        baseline_ref, candidate_ref, exact_clean_checkout=True
    )
    en = _load_dataset(candidate_ref, english_path, "database/", "candidate EN", "candidate")
    zh = _load_dataset(candidate_ref, localized_path, "database/zh/", "candidate ZH", "candidate")
    _require(not en["token_facts"]["unresolved"], "candidate EN contains unresolved token")
    _require(not zh["token_facts"]["unresolved"], "candidate ZH contains unresolved token")
    _require(not en["reachability"]["unreachable"], "candidate EN has unreachable graffiti keys")
    _require(not zh["reachability"]["unreachable"], "candidate ZH has unreachable graffiti keys")
    entries = _pair_candidate(en, zh)
    candidate = {
        "candidate_ref": candidate_ref,
        "dumps": {"english": {key: value for key, value in en.items() if key != "entries"},
                  "localized": {key: value for key, value in zh.items() if key != "entries"}},
        "entries": entries,
    }
    candidate["candidate_sha256"] = _sha256(_canonical_json(candidate))
    inventory["candidate"] = candidate
    return candidate


def _pair_candidate(en: dict[str, Any], zh: dict[str, Any]) -> list[dict[str, Any]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(en_by_key.keys() == zh_by_key.keys(), "candidate EN/ZH key sets differ")
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
        entries.append({
            "identity": f"graffiti:{key}", "key": key,
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
        })
    expected_ordered_differences = {
        locator for locator in ORDERED_TOKEN_EXCEPTIONS
        if locator[0] in en_by_key
    }
    _require(
        ordered_differences == expected_ordered_differences,
        "candidate ordered-token grammar exceptions differ: "
        f"{sorted(ordered_differences)!r}",
    )
    return entries


def _proposal_dataset(path: Path, directory: str, label: str) -> dict[str, Any]:
    """Load a mutable production dump for scaffolding only.

    This is never final evidence.  It must nevertheless match the current
    worktree source byte-for-byte after newline normalization; the exact
    candidate audit later re-derives the same data from the committed Git
    object and rejects any mismatch.
    """
    artifact, raw = hardened._load_dump_safe(path, label, directory)
    source_name = f"{directory}{SOURCE_BASENAME}"
    snapshot = next(
        source for source in artifact["sources"]
        if source["source_name"] == source_name
    )
    source_path = Path(__file__).resolve().parents[2] / "crawl-ref/source/dat" / source_name
    current = hardened._read_artifact_bytes(source_path, f"{label} worktree source")
    try:
        normalized = current.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeDecodeError as exc:
        raise InventoryError(f"cannot decode {label} worktree source") from exc
    _require(snapshot["normalized_utf8"] == normalized,
             f"{label} dump does not match the current worktree source")
    dataset = _dataset(artifact, raw, directory, label, "candidate")
    _require(not dataset["token_facts"]["unresolved"],
             f"{label} proposal contains unresolved token")
    _require(not dataset["reachability"]["unreachable"],
             f"{label} proposal has unreachable graffiti keys")
    return dataset


def _card(
    inventory: dict[str, Any], entry: dict[str, Any], proposal: dict[str, Any],
) -> dict[str, Any]:
    current_en = _variant_review_shape(entry["english_variants"])
    current_zh = _variant_review_shape(entry["chinese_variants"])
    proposed_en = _variant_review_shape(proposal["english_variants"])
    proposed_zh = _variant_review_shape(proposal["chinese_variants"])
    changed = current_en != proposed_en or current_zh != proposed_zh
    if changed:
        _require(entry["key"] in CHANGE_RATIONALES,
                 f"changed proposal {entry['key']!r} lacks a reviewed rationale")
        conclusion = "adjust" if entry["key"] in ADJUST_KEYS else "retranslate"
        rationale = CHANGE_RATIONALES[entry["key"]]
    else:
        conclusion = "keep"
        rationale = (
            f"逐项核对 {len(current_en)} 个英文与 {len(current_zh)} 个中文变体；"
            "命题、角色语气、术语、权重、递归/后处理 token 与随机选择站均可保持。"
        )
    lifecycle = entry["lifecycle"]
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": lifecycle,
        "dependency_group": entry["dependency_group"],
        "display_context": (
            "SpeakDB/MiscDB 直接查询根；生成可嵌入喷泉与 Xom 地形消息的涂鸦名词短语。"
            if lifecycle == "direct-production-root" else
            "仅由 any_graffiti 闭包递归展开的内部片段；不能脱离调用点独立解释。"
        ),
        "producer_consumer": {
            "speak_loader": "crawl-ref/source/database.cc:130",
            "misc_loader": "crawl-ref/source/database.cc:147",
            "recursive_expansion": "crawl-ref/source/database.cc:1497",
            "decor_consumer": "crawl-ref/source/directn.cc:3090",
            "xom_consumer": "crawl-ref/source/xom.cc:3213",
        },
        "evidence_locations": [
            f"crawl-ref/source/dat/database/graffiti.txt:{entry['english_source_line']}",
            f"crawl-ref/source/dat/database/zh/graffiti.txt:{entry['chinese_source_line']}",
            *(f"recursive-ref:{site['key']}:{site['variant_ordinal']}"
              for site in entry["english_referencing_sites"]),
            *(f"recursive-ref-zh:{site['key']}:{site['variant_ordinal']}"
              for site in entry["chinese_referencing_sites"]),
        ],
        "current_english_variants": current_en,
        "current_chinese_variants": current_zh,
        "proposed_english_variants": proposed_en,
        "proposed_chinese_variants": proposed_zh,
        "terminal_conclusion": conclusion,
        "confidence": "high",
        "rationale": rationale,
        "rejected_alternatives": [
            "只修表面措辞而保留错误权重、author pool 或递归拓扑。",
            "修改消费者或随机选择实现来补偿 TextDB 数据缺陷。",
        ],
        "reentry_trigger": (
            "英文/中文 graffiti source、加载顺序、递归/后处理 token、权重、"
            "database/directn/xom 消费者或 docs/glossary.md 权威变化时重审。"
        ),
        "deferral_owner": None,
        "deferral_reason": None,
    }


def scaffold_results(
    path: Path, inventory: dict[str, Any], proposal_en: dict[str, Any],
    proposal_zh: dict[str, Any],
) -> list[dict[str, Any]]:
    proposal_entries = _pair_candidate(proposal_en, proposal_zh)
    proposal_by_key = {entry["key"]: entry for entry in proposal_entries}
    _require(proposal_by_key.keys() == {entry["key"] for entry in inventory["entries"]},
             "proposal key set differs from frozen inventory")
    cards = [
        _card(inventory, entry, proposal_by_key[entry["key"]])
        for entry in inventory["entries"]
    ]
    records = [_expected_metadata(inventory, cards), *cards]
    text = (
        "# Graffiti 全量审核结果（Issue #66）\n\n"
        "本文件的严格 JSONL 块是 58 个 frozen identity 的完整审核账本。"
        "每张卡同时绑定基线 EN/ZH 变体和已批准 proposal；候选审计只接受"
        "逐字等于 proposal 的提交。\n\n"
        f"{STRICT_BEGIN}\n```jsonl\n"
        + "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True)
                    for record in records)
        + f"\n```\n{STRICT_END}\n"
    )
    resolved = path.resolve(strict=False)
    _require(resolved == RESULTS_PATH.resolve(strict=False),
             f"scaffold output must be {RESULTS_PATH}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(resolved, flags, 0o600)
    except OSError as exc:
        raise InventoryError(f"cannot exclusively create scaffold {resolved}: {exc}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
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
    parser.add_argument("--proposal-english-dump", type=Path)
    parser.add_argument("--proposal-localized-dump", type=Path)
    parser.add_argument("--scaffold-output", type=Path)
    parser.add_argument("--glossary", type=Path,
                        default=Path(__file__).resolve().parents[2] / "docs/glossary.md")
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
    proposal_values = (args.proposal_english_dump, args.proposal_localized_dump,
                       args.scaffold_output)
    if any(value is not None for value in proposal_values):
        _require(all(value is not None for value in proposal_values),
                 "proposal dumps and scaffold output must be supplied together")
        _require(args.review_results is None and args.candidate_ref is None,
                 "scaffolding cannot be combined with review/candidate validation")
    records = None
    if args.candidate_ref is not None:
        hardened.shared._require_candidate_commit(
            args.baseline_ref, args.candidate_ref, exact_clean_checkout=True
        )
        ledger = hardened._candidate_regular_blob(
            args.candidate_ref,
            hardened._repo_relative_git_path(args.review_results, "review results"),
            "review results",
        )
        records = _strict_block_from_text(ledger.decode("utf-8"))
    inventory = build_inventory(
        args.baseline_ref, args.english_dump, args.localized_dump, args.glossary,
        glossary_ref=args.candidate_ref if args.candidate_ref else None,
    )
    candidate = None
    if args.scaffold_output is not None:
        proposal_en = _proposal_dataset(
            args.proposal_english_dump, "database/", "proposal EN"
        )
        proposal_zh = _proposal_dataset(
            args.proposal_localized_dump, "database/zh/", "proposal ZH"
        )
        scaffold_results(args.scaffold_output, inventory, proposal_en, proposal_zh)
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
        print(f"graffiti_inventory.py: {exc}", file=sys.stderr)
        raise SystemExit(2)
