#!/usr/bin/env python3
"""Audit Phase-0 ${slot} schemas against a production SpeakDB dump."""

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

from audit_monspell_phase0 import ArtifactError, ArtifactKeySets, validate_artifact


REPORT_SCHEMA_VERSION = 1
INPUT_SCHEMA_VERSION = 1
ARTIFACT_SCHEMA_VERSION = 1
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_NAMESPACE_RE = re.compile(r"^[a-z_][a-z0-9_.-]*$")


class ProtocolError(ValueError):
    pass


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _fingerprint(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"cannot read {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProtocolError(f"{label} must be a JSON object")
    return value


def _effective_keys(artifact: dict[str, Any]) -> ArtifactKeySets:
    try:
        return validate_artifact(artifact, "SpeakDB dump")
    except ArtifactError as exc:
        raise ProtocolError(str(exc)) from exc


def _schema_parts(schema: dict[str, Any]) -> tuple[str, list[dict[str, str]], list[str], list[dict[str, Any]]]:
    if schema.get("schema_version") != INPUT_SCHEMA_VERSION:
        raise ProtocolError(
            f"unsupported slot schema_version {schema.get('schema_version')!r}"
        )
    namespace = schema.get("namespace_prefix")
    if not isinstance(namespace, str) or not namespace or not _NAMESPACE_RE.fullmatch(namespace):
        raise ProtocolError("namespace_prefix must be a lowercase ASCII namespace")
    slots = schema.get("slots")
    overlays = schema.get("overlay_keys")
    templates = schema.get("templates")
    if not isinstance(slots, list):
        raise ProtocolError("slots must be an array")
    if not isinstance(overlays, list):
        raise ProtocolError("overlay_keys must be an array")
    if not isinstance(templates, list):
        raise ProtocolError("templates must be an array")

    checked_slots: list[dict[str, str]] = []
    for index, slot in enumerate(slots):
        if not isinstance(slot, dict):
            raise ProtocolError(f"slots[{index}] must be an object")
        name, slot_type = slot.get("name"), slot.get("type")
        if not isinstance(name, str) or not isinstance(slot_type, str):
            raise ProtocolError(f"slots[{index}] requires string name and type")
        if not _IDENTIFIER_RE.fullmatch(slot_type):
            raise ProtocolError(f"slots[{index}].type is not a valid identifier")
        checked_slots.append({"name": name, "type": slot_type})
    if not all(isinstance(key, str) for key in overlays):
        raise ProtocolError("overlay_keys must contain strings")
    checked_templates: list[dict[str, Any]] = []
    for index, template in enumerate(templates):
        if not isinstance(template, dict):
            raise ProtocolError(f"templates[{index}] must be an object")
        stable_id = template.get("stable_id")
        text = template.get("text")
        declared = template.get("declared_recursive_keys")
        if not isinstance(stable_id, str) or not stable_id:
            raise ProtocolError(f"templates[{index}].stable_id must be a non-empty string")
        if not isinstance(text, str):
            raise ProtocolError(f"templates[{index}].text must be a string")
        if not isinstance(declared, list) or not all(isinstance(key, str) for key in declared):
            raise ProtocolError(
                f"templates[{index}].declared_recursive_keys must be a string array"
            )
        checked_templates.append({"stable_id": stable_id, "text": text,
                                  "declared_recursive_keys": declared})
    return namespace, checked_slots, list(overlays), checked_templates


def _violation(code: str, subject: str, detail: str, **evidence: Any) -> dict[str, Any]:
    result = {"code": code, "subject": subject, "detail": detail}
    result.update(evidence)
    return result


def _scan_template(text: str, subject: str) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    slots: list[str] = []
    recursive: list[str] = []
    violations: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        if text[index] == "$":
            if not text.startswith("${", index):
                violations.append(_violation(
                    "malformed_slot_syntax", subject,
                    "'$' must begin a ${slot} expression", offset=index,
                ))
                index += 1
                continue
            end = text.find("}", index + 2)
            if end < 0:
                violations.append(_violation(
                    "malformed_slot_syntax", subject,
                    "unterminated ${slot} expression", offset=index,
                ))
                break
            name = text[index + 2:end]
            if not _IDENTIFIER_RE.fullmatch(name):
                violations.append(_violation(
                    "malformed_slot_syntax", subject,
                    "slot expression contains an invalid name", offset=index,
                    expression=text[index:end + 1],
                ))
            else:
                slots.append(name)
            index = end + 1
            continue
        if text[index] == "@":
            end = text.find("@", index + 1)
            if end < 0 or "\n" in text[index + 1:end]:
                violations.append(_violation(
                    "malformed_recursive_syntax", subject,
                    "unterminated @key@ expression", offset=index,
                ))
                index += 1
                continue
            key = text[index + 1:end]
            if not key:
                violations.append(_violation(
                    "malformed_recursive_syntax", subject,
                    "recursive key may not be empty", offset=index,
                ))
            else:
                recursive.append(key.lower())
            index = end + 1
            continue
        index += 1
    return slots, recursive, violations


def audit(artifact: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    key_sets = _effective_keys(artifact)
    speak_keys = set(key_sets.reserved)
    namespace, slots, overlays, templates = _schema_parts(schema)
    violations: list[dict[str, Any]] = []

    slot_names: set[str] = set()
    for index, slot in enumerate(slots):
        name = slot["name"]
        subject = f"slot:{name or index}"
        if not _IDENTIFIER_RE.fullmatch(name):
            violations.append(_violation("invalid_slot_name", subject,
                                         "slot name must match [a-z][a-z0-9_]*"))
        if name in slot_names:
            violations.append(_violation("duplicate_slot_name", subject,
                                         "slot name is duplicated"))
        slot_names.add(name)
        if name in speak_keys:
            violations.append(_violation("slot_speakdb_collision", subject,
                                         "slot name collides with a SpeakDB key"))

    if any(key.startswith(namespace) for key in speak_keys):
        collisions = sorted(key for key in speak_keys if key.startswith(namespace))
        violations.append(_violation(
            "namespace_speakdb_collision", f"namespace:{namespace}",
            "reserved namespace already covers SpeakDB keys", keys=collisions,
        ))

    overlay_seen: set[str] = set()
    for key in overlays:
        subject = f"overlay:{key}"
        canonical_key = key.lower()
        if key != canonical_key:
            violations.append(_violation("noncanonical_overlay_key", subject,
                                         "overlay key must already be lowercase canonical form"))
        if canonical_key in overlay_seen:
            violations.append(_violation("duplicate_overlay_key", subject,
                                         "overlay key is duplicated"))
        overlay_seen.add(canonical_key)
        if not canonical_key.startswith(namespace) or canonical_key == namespace:
            violations.append(_violation("overlay_outside_namespace", subject,
                                         "overlay key is outside the reserved namespace"))
        if canonical_key in speak_keys:
            violations.append(_violation("overlay_speakdb_collision", subject,
                                         "overlay key collides with a SpeakDB key"))
        if canonical_key in slot_names:
            violations.append(_violation("slot_overlay_collision", subject,
                                         "overlay key collides with a slot name"))

    stable_ids: set[str] = set()
    for template in templates:
        stable_id = template["stable_id"]
        subject = f"template:{stable_id}"
        if stable_id in stable_ids:
            violations.append(_violation("duplicate_stable_id", subject,
                                         "template stable_id is duplicated"))
        stable_ids.add(stable_id)
        declared = template["declared_recursive_keys"]
        declared_set = set(declared)
        if len(declared_set) != len(declared):
            violations.append(_violation("duplicate_recursive_declaration", subject,
                                         "declared_recursive_keys contains duplicates"))
        used_slots, recursive, syntax = _scan_template(template["text"], subject)
        violations.extend(syntax)
        for name in sorted(set(used_slots) - slot_names):
            violations.append(_violation("undeclared_slot", subject,
                                         "template uses an undeclared slot", slot=name))
        for key in sorted(set(recursive) & slot_names):
            violations.append(_violation("slot_uses_textdb_syntax", subject,
                                         "declared slot must use ${slot}, not @slot@",
                                         slot=key))
        for key in sorted(set(recursive) - declared_set):
            violations.append(_violation("undeclared_recursive_key", subject,
                                         "@key@ reference is not declared", key=key))
        for key in sorted(declared_set - set(recursive)):
            violations.append(_violation("unused_recursive_declaration", subject,
                                         "declared recursive key has no @key@ reference",
                                         key=key))
        for key in sorted(declared_set):
            if key in key_sets.selectable:
                continue
            if key in key_sets.empty:
                violations.append(_violation(
                    "empty_recursive_key", subject,
                    "declared recursive key has an empty effective SpeakDB body",
                    key=key,
                ))
            elif key in key_sets.corrupt:
                violations.append(_violation(
                    "corrupt_recursive_key", subject,
                    "declared recursive key has a corrupt effective SpeakDB body",
                    key=key,
                ))
            else:
                violations.append(_violation(
                    "missing_recursive_key", subject,
                    "declared recursive key is absent from SpeakDB", key=key,
                ))

    violations.sort(key=lambda item: (
        item["subject"], item["code"], json.dumps(item, ensure_ascii=False, sort_keys=True)
    ))
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "tool": "audit_textdb_slots_phase0",
        "inputs": {
            "dump_fingerprint": _fingerprint(artifact),
            "slot_schema_fingerprint": _fingerprint(schema),
        },
        "summary": {
            "effective_speakdb_keys": len(speak_keys),
            "slots": len(slots),
            "overlay_keys": len(overlays),
            "templates": len(templates),
            "violations": len(violations),
            "valid": not violations,
        },
        "violations": violations,
    }
    return report


def _render(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", required=True, type=Path)
    parser.add_argument("--schema", required=True, type=Path)
    destination = parser.add_mutually_exclusive_group()
    destination.add_argument("--output", type=Path)
    destination.add_argument("--check", type=Path)
    args = parser.parse_args(argv)
    try:
        report = audit(_read_json(args.dump, "dump"),
                       _read_json(args.schema, "slot schema"))
        rendered = _render(report)
        if args.check:
            if args.check.read_bytes() != rendered:
                print(f"slot audit report drift: {args.check}", file=sys.stderr)
                return 1
        elif args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_bytes(rendered)
        else:
            sys.stdout.buffer.write(rendered)
        return 0 if report["summary"]["valid"] else 1
    except (OSError, UnicodeError, ProtocolError, ArtifactError) as exc:
        print(f"audit_textdb_slots_phase0.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
