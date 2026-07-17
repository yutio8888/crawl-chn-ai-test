#!/usr/bin/env python3
"""Validate the monspell overlay manifest and emit its C++14 sidecar."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
SLOT_RE = re.compile(r"\$\{([^}]*)\}")
TARGET_RELATIONS = ("AT", "NEXT_TO", "PAST")
NO_TARGET_RELATIONS = ("NONE",)
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
SLOT_TYPES = {
    "actor_ref", "actor_ref_lower", "actor_possessive_name",
    "actor_possessive_name_lower",
    "actor_possessive_pronoun",
    "actor_reflexive", "actor_arms_plural", "resolved_target",
    "resolved_foe", "resolved_beam", "recursive_capture",
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


def _normalise_manifest(manifest: dict[str, Any],
                        catalog_order: list[str] | None = None) -> dict[str, Any]:
    """Return the deterministic aggregate order consumed by validation/codegen."""
    result = dict(manifest)
    raw_entries = result.get("entries", [])
    _require(isinstance(raw_entries, list)
             and all(isinstance(item, dict) for item in raw_entries),
             "entries must be a list of objects")
    entries = list(raw_entries)
    for entry in entries:
        variants = entry.get("variants", [])
        _require(isinstance(variants, list)
                 and all(isinstance(item, dict) for item in variants),
                 "entry variants must be a list of objects")
        entry["variants"] = sorted(
            variants,
            key=lambda item: item.get("variant_ordinal", -1))
        for variant in entry["variants"]:
            cases = variant.get("materialization_cases", [])
            _require(isinstance(cases, list)
                     and all(isinstance(item, dict) for item in cases),
                     "materialization_cases must be a list of objects")
            variant["materialization_cases"] = sorted(
                cases,
                key=lambda item: (str(item.get("signature", "")),
                                  str(item.get("case_id", ""))))
    if catalog_order is None:
        catalog_order = [item.get("canonical_key", "") for item in entries]
    _require(all(isinstance(item, str) and item for item in catalog_order)
             and len(catalog_order) == len(set(catalog_order)),
             "catalog_order must contain unique canonical keys")
    rank = {key: ordinal for ordinal, key in enumerate(catalog_order)}
    result["entries"] = sorted(
        entries, key=lambda item: (
            rank.get(item.get("canonical_key"), len(rank)),
            str(item.get("canonical_key", ""))))
    tombstones = result.get("tombstones", [])
    _require(isinstance(tombstones, list)
             and all(isinstance(item, dict) for item in tombstones),
             "tombstones must be a list of objects")
    result["tombstones"] = sorted(
        tombstones,
        key=lambda item: str(item.get("stable_id", "")))
    return result


def load_manifest(path: Path) -> dict[str, Any]:
    """Load a legacy monolith or aggregate the fragments named by a header."""
    header = _read(path)
    fragments = header.get("fragments")
    fragment_glob = header.get("fragment_glob")
    if fragments is None and fragment_glob is None:
        return _normalise_manifest(header)
    _require((fragments is None) != (fragment_glob is None),
             "use exactly one of fragments or fragment_glob")
    if fragment_glob is not None:
        _require(isinstance(fragment_glob, str) and fragment_glob
                 and not Path(fragment_glob).is_absolute()
                 and ".." not in Path(fragment_glob).parts,
                 "fragment_glob must be a repository-relative pattern")
        fragments = sorted(
            item.relative_to(path.parent).as_posix()
            for item in path.parent.glob(fragment_glob) if item.is_file())
    _require(isinstance(fragments, list) and fragments
             and all(isinstance(item, str) and item for item in fragments)
             and len(set(fragments)) == len(fragments),
             "fragments must resolve to unique non-empty paths")
    _require("entries" not in header and "tombstones" not in header,
             "fragment header must not contain entries or tombstones")
    catalog_order = header.get("catalog_order", [])
    _require(isinstance(catalog_order, list),
             "catalog_order must be a list")
    aggregate = {key: value for key, value in header.items()
                 if key not in {"fragments", "fragment_glob",
                                "catalog_order"}}
    aggregate["entries"] = []
    aggregate["tombstones"] = []
    root = path.parent.resolve()
    for name in fragments:
        fragment_path = (path.parent / name).resolve()
        _require(fragment_path.is_relative_to(root),
                 f"fragment path escapes manifest directory: {name!r}")
        fragment = _read(fragment_path)
        _require(set(fragment) == {"entries", "tombstones"},
                 f"fragment {name!r} must contain entries and tombstones only")
        _require(isinstance(fragment["entries"], list)
                 and isinstance(fragment["tombstones"], list),
                 f"fragment {name!r} entries/tombstones must be lists")
        aggregate["entries"].extend(fragment["entries"])
        aggregate["tombstones"].extend(fragment["tombstones"])
    return _normalise_manifest(aggregate, catalog_order)


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


def _recursive_closure(nodes: dict[str, dict[str, Any]],
                       roots: list[str]) -> list[str]:
    pending = list(roots)
    seen: set[str] = set()
    while pending:
        key = pending.pop(0)
        _require(key in nodes, f"recursive closure key {key!r} is missing")
        if key in seen:
            continue
        seen.add(key)
        for variant in nodes[key]["variants"]:
            pending.extend(
                token["canonical_key"] for token in variant["tokens"]
                if token["classification"] == "recursive")
    return sorted(seen)


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


def _case_signatures(key: str, ordinal: int,
                     random_sites: list[dict[str, Any]]) -> set[str]:
    signatures = set()
    key_size = len(key.encode("utf-8"))
    for choices in itertools.product(
            *(range(len(site["options"])) for site in random_sites)):
        signature = (f"materialization-v1|variants=1|{key_size}:{key}:"
                     f"{ordinal}:0|lua=0|sites={len(random_sites)}")
        for site_ordinal, (site, choice) in enumerate(zip(random_sites,
                                                          choices)):
            signature += (f"|{key_size}:{key}:{ordinal}:{site_ordinal}:"
                          f"{len(site['options'])}:{choice}")
        signatures.add(signature)
    return signatures


def _validate_lines(lines: Any, languages: list[str], declared: set[str],
                    context: str, relations: tuple[str, ...]) -> tuple:
    _require(isinstance(lines, list) and lines,
             f"{context} needs line_metadata")
    used_slots: set[str] = set()
    shape = []
    for line_index, line in enumerate(lines):
        lcontext = f"{context}.line_metadata[{line_index}]"
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
        _require(not behavior["audible"],
                 f"{lcontext} audible behavior metadata is not enabled yet")
        shape.append((line["sensory"], line.get("channel"),
                      behavior["implies_gesture"], behavior["audible"]))
        templates = line.get("templates")
        _require(isinstance(templates, list),
                 f"{lcontext}.templates must be a list")
        matrix: set[tuple[str, str]] = set()
        for template_index, template in enumerate(templates):
            tcontext = f"{lcontext}.templates[{template_index}]"
            pair = (template.get("language"), template.get("relation"))
            _require(pair[0] in languages and pair[1] in relations
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
                            for relation in relations},
                 f"{lcontext} template matrix is incomplete")
    _require(used_slots == declared,
             f"{context} template slots mismatch slot schema")
    return tuple(shape)


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
            binding = variant.get("binding")
            _require(isinstance(binding, dict)
                     and set(binding) == {"resolves_target"}
                     and isinstance(binding["resolves_target"], bool),
                     f"{vcontext} has invalid binding requirements")
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
            if mode != "LEGACY_ONLY":
                _require(not applicability["requires_named_foe"]
                         and not applicability["requires_god"],
                         f"{vcontext} applicability metadata is not enabled yet")

            slot_schema = variant.get("slot_schema")
            _require(isinstance(slot_schema, list),
                     f"{vcontext}.slot_schema must be a list")
            declared: set[str] = set()
            slot_types: dict[str, str] = {}
            for slot in slot_schema:
                _require(isinstance(slot, dict)
                         and set(slot) == {"name", "type"}
                         and IDENTIFIER_RE.fullmatch(slot["name"])
                         and slot["type"] in SLOT_TYPES
                         and slot["name"] not in declared,
                         f"{vcontext} has invalid/duplicate slot schema")
                declared.add(slot["name"])
                slot_types[slot["name"]] = slot["type"]
            required = variant.get("required_arguments")
            _require(isinstance(required, list) and set(required) == declared
                     and len(required) == len(declared),
                     f"{vcontext} required arguments mismatch slot schema")

            direct_dependencies = sorted({
                token["canonical_key"] for token in actual["tokens"]
                if token["classification"] == "recursive"
            })
            dependency_fingerprints = variant.get(
                "recursive_dependency_fingerprints")
            _require(isinstance(dependency_fingerprints, dict),
                     f"{vcontext} recursive dependency closure mismatch")
            if policy == "CAPTURE_SLOT":
                dependencies = _recursive_closure(nodes, direct_dependencies)
                _require(sorted(dependency_fingerprints) == dependencies,
                         f"{vcontext} recursive capture closure mismatch")
                for dependency in dependencies:
                    _require(dependency_fingerprints[dependency]
                             == runtime_canonical_fingerprint(
                                 nodes[dependency]),
                             f"{vcontext} dependency fingerprint mismatch")
            else:
                dependencies = direct_dependencies
                _require(sorted(dependency_fingerprints) == dependencies,
                         f"{vcontext} recursive dependency closure mismatch")
                for dependency in dependencies:
                    _require(dependency in nodes
                             and dependency_fingerprints[dependency]
                             == nodes[dependency]["entry_text_fingerprint"],
                             f"{vcontext} dependency fingerprint mismatch")

            cases = variant.get("materialization_cases")
            _require(isinstance(cases, list),
                     f"{vcontext}.materialization_cases must be a list")
            suppresses = variant.get("suppresses", False)
            _require(isinstance(suppresses, bool),
                     f"{vcontext} has invalid suppresses flag")
            if policy == "NONE":
                _require(not actual["random_substring_sites"]
                         and not actual["lua_sites"] and not dependencies
                         and not cases,
                         f"{vcontext} NONE policy has dynamic materialization")
            if suppresses:
                _require(mode == "CANDIDATE",
                         f"{vcontext} suppress descriptor must be CANDIDATE")
                _require(actual["text"] == "__NONE" and policy == "NONE",
                         f"{vcontext} suppress descriptor must select exact __NONE")
                _require(not binding["resolves_target"]
                         and not any(applicability.values())
                         and not slot_schema and not required
                         and not variant.get("line_metadata") and not cases
                         and not dependency_fingerprints
                         and not variant.get("recursive_captures", []),
                         f"{vcontext} suppress descriptor contains renderable data")
                continue
            _require(mode != "CANDIDATE" or actual["text"] != "__NONE",
                     f"{vcontext} candidate __NONE requires suppress descriptor")
            if policy == "LEGACY_ONLY":
                _require(not variant.get("line_metadata") and not cases,
                         f"{vcontext} LEGACY_ONLY must not emit templates")
                continue
            has_actor_ref_token = "@The_monster@" in actual["text"]
            has_actor_ref_lower_token = "@the_monster@" in actual["text"]
            has_actor_possessive_token = (
                "@The_monster_possessive@" in actual["text"])
            has_actor_possessive_lower_token = (
                "@the_monster_possessive@" in actual["text"])
            has_actor_ref_slot = any(
                slot_type == "actor_ref"
                for slot_type in slot_types.values())
            has_actor_ref_lower_slot = any(
                slot_type == "actor_ref_lower"
                for slot_type in slot_types.values())
            has_actor_possessive_slot = any(
                slot_type == "actor_possessive_name"
                for slot_type in slot_types.values())
            has_actor_possessive_lower_slot = any(
                slot_type == "actor_possessive_name_lower"
                for slot_type in slot_types.values())
            _require(has_actor_ref_token == has_actor_ref_slot,
                     f"{vcontext} sentence actor token/type mismatch")
            _require(has_actor_ref_lower_token == has_actor_ref_lower_slot,
                     f"{vcontext} lower actor token/type mismatch")
            _require(has_actor_possessive_token == has_actor_possessive_slot,
                     f"{vcontext} sentence possessive actor token/type mismatch")
            _require(
                has_actor_possessive_lower_token
                == has_actor_possessive_lower_slot,
                f"{vcontext} lower possessive actor token/type mismatch")
            captures = variant.get("recursive_captures", [])
            _require(isinstance(captures, list),
                     f"{vcontext}.recursive_captures must be a list")
            has_target_slot = any(
                slot_type == "resolved_target"
                for slot_type in slot_types.values())
            _require(binding["resolves_target"] or not has_target_slot,
                     f"{vcontext} non-target binding declares resolved_target")
            target_tokens = {
                token["canonical_key"] for token in actual["tokens"]
                if token["classification"] == "runtime"
                and token["canonical_key"] in {"at", "target"}
            }
            _require(binding["resolves_target"] or not target_tokens,
                     f"{vcontext} non-target binding contains target tokens")
            has_foe_token = any(
                token["classification"] == "runtime"
                and token["canonical_key"] == "foe"
                for token in actual["tokens"])
            has_foe_slot = any(
                slot_type == "resolved_foe"
                for slot_type in slot_types.values())
            _require(has_foe_token == has_foe_slot,
                     f"{vcontext} foe token/type mismatch")
            _require(applicability["requires_foe"] == has_foe_slot,
                     f"{vcontext} foe applicability/slot mismatch")
            has_arms_token = any(
                token["classification"] == "runtime"
                and token["canonical_key"] == "arms"
                for token in actual["tokens"])
            has_arms_slot = any(
                slot_type == "actor_arms_plural"
                for slot_type in slot_types.values())
            _require(has_arms_token == has_arms_slot,
                     f"{vcontext} plural arms token/type mismatch")
            relations = (TARGET_RELATIONS if binding["resolves_target"]
                         else NO_TARGET_RELATIONS)
            if policy == "NONE":
                _require(not captures,
                         f"{vcontext} NONE declares recursive captures")
                _validate_lines(variant.get("line_metadata"), languages,
                                declared, vcontext, relations)
                continue
            if policy == "CAPTURE_SLOT":
                recursive_tokens = [
                    token for token in actual["tokens"]
                    if token["classification"] == "recursive"
                ]
                _require(not actual["random_substring_sites"]
                         and not actual["lua_sites"]
                         and len(recursive_tokens) == 3
                         and all(token["canonical_key"] == "orc name"
                                 for token in recursive_tokens),
                         f"{vcontext} unsupported recursive capture shape")
                _require(len(captures) == 3,
                         f"{vcontext} recursive capture count mismatch")
                for index, capture in enumerate(captures):
                    _require(isinstance(capture, dict)
                             and set(capture)
                                 == {"name", "marker", "ordinal",
                                     "vocabulary"}
                             and capture["name"] in declared
                             and slot_types[capture["name"]]
                                 == "recursive_capture"
                             and capture["marker"] == "orc name"
                             and capture["ordinal"] == index
                             and capture["vocabulary"] == "orc_name_leaf_v1",
                             f"{vcontext} invalid recursive capture declaration")
                leaf_keys = []
                for dependency_variant in nodes["orc name"]["variants"]:
                    parent_tokens = [
                        token for token in dependency_variant["tokens"]
                        if token["classification"] == "recursive"
                    ]
                    _require(
                        len(parent_tokens) == 1
                        and dependency_variant["text"]
                            == f"@{parent_tokens[0]['canonical_key']}@",
                        f"{vcontext} capture parent must be one exact marker")
                    leaf_keys.append(parent_tokens[0]["canonical_key"])
                leaf_keys = sorted(set(leaf_keys))
                vocabulary = []
                for leaf_key in leaf_keys:
                    for leaf_variant in nodes[leaf_key]["variants"]:
                        _require(not leaf_variant["tokens"]
                                 and not leaf_variant["random_substring_sites"]
                                 and not leaf_variant["lua_sites"],
                                 f"{vcontext} capture vocabulary is not leaf-only")
                        vocabulary.append({
                            "canonical_key": leaf_key,
                            "variant_ordinal":
                                leaf_variant["variant_ordinal"],
                            "variant_fingerprint":
                                _fnv1a64(
                                    leaf_variant["text"].encode("utf-8")),
                            "expanded_replacement_en": leaf_variant["text"],
                        })
                _require(len(vocabulary) == 103,
                         f"{vcontext} capture vocabulary size drifted")
                variant["_recursive_capture_vocabulary"] = vocabulary
                _validate_lines(variant.get("line_metadata"), languages,
                                declared, vcontext, relations)
                continue
            _require(policy == "CASE_MAP",
                     f"{vcontext} materialization policy is not enabled yet")
            _require(actual["random_substring_sites"]
                     and not actual["lua_sites"] and not dependencies,
                     f"{vcontext} CASE_MAP must consume finite bracket sites")
            _require(len(actual["random_substring_sites"]) == 1,
                     f"{vcontext} CASE_MAP slice supports exactly one site")
            _require(all(len(site["options"]) >= 2
                         for site in actual["random_substring_sites"]),
                     f"{vcontext} CASE_MAP site needs at least two options")
            _require(not variant.get("line_metadata"),
                     f"{vcontext} CASE_MAP lines belong to cases")
            expected = _case_signatures(key, variant_index,
                                        actual["random_substring_sites"])
            seen_signatures: set[str] = set()
            expected_shape = None
            for case_index, case in enumerate(cases):
                ccontext = f"{vcontext}.materialization_cases[{case_index}]"
                _require(isinstance(case, dict)
                         and set(case) == {"case_id", "signature",
                                          "line_metadata"},
                         f"{ccontext} has invalid fields")
                case_id = case["case_id"]
                _require(isinstance(case_id, str) and case_id
                         and case_id not in stable_ids,
                         f"{ccontext} has invalid/reused case_id")
                stable_ids.add(case_id)
                signature = case["signature"]
                _require(signature in expected
                         and signature not in seen_signatures,
                         f"{ccontext} has unknown/duplicate signature")
                seen_signatures.add(signature)
                shape = _validate_lines(case["line_metadata"], languages,
                                        declared, ccontext, relations)
                if expected_shape is None:
                    expected_shape = shape
                _require(shape == expected_shape,
                         f"{ccontext} changes binding-relevant line metadata")
            _require(seen_signatures == expected,
                     f"{vcontext} CASE_MAP cases are incomplete")

    # A structured recursive dependency must itself be present as closure data.
    by_key = {entry["canonical_key"]: entry for entry in manifest["entries"]}
    for entry in manifest["entries"]:
        if entry["mode"] != "CANDIDATE":
            continue
        for variant in entry["variants"]:
            if variant["materialization_policy"] == "CAPTURE_SLOT":
                continue
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
            captures = ", ".join(
                "{%s, %s, %d, %s}" % (
                    _cpp(x["name"]), _cpp(x["marker"]), x["ordinal"],
                    _cpp(x["vocabulary"]))
                for x in variant.get("recursive_captures", []))
            vocabulary = ", ".join(
                "{%s, %d, %s, %s}" % (
                    _cpp(x["canonical_key"]), x["variant_ordinal"],
                    _cpp(x["variant_fingerprint"]),
                    _cpp(x["expanded_replacement_en"]))
                for x in variant.get("_recursive_capture_vocabulary", []))
            lines = _emit_lines(variant.get("line_metadata", []), "                    ")
            emitted_cases = []
            for case in variant.get("materialization_cases", []):
                case_lines = _emit_lines(case["line_metadata"],
                                         "                            ")
                emitted_cases.extend([
                    "                            {",
                    f"                                {_cpp(case['case_id'])},",
                    f"                                {_cpp(case['signature'])},",
                ])
                emitted_cases.extend(case_lines[:-1])
                emitted_cases.append(case_lines[-1] + ",")
                emitted_cases.append("                            },")
            out.extend([
                "                    {",
                f"                        {_cpp(variant['stable_id'])}, false,",
                f"                        {variant['variant_ordinal']}, {variant['upstream_weight']},",
                f"                        {_cpp(variant['upstream_variant_fingerprint'])},",
                f"                        {_cpp(variant['english_snapshot'])},",
                f"                        cast_frame::{variant['frame']},",
                f"                        {str(variant['binding']['resolves_target']).lower()},",
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
            if emitted_cases:
                out.append("                        {")
                out.extend(emitted_cases)
                out.append("                        },")
            else:
                out.append("                        {},")
            out.extend([
                f"                        {{ {dep_names} }},",
                f"                        {{ {dep_fps} }},",
                f"                        {{ {captures} }},",
                f"                        {{ {vocabulary} }},",
            ])
            if variant.get("suppresses", False):
                out.append("                        true,")
            out.append("                    },")
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
        manifest = validate_manifest(load_manifest(args.manifest),
                                     _read(args.inventory))
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
