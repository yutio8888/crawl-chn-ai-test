#!/usr/bin/env python3
"""Immutable production inventory for the Issue #50 Hints review.

The identity space is the canonical-lowercase union of the effective EN and
ZH Hints TextDBs.  Producer evidence is rebuilt independently from every
``print_hint``, ``_get_hint`` and ``getHintString`` call in ``hints.cc``;
the only accepted non-literal producer calls are the two proven finite random
families.  Lifecycle exceptions are bound to their real enum/test consumers.

The script deliberately records language-structure differences without
turning them into translation judgements.  Malformed/unknown tokens and
unexplained producer or lifecycle gaps are emitted as blocking violations, so
the baseline inventory remains inspectable while the CLI still fails closed.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from command_inventory import (  # noqa: E402
    _desc_display,
    generate_name_table,
    git_show_blob,
    merge_desc_sequence,
    parse_command_enum,
    parse_db_keys,
    resolve_commit,
    write_inventory_output,
)
from i18n_shared import (  # noqa: E402
    AuditInput,
    load_review_input,
    lowercase_string,
    review_input_metadata,
    trusted_git_environment,
)
from tutorial_inventory import load_git_review_input  # noqa: E402


HINTS_EN = "crawl-ref/source/dat/descript/hints.txt"
HINTS_ZH = "crawl-ref/source/dat/descript/zh/hints.txt"
HINTS_CC = "crawl-ref/source/hints.cc"
HINTS_H = "crawl-ref/source/hints.h"
COMMAND_TYPE_H = "crawl-ref/source/command-type.h"
DATABASE_CC = "crawl-ref/source/database.cc"
L_CRAWL_CC = "crawl-ref/source/l-crawl.cc"
CTEST_CC = "crawl-ref/source/ctest.cc"
ZH_RUNTIME_LUA = "crawl-ref/source/test/zh_runtime.lua"
INVENT_CC = "crawl-ref/source/invent.cc"
FORMAT_CC = "crawl-ref/source/format.cc"
COLOUR_CC = "crawl-ref/source/colour.cc"
LIBUTIL_CC = "crawl-ref/source/libutil.cc"
GLOSSARY_MD = "docs/glossary.md"

INPUT_PATHS = (
    HINTS_EN,
    HINTS_ZH,
    HINTS_CC,
    HINTS_H,
    COMMAND_TYPE_H,
    DATABASE_CC,
    L_CRAWL_CC,
    CTEST_CC,
    ZH_RUNTIME_LUA,
    INVENT_CC,
    FORMAT_CC,
    COLOUR_CC,
    LIBUTIL_CC,
    GLOSSARY_MD,
)

STRICT_REVIEW_BEGIN = "<!-- BEGIN STRICT HINT REVIEW EVIDENCE v1 -->"
STRICT_REVIEW_END = "<!-- END STRICT HINT REVIEW EVIDENCE v1 -->"
TERMINAL_CONCLUSIONS = {
    "keep",
    "adjust",
    "retranslate",
    "defer terminology",
    "defer implementation",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
STRICT_CARD_FIELDS = {
    "actual_behavior",
    "confidence",
    "consumer",
    "current_chinese",
    "current_english",
    "deferral_owner",
    "deferral_reason",
    "dependency_group",
    "display_context",
    "evidence_locations",
    "fact_sha256",
    "glossary_authority",
    "identity",
    "lifecycle",
    "producer",
    "production_facts",
    "proposed_translation",
    "reentry_trigger",
    "rejected_alternatives",
    "reviewer_rationale",
    "terminal_conclusion",
}
_VAGUE_DEFERRAL_VALUES = {
    "n/a", "none", "not applicable", "tbd", "todo", "unknown",
    "不适用", "待定", "无",
}

FLEEING_KEY = "hint_fleeing_monster"
DISSECTION_KEY = "dissection reminder"

_ANY_HINT_CALL_RE = re.compile(
    r"\b(print_hint|_get_hint|getHintString)\s*\("
)
_LITERAL_HINT_CALL_RE = re.compile(
    r"\b(print_hint|_get_hint|getHintString)\s*\(\s*\"([^\"\n]+)\""
)
_KEY_RE = re.compile(r"[A-Za-z0-9_]+(?: [A-Za-z0-9_]+)*")
_COMMAND_RE = re.compile(r"\$cmd\[([A-Z][A-Z0-9_]*)\]")
_COMMAND_START_RE = re.compile(r"\$cmd\[")
_ITEM_RE = re.compile(r"\$item\[([a-z][a-z ]*)\]")
_ITEM_START_RE = re.compile(r"\$item\[")
_PLACEHOLDER_RE = re.compile(r"\$([12])(?![0-9])")
_DOLLAR_RE = re.compile(r"\$(?:[A-Za-z_][A-Za-z0-9_]*|[0-9]+)")

_PLATFORM_PROJECTIONS = (
    (
        "console",
        {
            "tiles": False,
            "console": True,
            "webtiles": False,
            "localtiles": False,
            "nomouse": True,
        },
    ),
    (
        "localtiles",
        {
            "tiles": True,
            "console": False,
            "webtiles": False,
            "localtiles": True,
            "nomouse": False,
        },
    ),
    (
        "webtiles",
        {
            "tiles": True,
            "console": False,
            "webtiles": True,
            "localtiles": False,
            "nomouse": True,
        },
    ),
)
_PLATFORM_UNTAG_ORDER = (
    "tiles", "console", "webtiles", "localtiles", "nomouse"
)


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _location(path: str, text: str, offset: int) -> str:
    return f"{path}:{_line_number(text, offset)}"


def _single_fragment(text: str, fragment: str, path: str) -> str:
    """Return an exact source location, rejecting missing/ambiguous facts."""
    if text.count(fragment) != 1:
        raise RuntimeError(
            f"{path}: expected exactly one consumer fragment {fragment!r}"
        )
    return _location(path, text, text.index(fragment))


def _canonical_key(raw: str, path: str, line: int) -> str:
    if not raw or raw.strip() != raw or not _KEY_RE.fullmatch(raw):
        raise RuntimeError(f"{path}:{line}: invalid hint lookup key {raw!r}")
    canonical = lowercase_string(raw)
    if not canonical:
        raise RuntimeError(f"{path}:{line}: empty canonical hint key")
    return canonical


def extract_producers(
    hints_cc: bytes,
) -> tuple[list[str], dict[str, list[dict[str, object]]]]:
    """Rebuild all static and finite-family hint producers from hints.cc.

    Every call occurrence is classified.  The function definitions and the
    two dynamic forwarding consumers are exact allowlisted shapes; a new
    dynamic call cannot silently disappear from the producer inventory.
    """
    text = hints_cc.decode("utf-8", errors="strict")
    literal_by_start = {
        match.start(): match for match in _LITERAL_HINT_CALL_RE.finditer(text)
    }
    facts: dict[str, list[dict[str, object]]] = {}

    def add(raw: str, function: str, offset: int, kind: str) -> None:
        canonical = _canonical_key(
            raw, HINTS_CC, _line_number(text, offset)
        )
        facts.setdefault(canonical, []).append({
            "function": function,
            "kind": kind,
            "lookup_key": raw,
            "location": _location(HINTS_CC, text, offset),
        })

    definitions = {
        "_get_hint": re.compile(
            r'_get_hint\(string key, const string& arg1 = "", '
            r'const string& arg2 = ""\)'
        ),
        "print_hint": re.compile(
            r"print_hint\(string key, const string& arg1, "
            r"const string& arg2\)"
        ),
    }
    forwarding = {
        "getHintString": re.compile(r"getHintString\(key\)"),
        "_get_hint": re.compile(r"_get_hint\(key, arg1, arg2\)"),
    }
    death_call = re.compile(
        r'print_hint\(make_stringf\("death random %d", hint\)\)'
    )
    finished_call = re.compile(
        r'print_hint\(make_stringf\("finished random %d", random2\(4\)\)\)'
    )

    classified: set[int] = set()
    for start, match in literal_by_start.items():
        add(match.group(2), match.group(1), start, "literal")
        classified.add(start)

    for name, pattern in definitions.items():
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise RuntimeError(f"{HINTS_CC}: {name} definition shape changed")
        classified.add(matches[0].start())

    forwarding_expected = {"getHintString": 2, "_get_hint": 1}
    for name, pattern in forwarding.items():
        matches = list(pattern.finditer(text))
        if len(matches) != forwarding_expected[name]:
            raise RuntimeError(f"{HINTS_CC}: {name} forwarding shape changed")
        classified.update(match.start() for match in matches)

    family_specs = (
        (
            death_call,
            range(6),
            "death random {}",
            (
                "int hint = random2(6);",
                "hint = random2(5) + 1;",
                "hint = random2(4) + 1;",
                "hint = random2(5);",
            ),
        ),
        (
            finished_call,
            range(4),
            "finished random {}",
            ("random2(4)",),
        ),
    )
    for pattern, values, template, proof_fragments in family_specs:
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise RuntimeError(
                f"{HINTS_CC}: finite producer family {template!r} changed"
            )
        match = matches[0]
        classified.add(match.start())
        for fragment in proof_fragments:
            if text.count(fragment) < 1:
                raise RuntimeError(
                    f"{HINTS_CC}: finite-family range proof changed: "
                    f"{fragment!r}"
                )
        for value in values:
            add(template.format(value), "print_hint", match.start(), "finite-family")

    calls = list(_ANY_HINT_CALL_RE.finditer(text))
    unresolved = [
        _location(HINTS_CC, text, match.start())
        for match in calls if match.start() not in classified
    ]
    if unresolved:
        raise RuntimeError(
            f"{HINTS_CC}: unparsed hint call shape(s): {unresolved}"
        )
    if len(classified) != len(calls):
        raise RuntimeError(f"{HINTS_CC}: hint call classification is ambiguous")

    ordered = sorted(facts)
    return ordered, {key: facts[key] for key in ordered}


def _parse_runtime_test_keys(text: str) -> tuple[list[str], str]:
    pattern = re.compile(
        r'for _, hint_key in ipairs\(\{(?P<keys>[^}]*)\}\) do\s*'
        r'local hint = crawl\.test_hint_text\(hint_key\)\s*'
        r'assert\(string\.find\(hint, god_display, 1, true\).*?\s*end',
        re.DOTALL,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"{ZH_RUNTIME_LUA}: localized hint test shape changed")
    keys = re.findall(r'"([^"\n]+)"', matches[0].group("keys"))
    if keys != ["dissection reminder", "HINT_CONVERT"]:
        raise RuntimeError(
            f"{ZH_RUNTIME_LUA}: localized compatibility keys changed: {keys}"
        )
    return [lowercase_string(key) for key in keys], _location(
        ZH_RUNTIME_LUA, text, matches[0].start()
    )


def _verify_lifecycle_sources(blobs: dict[str, bytes]) -> dict[str, object]:
    hints_h = blobs[HINTS_H].decode("utf-8", errors="strict")
    guarded = re.compile(
        r"#if TAG_MAJOR_VERSION == 34\s*"
        r"HINT_FLEEING_MONSTER,\s*#endif"
    )
    matches = list(guarded.finditer(hints_h))
    if len(matches) != 1:
        raise RuntimeError(
            f"{HINTS_H}: TAG34 HINT_FLEEING_MONSTER lifecycle changed"
        )
    runtime_text = blobs[ZH_RUNTIME_LUA].decode("utf-8", errors="strict")
    test_keys, test_location = _parse_runtime_test_keys(runtime_text)
    return {
        "fleeing_location": _location(HINTS_H, hints_h, matches[0].start()),
        "localized_test_keys": test_keys,
        "localized_test_location": test_location,
    }


def _verify_consumers(blobs: dict[str, bytes]) -> dict[str, str]:
    """Bind lookup, substitution, display, Lua and test consumers."""
    required = {
        HINTS_CC: (
            'string text = getHintString("welcome");',
            "string text = _get_hint(key, arg1, arg2);",
            'while ((p = text.find("$cmd[")) != string::npos)',
            'while ((p = text.find("$item[")) != string::npos)',
            'while ((p = text.find("<input>")) != string::npos)',
            'text = replace_all(text, "$1", arg1);',
            'text = replace_all(text, "$2", arg2);',
            "_replace_static_tags(text);\n    text = untag_tiles_console(text);\n"
            '    text = replace_all(text, "$1", arg1);',
            "auto prompt_ui = make_shared<Text>(formatted_string::parse_string(text));",
            'for (const string &chunk : split_string("\\n", text))\n'
            '        mprf(MSGCH_TUTORIAL, "%s", chunk.c_str());',
            'mprf(MSGCH_TUTORIAL, "%s", output.c_str());',
        ),
        DATABASE_CC: (
            "string getHintString(const string &key)",
            "return unwrap_desc(_query_database(HintsDB, key, true, true));",
            "_execute_embedded_lua(result);",
        ),
        L_CRAWL_CC: (
            "LUAWRAP(crawl_print_hint, print_hint(luaL_checkstring(ls, 1),",
            '{ "print_hint", crawl_print_hint },',
        ),
        CTEST_CC: (
            "static int crawl_test_hint_text(lua_State *ls)",
            "getHintString(luaL_checkstring(ls, 1)).c_str()",
        ),
    }
    locations: dict[str, str] = {}
    for path, fragments in required.items():
        text = blobs[path].decode("utf-8", errors="strict")
        for fragment in fragments:
            locations[f"{path}:{fragment}"] = _single_fragment(
                text, fragment, path
            )
    return locations


def _accepted_item_tokens(blobs: dict[str, bytes]) -> set[str]:
    text = blobs[INVENT_CC].decode("utf-8", errors="strict")
    match = re.search(
        r"const char \*item_class_name\(int type, bool terse\)\s*\{\s*"
        r"if \(terse\)\s*\{(?P<body>.*?)\}\s*else\s*\{",
        text,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"{INVENT_CC}: terse item_class_name switch changed")
    names = set(re.findall(r'case OBJ_[A-Z_]+:\s+return "([^"\n]+)";', match.group("body")))
    if not names or 'default:             return "";' not in match.group("body"):
        raise RuntimeError(f"{INVENT_CC}: terse item names are incomplete")
    hints_text = blobs[HINTS_CC].decode("utf-8", errors="strict")
    if hints_text.count('if (item == "amulet")') != 1:
        raise RuntimeError(f"{HINTS_CC}: amulet item-token exception changed")
    names.add("amulet")
    return names


def _accepted_markup_tags(blobs: dict[str, bytes]) -> tuple[set[str], set[str]]:
    colour = blobs[COLOUR_CC].decode("utf-8", errors="strict")
    match = re.search(
        r"static const char\* const cols\[(\d+)\]\s*=\s*\{(.*?)\};",
        colour,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"{COLOUR_CC}: terminal colour table changed")
    colours = set(re.findall(r'"([^"\n]+)"', match.group(2)))
    if len(colours) != int(match.group(1)):
        raise RuntimeError(f"{COLOUR_CC}: terminal colour table is ambiguous")
    colours.update({"lightgray", "darkgray"})

    format_text = blobs[FORMAT_CC].decode("utf-8", errors="strict")
    for fragment in ('if (tag == "h")', 'if (tag == "w")'):
        _single_fragment(format_text, fragment, FORMAT_CC)

    libutil = blobs[LIBUTIL_CC].decode("utf-8", errors="strict")
    consumer = re.search(
        r"string untag_tiles_console\(string s\)\s*\{"
        r"(?P<body>.*?)\n\s*return s;\s*\n\}",
        libutil,
        re.DOTALL,
    )
    if not consumer:
        raise RuntimeError(f"{LIBUTIL_CC}: platform-tag consumer changed")
    platform_calls = re.findall(
        r'_untag\(s, "<([a-z]+)>", "</\1>", ([^;\n]+)\);',
        consumer.group("body"),
    )
    expected_calls = [
        ("tiles", "is_tiles()"),
        ("console", "!is_tiles()"),
        ("webtiles", "true"),
        ("webtiles", "false"),
        ("localtiles", "true"),
        ("nomouse", "false"),
        ("localtiles", "false"),
        ("nomouse", "true"),
    ]
    if platform_calls != expected_calls:
        raise RuntimeError(
            f"{LIBUTIL_CC}: platform-tag consumer changed: "
            f"expected={expected_calls} actual={platform_calls}"
        )
    platform = {name for name, _condition in platform_calls}
    expected_platform = set(_PLATFORM_UNTAG_ORDER)
    if platform != expected_platform:
        raise RuntimeError(
            f"{LIBUTIL_CC}: platform-tag consumer changed: "
            f"expected={sorted(expected_platform)} actual={sorted(platform)}"
        )
    hints_text = blobs[HINTS_CC].decode("utf-8", errors="strict")
    _single_fragment(hints_text, 'text.find("<input>")', HINTS_CC)
    return colours | {"h", "w", "input"} | platform, platform


def _markup_facts(
    value: str, allowed_tags: set[str], platform_tags: set[str]
) -> dict[str, object]:
    tags: list[dict[str, object]] = []
    malformed: list[dict[str, object]] = []
    index = 0
    while index < len(value):
        start = value.find("<", index)
        if start < 0:
            break
        if start + 1 < len(value) and value[start + 1] == "<":
            index = start + 2
            continue
        end = value.find(">", start + 1)
        newline = value.find("\n", start + 1)
        if end < 0 or (newline >= 0 and newline < end):
            stop = newline if newline >= 0 else len(value)
            malformed.append({
                "line": _line_number(value, start),
                "token": value[start:stop],
            })
            index = start + 1
            continue
        raw = value[start:end + 1]
        content = value[start + 1:end]
        match = re.fullmatch(r"(/?)([A-Za-z][A-Za-z0-9:]*)", content)
        if not match:
            malformed.append({"line": _line_number(value, start), "token": raw})
        else:
            tags.append({
                "closing": bool(match.group(1)),
                "line": _line_number(value, start),
                "name": match.group(2),
                "raw": raw,
            })
        index = end + 1

    unknown = sorted({tag["name"] for tag in tags if tag["name"] not in allowed_tags})
    stack: list[str] = []
    balance_errors: list[str] = []
    for tag in tags:
        name = str(tag["name"])
        if name not in allowed_tags:
            continue
        if not tag["closing"]:
            stack.append(name)
        elif not stack or stack[-1] != name:
            balance_errors.append(f"line {tag['line']}: unexpected </{name}>")
        else:
            stack.pop()
    balance_errors.extend(f"unclosed <{name}>" for name in reversed(stack))
    raw_sequence = [str(tag["raw"]) for tag in tags]
    platform_sequence = [
        str(tag["raw"]) for tag in tags if tag["name"] in platform_tags
    ]
    return {
        "balance_errors": balance_errors,
        "malformed": malformed,
        "platform_counts": dict(sorted(Counter(platform_sequence).items())),
        "platform_sequence": platform_sequence,
        "tag_counts": dict(sorted(Counter(raw_sequence).items())),
        "tag_sequence": raw_sequence,
        "unknown_tags": unknown,
    }


def _lua_facts(value: str) -> dict[str, object]:
    blocks: list[dict[str, object]] = []
    errors: list[str] = []
    index = 0
    while index < len(value):
        start = value.find("{{", index)
        stray_end = value.find("}}", index)
        if stray_end >= 0 and (start < 0 or stray_end < start):
            errors.append(f"line {_line_number(value, stray_end)}: unmatched }}}}")
            index = stray_end + 2
            continue
        if start < 0:
            break
        end = value.find("}}", start + 2)
        if end < 0:
            errors.append(f"line {_line_number(value, start)}: unbalanced {{{{")
            break
        body = value[start + 2:end]
        if not body.strip():
            errors.append(f"line {_line_number(value, start)}: empty Lua block")
        blocks.append({
            "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "line": _line_number(value, start),
            "source": body,
        })
        index = end + 2
    return {"blocks": blocks, "errors": errors}


def _project_platform_value(
    value: str,
    keep_tags: dict[str, bool],
    allowed_tags: set[str],
) -> list[tuple[str, int]]:
    """Apply production platform filtering and strip presentation markup.

    Each surviving character retains its source offset.  This lets adjacency
    facts distinguish command occurrences after mutually exclusive branches
    have been projected instead of concatenating every branch together.
    """
    projected = [(character, offset) for offset, character in enumerate(value)]
    for name in _PLATFORM_UNTAG_ORDER:
        opening = f"<{name}>"
        closing = f"</{name}>"
        while True:
            text = "".join(character for character, _offset in projected)
            start = text.find(opening)
            if start < 0:
                break
            end = text.find(closing, start)
            if keep_tags[name]:
                if end >= 0:
                    del projected[end:end + len(closing)]
                del projected[start:start + len(opening)]
            else:
                stop = len(projected) if end < 0 else end + len(closing)
                del projected[start:stop]

    index = 0
    while index < len(projected):
        text = "".join(character for character, _offset in projected)
        start = text.find("<", index)
        if start < 0:
            break
        if start + 1 < len(text) and text[start + 1] == "<":
            index = start + 2
            continue
        end = text.find(">", start + 1)
        newline = text.find("\n", start + 1)
        if end < 0 or (newline >= 0 and newline < end):
            index = start + 1
            continue
        match = re.fullmatch(
            r"/?([A-Za-z][A-Za-z0-9:]*)", text[start + 1:end]
        )
        if match and match.group(1) in allowed_tags:
            del projected[start:end + 1]
            index = start
        else:
            index = end + 1
    return projected


def _command_ascii_adjacencies(
    value: str,
    allowed_tags: set[str],
    platform_tags: set[str],
) -> list[dict[str, object]]:
    if platform_tags != set(_PLATFORM_UNTAG_ORDER):
        raise RuntimeError("command adjacency platform projection is incomplete")

    by_occurrence: dict[tuple[int, str], dict[str, object]] = {}
    for platform, keep_tags in _PLATFORM_PROJECTIONS:
        projected = _project_platform_value(value, keep_tags, allowed_tags)
        text = "".join(character for character, _offset in projected)
        for match in _COMMAND_RE.finditer(text):
            prefix = text[match.start() - 1] if match.start() else None
            suffix = text[match.end()] if match.end() < len(text) else None
            ascii_prefix = (
                prefix if prefix is not None and re.fullmatch(r"[A-Za-z]", prefix)
                else None
            )
            ascii_suffix = (
                suffix if suffix is not None and re.fullmatch(r"[A-Za-z]", suffix)
                else None
            )
            if ascii_prefix is None and ascii_suffix is None:
                continue
            source_offset = projected[match.start()][1]
            key = (source_offset, match.group(1))
            fact = by_occurrence.setdefault(key, {
                "command": match.group(1),
                "projections": [],
                "source_line": _line_number(value, source_offset),
                "source_offset": source_offset,
            })
            projections = fact["projections"]
            assert isinstance(projections, list)
            projections.append({
                "ascii_prefix": ascii_prefix,
                "ascii_suffix": ascii_suffix,
                "platform": platform,
            })
    return [by_occurrence[key] for key in sorted(by_occurrence)]


def _token_facts(
    value: str,
    command_names: set[str],
    item_names: set[str],
    allowed_tags: set[str],
    platform_tags: set[str],
) -> dict[str, object]:
    command_matches = list(_COMMAND_RE.finditer(value))
    item_matches = list(_ITEM_RE.finditer(value))
    placeholder_matches = list(_PLACEHOLDER_RE.finditer(value))
    accepted_dollar_starts = {
        match.start() for match in command_matches + item_matches + placeholder_matches
    }
    commands = [match.group(1) for match in command_matches]
    items = [match.group(1) for match in item_matches]
    placeholders = [match.group(1) for match in placeholder_matches]
    malformed_commands = []
    if len(command_matches) != len(_COMMAND_START_RE.findall(value)):
        malformed_commands.append("unterminated or malformed $cmd token")
    malformed_items = []
    if len(item_matches) != len(_ITEM_START_RE.findall(value)):
        malformed_items.append("unterminated or malformed $item token")
    unknown_dollar = [
        {"line": _line_number(value, match.start()), "token": match.group(0)}
        for match in _DOLLAR_RE.finditer(value)
        if match.start() not in accepted_dollar_starts
    ]
    markup = _markup_facts(value, allowed_tags, platform_tags)
    lua = _lua_facts(value)
    return {
        "commands": commands,
        "command_counts": dict(sorted(Counter(commands).items())),
        "command_ascii_adjacencies": _command_ascii_adjacencies(
            value, allowed_tags, platform_tags
        ),
        "items": items,
        "item_counts": dict(sorted(Counter(items).items())),
        "lua": lua,
        "malformed_commands": malformed_commands,
        "malformed_items": malformed_items,
        "markup": markup,
        "placeholders": placeholders,
        "placeholder_counts": dict(sorted(Counter(placeholders).items())),
        "unknown_commands": sorted(set(commands) - command_names),
        "unknown_dollar_tokens": unknown_dollar,
        "unknown_items": sorted(set(items) - item_names),
    }


def _contract_comparison(
    english: dict[str, object], chinese: dict[str, object]
) -> dict[str, bool]:
    en_markup = english["markup"]
    zh_markup = chinese["markup"]
    en_lua = english["lua"]
    zh_lua = chinese["lua"]
    assert isinstance(en_markup, dict) and isinstance(zh_markup, dict)
    assert isinstance(en_lua, dict) and isinstance(zh_lua, dict)
    return {
        "command_counts": english["command_counts"] == chinese["command_counts"],
        "command_sequence": english["commands"] == chinese["commands"],
        "item_counts": english["item_counts"] == chinese["item_counts"],
        "item_sequence": english["items"] == chinese["items"],
        "lua_block_count": len(en_lua["blocks"]) == len(zh_lua["blocks"]),
        "lua_source_sequence": [block["source"] for block in en_lua["blocks"]]
        == [block["source"] for block in zh_lua["blocks"]],
        "markup_counts": en_markup["tag_counts"] == zh_markup["tag_counts"],
        "markup_sequence": en_markup["tag_sequence"] == zh_markup["tag_sequence"],
        "placeholder_counts": english["placeholder_counts"] == chinese["placeholder_counts"],
        "placeholder_sequence": english["placeholders"] == chinese["placeholders"],
        "platform_tag_counts": en_markup["platform_counts"] == zh_markup["platform_counts"],
        "platform_tag_sequence": en_markup["platform_sequence"] == zh_markup["platform_sequence"],
    }


def _token_errors(language: str, identity: str, facts: dict[str, object]) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    direct_fields = (
        "malformed_commands", "malformed_items", "unknown_commands",
        "unknown_dollar_tokens", "unknown_items",
    )
    for field in direct_fields:
        if facts[field]:
            errors.append({
                "identity": identity,
                "kind": f"{language}-{field.replace('_', '-')}",
                "detail": json.dumps(facts[field], ensure_ascii=False, sort_keys=True),
            })
    if language == "english" and facts["command_ascii_adjacencies"]:
        errors.append({
            "identity": identity,
            "kind": "english-command-ascii-adjacency",
            "detail": json.dumps(
                facts["command_ascii_adjacencies"],
                ensure_ascii=False,
                sort_keys=True,
            ),
        })
    markup = facts["markup"]
    lua = facts["lua"]
    assert isinstance(markup, dict) and isinstance(lua, dict)
    for field in ("malformed", "unknown_tags", "balance_errors"):
        if markup[field]:
            errors.append({
                "identity": identity,
                "kind": f"{language}-markup-{field.replace('_', '-')}",
                "detail": json.dumps(markup[field], ensure_ascii=False, sort_keys=True),
            })
    if lua["errors"]:
        errors.append({
            "identity": identity,
            "kind": f"{language}-lua-errors",
            "detail": json.dumps(lua["errors"], ensure_ascii=False, sort_keys=True),
        })
    return errors


def _dependency_group(key: str) -> str:
    if key == "welcome" or key.startswith(("death", "finished")):
        return "entry, death, and completion"
    if any(word in key for word in (
        "potion", "scroll", "wand", "weapon", "missile", "armour",
        "jewellery", "staff", "gold", "pickup", "inventory", "item",
    )):
        return "items and inventory"
    if any(word in key for word in (
        "stair", "branch", "portal", "trap", "door", "shop", "map",
        "explore", "travel", "abyss",
    )):
        return "movement and exploration"
    if any(word in key for word in (
        "convert", "god", "ability", "piety", "excommunicate",
    )):
        return "gods and abilities"
    if any(word in key for word in (
        "spell", "magic", "miscast", "contamination", "silence", "cloud",
    )):
        return "magic and status"
    if any(word in key for word in (
        "monster", "berserk", "healing", "poison", "resist", "fire",
        "run_away", "retreat", "fleeing", "net",
    )):
        return "combat and survival"
    return "interface and progression"


def _fact_sha(row: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _entry_maps(
    blobs: dict[str, bytes]
) -> tuple[dict[str, object], dict[str, object]]:
    maps = []
    for path in (HINTS_EN, HINTS_ZH):
        entries = parse_db_keys(
            blobs[path].decode("utf-8", errors="strict"), path
        )
        effective, overrides = merge_desc_sequence(entries)
        if overrides:
            raise RuntimeError(f"{path}: TextDB overrides are forbidden: {overrides}")
        empty = [
            {"raw_key": entry.raw_key, "key_line": entry.key_line}
            for entry in entries if not _desc_display(entry.value)
        ]
        if empty:
            raise RuntimeError(f"{path}: empty TextDB values are forbidden: {empty}")
        for canonical, entry in effective.items():
            if not canonical or not entry.raw_key:
                raise RuntimeError(f"{path}: empty TextDB key is forbidden")
        maps.append(effective)
    return maps[0], maps[1]


def build_payload(baseline: str) -> dict[str, object]:
    blobs = {path: git_show_blob(baseline, path) for path in INPUT_PATHS}
    return build_payload_from_blobs(baseline, blobs)


def build_payload_from_blobs(
    baseline: str, blobs: dict[str, bytes]
) -> dict[str, object]:
    """Build from an already frozen exact manifest (the focused-test seam)."""
    if set(blobs) != set(INPUT_PATHS):
        raise RuntimeError(
            "hint input manifest mismatch: "
            f"missing={sorted(set(INPUT_PATHS) - set(blobs))} "
            f"extra={sorted(set(blobs) - set(INPUT_PATHS))}"
        )
    consumers = _verify_consumers(blobs)
    lifecycle = _verify_lifecycle_sources(blobs)
    producer_keys, producer_facts = extract_producers(blobs[HINTS_CC])
    en_effective, zh_effective = _entry_maps(blobs)
    en_keys = set(en_effective)
    zh_keys = set(zh_effective)
    union = en_keys | zh_keys
    producer_set = set(producer_keys)

    command_enum = parse_command_enum(
        blobs[COMMAND_TYPE_H].decode("utf-8", errors="strict")
    )
    command_names = set(generate_name_table(command_enum).values())
    item_names = _accepted_item_tokens(blobs)
    allowed_tags, platform_tags = _accepted_markup_tags(blobs)

    blocking: list[dict[str, str]] = []
    for key in sorted(producer_set - union):
        blocking.append({
            "identity": f"hint:{key}",
            "kind": "producer-without-textdb-identity",
            "detail": "hints.cc producer is absent from both EN and ZH TextDB",
        })

    inventory: list[dict[str, object]] = []
    for key in sorted(union):
        en = en_effective.get(key)
        zh = zh_effective.get(key)
        english = _desc_display(en.value) if en else None
        chinese = _desc_display(zh.value) if zh else None
        if key in producer_set:
            lifecycle_name = "current-producer"
        elif key == FLEEING_KEY and key in en_keys and key in zh_keys:
            lifecycle_name = "tag34-enum-compatibility-unconsumed"
        elif (
            key == DISSECTION_KEY
            and key not in en_keys
            and key in zh_keys
            and key in lifecycle["localized_test_keys"]
        ):
            lifecycle_name = "localized-test-only-compatibility"
        else:
            lifecycle_name = "unexplained-unconsumed"
            blocking.append({
                "identity": f"hint:{key}",
                "kind": "unexplained-unconsumed-textdb-identity",
                "detail": "TextDB identity has no accepted producer/lifecycle evidence",
            })

        producer_locations = [
            fact["location"] for fact in producer_facts.get(key, [])
        ]
        if lifecycle_name == "tag34-enum-compatibility-unconsumed":
            producer_locations = [str(lifecycle["fleeing_location"])]
        elif lifecycle_name == "localized-test-only-compatibility":
            producer_locations = [str(lifecycle["localized_test_location"])]

        en_tokens = _token_facts(
            english or "", command_names, item_names, allowed_tags, platform_tags
        )
        zh_tokens = _token_facts(
            chinese or "", command_names, item_names, allowed_tags, platform_tags
        )
        comparison = _contract_comparison(en_tokens, zh_tokens)
        structural_differences = sorted(
            field for field, equal in comparison.items() if not equal
        )

        producer_functions = {
            str(fact["function"]) for fact in producer_facts.get(key, [])
        }
        if key == "welcome":
            display_context = (
                "Hints starting-screen popup after DB lookup and static "
                "substitutions."
            )
        elif "_get_hint" in producer_functions:
            display_context = (
                "Hint fragment composed into learned_something_new output after "
                "DB lookup and substitutions."
            )
        elif lifecycle_name == "current-producer":
            display_context = "Hints/tutorial message stream through print_hint."
        elif lifecycle_name == "tag34-enum-compatibility-unconsumed":
            display_context = "TAG34 compatibility TextDB entry; no current hints.cc display call."
        else:
            display_context = (
                "ZH runtime localized embedded-Lua lookup test only; no "
                "gameplay producer."
            )

        lookup_location = consumers[
            f"{DATABASE_CC}:return unwrap_desc(_query_database(HintsDB, key, true, true));"
        ]
        lua_location = consumers[f"{DATABASE_CC}:_execute_embedded_lua(result);"]
        substitution_location = consumers[
            f'{HINTS_CC}:while ((p = text.find("$cmd[")) != string::npos)'
        ]
        if lifecycle_name == "tag34-enum-compatibility-unconsumed":
            consumer = {
                "compatibility_enum": str(lifecycle["fleeing_location"]),
                "current_display": None,
            }
        elif lifecycle_name == "localized-test-only-compatibility":
            consumer = {
                "lookup": lookup_location,
                "lua": lua_location,
                "test": consumers[
                    f"{CTEST_CC}:getHintString(luaL_checkstring(ls, 1)).c_str()"
                ],
            }
        else:
            if key == "welcome":
                display_location = consumers[
                    f"{HINTS_CC}:auto prompt_ui = make_shared<Text>("
                    "formatted_string::parse_string(text));"
                ]
            elif "_get_hint" in producer_functions:
                display_location = consumers[
                    f'{HINTS_CC}:mprf(MSGCH_TUTORIAL, "%s", output.c_str());'
                ]
            else:
                display_location = consumers[
                    f'{HINTS_CC}:for (const string &chunk : split_string("\\n", text))\n'
                    f'        mprf(MSGCH_TUTORIAL, "%s", chunk.c_str());'
                ]
            consumer = {
                "display": display_location,
                "lookup": lookup_location,
                "lua": lua_location,
                "substitution": substitution_location,
            }

        mechanical: dict[str, object] = {
            "identity": f"hint:{key}",
            "key": key,
            "lifecycle": lifecycle_name,
            "english": english,
            "chinese": chinese,
            "english_key_line": en.key_line if en else None,
            "chinese_key_line": zh.key_line if zh else None,
            "english_raw_key": en.raw_key if en else None,
            "chinese_raw_key": zh.raw_key if zh else None,
            "producer_calls": producer_facts.get(key, []),
            "producer_locations": producer_locations,
            "consumer": consumer,
            "display_context": display_context,
            "dependency_group": _dependency_group(key),
            "english_tokens": en_tokens,
            "chinese_tokens": zh_tokens,
            "token_contract_equal": comparison,
            "structural_differences": structural_differences,
        }
        mechanical["fact_sha256"] = _fact_sha(mechanical)
        inventory.append(mechanical)
        blocking.extend(_token_errors("english", mechanical["identity"], en_tokens))
        blocking.extend(_token_errors("chinese", mechanical["identity"], zh_tokens))

    for language, missing in (
        ("english", producer_set - en_keys),
        ("chinese", producer_set - zh_keys),
    ):
        for key in sorted(missing):
            blocking.append({
                "identity": f"hint:{key}",
                "kind": f"producer-missing-{language}-textdb",
                "detail": f"current producer lacks a {language} TextDB value",
            })

    inventory_keys = [str(row["key"]) for row in inventory]
    if inventory_keys != sorted(union) or len(inventory_keys) != len(set(inventory_keys)):
        raise RuntimeError("hint inventory identity order/uniqueness invariant failed")

    payload: dict[str, object] = {
        "baseline": baseline,
        "glossary_sha256": hashlib.sha256(blobs[GLOSSARY_MD]).hexdigest(),
        "inputs": {
            path: {"sha256": hashlib.sha256(blobs[path]).hexdigest()}
            for path in INPUT_PATHS
        },
        "producer_keys": producer_keys,
        "hints_en_keys": sorted(en_keys),
        "hints_zh_keys": sorted(zh_keys),
        "union_keys": sorted(union),
        "producer_minus_en": sorted(producer_set - en_keys),
        "en_minus_producer": sorted(en_keys - producer_set),
        "producer_minus_zh": sorted(producer_set - zh_keys),
        "zh_minus_producer": sorted(zh_keys - producer_set),
        "en_minus_zh": sorted(en_keys - zh_keys),
        "zh_minus_en": sorted(zh_keys - en_keys),
        "inventory_minus_union": sorted(set(inventory_keys) - union),
        "union_minus_inventory": sorted(union - set(inventory_keys)),
        "blocking_violations": sorted(
            blocking,
            key=lambda value: (
                value["identity"], value["kind"], value["detail"]
            ),
        ),
        "structural_review_candidates": [
            row["identity"] for row in inventory
            if row["structural_differences"]
        ],
        "inventory": inventory,
    }
    payload["inventory_sha256"] = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return payload


def _load_json(line: str, label: str) -> object:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON value {value}")

    try:
        return json.loads(line, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"invalid {label} JSON") from error


def parse_review(
    review_input: AuditInput,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    text = review_input.text
    if text.count(STRICT_REVIEW_BEGIN) != 1 or text.count(STRICT_REVIEW_END) != 1:
        raise RuntimeError("strict hint review block is missing or duplicated")
    block = text.split(STRICT_REVIEW_BEGIN, 1)[1].split(STRICT_REVIEW_END, 1)[0]
    if not block.startswith("\n") or not block.endswith("\n"):
        raise RuntimeError("strict hint review framing is invalid")
    lines = block[1:-1].splitlines()
    if len(lines) < 4 or lines[1] != "```jsonl" or lines[-1] != "```":
        raise RuntimeError("strict hint review structure is invalid")
    metadata = _load_json(lines[0], "hint review metadata")
    expected_meta = {
        "baseline", "glossary_sha256", "identity_count", "inventory_sha256"
    }
    if not isinstance(metadata, dict) or set(metadata) != expected_meta:
        raise RuntimeError("strict hint review metadata fields are invalid")
    if lines[0] != json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ):
        raise RuntimeError("strict hint review metadata is not canonical JSON")
    if (
        not isinstance(metadata["baseline"], str)
        or not re.fullmatch(r"[0-9a-f]{40}", metadata["baseline"])
        or not isinstance(metadata["glossary_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", metadata["glossary_sha256"])
        or not isinstance(metadata["inventory_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", metadata["inventory_sha256"])
        or isinstance(metadata["identity_count"], bool)
        or not isinstance(metadata["identity_count"], int)
        or metadata["identity_count"] < 0
    ):
        raise RuntimeError("strict hint review metadata values are invalid")

    cards: list[dict[str, object]] = []
    for line in lines[2:-1]:
        card = _load_json(line, "hint review card")
        if not isinstance(card, dict) or set(card) != STRICT_CARD_FIELDS:
            raise RuntimeError("strict hint review card fields are invalid")
        if line != json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ):
            raise RuntimeError("strict hint review card is not canonical JSON")
        if not isinstance(card["identity"], str) or not card["identity"]:
            raise RuntimeError("strict hint review card identity is invalid")
        cards.append(card)
    return metadata, cards


def _mechanical_fields(row: dict[str, object]) -> dict[str, object]:
    evidence_locations = list(row["producer_locations"])
    evidence_locations.extend([
        f"{HINTS_EN}:{row['english_key_line']}" if row["english_key_line"] else HINTS_EN,
        f"{HINTS_ZH}:{row['chinese_key_line']}" if row["chinese_key_line"] else HINTS_ZH,
    ])
    for value in row["consumer"].values():
        if isinstance(value, list):
            evidence_locations.extend(str(item) for item in value)
        elif value is not None:
            evidence_locations.append(str(value))
    return {
        "consumer": row["consumer"],
        "current_chinese": row["chinese"],
        "current_english": row["english"],
        "dependency_group": row["dependency_group"],
        "display_context": row["display_context"],
        "evidence_locations": evidence_locations,
        "fact_sha256": row["fact_sha256"],
        "identity": row["identity"],
        "lifecycle": row["lifecycle"],
        "producer": row["producer_calls"] or row["producer_locations"],
        "production_facts": row,
    }


def _typed_equal(left: object, right: object) -> bool:
    return json.dumps(
        left, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) == json.dumps(
        right, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _specific(value: object) -> bool:
    return (
        _nonempty(value)
        and str(value).strip().lower().strip(".。;；") not in _VAGUE_DEFERRAL_VALUES
    )


def review_coverage(
    payload: dict[str, object], review_input: AuditInput
) -> dict[str, object]:
    metadata, cards = parse_review(review_input)
    inventory = payload["inventory"]
    assert isinstance(inventory, list)
    inventory_ids = [row["identity"] for row in inventory]
    review_ids = [card["identity"] for card in cards]
    expected = {row["identity"]: row for row in inventory}
    mismatches: list[str] = []
    invalid: list[str] = []
    for card in cards:
        identity = card["identity"]
        if identity in expected:
            for field, value in _mechanical_fields(expected[identity]).items():
                if not _typed_equal(card[field], value):
                    mismatches.append(f"{identity}:{field}")
        conclusion = card["terminal_conclusion"]
        proposal = card["proposed_translation"]
        if conclusion not in TERMINAL_CONCLUSIONS:
            invalid.append(f"{identity}:terminal_conclusion")
        if conclusion in {"adjust", "retranslate"}:
            if not _nonempty(proposal) or proposal == card["current_chinese"]:
                invalid.append(f"{identity}:proposed_translation")
        elif proposal is not None:
            invalid.append(f"{identity}:unexpected_proposal")
        for field in (
            "actual_behavior", "glossary_authority", "reviewer_rationale",
            "reentry_trigger",
        ):
            if not _nonempty(card[field]):
                invalid.append(f"{identity}:{field}")
        if card["confidence"] not in CONFIDENCE_LEVELS:
            invalid.append(f"{identity}:confidence")
        if (
            not isinstance(card["rejected_alternatives"], list)
            or any(not _nonempty(value) for value in card["rejected_alternatives"])
        ):
            invalid.append(f"{identity}:rejected_alternatives")
        deferred = isinstance(conclusion, str) and conclusion.startswith("defer ")
        if deferred:
            for field in ("deferral_reason", "deferral_owner", "reentry_trigger"):
                if not _specific(card[field]):
                    invalid.append(f"{identity}:{field}")
        elif card["deferral_reason"] is not None or card["deferral_owner"] is not None:
            invalid.append(f"{identity}:unexpected_deferral_fields")

    binding = {
        "baseline": metadata["baseline"] == payload["baseline"],
        "glossary_sha256": metadata["glossary_sha256"] == payload["glossary_sha256"],
        "identity_count": metadata["identity_count"] == len(inventory),
        "inventory_sha256": metadata["inventory_sha256"] == payload["inventory_sha256"],
    }
    inventory_duplicates = sorted(
        key for key, count in Counter(inventory_ids).items() if count > 1
    )
    review_duplicates = sorted(
        key for key, count in Counter(review_ids).items() if count > 1
    )
    inventory_minus_review = sorted(set(inventory_ids) - set(review_ids))
    review_minus_inventory = sorted(set(review_ids) - set(inventory_ids))
    order_matches = review_ids == inventory_ids
    coverage_equal = (
        all(binding.values())
        and len(review_ids) == len(inventory_ids)
        and not inventory_duplicates
        and not review_duplicates
        and not inventory_minus_review
        and not review_minus_inventory
        and order_matches
        and not mismatches
        and not invalid
    )
    return {
        **review_input_metadata(review_input),
        "evidence_card_count": len(cards),
        "terminal_conclusion_counts": dict(sorted(Counter(
            card["terminal_conclusion"] for card in cards
            if isinstance(card["terminal_conclusion"], str)
        ).items())),
        "binding_matches": binding,
        "inventory_duplicate_identities": inventory_duplicates,
        "duplicate_evidence_cards": review_duplicates,
        "inventory_minus_review": inventory_minus_review,
        "review_minus_inventory": review_minus_inventory,
        "canonical_card_order": order_matches,
        "mismatched_mechanical_fields": sorted(mismatches),
        "invalid_cards": sorted(invalid),
        "coverage_equal": coverage_equal,
    }


def candidate_integrity(
    payload: dict[str, object], candidate_payload: dict[str, object]
) -> dict[str, object]:
    """Compare a completely rebuilt candidate artifact to the baseline.

    Text can legitimately change, so inventory/fact digests are reported but
    are not required to equal the baseline.  Identity, lifecycle, producers,
    glossary authority, complete union coverage, and zero blocking violations
    are the immutable candidate contract.
    """
    baseline_inventory = payload["inventory"]
    candidate_inventory = candidate_payload["inventory"]
    if not isinstance(baseline_inventory, list) or not isinstance(
        candidate_inventory, list
    ):
        raise RuntimeError("candidate integrity requires complete inventories")

    baseline_lifecycle = {
        row["key"]: row["lifecycle"] for row in baseline_inventory
    }
    candidate_lifecycle = {
        row["key"]: row["lifecycle"] for row in candidate_inventory
    }
    baseline_keys = set(payload["union_keys"])
    candidate_keys = set(candidate_payload["union_keys"])
    candidate_inventory_keys = [
        row["key"] for row in candidate_inventory
    ]
    baseline_producers = set(payload["producer_keys"])
    candidate_producers = set(candidate_payload["producer_keys"])
    lifecycle_mismatches = sorted(
        key for key in baseline_keys & candidate_keys
        if baseline_lifecycle.get(key) != candidate_lifecycle.get(key)
    )
    blocking = candidate_payload["blocking_violations"]
    if not isinstance(blocking, list):
        raise RuntimeError("candidate blocking violations are unavailable")

    matches = {
        "blocking_violations": not blocking,
        "candidate_commit": (
            isinstance(candidate_payload["baseline"], str)
            and bool(re.fullmatch(
                r"[0-9a-f]{40}", candidate_payload["baseline"]
            ))
        ),
        "glossary_sha256": (
            candidate_payload["glossary_sha256"] == payload["glossary_sha256"]
        ),
        "identity_set": candidate_keys == baseline_keys,
        "inventory_coverage": (
            not candidate_payload["inventory_minus_union"]
            and not candidate_payload["union_minus_inventory"]
            and candidate_inventory_keys == sorted(candidate_keys)
            and len(candidate_inventory_keys) == len(set(candidate_inventory_keys))
        ),
        "lifecycle": (
            candidate_lifecycle == baseline_lifecycle
            and not lifecycle_mismatches
        ),
        "producer_set": candidate_producers == baseline_producers,
    }
    return {
        "candidate": candidate_payload["baseline"],
        "candidate_inventory_sha256": candidate_payload["inventory_sha256"],
        "candidate_glossary_sha256": candidate_payload["glossary_sha256"],
        "candidate_blocking_violations": blocking,
        "baseline_minus_candidate_identities": sorted(
            baseline_keys - candidate_keys
        ),
        "candidate_minus_baseline_identities": sorted(
            candidate_keys - baseline_keys
        ),
        "baseline_minus_candidate_producers": sorted(
            baseline_producers - candidate_producers
        ),
        "candidate_minus_baseline_producers": sorted(
            candidate_producers - baseline_producers
        ),
        "lifecycle_mismatches": lifecycle_mismatches,
        "integrity_matches": matches,
        "integrity_equal": all(matches.values()),
    }


def candidate_agreement_from_payload(
    payload: dict[str, object],
    review_input: AuditInput,
    candidate_payload: dict[str, object],
) -> dict[str, object]:
    """Bind terminal cards to one fully rebuilt candidate inventory."""
    coverage = review_coverage(payload, review_input)
    integrity = candidate_integrity(payload, candidate_payload)
    _metadata, cards = parse_review(review_input)
    card_by_id = {card["identity"]: card for card in cards}
    inventory = payload["inventory"]
    candidate_inventory = candidate_payload["inventory"]
    assert isinstance(inventory, list)
    assert isinstance(candidate_inventory, list)
    candidate_by_key = {row["key"]: row for row in candidate_inventory}
    mismatches: list[str] = []
    for row in inventory:
        identity = row["identity"]
        card = card_by_id.get(identity)
        if card is None:
            mismatches.append(f"{identity}:missing_card")
            continue
        expected = (
            card["proposed_translation"]
            if card["terminal_conclusion"] in {"adjust", "retranslate"}
            else card["current_chinese"]
        )
        candidate_row = candidate_by_key.get(row["key"])
        actual = candidate_row["chinese"] if candidate_row else None
        if actual != expected:
            mismatches.append(str(identity))
    candidate_zh_keys = set(candidate_payload["hints_zh_keys"])
    inventory_keys = {row["key"] for row in inventory}
    return {
        "candidate": candidate_payload["baseline"],
        "candidate_integrity": integrity,
        "candidate_minus_inventory": sorted(
            candidate_zh_keys - inventory_keys
        ),
        "inventory_minus_candidate": sorted(
            inventory_keys - candidate_zh_keys
        ),
        "translation_mismatches": sorted(mismatches),
        "review_coverage_equal": coverage["coverage_equal"],
        "candidate_agrees": (
            coverage["coverage_equal"]
            and integrity["integrity_equal"]
            and candidate_zh_keys == inventory_keys
            and not mismatches
        ),
    }


def candidate_agreement(
    payload: dict[str, object], review_input: AuditInput, candidate: str
) -> dict[str, object]:
    """Rebuild the exact candidate Git tree before proving agreement."""
    candidate_payload = build_payload(candidate)
    return candidate_agreement_from_payload(
        payload, review_input, candidate_payload
    )


def _result_exit_code(payload: dict[str, object]) -> int:
    """Return the CLI status after baseline/candidate evidence is attached."""
    has_candidate = "candidate_agreement" in payload
    if payload["blocking_violations"] and not has_candidate:
        return 1
    if payload["inventory_minus_union"] or payload["union_minus_inventory"]:
        return 1
    if (
        "review_coverage" in payload
        and not payload["review_coverage"]["coverage_equal"]
    ):
        return 1
    if (
        has_candidate
        and not payload["candidate_agreement"]["candidate_agrees"]
    ):
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", default="HEAD")
    parser.add_argument(
        "--candidate-ref",
        help="optional exact candidate commit whose ZH Hints TextDB must "
             "agree with the terminal review cards",
    )
    parser.add_argument("--inventory-output", default="/tmp/hint-inventory.json")
    parser.add_argument("--review-results", type=Path)
    args = parser.parse_args()
    try:
        baseline = resolve_commit(args.baseline_ref)
        payload = build_payload(baseline)
        candidate = resolve_commit(args.candidate_ref) if args.candidate_ref else None
        if args.review_results:
            review_input = (
                load_git_review_input(candidate, args.review_results)
                if candidate else load_review_input(ROOT, args.review_results)
            )
            payload["review_input"] = review_input_metadata(review_input)
            payload["review_coverage"] = review_coverage(payload, review_input)
            if candidate:
                payload["candidate_agreement"] = candidate_agreement(
                    payload, review_input, candidate
                )
        elif candidate:
            raise RuntimeError("--candidate-ref requires --review-results")
        out = write_inventory_output(
            args.inventory_output,
            json.dumps(payload, ensure_ascii=False, indent=1),
        )
    except (OSError, RuntimeError, UnicodeError, ValueError) as error:
        print(f"ERROR: hint inventory failed: {error}", file=sys.stderr)
        return 2

    print(f"hint inventory sha256: {payload['inventory_sha256']}")
    print(f"producer identities: {len(payload['producer_keys'])}")
    print(
        "EN/ZH/union identities: "
        f"{len(payload['hints_en_keys'])}/"
        f"{len(payload['hints_zh_keys'])}/"
        f"{len(payload['union_keys'])}"
    )
    print(
        "EN/ZH differences: "
        f"{payload['en_minus_zh']} / {payload['zh_minus_en']}"
    )
    print(
        "producer/EN differences: "
        f"{payload['producer_minus_en']} / {payload['en_minus_producer']}"
    )
    print(
        "producer/ZH differences: "
        f"{payload['producer_minus_zh']} / {payload['zh_minus_producer']}"
    )
    print(f"blocking violations: {len(payload['blocking_violations'])}")
    print(
        "structural review candidates: "
        + json.dumps(payload["structural_review_candidates"], ensure_ascii=False)
    )
    if "review_coverage" in payload:
        print(
            "review coverage: "
            + json.dumps(
                payload["review_coverage"], ensure_ascii=False,
                sort_keys=True, separators=(",", ":")
            )
        )
    if "candidate_agreement" in payload:
        print(
            "candidate agreement: "
            + json.dumps(
                payload["candidate_agreement"], ensure_ascii=False,
                sort_keys=True, separators=(",", ":")
            )
        )
    print(f"wrote {out}")
    return _result_exit_code(payload)


if __name__ == "__main__":
    raise SystemExit(main())
