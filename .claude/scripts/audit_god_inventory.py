#!/usr/bin/env python3
"""Freeze the production god inventory and its translation-facing children.

God enum identities and English identity accessors are the parent authority.
TextDB files, titles, and code-side child enums are derived inputs; the script
does not use Wiki lists or a hand-maintained god-name table.
"""

import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "crawl-ref/source"
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from audit_item_name_inventory import (  # noqa: E402
    active_source,
    function_body,
    sha,
    source_entries,
    source_files,
    switch_literals,
)
from i18n_shared import (  # noqa: E402
    parse_entries_physical,
    runtime_normalize_value,
)


GOD_ENUM = SRC / "god-type.h"
RELIGION = SRC / "religion.cc"
OUCH = SRC / "ouch.cc"
DESCRIBE_GOD = SRC / "describe-god.cc"
GOD_PASSIVE = SRC / "god-passive.cc"
GOD_PASSIVE_HEADER = SRC / "god-passive.h"
GOD_CONDUCT = SRC / "god-conduct.cc"
CONDUCT_TYPE = SRC / "conduct-type.h"
GOD_WRATH = SRC / "god-wrath.cc"
ABILITY = SRC / "ability.cc"
ABILITY_TYPE = SRC / "ability-type.h"
EN_GODS = SRC / "dat/descript/gods.txt"
ZH_GODS = SRC / "dat/descript/zh/gods.txt"
EN_GODNAME = SRC / "dat/database/godname.txt"
ZH_GODNAME = SRC / "dat/database/zh/godname.txt"
EN_GODSPEAK = SRC / "dat/database/godspeak.txt"
ZH_GODSPEAK = SRC / "dat/database/zh/godspeak.txt"
EN_ABILITIES = SRC / "dat/descript/ability.txt"
ZH_ABILITIES = SRC / "dat/descript/zh/ability.txt"
ZH_SOURCE_DIR = SRC / "dat/i18n/zh"


def relative(path):
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def physical_entries(path):
    entries = parse_entries_physical(str(path))
    counts = Counter(entry.canonical_key for entry in entries)
    effective = {}
    for entry in entries:
        effective[entry.canonical_key] = runtime_normalize_value(entry.value)
    return effective, sorted(key for key, count in counts.items() if count > 1)


def god_enum_identities(path=GOD_ENUM):
    """Return concrete active god enum identities, excluding pseudo-gods."""
    text = active_source(path)
    match = re.search(r"\benum\s+god_type\s*\{(.*?)\bNUM_GODS\b", text, re.S)
    if not match:
        raise RuntimeError("active god_type enum ending at NUM_GODS was not found")
    identities = re.findall(r"^\s*(GOD_[A-Z0-9_]+)\s*,", match.group(1),
                            re.MULTILINE)
    identities = [identity for identity in identities
                  if identity != "GOD_NO_GOD"]
    if not identities:
        raise RuntimeError("no concrete god identities were parsed")
    return identities


def disabled_gods(text=None):
    body = function_body(
        active_source(RELIGION) if text is None else text,
        "_is_disabled_god",
    )
    return set(re.findall(r"\bcase\s+(GOD_[A-Z0-9_]+)\s*:", body))


def title_rows(path=DESCRIBE_GOD):
    """Parse the active divine_title table as ordered eight-slot rows."""
    text = active_source(path)
    match = re.search(
        r"\bdivine_title\s*\[\]\s*\[8\]\s*=\s*\{(.*?)\n\};", text, re.S
    )
    if not match:
        raise RuntimeError("divine_title[][8] initializer was not found")
    literals = re.findall(r'\bN_\(\s*"((?:[^"\\]|\\.)*)"\s*\)',
                          match.group(1))
    if len(literals) % 8:
        raise RuntimeError(
            f"divine_title contains {len(literals)} literals, not full rows"
        )
    return [literals[index:index + 8]
            for index in range(0, len(literals), 8)]


def _strip_cpp_comments(text):
    """Remove comments while retaining strings for balanced parsing."""
    result = []
    index = 0
    state = "code"
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if state == "code":
            if char == "/" and next_char == "/":
                state = "line_comment"
                result.extend("  ")
                index += 2
                continue
            if char == "/" and next_char == "*":
                state = "block_comment"
                result.extend("  ")
                index += 2
                continue
            if char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            result.append(char)
        elif state == "line_comment":
            result.append("\n" if char == "\n" else " ")
            if char == "\n":
                state = "code"
        elif state == "block_comment":
            if char == "*" and next_char == "/":
                result.extend("  ")
                index += 2
                state = "code"
                continue
            result.append("\n" if char == "\n" else " ")
        else:
            result.append(char)
            if char == "\\" and next_char:
                result.append(next_char)
                index += 2
                continue
            if (state == "string" and char == '"') or (
                state == "char" and char == "'"
            ):
                state = "code"
        index += 1
    if state in {"block_comment", "string", "char"}:
        raise RuntimeError(f"unterminated C++ lexical state: {state}")
    return "".join(result)


def _matching_brace(text, start):
    if start >= len(text) or text[start] != "{":
        raise ValueError("balanced initializer must start at an opening brace")
    depth = 0
    state = "code"
    index = start
    while index < len(text):
        char = text[index]
        if state == "code":
            if char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index
        else:
            if char == "\\":
                index += 1
            elif (state == "string" and char == '"') or (
                state == "char" and char == "'"
            ):
                state = "code"
        index += 1
    raise RuntimeError("unclosed balanced initializer")


def exact_function_body(text, declaration):
    match = re.search(
        declaration + r"\s*\([^;{}]*\)\s*\{", text, re.S
    )
    if not match:
        raise RuntimeError(f"function not found: {declaration}")
    start = text.find("{", match.start())
    return text[start + 1:_matching_brace(text, start)]


def ordered_initializer_rows(text, declaration):
    """Split one initializer into comma-delimited top-level enum rows."""
    clean = _strip_cpp_comments(text)
    match = re.search(declaration + r"\s*=\s*\{", clean, re.S)
    if not match:
        raise RuntimeError(f"initializer not found: {declaration}")
    start = clean.find("{", match.start())
    end = _matching_brace(clean, start)
    body = clean[start + 1:end]
    rows = []
    row_start = 0
    brace = paren = bracket = 0
    state = "code"
    index = 0
    while index < len(body):
        char = body[index]
        if state == "code":
            if char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            elif char == "{":
                brace += 1
            elif char == "}":
                brace -= 1
            elif char == "(":
                paren += 1
            elif char == ")":
                paren -= 1
            elif char == "[":
                bracket += 1
            elif char == "]":
                bracket -= 1
            elif char == "," and brace == paren == bracket == 0:
                row = body[row_start:index].strip()
                if row:
                    rows.append(row)
                row_start = index + 1
        else:
            if char == "\\":
                index += 1
            elif (state == "string" and char == '"') or (
                state == "char" and char == "'"
            ):
                state = "code"
        if min(brace, paren, bracket) < 0:
            raise RuntimeError(f"unbalanced row in initializer: {declaration}")
        index += 1
    tail = body[row_start:].strip()
    if tail:
        rows.append(tail)
    if brace or paren or bracket or state != "code":
        raise RuntimeError(f"unbalanced row in initializer: {declaration}")
    return rows


def declared_tokens(path, prefix):
    return set(re.findall(
        rf"\b{re.escape(prefix)}[A-Za-z0-9_]+\b", active_source(path)
    ))


def dynamic_ability_sources(parent_ids):
    body = exact_function_body(
        active_source(ABILITY),
        r"\bvector\s*<\s*ability_type\s*>\s+get_god_abilities",
    )
    known_abilities = declared_tokens(ABILITY_TYPE, "ABIL_")
    sources = {}
    pattern = re.compile(
        r"\bif\s*\(\s*you_worship\((GOD_[A-Z0-9_]+)\)", re.S
    )
    for match in pattern.finditer(body):
        identity = match.group(1)
        if identity not in parent_ids:
            continue
        opening = body.find("{", match.end())
        if opening < 0:
            raise RuntimeError(f"dynamic ability branch has no body: {identity}")
        branch = body[
            match.start():_matching_brace(body, opening) + 1
        ]
        tokens = sorted(set(re.findall(r"\bABIL_[A-Z0-9_]+\b", branch)))
        sources[identity] = {
            "ability_markers": tokens,
            "runtime_property_markers": sorted(set(
                re.findall(r"\b[A-Z][A-Z0-9_]*_KEY\b", branch)
            )),
            "unknown_ability_tokens": sorted(set(tokens) - known_abilities),
        }
    return sources


def ordered_child_tables():
    return {
        "abilities": ordered_initializer_rows(
            function_body(active_source(RELIGION), "get_all_god_powers"),
            r"\bgod_powers",
        ),
        "passives": ordered_initializer_rows(
            active_source(GOD_PASSIVE), r"\bgod_passives\s*\[\]"
        ),
        "disliked_conducts": ordered_initializer_rows(
            active_source(GOD_CONDUCT), r"\bdivine_peeves\s*\[\]"
        ),
        "liked_conducts": ordered_initializer_rows(
            active_source(GOD_CONDUCT), r"\bdivine_likes\s*\[\]"
        ),
    }


def weighted_topology(value, known_keys):
    """Mirror database.cc::_parse_weighted_entry for static topology."""
    lines = value.split("\n")
    variants = []
    index = 0
    while index < len(lines):
        while index < len(lines) and not lines[index]:
            index += 1
        if index == len(lines):
            break
        weight = 10
        match = re.match(r"w:([+-]?\d+)", lines[index])
        if match:
            weight = int(match.group(1))
            index += 1
            if index == len(lines):
                raise ValueError("weight marker at end of weighted entry")
        part = []
        while index < len(lines) and lines[index]:
            part.append(lines[index])
            index += 1
        pattern = "\n".join(part).strip()
        recursive = [
            token.lower()
            for token in re.findall(r"@([^@]+)@", pattern)
            if token.lower() in known_keys
        ]
        variants.append({
            "weight": weight,
            "recursive_references": recursive,
            "lua_site_count": len(re.findall(r"\{\{.*?\}\}", pattern, re.S)),
            "random_substring_option_counts": [
                len(raw.split("|")) for raw in re.findall(r"\[([^\]]*)\]", pattern)
            ],
        })
    if not variants:
        raise ValueError("empty weighted entry")
    total = 0
    bounds = []
    for variant in variants:
        total += variant["weight"]
        bounds.append(total)
    return {
        "variant_count": len(variants),
        "weights": [variant["weight"] for variant in variants],
        "selection_bounds": bounds,
        "random_bound": total,
        "variants": variants,
    }


def godspeak_topology_drift(en_entries, zh_entries):
    known = set(en_entries) | set(zh_entries)
    result = []
    for key in sorted(set(en_entries) & set(zh_entries)):
        canonical = weighted_topology(en_entries[key], known)
        localized = weighted_topology(zh_entries[key], known)
        if canonical != localized:
            result.append({
                "key": key,
                "canonical": canonical,
                "localized": localized,
            })
    return result


def child_summary():
    power_body = function_body(active_source(RELIGION), "get_all_god_powers")
    passive_text = active_source(GOD_PASSIVE)
    conduct_text = active_source(GOD_CONDUCT)
    wrath_text = active_source(GOD_WRATH)
    return {
        "abilities": sorted(set(re.findall(r"\bABIL_[A-Z0-9_]+\b", power_body))),
        "passives": sorted(set(
            re.findall(r"\bpassive_t::([a-z0-9_]+)\b", passive_text)
        ) - {"none"}),
        "conducts": sorted(set(re.findall(r"\bDID_[A-Z0-9_]+\b", conduct_text))),
        "wrath_gods": sorted(set(re.findall(r"\bGOD_[A-Z0-9_]+\b", wrath_text))),
    }


def _parent_for_key(key, english_names):
    matches = [
        identity for identity, name in english_names.items()
        if key == name.lower() or key.startswith(name.lower() + " ")
    ]
    return max(matches, key=lambda identity: len(english_names[identity]),
               default=None)


def inventory_violations(
    parents,
    expected_identities,
    name_en,
    name_display,
    disabled,
    database_state,
    titles,
    death_lookup_safe,
    child_tables=None,
    unknown_child_tokens=None,
):
    identities = [row["identity"] for row in parents]
    actual = set(identities)
    expected = set(expected_identities)
    english_names = {
        identity: row["english_name"]
        for identity, row in ((row["identity"], row) for row in parents)
        if row.get("english_name")
    }
    expected_desc = {
        suffix
        for name in english_names.values()
        for suffix in (
            name.lower(), name.lower() + " powers", name.lower() + " wrath"
        )
    }
    expected_desc.update(
        key for key in database_state["english_gods"]
        if key.endswith(" extra") and _parent_for_key(key, english_names)
    )
    valid_lastnames = {
        name.lower() + " lastname" for name in english_names.values()
    }
    title_count = len(expected) + 1  # row zero is GOD_NO_GOD
    return {
        "duplicate_parent_identities": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "missing_parent_identities": sorted(expected - actual),
        "unexpected_parent_identities": sorted(actual - expected),
        "missing_english_identity_names": sorted(expected - set(name_en)),
        "unexpected_english_identity_names": sorted(set(name_en) - expected),
        "missing_display_names": sorted(expected - set(name_display)),
        "unexpected_display_names": [],
        "english_display_name_mismatches": sorted(
            identity for identity in expected & set(name_en) & set(name_display)
            if name_en[identity]["en"] != name_display[identity]["en"]
        ),
        "missing_current_chinese_names": sorted(
            row["identity"] for row in parents
            if not row.get("current_chinese_name")
        ),
        "missing_current_chinese_titles": sorted(
            f"{row['identity']}:{slot}"
            for row in parents
            for slot, title in enumerate(row.get("current_chinese_titles", []))
            if not title
        ) + sorted(
            f"{row['identity']}:{slot}"
            for row in parents
            for slot in range(
                len(row.get("current_chinese_titles", [])), 8
            )
        ),
        "unexpected_disabled_gods": sorted(disabled - expected),
        "duplicate_textdb_keys": {
            name: values for name, values in database_state["duplicates"].items()
            if values
        },
        "god_description_locale_key_mismatch": sorted(
            set(database_state["english_gods"])
            ^ set(database_state["chinese_gods"])
        ),
        "missing_god_description_keys": sorted(
            expected_desc - set(database_state["english_gods"])
        ),
        "unexpected_god_description_keys": sorted(
            set(database_state["english_gods"]) - expected_desc
        ),
        "godname_locale_key_mismatch": sorted(
            set(database_state["english_godname"])
            ^ set(database_state["chinese_godname"])
        ),
        "invalid_godname_keys": sorted(
            set(database_state["english_godname"]) - valid_lastnames
        ),
        "godspeak_locale_key_mismatch": sorted(
            set(database_state["english_godspeak"])
            ^ set(database_state["chinese_godspeak"])
        ),
        "title_row_count_mismatch": (
            {"expected": title_count, "actual": len(titles)}
            if len(titles) != title_count else {}
        ),
        "title_slot_count_mismatches": [
            {"row": index, "actual": len(row), "expected": 8}
            for index, row in enumerate(titles) if len(row) != 8
        ],
        "death_lookup_uses_display_name": [] if death_lookup_safe else [
            "ouch.cc:_god_death_messages"
        ],
        "child_row_count_mismatches": {
            name: {"expected": len(expected) + 1, "actual": len(rows)}
            for name, rows in sorted((child_tables or {}).items())
            if len(rows) != len(expected) + 1
        },
        "unknown_child_tokens": {
            name: sorted(tokens)
            for name, tokens in sorted((unknown_child_tokens or {}).items())
            if tokens
        },
    }


def build_inventory():
    enum_ids = god_enum_identities()
    religion_text = active_source(RELIGION)
    name_en = switch_literals(religion_text, "_god_name_en")
    name_display = switch_literals(religion_text, "god_name")
    disabled = disabled_gods(religion_text)
    zh_source = source_entries(ZH_SOURCE_DIR)

    database_paths = {
        "english_gods": EN_GODS,
        "chinese_gods": ZH_GODS,
        "english_godname": EN_GODNAME,
        "chinese_godname": ZH_GODNAME,
        "english_godspeak": EN_GODSPEAK,
        "chinese_godspeak": ZH_GODSPEAK,
        "english_abilities": EN_ABILITIES,
        "chinese_abilities": ZH_ABILITIES,
    }
    database_state = {"duplicates": {}}
    for name, path in database_paths.items():
        values, duplicates = physical_entries(path)
        database_state[name] = values
        database_state["duplicates"][name] = duplicates

    titles = title_rows()
    child_tables = ordered_child_tables()
    parent_order = ["GOD_NO_GOD", *enum_ids]
    known_abilities = declared_tokens(ABILITY_TYPE, "ABIL_")
    passive_header = _strip_cpp_comments(active_source(GOD_PASSIVE_HEADER))
    passive_enum = re.search(
        r"\benum\s+class\s+passive_t\s*\{(.*?)\};", passive_header, re.S
    )
    if not passive_enum:
        raise RuntimeError("passive_t enum was not found")
    known_passives = set(re.findall(
        r"^\s*([a-z][a-z0-9_]*)\s*(?:=[^,]+)?\s*,",
        passive_enum.group(1),
        re.MULTILINE,
    ))
    known_conducts = declared_tokens(CONDUCT_TYPE, "DID_")
    dynamic_sources = dynamic_ability_sources(set(enum_ids))
    child_tokens = {
        "abilities": [
            sorted(set(re.findall(r"\bABIL_[A-Z0-9_]+\b", row)))
            for row in child_tables["abilities"]
        ],
        "passives": [
            sorted(set(re.findall(r"\bpassive_t::([a-z0-9_]+)\b", row)))
            for row in child_tables["passives"]
        ],
        "disliked_conducts": [
            sorted(set(re.findall(r"\bDID_[A-Z0-9_]+\b", row)))
            for row in child_tables["disliked_conducts"]
        ],
        "liked_conducts": [
            sorted(set(re.findall(r"\bDID_[A-Z0-9_]+\b", row)))
            for row in child_tables["liked_conducts"]
        ],
    }
    unknown_child_tokens = {
        "abilities": {
            token for row in child_tokens["abilities"] for token in row
        } - known_abilities,
        "passives": {
            token for row in child_tokens["passives"] for token in row
        } - known_passives,
        "disliked_conducts": {
            token for row in child_tokens["disliked_conducts"] for token in row
        } - known_conducts,
        "liked_conducts": {
            token for row in child_tokens["liked_conducts"] for token in row
        } - known_conducts,
        "dynamic_abilities": {
            token
            for source in dynamic_sources.values()
            for token in source["unknown_ability_tokens"]
        },
    }
    parents = []
    for index, identity in enumerate(enum_ids, start=1):
        en = name_en.get(identity, {}).get("en")
        display_key = name_display.get(identity, {}).get("key")
        english_titles = titles[index] if index < len(titles) else []
        chinese_titles = [
            zh_source.get(f"god title|{title}".lower())
            or zh_source.get(title.lower())
            for title in english_titles
        ]
        parent = {
            "identity": identity,
            "lifecycle": (
                "compatibility_disabled" if identity in disabled
                else "current"
            ),
            "english_name": en,
            "display_lookup_key": display_key,
            "current_chinese_name": (
                zh_source.get(display_key.lower()) if display_key else None
            ),
            "description_keys": sorted(
                key for key in database_state["english_gods"]
                if en and (key == en.lower() or key.startswith(en.lower() + " "))
            ),
            "longname_keys": sorted(
                key for key in database_state["english_godname"]
                if en and key == en.lower() + " lastname"
            ),
            "godspeak_keys": sorted(
                key for key in database_state["english_godspeak"]
                if en and (key == en.lower() or key.startswith(en.lower() + " "))
            ),
            "title_slots": english_titles,
            "current_chinese_titles": chinese_titles,
            "ability_ids": (
                child_tokens["abilities"][index]
                if index < len(child_tokens["abilities"]) else []
            ),
            "passive_ids": (
                child_tokens["passives"][index]
                if index < len(child_tokens["passives"]) else []
            ),
            "disliked_conduct_ids": (
                child_tokens["disliked_conducts"][index]
                if index < len(child_tokens["disliked_conducts"]) else []
            ),
            "liked_conduct_ids": (
                child_tokens["liked_conducts"][index]
                if index < len(child_tokens["liked_conducts"]) else []
            ),
            "dynamic_ability_source": dynamic_sources.get(identity),
            "wrath_key": en.lower() + " wrath" if en else None,
        }
        parents.append(parent)

    ouch_body = function_body(active_source(OUCH), "_god_death_messages")
    death_lookup_safe = (
        "_god_name_en(you.religion)" in ouch_body
        and "god_name(you.religion)" not in ouch_body
    )
    violations = inventory_violations(
        parents,
        enum_ids,
        name_en,
        name_display,
        disabled,
        database_state,
        titles,
        death_lookup_safe,
        child_tables,
        unknown_child_tokens,
    )
    topology_drift = godspeak_topology_drift(
        database_state["english_godspeak"],
        database_state["chinese_godspeak"],
    )
    zh_only_abilities = sorted(
        set(database_state["chinese_abilities"])
        - set(database_state["english_abilities"])
    )
    children = child_summary()
    children.update({
        "description_keys": sorted(database_state["english_gods"]),
        "longname_keys": sorted(database_state["english_godname"]),
        "godspeak_keys": sorted(database_state["english_godspeak"]),
        "title_slots": [
            f"{identity}:{slot}"
            for identity in ["GOD_NO_GOD", *enum_ids]
            for slot in range(8)
        ],
    })

    inputs = [
        GOD_ENUM, RELIGION, OUCH, DESCRIBE_GOD, GOD_PASSIVE,
        GOD_PASSIVE_HEADER, GOD_CONDUCT, CONDUCT_TYPE, GOD_WRATH,
        ABILITY, ABILITY_TYPE, *database_paths.values(),
        *source_files(ZH_SOURCE_DIR),
        ROOT / "docs/glossary.md",
    ]
    payload = {
        "schema": "dcss-god-review-inventory-v1",
        "baseline": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "glossary_sha256": sha(ROOT / "docs/glossary.md"),
        "input_sha256": {
            relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in inputs
        },
        "scope": {
            "included": [
                "active god enum parents through NUM_GODS",
                "TAG compatibility and disabled god parents",
                "canonical English and localized short-name producers",
                "god description, longname, godspeak and title identities",
                "code-side ability, passive, conduct and wrath identity summaries",
            ],
            "excluded": [
                "Wiki-derived god lists",
                "strategy, balance and gameplay-mechanics review",
                "independent wording conclusions for abilities and passives",
                "protocol keys outside god display sinks",
            ],
        },
        "count": len(parents),
        "lifecycle_counts": {
            lifecycle: sum(row["lifecycle"] == lifecycle for row in parents)
            for lifecycle in sorted({row["lifecycle"] for row in parents})
        },
        "textdb_counts": {
            "god_descriptions": len(database_state["english_gods"]),
            "god_longnames": len(database_state["english_godname"]),
            "godspeak": len(database_state["english_godspeak"]),
        },
        "child_counts": {
            name: len(values) for name, values in children.items()
        },
        "review_findings": {
            "zh_only_ability_keys": zh_only_abilities,
            "godspeak_topology_drift": topology_drift,
        },
        **violations,
        "children": children,
        "parents": parents,
    }
    encoded = json.dumps(
        {"parents": parents, "children": children},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    payload["inventory_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def has_violations(payload):
    ignored = {
        "schema", "baseline", "glossary_sha256", "input_sha256", "scope",
        "count", "lifecycle_counts", "textdb_counts", "child_counts",
        "review_findings", "children", "parents", "inventory_sha256",
        "review_coverage",
    }
    return any(value for key, value in payload.items() if key not in ignored)


def review_coverage(payload, path):
    """Prove one non-empty terminal conclusion per frozen god parent."""
    text = path.read_text(encoding="utf-8")
    rows = re.findall(
        r"^\|\s*`(GOD_[A-Z0-9_]+)`\s*\|.*?\|\s*([^|\n]+?)\s*\|\s*$",
        text,
        re.MULTILINE,
    )
    identities = [identity for identity, _conclusion in rows]
    conclusions = {identity: conclusion.strip() for identity, conclusion in rows}
    expected = {row["identity"] for row in payload["parents"]}
    actual = set(identities)
    return {
        "review_results": relative(path),
        "review_results_sha256": sha(path),
        "evidence_card_count": len(identities),
        "duplicate_evidence_cards": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "missing_evidence_cards": sorted(expected - actual),
        "unexpected_evidence_cards": sorted(actual - expected),
        "missing_terminal_conclusions": sorted(
            identity for identity in actual if not conclusions.get(identity)
        ),
        "coverage_equal": (
            len(identities) == len(expected)
            and actual == expected
            and all(conclusions.values())
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-results", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = build_inventory()
        if args.review_results:
            payload["review_coverage"] = review_coverage(
                payload, args.review_results
            )
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(f"ERROR: god inventory could not be built: {error}",
              file=sys.stderr)
        return 2
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    summary = {
        key: payload[key] for key in (
            "baseline", "glossary_sha256", "inventory_sha256", "count",
            "lifecycle_counts", "textdb_counts", "child_counts",
        )
    }
    summary["review_finding_counts"] = {
        key: len(value) for key, value in payload["review_findings"].items()
    }
    summary["godspeak_topology_drift_keys"] = [
        row["key"]
        for row in payload["review_findings"]["godspeak_topology_drift"]
    ]
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    coverage_failed = (
        "review_coverage" in payload
        and not payload["review_coverage"]["coverage_equal"]
    )
    return 1 if has_violations(payload) or coverage_failed else 0


if __name__ == "__main__":
    sys.exit(main())
