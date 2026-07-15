#!/usr/bin/env python3
"""Compare two Phase 0 monspell canonical inventory dumps.

This tool deliberately consumes inventory JSON only.  It neither parses TextDB
nor assigns/inherits stable message IDs.  Every observed drift is evidence that
requires review; the report does not guess whether a body change is textual or
semantic.
"""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any, Iterable


TOOL_SCHEMA_VERSION = 1
SUPPORTED_INVENTORY_SCHEMA = 1


class ProtocolError(ValueError):
    pass


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProtocolError(message)


def _validate_variant(value: object, key: str, ordinal: int, context: str) -> None:
    _require(isinstance(value, dict), f"{context} must be an object")
    _require(value.get("variant_ordinal") == ordinal,
             f"{context}.variant_ordinal must be contiguous")
    locator = value.get("snapshot_locator")
    _require(isinstance(locator, dict)
             and locator.get("canonical_key") == key
             and locator.get("variant_ordinal") == ordinal,
             f"{context}.snapshot_locator is invalid")
    _require(_is_int(value.get("weight")), f"{context}.weight must be an integer")
    _require(isinstance(value.get("text"), str), f"{context}.text must be a string")
    _require(isinstance(value.get("text_fingerprint"), str),
             f"{context}.text_fingerprint must be a string")

    tokens = value.get("tokens")
    _require(isinstance(tokens, list), f"{context}.tokens must be an array")
    for index, token in enumerate(tokens):
        site = f"{context}.tokens[{index}]"
        _require(isinstance(token, dict), f"{site} must be an object")
        for field in ("token", "canonical_key"):
            _require(isinstance(token.get(field), str),
                     f"{site}.{field} must be a string")
        _require(token.get("classification") in ("runtime", "recursive"),
                 f"{site}.classification is invalid")
        for field in ("start", "end"):
            _require(_is_int(token.get(field)) and token[field] >= 0,
                     f"{site}.{field} must be a non-negative integer")

    random_sites = value.get("random_substring_sites")
    _require(isinstance(random_sites, list),
             f"{context}.random_substring_sites must be an array")
    for index, site in enumerate(random_sites):
        label = f"{context}.random_substring_sites[{index}]"
        _require(isinstance(site, dict), f"{label} must be an object")
        for field in ("start", "end"):
            _require(_is_int(site.get(field)) and site[field] >= 0,
                     f"{label}.{field} must be a non-negative integer")
        raw = site.get("raw")
        options = site.get("options")
        _require(isinstance(raw, str), f"{label}.raw must be a string")
        _require(isinstance(options, list)
                 and all(isinstance(option, str) for option in options),
                 f"{label}.options must be an array of strings")
        _require(options == raw.split("|"),
                 f"{label}.options must match the raw site")

    controls = value.get("control_prefixes")
    _require(isinstance(controls, list), f"{context}.control_prefixes must be an array")
    for index, control in enumerate(controls):
        label = f"{context}.control_prefixes[{index}]"
        _require(isinstance(control, dict), f"{label} must be an object")
        _require(isinstance(control.get("prefix"), str),
                 f"{label}.prefix must be a string")
        for field in ("line", "start"):
            _require(_is_int(control.get(field)) and control[field] >= 0,
                     f"{label}.{field} must be a non-negative integer")

    lua_sites = value.get("lua_sites")
    _require(isinstance(lua_sites, list), f"{context}.lua_sites must be an array")
    for index, site in enumerate(lua_sites):
        label = f"{context}.lua_sites[{index}]"
        _require(isinstance(site, dict), f"{label} must be an object")
        for field in ("start", "end"):
            _require(_is_int(site.get(field)) and site[field] >= 0,
                     f"{label}.{field} must be a non-negative integer")
        _require(isinstance(site.get("text_fingerprint"), str),
                 f"{label}.text_fingerprint must be a string")


def _validate_entry(value: object, context: str) -> str:
    _require(isinstance(value, dict), f"{context} must be an object")
    key = value.get("key")
    _require(isinstance(key, str) and key, f"{context}.key must be a non-empty string")
    _require(isinstance(value.get("defined_in_monspell"), bool),
             f"{context}.defined_in_monspell must be a boolean")
    _require(isinstance(value.get("effective_source"), str),
             f"{context}.effective_source must be a string")
    _require(isinstance(value.get("overridden"), bool),
             f"{context}.overridden must be a boolean")
    _require(isinstance(value.get("entry_text_fingerprint"), str),
             f"{context}.entry_text_fingerprint must be a string")
    history = value.get("source_history")
    _require(isinstance(history, list) and history,
             f"{context}.source_history must be a non-empty array")
    for index, source in enumerate(history):
        label = f"{context}.source_history[{index}]"
        _require(isinstance(source, dict), f"{label} must be an object")
        _require(isinstance(source.get("file"), str), f"{label}.file must be a string")
        _require(_is_int(source.get("ordinal")) and source["ordinal"] >= 0,
                 f"{label}.ordinal must be a non-negative integer")
    variants = value.get("variants")
    _require(isinstance(variants, list), f"{context}.variants must be an array")
    for ordinal, variant in enumerate(variants):
        _validate_variant(variant, key, ordinal, f"{context}.variants[{ordinal}]")
    return key


def validate_inventory(value: object, label: str = "inventory") -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolError(f"{label} must be a JSON object")
    if value.get("schema_version") != SUPPORTED_INVENTORY_SCHEMA:
        raise ProtocolError(
            f"{label} has unsupported schema_version "
            f"{value.get('schema_version')!r}; expected {SUPPORTED_INVENTORY_SCHEMA}"
        )
    for field in ("semantic_fingerprint", "source_fingerprint"):
        _require(isinstance(value.get(field), str), f"{label} is missing string {field}")
    _require(isinstance(value.get("speakdb_directory"), str),
             f"{label}.speakdb_directory must be a string")
    _require(isinstance(value.get("speakdb_files"), list)
             and all(isinstance(item, str) for item in value["speakdb_files"]),
             f"{label}.speakdb_files must be an array of strings")
    entries = value.get("entries")
    _require(isinstance(entries, list), f"{label} is missing entries array")
    entry_keys = [_validate_entry(entry, f"{label}.entries[{index}]")
                  for index, entry in enumerate(entries)]
    _require(entry_keys == sorted(set(entry_keys)),
             f"{label}.entries must be sorted and unique")
    closure = value.get("closure")
    _require(isinstance(closure, dict), f"{label} is missing closure object")
    keys = closure.get("keys")
    _require(isinstance(keys, list) and all(isinstance(key, str) for key in keys),
             f"{label}.closure.keys must be an array of strings")
    _require(keys == sorted(set(keys)), f"{label}.closure.keys must be sorted and unique")
    extra = closure.get("additional_nodes")
    _require(isinstance(extra, list),
             f"{label}.closure.additional_nodes must be an array")
    extra_keys = [_validate_entry(entry, f"{label}.closure.additional_nodes[{index}]")
                  for index, entry in enumerate(extra)]
    _require(extra_keys == sorted(set(extra_keys)),
             f"{label}.closure.additional_nodes must be sorted and unique")
    _require(not (set(entry_keys) & set(extra_keys)),
             f"{label} duplicates keys between entries and additional_nodes")
    edges = closure.get("edges")
    _require(isinstance(edges, list), f"{label}.closure.edges must be an array")
    for index, edge in enumerate(edges):
        site = f"{label}.closure.edges[{index}]"
        _require(isinstance(edge, dict), f"{site} must be an object")
        for field in ("from_key", "to_key", "token"):
            _require(isinstance(edge.get(field), str), f"{site}.{field} must be a string")
        for field in ("from_variant_ordinal", "start", "end"):
            _require(_is_int(edge.get(field)) and edge[field] >= 0,
                     f"{site}.{field} must be a non-negative integer")
    cycles = closure.get("cycles")
    _require(isinstance(cycles, list), f"{label}.closure.cycles must be an array")
    for index, cycle in enumerate(cycles):
        site = f"{label}.closure.cycles[{index}]"
        _require(isinstance(cycle, dict), f"{site} must be an object")
        _require(isinstance(cycle.get("keys"), list)
                 and all(isinstance(key, str) for key in cycle["keys"]),
                 f"{site}.keys must be an array of strings")
        _require(_is_int(cycle.get("edge_sites")) and cycle["edge_sites"] >= 0,
                 f"{site}.edge_sites must be a non-negative integer")
    return value


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"cannot read inventory {path}: {exc}") from exc
    return validate_inventory(value, f"inventory {path}")


def _entry_map(dump: dict[str, Any], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    all_entries = list(dump["entries"])
    extra = dump["closure"].get("additional_nodes", [])
    if not isinstance(extra, list):
        raise ProtocolError(f"{label} closure.additional_nodes must be an array")
    all_entries.extend(extra)
    for entry in all_entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("key"), str):
            raise ProtocolError(f"{label} contains an entry without a string key")
        key = entry["key"]
        if key in result:
            raise ProtocolError(f"{label} contains duplicate canonical key {key!r}")
        if not isinstance(entry.get("variants"), list):
            raise ProtocolError(f"{label} key {key!r} is missing variants array")
        result[key] = entry
    return result


def _evidence(kind: str, old: Any, new: Any, **context: Any) -> dict[str, Any]:
    value = {"kind": kind, "old": old, "new": new}
    value.update(context)
    return value


def _token_sets(variant: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    placeholders: set[str] = set()
    runtime: set[str] = set()
    recursive: set[str] = set()
    for token in variant["tokens"]:
        canonical = token["canonical_key"]
        placeholders.add(canonical)
        if token.get("classification") == "runtime":
            runtime.add(canonical)
        elif token.get("classification") == "recursive":
            recursive.add(canonical)
    return sorted(placeholders), sorted(runtime), sorted(recursive)


def _random_signature(variant: dict[str, Any]) -> list[dict[str, Any]]:
    signature: list[dict[str, Any]] = []
    for site in variant["random_substring_sites"]:
        options = site["options"]
        signature.append({
            "start": site.get("start"),
            "end": site.get("end"),
            "raw": site.get("raw"),
            "options": list(options),
        })
    return signature


def _lua_signature(variant: dict[str, Any]) -> list[Any]:
    result = []
    for site in variant.get("lua_sites", []):
        if not isinstance(site, dict):
            result.append(site)
            continue
        # Offsets are part of the lexical boundary contract. Preserve all fields
        # so future inventory versions cannot silently weaken this comparison.
        result.append(site)
    return result


def _variant_evidence(old: dict[str, Any], new: dict[str, Any], ordinal: int) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    fields = (
        ("weight", "variant_weight"),
        ("text_fingerprint", "variant_text_fingerprint"),
    )
    for field, kind in fields:
        if old.get(field) != new.get(field):
            evidence.append(_evidence(kind, old.get(field), new.get(field), variant_ordinal=ordinal))

    old_placeholders, old_runtime, old_recursive = _token_sets(old)
    new_placeholders, new_runtime, new_recursive = _token_sets(new)
    if old_placeholders != new_placeholders:
        evidence.append(_evidence("placeholder_token_set", old_placeholders, new_placeholders,
                                  variant_ordinal=ordinal))
    if old_runtime != new_runtime:
        evidence.append(_evidence("runtime_token_set", old_runtime, new_runtime,
                                  variant_ordinal=ordinal))
    if old_recursive != new_recursive:
        evidence.append(_evidence("recursive_target_set", old_recursive, new_recursive,
                                  variant_ordinal=ordinal))

    old_random = _random_signature(old)
    new_random = _random_signature(new)
    if old_random != new_random:
        evidence.append(_evidence("random_substring_sites", old_random, new_random,
                                  variant_ordinal=ordinal))
    if len(old_random) != len(new_random):
        evidence.append(_evidence("random_substring_site_count", len(old_random),
                                  len(new_random), variant_ordinal=ordinal))
    for site in range(min(len(old_random), len(new_random))):
        old_options = old_random[site]["options"]
        new_options = new_random[site]["options"]
        if len(old_options) != len(new_options):
            evidence.append(_evidence("random_substring_option_count",
                                      len(old_options), len(new_options),
                                      variant_ordinal=ordinal, site_ordinal=site))
        if old_options != new_options:
            evidence.append(_evidence("random_substring_options", old_options,
                                      new_options, variant_ordinal=ordinal,
                                      site_ordinal=site))

    if old.get("control_prefixes", []) != new.get("control_prefixes", []):
        evidence.append(_evidence("control_prefixes", old.get("control_prefixes", []),
                                  new.get("control_prefixes", []), variant_ordinal=ordinal))
    old_lua = _lua_signature(old)
    new_lua = _lua_signature(new)
    if old_lua != new_lua:
        evidence.append(_evidence("lua_boundaries", old_lua, new_lua,
                                  variant_ordinal=ordinal))
    return evidence


def _entry_evidence(old: dict[str, Any], new: dict[str, Any]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    provenance_fields = ("defined_in_monspell", "effective_source", "source_history", "overridden")
    old_provenance = {name: old.get(name) for name in provenance_fields}
    new_provenance = {name: new.get(name) for name in provenance_fields}
    if old_provenance != new_provenance:
        evidence.append(_evidence("effective_source_provenance", old_provenance, new_provenance))

    old_variants = old["variants"]
    new_variants = new["variants"]
    if len(old_variants) != len(new_variants):
        evidence.append(_evidence("variant_count", len(old_variants), len(new_variants)))

    old_order = [v.get("text_fingerprint") for v in old_variants]
    new_order = [v.get("text_fingerprint") for v in new_variants]
    if (len(old_order) == len(new_order) and old_order != new_order
            and collections.Counter(old_order) == collections.Counter(new_order)):
        evidence.append(_evidence("variant_order", old_order, new_order))

    for ordinal, (old_variant, new_variant) in enumerate(zip(old_variants, new_variants)):
        if not isinstance(old_variant, dict) or not isinstance(new_variant, dict):
            raise ProtocolError("variants must contain objects")
        evidence.extend(_variant_evidence(old_variant, new_variant, ordinal))
    for ordinal in range(len(new_variants), len(old_variants)):
        evidence.append(_evidence("variant_removed", _variant_signature(old_variants[ordinal]),
                                  None, variant_ordinal=ordinal))
    for ordinal in range(len(old_variants), len(new_variants)):
        evidence.append(_evidence("variant_added", None, _variant_signature(new_variants[ordinal]),
                                  variant_ordinal=ordinal))

    if old.get("entry_text_fingerprint") != new.get("entry_text_fingerprint"):
        evidence.append(_evidence("entry_text_fingerprint",
                                  old.get("entry_text_fingerprint"),
                                  new.get("entry_text_fingerprint")))
    return evidence


def _variant_signature(variant: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(variant, dict):
        raise ProtocolError("variants must contain objects")
    placeholders, runtime, recursive = _token_sets(variant)
    return {
        "weight": variant.get("weight"),
        "text_fingerprint": variant.get("text_fingerprint"),
        "placeholder_tokens": placeholders,
        "runtime_tokens": runtime,
        "recursive_targets": recursive,
        "random_substring_sites": _random_signature(variant),
        "control_prefixes": variant.get("control_prefixes", []),
        "lua_boundaries": _lua_signature(variant),
    }


def _entry_signature(entry: dict[str, Any]) -> dict[str, Any]:
    provenance_fields = ("defined_in_monspell", "effective_source", "source_history", "overridden")
    return {
        "entry_text_fingerprint": entry.get("entry_text_fingerprint"),
        "provenance": {name: entry.get(name) for name in provenance_fields},
        "variants": [_variant_signature(variant) for variant in entry["variants"]],
    }


def _closure_by_key(closure: dict[str, Any]) -> dict[str, dict[str, Any]]:
    keys = closure.get("keys", [])
    if not isinstance(keys, list) or not all(isinstance(k, str) for k in keys):
        raise ProtocolError("closure.keys must be an array of strings")
    result = {key: {"member": True, "outgoing_edges": []} for key in keys}
    edges = closure.get("edges", [])
    if not isinstance(edges, list):
        raise ProtocolError("closure.edges must be an array")
    for edge in edges:
        if not isinstance(edge, dict) or not isinstance(edge.get("from_key"), str):
            raise ProtocolError("closure edge is missing from_key")
        result.setdefault(edge["from_key"], {"member": False, "outgoing_edges": []})
        result[edge["from_key"]]["outgoing_edges"].append(edge)
    for value in result.values():
        value["outgoing_edges"].sort(key=lambda edge: json.dumps(edge, sort_keys=True))
    return result


def compare(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    validate_inventory(old, "old inventory")
    validate_inventory(new, "new inventory")
    old_entries = _entry_map(old, "old inventory")
    new_entries = _entry_map(new, "new inventory")
    old_closure = _closure_by_key(old["closure"])
    new_closure = _closure_by_key(new["closure"])
    changes: list[dict[str, Any]] = []

    all_keys = sorted(set(old_entries) | set(new_entries) | set(old_closure) | set(new_closure))
    for key in all_keys:
        evidence: list[dict[str, Any]] = []
        status = "modified"
        if key not in old_entries and key in new_entries:
            status = "added"
            evidence.append(_evidence("key_added", None, _entry_signature(new_entries[key])))
        elif key in old_entries and key not in new_entries:
            status = "removed"
            evidence.append(_evidence("key_removed", _entry_signature(old_entries[key]), None))
        elif key in old_entries and key in new_entries:
            evidence.extend(_entry_evidence(old_entries[key], new_entries[key]))

        old_c = old_closure.get(key, {"member": False, "outgoing_edges": []})
        new_c = new_closure.get(key, {"member": False, "outgoing_edges": []})
        if old_c["member"] != new_c["member"]:
            evidence.append(_evidence("closure_membership", old_c["member"], new_c["member"]))
        if old_c["outgoing_edges"] != new_c["outgoing_edges"]:
            evidence.append(_evidence("closure_outgoing_edges", old_c["outgoing_edges"],
                                      new_c["outgoing_edges"]))
        if evidence:
            changes.append({"canonical_key": key, "status": status,
                            "review_required": True, "evidence": evidence})

    global_evidence: list[dict[str, Any]] = []
    for field, kind in (("speakdb_directory", "speakdb_directory"),
                        ("speakdb_files", "speakdb_load_order")):
        if old.get(field) != new.get(field):
            global_evidence.append(_evidence(kind, old.get(field), new.get(field)))
    for field in ("cycles",):
        if old["closure"].get(field, []) != new["closure"].get(field, []):
            global_evidence.append(_evidence("closure_cycles",
                                              old["closure"].get(field, []),
                                              new["closure"].get(field, [])))

    evidence_counts = collections.Counter(
        item["kind"] for change in changes for item in change["evidence"]
    )
    evidence_counts.update(item["kind"] for item in global_evidence)
    summary = {
        "changed": bool(changes or global_evidence),
        "changed_keys": len(changes),
        "keys_added": sum(change["status"] == "added" for change in changes),
        "keys_removed": sum(change["status"] == "removed" for change in changes),
        "keys_modified": sum(change["status"] == "modified" for change in changes),
        "review_required": bool(changes or global_evidence),
        "evidence_counts": dict(sorted(evidence_counts.items())),
    }
    return {
        "schema_version": TOOL_SCHEMA_VERSION,
        "tool_schema_version": TOOL_SCHEMA_VERSION,
        "tool": "compare_monspell_phase0",
        "review_policy": {
            "automatic_stable_id_inheritance": False,
            "body_change_classification": "unclassified",
            "all_changes_require_review": True,
        },
        "old_inventory": {
            "semantic_fingerprint": old["semantic_fingerprint"],
            "source_fingerprint": old["source_fingerprint"],
        },
        "new_inventory": {
            "semantic_fingerprint": new["semantic_fingerprint"],
            "source_fingerprint": new["source_fingerprint"],
        },
        "summary": summary,
        "global_evidence": global_evidence,
        "changes": changes,
    }


def _encoded(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_inventory", type=Path)
    parser.add_argument("new_inventory", type=Path)
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", type=Path, help="write deterministic report")
    destination.add_argument("--check", type=Path, help="byte-compare against checked-in report")
    args = parser.parse_args(argv)
    try:
        report = compare(_load(args.old_inventory), _load(args.new_inventory))
        encoded = _encoded(report)
        if args.check:
            try:
                expected = args.check.read_bytes()
            except OSError as exc:
                raise ProtocolError(f"cannot read check file {args.check}: {exc}") from exc
            if expected != encoded:
                print(f"drift: {args.check} does not match generated report", file=sys.stderr)
                return 1
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(encoded)
        else:
            sys.stdout.buffer.write(encoded)
    except ProtocolError as exc:
        print(f"protocol error: {exc}", file=sys.stderr)
        return 2
    except (KeyError, TypeError, AttributeError) as exc:
        print(f"protocol error: malformed inventory: {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"I/O error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
