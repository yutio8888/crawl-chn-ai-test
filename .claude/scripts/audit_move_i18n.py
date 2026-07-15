#!/usr/bin/env python3
"""Audit exact context-qualified movement phrase coverage.

The runtime C_() lookup falls back to the unqualified verb, so a successful
runtime lookup cannot prove that a context-specific translation exists. This
gate independently inventories reachable verbs and requires every expected
``context|verb`` TextDB key to exist with a non-empty translation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from i18n_shared import parse_entries


CONTEXTS = {
    "move.bare",
    "move.enter-area",
    "move.onto-surface",
    "move.onto-actor",
    "move.through-obstacle",
    "move.toward-target",
    "move.over-terrain",
}


def normalise_walking_verb(stem: str) -> str:
    verb = stem.lower()
    if verb == "wriggl":
        return "wriggle"
    if verb == "glid":
        return "walk"
    return verb


def string_literals(text: str) -> set[str]:
    return set(re.findall(r'"([^"\\]*(?:\\.[^"\\]*)*)"', text))


def strip_cpp_comments(text: str) -> str:
    text = re.sub(r"//[^\n]*", "", text)
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def call_arguments(text: str, function_names: set[str]) -> list[str]:
    """Return balanced argument text for named C++ calls, across newlines."""
    names = "|".join(re.escape(name) for name in sorted(function_names,
                                                          key=len, reverse=True))
    calls = []
    for match in re.finditer(rf"\b(?:{names})\s*\(", text):
        opening = text.find("(", match.start())
        depth = 0
        quote = None
        escaped = False
        for index in range(opening, len(text)):
            char = text[index]
            if quote:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == quote:
                    quote = None
                continue
            if char in {'"', "'"}:
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    calls.append(text[opening + 1:index])
                    break
    return calls


def split_arguments(arguments: str) -> list[str]:
    """Split a balanced C++ call argument list at top-level commas."""
    result = []
    start = 0
    depths = {"(": 0, "[": 0, "{": 0}
    closing = {")": "(", "]": "[", "}": "{"}
    quote = None
    escaped = False
    for index, char in enumerate(arguments):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {'"', "'"}:
            quote = char
        elif char in depths:
            depths[char] += 1
        elif char in closing:
            depths[closing[char]] -= 1
        elif char == "," and not any(depths.values()):
            result.append(arguments[start:index].strip())
            start = index + 1
    result.append(arguments[start:].strip())
    return result


def literal_argument(argument: str) -> str | None:
    match = re.fullmatch(r'\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*', argument)
    return match.group(1) if match else None


def function_body(text: str, signature: str) -> str:
    start = text.find(signature)
    if start < 0:
        raise ValueError(f"cannot find {signature}")
    opening = text.find("{", start)
    depth = 0
    for index in range(opening, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[opening + 1:index]
    raise ValueError(f"unterminated body for {signature}")


def discover(source: Path) -> dict[str, set[str]]:
    movement = (source / "movement.cc").read_text(encoding="utf-8")
    dynamic = string_literals(strip_cpp_comments(function_body(
        movement, "static string _get_move_verb")))

    species_verbs = set()
    for yaml_path in (source / "dat/species").glob("*.yaml"):
        match = re.search(r"^walking_verb:\s*(\S+)\s*$",
                          yaml_path.read_text(encoding="utf-8"), re.MULTILINE)
        if match:
            species_verbs.add(normalise_walking_verb(match.group(1)))
    dynamic |= species_verbs
    dynamic.add("walk")  # species without walking_verb use the default.

    fixed_by_call = {
        "check_moveto": {"step"},  # default argument in player.h
        "check_moveto_terrain": set(),
        "check_moveto_cloud": set(),
        "check_moveto_trap": set(),
        "check_moveto_exclusion": set(),
        "check_moveto_exclusions": set(),
        "check_move_over": set(),
    }
    for path in source.rglob("*.cc"):
        text = strip_cpp_comments(path.read_text(encoding="utf-8"))
        for name in fixed_by_call:
            for arguments in call_arguments(text, {name}):
                args = split_arguments(arguments)
                if len(args) > 1:
                    literal = literal_argument(args[1])
                    if literal:
                        fixed_by_call[name].add(literal)

    direct_context = {context: set() for context in CONTEXTS}
    context_names = {
        "bare": "move.bare",
        "enter_area": "move.enter-area",
        "onto_surface": "move.onto-surface",
        "onto_actor": "move.onto-actor",
        "through_obstacle": "move.through-obstacle",
        "toward_target": "move.toward-target",
        "over_terrain": "move.over-terrain",
    }
    for path in source.rglob("*.cc"):
        text = strip_cpp_comments(path.read_text(encoding="utf-8"))
        for arguments in call_arguments(text, {"translated_move_phrase"}):
            args = split_arguments(arguments)
            if len(args) < 2:
                continue
            verb = literal_argument(args[0])
            context_match = re.fullmatch(
                r"move_phrase_context::([a-z_]+)", args[1].strip())
            if verb and context_match and context_match.group(1) in context_names:
                direct_context[context_names[context_match.group(1)]].add(verb)

    spl = (source / "spl-transloc.cc").read_text(encoding="utf-8")
    cblink = set()
    for arguments in call_arguments(strip_cpp_comments(spl),
                                    {"_find_cblink_target"}):
        args = split_arguments(arguments)
        if len(args) > 2:
            literal = literal_argument(args[2])
            if literal:
                cblink.add(literal)

    full = dynamic | fixed_by_call["check_moveto"] | cblink
    terrain = fixed_by_call["check_moveto_terrain"]
    enter = (full | terrain | fixed_by_call["check_moveto_cloud"]
             | fixed_by_call["check_moveto_trap"]
             | fixed_by_call["check_moveto_exclusion"]
             | fixed_by_call["check_moveto_exclusions"]
             | fixed_by_call["check_move_over"])
    onto = (full | terrain | fixed_by_call["check_moveto_trap"]
            | fixed_by_call["check_move_over"])
    over = full | terrain
    discovered = {
        "move.bare": cblink,
        "move.enter-area": enter,
        "move.onto-surface": onto,
        "move.onto-actor": cblink,
        "move.through-obstacle": dynamic,
        "move.toward-target": dynamic & {"stride", "roll", "rampage"},
        "move.over-terrain": over,
    }
    for context, verbs in direct_context.items():
        discovered[context] |= verbs
    return discovered


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", nargs="?", default="crawl-ref/source")
    parser.add_argument("--source-txt",
                        default="crawl-ref/source/dat/i18n/zh/source.txt")
    parser.add_argument("--manifest",
                        default=".claude/scripts/data/move_i18n_manifest.json")
    args = parser.parse_args()

    source = Path(args.source)
    manifest_path = Path(args.manifest)
    source_txt = Path(args.source_txt)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contexts = manifest.get("contexts", {})
    errors: list[str] = []
    warnings: list[str] = []

    if set(contexts) != CONTEXTS:
        missing = sorted(CONTEXTS - set(contexts))
        unknown = sorted(set(contexts) - CONTEXTS)
        if missing:
            errors.append("manifest missing contexts: " + ", ".join(missing))
        if unknown:
            errors.append("manifest has unknown contexts: " + ", ".join(unknown))

    discovered = discover(source)
    entries = {
        entry.key: entry.value
        for entry in parse_entries(source_txt, lowercase_keys=False)
    }
    for context in sorted(CONTEXTS):
        record = contexts.get(context, {})
        if not isinstance(record.get("description"), str) or not record["description"].strip():
            errors.append(f"{context}: missing description")
        verbs = record.get("verbs", [])
        if not isinstance(verbs, list) or any(not isinstance(v, str) for v in verbs):
            errors.append(f"{context}: verbs must be a string list")
            continue
        if len(verbs) != len(set(verbs)):
            errors.append(f"{context}: duplicate verbs")
        actual = set(verbs)
        missing_verbs = discovered[context] - actual
        stale_verbs = actual - discovered[context]
        if missing_verbs:
            errors.append(f"{context}: unclassified reachable verbs: "
                          + ", ".join(sorted(missing_verbs)))
        if stale_verbs:
            warnings.append(f"{context}: stale manifest verbs: "
                            + ", ".join(sorted(stale_verbs)))
        for verb in sorted(actual):
            key = f"{context}|{verb}"
            if key not in entries:
                errors.append(f"missing exact TextDB key: {key}")
            elif not entries[key].strip():
                errors.append(f"empty translation: {key}")

    print("Movement i18n inventory:")
    for context in sorted(discovered):
        print(f"  {context}: {', '.join(sorted(discovered[context]))}")
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    print(f"Summary: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
