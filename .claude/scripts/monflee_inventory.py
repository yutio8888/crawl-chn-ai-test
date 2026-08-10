#!/usr/bin/env python3
"""Build and audit the Issue #54 monflee inventory from production dumps.

This is deliberately a consumer of ``textdb-phase0-dump`` JSON.  The C++
dump and :mod:`audit_monspell_phase0` remain the parser/schema authorities;
this module only selects the effective monflee source and compares its already
parsed variants.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any

from audit_monspell_phase0 import ArtifactError, textdb_marker_sites, validate_artifact


SCHEMA_VERSION = 1
STRICT_BEGIN = "<!-- BEGIN STRICT MONFLEE REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT MONFLEE REVIEW EVIDENCE v1 -->"
OID_RE = re.compile(r"^[0-9a-f]{40}$")
CONTROL_RE = re.compile(r"^([A-Z][A-Z0-9_]*):")
ALLOWED_CONTROLS = {None, "VISUAL"}
DEFER_CONCLUSIONS = {"defer terminology", "defer implementation"}
TERMINAL_CONCLUSIONS = {"keep", "adjust", "retranslate", *DEFER_CONCLUSIONS}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
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
    "随后展开怪物 token。普通正文走 MSGCH_TALK 并受沉默影响；VISUAL 正文走 "
    "MSGCH_TALK_VISUAL，仅怪物可见时显示且不因沉默消失。"
)
FROZEN_DISPLAY_CONTEXT = "怪物首次受惊逃跑或 Xom 梦羊事件触发的玩家可见消息。"
FROZEN_CONSUMER = {
    "channel_routing": "crawl-ref/source/mon-speak.cc:851",
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
        text=True, capture_output=True,
    )
    _require(checked.returncode == 0, f"{label} ref is not a commit in this repository")


def _source_snapshot_at_oid(oid: str, source_name: str, label: str) -> str:
    source_path = PurePosixPath(source_name)
    _require(
        not source_path.is_absolute()
        and source_path.as_posix() == source_name
        and all(part not in {"", ".", ".."} for part in source_path.parts),
        f"{label} source snapshot has an unsafe source_name {source_name!r}",
    )
    repository = Path(__file__).resolve().parents[2]
    git_path = PurePosixPath("crawl-ref/source/dat") / source_path
    fetched = subprocess.run(
        ["git", "-C", str(repository), "show", f"{oid}:{git_path.as_posix()}"],
        capture_output=True,
    )
    _require(fetched.returncode == 0,
             f"{label} source snapshot is missing at {oid}:{git_path.as_posix()}")
    try:
        return fetched.stdout.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InventoryError(
            f"{label} source snapshot is not UTF-8 at {oid}:{git_path.as_posix()}"
        ) from exc


def _extract_git_archive(archive: bytes, destination: Path, label: str) -> None:
    try:
        stream = tarfile.open(fileobj=io.BytesIO(archive), mode="r:")
    except tarfile.TarError as exc:
        raise InventoryError(f"cannot read {label} Git archive: {exc}") from exc
    with stream:
        for member in stream:
            relative = PurePosixPath(member.name)
            _require(
                not relative.is_absolute()
                and all(part not in {"", ".", ".."} for part in relative.parts),
                f"{label} Git archive contains unsafe path {member.name!r}",
            )
            target = destination.joinpath(*relative.parts)
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            _require(member.isfile(),
                     f"{label} Git archive contains unsupported object {member.name!r}")
            source = stream.extractfile(member)
            _require(source is not None,
                     f"{label} Git archive cannot extract {member.name!r}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read())


def _run_production_dump(
    executable: Path, source_root: Path, output: Path, language: str | None,
) -> dict[str, Any]:
    environment = os.environ.copy()
    environment["TEXTDB_PHASE0_DUMP"] = str(output)
    if language is None:
        environment.pop("TEXTDB_PHASE0_LANGUAGE", None)
    else:
        environment["TEXTDB_PHASE0_LANGUAGE"] = language
    completed = subprocess.run(
        [str(executable), "[.textdb-phase0-dump]", "--reporter", "compact"],
        cwd=source_root, env=environment, text=True, capture_output=True,
    )
    locale = language or "en"
    _require(
        completed.returncode == 0,
        f"production {locale} dump replay failed: "
        f"{(completed.stderr or completed.stdout)[-2000:]}",
    )
    artifact, _raw = _load_dump(
        output, f"trusted {locale}",
        "database/" if language is None else f"database/{language}/",
    )
    return artifact


@lru_cache(maxsize=4)
def _trusted_artifacts_at_oid(oid: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Replay production source discovery/parser against an exact Git tree."""
    _validate_oid(oid, "production replay")
    repository = Path(__file__).resolve().parents[2]
    executable = repository / "crawl-ref/source/catch2-tests-executable"
    _require(
        executable.is_file() and not executable.is_symlink()
        and os.access(executable, os.X_OK),
        "production dump executable is missing; build "
        "crawl-ref/source/catch2-tests-executable first",
    )
    archived = subprocess.run(
        ["git", "-C", str(repository), "archive", oid, "--",
         "crawl-ref/source/dat"],
        capture_output=True,
    )
    _require(archived.returncode == 0,
             "cannot archive exact-OID production data tree")
    with tempfile.TemporaryDirectory(prefix="monflee-production-replay-") as temp:
        temporary = Path(temp)
        _extract_git_archive(archived.stdout, temporary, "production replay")
        source_root = temporary / "crawl-ref/source"
        generated_tags = repository / "crawl-ref/source/dat/dlua/tags.lua"
        _require(generated_tags.is_file() and not generated_tags.is_symlink(),
                 "generated dat/dlua/tags.lua required by production replay is missing")
        # The Catch2 main loads this generated file while initializing clua.  The
        # phase-0 dump entry point then calls dump_*_speakdb_typed(), which only
        # discovers, normalizes, and parses the staged TextDB sources; unlike
        # getSpeakString(), that path never executes embedded Lua.  tags.lua is
        # therefore startup support, not an input to the replayed artifact.
        replay_tags = source_root / "dat/dlua/tags.lua"
        replay_tags.parent.mkdir(parents=True, exist_ok=True)
        replay_tags.write_bytes(generated_tags.read_bytes())
        english = _run_production_dump(
            executable, source_root, temporary / "english.json", None
        )
        localized = _run_production_dump(
            executable, source_root, temporary / "localized.json", "zh"
        )
    return english, localized


def _require_production_derivation(
    supplied: dict[str, Any], trusted: dict[str, Any], label: str,
) -> None:
    _require(
        supplied["sources"] == trusted["sources"],
        f"{label} source discovery/order does not match exact-OID production replay",
    )
    _require(
        supplied["entries"] == trusted["entries"],
        f"{label} entries/raw_body/variants do not match exact-OID production replay",
    )
    _require(
        supplied == trusted,
        f"{label} artifact metadata does not match exact-OID production replay",
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
    artifact: dict[str, Any], raw: bytes, label: str, oid: str,
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
    for source in artifact["sources"]:
        committed = _source_snapshot_at_oid(oid, source["source_name"], label)
        _require(
            source["normalized_utf8"] == committed,
            f"{label} source snapshot does not match OID for {source['source_name']!r}",
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
    trusted_en, trusted_zh = _trusted_artifacts_at_oid(baseline_ref)
    _require_production_derivation(en_dump, trusted_en, "baseline EN")
    _require_production_derivation(zh_dump, trusted_zh, "baseline ZH")
    en_binding, en_rows = _dump_binding(en_dump, en_raw, "baseline EN", baseline_ref)
    zh_binding, zh_rows = _dump_binding(zh_dump, zh_raw, "baseline ZH", baseline_ref)
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


def _validate_deferral(record: dict[str, Any], context: str) -> None:
    conclusion = record.get("terminal_conclusion")
    if conclusion in DEFER_CONCLUSIONS:
        for field in ("deferral_owner", "deferral_reason", "reentry_trigger"):
            _require(_nonempty_string(record.get(field)),
                     f"{context} deferred conclusion requires {field}")


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
    _require(
        card.get("production_facts") == _expected_production_facts(inventory, entry),
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
    _require(metadata.get("baseline") == inventory["baseline_ref"],
             "review metadata baseline mismatch")
    _require(metadata.get("glossary_sha256") == inventory["glossary"]["sha256"],
             "review metadata glossary_sha256 mismatch")
    _require(metadata.get("identity_count") == len(expected_entries),
             "review metadata identity_count mismatch")
    _require(metadata.get("inventory_sha256") == inventory["inventory_sha256"],
             "review metadata inventory_sha256 mismatch")

    seen: dict[str, dict[str, Any]] = {}
    for card in cards:
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
        _require(len(set(ordinals)) == len(ordinals), f"{identity} duplicate variant locator")
        _require(ordinals == list(range(len(baseline["variants"]))),
                 f"{identity} variant reviews must be locator sorted and complete")
        variant_conclusions = []
        for variant, review, proposed_pattern in zip(baseline["variants"], reviews, proposed):
            ordinal = variant["locator"]["variant_ordinal"]
            context = f"{identity} variant {ordinal}"
            for field, expected in (
                ("weight", variant["weight"]),
                ("control_prefix", variant["control_prefix"]),
                ("runtime_tokens", variant["runtime_tokens"]),
                ("english", variant["english"]),
                ("current_chinese", variant["chinese"]),
                ("proposed_translation", proposed_pattern),
            ):
                _require(review.get(field) == expected, f"{context} {field} mismatch")
            variant_conclusion = review.get("terminal_conclusion")
            _require(variant_conclusion in TERMINAL_CONCLUSIONS,
                     f"{context} has nonterminal conclusion {variant_conclusion!r}")
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
            _validate_deferral(card, identity)
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
        text=True, capture_output=True,
    )
    _require(
        ancestry.returncode == 0,
        "baseline ref must be an ancestor of candidate ref",
    )
    en_dump, en_raw = _load_dump(english_path, "candidate EN", "database/")
    zh_dump, zh_raw = _load_dump(
        localized_path, "candidate ZH", "database/zh/"
    )
    trusted_en, trusted_zh = _trusted_artifacts_at_oid(candidate_ref)
    _require_production_derivation(en_dump, trusted_en, "candidate EN")
    _require_production_derivation(zh_dump, trusted_zh, "candidate ZH")
    en_binding, en_rows = _dump_binding(en_dump, en_raw, "candidate EN", candidate_ref)
    zh_binding, zh_rows = _dump_binding(zh_dump, zh_raw, "candidate ZH", candidate_ref)
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
