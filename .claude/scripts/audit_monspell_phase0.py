#!/usr/bin/env python3
"""Build the Phase-0 monspell inventory from a production C++ TextDB dump.

The C++ canonical dump is the sole parser authority.  This consumer validates
its protocol, derives the monspell recursive closure, and performs only static
inspection of already parsed raw patterns.  It never reparses TextDB source or
weighted entries.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


SCHEMA_VERSION = 1
ARTIFACT_SCHEMA_VERSION = 1
_LUA_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
_CONTROL_RE = re.compile(r"^([A-Z][A-Z0-9_]*):")
MAX_RECURSION_DEPTH = 10
MAX_REPLACEMENTS = 100
ARTIFACT_FIELDS = {
    "schema_version", "database_name", "source_directory", "sources", "entries",
}
SOURCE_FIELDS = {"source_name", "load_index", "normalized_utf8"}
ENTRY_FIELDS = {
    "canonical_key", "effective_provenance", "raw_body", "source_history",
    "variants", "parse_error", "body_empty",
}
PROVENANCE_FIELDS = {"source_name", "load_index", "definition_ordinal"}
VARIANT_FIELDS = {"locator", "provenance", "weight", "raw_pattern"}
LOCATOR_FIELDS = {"canonical_key", "variant_ordinal"}


class ArtifactError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactKeySets:
    """Lookup-relevant views of a fully validated production artifact."""

    reserved: frozenset[str]
    selectable: frozenset[str]
    empty: frozenset[str]
    corrupt: frozenset[str]


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _framed_source_fingerprint(files: Iterable[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    digest.update(f"monspell-phase0-source-v{SCHEMA_VERSION}\0".encode())
    for name, data in files:
        encoded = name.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ArtifactError(message)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require_exact_fields(
    value: object, expected: set[str], context: str,
) -> dict[str, Any]:
    _require(isinstance(value, dict), f"{context} must be an object")
    actual = set(value)
    _require(
        actual == expected,
        f"{context} field set mismatch: missing {sorted(expected - actual)!r}, "
        f"unknown {sorted(actual - expected)!r}",
    )
    return value


def _validate_provenance(
    value: object,
    context: str,
    source_indexes: dict[str, int],
) -> dict[str, Any]:
    value = _require_exact_fields(value, PROVENANCE_FIELDS, context)
    source_name = value.get("source_name")
    load_index = value.get("load_index")
    ordinal = value.get("definition_ordinal")
    _require(isinstance(source_name, str), f"{context}.source_name must be a string")
    _require(source_name in source_indexes, f"{context}.source_name is not in sources")
    _require(_is_int(load_index), f"{context}.load_index must be an integer")
    _require(load_index == source_indexes[source_name],
             f"{context}.load_index does not match source")
    _require(_is_int(ordinal),
             f"{context}.definition_ordinal must be an integer")
    _require(ordinal >= 0,
             f"{context}.definition_ordinal must be non-negative")
    return value


def validate_artifact(
    artifact: object, label: str = "canonical dump",
) -> ArtifactKeySets:
    artifact = _require_exact_fields(
        artifact, ARTIFACT_FIELDS, "canonical dump"
    )
    _require(_is_int(artifact["schema_version"]),
             "artifact schema_version must be an integer")
    _require(artifact["schema_version"] == ARTIFACT_SCHEMA_VERSION,
             f"unsupported artifact schema_version {artifact.get('schema_version')!r}")
    _require(artifact.get("database_name") in ("speak", "misc"),
             "artifact database_name must be 'speak' or 'misc'")
    directory = artifact.get("source_directory")
    _require(isinstance(directory, str) and directory,
             "artifact source_directory must be a non-empty string")

    sources = artifact.get("sources")
    _require(isinstance(sources, list) and sources,
             "artifact sources must be a non-empty array")
    source_indexes: dict[str, int] = {}
    for expected_index, source in enumerate(sources):
        context = f"sources[{expected_index}]"
        source = _require_exact_fields(source, SOURCE_FIELDS, context)
        name = source.get("source_name")
        load_index = source.get("load_index")
        normalised = source.get("normalized_utf8")
        _require(isinstance(name, str) and name,
                 f"{context}.source_name must be a non-empty string")
        _require(name not in source_indexes, f"duplicate source_name {name!r}")
        _require(_is_int(load_index), f"{context}.load_index must be an integer")
        _require(load_index == expected_index,
                 f"{context}.load_index must be contiguous and ordered")
        _require(isinstance(normalised, str),
                 f"{context}.normalized_utf8 must be a string")
        _require(name.startswith(directory),
                 f"{context}.source_name must be under source_directory")
        source_indexes[name] = expected_index

    entries = artifact.get("entries")
    _require(isinstance(entries, list), "artifact entries must be an array")
    previous_key: str | None = None
    selectable: set[str] = set()
    empty_keys: set[str] = set()
    corrupt: set[str] = set()
    for entry_index, entry in enumerate(entries):
        context = f"entries[{entry_index}]"
        entry = _require_exact_fields(entry, ENTRY_FIELDS, context)
        key = entry.get("canonical_key")
        _require(isinstance(key, str) and key,
                 f"{context}.canonical_key must be a non-empty string")
        _require(previous_key is None or previous_key < key,
                 "entries canonical_key values must be strictly sorted and unique")
        previous_key = key

        effective = _validate_provenance(
            entry.get("effective_provenance"), f"{context}.effective_provenance",
            source_indexes,
        )
        history = entry.get("source_history")
        _require(isinstance(history, list) and history,
                 f"{context}.source_history must be a non-empty array")
        validated_history = [
            _validate_provenance(item, f"{context}.source_history[{index}]", source_indexes)
            for index, item in enumerate(history)
        ]
        order = [(item["load_index"], item["definition_ordinal"])
                 for item in validated_history]
        _require(all(left < right for left, right in zip(order, order[1:])),
                 f"{context}.source_history must be strictly ordered and unique")
        _require(effective == validated_history[-1],
                 f"{context}.effective_provenance must equal source_history last")

        raw_body = entry.get("raw_body")
        body_empty = entry.get("body_empty")
        parse_error = entry.get("parse_error")
        _require(isinstance(raw_body, str), f"{context}.raw_body must be a string")
        _require(isinstance(body_empty, bool), f"{context}.body_empty must be a boolean")
        _require(body_empty == (raw_body == ""),
                 f"{context}.body_empty does not match raw_body")
        _require(parse_error is None or isinstance(parse_error, str),
                 f"{context}.parse_error must be null or a string")

        variants = entry.get("variants")
        _require(isinstance(variants, list), f"{context}.variants must be an array")
        if parse_error is None and not body_empty:
            _require(bool(variants), f"{context} non-empty parsed body has no variants")
        if parse_error is not None or body_empty:
            _require(not variants, f"{context} errored/empty body must have no variants")
        for ordinal, variant in enumerate(variants):
            vcontext = f"{context}.variants[{ordinal}]"
            variant = _require_exact_fields(variant, VARIANT_FIELDS, vcontext)
            locator = _require_exact_fields(
                variant.get("locator"), LOCATOR_FIELDS, f"{vcontext}.locator"
            )
            _require(locator.get("canonical_key") == key,
                     f"{vcontext}.locator canonical_key mismatch")
            _require(_is_int(locator.get("variant_ordinal")),
                     f"{vcontext}.locator variant_ordinal must be an integer")
            _require(locator.get("variant_ordinal") == ordinal,
                     f"{vcontext}.locator variant_ordinal must be contiguous")
            _require(variant.get("provenance") == effective,
                     f"{vcontext}.provenance must match effective provenance")
            _validate_provenance(variant.get("provenance"),
                                 f"{vcontext}.provenance", source_indexes)
            _require(_is_int(variant.get("weight")),
                     f"{vcontext}.weight must be an integer")
            _require(isinstance(variant.get("raw_pattern"), str),
                     f"{vcontext}.raw_pattern must be a string")
        if parse_error is not None:
            corrupt.add(key)
        elif body_empty:
            empty_keys.add(key)
        else:
            selectable.add(key)
    return ArtifactKeySets(
        reserved=frozenset(entry["canonical_key"] for entry in entries),
        selectable=frozenset(selectable),
        empty=frozenset(empty_keys),
        corrupt=frozenset(corrupt),
    )


def load_artifact(path: Path) -> dict[str, Any]:
    try:
        artifact = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ArtifactError(f"cannot read canonical dump {path}: {exc}") from exc
    validate_artifact(artifact, f"canonical dump {path}")
    return artifact


def _random_sites(text: str) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    start = 0
    while True:
        begin = text.find("[", start)
        if begin < 0:
            break
        end = text.find("]", begin)
        if end < 0:
            break
        raw = text[begin + 1:end]
        result.append({"start": begin, "end": end + 1, "raw": raw,
                       "options": raw.split("|")})
        start = end + 1
    return result


def textdb_marker_sites(text: str) -> tuple[list[dict[str, object]], int | None]:
    """Mirror runtime left-to-right next-@ pairing, with Python string offsets."""
    markers: list[dict[str, object]] = []
    position = text.find("@")
    while position >= 0:
        end = text.find("@", position + 1)
        if end < 0:
            return markers, position
        token = text[position + 1:end]
        markers.append({
            "token": token,
            "canonical_key": token.lower(),
            "start": position,
            "end": end + 1,
        })
        position = text.find("@", end + 1)
    return markers, None


def _unbalanced_lua_offset(text: str) -> int | None:
    position = text.find("{{")
    while position >= 0:
        end = text.find("}}", position + 2)
        if end < 0:
            return position
        position = text.find("{{", end + 2)
    return None


def _reachable_variants(entry: dict[str, Any]) -> list[dict[str, Any]]:
    variants = entry["variants"]
    total = sum(variant["weight"] for variant in variants)
    if total <= 0:
        return []
    reachable = []
    cumulative = 0
    previous_max = 0
    for variant in variants:
        cumulative += variant["weight"]
        # Production chooses the first variant whose cumulative bound exceeds
        # choice. Therefore a later variant is reachable only above every
        # earlier cumulative bound, not merely above the immediately preceding
        # one (which may have fallen because negative weights are accepted).
        if previous_max < min(cumulative, total):
            reachable.append(variant)
        previous_max = max(previous_max, cumulative)
    return reachable


def _validate_static_closure(
    entries: dict[str, dict[str, Any]], roots: set[str], selectable: set[str],
) -> None:
    dependencies: dict[str, list[tuple[int, list[str]]]] = {}
    problems: list[str] = []
    pending = sorted(roots)
    visited: set[str] = set()
    while pending:
        key = pending.pop(0)
        if key in visited or key not in selectable:
            continue
        visited.add(key)
        variants = _reachable_variants(entries[key])
        if not variants:
            problems.append(f"{key!r} has no statically selectable weighted variant")
            dependencies[key] = []
            continue
        dependencies[key] = []
        for ordinal, variant in enumerate(variants):
            text = variant["raw_pattern"]
            markers, unbalanced = textdb_marker_sites(text)
            if unbalanced is not None:
                problems.append(
                    f"{key!r} has an unbalanced @ marker at offset {unbalanced}"
                )
            lua_offset = _unbalanced_lua_offset(text)
            if lua_offset is not None:
                problems.append(
                    f"{key!r} has an unbalanced Lua site at offset {lua_offset}"
                )
            children = [str(marker["canonical_key"]) for marker in markers
                        if marker["canonical_key"] in selectable]
            dependencies[key].append((len(markers), children))
            pending.extend(child for child in children if child not in visited)

    memo: dict[str, tuple[int, int]] = {}

    def limits(key: str, stack: tuple[str, ...]) -> tuple[int, int]:
        if key in stack:
            cycle = " -> ".join(stack[stack.index(key):] + (key,))
            problems.append(f"recursive closure cycle: {cycle}")
            return MAX_RECURSION_DEPTH + 1, MAX_REPLACEMENTS + 1
        if key in memo:
            return memo[key]
        max_depth = 1
        max_replacements = 0
        for marker_count, children in dependencies.get(key, []):
            variant_depth = 1
            # Every paired marker consumes one replacement, including runtime
            # slots that do not resolve through SpeakDB.
            variant_replacements = marker_count
            for child in children:
                child_depth, child_replacements = limits(child, stack + (key,))
                variant_depth = max(variant_depth, 1 + child_depth)
                variant_replacements += child_replacements
            max_depth = max(max_depth, variant_depth)
            max_replacements = max(max_replacements, variant_replacements)
        memo[key] = max_depth, max_replacements
        return memo[key]

    for root in sorted(roots & selectable):
        depth, replacements = limits(root, ())
        if depth > MAX_RECURSION_DEPTH:
            problems.append(
                f"{root!r} can exceed recursion depth {MAX_RECURSION_DEPTH}"
            )
        if replacements > MAX_REPLACEMENTS:
            problems.append(
                f"{root!r} can exceed replacement limit {MAX_REPLACEMENTS}"
            )
    if problems:
        raise ArtifactError("; ".join(sorted(set(problems))))


def _inspect_variant(
    key: str,
    ordinal: int,
    variant: dict[str, Any],
    speak_keys: set[str],
) -> dict[str, object]:
    text = variant["raw_pattern"]
    marker_sites, _ = textdb_marker_sites(text)
    tokens = [{
        **site,
        "classification": ("recursive"
                           if site["canonical_key"] in speak_keys
                           else "runtime"),
    } for site in marker_sites]
    lua = [{
        "start": match.start(),
        "end": match.end(),
        "text_fingerprint": _sha256(match.group(0).encode("utf-8")),
    } for match in _LUA_RE.finditer(text)]
    controls = []
    offset = 0
    for line_number, line in enumerate(text.split("\n"), 1):
        match = _CONTROL_RE.match(line)
        if match:
            controls.append({"prefix": match.group(1), "line": line_number,
                             "start": offset})
        offset += len(line) + 1
    return {
        "variant_ordinal": ordinal,
        "snapshot_locator": {"canonical_key": key, "variant_ordinal": ordinal},
        "weight": variant["weight"],
        "text": text,
        "text_fingerprint": _sha256(text.encode("utf-8")),
        "tokens": tokens,
        "lua_sites": lua,
        "control_prefixes": controls,
        "random_substring_sites": _random_sites(text),
    }


def _cycle_components(keys: set[str], edges: list[dict[str, object]]) -> list[dict[str, object]]:
    adjacency = {key: set() for key in keys}
    for edge in edges:
        adjacency[str(edge["from_key"])].add(str(edge["to_key"]))
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def visit(key: str) -> None:
        nonlocal index
        indices[key] = lowlinks[key] = index
        index += 1
        stack.append(key)
        on_stack.add(key)
        for target in sorted(adjacency[key]):
            if target not in indices:
                visit(target)
                lowlinks[key] = min(lowlinks[key], lowlinks[target])
            elif target in on_stack:
                lowlinks[key] = min(lowlinks[key], indices[target])
        if lowlinks[key] == indices[key]:
            component: list[str] = []
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)
                if member == key:
                    break
            components.append(sorted(component))

    for key in sorted(keys):
        if key not in indices:
            visit(key)
    cyclic = []
    for component in components:
        members = set(component)
        internal = [edge for edge in edges
                    if edge["from_key"] in members and edge["to_key"] in members]
        if len(component) > 1 or any(edge["from_key"] == edge["to_key"]
                                     for edge in internal):
            cyclic.append({"keys": component, "edge_sites": len(internal)})
    return sorted(cyclic, key=lambda item: item["keys"])


def build_inventory(artifact: dict[str, Any]) -> dict[str, object]:
    key_sets = validate_artifact(artifact)
    if key_sets.corrupt:
        keys = ", ".join(sorted(key_sets.corrupt))
        raise ArtifactError(
            f"production SpeakDB contains corrupt effective entries: {keys}"
        )
    directory = artifact["source_directory"]
    sources = artifact["sources"]
    file_names = [Path(source["source_name"]).name for source in sources]
    source_blobs: list[tuple[str, bytes]] = [
        ("speakdb-directory", directory.encode("utf-8")),
        ("speakdb-files", _canonical_json(file_names)),
    ]
    source_blobs.extend(
        (f"dat/{source['source_name']}", source["normalized_utf8"].encode("utf-8"))
        for source in sources
    )

    artifact_entries = {entry["canonical_key"]: entry for entry in artifact["entries"]}
    monspell_source = f"{directory}monspell.txt"
    monspell_keys = {
        key for key, entry in artifact_entries.items()
        if any(item["source_name"] == monspell_source for item in entry["source_history"])
    }
    speak_keys = set(key_sets.selectable)
    _validate_static_closure(artifact_entries, monspell_keys, speak_keys)

    def inventory_entry(key: str) -> dict[str, object]:
        entry = artifact_entries[key]
        effective = entry["effective_provenance"]
        variants = [
            _inspect_variant(key, ordinal, variant, speak_keys)
            for ordinal, variant in enumerate(entry["variants"])
        ]
        return {
            "key": key,
            "effective_source": Path(effective["source_name"]).name,
            "defined_in_monspell": key in monspell_keys,
            "overridden": len(entry["source_history"]) > 1,
            "source_history": [
                {"file": Path(item["source_name"]).name,
                 "ordinal": item["definition_ordinal"]}
                for item in entry["source_history"]
            ],
            "entry_text_fingerprint": _sha256(entry["raw_body"].encode("utf-8")),
            "variants": variants,
        }

    entries = [inventory_entry(key) for key in sorted(monspell_keys)]
    closure_keys = set(monspell_keys)
    pending = list(sorted(monspell_keys))
    closure_nodes_by_key: dict[str, dict[str, object]] = {}
    closure_edges: list[dict[str, object]] = []
    while pending:
        key = pending.pop(0)
        node = inventory_entry(key)
        closure_nodes_by_key[key] = node
        for variant in node["variants"]:
            for token in variant["tokens"]:
                if token["classification"] != "recursive":
                    continue
                target = str(token["canonical_key"])
                closure_edges.append({
                    "from_key": key,
                    "from_variant_ordinal": variant["variant_ordinal"],
                    "start": token["start"],
                    "end": token["end"],
                    "token": token["token"],
                    "to_key": target,
                })
                if target not in closure_keys:
                    closure_keys.add(target)
                    pending.append(target)
    closure_key_list = sorted(closure_nodes_by_key)
    closure_edges.sort(key=lambda edge: (
        edge["from_key"], edge["from_variant_ordinal"], edge["start"], edge["to_key"],
    ))
    closure = {
        "keys": closure_key_list,
        "additional_nodes": [closure_nodes_by_key[key] for key in closure_key_list
                             if key not in monspell_keys],
        "edges": closure_edges,
        "cycles": _cycle_components(closure_keys, closure_edges),
    }
    semantic_basis = {
        "schema_version": SCHEMA_VERSION,
        "speakdb_directory": directory,
        "speakdb_files": file_names,
        "entries": entries,
        "closure": closure,
    }
    recursive_count = sum(token["classification"] == "recursive"
                          for entry in entries for variant in entry["variants"]
                          for token in variant["tokens"])
    runtime_count = sum(token["classification"] == "runtime"
                        for entry in entries for variant in entry["variants"]
                        for token in variant["tokens"])
    summary = {
        "monspell_keys": len(entries),
        "variants": sum(len(entry["variants"]) for entry in entries),
        "overridden_keys": sum(bool(entry["overridden"]) for entry in entries),
        "recursive_tokens": recursive_count,
        "runtime_tokens": runtime_count,
        "lua_sites": sum(len(v["lua_sites"]) for e in entries for v in e["variants"]),
        "random_substring_sites": sum(len(v["random_substring_sites"])
                                      for e in entries for v in e["variants"]),
        "closure_keys": len(closure_key_list),
        "closure_edge_sites": len(closure_edges),
        "closure_cycles": len(closure["cycles"]),
    }
    return {
        **semantic_basis,
        "source_fingerprint": _framed_source_fingerprint(source_blobs),
        "semantic_fingerprint": _sha256(_canonical_json(semantic_basis)),
        "summary": summary,
    }


def _render(inventory: dict[str, object]) -> str:
    return json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def validate_materialization_policy(
    inventory: dict[str, Any], policy: dict[str, Any]
) -> None:
    """Require an explicit disposition for every display-dynamic variant.

    Top-level variant selection already has a stable locator.  This ledger is
    for dynamic materialization *inside* a selected variant: bracket sites,
    Lua, or a recursive subtree that can select/display more than one result.
    It is a Phase-0 coverage gate, not a Phase-1 catalog.
    """
    if policy.get("schema_version") != 1:
        raise ArtifactError("materialization policy schema_version must be 1")
    if policy.get("inventory_semantic_fingerprint") != inventory.get(
        "semantic_fingerprint"
    ):
        raise ArtifactError(
            "materialization policy inventory fingerprint mismatch"
        )

    nodes = {entry["key"]: entry for entry in inventory["entries"]}
    nodes.update(
        {entry["key"]: entry for entry in inventory["closure"]["additional_nodes"]}
    )

    dynamic_cache: dict[str, bool] = {}

    def dynamic_node(key: str, visiting: frozenset[str] = frozenset()) -> bool:
        if key in dynamic_cache:
            return dynamic_cache[key]
        if key in visiting:
            # Cycles are rejected while building the inventory; retain a safe
            # answer if this validator is called on a hand-built test value.
            return True
        node = nodes[key]
        variants = node["variants"]
        dynamic = len(variants) > 1
        next_visiting = visiting | {key}
        for variant in variants:
            dynamic = dynamic or bool(variant["random_substring_sites"])
            dynamic = dynamic or bool(variant["lua_sites"])
            for token in variant["tokens"]:
                if token["classification"] == "recursive":
                    dynamic = dynamic or dynamic_node(
                        token["canonical_key"], next_visiting
                    )
        dynamic_cache[key] = dynamic
        return dynamic

    required: list[dict[str, Any]] = []
    for entry in inventory["entries"]:
        for variant in entry["variants"]:
            recursive_targets = [
                token["canonical_key"]
                for token in variant["tokens"]
                if token["classification"] == "recursive"
                and dynamic_node(token["canonical_key"])
            ]
            option_counts = [
                len(site["options"])
                for site in variant["random_substring_sites"]
            ]
            lua_count = len(variant["lua_sites"])
            if not option_counts and not recursive_targets and not lua_count:
                continue
            required.append({
                "key": entry["key"],
                "variant_ordinal": variant["variant_ordinal"],
                "random_site_option_counts": option_counts,
                "recursive_dynamic_targets": recursive_targets,
                "lua_site_count": lua_count,
            })

    declared = policy.get("variants")
    if not isinstance(declared, list):
        raise ArtifactError("materialization policy variants must be a list")
    allowed = {"CASE_MAP_PROTOTYPE", "CAPTURE_SLOT_PROTOTYPE", "LEGACY_ONLY"}
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for record in declared:
        if not isinstance(record, dict):
            raise ArtifactError("materialization policy variant must be an object")
        key = record.get("key")
        ordinal = record.get("variant_ordinal")
        if not isinstance(key, str) or not isinstance(ordinal, int):
            raise ArtifactError("materialization policy locator is invalid")
        identity = (key, ordinal)
        if identity in seen:
            raise ArtifactError(f"duplicate materialization policy locator: {identity}")
        seen.add(identity)
        disposition = record.get("policy")
        if disposition not in allowed:
            raise ArtifactError(
                f"invalid materialization policy for {key}[{ordinal}]: {disposition}"
            )
        evidence = record.get("evidence")
        if not isinstance(evidence, str) or not evidence:
            raise ArtifactError(
                f"materialization policy evidence missing for {key}[{ordinal}]"
            )
        normalized.append({
            "key": key,
            "variant_ordinal": ordinal,
            "random_site_option_counts": record.get(
                "random_site_option_counts"
            ),
            "recursive_dynamic_targets": record.get(
                "recursive_dynamic_targets"
            ),
            "lua_site_count": record.get("lua_site_count"),
            "policy": disposition,
        })

    required.sort(key=lambda item: (item["key"], item["variant_ordinal"]))
    normalized.sort(key=lambda item: (item["key"], item["variant_ordinal"]))
    if len(required) != len(normalized):
        raise ArtifactError(
            "materialization policy does not exactly cover current dynamic variants"
        )
    required_shape = [
        {**record, "policy": normalized[index]["policy"]}
        for index, record in enumerate(required)
    ]
    if normalized != required_shape:
        raise ArtifactError(
            "materialization policy does not exactly cover current dynamic variants"
        )
    for record in normalized:
        if record["lua_site_count"] and record["policy"] != "LEGACY_ONLY":
            raise ArtifactError(
                f"Lua variant must remain LEGACY_ONLY: "
                f"{record['key']}[{record['variant_ordinal']}]"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", required=True, type=Path,
                        help="production C++ canonical TextDB artifact")
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", type=Path, help="write inventory JSON here")
    destination.add_argument("--check", type=Path,
                             help="byte-compare with a checked-in inventory")
    parser.add_argument(
        "--materialization-policy", type=Path,
        help="validate Phase-0 dynamic materialization dispositions",
    )
    args = parser.parse_args(argv)
    try:
        inventory = build_inventory(load_artifact(args.dump))
        if args.materialization_policy:
            policy = json.loads(
                args.materialization_policy.read_text(encoding="utf-8")
            )
            if not isinstance(policy, dict):
                raise ArtifactError("materialization policy root must be an object")
            validate_materialization_policy(inventory, policy)
        rendered = _render(inventory)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        elif args.check:
            expected = args.check.read_text(encoding="utf-8")
            if expected != rendered:
                print(f"monspell Phase-0 inventory drift: {args.check}", file=sys.stderr)
                return 1
        else:
            sys.stdout.write(rendered)
    except (OSError, UnicodeError, json.JSONDecodeError, ArtifactError) as exc:
        print(f"audit_monspell_phase0.py: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
