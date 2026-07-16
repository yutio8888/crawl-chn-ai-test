#!/usr/bin/env python3
"""Validate the monspell overlay manifest and emit its C++14 sidecar."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SLOT_RE = re.compile(r"\$\{([^}]*)\}")
RELATIONS = ("AT", "NEXT_TO", "PAST")
MODES = {"CANDIDATE", "CLOSURE_ONLY", "LEGACY_ONLY"}
POLICIES = {"NONE", "CASE_MAP", "CAPTURE_SLOT", "LEGACY_ONLY"}
FRAMES = {"PROJECTILE", "GAZE", "GESTURE", "VOCAL", "INVOCATION",
          "DIRECT_EFFECT"}
SENSORY = {"PLAIN", "VISUAL", "SOUND"}
CHANNELS = {
    "plain", "friend_action", "prompt", "god", "duration", "danger",
    "warning", "recovery", "sound", "talk", "talk_visual",
    "intrinsic_gain", "mutation", "monster_spell", "monster_enchant",
    "friend_spell", "friend_enchant", "monster_damage",
    "monster_target", "banishment", "equipment", "floor", "multiturn",
    "examine", "examine_filter", "diagnostic", "error", "tutorial",
    "orb", "timed_portal", "hell_effect", "monster_warning",
    "dgl_message", "decor_flavour", "monster_timeout", "visual", "spell",
}


class ManifestError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ManifestError(message)


def _read(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read {path}: {exc}") from exc
    _require(isinstance(value, dict), f"{path} must contain an object")
    return value


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def selection_graph_fingerprint(entry: dict[str, Any]) -> str:
    variants = []
    for variant in entry["variants"]:
        variants.append({
            "ordinal": variant["variant_ordinal"],
            "weight": variant["weight"],
            "text_fingerprint": variant["text_fingerprint"],
            "tokens": [
                [token["canonical_key"], token["classification"]]
                for token in variant["tokens"]
            ],
            "random_substring_sites": [
                [site["raw"], len(site["options"])]
                for site in variant["random_substring_sites"]
            ],
            "lua_sites": variant["lua_sites"],
        })
    return hashlib.sha256(_canonical_bytes({
        "schema_version": 1,
        "key": entry["key"],
        "variants": variants,
    })).hexdigest()


def _fnv1a64(data: bytes) -> str:
    value = 14695981039346656037
    for byte in data:
        value ^= byte
        value = (value * 1099511628211) & 0xffffffffffffffff
    return f"fnv1a64:{value:016x}"


def runtime_canonical_fingerprint(entry: dict[str, Any]) -> str:
    payload = bytearray(b"canonical-v1\0")
    payload.extend(entry["key"].encode("utf-8"))
    payload.append(0)
    for variant in entry["variants"]:
        payload.extend(str(variant["variant_ordinal"]).encode("ascii"))
        payload.extend(b":")
        payload.extend(variant["text"].encode("utf-8"))
        payload.append(0)
    return _fnv1a64(bytes(payload))


def runtime_selection_fingerprint(entry: dict[str, Any]) -> str:
    payload = bytearray(b"selection-v1\0")
    payload.extend(entry["key"].encode("utf-8"))
    payload.append(0)
    for variant in entry["variants"]:
        payload.extend(str(variant["variant_ordinal"]).encode("ascii"))
        payload.extend(b":")
        payload.extend(str(variant["weight"]).encode("ascii"))
        payload.extend(b":")
        payload.extend(variant["text"].encode("utf-8"))
        payload.append(0)
    return _fnv1a64(bytes(payload))


def _inventory_nodes(inventory: dict[str, Any]) -> dict[str, dict[str, Any]]:
    nodes = list(inventory.get("entries", []))
    nodes.extend(inventory.get("closure", {}).get("additional_nodes", []))
    result: dict[str, dict[str, Any]] = {}
    for node in nodes:
        _require(node["key"] not in result,
                 f"inventory has duplicate key {node['key']!r}")
        result[node["key"]] = node
    return result


def _template_slots(pattern: str, context: str) -> set[str]:
    _require("@" not in pattern and "[" not in pattern and "]" not in pattern
             and "{{" not in pattern and "}}" not in pattern,
             f"{context} contains legacy TextDB syntax")
    slots = set(SLOT_RE.findall(pattern))
    _require(all(IDENTIFIER_RE.fullmatch(slot) for slot in slots),
             f"{context} contains an invalid slot")
    _require(pattern.count("${") == len(SLOT_RE.findall(pattern)),
             f"{context} contains an unclosed slot")
    return slots


def validate_manifest(manifest: dict[str, Any],
                      inventory: dict[str, Any]) -> dict[str, Any]:
    _require(manifest.get("schema_version") == SCHEMA_VERSION,
             "unknown manifest schema_version")
    _require(manifest.get("domain") == "monspell", "domain must be monspell")
    _require(manifest.get("inventory_semantic_fingerprint")
             == inventory.get("semantic_fingerprint"),
             "inventory semantic fingerprint mismatch")
    languages = manifest.get("supported_languages")
    _require(isinstance(languages, list) and languages
             and len(set(languages)) == len(languages)
             and all(isinstance(x, str) and x for x in languages)
             and {"en", "zh"}.issubset(languages),
             "supported_languages must be unique non-empty strings")

    nodes = _inventory_nodes(inventory)
    stable_ids: set[str] = set()
    for ordinal, tombstone in enumerate(manifest.get("tombstones", [])):
        context = f"tombstones[{ordinal}]"
        stable_id = tombstone.get("stable_id")
        _require(isinstance(stable_id, str) and stable_id
                 and stable_id not in stable_ids,
                 f"{context} has an invalid or duplicate stable_id")
        _require(isinstance(tombstone.get("reason"), str)
                 and tombstone["reason"], f"{context} needs a reason")
        stable_ids.add(stable_id)

    keys: set[str] = set()
    for entry_index, record in enumerate(manifest.get("entries", [])):
        context = f"entries[{entry_index}]"
        key = record.get("canonical_key")
        _require(isinstance(key, str) and key in nodes and key not in keys,
                 f"{context} has an invalid or duplicate canonical_key")
        keys.add(key)
        upstream = nodes[key]
        _require(record.get("canonical_fingerprint")
                 == runtime_canonical_fingerprint(upstream),
                 f"{context} canonical fingerprint mismatch")
        _require(record.get("selection_graph_fingerprint")
                 == runtime_selection_fingerprint(upstream),
                 f"{context} selection graph fingerprint mismatch")
        mode = record.get("mode")
        _require(mode in MODES, f"{context} has invalid mode")
        variants = record.get("variants")
        _require(isinstance(variants, list)
                 and len(variants) == len(upstream["variants"]),
                 f"{context} must cover every selectable variant")

        for variant_index, variant in enumerate(variants):
            vcontext = f"{context}.variants[{variant_index}]"
            actual = upstream["variants"][variant_index]
            _require(variant.get("variant_ordinal") == variant_index,
                     f"{vcontext} locator is not contiguous")
            _require(variant.get("upstream_weight") == actual["weight"],
                     f"{vcontext} weight mismatch")
            _require(variant.get("upstream_variant_fingerprint")
                     == actual["text_fingerprint"],
                     f"{vcontext} fingerprint mismatch")
            _require(variant.get("english_snapshot") == actual["text"],
                     f"{vcontext} English snapshot mismatch")
            stable_id = variant.get("stable_id")
            _require(isinstance(stable_id, str) and stable_id
                     and stable_id not in stable_ids
                     and variant.get("tombstone") is False,
                     f"{vcontext} has an invalid/reused active stable_id")
            stable_ids.add(stable_id)
            _require(variant.get("frame") in FRAMES,
                     f"{vcontext} has invalid frame")
            policy = variant.get("materialization_policy")
            _require(policy in POLICIES, f"{vcontext} has invalid policy")
            _require((mode == "LEGACY_ONLY") == (policy == "LEGACY_ONLY"),
                     f"{vcontext} mode/policy mismatch")

            applicability = variant.get("applicability")
            expected_applicability = {
                "requires_player", "requires_foe", "requires_named_foe",
                "requires_god", "requires_caster_visible",
            }
            _require(isinstance(applicability, dict)
                     and set(applicability) == expected_applicability
                     and all(isinstance(x, bool)
                             for x in applicability.values()),
                     f"{vcontext} has invalid applicability")

            slot_schema = variant.get("slot_schema")
            _require(isinstance(slot_schema, list),
                     f"{vcontext}.slot_schema must be a list")
            declared: set[str] = set()
            for slot in slot_schema:
                _require(isinstance(slot, dict)
                         and set(slot) == {"name", "type"}
                         and IDENTIFIER_RE.fullmatch(slot["name"])
                         and isinstance(slot["type"], str) and slot["type"]
                         and slot["name"] not in declared,
                         f"{vcontext} has invalid/duplicate slot schema")
                declared.add(slot["name"])
            required = variant.get("required_arguments")
            _require(isinstance(required, list) and set(required) == declared
                     and len(required) == len(declared),
                     f"{vcontext} required arguments mismatch slot schema")

            dependencies = sorted({
                token["canonical_key"] for token in actual["tokens"]
                if token["classification"] == "recursive"
            })
            dependency_fingerprints = variant.get(
                "recursive_dependency_fingerprints")
            _require(isinstance(dependency_fingerprints, dict)
                     and sorted(dependency_fingerprints) == dependencies,
                     f"{vcontext} recursive dependency closure mismatch")
            for dependency in dependencies:
                _require(dependency in nodes
                         and dependency_fingerprints[dependency]
                         == nodes[dependency]["entry_text_fingerprint"],
                         f"{vcontext} dependency fingerprint mismatch")

            cases = variant.get("materialization_cases")
            _require(isinstance(cases, list),
                     f"{vcontext}.materialization_cases must be a list")
            _require(policy in {"NONE", "LEGACY_ONLY"},
                     f"{vcontext} materialization policy is not enabled yet")
            if policy == "NONE":
                _require(not actual["random_substring_sites"]
                         and not actual["lua_sites"] and not dependencies
                         and not cases,
                         f"{vcontext} NONE policy has dynamic materialization")
            if policy == "LEGACY_ONLY":
                _require(not variant.get("line_metadata") and not cases,
                         f"{vcontext} LEGACY_ONLY must not emit templates")
                continue

            lines = variant.get("line_metadata")
            _require(isinstance(lines, list) and lines,
                     f"{vcontext} needs line_metadata")
            used_slots: set[str] = set()
            for line_index, line in enumerate(lines):
                lcontext = f"{vcontext}.line_metadata[{line_index}]"
                _require(line.get("sensory") in SENSORY,
                         f"{lcontext} has invalid sensory")
                _require(line.get("channel") is None
                         or (isinstance(line.get("channel"), str)
                             and line.get("channel") in CHANNELS),
                         f"{lcontext} has invalid channel")
                behavior = line.get("behavior")
                _require(isinstance(behavior, dict)
                         and set(behavior) == {"implies_gesture", "audible"}
                         and all(isinstance(x, bool) for x in behavior.values()),
                         f"{lcontext} has invalid behavior metadata")
                templates = line.get("templates")
                _require(isinstance(templates, list),
                         f"{lcontext}.templates must be a list")
                matrix: set[tuple[str, str]] = set()
                for template_index, template in enumerate(templates):
                    tcontext = f"{lcontext}.templates[{template_index}]"
                    pair = (template.get("language"), template.get("relation"))
                    _require(pair[0] in languages and pair[1] in RELATIONS
                             and pair not in matrix,
                             f"{tcontext} invalid/duplicate language relation")
                    matrix.add(pair)
                    pattern = template.get("pattern")
                    _require(isinstance(pattern, str) and pattern
                             and "\n" not in pattern,
                             f"{tcontext} needs a pattern")
                    used_slots.update(_template_slots(pattern, tcontext))
                _require(matrix == {(language, relation)
                                    for language in languages
                                    for relation in RELATIONS},
                         f"{lcontext} template matrix is incomplete")
            _require(used_slots == declared,
                     f"{vcontext} template slots mismatch slot schema")

    # A structured recursive dependency must itself be present as closure data.
    by_key = {entry["canonical_key"]: entry for entry in manifest["entries"]}
    for entry in manifest["entries"]:
        if entry["mode"] != "CANDIDATE":
            continue
        for variant in entry["variants"]:
            for dependency in variant["recursive_dependency_fingerprints"]:
                _require(dependency in by_key
                         and by_key[dependency]["mode"] != "LEGACY_ONLY",
                         f"{entry['canonical_key']!r} structured closure missing "
                         f"{dependency!r}")
    return manifest


def _cpp(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _emit_lines(lines: list[dict[str, Any]], indent: str) -> list[str]:
    output = [indent + "{"]
    for line in lines:
        templates = ", ".join(
            "{%s, %s, %s}" % (_cpp(t["language"]), _cpp(t["relation"]),
                                _cpp(t["pattern"]))
            for t in line["templates"]
        )
        output.append(
            indent + "  { sensory_mode::%s, %s, %s, %s, { %s } }," % (
                line["sensory"], _cpp(line["channel"] or ""),
                str(line["behavior"]["implies_gesture"]).lower(),
                str(line["behavior"]["audible"]).lower(), templates))
    output.append(indent + "}")
    return output


def render_sidecar(manifest: dict[str, Any]) -> str:
    out = [
        "// Generated by .claude/scripts/generate_message_overlay.py.",
        "// Do not edit by hand.",
        "const catalog_source &generated_monspell_catalog()",
        "{",
        "    static const catalog_source catalog =",
        "    {",
        f"        {manifest['schema_version']},",
        f"        {_cpp(manifest['domain'])},",
        f"        {_cpp(manifest['inventory_semantic_fingerprint'])},",
        "        { " + ", ".join(_cpp(x) for x in manifest["supported_languages"])
        + " },",
        "        {",
    ]
    for entry in manifest["entries"]:
        out.extend([
            "            {",
            f"                {_cpp(entry['canonical_key'])},",
            f"                {_cpp(entry['canonical_fingerprint'])},",
            f"                {_cpp(entry['selection_graph_fingerprint'])},",
            f"                entry_mode::{entry['mode']},",
            "                {",
        ])
        for variant in entry["variants"]:
            app = variant["applicability"]
            slots = ", ".join("{%s, %s}" % (_cpp(x["name"]), _cpp(x["type"]))
                              for x in variant["slot_schema"])
            required = ", ".join(_cpp(x) for x in variant["required_arguments"])
            deps = sorted(variant["recursive_dependency_fingerprints"])
            dep_names = ", ".join(_cpp(x) for x in deps)
            dep_fps = ", ".join(
                _cpp(variant["recursive_dependency_fingerprints"][x])
                for x in deps)
            lines = _emit_lines(variant.get("line_metadata", []), "                    ")
            out.extend([
                "                    {",
                f"                        {_cpp(variant['stable_id'])}, false,",
                f"                        {variant['variant_ordinal']}, {variant['upstream_weight']},",
                f"                        {_cpp(variant['upstream_variant_fingerprint'])},",
                f"                        {_cpp(variant['english_snapshot'])},",
                f"                        cast_frame::{variant['frame']},",
                "                        { %s, %s, %s, %s, %s }," % tuple(
                    str(app[k]).lower() for k in (
                        "requires_player", "requires_foe",
                        "requires_named_foe", "requires_god",
                        "requires_caster_visible")),
                f"                        materialization_policy::{variant['materialization_policy']},",
                f"                        {{ {slots} }},",
                f"                        {{ {required} }},",
            ])
            out.extend(lines[:-1])
            out.append(lines[-1] + ",")
            out.extend([
                "                        {},",
                f"                        {{ {dep_names} }},",
                f"                        {{ {dep_fps} }},",
                "                    },",
            ])
        out.extend(["                },", "            },"])
    out.extend(["        },", "        {"])
    for tombstone in manifest.get("tombstones", []):
        out.append("            {%s, %s}," % (
            _cpp(tombstone["stable_id"]), _cpp(tombstone["reason"])))
    out.extend(["        },", "    };", "    return catalog;", "}", ""])
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    try:
        manifest = validate_manifest(_read(args.manifest), _read(args.inventory))
        rendered = render_sidecar(manifest)
    except ManifestError as exc:
        print(f"message overlay error: {exc}", file=sys.stderr)
        return 2
    if args.check:
        try:
            existing = args.check.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            print(f"message overlay error: cannot read {args.check}: {exc}",
                  file=sys.stderr)
            return 2
        if existing != rendered:
            print("message overlay generated sidecar drift", file=sys.stderr)
            return 1
    if args.output:
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
    if not args.output and not args.check:
        sys.stdout.write(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
