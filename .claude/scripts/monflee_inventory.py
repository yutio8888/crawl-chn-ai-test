#!/usr/bin/env python3
"""Build and audit the Issue #54 monflee inventory from production dumps.

The supplied ``textdb-phase0-dump`` JSON remains the artifact under review.
For this narrow scope, exact Git inputs independently rebuild every definition
whose history touches ``monflee.txt`` and cross-check the artifact.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from audit_monspell_phase0 import ArtifactError, textdb_marker_sites, validate_artifact
from command_inventory import merge_desc_sequence, parse_db_keys
from i18n_shared import lowercase_string, trim_string, trusted_git_environment


SCHEMA_VERSION = 1
STRICT_BEGIN = "<!-- BEGIN STRICT MONFLEE REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT MONFLEE REVIEW EVIDENCE v1 -->"
OID_RE = re.compile(r"^[0-9a-f]{40}$")
CONTROL_RE = re.compile(r"^([A-Z][A-Z0-9_]*):")
ALLOWED_CONTROLS = {None, "VISUAL"}
DEFER_CONCLUSIONS = {"defer terminology", "defer implementation"}
TERMINAL_CONCLUSIONS = {"keep", "adjust", "retranslate", *DEFER_CONCLUSIONS}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
INT_MIN = -(2 ** 31)
INT_MAX = 2 ** 31 - 1
METADATA_FIELDS = {
    "baseline", "glossary_sha256", "identity_count", "inventory_sha256",
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
VARIANT_FIELDS = {
    "control_prefix", "current_chinese", "english", "proposed_translation",
    "rationale", "runtime_tokens", "terminal_conclusion", "variant_ordinal",
    "weight",
}
DEFERRAL_FIELDS = {"deferral_owner", "deferral_reason", "reentry_trigger"}
SCOPE = {
    "source_basename": "monflee.txt",
    "identities": [
        {"identity": "monflee:dream sheep flee", "key": "dream sheep flee"},
    ],
    "producer_sites": [
        "crawl-ref/source/mon-behv.cc:1287",
        "crawl-ref/source/dat/des/altar/xom_sheep.des:44",
    ],
}
FROZEN_ACTUAL_BEHAVIOR = (
    "梦羊在 ME_SCARE 中进入逃跑行为时，以稳定英文 DB name 查询该 key；"
    "Xom 梦羊 vault 也直接查询同一 key。localized SpeakDB 使用生产权重选择正文，"
    "随后展开怪物 token。无前缀 ordinal 0 在 pre-mprf seam 作为 MSGCH_TALK "
    "emission 继续传递：源怪物 ENCH_MUTE 或源格沉默只将 effective_silence 置为 "
    "true，不阻止它抵达 MSGCH_TALK；最终 mprf sink 仅在玩家所在格沉默时由 "
    "prepare_message 抑制该 MSGCH_TALK。VISUAL 正文路由至 MSGCH_TALK_VISUAL、"
    "清除 silence，仅怪物可见时产生 emission，且不受该 sink 抑制。"
)
FROZEN_DISPLAY_CONTEXT = "怪物首次受惊逃跑或 Xom 梦羊事件触发的玩家可见消息。"
FROZEN_CONSUMER = {
    "channel_routing": "crawl-ref/source/mon-speak.cc:851",
    "final_sink": "crawl-ref/source/message.cc:1845",
    "localized_lookup": "crawl-ref/source/database.cc:2307",
    "weighted_selection": "crawl-ref/source/database.cc:1238",
}
FROZEN_PRODUCERS = [
    {"location": SCOPE["producer_sites"][0], "mode": "fear transition"},
    {
        "location": SCOPE["producer_sites"][1],
        "mode": "Xom dream sheep event",
    },
]
FROZEN_EVIDENCE_LOCATIONS = [
    "crawl-ref/source/dat/database/monflee.txt:8",
    "crawl-ref/source/dat/database/zh/monflee.txt:8",
    "crawl-ref/source/mon-behv.cc:1287",
    "crawl-ref/source/mon-speak.cc:851",
    "crawl-ref/source/message.cc:1845",
    "crawl-ref/source/dat/des/altar/xom_sheep.des:44",
]


class InventoryError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise InventoryError(message)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_oid(value: str, label: str) -> None:
    _require(bool(OID_RE.fullmatch(value)),
             f"{label} ref must be a full lowercase OID")
    repository = Path(__file__).resolve().parents[2]
    checked = subprocess.run(
        ["git", "-C", str(repository), "cat-file", "-e", f"{value}^{{commit}}"],
        text=True, capture_output=True, env=trusted_git_environment(),
    )
    _require(checked.returncode == 0, f"{label} ref is not a commit in this repository")


def _git_output(arguments: list[str], label: str) -> bytes:
    repository = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        ["git", "-C", str(repository), *arguments], capture_output=True,
        env=trusted_git_environment(),
    )
    _require(completed.returncode == 0, f"cannot read {label} from exact Git OID")
    return completed.stdout


def _git_blob_at_oid(oid: str, git_path: str, label: str) -> bytes:
    path = PurePosixPath(git_path)
    _require(
        not path.is_absolute() and path.as_posix() == git_path
        and all(part not in {"", ".", ".."} for part in path.parts),
        f"{label} has an unsafe Git path {git_path!r}",
    )
    return _git_output(["show", f"{oid}:{git_path}"], label)


def _decode_utf8(raw: bytes, label: str) -> str:
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InventoryError(f"{label} is not valid UTF-8") from exc


def _normalize_textdb_source(raw: bytes, label: str) -> str:
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    _require(b"\0" not in normalized, f"{label} contains an embedded NUL byte")
    return _decode_utf8(normalized, label)


def _source_snapshot_at_oid(oid: str, source_name: str, label: str) -> str:
    path = PurePosixPath("crawl-ref/source/dat") / PurePosixPath(source_name)
    return _normalize_textdb_source(
        _git_blob_at_oid(oid, path.as_posix(), label), label
    )


def _english_source_manifest(oid: str, label: str) -> list[str]:
    database = _decode_utf8(
        _git_blob_at_oid(oid, "crawl-ref/source/database.cc", label), label
    )
    matches = list(re.finditer(
        r'\bTextDB\s*\(\s*"speak"\s*,\s*"database/"\s*,\s*\{(.*?)\}\s*\)',
        database, re.DOTALL,
    ))
    _require(len(matches) == 1,
             f"{label} database.cc must have one literal SpeakDB initializer")
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
                     f"{label} SpeakDB initializer is not a literal list")
            end = body.find('"', position + 1)
            _require(end >= 0 and "\\" not in body[position + 1:end],
                     f"{label} SpeakDB source literal is malformed")
            filename = body[position + 1:end]
            _require(bool(re.fullmatch(r"[A-Za-z0-9_]+\.txt", filename)),
                     f"{label} has unsafe SpeakDB source {filename!r}")
            _require(filename not in files,
                     f"{label} has duplicate SpeakDB source {filename!r}")
            files.append(filename)
            position = end + 1
            expect_value = False
        else:
            _require(body[position] == ',',
                     f"{label} SpeakDB source literals must be comma separated")
            position += 1
            expect_value = True
    _require(bool(files), f"{label} SpeakDB source manifest is empty")
    return [f"database/{filename}" for filename in files]


def _localized_source_manifest(oid: str, label: str) -> list[str]:
    raw = _git_output([
        "ls-tree", "-z", f"{oid}:crawl-ref/source/dat/database/zh",
    ], label)
    filenames: list[str] = []
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
        filename = _decode_utf8(encoded_name, label)
        _require(filename not in {"", ".", ".."} and "/" not in filename,
                 f"{label} has unsafe direct source name {filename!r}")
        # get_dir_files_ext(..., "txt") uses a byte suffix, not a glob parser.
        if filename.endswith("txt"):
            filenames.append(filename)
    _require(len(filenames) == len(set(filenames)),
             f"{label} has duplicate localized source names")
    filenames.sort(key=lambda value: value.encode("utf-8"))
    if "source.txt" in filenames:
        filenames.remove("source.txt")
        filenames.insert(0, "source.txt")
    _require(bool(filenames), f"{label} localized source manifest is empty")
    return [f"database/zh/{filename}" for filename in filenames]


def _parse_weighted_entry(
    body: str, provenance: dict[str, Any], canonical_key: str,
) -> tuple[list[dict[str, Any]], str | None]:
    lines = body.split("\n")
    variants: list[dict[str, Any]] = []
    index = 0
    while index < len(lines):
        while index < len(lines) and lines[index] == "":
            index += 1
        if index == len(lines):
            break
        weight = 10
        matched = re.match(r"w:[ \t\v\f\r]*([+-]?[0-9]+)", lines[index])
        if matched:
            weight = int(matched.group(1))
            _require(INT_MIN <= weight <= INT_MAX,
                     f"{canonical_key!r} weight is outside C++ int range")
            index += 1
            if index == len(lines):
                return variants, "BUG, WEIGHT AT END OF ENTRY"
        part: list[str] = []
        while index < len(lines) and lines[index] != "":
            part.append(lines[index])
            index += 1
        pattern = trim_string("\n".join(part) + ("\n" if part else ""))
        ordinal = len(variants)
        variants.append({
            "locator": {
                "canonical_key": canonical_key,
                "variant_ordinal": ordinal,
            },
            "provenance": provenance,
            "weight": weight,
            "raw_pattern": pattern,
        })
    return (variants, None) if variants else ([], "BUG, EMPTY ENTRY")


def _derive_scoped_from_sources(
    sources: list[dict[str, Any]], directory: str, label: str,
) -> dict[str, Any]:
    parsed = []
    provenance_by_entry: dict[int, dict[str, Any]] = {}
    histories: dict[str, list[dict[str, Any]]] = {}
    scoped_keys: set[str] = set()
    monflee_source = f"{directory}{SCOPE['source_basename']}"
    for load_index, source in enumerate(sources):
        try:
            definitions = parse_db_keys(
                source["normalized_utf8"], source["source_name"]
            )
        except SystemExit as exc:
            raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
        for ordinal, definition in enumerate(definitions):
            canonical_key = lowercase_string(definition.raw_key)
            provenance = {
                "source_name": source["source_name"],
                "load_index": load_index,
                "definition_ordinal": ordinal,
            }
            parsed.append(definition)
            provenance_by_entry[id(definition)] = provenance
            histories.setdefault(canonical_key, []).append(provenance)
            if source["source_name"] == monflee_source:
                scoped_keys.add(canonical_key)
    try:
        effective, _overrides = merge_desc_sequence(parsed)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB merge failed: {exc}") from exc
    entries = []
    for canonical_key in sorted(scoped_keys):
        winner = effective[canonical_key]
        provenance = provenance_by_entry[id(winner)]
        variants, parse_error = _parse_weighted_entry(
            winner.value, provenance, canonical_key
        )
        entries.append({
            "canonical_key": canonical_key,
            "effective_provenance": provenance,
            "raw_body": winner.value,
            "source_history": histories[canonical_key],
            "variants": variants,
            "parse_error": parse_error,
            "body_empty": winner.value == "",
        })
    return {"sources": sources, "entries": entries}


def _derive_scoped_dump(oid: str, directory: str, label: str) -> dict[str, Any]:
    manifest = (
        _english_source_manifest(oid, label)
        if directory == "database/"
        else _localized_source_manifest(oid, label)
    )
    sources = [
        {
            "source_name": source_name,
            "load_index": load_index,
            "normalized_utf8": _source_snapshot_at_oid(
                oid, source_name, f"{label} {source_name}"
            ),
        }
        for load_index, source_name in enumerate(manifest)
    ]
    return _derive_scoped_from_sources(sources, directory, label)


def _require_scoped_derivation(
    supplied: dict[str, Any], derived: dict[str, Any], label: str,
) -> None:
    _require(
        supplied["sources"] == derived["sources"],
        f"{label} source manifest/order/snapshots do not match exact Git inputs",
    )
    monflee_source = f"{supplied['source_directory']}{SCOPE['source_basename']}"
    touching = [
        entry for entry in supplied["entries"]
        if any(item["source_name"] == monflee_source
               for item in entry["source_history"])
    ]
    _require(
        touching == derived["entries"],
        f"{label} scoped history/raw_body/variants do not match exact Git derivation",
    )


def _load_dump(
    path: Path, label: str, expected_directory: str,
) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InventoryError(f"cannot read {label} production dump {path}: {exc}") from exc
    try:
        validate_artifact(value, f"{label} production dump")
    except ArtifactError as exc:
        raise InventoryError(str(exc)) from exc
    _require(
        value["source_directory"] == expected_directory,
        f"{label} source_directory must be exactly {expected_directory!r}",
    )
    return value, raw


def _control_prefix(pattern: str) -> str | None:
    match = CONTROL_RE.match(pattern)
    return match.group(1) if match else None


def _runtime_tokens(pattern: str) -> list[str]:
    sites, unbalanced = textdb_marker_sites(pattern)
    _require(unbalanced is None, f"unbalanced runtime token marker at offset {unbalanced}")
    return [f"@{site['token']}@" for site in sites]


def _dump_binding(
    artifact: dict[str, Any], raw: bytes, label: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    directory = artifact["source_directory"]
    expected_source = f"{directory}{SCOPE['source_basename']}"
    matching_sources = [
        source for source in artifact["sources"]
        if source["source_name"] == expected_source
    ]
    _require(
        len(matching_sources) == 1,
        f"{label} dump must contain exactly one source snapshot {expected_source!r}",
    )
    touching = [
        entry for entry in artifact["entries"]
        if any(item["source_name"] == expected_source for item in entry["source_history"])
    ]
    for entry in touching:
        key = entry["canonical_key"]
        _require(entry["parse_error"] is None, f"{label} key {key!r} has parse error")
        _require(not entry["body_empty"], f"{label} key {key!r} has an empty body")
        _require(
            len(entry["source_history"]) == 1,
            f"{label} key {key!r} is overridden",
        )
        _require(
            entry["effective_provenance"]["source_name"] == expected_source,
            f"{label} key {key!r} is not effective from monflee.txt",
        )

    expected_keys = {item["key"] for item in SCOPE["identities"]}
    actual_keys = {entry["canonical_key"] for entry in touching}
    _require(
        actual_keys == expected_keys,
        f"{label} monflee key set mismatch: expected {sorted(expected_keys)!r}, "
        f"got {sorted(actual_keys)!r}",
    )
    ordinals = sorted(entry["effective_provenance"]["definition_ordinal"] for entry in touching)
    _require(
        ordinals == list(range(len(ordinals))),
        f"{label} monflee definition ordinals are not contiguous from zero: {ordinals!r}",
    )

    rows: list[dict[str, Any]] = []
    for entry in sorted(touching, key=lambda item: item["canonical_key"]):
        variants = []
        seen_locators: set[tuple[str, int]] = set()
        for expected_ordinal, variant in enumerate(entry["variants"]):
            locator = variant["locator"]
            locator_key = (locator["canonical_key"], locator["variant_ordinal"])
            _require(locator_key not in seen_locators,
                     f"{label} duplicate variant locator {locator_key!r}")
            seen_locators.add(locator_key)
            _require(locator["variant_ordinal"] == expected_ordinal,
                     f"{label} ordinal gap for {entry['canonical_key']!r}")
            prefix = _control_prefix(variant["raw_pattern"])
            _require(prefix in ALLOWED_CONTROLS,
                     f"{label} unrecognized control prefix {prefix!r}")
            variants.append({
                "locator": {
                    "key": entry["canonical_key"],
                    "variant_ordinal": expected_ordinal,
                },
                "weight": variant["weight"],
                "control_prefix": prefix,
                "runtime_tokens": _runtime_tokens(variant["raw_pattern"]),
                "raw_pattern": variant["raw_pattern"],
            })
        rows.append({
            "key": entry["canonical_key"],
            "effective_source": expected_source,
            "definition_ordinal": entry["effective_provenance"]["definition_ordinal"],
            "variants": variants,
        })

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
        "effective_monflee_source": expected_source,
    }
    return binding, rows


def _topology(row: dict[str, Any]) -> list[tuple[int, str | None, tuple[str, ...]]]:
    return [
        (variant["weight"], variant["control_prefix"], tuple(variant["runtime_tokens"]))
        for variant in row["variants"]
    ]


def _paired_entries(
    en_rows: list[dict[str, Any]], zh_rows: list[dict[str, Any]], label: str,
) -> list[dict[str, Any]]:
    en_by_key = {row["key"]: row for row in en_rows}
    zh_by_key = {row["key"]: row for row in zh_rows}
    _require(en_by_key.keys() == zh_by_key.keys(), f"{label} EN/ZH key sets differ")
    entries = []
    identities = {item["key"]: item["identity"] for item in SCOPE["identities"]}
    for key in sorted(en_by_key):
        en = en_by_key[key]
        zh = zh_by_key[key]
        _require(len(en["variants"]) == len(zh["variants"]),
                 f"{label} variant count differs for {key!r}")
        _require(_topology(en) == _topology(zh),
                 f"{label} weight/control/token topology differs for {key!r}")
        variants = []
        for en_variant, zh_variant in zip(en["variants"], zh["variants"]):
            variants.append({
                "locator": en_variant["locator"],
                "weight": en_variant["weight"],
                "control_prefix": en_variant["control_prefix"],
                "runtime_tokens": en_variant["runtime_tokens"],
                "english": en_variant["raw_pattern"],
                "chinese": zh_variant["raw_pattern"],
            })
        entries.append({"identity": identities[key], "key": key, "variants": variants})
    return entries


def build_inventory(
    baseline_ref: str, english_path: Path, localized_path: Path, glossary_path: Path,
) -> dict[str, Any]:
    _validate_oid(baseline_ref, "baseline")
    en_dump, en_raw = _load_dump(english_path, "baseline EN", "database/")
    zh_dump, zh_raw = _load_dump(
        localized_path, "baseline ZH", "database/zh/"
    )
    _require_scoped_derivation(
        en_dump, _derive_scoped_dump(
            baseline_ref, "database/", "baseline EN"
        ), "baseline EN",
    )
    _require_scoped_derivation(
        zh_dump, _derive_scoped_dump(
            baseline_ref, "database/zh/", "baseline ZH"
        ), "baseline ZH",
    )
    en_binding, en_rows = _dump_binding(en_dump, en_raw, "baseline EN")
    zh_binding, zh_rows = _dump_binding(zh_dump, zh_raw, "baseline ZH")
    entries = _paired_entries(en_rows, zh_rows, "baseline")
    try:
        glossary_sha256 = _sha256(glossary_path.read_bytes())
    except OSError as exc:
        raise InventoryError(f"cannot read glossary {glossary_path}: {exc}") from exc
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": SCOPE,
        "scope_sha256": _sha256(_canonical_json(SCOPE)),
        "glossary": {"path": "docs/glossary.md", "sha256": glossary_sha256},
        "dumps": {"english": en_binding, "localized": zh_binding},
        "entries": entries,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _strict_block(path: Path) -> list[dict[str, Any]]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InventoryError(f"cannot read review results {path}: {exc}") from exc
    _require(text.count(STRICT_BEGIN) == 1, "review results require exactly one strict begin marker")
    _require(text.count(STRICT_END) == 1, "review results require exactly one strict end marker")
    begin = text.index(STRICT_BEGIN) + len(STRICT_BEGIN)
    end = text.index(STRICT_END, begin)
    body = text[begin:end].strip()
    match = re.fullmatch(r"```jsonl\s*\n(.*?)\n```", body, re.DOTALL)
    _require(match is not None, "strict review evidence must be one fenced jsonl block")
    lines = [line for line in match.group(1).splitlines() if line.strip()]
    records = []
    for line_number, line in enumerate(lines, 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InventoryError(f"invalid review JSONL line {line_number}: {exc}") from exc
        _require(isinstance(value, dict), f"review JSONL line {line_number} must be an object")
        records.append(value)
    return records


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_exact_fields(
    record: dict[str, Any], expected: set[str], context: str,
) -> None:
    actual = set(record)
    _require(
        actual == expected,
        f"{context} field set mismatch: missing {sorted(expected - actual)!r}, "
        f"unknown {sorted(actual - expected)!r}",
    )


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


def _expected_production_facts(
    inventory: dict[str, Any], entry: dict[str, Any],
) -> dict[str, Any]:
    variants = entry["variants"]
    return {
        "english_source": inventory["dumps"]["english"]["effective_monflee_source"],
        "localized_source": inventory["dumps"]["localized"]["effective_monflee_source"],
        "variant_count": len(variants),
        "weights": [variant["weight"] for variant in variants],
        "control_prefixes": [variant["control_prefix"] for variant in variants],
        "runtime_tokens": [list(variant["runtime_tokens"]) for variant in variants],
    }


def _validate_production_evidence(
    card: dict[str, Any], inventory: dict[str, Any], entry: dict[str, Any],
    identity: str,
) -> None:
    _require(card.get("confidence") in CONFIDENCE_LEVELS,
             f"{identity} confidence must be high, medium, or low")
    _require(
        card.get("dependency_group")
        == f"{entry['key']} voice and visual motion",
        f"{identity} dependency_group mismatch",
    )
    _require(
        card.get("glossary_authority")
        == f"{inventory['glossary']['path']}@{inventory['glossary']['sha256']}",
        f"{identity} glossary_authority mismatch",
    )
    _require(card.get("actual_behavior") == FROZEN_ACTUAL_BEHAVIOR,
             f"{identity} actual_behavior does not match frozen runtime behavior")
    _require(card.get("display_context") == FROZEN_DISPLAY_CONTEXT,
             f"{identity} display_context does not match frozen display scope")
    _require(card.get("consumer") == FROZEN_CONSUMER,
             f"{identity} consumer evidence mismatch")
    _require(card.get("producers") == FROZEN_PRODUCERS,
             f"{identity} producer evidence mismatch")
    _require(card.get("evidence_locations") == FROZEN_EVIDENCE_LOCATIONS,
             f"{identity} evidence_locations mismatch")
    facts = card.get("production_facts")
    _require(
        isinstance(facts, dict) and _is_int(facts.get("variant_count")),
        f"{identity} production_facts.variant_count must be an integer",
    )
    fact_weights = facts.get("weights")
    _require(
        isinstance(fact_weights, list)
        and all(_is_int(weight) for weight in fact_weights),
        f"{identity} production_facts.weights must be an integer array",
    )
    _require(
        facts == _expected_production_facts(inventory, entry),
        f"{identity} production_facts mismatch",
    )
    _require(_nonempty_string(card.get("reentry_trigger")),
             f"{identity} requires a nonempty reentry_trigger")
    alternatives = card.get("rejected_alternatives")
    _require(
        isinstance(alternatives, list) and bool(alternatives)
        and all(_nonempty_string(alternative) for alternative in alternatives),
        f"{identity} rejected_alternatives must be a nonempty string array",
    )
    _require(_nonempty_string(card.get("reviewer_rationale")),
             f"{identity} requires a nonempty reviewer_rationale")


def validate_results(
    path: Path, inventory: dict[str, Any], candidate_entries: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    records = _strict_block(path)
    expected_entries = {entry["identity"]: entry for entry in inventory["entries"]}
    _require(len(records) >= 1, "review evidence is missing metadata")
    metadata, cards = records[0], records[1:]
    _require_exact_fields(metadata, METADATA_FIELDS, "review metadata")
    _require(metadata.get("baseline") == inventory["baseline_ref"],
             "review metadata baseline mismatch")
    _require(metadata.get("glossary_sha256") == inventory["glossary"]["sha256"],
             "review metadata glossary_sha256 mismatch")
    identity_count = metadata.get("identity_count")
    _require(_is_int(identity_count) and identity_count == len(expected_entries),
             "review metadata identity_count mismatch")
    _require(metadata.get("inventory_sha256") == inventory["inventory_sha256"],
             "review metadata inventory_sha256 mismatch")

    seen: dict[str, dict[str, Any]] = {}
    for card in cards:
        _require_exact_fields(card, CARD_FIELDS, "review card")
        identity = card.get("identity")
        _require(isinstance(identity, str), "review card identity must be a string")
        _require(identity not in seen, f"duplicate review card {identity!r}")
        seen[identity] = card
    _require(seen.keys() == expected_entries.keys(),
             f"review card identity set mismatch: expected {sorted(expected_entries)!r}, "
             f"got {sorted(seen)!r}")

    candidate_by_identity = (
        {entry["identity"]: entry for entry in candidate_entries}
        if candidate_entries is not None else None
    )
    for identity, baseline in expected_entries.items():
        card = seen[identity]
        _require(_nonempty_string(card.get("lifecycle")), f"{identity} requires lifecycle")
        conclusion = card.get("terminal_conclusion")
        _require(conclusion in TERMINAL_CONCLUSIONS,
                 f"{identity} has nonterminal conclusion {conclusion!r}")
        _validate_deferral(card, identity)
        _require(card.get("key") == baseline["key"], f"{identity} key mismatch")
        _validate_production_evidence(card, inventory, baseline, identity)
        baseline_en = [variant["english"] for variant in baseline["variants"]]
        baseline_zh = [variant["chinese"] for variant in baseline["variants"]]
        _require(card.get("current_english") == baseline_en,
                 f"{identity} current_english does not match baseline dump")
        _require(card.get("current_chinese") == baseline_zh,
                 f"{identity} current_chinese does not match baseline dump")
        proposed = card.get("proposed_translation")
        _require(isinstance(proposed, list) and all(isinstance(item, str) for item in proposed),
                 f"{identity} proposed_translation must be a string array")
        _require(len(proposed) == len(baseline["variants"]),
                 f"{identity} proposed_translation variant count mismatch")
        reviews = card.get("variant_reviews")
        _require(isinstance(reviews, list), f"{identity} variant_reviews must be an array")
        _require(len(reviews) == len(baseline["variants"]),
                 f"{identity} variant_reviews coverage mismatch")
        ordinals = [review.get("variant_ordinal") for review in reviews
                    if isinstance(review, dict)]
        _require(len(ordinals) == len(reviews), f"{identity} variant review must be an object")
        _require(all(_is_int(ordinal) for ordinal in ordinals),
                 f"{identity} variant ordinals must be integers")
        _require(len(set(ordinals)) == len(ordinals), f"{identity} duplicate variant locator")
        _require(ordinals == list(range(len(baseline["variants"]))),
                 f"{identity} variant reviews must be locator sorted and complete")
        variant_conclusions = []
        for variant, review, proposed_pattern in zip(baseline["variants"], reviews, proposed):
            ordinal = variant["locator"]["variant_ordinal"]
            context = f"{identity} variant {ordinal}"
            variant_conclusion = review.get("terminal_conclusion")
            _require(variant_conclusion in TERMINAL_CONCLUSIONS,
                     f"{context} has nonterminal conclusion {variant_conclusion!r}")
            expected_fields = (
                VARIANT_FIELDS | DEFERRAL_FIELDS
                if variant_conclusion in DEFER_CONCLUSIONS
                else VARIANT_FIELDS
            )
            _require_exact_fields(review, expected_fields, context)
            _require(_is_int(review.get("weight")),
                     f"{context} weight must be an integer")
            for field, expected in (
                ("weight", variant["weight"]),
                ("control_prefix", variant["control_prefix"]),
                ("runtime_tokens", variant["runtime_tokens"]),
                ("english", variant["english"]),
                ("current_chinese", variant["chinese"]),
                ("proposed_translation", proposed_pattern),
            ):
                _require(review.get(field) == expected, f"{context} {field} mismatch")
            _require(_nonempty_string(review.get("rationale")), f"{context} requires rationale")
            if variant_conclusion == "keep":
                _require(proposed_pattern == variant["chinese"],
                         f"{context} keep must preserve current Chinese")
            elif variant_conclusion in {"adjust", "retranslate"}:
                _require(proposed_pattern != variant["chinese"],
                         f"{context} {variant_conclusion} must change current Chinese")
            else:
                _validate_deferral(review, context)
                _require(proposed_pattern == variant["chinese"],
                         f"{context} deferred conclusion must preserve current Chinese")
            variant_conclusions.append(variant_conclusion)
        if conclusion == "keep":
            _require(set(variant_conclusions) == {"keep"},
                     f"{identity} keep conflicts with variant conclusions")
        elif conclusion == "adjust":
            _require("adjust" in variant_conclusions and "retranslate" not in variant_conclusions,
                     f"{identity} adjust conflicts with variant conclusions")
        elif conclusion == "retranslate":
            _require("retranslate" in variant_conclusions,
                     f"{identity} retranslate requires a retranslate variant")
        else:
            _require(conclusion in variant_conclusions,
                     f"{identity} deferred conclusion requires a matching deferred variant")

        if candidate_by_identity is not None:
            candidate = candidate_by_identity[identity]
            candidate_zh = [variant["chinese"] for variant in candidate["variants"]]
            _require(proposed == candidate_zh,
                     f"{identity} proposed translation does not match candidate dump")
            for review, pattern in zip(reviews, candidate_zh):
                _require(review["proposed_translation"] == pattern,
                         f"{identity} variant proposed translation does not match candidate dump")
    return {"metadata": metadata, "cards": cards}


def add_candidate(
    inventory: dict[str, Any], candidate_ref: str, english_path: Path,
    localized_path: Path,
) -> list[dict[str, Any]]:
    _validate_oid(candidate_ref, "candidate")
    _require(candidate_ref != inventory["baseline_ref"],
             "candidate ref must differ from baseline ref")
    repository = Path(__file__).resolve().parents[2]
    ancestry = subprocess.run(
        ["git", "-C", str(repository), "merge-base", "--is-ancestor",
         inventory["baseline_ref"], candidate_ref],
        text=True, capture_output=True, env=trusted_git_environment(),
    )
    _require(
        ancestry.returncode == 0,
        "baseline ref must be an ancestor of candidate ref",
    )
    en_dump, en_raw = _load_dump(english_path, "candidate EN", "database/")
    zh_dump, zh_raw = _load_dump(
        localized_path, "candidate ZH", "database/zh/"
    )
    _require_scoped_derivation(
        en_dump, _derive_scoped_dump(
            candidate_ref, "database/", "candidate EN"
        ), "candidate EN",
    )
    _require_scoped_derivation(
        zh_dump, _derive_scoped_dump(
            candidate_ref, "database/zh/", "candidate ZH"
        ), "candidate ZH",
    )
    en_binding, en_rows = _dump_binding(en_dump, en_raw, "candidate EN")
    zh_binding, zh_rows = _dump_binding(zh_dump, zh_raw, "candidate ZH")
    entries = _paired_entries(en_rows, zh_rows, "candidate")
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
        "dumps": {"english": en_binding, "localized": zh_binding},
        "entries": entries,
    }
    inventory["candidate"]["candidate_sha256"] = _sha256(
        _canonical_json(inventory["candidate"])
    )
    return entries


def _safe_output(path: Path, payload: dict[str, Any]) -> None:
    _require(path.is_absolute(), "inventory output must be an absolute /tmp path")
    _require(path.parent in {Path("/tmp"), Path("/private/tmp")},
             "inventory output must be a direct child of /tmp or /private/tmp")
    resolved_parent = path.parent.resolve(strict=True)
    _require(resolved_parent in {Path("/tmp"), Path("/private/tmp")},
             "inventory output parent must resolve to /tmp or /private/tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        fd = os.open(path, flags, 0o600)
    except OSError as exc:
        raise InventoryError(f"cannot exclusively create inventory output {path}: {exc}") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


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
        args.candidate_ref, args.candidate_english_dump, args.candidate_localized_dump
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
    _safe_output(args.inventory_output, inventory)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"monflee_inventory.py: {exc}", file=sys.stderr)
        raise SystemExit(2)
