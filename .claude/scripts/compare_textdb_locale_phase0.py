#!/usr/bin/env python3
"""Compare static TextDB selection topology for canonical and localized dumps.

This consumes production C++ artifacts only.  It quantifies static selection
graphs and does not prove seeded dynamic RNG/Lua trace equivalence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from audit_monspell_phase0 import (
    ArtifactError,
    ArtifactKeySets,
    textdb_marker_sites,
    validate_artifact,
)


REPORT_SCHEMA_VERSION = 1
ARTIFACT_SCHEMA_VERSION = 1
_LUA_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)


class ProtocolError(ValueError):
    pass


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _read(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProtocolError(f"{label} must be a JSON object")
    return value


def _entries(
    artifact: dict[str, Any], label: str,
) -> tuple[dict[str, dict[str, Any]], ArtifactKeySets]:
    try:
        key_sets = validate_artifact(artifact, label)
    except ArtifactError as exc:
        raise ProtocolError(str(exc)) from exc
    return ({entry["canonical_key"]: entry for entry in artifact["entries"]},
            key_sets)


def _recursive_sequence(text: str, recursive_keys: set[str]) -> list[str]:
    sites, _ = textdb_marker_sites(text)
    return [str(site["canonical_key"]) for site in sites
            if site["canonical_key"] in recursive_keys]


def _lua_sequence(text: str) -> list[dict[str, Any]]:
    return [
        {
            "site_ordinal": ordinal,
            "source_fingerprint": hashlib.sha256(
                match.group(0).encode("utf-8")
            ).hexdigest(),
        }
        for ordinal, match in enumerate(_LUA_RE.finditer(text))
    ]


def _substring_option_counts(text: str) -> list[int]:
    counts: list[int] = []
    start = 0
    while True:
        begin = text.find("[", start)
        if begin < 0:
            break
        end = text.find("]", begin)
        if end < 0:
            break
        counts.append(len(text[begin + 1:end].split("|")))
        start = end + 1
    return counts


def _topology(entry: dict[str, Any], recursive_keys: set[str]) -> dict[str, Any]:
    weights = [variant["weight"] for variant in entry["variants"]]
    total = 0
    bounds = []
    for weight in weights:
        total += weight
        bounds.append(total)
    variants = []
    for ordinal, variant in enumerate(entry["variants"]):
        text = variant["raw_pattern"]
        variants.append({
            "variant_ordinal": ordinal,
            "recursive_references": _recursive_sequence(text, recursive_keys),
            "lua_sites": _lua_sequence(text),
            "random_substring_option_counts": _substring_option_counts(text),
        })
    return {
        "variant_count": len(weights),
        "weights": weights,
        "selection_bounds": bounds,
        "random_bound": total,
        "variants": variants,
    }


def _graph(
    root: str,
    lookup: dict[str, dict[str, Any]],
    recursive_keys: set[str],
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    if root not in lookup:
        return [], {}
    pending = [root]
    visited: set[str] = set()
    nodes: dict[str, dict[str, Any]] = {}
    while pending:
        key = pending.pop(0)
        if key in visited or key not in lookup:
            continue
        visited.add(key)
        topology = _topology(lookup[key], recursive_keys)
        nodes[key] = topology
        targets = sorted({target for variant in topology["variants"]
                          for target in variant["recursive_references"]})
        pending.extend(target for target in targets if target not in visited)
    return sorted(visited), {key: nodes[key] for key in sorted(nodes)}


def _evidence(old: Any, new: Any, kind: str, key: str | None = None) -> dict[str, Any]:
    result = {"kind": kind, "canonical": old, "localized": new}
    if key is not None:
        result["key"] = key
    return result


def compare(canonical: dict[str, Any], localized: dict[str, Any]) -> dict[str, Any]:
    canonical_entries, canonical_keys = _entries(canonical, "canonical dump")
    localized_entries, localized_keys = _entries(localized, "localized dump")
    canonical_nonempty = set(canonical_keys.selectable)
    localized_nonempty = set(localized_keys.selectable)
    merged_keys = canonical_nonempty | localized_nonempty

    canonical_lookup = {key: canonical_entries[key] for key in canonical_nonempty}
    localized_lookup = {
        key: (localized_entries[key] if key in localized_nonempty else canonical_entries[key])
        for key in merged_keys
        if key in localized_nonempty or key in canonical_nonempty
    }
    all_declared_keys = set(canonical_entries) | set(localized_entries)
    resolution = {
        "localized_only": sorted(localized_nonempty - set(canonical_entries)),
        "overridden": sorted(localized_nonempty & canonical_nonempty),
        "fallback": sorted(canonical_nonempty - localized_nonempty
                           - set(localized_keys.corrupt)),
        "missing": sorted(key for key in all_declared_keys
                          if key not in canonical_nonempty
                          and key not in localized_nonempty
                          and key not in canonical_keys.corrupt
                          and key not in localized_keys.corrupt),
    }
    corrupt = {
        "canonical": sorted(canonical_keys.corrupt),
        "localized": sorted(localized_keys.corrupt),
    }
    has_corrupt = bool(corrupt["canonical"] or corrupt["localized"])
    if has_corrupt:
        resolution["corrupt"] = corrupt

    monspell_source = f"{canonical['source_directory']}monspell.txt"
    roots = sorted(
        key for key, entry in canonical_entries.items()
        if any(isinstance(item, dict) and item.get("source_name") == monspell_source
               for item in entry["source_history"])
    )
    comparisons = []
    changed_roots = []
    for root in roots:
        canonical_closure, canonical_nodes = _graph(root, canonical_lookup, merged_keys)
        localized_closure, localized_nodes = _graph(root, localized_lookup, merged_keys)
        evidence = []
        if canonical_closure != localized_closure:
            evidence.append(_evidence(canonical_closure, localized_closure,
                                      "recursive_closure"))
        for key in sorted(set(canonical_nodes) | set(localized_nodes)):
            old = canonical_nodes.get(key)
            new = localized_nodes.get(key)
            if old is None or new is None:
                evidence.append(_evidence(old, new, "graph_node_presence", key))
                continue
            for field, kind in (
                ("variant_count", "variant_count"),
                ("weights", "weights"),
                ("selection_bounds", "selection_bounds"),
                ("random_bound", "random_bound"),
            ):
                if old[field] != new[field]:
                    evidence.append(_evidence(old[field], new[field], kind, key))
            for ordinal, (old_variant, new_variant) in enumerate(
                zip(old["variants"], new["variants"])
            ):
                for field, kind in (
                    ("recursive_references", "recursive_reference_sequence"),
                    ("lua_sites", "lua_site_sequence"),
                    ("random_substring_option_counts",
                     "random_substring_option_count_sequence"),
                ):
                    if old_variant[field] != new_variant[field]:
                        item = _evidence(old_variant[field], new_variant[field], kind, key)
                        item["variant_ordinal"] = ordinal
                        evidence.append(item)
            for ordinal in range(len(new["variants"]), len(old["variants"])):
                evidence.append(_evidence(old["variants"][ordinal], None,
                                          "variant_removed", key)
                                | {"variant_ordinal": ordinal})
            for ordinal in range(len(old["variants"]), len(new["variants"])):
                evidence.append(_evidence(None, new["variants"][ordinal],
                                          "variant_added", key)
                                | {"variant_ordinal": ordinal})
        changed = bool(evidence)
        if changed:
            changed_roots.append(root)
        comparisons.append({
            "root": root,
            "canonical_closure": canonical_closure,
            "localized_closure": localized_closure,
            "trace_topology_changed": changed,
            "review_required": changed,
            "evidence": evidence,
        })

    summary = {
        "canonical_roots": len(roots),
        "localized_only": len(resolution["localized_only"]),
        "overridden": len(resolution["overridden"]),
        "fallback": len(resolution["fallback"]),
        "missing": len(resolution["missing"]),
        "trace_topology_changed_roots": changed_roots,
        "review_required": bool(changed_roots or has_corrupt),
    }
    if has_corrupt:
        summary["corrupt_entries"] = (
            len(corrupt["canonical"]) + len(corrupt["localized"])
        )

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "tool": "compare_textdb_locale_phase0",
        "scope": "static_selection_topology_only",
        "dynamic_trace_proven": False,
        "inputs": {
            "canonical_dump_fingerprint": _fingerprint(canonical),
            "localized_dump_fingerprint": _fingerprint(localized),
        },
        "resolution": resolution,
        "summary": summary,
        "roots": comparisons,
    }


def _render(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-dump", required=True, type=Path)
    parser.add_argument("--localized-dump", required=True, type=Path)
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", type=Path)
    destination.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    try:
        report = compare(_read(args.canonical_dump, "canonical dump"),
                         _read(args.localized_dump, "localized dump"))
        rendered = _render(report)
        if args.check:
            if args.check.read_bytes() != rendered:
                print(f"locale topology report drift: {args.check}", file=sys.stderr)
                return 1
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(rendered)
        else:
            sys.stdout.buffer.write(rendered)
        return 0
    except (OSError, UnicodeError, ProtocolError, ArtifactError) as exc:
        print(f"compare_textdb_locale_phase0.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
