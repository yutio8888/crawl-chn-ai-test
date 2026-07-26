#!/usr/bin/env python3
"""Build the production world-text review inventory.

The inventory is intentionally derived from the active C++ enums/tables and a
single sorted walk of production .des files.  It is a read-only audit: known
translation gaps are violations, not reasons to omit rows.
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

from audit_god_inventory import ordered_initializer_rows  # noqa: E402
from audit_item_name_inventory import (  # noqa: E402
    active_source,
    function_body,
    sha,
    source_entries,
    source_files,
    tag_major_version,
)
from i18n_extract import _lua_tokens, cpp_unescape  # noqa: E402
from i18n_shared import (  # noqa: E402
    i18n_escape_key,
    lowercase_string,
    parse_entries_physical,
    runtime_normalize_value,
)


BRANCH_ENUM = SRC / "branch-type.h"
BRANCH_DATA = SRC / "branch-data.h"
BRANCH_CC = SRC / "branch.cc"
FEATURE_ENUM = SRC / "dungeon-feature-type.h"
FEATURE_DATA = SRC / "feature-data.h"
EN_BRANCHES = SRC / "dat/descript/branches.txt"
ZH_BRANCHES = SRC / "dat/descript/zh/branches.txt"
EN_FEATURES = SRC / "dat/descript/features.txt"
ZH_FEATURES = SRC / "dat/descript/zh/features.txt"
DES_ROOT = SRC / "dat/des"
ZH_SOURCE_DIR = SRC / "dat/i18n/zh"
GLOSSARY = ROOT / "docs/glossary.md"

DIRECT_SINKS = {"mpr", "formatted_mpr", "yesno", "take_note", "god_speaks"}
FINITE_TITLE_PRODUCERS = {
    "trove_milestone": {
        "sink_kind": "trove_milestone_title",
        "consumer": "trove_milestone:crawl.mpr",
    },
    "wizlab_milestone": {
        "sink_kind": "wizlab_milestone_title",
        "consumer": "wizlab_milestone:crawl.mpr",
    },
}
TIMED_FIELDS = {
    "initmsg", "finalmsg", "range_msg_fmt", "ranges", "messages", "verb",
    "noisemaker", "disappear", "entity", "desc",
}
INTERNAL_FEATURES = {
    "DNGN_UNSEEN": "internal_sentinel",
    "DNGN_EXPLORE_HORIZON": "internal_overlay",
    "DNGN_TRAVEL_TRAIL": "internal_overlay",
    "DNGN_DECORATIVE_FLOOR": "dummy_redefinition",
}
DISPLAY_ASSIGNMENTS = TIMED_FIELDS | {"toll_desc"}
PROTOCOL_ASSIGNMENTS = {
    "NAME", "TAGS", "KFEAT", "MARKER", "replica_name", "feature",
    "vaultname",
}
CRAWL_API_CLASSIFICATIONS = {
    "included_player_display": {
        "formatted_mpr", "god_speaks", "mpr", "take_note", "yesno",
    },
    "display_translation_helper": {
        "grammar", "t_",
    },
    "persistent_protocol": {
        "mark_game_won", "mark_milestone",
    },
    "diagnostic": {
        "dpr",
    },
    "ui_control": {
        "more", "redraw_view", "tutorial_msg",
    },
    "gameplay_state_or_lookup": {
        "game_started", "make_name", "set_max_runes", "split_bytes",
    },
    "randomness": {
        "coinflip", "div_rand_round", "one_chance_in", "random2",
        "random2avg", "random_range", "random_real", "rng_wrap", "roll_dice",
        "x_chance_in_y",
    },
}
CONSTRUCTOR_CLASSIFICATIONS = {
    "timed_msg": "included_display_marker",
    "timed_marker": "included_display_marker",
    "portal_desc": "included_display_marker",
    "trove_marker": "included_display_marker",
    "tutorial_msg": "excluded_lookup_protocol_owned",
    "tutorial_hint": "excluded_lookup_protocol_owned",
    "get_marker": "excluded_lookup_protocol_owned",
    "lua_marker": "excluded_lookup_protocol_owned",
    "props_marker": "excluded_lookup_protocol_owned",
}
REVIEW_COLUMNS = [
    "identity",
    # Existing evidence-card fields retained for compatibility.
    "producer_consumer",
    "trigger_context",
    "persistence_protocol",
    "en",
    "zh",
    "mechanics_tokens",
    # Plan-required independently reviewable fields.
    "lifecycle",
    "display_context",
    "producer",
    "consumers_users",
    "mechanics_behavior",
    "target_scope_conditions_exceptions_consequences",
    "trigger_timing",
    "persistence_serialization",
    "late_translation_sink",
    "format_entity_markup_structure_tokens",
    "glossary_decision_authority",
    "shared_dependency_group",
    "evidence_locations",
    "proposed_translation",
    "adopted_translation",
    "rejected_alternatives",
    "confidence",
    "deferred_follow_up",
    "re_entry_conditions",
    "conclusion",
]
REVIEW_DECISION_FIELDS = {
    "proposed_translation",
    "adopted_translation",
    "rejected_alternatives",
    "confidence",
    "deferred_follow_up",
    "re_entry_conditions",
}
PENDING_REVIEW = "pending review"


def relative(path):
    path = Path(path).resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def physical_db(path):
    entries = parse_entries_physical(str(path))
    counts = Counter(entry.canonical_key for entry in entries)
    effective = {}
    raw = {}
    for entry in entries:
        effective[entry.canonical_key] = runtime_normalize_value(entry.value)
        raw[entry.raw_key] = runtime_normalize_value(entry.value)
    # TextDB accepts an entry before the first separator. The shared physical
    # parser intentionally exposes separator-delimited entries, so recover
    # that production-visible leading entry after any comment banner.
    prefix = Path(path).read_text(encoding="utf-8").split("%%%%", 1)[0]
    prefix_lines = prefix.splitlines()
    first_key = next((
        index for index, line in enumerate(prefix_lines)
        if line.strip() and not line.lstrip().startswith("#")
    ), None)
    if first_key is not None:
        raw_key = prefix_lines[first_key].strip()
        value = "\n".join(prefix_lines[first_key + 1:]).strip()
        canonical_key = lowercase_string(raw_key)
        if raw_key not in raw:
            counts[canonical_key] += 1
            effective[canonical_key] = runtime_normalize_value(value)
            raw[raw_key] = runtime_normalize_value(value)
    return {
        "effective": effective,
        "raw": raw,
        "duplicates": sorted(key for key, count in counts.items() if count > 1),
    }


def _enum_body(path, enum_name, terminator):
    text = active_source(path)
    match = re.search(
        rf"\benum\s+{re.escape(enum_name)}[^{{]*\{{(.*?)"
        rf"\b{re.escape(terminator)}\b",
        text,
        re.S,
    )
    if not match:
        raise RuntimeError(f"{enum_name} ending at {terminator} was not found")
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", match.group(1), flags=re.S)


def enum_identities(path, enum_name, prefix, terminator):
    """Parse concrete enum identities, values, and aliases after TAG pruning."""
    body = _enum_body(path, enum_name, terminator)
    values = {}
    concrete = []
    aliases = []
    next_value = 0
    for part in body.split(","):
        declaration = part.strip()
        if not declaration:
            continue
        match = re.fullmatch(
            rf"({re.escape(prefix)}[A-Z0-9_]+)"
            r"(?:\s*=\s*([A-Z0-9_]+|[-+]?\d+))?",
            declaration,
        )
        if not match:
            raise RuntimeError(f"unsupported enum declaration: {declaration}")
        identity, expression = match.groups()
        alias_of = None
        if expression is None:
            value = next_value
        elif re.fullmatch(r"[-+]?\d+", expression):
            value = int(expression)
        elif expression in values:
            value = values[expression]
            alias_of = expression
        else:
            raise RuntimeError(
                f"unresolved enum expression for {identity}: {expression}"
            )
        values[identity] = value
        next_value = value + 1
        record = {"identity": identity, "value": value}
        if alias_of:
            record["alias_of"] = alias_of
            aliases.append(record)
        else:
            concrete.append(record)
    if not concrete:
        raise RuntimeError(f"no concrete {prefix} identities parsed")
    return concrete, aliases


def _cpp_literals(text):
    return [
        cpp_unescape(raw)
        for raw in re.findall(r'"((?:[^"\\]|\\.)*)"', text)
    ]


def _split_cpp_fields(row):
    fields = []
    start = 1 if row.lstrip().startswith("{") else 0
    text = row.lstrip()
    depth = 0
    state = "code"
    field_start = start
    for index in range(start, len(text)):
        char = text[index]
        if state == "code":
            if char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            elif char in "({[":
                depth += 1
            elif char in ")}]":
                depth -= 1
            elif char == "," and depth == 0:
                fields.append(text[field_start:index].strip())
                field_start = index + 1
        elif char == "\\":
            state = "escape"
        elif (state == "string" and char == '"') or (
                state == "char" and char == "'"):
            state = "code"
        elif state == "escape":
            state = "string"
    tail = text[field_start:].strip().rstrip("}").strip()
    if tail:
        fields.append(tail)
    return fields


def branch_rows():
    enum_rows, aliases = enum_identities(
        BRANCH_ENUM, "branch_type", "BRANCH_", "NUM_BRANCHES"
    )
    initializers = ordered_initializer_rows(
        active_source(BRANCH_DATA), r"\bbranches\s*\[\s*NUM_BRANCHES\s*\]"
    )
    data = []
    for raw in initializers:
        fields = _split_cpp_fields(raw)
        identity_match = re.match(r"\{\s*(BRANCH_[A-Z0-9_]+)\s*,", raw)
        literals = _cpp_literals(raw)
        if not identity_match or len(literals) < 3:
            raise RuntimeError(f"unparsed branch initializer: {raw[:100]}")
        entry_match = re.search(
            r'"(?:[^"\\]|\\.)*"\s*,\s*"(?:[^"\\]|\\.)*"\s*,\s*'
            r'"(?:[^"\\]|\\.)*"\s*,\s*'
            r'((?:"(?:[^"\\]|\\.)*"\s*)+|nullptr)\s*,',
            raw,
            re.S,
        )
        entry_message = None
        if entry_match and entry_match.group(1).strip() != "nullptr":
            entry_message = "".join(_cpp_literals(entry_match.group(1)))
        data.append({
            "identity": identity_match.group(1),
            "shortname": literals[0],
            "longname": literals[1],
            "abbrevname": literals[2],
            "entry_message": entry_message,
            "mechanics": {
                "parent": fields[1],
                "mindepth": fields[2],
                "maxdepth": fields[3],
                "numlevels": fields[4],
                "absdepth": fields[5],
                "flags": fields[6],
                "entry_feature": fields[7],
                "exit_feature": fields[8],
                "escape_feature": fields[9],
                "runes": fields[17],
                "noise": fields[18],
                "descent_parents": fields[20],
            },
            "raw_producer": raw,
        })

    unfinished_body = function_body(active_source(BRANCH_CC),
                                    "branch_is_unfinished")
    unfinished = set(re.findall(r"\bBRANCH_[A-Z0-9_]+\b", unfinished_body))
    source = source_entries(ZH_SOURCE_DIR)
    en_desc = physical_db(EN_BRANCHES)
    zh_desc = physical_db(ZH_BRANCHES)
    rows = []
    for item in data:
        identity = item["identity"]
        keys = [
            ("shortname", item["shortname"]),
            ("longname", item["longname"]),
            ("entry_message", item["entry_message"]),
        ]
        display = []
        for field, key in keys:
            if key:
                display.append({
                    "field": field,
                    "en": key,
                    "zh": source.get(lowercase_string(i18n_escape_key(key))),
                    "source_exact": (
                        lowercase_string(i18n_escape_key(key)) in source
                    ),
                })
        desc_key = item["shortname"]
        rows.append({
            "identity": f"branch:{identity}",
            "category": "branch",
            "enum_identity": identity,
            "lifecycle": (
                "compatibility_unfinished" if identity in unfinished else "current"
            ),
            **{key: item[key] for key in (
                "shortname", "longname", "abbrevname", "entry_message"
            )},
            "display_strings": display,
            "lookup_identity": {
                "abbrevname": item["abbrevname"],
                "translation_owner": False,
            },
            "shortname_paths": {
                "english_lookup_textdb_key": item["shortname"],
                "display_sink": "branch display consumers translate with T_",
                "required_consumer_refs": [
                    "branch.cc:branch_by_shortname",
                    "describe.cc/lookup-help.cc display sinks",
                ],
            },
            "mechanics": item["mechanics"],
            "raw_producer": item["raw_producer"],
            "english_description": en_desc["raw"].get(desc_key),
            "chinese_description": zh_desc["raw"].get(desc_key),
            "evidence": {
                "enum": relative(BRANCH_ENUM),
                "initializer": relative(BRANCH_DATA),
                "lifecycle_producer": relative(BRANCH_CC),
            },
        })
    proof = {
        "enum_order": [row["identity"] for row in enum_rows],
        "data_order": [row["identity"] for row in data],
        "aliases": aliases,
        "unfinished_from_producer": sorted(unfinished),
    }
    return rows, proof, en_desc, zh_desc


def feature_rows():
    enum_rows, aliases = enum_identities(
        FEATURE_ENUM, "dungeon_feature_type", "DNGN_", "NUM_FEATURES"
    )
    text = active_source(FEATURE_DATA)
    parsed = []
    # Concrete brace rows and macro invocations share the same first three
    # semantic arguments. Macro definitions use the token `enum`, so they
    # cannot satisfy this production-identity pattern.
    pattern = re.compile(
        r"\b(DNGN_[A-Z0-9_]+)\s*,\s*"
        r'"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"',
        re.S,
    )
    for match in pattern.finditer(text):
        identity, name, vaultname = match.groups()
        parsed.append((match.start(), {
            "identity": identity,
            "name": cpp_unescape(name),
            "vaultname": cpp_unescape(vaultname),
        }))
    for match in re.finditer(
        r"\bSTONE_STAIRS_(DOWN|UP)\s*\(\s*([A-Z]+)\s*,\s*([a-z]+)\s*\)",
        text,
    ):
        direction, numeral, vault_numeral = match.groups()
        parsed.append((match.start(), {
            "identity": f"DNGN_STONE_STAIRS_{direction}_{numeral}",
            "name": f"stone staircase leading {direction.lower()}",
            "vaultname": f"stone_stairs_{direction.lower()}_{vault_numeral}",
        }))
    data = [row for _offset, row in sorted(parsed)]
    macro_behavior = {}
    for match in re.finditer(
        r"#define\s+([A-Z_]+)\([^)]*\)\\\n((?:.*\\\n)+.*)",
        text,
    ):
        flags = re.findall(r"\bFFT_[A-Z0-9_| ]+", match.group(2))
        minimap = re.findall(r"\bMF_[A-Z0-9_]+", match.group(2))
        if flags and minimap:
            macro_behavior[match.group(1)] = (
                flags[-1].strip(), minimap[-1]
            )
    for item in data:
        identity = item["identity"]
        stone = re.fullmatch(
            r"DNGN_STONE_STAIRS_(DOWN|UP)_([A-Z]+)", identity
        )
        if stone:
            macro_name = "STONE_STAIRS_" + stone.group(1)
            invocation = re.search(
                rf"(?m)^\s*{macro_name}\(\s*{stone.group(2)}\s*,.*$",
                text,
            )
            item["flags"], item["minimap"] = macro_behavior[macro_name]
            item["raw_producer"] = invocation.group(0).strip()
            continue
        hit = re.search(
            rf"(?m)^.*\b{re.escape(identity)}\b.*(?:\n(?:.*\\\n)*)?", text
        )
        raw = hit.group(0).strip() if hit else identity
        line_start = text.rfind("\n", 0, hit.start()) + 1 if hit else 0
        line_end = text.find("\n", hit.start()) if hit else 0
        producer_line = text[line_start:line_end]
        macro = re.match(r"\s*([A-Z_]+)\s*\(", producer_line)
        behavior = macro_behavior.get(macro.group(1)) if macro else None
        if not behavior:
            tail = text[hit.start():hit.start() + 500] if hit else ""
            flags = re.search(
                r"\(?\s*\b(FFT_[A-Z0-9_| ]+?)\s*\)?\s*,\s*"
                r"(MF_[A-Z0-9_]+)",
                tail,
            )
            behavior = flags.groups() if flags else (None, None)
        item["flags"], item["minimap"] = behavior
        item["raw_producer"] = raw
    source = source_entries(ZH_SOURCE_DIR)
    en_desc = physical_db(EN_FEATURES)
    zh_desc = physical_db(ZH_FEATURES)
    en_desc_keys = {key.lower(): key for key in en_desc["raw"]}
    zh_desc_keys = {key.lower(): key for key in zh_desc["raw"]}

    def description_value(db, keys, feature_name):
        for candidate in (
                feature_name,
                f"A {feature_name}",
                f"An {feature_name}",
                f"The {feature_name}"):
            matched = keys.get(candidate.lower())
            if matched is not None:
                return db["raw"].get(matched)
        return None

    alias_names = {}
    alias_vaultnames = {}
    for item in data:
        alias_names.setdefault(item["name"], []).append(item["identity"])
        alias_vaultnames.setdefault(item["vaultname"], []).append(item["identity"])
    rows = []
    for item in data:
        identity = item["identity"]
        name = item["name"]
        rows.append({
            "identity": f"feature:{identity}",
            "category": "feature",
            "enum_identity": identity,
            "lifecycle": INTERNAL_FEATURES.get(identity, "current"),
            "name": name,
            "vaultname": item["vaultname"],
            "current_chinese_name": source.get(name.lower()) if name else None,
            "english_description": description_value(
                en_desc, en_desc_keys, name
            ),
            "chinese_description": description_value(
                zh_desc, zh_desc_keys, name
            ),
            "name_alias_group": alias_names[name],
            "vaultname_alias_group": alias_vaultnames[item["vaultname"]],
            "protocol_identity": {
                "vaultname": item["vaultname"],
                "translation_owner": False,
                "display_value": item["name"],
                "required_consumer_refs": [
                    "feature.cc:get_feature_def",
                    "mapdef KFEAT/& lookup consumers",
                    "terrain.cc/describe.cc display consumers",
                ],
            },
            "flags": item["flags"],
            "minimap": item["minimap"],
            "raw_producer": item["raw_producer"],
            "behavior_evidence_refs": [
                "feature.cc:_init_feat_index/get_feature_def",
                "terrain.cc feature behaviour",
                "directn.cc/describe.cc observation sinks",
            ],
            "evidence": {
                "enum": relative(FEATURE_ENUM),
                "initializer": relative(FEATURE_DATA),
            },
        })
    proof = {
        "enum_order": [row["identity"] for row in enum_rows],
        "enum_values": {row["identity"]: row["value"] for row in enum_rows},
        "data_order": [row["identity"] for row in data],
        "aliases": aliases,
    }
    return rows, proof, en_desc, zh_desc


def _line_number(text, offset):
    return text.count("\n", 0, offset) + 1


def _anchor_at(text, offset):
    anchor = "file"
    for match in re.finditer(r"(?m)^\s*NAME:\s*(\S.*?)(?:\s*$)", text[:offset]):
        anchor = "NAME:" + re.sub(r"\s+", " ", match.group(1).strip())
    if anchor == "file":
        functions = list(re.finditer(
            r"\bfunction\s+([A-Za-z_][A-Za-z0-9_.:]*)\s*\(", text[:offset]
        ))
        if functions:
            anchor = "function:" + functions[-1].group(1)
    return anchor


def _matching_token(tokens, opening):
    depth = 0
    for index in range(opening, len(tokens)):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unclosed Lua expression at offset {tokens[opening][2]}")


def _expression_record(text, tokens, start, end):
    selected = tokens[start:end]
    strings = [token[1] for token in selected if token[0] == "STRING"]
    identifiers = sorted({
        token[1] for token in selected if token[0] == "IDENT"
    })
    expression_end = tokens[end - 1][2] + 1 if selected else 0
    if selected and selected[-1][0] == "STRING":
        quote_start = selected[-1][2]
        if text[quote_start] in {'"', "'"}:
            quote = text[quote_start]
            expression_end = quote_start + 1
            while expression_end < len(text):
                if text[expression_end] == "\\":
                    expression_end += 2
                    continue
                if text[expression_end] == quote:
                    expression_end += 1
                    break
                expression_end += 1
    expression = text[selected[0][2]:expression_end] if selected else ""
    static = None
    meaningful = [token for token in selected if token[0] not in {"(", ")"}]
    if meaningful and all(token[0] in {"STRING", ".", ".."}
                          for token in meaningful):
        static = "".join(strings)
    elif len(meaningful) == 1 and meaningful[0][0] == "STRING":
        static = meaningful[0][1]
    return {
        "expression": expression.strip(),
        "literal_fragments": strings,
        "dynamic_parameters": identifiers,
        "static_english": static,
    }


def _top_level_first_arg(tokens, opening, closing):
    depth = 0
    end = closing
    for index in range(opening + 1, closing):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            depth -= 1
        elif kind == "," and depth == 0:
            end = index
            break
    return opening + 1, end


def _top_level_args(tokens, opening, closing):
    result = []
    start = opening + 1
    depth = 0
    for index in range(start, closing):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            depth -= 1
        elif kind == "," and depth == 0:
            result.append((start, index))
            start = index + 1
    result.append((start, closing))
    return result


def _assignment_end(tokens, start, limit):
    depth = 0
    for index in range(start, limit):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            if depth == 0:
                return index
            depth -= 1
        elif kind == "," and depth == 0:
            return index
    return limit


def _producer_contexts(tokens):
    contexts = []
    names = {"timed_msg", "timed_marker", "portal_desc", "trove_marker"}
    for index, token in enumerate(tokens[:-1]):
        if token[0] != "IDENT" or token[1] not in names:
            continue
        opening = index + 1
        if tokens[opening][0] == "(" and opening + 1 < len(tokens):
            opening += 1
        if tokens[opening][0] != "{":
            continue
        contexts.append({
            "kind": token[1],
            "start": opening,
            "end": _matching_token(tokens, opening),
        })
    return contexts


def _tokensets(value):
    if value is None:
        return {"placeholders": [], "entity_macros": [], "markup": []}
    return {
        "placeholders": sorted(set(re.findall(
            r"%(?:\d+\$)?[-+#0 .'I]*\d*(?:\.\d+)?[a-zA-Z]", value
        ))),
        "entity_macros": sorted(set(
            re.findall(r"\$[A-Za-z]+(?:\{[^}]*\})?|\{[A-Za-z_]+\}", value)
        )),
        "markup": sorted(set(re.findall(r"</?[A-Za-z_]+>", value))),
    }


def _source_lookup(record, source_exact, trim_fallback=False):
    en = record["static_english"]
    lookup = (
        lowercase_string(i18n_escape_key(en)) if en is not None else None
    )
    zh = source_exact.get(lookup) if lookup is not None else None
    matched_key = lookup if zh is not None else None
    if zh is None and trim_fallback and en is not None:
        trimmed = en.rstrip()
        if trimmed != en:
            trimmed_key = lowercase_string(i18n_escape_key(trimmed))
            zh = source_exact.get(trimmed_key)
            if zh is not None:
                matched_key = trimmed_key
    record["source_lookup_key"] = lookup
    record["source_matched_key"] = matched_key
    record["source_trim_fallback"] = bool(
        matched_key is not None and matched_key != lookup
    )
    record["source_exact_match"] = zh is not None
    record["current_chinese"] = zh
    record["tokens"] = {
        "english": _tokensets(en),
        "chinese": _tokensets(zh),
    }
    record["token_drift"] = (
        record["tokens"]["english"] != record["tokens"]["chinese"]
        if zh is not None else False
    )
    return record


def _des_lua_view(text):
    """Mask non-Lua .des syntax while preserving byte/character offsets."""
    output = []
    in_block = False
    interesting = re.compile(
        r"crawl\.(?:mpr|formatted_mpr|yesno|take_note)|"
        r"set_feature_name|portal_desc|toll_desc|"
        r"trove_milestone|wizlab_milestone"
    )
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        starts_block = re.match(
            r"(?i)(?:[a-z_]\w*\s+)?\{\{(?:\s*$|\s+(?:local|function|if|"
            r"crawl|return)\b)",
            stripped,
        )
        include = in_block or bool(starts_block) or stripped.startswith(":")
        include = include or bool(interesting.search(line))
        if include:
            output.append(line)
        else:
            output.append("".join(
                char if char in "\r\n" else " " for char in line
            ))
        if starts_block:
            in_block = True
        if in_block and "}}" in line:
            in_block = False
    if in_block:
        raise ValueError("unterminated .des lua {{ block")
    return "".join(output)


def scan_des_file(path, source_exact, exclusions=None, feature_desc_exact=None):
    """Extract player-facing slots from one .des using the shared Lua lexer."""
    text = path.read_text(encoding="utf-8")
    tokens = list(_lua_tokens(_des_lua_view(text)))
    candidates = []
    exclusions = exclusions if exclusions is not None else []
    contexts = _producer_contexts(tokens)

    # Direct crawl display sinks.
    for index in range(len(tokens) - 3):
        if not (
            tokens[index][:2] == ("IDENT", "crawl")
            and tokens[index + 1][0] == "."
            and tokens[index + 2][0] == "IDENT"
            and tokens[index + 3][0] == "("
        ):
            continue
        sink = tokens[index + 2][1]
        suspicious = re.search(r"mpr|message|note|yesno|formatted", sink)
        if sink not in DIRECT_SINKS and not suspicious:
            continue
        closing = _matching_token(tokens, index + 3)
        arguments = _top_level_args(tokens, index + 3, closing)
        selected_argument = 1 if sink == "god_speaks" else 0
        if selected_argument >= len(arguments):
            exclusions.append({
                "file": relative(path),
                "line": _line_number(text, tokens[index][2]),
                "sink": f"crawl.{sink}",
                "reason": "malformed display sink arguments",
            })
            continue
        start, end = arguments[selected_argument]
        diagnostic_window = text[max(0, tokens[index][2] - 500):
                                 tokens[index][2] + 200]
        literal_text = " ".join(
            token[1] for token in tokens[start:end] if token[0] == "STRING"
        )
        diagnostic_reason = None
        rel_path = relative(path)
        if "/dat/des/builder/" in rel_path:
            diagnostic_reason = "map-generation diagnostic output"
        elif ("/dat/des/arrival/" in rel_path
              and "replica[1].x" in diagnostic_window):
            diagnostic_reason = "map-generation coordinate diagnostic"
        elif re.search(
            r"(?i)(?:^|[< ])error(?:\s|:)|not a valid|couldn.t find",
            literal_text,
        ):
            diagnostic_reason = "diagnostic/error output"
        elif re.search(r"\b(?:wizmode|dry_run|is_validating|debug)\b",
                       diagnostic_window):
            diagnostic_reason = "wizmode/dry_run/validation output"
        if diagnostic_reason:
            exclusions.append({
                "file": relative(path),
                "line": _line_number(text, tokens[index][2]),
                "sink": f"crawl.{sink}",
                "reason": diagnostic_reason,
            })
            continue
        # A nested crawl.t_(...) is the real SourceDB key.  Keep the outer
        # display call as the slot identity whether translation is direct
        # (crawl.mpr(crawl.t_(...))) or followed by interpolation
        # (crawl.mpr(string.format(crawl.t_(...), value))).
        translations = []
        for pos in range(start, max(start, end - 3)):
            if not (
                tokens[pos][:2] == ("IDENT", "crawl")
                and tokens[pos + 1][0] == "."
                and tokens[pos + 2][:2] == ("IDENT", "t_")
                and tokens[pos + 3][0] == "("
            ):
                continue
            translation_end = _matching_token(tokens, pos + 3)
            if translation_end < end:
                inner = _expression_record(
                    text, tokens, pos + 4, translation_end
                )
                translations.append((pos + 4, translation_end, inner))
        static_translations = [
            item for item in translations
            if item[2]["static_english"] is not None
        ]
        selected_translation = (
            static_translations[0] if len(static_translations) == 1
            else translations[0] if len(translations) == 1
            else None
        )
        if selected_translation is not None:
            _, _, record = selected_translation
            record["expression"] = text[
                tokens[start][2]:tokens[end - 1][2] + 1
            ].strip()
            record["dynamic_parameters"] = sorted(set(
                record["dynamic_parameters"]
                + [
                    token[1] for token in tokens[start:end]
                    if token[0] == "IDENT"
                    and token[1] not in {"crawl", "t_", "string", "format"}
                ]
            ))
            late_consumer = "crawl.t_"
        else:
            record = _expression_record(text, tokens, start, end)
            late_consumer = None
            if translations:
                record["unsupported"] = (
                    "no unique static translated template in display expression"
                )
        translated_dynamic_parameters = sorted({
            token[1]
            for translation_start, translation_end, translation in translations
            if translation["static_english"] is None
            for token in tokens[translation_start:translation_end]
            if token[0] == "IDENT"
        })
        display_title_parameters = sorted({
            parameter for parameter in record["dynamic_parameters"]
            if re.search(r"(?:^|_)(?:desc|name|title)$", parameter)
        })
        untranslated_display_title_parameters = sorted(
            set(display_title_parameters) - set(translated_dynamic_parameters)
        )
        record.update({
            "sink_kind": f"crawl.{sink}",
            "channel": "note" if sink == "take_note" else "message",
            "trigger": "direct_call",
            "persistence": sink == "take_note",
            "late_translation_consumer": late_consumer,
            "offset": tokens[index][2],
            "line": _line_number(text, tokens[index][2]),
            "translated_dynamic_parameters": translated_dynamic_parameters,
            "display_title_parameters": display_title_parameters,
            "untranslated_display_title_parameters": (
                untranslated_display_title_parameters
            ),
        })
        if sink not in DIRECT_SINKS:
            record["unsupported"] = f"unknown display-like crawl sink: {sink}"
        elif sink == "take_note":
            record["protocol_deferral"] = {
                "classification": "canonical_english_persistent_payload",
                "owner": "save/note schema maintainer",
                "re_entry": (
                    "Re-enter when notes support canonical-English storage "
                    "with language-dependent late display."
                ),
            }
            if translations:
                record["protocol_boundary_issue"] = (
                    "persistent note payload invokes crawl.t_ before storage"
                )
        elif untranslated_display_title_parameters:
            record["protocol_boundary_issue"] = (
                "dynamic display title parameter lacks late translation: "
                + ", ".join(untranslated_display_title_parameters)
            )
        elif record["static_english"] is None and late_consumer is None:
            record["unsupported"] = "dynamic direct display expression"
        candidates.append(_source_lookup(record, source_exact))

    # Finite runtime title producers. Their literal callsite arguments are
    # distinct display values consumed through crawl.t_(..._desc) by the
    # milestone display helper; inventory them independently of the shared
    # format-template row.
    for index in range(len(tokens) - 1):
        token = tokens[index]
        if (token[0] != "IDENT"
                or token[1] not in FINITE_TITLE_PRODUCERS
                or tokens[index + 1][0] != "("):
            continue
        closing = _matching_token(tokens, index + 1)
        arguments = _top_level_args(tokens, index + 1, closing)
        if len(arguments) < 2:
            continue
        start, end = arguments[1]
        record = _expression_record(text, tokens, start, end)
        if record["static_english"] is None:
            continue
        producer = FINITE_TITLE_PRODUCERS[token[1]]
        record.update({
            "sink_kind": producer["sink_kind"],
            "channel": "message_title",
            "trigger": "vault_epilogue",
            "persistence": False,
            "late_translation_consumer": "crawl.t_",
            "finite_title_producer": token[1],
            "finite_title_consumer": producer["consumer"],
            "offset": token[2],
            "line": _line_number(text, token[2]),
        })
        candidates.append(_source_lookup(record, source_exact))

    # Production display-producing fields.  Each literal is an independent
    # stable slot; table-valued fields therefore retain every alternative.
    for index, token in enumerate(tokens):
        if token[0] != "IDENT":
            continue
        name = token[1]
        if name in DISPLAY_ASSIGNMENTS and index + 1 < len(tokens):
            if tokens[index + 1][0] not in {"=", "{"}:
                continue
            context = next(
                (item for item in contexts
                 if item["start"] < index < item["end"]),
                None,
            )
            allowed = (
                context is not None
                and (
                    (name == "desc"
                     and context["kind"] in {"portal_desc", "timed_marker"})
                    or (name == "toll_desc"
                        and context["kind"] in {"portal_desc", "trove_marker"})
                    or (name in TIMED_FIELDS - {"desc"}
                        and context["kind"] in {"timed_msg", "timed_marker"})
                )
            )
            if not allowed:
                continue
            value_start = index + 2 if tokens[index + 1][0] == "=" else index + 1
            if value_start >= len(tokens):
                continue
            value_end = _assignment_end(tokens, value_start, context["end"])
            is_table = tokens[value_start][0] == "{"
            if is_table and name == "initmsg":
                table_end = _matching_token(tokens, value_start)
                literal_ranges = _top_level_args(
                    tokens, value_start, table_end
                )
            elif is_table:
                literal_ranges = [
                    (pos, pos + 1) for pos in range(value_start, value_end)
                    if tokens[pos][0] == "STRING"
                ]
            else:
                literal_ranges = [(value_start, value_end)]
            if not any(tokens[pos][0] == "STRING"
                       for pos in range(value_start, value_end)):
                candidates.append({
                    "sink_kind": name,
                    "channel": "message",
                    "trigger": "producer_field",
                    "persistence": name in {"toll_desc", "desc"},
                    "late_translation_consumer": (
                        "lm_trove:crawl.t_" if name == "toll_desc"
                        else "lm_tmsg/lm_timed"
                    ),
                    "expression": text[tokens[value_start][2]:
                                       tokens[value_end - 1][2] + 1].strip(),
                    "literal_fragments": [],
                    "dynamic_parameters": sorted({
                        t[1] for t in tokens[value_start:value_end]
                        if t[0] == "IDENT"
                    }),
                    "static_english": None,
                    "source_exact_match": False,
                    "current_chinese": None,
                    "tokens": {"english": _tokensets(None),
                               "chinese": _tokensets(None)},
                    "token_drift": False,
                    "offset": token[2],
                    "line": _line_number(text, token[2]),
                    "unsupported": "dynamic producer field",
                })
            for literal_start, literal_end in literal_ranges:
                record = _expression_record(
                    text, tokens, literal_start, literal_end
                )
                record.update({
                    "sink_kind": name,
                    "channel": "message",
                    "trigger": "producer_field",
                    "persistence": name in {"toll_desc", "desc"},
                    "late_translation_consumer": (
                        "lm_trove:crawl.t_" if name == "toll_desc"
                        else "lm_tmsg/lm_timed"
                    ),
                    "offset": token[2],
                    "line": _line_number(text, token[2]),
                })
                lookup_db = (
                    feature_desc_exact
                    if (name == "desc" and context["kind"] == "portal_desc"
                        and feature_desc_exact is not None)
                    else source_exact
                )
                candidates.append(_source_lookup(
                    record,
                    lookup_db,
                    trim_fallback=name in {
                        "initmsg", "finalmsg", "range_msg_fmt", "ranges",
                        "messages", "verb", "noisemaker", "entity",
                    },
                ))

    # Feature renames: only the second argument is display; first is protocol.
    for index, token in enumerate(tokens):
        if token[:2] != ("IDENT", "set_feature_name"):
            continue
        opening = index + 1
        if opening >= len(tokens) or tokens[opening][0] != "(":
            continue
        closing = _matching_token(tokens, opening)
        depth = 0
        comma = None
        for pos in range(opening + 1, closing):
            if tokens[pos][0] in {"(", "{", "["}:
                depth += 1
            elif tokens[pos][0] in {")", "}", "]"}:
                depth -= 1
            elif tokens[pos][0] == "," and depth == 0:
                comma = pos
                break
        if comma is None:
            continue
        record = _expression_record(text, tokens, comma + 1, closing)
        record.update({
            "sink_kind": "feature_rename",
            "channel": "feature_description",
            "trigger": "feature_observation",
            "persistence": True,
            "late_translation_consumer": "feature description display",
            "offset": token[2],
            "line": _line_number(text, token[2]),
        })
        candidates.append(_source_lookup(record, source_exact))

    rel = relative(path)
    ordinals = Counter()
    rows = []
    for candidate in sorted(candidates, key=lambda row: (
            row["offset"], row["sink_kind"], row.get("static_english") or "")):
        anchor = _anchor_at(text, candidate["offset"])
        key = (anchor, candidate["sink_kind"])
        ordinals[key] += 1
        candidate["identity"] = (
            f"des_display:{rel}:{anchor}:{candidate['sink_kind']}:"
            f"{ordinals[key]}"
        )
        candidate["category"] = "des_display"
        candidate["lifecycle"] = "current"
        candidate["evidence"] = {"file": rel, "line": candidate.pop("line")}
        candidate.pop("offset")
        rows.append(candidate)
    return rows


def des_producer_universe(files):
    """Enumerate and classify every production crawl call/marker constructor."""
    calls = {}
    constructors = {}
    crawl_classification = {}
    for classification, methods in CRAWL_API_CLASSIFICATIONS.items():
        for method in methods:
            if method in crawl_classification:
                raise ValueError(
                    f"crawl.{method} appears in multiple producer classes"
                )
            crawl_classification[method] = classification
    for path in files:
        text = path.read_text(encoding="utf-8")
        tokens = list(_lua_tokens(_des_lua_view(text)))
        for index in range(len(tokens) - 3):
            name = None
            collection = None
            if (tokens[index][:2] == ("IDENT", "crawl")
                    and tokens[index + 1][0] == "."
                    and tokens[index + 2][0] == "IDENT"
                    and tokens[index + 3][0] == "("):
                name = "crawl." + tokens[index + 2][1]
                collection = calls
            elif (tokens[index][0] == "IDENT"
                    and re.search(r"(?:_msg|_hint|_marker|_desc)$",
                                  tokens[index][1])
                    and tokens[index + 1][0] in {"(", "{"}):
                name = tokens[index][1]
                collection = constructors
            if collection is None:
                continue
            record = collection.setdefault(
                name, {"count": 0, "evidence": []}
            )
            record["count"] += 1
            if len(record["evidence"]) < 3:
                record["evidence"].append({
                    "file": relative(path),
                    "line": _line_number(text, tokens[index][2]),
                })
    classified = []
    unknown = []
    for name, evidence in sorted(calls.items()):
        method = name.split(".", 1)[1]
        classification = crawl_classification.get(method, "unknown")
        if classification == "unknown":
            unknown.append(name)
        classified.append(
            {"producer": name, "classification": classification, **evidence}
        )
    for required in {"tutorial_msg", "tutorial_hint"}:
        constructors.setdefault(required, {"count": 0, "evidence": []})
    for name, evidence in sorted(constructors.items()):
        classification = CONSTRUCTOR_CLASSIFICATIONS.get(name, "unknown")
        if classification == "unknown":
            unknown.append(name)
        classified.append(
            {"producer": name, "classification": classification, **evidence}
        )
    return classified, unknown


def des_rows():
    files = sorted(DES_ROOT.rglob("*.des"), key=lambda path: relative(path))
    source_exact = {}
    for path in source_files(ZH_SOURCE_DIR):
        for entry in parse_entries_physical(str(path)):
            source_exact[entry.canonical_key] = runtime_normalize_value(
                entry.value
            )
    feature_desc_exact = physical_db(ZH_FEATURES)["effective"]
    rows = []
    excluded = []
    excluded_slots = []
    for path in files:
        rel = relative(path)
        if path.name == "test.des" or "test" in path.parts:
            excluded.append({"file": rel, "reason": "test fixture"})
            continue
        try:
            file_rows = scan_des_file(
                path, source_exact, excluded_slots, feature_desc_exact
            )
        except ValueError as error:
            raise ValueError(f"{rel}: {error}") from error
        rows.extend(file_rows)
        if not file_rows:
            excluded.append({
                "file": rel,
                "reason": "no supported player-display producer",
            })
    portal_files = sorted(
        (DES_ROOT / "portals").glob("*.des"), key=lambda path: path.name
    )
    family_rows = []
    child_counts = Counter(
        Path(row["evidence"]["file"]).stem
        for row in rows
        if "/dat/des/portals/" in row["evidence"]["file"]
    )
    for path in portal_files:
        family_rows.append({
            "identity": f"portal_family:{path.stem}",
            "category": "portal_family",
            "lifecycle": "current",
            "file": relative(path),
            "display_slot_count": child_counts[path.stem],
            "evidence": {"file": relative(path)},
        })
    universe, unknown = des_producer_universe(files)
    return (family_rows + rows, files, excluded, excluded_slots,
            universe, unknown)


def inventory_violations(rows, branch_proof, feature_proof,
                         branch_dbs, feature_dbs, unknown_producers=None):
    identities = [row["identity"] for row in rows]
    branches = [row for row in rows if row["category"] == "branch"]
    features = [row for row in rows if row["category"] == "feature"]
    enum_branch = branch_proof["enum_order"]
    data_branch = branch_proof["data_order"]
    enum_feature = feature_proof["enum_order"]
    data_feature = feature_proof["data_order"]
    display = [row for row in rows if row["category"] == "des_display"]
    return {
        "duplicate_identities": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "branch_enum_data_set_drift": {
            "enum_only": sorted(set(enum_branch) - set(data_branch)),
            "data_only": sorted(set(data_branch) - set(enum_branch)),
        } if set(enum_branch) != set(data_branch) else {},
        "branch_enum_data_order_drift": (
            {"enum": enum_branch, "data": data_branch}
            if enum_branch != data_branch else {}
        ),
        "feature_enum_data_set_drift": {
            "enum_only": sorted(set(enum_feature) - set(data_feature)),
            "data_only": sorted(set(data_feature) - set(enum_feature)),
        } if set(enum_feature) != set(data_feature) else {},
        "feature_duplicate_data_identities": sorted(
            identity for identity, count in Counter(data_feature).items()
            if count > 1
        ),
        "missing_display_translations": sorted(
            f"{row['identity']}:{item['field']}" for row in branches
            if row["lifecycle"] == "current"
            for item in row["display_strings"] if not item["zh"]
        ) + sorted(
            row["identity"] for row in features
            if row["lifecycle"] == "current" and row["name"]
            and not row["current_chinese_name"]
        ),
        "missing_descriptions": sorted(
            row["identity"] for row in branches + features
            if row["lifecycle"] == "current"
            and row.get("english_description") is not None
            and not row.get("chinese_description")
        ),
        "unexpected_zh_branch_description_keys": sorted(
            set(branch_dbs[1]["raw"]) - set(branch_dbs[0]["raw"])
        ),
        "unexpected_zh_feature_description_keys": sorted(
            set(feature_dbs[1]["raw"]) - set(feature_dbs[0]["raw"])
        ),
        "duplicate_textdb_keys": {
            name: db["duplicates"]
            for name, db in {
                "en_branches": branch_dbs[0],
                "zh_branches": branch_dbs[1],
                "en_features": feature_dbs[0],
                "zh_features": feature_dbs[1],
            }.items() if db["duplicates"]
        },
        "missing_exact_source_keys": sorted(
            row["identity"] for row in display
            if row.get("static_english") and not row["source_exact_match"]
            and not row.get("protocol_deferral")
        ),
        "unresolved_or_unsupported_display_slots": sorted(
            row["identity"] for row in display
            if row.get("unsupported")
        ),
        "placeholder_macro_markup_drift": sorted(
            row["identity"] for row in display if row.get("token_drift")
        ),
        "protocol_display_boundary_issues": sorted(
            row["identity"] for row in display
            if (row["sink_kind"] in PROTOCOL_ASSIGNMENTS
                or row.get("protocol_boundary_issue"))
        ),
        "unknown_des_producers": sorted(unknown_producers or []),
        "missing_branch_mechanics": sorted(
            row["identity"] for row in branches
            if not row.get("mechanics") or not row.get("raw_producer")
        ),
        "missing_feature_behavior_evidence": sorted(
            row["identity"] for row in features
            if not row.get("flags") or not row.get("minimap")
            or not row.get("raw_producer")
            or not row.get("behavior_evidence_refs")
        ),
    }


def _review_safe(value):
    value = str(value if value is not None and value != "" else "(none)")
    # Markdown table parsing strips cell-edge whitespace. Normalize the
    # production-derived expectation to that representable boundary only;
    # inventory identities and SourceDB lookup values remain untouched.
    return re.sub(r"\s+", " ", value).strip().replace("|", "/")


def _row_current_chinese(row):
    return (
        row.get("current_chinese")
        or row.get("current_chinese_name")
        or next((
            item.get("zh") for item in row.get("display_strings", [])
            if item.get("zh")
        ), None)
        or row.get("chinese_description")
    )


def review_expected_composite_adoption(row, adopted_values=None):
    """Build the complete branch/feature adoption object bound to review."""
    if row["category"] == "branch":
        displays = {
            item["field"]: item.get("zh")
            for item in row.get("display_strings", [])
        }
        expected_values = {
            "description": row.get("chinese_description"),
            "entry_message": displays.get("entry_message"),
            "longname": displays.get("longname"),
            "shortname": displays.get("shortname"),
        }
        english_values = {
            "description": row.get("english_description"),
            "entry_message": row.get("entry_message"),
            "longname": row.get("longname"),
            "shortname": row.get("shortname"),
        }
    elif row["category"] == "feature":
        expected_values = {
            "description": row.get("chinese_description"),
            "name": row.get("current_chinese_name"),
            "vaultname": (
                "preserve canonical English: " + row["vaultname"]
                if row.get("vaultname") else None
            ),
        }
        english_values = {
            "description": row.get("english_description"),
            "name": row.get("name"),
            "vaultname": row.get("vaultname"),
        }
    else:
        return None

    values = expected_values if adopted_values is None else adopted_values
    return {
        "category": row["category"],
        "values": values,
        "tokens": {
            field: {
                "english": _tokensets(english_values.get(field) or ""),
                "adopted": _tokensets(values.get(field) or ""),
            }
            for field in expected_values
        },
    }


def _submitted_composite_adoption(row, cell):
    """Canonicalize the adopted/current object carried by a decision cell."""
    try:
        decision = json.loads(cell)
    except (TypeError, json.JSONDecodeError):
        return {"invalid_json": cell}
    if not isinstance(decision, dict):
        return {"invalid_structure": decision}
    if "adopt" in decision:
        adopted = decision["adopt"]
    elif "current" in decision:
        # Keep/defer cards preserve the production value rather than proposing
        # a replacement, so their current object is the adopted object.
        adopted = decision["current"]
    elif set(decision) == set(
            review_expected_composite_adoption(row)["values"]):
        # Some terminal adjustment cards carry the complete adopted object
        # directly, without historical/current wrapper metadata.
        adopted = decision
    else:
        return {"missing_adopt_or_current": decision}
    if not isinstance(adopted, dict):
        return {"invalid_adopted_object": adopted}
    return review_expected_composite_adoption(row, adopted)


def review_expected_fact_cells(payload, row):
    """Return production-derived evidence cells shared by writer and validator."""
    evidence = row.get("evidence", {})
    producer = evidence.get("file") or evidence.get("initializer") or (
        row.get("file") or row["category"]
    )
    consumers = (
        row.get("behavior_evidence_refs")
        or row.get("protocol_identity", {}).get("required_consumer_refs")
        or row.get("shortname_paths", {}).get("required_consumer_refs")
        or [row.get("finite_title_consumer")
            or row.get("late_translation_consumer")
            or "inventory parent"]
    )
    english = (
        row.get("static_english") or row.get("name")
        or row.get("shortname") or row.get("file")
    )
    chinese = _row_current_chinese(row)
    if row["category"] == "feature":
        mechanics = {
            "flags": row.get("flags"),
            "minimap": row.get("minimap"),
            "raw_producer": row.get("raw_producer"),
            "behavior_evidence_refs": row.get("behavior_evidence_refs"),
        }
    elif row["category"] == "branch":
        mechanics = {
            "mechanics": row.get("mechanics"),
            "raw_producer": row.get("raw_producer"),
        }
    elif row["category"] == "portal_family":
        mechanics = {
            "display_slot_count": row.get("display_slot_count"),
            "file": row.get("file"),
        }
    else:
        mechanics = {
            "sink_kind": row.get("sink_kind"),
            "tokens": row.get("tokens"),
            "dynamic_parameters": row.get("dynamic_parameters"),
            "translated_dynamic_parameters": row.get(
                "translated_dynamic_parameters"
            ),
        }
    protocol = bool(
        row.get("protocol_identity") or row.get("lookup_identity")
        or row.get("protocol_deferral")
    )
    tokens = row.get("tokens") or {
        "format": "not applicable",
        "entity_macro": "not applicable",
        "markup": "not applicable",
        "structure": row["category"],
    }
    dependencies = (
        row.get("name_alias_group")
        or row.get("vaultname_alias_group")
        or [row.get("finite_title_producer") or row["category"]]
    )
    authority = {
        "glossary_sha256": payload.get("glossary_sha256", "not supplied"),
        "decisions_sha256": payload.get("input_sha256", {}).get(
            "docs/decisions.md", "not supplied"
        ),
    }
    target_scope = {
        "category": row["category"],
        "identity": row["identity"],
        "lifecycle": row["lifecycle"],
        "conditions": row.get("trigger") or row["lifecycle"],
        "exceptions": row.get("protocol_deferral") or "none",
        "consequences": row.get("channel") or row["category"],
    }
    facts = {
        "producer_consumer": _review_safe(
            f"{producer}; {', '.join(consumers)}"
        ),
        "trigger_context": _review_safe(
            f"{row.get('trigger', row['category'])}; "
            f"{row.get('channel', row['lifecycle'])}"
        ),
        "persistence_protocol": _review_safe(
            f"persistent={row.get('persistence', False)}; "
            f"protocol={protocol}"
        ),
        "en": _review_safe(english),
        "zh": _review_safe(chinese if chinese else "(missing)"),
        "mechanics_tokens": _review_safe(json.dumps(
            mechanics, ensure_ascii=False, sort_keys=True
        )),
        "lifecycle": _review_safe(row["lifecycle"]),
        "display_context": _review_safe(
            row.get("channel") or row.get("category")
        ),
        "producer": _review_safe(producer),
        "consumers_users": _review_safe(", ".join(consumers)),
        "mechanics_behavior": _review_safe(json.dumps(
            mechanics, ensure_ascii=False, sort_keys=True
        )),
        "target_scope_conditions_exceptions_consequences": _review_safe(
            json.dumps(target_scope, ensure_ascii=False, sort_keys=True)
        ),
        "trigger_timing": _review_safe(
            row.get("trigger") or "inventory parent lifecycle"
        ),
        "persistence_serialization": _review_safe(
            f"persistent={row.get('persistence', False)}; "
            f"serialization_protocol={protocol}"
        ),
        "late_translation_sink": _review_safe(
            row.get("late_translation_consumer") or "not applicable"
        ),
        "format_entity_markup_structure_tokens": _review_safe(json.dumps(
            tokens, ensure_ascii=False, sort_keys=True
        )),
        "glossary_decision_authority": _review_safe(json.dumps(
            authority, ensure_ascii=False, sort_keys=True
        )),
        "shared_dependency_group": _review_safe(json.dumps(
            dependencies, ensure_ascii=False, sort_keys=True
        )),
        "evidence_locations": _review_safe(json.dumps(
            evidence, ensure_ascii=False, sort_keys=True
        )),
    }
    return facts, (_review_safe(chinese) if chinese else None)


def review_coverage(payload, path):
    """Prove exactly one terminal conclusion per frozen inventory identity."""
    text = path.read_text(encoding="utf-8")
    managed_match = re.search(
        r"<!-- BEGIN WORLD INVENTORY EVIDENCE -->(.*?)"
        r"<!-- END WORLD INVENTORY EVIDENCE -->",
        text,
        re.S,
    )
    review_text = managed_match.group(1) if managed_match else text
    known = {row["identity"] for row in payload["rows"]}
    digest_match = re.search(
        r"(?mi)^\s*Inventory-SHA256:\s*`?([0-9a-f]{64})`?\s*$",
        review_text,
    )
    required_columns = REVIEW_COLUMNS
    table_lines = [
        line for line in review_text.splitlines()
        if line.lstrip().startswith("|")
    ]
    header = []
    if table_lines:
        header = [
            cell.strip().lower()
            for cell in table_lines[0].strip().strip("|").split("|")
        ]
    rows = []
    missing_fields = {}
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header != required_columns or len(cells) != len(required_columns):
            continue
        card = dict(zip(required_columns, cells))
        identity = card["identity"].strip("`")
        if identity in known or identity.startswith(
                ("branch:", "feature:", "portal_family:", "des_display:")):
            rows.append((identity, card))
            empty = [
                field for field in required_columns[1:]
                if not card[field] or card[field] in {"-", "—"}
            ]
            if empty:
                missing_fields[identity] = empty
    identities = [identity for identity, _ in rows]
    actual = set(identities)
    cards = {identity: card for identity, card in rows}
    inventory_rows = {row["identity"]: row for row in payload["rows"]}
    fact_mismatches = {}
    adopted_translation_mismatches = {}
    composite_adoption_mismatches = {}
    for identity, card in cards.items():
        row = inventory_rows.get(identity)
        if row is None:
            continue
        expected_facts, expected_adopted = review_expected_fact_cells(
            payload, row
        )
        mismatched = sorted(
            field for field, expected in expected_facts.items()
            if card.get(field) != expected
        )
        if mismatched:
            fact_mismatches[identity] = mismatched
        if (expected_adopted is not None
                and card.get("adopted_translation") != expected_adopted):
            adopted_translation_mismatches[identity] = {
                "expected": expected_adopted,
                "actual": card.get("adopted_translation"),
            }
        expected_composite = review_expected_composite_adoption(row)
        if expected_composite is not None:
            actual_composite = _submitted_composite_adoption(
                row, card.get("proposed_translation")
            )
            if actual_composite != expected_composite:
                composite_adoption_mismatches[identity] = {
                    "decision_field": "proposed_translation",
                    "expected": expected_composite,
                    "actual": actual_composite,
                }
    conclusions = {
        identity: card["conclusion"] for identity, card in rows
    }
    terminal = re.compile(
        r"^(?:keep|adjust|retranslate|defer terminology|"
        r"defer implementation|保留|调整|重译|暂缓(?:术语|实现))\b",
        re.I,
    )
    invalid = sorted(
        identity for identity, conclusion in conclusions.items()
        if not terminal.match(conclusion.strip())
    )
    pending_pattern = re.compile(
        r"^(?:pending(?: review| evidence review)?|insufficient evidence|"
        r"not reviewed|tbd|unknown)$",
        re.I,
    )
    pending_required_fields = {
        identity: sorted(
            field for field in required_columns[1:]
            if pending_pattern.match(card[field].strip())
        )
        for identity, card in cards.items()
        if terminal.match(card["conclusion"].strip())
        and any(
            pending_pattern.match(card[field].strip())
            for field in required_columns[1:]
        )
    }
    invalid_decision_fields = {
        identity: sorted(
            field for field in REVIEW_DECISION_FIELDS
            if pending_pattern.match(card[field].strip())
        )
        for identity, card in cards.items()
        if terminal.match(card["conclusion"].strip())
        and any(
            pending_pattern.match(card[field].strip())
            for field in REVIEW_DECISION_FIELDS
        )
    }
    confidence_pattern = re.compile(
        r"^(?:high|medium|low|高|中|低)(?:$|[\s:：])", re.I
    )
    invalid_confidence = sorted(
        identity for identity, card in cards.items()
        if terminal.match(card["conclusion"].strip())
        and not confidence_pattern.match(card["confidence"].strip())
    )
    return {
        "review_results": relative(path),
        "review_results_sha256": sha(path),
        "inventory_sha256_binding": (
            digest_match.group(1) if digest_match else None
        ),
        "inventory_digest_matches": bool(
            digest_match
            and digest_match.group(1) == payload["inventory_sha256"]
        ),
        "required_columns": required_columns,
        "header_matches": header == required_columns,
        "evidence_card_count": len(identities),
        "duplicate_evidence_cards": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "missing_evidence_cards": sorted(known - actual),
        "unexpected_evidence_cards": sorted(actual - known),
        "invalid_terminal_conclusions": invalid,
        "missing_required_fields": missing_fields,
        "pending_required_fields": pending_required_fields,
        "invalid_decision_fields": invalid_decision_fields,
        "invalid_confidence": invalid_confidence,
        "fact_mismatches": fact_mismatches,
        "adopted_translation_mismatches": (
            adopted_translation_mismatches
        ),
        "composite_adoption_mismatches": composite_adoption_mismatches,
        "coverage_equal": (
            len(identities) == len(known)
            and actual == known
            and not invalid
            and not missing_fields
            and not pending_required_fields
            and not invalid_decision_fields
            and not invalid_confidence
            and not fact_mismatches
            and not adopted_translation_mismatches
            and not composite_adoption_mismatches
            and header == required_columns
            and bool(digest_match)
            and digest_match.group(1) == payload["inventory_sha256"]
        ),
    }


def complete_review_results(payload, path):
    """Write/replace the script-owned strict evidence-card table."""
    columns = REVIEW_COLUMNS

    lines = [
        "<!-- BEGIN WORLD INVENTORY EVIDENCE -->",
        f"Inventory-SHA256: {payload['inventory_sha256']}",
        "",
        "| " + " | ".join(columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in payload["rows"]:
        facts, _expected_adopted = review_expected_fact_cells(payload, row)
        card = {
            "identity": f"`{row['identity']}`",
            **facts,
            # These are reviewer decisions. Never infer them from current
            # assets or prefill them with a fabricated terminal answer.
            "proposed_translation": PENDING_REVIEW,
            "adopted_translation": PENDING_REVIEW,
            "rejected_alternatives": PENDING_REVIEW,
            "confidence": PENDING_REVIEW,
            "deferred_follow_up": PENDING_REVIEW,
            "re_entry_conditions": PENDING_REVIEW,
            "conclusion": "insufficient evidence",
        }
        cells = [card[column] for column in columns]
        lines.append("| " + " | ".join(cells) + " |")
    lines.append("<!-- END WORLD INVENTORY EVIDENCE -->")
    managed = "\n".join(lines) + "\n"
    old = path.read_text(encoding="utf-8") if path.exists() else ""
    pattern = re.compile(
        r"<!-- BEGIN WORLD INVENTORY EVIDENCE -->.*?"
        r"<!-- END WORLD INVENTORY EVIDENCE -->\n?",
        re.S,
    )
    updated = pattern.sub(managed, old) if pattern.search(old) else (
        old.rstrip() + ("\n\n" if old.strip() else "") + managed
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated, encoding="utf-8")


def build_inventory():
    branches, branch_proof, en_branches, zh_branches = branch_rows()
    features, feature_proof, en_features, zh_features = feature_rows()
    (des, des_files, excluded_files, excluded_slots,
     producer_universe, unknown_producers) = des_rows()
    rows = branches + features + des
    inputs = [
        BRANCH_ENUM, BRANCH_DATA, BRANCH_CC, FEATURE_ENUM, FEATURE_DATA,
        EN_BRANCHES, ZH_BRANCHES, EN_FEATURES, ZH_FEATURES, GLOSSARY,
        SRC / "tag-version.h",
        SRC / "branch.h", SRC / "feature.h", SRC / "feature.cc",
        SRC / "directn.cc", SRC / "terrain.cc", SRC / "describe.cc",
        SRC / "lookup-help.cc", SRC / "stairs.cc", SRC / "database.cc",
        SRC / "dat/dlua/lm_tmsg.lua", SRC / "dat/dlua/lm_timed.lua",
        SRC / "dat/dlua/lm_pdesc.lua", SRC / "dat/dlua/lm_trove.lua",
        SCRIPT_DIR / "audit_item_name_inventory.py",
        SCRIPT_DIR / "audit_god_inventory.py",
        SCRIPT_DIR / "i18n_extract.py", SCRIPT_DIR / "i18n_shared.py",
        ROOT / "docs/decisions.md",
        *source_files(ZH_SOURCE_DIR), *des_files,
    ]
    violations = inventory_violations(
        rows, branch_proof, feature_proof,
        (en_branches, zh_branches), (en_features, zh_features),
        unknown_producers,
    )
    category_counts = Counter(row["category"] for row in rows)
    lifecycle_counts = Counter(row["lifecycle"] for row in rows)
    payload = {
        "schema": "dcss-world-review-inventory-v1",
        "baseline": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "tag_major_version": tag_major_version(),
        "glossary_sha256": sha(GLOSSARY),
        "input_sha256": {
            relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(inputs), key=relative)
        },
        "scope": {
            "included": [
                "active branch enum and branches[] display producers",
                "active feature enum and feat_defs[] display producers",
                "all sorted dat/des/portals/*.des families including zero-slot families",
                "single sorted production dat/des/**/*.des display-producer walk",
                "direct crawl display sinks, timed portal fields, trove toll_desc, "
                "portal desc and feature renames",
            ],
            "excluded": [
                "comments and dead/commented calls",
                "test files and directories",
                "diagnostic, error, assert, wizmode and dry_run output",
                "milestone and xlog protocol payloads",
                ".des NAME/TAGS/KFEAT/MARKER and feature/schema/lookup/"
                "comparison/serialization identity keys",
                "vaultname and branch abbrevname protocol identities",
            ],
            "excluded_files": excluded_files,
            "excluded_slots": excluded_slots,
            "non_owner_universe": [
                "dat/des/tutorial", "dat/des/sprint", "dat/des/altar"
            ],
            "producer_universe": producer_universe,
        },
        "proof": {"branches": branch_proof, "features": feature_proof},
        "category_counts": dict(sorted(category_counts.items())),
        "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "rows": rows,
        "violations": violations,
    }
    encoded = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    payload["inventory_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def has_violations(payload):
    return any(payload["violations"].values())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-results", type=Path)
    parser.add_argument("--complete-review-results", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = build_inventory()
        if args.complete_review_results:
            complete_review_results(payload, args.complete_review_results)
        if args.review_results:
            payload["review_coverage"] = review_coverage(
                payload, args.review_results
            )
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        print(f"ERROR: world inventory could not be built: {error}",
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
            "baseline", "glossary_sha256", "inventory_sha256",
            "category_counts", "lifecycle_counts",
        )
    }
    summary["violation_counts"] = {
        key: len(value) if hasattr(value, "__len__") else int(bool(value))
        for key, value in payload["violations"].items()
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    coverage_failed = (
        "review_coverage" in payload
        and not payload["review_coverage"]["coverage_equal"]
    )
    return 1 if has_violations(payload) or coverage_failed else 0


if __name__ == "__main__":
    sys.exit(main())
