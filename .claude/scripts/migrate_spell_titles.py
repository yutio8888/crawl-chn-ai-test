#!/usr/bin/env python3
"""Safely inspect the current production spell-title artifact.

This was once an in-place migration script.  It is now deliberately read-only:
running it without a subcommand prints help, and the only subcommand is
``inventory``.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SPL_DATA = ROOT / "crawl-ref/source/spl-data.h"
DEFAULT_SPELL_TYPE = ROOT / "crawl-ref/source/spell-type.h"
DEFAULT_TAG_VERSION = ROOT / "crawl-ref/source/tag-version.h"
DEFAULT_SOURCE_TXT = ROOT / "crawl-ref/source/dat/i18n/zh/source.txt"
DEFAULT_EN_DESCRIPTIONS = ROOT / "crawl-ref/source/dat/descript/spells.txt"
DEFAULT_ZH_DESCRIPTIONS = ROOT / "crawl-ref/source/dat/descript/zh/spells.txt"


class InventoryError(ValueError):
    """The production artifact could not be completely and safely parsed."""


@dataclass(frozen=True)
class Spell:
    enum: str
    title: str
    schools: str
    flags: str
    level: int
    lifecycle: str


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise InventoryError(f"cannot read required input {path}: {exc}") from exc


def _without_comments(text: str) -> str:
    """Remove C++ comments while preserving strings and line structure."""
    out: list[str] = []
    i = 0
    state = "code"
    while i < len(text):
        pair = text[i:i + 2]
        char = text[i]
        if state == "code" and pair == "//":
            out.extend("  ")
            i += 2
            state = "line"
        elif state == "code" and pair == "/*":
            out.extend("  ")
            i += 2
            state = "block"
        elif state == "line":
            if char == "\n":
                out.append(char)
                state = "code"
            else:
                out.append(" ")
            i += 1
        elif state == "block":
            if pair == "*/":
                out.extend("  ")
                i += 2
                state = "code"
            else:
                out.append("\n" if char == "\n" else " ")
                i += 1
        else:
            out.append(char)
            i += 1
            if state == "code" and char == '"':
                state = "string"
            elif state == "string" and char == "\\" and i < len(text):
                out.append(text[i])
                i += 1
            elif state == "string" and char == '"':
                state = "code"
    if state in {"block", "string"}:
        raise InventoryError(f"unterminated C++ {state}")
    return "".join(out)


def _split_fields(block: str) -> list[str]:
    fields: list[str] = []
    start = 0
    depth = 0
    in_string = False
    escaped = False
    for i, char in enumerate(block):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
            if depth < 0:
                raise InventoryError("unbalanced delimiter in spell entry")
        elif char == "," and depth == 0:
            fields.append(block[start:i].strip())
            start = i + 1
    tail = block[start:].strip()
    if tail:
        fields.append(tail)
    return fields


def _cpp_string(expression: str) -> str:
    match = re.fullmatch(
        r'(?:(?P<plain>"(?:[^"\\]|\\.)*")'
        r'|T_\(\s*(?P<translated>"(?:[^"\\]|\\.)*")\s*\))',
        expression,
    )
    if not match:
        raise InventoryError(f"spell title is not one literal or T_(literal): {expression!r}")
    try:
        value = ast.literal_eval(match.group("plain") or match.group("translated"))
    except (SyntaxError, ValueError) as exc:
        raise InventoryError(f"invalid C++ title literal: {expression!r}") from exc
    if not isinstance(value, str) or not value:
        raise InventoryError(f"empty or invalid spell title: {expression!r}")
    return value


def _balanced_entries(array_body: str) -> tuple[list[str], str]:
    blocks: list[str] = []
    residual: list[str] = []
    depth = 0
    start = -1
    in_string = False
    escaped = False
    for i, char in enumerate(array_body):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            if depth == 0:
                start = i + 1
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise InventoryError("unbalanced closing brace in spelldata")
            if depth == 0:
                blocks.append(array_body[start:i])
                residual.extend(" " * (i - start + 2))
        elif depth == 0:
            residual.append(char)
        else:
            residual.append(" ")
    if depth or in_string:
        raise InventoryError("unterminated spell entry in spelldata")
    return blocks, "".join(residual)


def _tag_major_version(path: Path) -> int:
    matches = re.findall(
        r"(?m)^\s*#define\s+TAG_MAJOR_VERSION\s+([0-9]+)\s*$", _read(path)
    )
    if len(matches) != 1:
        raise InventoryError(
            f"{path}: expected exactly one integer TAG_MAJOR_VERSION definition"
        )
    return int(matches[0])


def _tag_condition(expression: str, tag_major_version: int) -> bool:
    match = re.fullmatch(
        r"\s*TAG_MAJOR_VERSION\s*(==|!=|>=|<=|>|<)\s*([0-9]+)\s*",
        expression,
    )
    if not match:
        raise InventoryError(f"unsupported spell enum preprocessor condition: {expression!r}")
    right = int(match.group(2))
    return {
        "==": tag_major_version == right,
        "!=": tag_major_version != right,
        ">=": tag_major_version >= right,
        "<=": tag_major_version <= right,
        ">": tag_major_version > right,
        "<": tag_major_version < right,
    }[match.group(1)]


def expected_spell_enums(path: Path, tag_version_path: Path) -> set[str]:
    """Read the independently maintained production spell_type identity set."""
    tag_major_version = _tag_major_version(tag_version_path)
    text = _without_comments(_read(path))
    match = re.search(r"enum\s+spell_type\s*:\s*int\s*\{(.*?)\};", text, re.DOTALL)
    if not match:
        raise InventoryError(f"{path}: spell_type enum not found")

    active = True
    stack: list[tuple[bool, bool, bool]] = []
    retained: list[str] = []
    for number, line in enumerate(match.group(1).splitlines(), 1):
        directive = re.fullmatch(r"\s*#(if|else|endif)\b(.*)", line)
        if directive:
            kind, remainder = directive.groups()
            if kind == "if":
                condition = _tag_condition(remainder, tag_major_version)
                stack.append((active, condition, False))
                active = active and condition
            elif kind == "else":
                if not stack:
                    raise InventoryError(f"{path}:{number}: unmatched #else")
                parent, condition, seen_else = stack[-1]
                if seen_else or remainder.strip():
                    raise InventoryError(f"{path}:{number}: invalid #else")
                stack[-1] = (parent, condition, True)
                active = parent and not condition
            else:
                if not stack or remainder.strip():
                    raise InventoryError(f"{path}:{number}: invalid #endif")
                parent, _, _ = stack.pop()
                active = parent
            continue
        if "#" in line:
            raise InventoryError(f"{path}:{number}: unsupported preprocessor directive")
        if active:
            retained.append(line)
    if stack:
        raise InventoryError(f"{path}: unterminated spell enum preprocessor condition")

    identities: set[str] = set()
    for raw in "".join(retained).split(","):
        token = raw.strip()
        if not token:
            continue
        item = re.fullmatch(r"([A-Z][A-Z0-9_]*)(?:\s*=\s*([A-Z][A-Z0-9_]*))?", token)
        if not item:
            raise InventoryError(f"{path}: unparsed spell enum token {token!r}")
        name, alias = item.groups()
        if name == "SPELL_FIRST_SPELL":
            if not alias:
                raise InventoryError(f"{path}: SPELL_FIRST_SPELL must be an alias")
            continue
        if name == "NUM_SPELLS":
            continue
        if not name.startswith("SPELL_") or alias:
            raise InventoryError(f"{path}: unexpected spell enum item {token!r}")
        if name in identities:
            raise InventoryError(f"{path}: duplicate spell enum identity {name}")
        identities.add(name)
    if not identities:
        raise InventoryError(f"{path}: no production spell enum identities")
    return identities


def _lifecycle(enum: str, flags: str, *, axed: bool) -> str:
    if enum in {"SPELL_NO_SPELL", "SPELL_MELEE"}:
        return "internal_placeholder"
    if re.search(r"(?:^|\|)\s*spflag::dummy\s*(?:\||$)", flags):
        return "description_dummy"
    return "axed_compat" if axed else "active"


def parse_spells(path: Path, tag_version_path: Path) -> list[Spell]:
    text = _without_comments(_read(path))
    tag_major_version = _tag_major_version(tag_version_path)
    match = re.search(
        r"static\s+const\s+struct\s+spell_desc\s+spelldata\s*\[\s*\]\s*=\s*\{",
        text,
    )
    if not match:
        raise InventoryError("spelldata array declaration not found")
    start = match.end()
    depth = 1
    in_string = False
    escaped = False
    end = None
    for i in range(start, len(text)):
        char = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    if end is None:
        raise InventoryError("spelldata array is not closed")

    body = text[start:end]
    # The only generated records in the production header are the active
    # TAG_MAJOR_VERSION=34 AXED_SPELL compatibility records.
    conditional = re.search(
        r"(?ms)^\s*#if\s+TAG_MAJOR_VERSION\s*==\s*34\s*$"
        r"(.*?)^\s*#endif\s*$",
        body,
    )
    if not conditional:
        raise InventoryError("expected TAG_MAJOR_VERSION=34 AXED_SPELL block not found")
    conditional_body = conditional.group(1)
    axed_pattern = (
        r"(?m)^\s*AXED_SPELL\(\s*(SPELL_[A-Z0-9_]+)\s*,\s*"
        r'("(?:[^"\\]|\\.)*")\s*\)\s*$'
    )
    axed_candidates = re.findall(axed_pattern, conditional_body)
    if not axed_candidates:
        raise InventoryError("AXED_SPELL block contains no records")
    conditional_residual = re.sub(
        r"(?ms)^\s*#define\s+AXED_SPELL\(tag,\s*name\)\s*\\\s*$"
        r"\s*\{.*?\},\s*$",
        "",
        conditional_body,
    )
    conditional_residual = re.sub(axed_pattern, "", conditional_residual)
    if conditional_residual.strip():
        raise InventoryError("unparsed tokens remain in AXED_SPELL block")
    axed = axed_candidates if tag_major_version == 34 else []
    body = body[:conditional.start()] + body[conditional.end():]
    blocks, residual = _balanced_entries(body)
    # Outside records, only separators and preprocessor/macro definition lines
    # are permitted. Anything else means this parser skipped production data.
    residual = re.sub(r"(?m)^\s*#.*(?:\\\n.*)*$", "", residual)
    if re.sub(r"[\s,;]", "", residual):
        raise InventoryError("unparsed tokens remain in spelldata array")

    spells: list[Spell] = []
    for block in blocks:
        fields = _split_fields(block)
        if len(fields) != 10:
            enum = fields[0] if fields else "<unknown>"
            raise InventoryError(
                f"{enum}: expected 10 spell_desc fields, found {len(fields)}"
            )
        enum = fields[0]
        if not re.fullmatch(r"SPELL_[A-Z0-9_]+", enum):
            raise InventoryError(f"unknown spell enum expression: {enum!r}")
        try:
            level = int(fields[4])
        except ValueError as exc:
            raise InventoryError(f"{enum}: level is not an integer literal") from exc
        if not 1 <= level <= 9:
            raise InventoryError(f"{enum}: level {level} is outside production bounds")
        for label, expression in (("schools", fields[2]), ("flags", fields[3])):
            if not expression:
                raise InventoryError(f"{enum}: missing {label} expression")
        spells.append(
            Spell(enum, _cpp_string(fields[1]), fields[2], fields[3], level,
                  _lifecycle(enum, fields[3], axed=False))
        )

    for enum, title_literal in axed:
        spells.append(Spell(enum, _cpp_string(title_literal),
                            "spschool::none", "spflag::none", 7,
                            _lifecycle(enum, "spflag::none", axed=True)))
    if not spells:
        raise InventoryError("spelldata contains no records")
    enums = [spell.enum for spell in spells]
    duplicates = sorted({enum for enum in enums if enums.count(enum) > 1})
    if duplicates:
        raise InventoryError(f"duplicate spell enum(s): {', '.join(duplicates)}")
    return spells


def _parse_textdb(path: Path, *, trim_keys: bool) -> list[tuple[str, str]]:
    """Mirror database.cc `_parse_text_db` key/value construction."""
    entries: list[tuple[str, str]] = []
    key = ""
    value = ""
    in_entry = False
    saw_separator = False
    for number, raw in enumerate(_read(path).splitlines(), 1):
        if raw and raw[0] == "#":
            continue
        if raw.startswith("%%%%"):
            saw_separator = True
            if key:
                entries.append((key, value.lstrip("\n")))
            key = ""
            value = ""
            in_entry = True
        elif not in_entry:
            continue
        elif not key:
            key = raw.strip() if trim_keys else raw
            key = key.lower()
        else:
            value += raw.rstrip(" \t\r\n") + "\n"
    if key:
        entries.append((key, value.lstrip("\n")))
    if not saw_separator or not entries:
        raise InventoryError(f"{path}: no TextDB entries")
    for key, value in entries:
        if not key:
            raise InventoryError(f"{path}: empty TextDB key")
    return entries


def _production_map(entries: list[tuple[str, str]]) -> dict[str, str]:
    """Apply production TextDB's canonical-key, last-write-wins behavior."""
    result: dict[str, str] = {}
    for key, value in entries:
        result[key] = value
    return result


def _i18n_unescape_value(value: str) -> str:
    output: list[str] = []
    i = 0
    escapes = {"\\": "\\", "n": "\n", "r": "\r", "t": "\t"}
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            output.append(escapes.get(value[i + 1], value[i + 1]))
            i += 2
        else:
            output.append(value[i])
            i += 1
    return "".join(output)


def _i18n_escape_key(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )


def _source_lookup(entries: dict[str, str], english: str) -> str | None:
    stored = entries.get(_i18n_escape_key(english).lower())
    if not stored:
        return None
    return _i18n_unescape_value(stored.rstrip("\n\r"))


def _input_reference(path: Path) -> dict[str, str]:
    """Represent repository inputs portably and external inputs explicitly."""
    resolved = path.resolve()
    try:
        relative = resolved.relative_to(ROOT.resolve())
    except ValueError:
        return {"kind": "external", "path": str(resolved)}
    return {"kind": "repo_relative", "path": relative.as_posix()}


def build_inventory(args: argparse.Namespace) -> dict[str, object]:
    spells = parse_spells(args.spl_data, args.tag_version)
    expected = expected_spell_enums(args.spell_type, args.tag_version)
    actual = {spell.enum for spell in spells}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise InventoryError(
            "spl-data identity set differs from spell_type: "
            f"missing={missing}, extra={extra}"
        )
    zh_titles = _production_map(_parse_textdb(args.source_txt, trim_keys=False))
    en_desc = _production_map(_parse_textdb(args.en_descriptions, trim_keys=True))
    zh_desc = _production_map(_parse_textdb(args.zh_descriptions, trim_keys=True))
    records = []
    for spell in spells:
        description_key = f"{spell.title} spell"
        records.append({
            "enum": spell.enum,
            "english_title": spell.title,
            "level": spell.level,
            "schools_expression": spell.schools,
            "flags_expression": spell.flags,
            "lifecycle": spell.lifecycle,
            "zh_title": _source_lookup(zh_titles, spell.title),
            "description_key": description_key,
            "en_description_present": description_key.lower() in en_desc,
            "zh_description_present": description_key.lower() in zh_desc,
        })
    if args.require_zh_titles and any(row["zh_title"] is None for row in records):
        raise InventoryError("one or more spell titles lack an exact ZH mapping")
    if args.require_descriptions and any(
        not row["en_description_present"] or not row["zh_description_present"]
        for row in records
    ):
        raise InventoryError("one or more spells lack an EN or ZH description")
    return {
        "schema_version": 1,
        "inputs": {
            "spl_data": _input_reference(args.spl_data),
            "spell_type": _input_reference(args.spell_type),
            "tag_version": _input_reference(args.tag_version),
            "source_txt": _input_reference(args.source_txt),
            "en_descriptions": _input_reference(args.en_descriptions),
            "zh_descriptions": _input_reference(args.zh_descriptions),
        },
        "assertions": {
            "parsed_spell_count": len(records),
            "expected_enum_count": len(expected),
            "unique_enum_count": len({row["enum"] for row in records}),
            "enum_identity_complete_and_unique": actual == expected,
        },
        "spells": records,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Read-only tools for the current production spell artifact."
    )
    commands = result.add_subparsers(dest="command")
    inventory = commands.add_parser(
        "inventory", help="emit a deterministic JSON inventory to stdout"
    )
    inventory.add_argument("--spl-data", type=Path, default=DEFAULT_SPL_DATA)
    inventory.add_argument("--spell-type", type=Path, default=DEFAULT_SPELL_TYPE)
    inventory.add_argument("--tag-version", type=Path, default=DEFAULT_TAG_VERSION)
    inventory.add_argument("--source-txt", type=Path, default=DEFAULT_SOURCE_TXT)
    inventory.add_argument(
        "--en-descriptions", type=Path, default=DEFAULT_EN_DESCRIPTIONS
    )
    inventory.add_argument(
        "--zh-descriptions", type=Path, default=DEFAULT_ZH_DESCRIPTIONS
    )
    inventory.add_argument(
        "--require-zh-titles", action="store_true",
        help="fail unless every spell has an exact source.txt mapping",
    )
    inventory.add_argument(
        "--require-descriptions", action="store_true",
        help="fail unless every spell has both EN and ZH descriptions",
    )
    return result


def main(argv: list[str] | None = None) -> int:
    arg_parser = parser()
    args = arg_parser.parse_args(argv)
    if args.command is None:
        arg_parser.print_help()
        return 0
    try:
        artifact = build_inventory(args)
    except InventoryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    json.dump(artifact, sys.stdout, ensure_ascii=False, sort_keys=True, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
