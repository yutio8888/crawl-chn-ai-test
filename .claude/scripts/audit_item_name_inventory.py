#!/usr/bin/env python3
"""Freeze the ordinary-item and equipment-ego name inventory for ZH review.

The inventory is derived from production enums and name producers rather than
from a hand-maintained list. It covers stable ordinary item subtype names,
weapon-brand verbose/terse/adjective forms, armour-ego verbose/terse forms,
and concrete jewellery effect names.
"""

import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_shared import AuditRootError, resolve_audit_root  # noqa: E402

try:
    ROOT = resolve_audit_root(SCRIPT_ROOT)
except AuditRootError as error:
    print(f"ERROR: invalid audit root: {error}", file=sys.stderr)
    raise SystemExit(2)

SRC = ROOT / "crawl-ref/source"
ZH_SOURCE = SRC / "dat/i18n/zh/source.txt"
ZH_SOURCE_DIR = ZH_SOURCE.parent
ISSUE29_REVIEW_BASE = "01dc9911ec9948aff661f6ec0b9b0a798fcf909d"

DEVELOPMENT_REPORTS = [
    {
        "path": (
            ".claude/metrics/verify/"
            "20260727T010743460030000+0800-11676-01dc9911ec99/"
            "verify.log"
        ),
        "profile": "translation",
        "status": "fail",
        "blocking_failures": 1,
        "note": "initial translation development run; retained raw failure",
    },
    {
        "path": (
            ".claude/metrics/verify/"
            "20260727T010920784160000+0800-12201-01dc9911ec99/"
            "verify.log"
        ),
        "profile": "translation",
        "status": "pass",
        "blocking_failures": 0,
        "note": "translation development rerun",
    },
    {
        "path": (
            ".claude/metrics/verify/"
            "20260727T014522409076000+0800-30190-01dc9911ec99/"
            "verify.log"
        ),
        "profile": "code",
        "status": "fail",
        "blocking_failures": 3,
        "note": (
            "initial code run: missing AST dependencies, headless smoke, "
            "and 83 over-broad enumerator reports"
        ),
    },
    {
        "path": (
            ".claude/metrics/verify/"
            "20260727T020030796997000+0800-50072-01dc9911ec99/"
            "verify.log"
        ),
        "profile": "code",
        "status": "pass",
        "blocking_failures": 0,
        "note": "full code development rerun; all phases passed",
    },
]

from i18n_shared import (
    load_review_input,
    parse_entries_physical,
    review_input_metadata,
    runtime_normalize_value,
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def resolve_commit(revision, root=ROOT):
    if not revision:
        raise RuntimeError("review base is required")
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{revision}^{{commit}}"],
            cwd=root, text=True, stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"invalid review base: {revision}") from error


def git_revision_bytes(path, revision, root=ROOT):
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as error:
        raise RuntimeError(f"path is outside review repository: {path}") from error
    try:
        return subprocess.check_output(
            ["git", "show", f"{revision}:{relative}"],
            cwd=root, stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"required review-base input is missing: {revision}:{relative}"
        ) from error


def git_revision_text(path, revision, root=ROOT):
    try:
        return git_revision_bytes(path, revision, root).decode("utf-8")
    except UnicodeDecodeError as error:
        raise RuntimeError(
            f"review-base input is not UTF-8: {revision}:{path}"
        ) from error


def source_files(directory):
    """Return localized SourceDB inputs in the production load order."""
    source = directory / "source.txt"
    if not source.is_file():
        raise FileNotFoundError(f"required SourceDB input is missing: {source}")
    files = sorted(directory.glob("*.txt"), key=lambda path: path.name)
    return [source, *(path for path in files if path != source)]


def source_entries(directory):
    # Localized SourceDB loads source.txt first, then every other sorted .txt
    # file with trim_keys=false. DBM_REPLACE makes the final exact canonical
    # key definition authoritative.
    result = {}
    for path in source_files(directory):
        for entry in parse_entries_physical(str(path)):
            result[entry.canonical_key] = runtime_normalize_value(entry.value)
    return result


def tag_major_version():
    text = (SRC / "tag-version.h").read_text(encoding="utf-8")
    match = re.search(r"^\s*#define\s+TAG_MAJOR_VERSION\s+(\d+)\s*$",
                      text, re.MULTILINE)
    if not match:
        raise RuntimeError("TAG_MAJOR_VERSION was not found")
    return int(match.group(1))


def _tag_condition(expression, version):
    match = re.fullmatch(
        r"\s*TAG_MAJOR_VERSION\s*(==|!=|>=|<=|>|<)\s*(\d+)\s*",
        expression,
    )
    if not match:
        if "TAG_MAJOR_VERSION" in expression:
            raise RuntimeError(
                f"unsupported TAG_MAJOR_VERSION condition: {expression.strip()}"
            )
        return None
    operator, raw_target = match.groups()
    target = int(raw_target)
    return {
        "==": version == target,
        "!=": version != target,
        ">=": version >= target,
        "<=": version <= target,
        ">": version > target,
        "<": version < target,
    }[operator]


def active_source(path):
    """Select TAG_MAJOR_VERSION branches without preprocessing full Crawl.

    Full C++ preprocessing depends on generated build headers such as
    art-enum.h, which are intentionally absent in a fresh worktree. The item
    name producers only need their TAG_MAJOR_VERSION branches selected; other
    preprocessor conditions are left inclusive for the literal parser.
    """
    version = tag_major_version()
    output = []
    stack = []
    active = True
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        directive = re.match(r"^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)",
                             line)
        if not directive:
            output.append(line if active else "\n")
            continue

        kind, expression = directive.groups()
        if kind in {"if", "ifdef", "ifndef"}:
            if kind == "if":
                condition = _tag_condition(expression, version)
            elif expression.strip() == "TAG_MAJOR_VERSION":
                condition = kind == "ifdef"
            elif "TAG_MAJOR_VERSION" in expression:
                raise RuntimeError(
                    "unsupported TAG_MAJOR_VERSION directive: "
                    f"#{kind} {expression.strip()}"
                )
            else:
                condition = None
            frame = {
                "parent": active,
                "tag": condition is not None,
                "taken": bool(condition),
            }
            stack.append(frame)
            active = active and condition if condition is not None else active
        elif kind == "elif":
            if not stack:
                raise RuntimeError(f"unmatched #elif in {path}")
            frame = stack[-1]
            condition = _tag_condition(expression, version)
            if frame["tag"]:
                if condition is None:
                    raise RuntimeError(
                        "unsupported non-TAG #elif in TAG condition chain: "
                        f"{expression.strip()}"
                    )
                active = frame["parent"] and not frame["taken"] and condition
                frame["taken"] = frame["taken"] or condition
            else:
                active = frame["parent"]
        elif kind == "else":
            if not stack:
                raise RuntimeError(f"unmatched #else in {path}")
            frame = stack[-1]
            if frame["tag"]:
                active = frame["parent"] and not frame["taken"]
                frame["taken"] = True
            else:
                active = frame["parent"]
        else:
            if not stack:
                raise RuntimeError(f"unmatched #endif in {path}")
            active = stack.pop()["parent"]
        output.append("\n")
    if stack:
        raise RuntimeError(f"unterminated preprocessor condition in {path}")
    return "".join(output)


def function_body(text, name):
    match = re.search(r"\b" + re.escape(name) + r"\s*\([^;]*?\)\s*\{", text, re.S)
    if not match:
        raise RuntimeError(f"function not found: {name}")
    start = match.end() - 1
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    raise RuntimeError(f"unclosed function: {name}")


def switch_literals(text, name):
    body = function_body(text, name)
    pattern = re.compile(
        r"case\s+([A-Z][A-Z0-9_]+)\s*:\s*"
        r"return\s+(?:(T_|C_)\()?"
        r"(?:\"([^\"]+)\"\s*,\s*)?\"([^\"]*)\"\)?\s*;"
    )
    rows = {}
    for identity, wrapper, context, literal in pattern.findall(body):
        key = f"{context}|{literal}" if wrapper == "C_" else literal
        rows[identity] = {
            "key": key, "en": literal, "runtime_lookup": bool(wrapper),
        }
    return rows


def property_literals(text, array_name):
    match = re.search(
        r"\b" + re.escape(array_name) + r"\s*\[\]\s*=\s*\{(.*?)\n\};",
        text, re.S,
    )
    if not match:
        raise RuntimeError(f"array not found: {array_name}")
    rows = {}
    for entry in re.finditer(
        r"\{\s*([A-Z][A-Z0-9_]+)\s*,\s*((?:\"[^\"]*\"\s*)+)",
        match.group(1),
    ):
        identity, string_expr = entry.groups()
        literal = "".join(re.findall(r'"([^"]*)"', string_expr))
        rows[identity] = {"key": literal, "en": literal}
    if array_name == "Armour_prop":
        for identity, name in re.findall(
            r'DRAGON_ARMOUR\(\s*([A-Z_]+)\s*,\s*"([^"]+)"',
            match.group(1),
        ):
            literal = f"{name} dragon scales"
            rows[f"ARM_{identity}_DRAGON_ARMOUR"] = {
                "key": literal,
                "en": literal,
            }
    return rows


def contextual_brand_forms(text):
    """Parse the narrow C_() overrides layered over weapon-brand arrays."""
    name_body = function_body(text, "brand_type_name")
    adj_body = function_body(text, "brand_type_adj")
    overrides = {}
    name_pattern = re.compile(
        r"if\s*\(\s*brand\s*==\s*(SPWPN_[A-Z0-9_]+)\s*\)\s*\{\s*"
        r"return\s+terse\s*\?\s*C_\s*\(\"([^\"]+)\",\s*\"([^\"]+)\"\)"
        r"\s*:\s*C_\s*\(\"([^\"]+)\",\s*\"([^\"]+)\"\)\s*;\s*\}",
        re.S,
    )
    for identity, terse_context, terse, verbose_context, verbose in (
        name_pattern.findall(name_body)
    ):
        overrides.setdefault(identity, {}).update({
            "terse": {"key": f"{terse_context}|{terse}", "en": terse},
            "verbose": {
                "key": f"{verbose_context}|{verbose}", "en": verbose,
            },
        })
    adj_pattern = re.compile(
        r"if\s*\(\s*brand\s*==\s*(SPWPN_[A-Z0-9_]+)\s*\)\s*"
        r"return\s+C_\s*\(\"([^\"]+)\",\s*\"([^\"]+)\"\)\s*;"
    )
    for identity, context, literal in adj_pattern.findall(adj_body):
        overrides.setdefault(identity, {})["adj"] = {
            "key": f"{context}|{literal}", "en": literal,
        }
    parsed = sum(len(forms) for forms in overrides.values())
    expected = len(re.findall(r"\bC_\s*\(", name_body + adj_body))
    if parsed != expected:
        raise RuntimeError(
            "unparsed contextual weapon-brand producer override"
        )
    return overrides


def contextual_book_names(text):
    """Parse contextual full-name overrides in the OBJ_BOOKS producer."""
    body = function_body(text, "sub_type_string")
    pattern = re.compile(
        r"sub_type\s*==\s*(BOOK_[A-Z0-9_]+)\s*\?\s*"
        r"C_\s*\(\"([^\"]+)\",\s*\"([^\"]+)\"\)\s*"
        r":\s*T_\(_book_type_name\(sub_type\)\)",
        re.S,
    )
    rows = {
        identity: {
            "key": f"{context}|{literal}",
            "en": f"book of {literal}",
        }
        for identity, context, literal in pattern.findall(body)
    }
    if len(rows) != len(re.findall(r"\bC_\s*\(", body)):
        raise RuntimeError("unparsed contextual book-name producer override")
    return rows


def enum_constants(headers, enum_names):
    source = "\n".join(f'#include "{header}"' for header in headers)
    with tempfile.TemporaryDirectory(prefix="dcss-item-audit-") as directory:
        probe = Path(directory) / "enums.cc"
        probe.write_text(source, encoding="utf-8")
        raw = subprocess.run(
            ["clang++", "-std=c++17", "-I", str(SRC),
             "-Xclang", "-ast-dump=json", "-fsyntax-only", str(probe)],
            cwd=ROOT, check=True, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        ).stdout
    ast = json.loads(raw)
    found = {}

    def visit(node):
        if node.get("kind") == "EnumDecl" and node.get("name") in enum_names:
            constants = []
            for child in node.get("inner", []):
                if child.get("kind") != "EnumConstantDecl":
                    continue
                value = None
                stack = [child]
                while stack:
                    current = stack.pop()
                    if "value" in current:
                        value = int(current["value"])
                        break
                    stack.extend(current.get("inner", []))
                constants.append((child["name"], value))
            resolved = []
            previous = -1
            for constant, value in constants:
                if value is None:
                    value = previous + 1
                resolved.append((constant, value))
                previous = value
            found[node["name"]] = resolved
        for child in node.get("inner", []):
            visit(child)
    visit(ast)
    return found


def translated(db, key):
    return db.get(key.lower())


def add(rows, category, mapping, db, render=None, lifecycle="current"):
    for identity, data in mapping.items():
        key = data["key"]
        en = data["en"]
        present = key.lower() in db
        zh_token = translated(db, key) if present else en
        zh = render(en, zh_token, identity) if render else zh_token
        rows.append({
            "identity": f"{category}:{identity}",
            "category": category,
            "lifecycle": lifecycle,
            "english_source_name": en,
            "translation_key": key,
            "current_chinese_name": zh,
            "translation_present": present,
            "runtime_lookup": data.get("runtime_lookup", True),
        })


def inventory_violations(rows, expected_identities=None):
    identities = [row["identity"] for row in rows]
    actual_identities = set(identities)
    expected_identities = (
        actual_identities if expected_identities is None
        else set(expected_identities)
    )
    duplicates = sorted(
        identity for identity, count
        in Counter(identities).items()
        if count > 1
    )
    missing_chinese = [
        row["identity"] for row in rows
        if row.get("runtime_lookup", True)
        and not row.get(
            "translation_present",
            bool(row.get("current_chinese_name")),
        )
    ]
    required_forms = {
        "weapon_brand": ("verbose", "terse", "adj"),
        "armour_ego": ("verbose", "terse"),
    }
    missing_forms = []
    for row in rows:
        forms = row.get("forms", {})
        for form in required_forms.get(row.get("category"), ()):
            data = forms.get(form)
            if not data or not data.get("en") or data.get("zh") is None:
                missing_forms.append(f"{row['identity']}:{form}")
    return {
        "duplicates": duplicates,
        "missing_identities": sorted(expected_identities - actual_identities),
        "unexpected_identities": sorted(actual_identities - expected_identities),
        "missing_chinese": missing_chinese,
        "missing_forms": missing_forms,
    }


def expected_identities(enums, removed_pairs):
    """Derive the frozen membership independently from name producers."""
    specs = [
        ("weapon", "OBJ_WEAPONS", "weapon_type", "WPN_", "NUM_WEAPONS"),
        ("missile", "OBJ_MISSILES", "missile_type", "MI_", "NUM_MISSILES"),
        ("armour", "OBJ_ARMOUR", "armour_type", "ARM_", "NUM_ARMOURS"),
        ("wand", "OBJ_WANDS", "wand_type", "WAND_", "NUM_WANDS"),
        ("scroll", "OBJ_SCROLLS", "scroll_type", "SCR_", "NUM_SCROLLS"),
        (
            "jewellery_effect", "OBJ_JEWELLERY", "jewellery_type", None,
            "NUM_JEWELLERY",
        ),
        ("potion", "OBJ_POTIONS", "potion_type", "POT_", "NUM_POTIONS"),
        ("book", "OBJ_BOOKS", "book_type", "BOOK_", "NUM_BOOKS"),
        ("staff", "OBJ_STAVES", "stave_type", "STAFF_", "NUM_STAVES"),
        (
            "miscellany", "OBJ_MISCELLANY", "misc_item_type", "MISC_",
            "NUM_MISCELLANY",
        ),
        (
            "talisman", "OBJ_TALISMANS", "talisman_type", "TALISMAN_",
            "NUM_TALISMANS",
        ),
        (
            "bauble", "OBJ_BAUBLES", "bauble_type", "BAUBLE_",
            "NUM_BAUBLES",
        ),
    ]
    expected = {"orb:ORB_ZOT"}
    excluded = {"BOOK_RANDART_LEVEL", "BOOK_RANDART_THEME"}
    for category, object_class, enum_name, prefix, end_marker in specs:
        values = enums[enum_name]
        limit = dict(values)[end_marker]
        seen_values = set()
        for identity, value in values:
            if value >= limit or value in seen_values:
                continue
            if prefix is None:
                if not identity.startswith(("RING_", "AMU_")):
                    continue
            elif not identity.startswith(prefix):
                continue
            seen_values.add(value)
            if ((object_class, identity) in removed_pairs
                    or identity in excluded):
                continue
            expected.add(f"{category}:{identity}")

    for enum_name, category, prefix, limit_marker, excluded_identity in [
        (
            "brand_type", "weapon_brand", "SPWPN_",
            "NUM_REAL_SPECIAL_WEAPONS", "SPWPN_NORMAL",
        ),
        (
            "special_armour_type", "armour_ego", "SPARM_",
            "NUM_REAL_SPECIAL_ARMOURS", "SPARM_NORMAL",
        ),
    ]:
        values = enums[enum_name]
        limit = dict(values)[limit_marker]
        seen_values = set()
        for identity, value in values:
            if (not identity.startswith(prefix) or value < 0
                    or value >= limit or value in seen_values):
                continue
            seen_values.add(value)
            if identity != excluded_identity:
                expected.add(f"{category}:{identity}")
    return expected


def build_inventory():
    db = source_entries(ZH_SOURCE_DIR)
    item_prop = active_source(SRC / "item-prop.cc")
    item_name = active_source(SRC / "item-name.cc")
    enums = enum_constants(
        ["item-prop-enum.h", "potion-type.h", "book-type.h"],
        {
            "armour_type", "weapon_type", "missile_type", "wand_type",
            "scroll_type", "jewellery_type", "potion_type", "book_type",
            "stave_type", "misc_item_type", "talisman_type", "bauble_type",
            "gem_type", "brand_type", "special_armour_type",
        },
    )

    removed_pairs = set(re.findall(
        r"\{\s*(OBJ_[A-Z0-9_]+)\s*,\s*([A-Z][A-Z0-9_]+)\s*\}",
        re.search(r"removed_items\s*=\s*\{(.*?)\};", item_prop, re.S).group(1),
    ))
    def current(mapping, object_class):
        return {
            identity: data for identity, data in mapping.items()
            if (object_class, identity) not in removed_pairs
        }

    rows = []
    add(rows, "weapon", current(property_literals(item_prop, "Weapon_prop"),
                                "OBJ_WEAPONS"), db)
    add(rows, "missile", current(property_literals(item_prop, "Missile_prop"),
                                 "OBJ_MISSILES"), db)
    add(rows, "armour", current(property_literals(item_prop, "Armour_prop"),
                                "OBJ_ARMOUR"), db)

    add(rows, "wand", current(switch_literals(item_name, "_wand_type_name"),
                              "OBJ_WANDS"), db,
        lambda en, zh, _: f"{zh}魔杖" if zh else None)
    add(rows, "scroll", current(switch_literals(item_name, "scroll_type_name"),
                                "OBJ_SCROLLS"), db,
        lambda en, zh, _: f"{zh}卷轴" if zh else None)
    add(rows, "potion", current(switch_literals(item_name, "potion_type_name"),
                                "OBJ_POTIONS"), db,
        lambda en, zh, _: f"{zh}药水" if zh else None)

    jewellery = switch_literals(item_name, "jewellery_effect_name")
    # The parser sees both full and terse switches; retain the first/full form.
    body = function_body(item_name, "jewellery_effect_name")
    full_body = body.split("else", 1)[0]
    jewellery = {}
    pattern = re.compile(
        r"case\s+([A-Z][A-Z0-9_]+)\s*:\s*return\s+"
        r"(?:(T_|C_)\()?(?:\"([^\"]+)\"\s*,\s*)?\"([^\"]*)\"\)?\s*;"
    )
    for identity, wrapper, context, literal in pattern.findall(full_body):
        key = f"{context}|{literal}" if wrapper == "C_" else literal
        jewellery[identity] = {"key": key, "en": literal}
    def jewel_render(en, zh, identity):
        if not zh:
            return None
        return f"{zh}{'项链' if identity.startswith('AMU_') else '戒指'}"
    add(rows, "jewellery_effect", current(jewellery, "OBJ_JEWELLERY"),
        db, jewel_render)

    staff = property_literals(item_prop, "Staff_prop")
    add(rows, "staff", current(staff, "OBJ_STAVES"), db,
        lambda en, zh, _: f"{zh}法杖" if zh else None)

    misc = switch_literals(item_name, "misc_type_name")
    for identity, value in enums["misc_item_type"]:
        if identity.startswith("MISC_DECK_OF_") and identity not in misc:
            misc[identity] = {
                "key": "removed deck", "en": "removed deck",
                "runtime_lookup": False,
            }
    add(rows, "miscellany", current(misc, "OBJ_MISCELLANY"), db)
    talisman = switch_literals(item_prop, "talisman_type_name")
    add(rows, "talisman", talisman, db)

    # Books: merge generic "book of X" titles and the explicit title cases
    # used by sub_type_string. Parameterised manual/parchment entries remain
    # explicit template identities.
    generic_books = switch_literals(item_name, "_book_type_name")
    book_rows = {
        identity: {"key": data["en"], "en": f"book of {data['en']}"}
        for identity, data in generic_books.items()
    }
    explicit = {}
    subtype_body = re.sub(
        r"//[^\n]*", "", function_body(item_name, "sub_type_string")
    )
    for identity, string_expression in re.findall(
        r"case\s+(BOOK_[A-Z0-9_]+)\s*:\s*return\s+T_?\("
        r"\s*((?:\"[^\"]*\"\s*)+)\)\s*;",
        subtype_body,
    ):
        literal = "".join(re.findall(r'"([^"]*)"', string_expression))
        explicit[identity] = {"key": literal, "en": literal}
    book_rows.update(explicit)
    book_rows.update(contextual_book_names(item_name))
    # Internal randart-book generation sentinels are not stable ordinary
    # display identities and are explicitly outside this audit.
    book_rows.pop("BOOK_RANDART_LEVEL", None)
    book_rows.pop("BOOK_RANDART_THEME", None)
    def book_render(en, zh, identity):
        if zh:
            return zh if not en.startswith("book of ") else f"{zh}之书"
        if identity == "BOOK_MANUAL":
            return "<技能名>手册"
        if identity == "BOOK_PARCHMENT":
            return "<法术名>羊皮纸"
        return None
    add(rows, "book", current(book_rows, "OBJ_BOOKS"), db, book_render)
    rows.extend([
        {
            "identity": "book:BOOK_MANUAL", "category": "book",
            "lifecycle": "current-parameterised",
            "english_source_name": "manual of <skill>",
            "translation_key": "book_type|manual",
            "current_chinese_name": "<技能名>手册",
        },
        {
            "identity": "book:BOOK_PARCHMENT", "category": "book",
            "lifecycle": "current-parameterised",
            "english_source_name": "parchment of <spell>",
            "translation_key": "parchment",
            "current_chinese_name": "<法术名>羊皮纸",
        },
    ])

    rows.append({
        "identity": "orb:ORB_ZOT", "category": "orb", "lifecycle": "current",
        "english_source_name": "Orb of Zot", "translation_key": "Orb of Zot",
        "current_chinese_name": db.get("orb of zot"),
        "translation_present": "orb of zot" in db,
        "runtime_lookup": True,
    })
    rows.append({
        "identity": "bauble:BAUBLE_FLUX", "category": "bauble",
        "lifecycle": "current", "english_source_name": "flux bauble",
        "translation_key": "flux bauble",
        "current_chinese_name": db.get("flux bauble"),
        "translation_present": "flux bauble" in db,
        "runtime_lookup": True,
    })

    # Weapon brands: one identity with all three runtime forms.
    terse_block = re.search(
        r"weapon_brands_terse\[\]\s*=\s*\{(.*?)\};", item_name, re.S
    ).group(1)
    verbose_block = re.search(
        r"weapon_brands_verbose\[\]\s*=\s*\{(.*?)\};", item_name, re.S
    ).group(1)
    adj_block = re.search(
        r"weapon_brands_adj\[\]\s*=\s*\{(.*?)\};", item_name, re.S
    ).group(1)
    literals = lambda block: re.findall(r'"([^"]*)"', block)
    terse, verbose, adj = map(literals, (terse_block, verbose_block, adj_block))
    brand_overrides = contextual_brand_forms(item_name)
    real_brand_limit = dict(enums["brand_type"])["NUM_REAL_SPECIAL_WEAPONS"]
    # Enum declaration order includes markers; numeric values select the arrays.
    seen_brand_values = set()
    for identity, value in enums["brand_type"]:
        if not identity.startswith("SPWPN_") or value is None or value in seen_brand_values:
            continue
        if (identity in {"SPWPN_FORBID_BRAND"}
                or value >= len(verbose) or value >= real_brand_limit):
            continue
        seen_brand_values.add(value)
        if identity == "SPWPN_NORMAL":
            continue
        forms = {
            "verbose": {"key": verbose[value], "en": verbose[value]},
            "terse": {"key": terse[value], "en": terse[value]},
            "adj": {"key": adj[value], "en": adj[value]},
        }
        forms.update(brand_overrides.get(identity, {}))
        verbose_form = forms["verbose"]
        rows.append({
            "identity": f"weapon_brand:{identity}",
            "category": "weapon_brand",
            "lifecycle": (
                "compatibility" if verbose_form["en"] == "obsolescence"
                else "internal" if identity == "SPWPN_CONFUSE"
                else "current"
            ),
            "english_source_name": verbose_form["en"],
            "translation_key": verbose_form["key"],
            "current_chinese_name": db.get(
                verbose_form["key"].lower(), verbose_form["en"]
            ),
            "translation_present": verbose_form["key"].lower() in db,
            "runtime_lookup": True,
            "forms": {
                form: {
                    "en": data["en"],
                    "zh": db.get(data["key"].lower()),
                }
                for form, data in forms.items()
            },
        })

    # Armour ego: verbose and terse forms share an enum identity.
    # Split the two branches explicitly to avoid the generic parser replacing
    # verbose cases with terse cases.
    tr_body = function_body(item_name, "special_armour_type_name")
    def branch_cases(body, marker):
        part = body.split(marker, 1)[0] if marker else body
        cases = {}
        pattern = re.compile(
            r"case\s+(SPARM_[A-Z0-9_]+)\s*:\s*return\s+"
            r"(T_|C_)\((?:\"([^\"]+)\"\s*,\s*)?\"([^\"]+)\"\)\s*;"
        )
        for identity, wrapper, context, literal in pattern.findall(part):
            cases[identity] = {
                "key": f"{context}|{literal}" if wrapper == "C_" else literal,
                "en": literal,
            }
        return cases
    tr_verbose_part = tr_body.split("else", 1)[0]
    tr_terse_part = tr_body.split("else", 1)[1]
    tr_verbose = branch_cases(tr_verbose_part, None)
    tr_terse = branch_cases(tr_terse_part, None)
    for compatibility_identity in (
        "SPARM_RUNNING", "SPARM_JUMPING", "SPARM_CLOUD_IMMUNE"
    ):
        tr_verbose[compatibility_identity] = {
            "key": "obsolescence", "en": "obsolescence",
        }
        tr_terse[compatibility_identity] = {
            "key": "obsolete", "en": "obsolete",
        }
    en_verbose = tr_verbose
    en_terse = tr_terse
    for identity in sorted(en_verbose):
        forms = {
            "verbose": en_verbose[identity],
            "terse": en_terse.get(identity),
        }
        verbose = forms["verbose"]
        rows.append({
            "identity": f"armour_ego:{identity}",
            "category": "armour_ego",
            "lifecycle": (
                "compatibility" if verbose["en"] == "obsolescence"
                else "current"
            ),
            "english_source_name": verbose["en"],
            "translation_key": verbose["key"],
            "current_chinese_name": db.get(
                verbose["key"].lower(), verbose["en"]
            ),
            "translation_present": verbose["key"].lower() in db,
            "runtime_lookup": True,
            "forms": {
                form: {
                    "en": data["en"] if data else None,
                    "zh": db.get(data["key"].lower()) if data else None,
                }
                for form, data in forms.items()
            },
        })

    rows.sort(key=lambda r: r["identity"])
    for row in rows:
        en = row["english_source_name"].lower()
        if row["lifecycle"] == "current" and (
            en.startswith("old ") or en.startswith("removed ")
            or en.startswith("obsolete ")
        ):
            row["lifecycle"] = "compatibility"
        if row["identity"] in {
            "armour:ARM_CAP",
            "armour:ARM_CENTAUR_BARDING",
            "missile:MI_NEEDLE",
            "miscellany:MISC_BOTTLED_EFREET",
        }:
            row["lifecycle"] = "compatibility"
    violations = inventory_violations(
        rows, expected_identities(enums, removed_pairs)
    )
    payload = {
        "schema": "dcss-item-name-review-inventory-v1",
        "baseline": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "glossary_sha256": sha(ROOT / "docs/glossary.md"),
        "input_sha256": {
            str(p.relative_to(ROOT)): sha(p)
            for p in [
                *source_files(ZH_SOURCE_DIR),
                SRC / "item-name.cc", SRC / "item-prop.cc",
                SRC / "item-prop-enum.h", SRC / "potion-type.h",
                SRC / "book-type.h",
            ]
        },
        "scope": {
            "included": [
                "current stable ordinary item subtype display names",
                "named TAG_MAJOR_VERSION compatibility identities",
                "weapon brand verbose/terse/adjective names",
                "armour ego verbose/terse names",
                "jewellery effect names",
            ],
            "excluded": [
                "fixed and random artefacts",
                "unidentified cosmetic appearances",
                "corpses, gold, runes, procedural gizmo names",
                "removed identities without a name producer",
                "internal random-book generation sentinels",
                "descriptions except as semantic evidence",
            ],
        },
        "count": len(rows),
        "category_counts": {
            category: sum(r["category"] == category for r in rows)
            for category in sorted({r["category"] for r in rows})
        },
        **violations,
        "rows": rows,
    }
    encoded_rows = json.dumps(rows, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")).encode()
    payload["inventory_sha256"] = hashlib.sha256(encoded_rows).hexdigest()
    return payload


def textdb_rows(path):
    entries = parse_entries_physical(str(path))
    keys = [entry.canonical_key for entry in entries]
    duplicates = sorted(
        key for key, count in Counter(keys).items() if count > 1
    )
    if duplicates:
        raise RuntimeError(f"duplicate TextDB keys in {path}: {duplicates}")
    return entries


def physical_candidates(entry):
    """Parse TextDB weighted variants with the production blank-line grammar."""
    lines = entry.value.splitlines()
    candidates = []
    index = 0
    while index < len(lines):
        while index < len(lines) and not lines[index]:
            index += 1
        if index == len(lines):
            break

        weight = 10
        match = re.fullmatch(r"w:([+-]?\d+)", lines[index])
        if match:
            weight = int(match.group(1))
            index += 1
            if index == len(lines):
                raise RuntimeError(
                    f"{entry.source_file}:{entry.raw_key}: "
                    "weight at end of entry"
                )

        pattern = []
        while index < len(lines) and lines[index]:
            pattern.append(lines[index])
            index += 1
        if not pattern:
            raise RuntimeError(
                f"{entry.source_file}:{entry.raw_key}: empty weighted variant"
            )
        candidates.append((weight, "\n".join(pattern).strip()))

    if not candidates:
        raise RuntimeError(
            f"{entry.source_file}:{entry.raw_key}: empty weighted entry"
        )
    return candidates


def weighted_grammar_metrics(entries):
    variants = 0
    raw_nonempty_lines = 0
    weight_marker_lines = 0
    weight_mass = 0
    for entry in entries:
        candidates = physical_candidates(entry)
        variants += len(candidates)
        weight_mass += sum(weight for weight, _ in candidates)
        nonempty = [line for line in entry.value.splitlines() if line]
        raw_nonempty_lines += len(nonempty)
        weight_marker_lines += sum(
            bool(re.fullmatch(r"w:[+-]?\d+", line)) for line in nonempty
        )
    continuation_lines = (
        raw_nonempty_lines - variants - weight_marker_lines
    )
    if continuation_lines < 0:
        raise RuntimeError("weighted grammar line accounting is negative")
    return {
        "physical_variant_identities": variants,
        "raw_nonempty_grammar_lines": raw_nonempty_lines,
        "explicit_weight_marker_lines": weight_marker_lines,
        "continuation_lines": continuation_lines,
        "weight_mass": weight_mass,
    }


def require_weighted_metrics(actual, expected, label):
    if actual != expected:
        raise RuntimeError(f"{label} metric drift: {actual}")


RANDART_METRICS = {
    "randname.txt": {
        "grammar_keys": 33,
        "physical_variant_identities": 482,
        "raw_nonempty_grammar_lines": 698,
        "explicit_weight_marker_lines": 215,
        "continuation_lines": 1,
        "weight_mass": 8007,
    },
    "rand_wpn.txt": {
        "grammar_keys": 45,
        "physical_variant_identities": 845,
        "raw_nonempty_grammar_lines": 867,
        "explicit_weight_marker_lines": 22,
        "continuation_lines": 0,
        "weight_mass": 8346,
    },
    "rand_arm.txt": {
        "grammar_keys": 19,
        "physical_variant_identities": 529,
        "raw_nonempty_grammar_lines": 537,
        "explicit_weight_marker_lines": 8,
        "continuation_lines": 0,
        "weight_mass": 5242,
    },
    "rand_all.txt": {
        "grammar_keys": 18,
        "physical_variant_identities": 584,
        "raw_nonempty_grammar_lines": 632,
        "explicit_weight_marker_lines": 48,
        "continuation_lines": 0,
        "weight_mass": 5709,
    },
}


def validate_randart_metrics(filename, en_entries, zh_entries):
    expected = RANDART_METRICS[filename]
    en_metrics = {
        "grammar_keys": len(en_entries),
        **weighted_grammar_metrics(en_entries),
    }
    zh_metrics = {
        "grammar_keys": len(zh_entries),
        **weighted_grammar_metrics(zh_entries),
    }
    require_weighted_metrics(
        en_metrics, expected, f"randart production {filename}"
    )
    require_weighted_metrics(
        zh_metrics, expected, f"randart ZH {filename}"
    )
    return expected


def physical_entries_from_text(text):
    with tempfile.TemporaryDirectory(prefix="dcss-item-v2-textdb-") as tmp:
        path = Path(tmp) / "input.txt"
        path.write_text(text, encoding="utf-8")
        return parse_entries_physical(str(path))


def revision_textdb_rows(path, revision):
    return physical_entries_from_text(git_revision_text(path, revision))


def source_entries_at_revision(directory, revision):
    try:
        relative = directory.relative_to(ROOT).as_posix()
    except ValueError as error:
        raise RuntimeError(
            f"SourceDB directory is outside review repository: {directory}"
        ) from error
    try:
        listing = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", revision, "--", relative],
            cwd=ROOT, text=True, stderr=subprocess.PIPE,
        ).splitlines()
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"cannot enumerate review-base SourceDB: {revision}:{relative}"
        ) from error
    paths = sorted(
        (ROOT / line for line in listing if line.endswith(".txt")),
        key=lambda path: path.name,
    )
    source = directory / "source.txt"
    if source not in paths:
        raise RuntimeError(
            f"required review-base SourceDB input is missing: "
            f"{revision}:{source.relative_to(ROOT)}"
        )
    paths = [source, *(path for path in paths if path != source)]
    result = {}
    for path in paths:
        for entry in revision_textdb_rows(path, revision):
            result[entry.canonical_key] = runtime_normalize_value(entry.value)
    return result


def changed_textdb_keys(path, review_base):
    before = {
        entry.canonical_key: runtime_normalize_value(entry.value)
        for entry in revision_textdb_rows(path, review_base)
    }
    after = {
        entry.canonical_key: runtime_normalize_value(entry.value)
        for entry in textdb_rows(path)
    }
    return {
        key for key in before.keys() | after.keys()
        if before.get(key) != after.get(key)
    }


def array_literals(text, array_name):
    match = re.search(
        r"\b" + re.escape(array_name)
        + r"\s*\[\]\s*=\s*\{(.*?)\};", text, re.S,
    )
    if not match:
        raise RuntimeError(f"array not found: {array_name}")
    return re.findall(r'"([^"]*)"', match.group(1))


def unrand_enum_identity(name, block):
    explicit = re.search(r"(?m)^ENUM:\s*(.+?)\s*$", block)
    if explicit:
        enum_name = explicit.group(1)
    else:
        enum_name = name.replace("'", "")
        quoted = re.search(r'"(.*)"', enum_name)
        after_of = re.search(r" of (?:the )?(.*)", enum_name)
        if quoted:
            enum_name = quoted.group(1)
        elif after_of:
            enum_name = after_of.group(1)
        enum_name = enum_name.upper().replace(" ", "_").replace("-", "_")
    if not re.fullmatch(r"[A-Z0-9_]+", enum_name):
        raise RuntimeError(
            f"invalid production-derived unrand enum: {enum_name}"
        )
    return f"UNRAND_{enum_name}"


def art_data_blocks(text):
    """Match util/art-data.pl's comment stripping and blank-line records."""
    blocks = []
    current = []
    for raw_line in text.splitlines():
        if raw_line.startswith("#"):
            continue
        line = re.sub(r"#.*", "", raw_line).rstrip()
        if not line:
            if current:
                blocks.append("\n".join(current))
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def unrand_rows(db, source_db, base_db, base_source_db, review_base):
    art = active_source(SRC / "art-data.txt")
    blocks = art_data_blocks(art)
    definitions = []
    for block in blocks:
        name = re.search(r"(?m)^NAME:\s*(.+?)\s*$", block)
        if not name:
            continue
        definitions.append({
            "name": name.group(1),
            "enum": unrand_enum_identity(name.group(1), block),
            "unid": (
                re.search(r"(?m)^APPEAR:\s*(.+?)\s*$", block)
                or re.search(r"(?m)^UNID:\s*(.+?)\s*$", block)
            ),
            "deleted": bool(re.search(
                r"(?m)^BOOL:.*\bdeleted\b", block
            )),
        })
    enums = [definition["enum"] for definition in definitions]
    if len(definitions) != 142 or len(enums) != 142:
        raise RuntimeError(
            f"unrand inventory drift: definitions={len(definitions)} "
            f"enums={len(enums)}"
        )
    enum_duplicates = sorted(
        enum_id for enum_id, count in Counter(enums).items() if count > 1
    )
    if enum_duplicates:
        raise RuntimeError(
            f"duplicate production-derived unrand enums: {enum_duplicates}"
        )

    changed_desc = changed_textdb_keys(
        SRC / "dat/descript/zh/unrand.txt", review_base
    )
    changed_names = set()
    for definition in definitions:
        key = definition["name"].lower()
        if base_source_db.get(key) != source_db.get(key):
            changed_names.add(key)
    expected_changed_names = {
        "glaive of prune", 'morningstar "eos"',
        "sword of cerebov", "amulet of the air",
    }
    if changed_names != expected_changed_names:
        raise RuntimeError(
            f"unrand SourceDB conclusion boundary drift: "
            f"{sorted(changed_names)}"
        )
    adjust_names = {"glaive of prune", 'morningstar "eos"'}

    rows = []
    for enum_id, definition in zip(enums, definitions):
        name = definition["name"]
        key = name.lower()
        dummy = name.startswith("DUMMY UNRANDART")
        lifecycle = (
            "internal" if dummy else
            "compatibility" if definition["deleted"] else "current"
        )
        if dummy:
            conclusion = "keep"
        elif key in adjust_names:
            conclusion = "adjust"
        elif key in changed_desc or key in changed_names:
            conclusion = "retranslate"
        else:
            conclusion = "keep"
        rows.append({
            "identity": f"unrand:{enum_id}",
            "category": "unrand",
            "lifecycle": lifecycle,
            "english_source": name,
            "_pre_review_chinese": base_source_db.get(key),
            "current_chinese": source_db.get(key),
            "description_key": name,
            "description_present": key in db,
            "producer": "art-data.txt -> unranddata[]",
            "consumer": (
                "get_artefact_name display; canonical English "
                "get_unrand_name_en TextDB lookup"
            ),
            "input": "crawl-ref/source/art-data.txt",
            "_metadata": {
                "description_pre_review_chinese": base_db.get(key),
                "description_current_chinese": db.get(key),
                "description_present_at_review_base": key in base_db,
                "description_present_in_candidate": key in db,
            },
            "_conclusion": conclusion,
        })
    return rows


def unidentified_appearance_rows(source_db, base_source_db):
    item_name = active_source(SRC / "item-name.cc")
    scroll = active_source(SRC / "zh-scroll-appearance.cc")
    specs = [
        ("wand-primary", array_literals(item_name, "primary_strings")[:12]),
        ("wand-secondary",
         array_literals(function_body(item_name, "wand_secondary_string"),
                        "secondary_strings")),
        ("ring-primary",
         array_literals(function_body(item_name, "ring_primary_string"),
                        "primary_strings")),
        ("ring-secondary",
         array_literals(function_body(item_name, "ring_secondary_string"),
                        "secondary_strings")),
        ("amulet-primary",
         array_literals(function_body(item_name, "amulet_primary_string"),
                        "primary_strings")),
        ("amulet-secondary",
         array_literals(function_body(item_name, "amulet_secondary_string"),
                        "secondary_strings")),
        ("staff-primary",
         array_literals(function_body(item_name, "staff_primary_string"),
                        "primary_strings")),
        ("staff-secondary",
         array_literals(function_body(item_name, "staff_secondary_string"),
                        "secondary_strings")),
        ("potion-colour", array_literals(item_name, "potion_colours")),
        ("potion-qualifier", array_literals(item_name, "potion_qualifiers")),
        ("scroll-binding", array_literals(scroll, "scroll_binding_zh")),
        ("scroll-seal", array_literals(scroll, "scroll_seal_zh")),
    ]
    expected = {
        "wand-primary": 12, "wand-secondary": 16,
        "ring-primary": 29, "ring-secondary": 13,
        "amulet-primary": 29, "amulet-secondary": 13,
        "staff-primary": 4, "staff-secondary": 10,
        "potion-colour": 23, "potion-qualifier": 15,
        "scroll-binding": 12, "scroll-seal": 10,
    }
    counts = {name: len(values) for name, values in specs}
    if counts != expected:
        raise RuntimeError(f"unidentified appearance drift: {counts}")
    rows = []
    for family, values in specs:
        for ordinal, value in enumerate(values):
            english = value.strip()
            current_chinese = (
                value if family.startswith("scroll-")
                else source_db.get(english.lower(), english)
            )
            rows.append({
                "identity": f"appearance:{family}:{ordinal:03d}",
                "category": "appearance",
                "lifecycle": "current",
                "english_source": english or "(empty component)",
                "_pre_review_chinese": (
                    current_chinese if family.startswith("scroll-")
                    else base_source_db.get(english.lower(), english)
                ),
                "current_chinese": current_chinese,
                "producer": "item-name.cc unidentified appearance arrays",
                "consumer": "item_def::name unidentified display grammar",
                "input": (
                    "crawl-ref/source/zh-scroll-appearance.cc"
                    if family.startswith("scroll-")
                    else "crawl-ref/source/item-name.cc"
                ),
                "_metadata": {
                    "family": family,
                    "physical_ordinal": ordinal,
                },
                "_conclusion": "keep",
            })
    return rows


def special_item_rows(source_db, base_source_db):
    item_name = active_source(SRC / "item-name.cc")
    body = function_body(item_name, "rune_type_name")
    runes = re.findall(
        r"case\s+(RUNE_[A-Z0-9_]+)\s*:\s*return\s+"
        r"C_\(\"rune_name\",\s*\"([^\"]+)\"\)", body,
    )
    if len(runes) != 19:
        raise RuntimeError(f"rune producer drift: {len(runes)}")
    rows = []
    for enum_id, english in runes:
        key = f"rune_name|{english}".lower()
        rows.append({
            "identity": f"special:{enum_id}",
            "category": "special",
            "lifecycle": "current",
            "english_source": english,
            "_pre_review_chinese": base_source_db.get(key),
            "current_chinese": source_db.get(key),
            "producer": "rune_type_name",
            "consumer": "item_def::name OBJ_RUNES",
            "input": "crawl-ref/source/item-name.cc",
            "_metadata": {"enum_identity": enum_id},
            "_conclusion": "keep",
        })
    for identity, english in [
        ("CORPSE_BODY", "corpse"),
        ("CORPSE_SKELETON", "skeleton"),
        ("OBJ_GOLD", "gold piece"),
        ("ORB_ZOT", "Orb of Zot"),
    ]:
        rows.append({
            "identity": f"special:{identity}",
            "category": "special",
            "lifecycle": "current",
            "english_source": english,
            "_pre_review_chinese": base_source_db.get(
                english.lower(), english
            ),
            "current_chinese": source_db.get(english.lower()),
            "producer": "item_def::name switch",
            "consumer": "item display",
            "input": "crawl-ref/source/item-name.cc",
            "_metadata": {"enum_identity": identity},
            "_conclusion": "keep",
        })
    if len(rows) != 23:
        raise RuntimeError(f"special item inventory drift: {len(rows)}")
    return rows


def _pre_review_variant_value(current, ordinal, base_values):
    base_patterns = [pattern for _, pattern in base_values]
    if current in base_patterns:
        return current
    for start in range(len(base_patterns)):
        combined = ""
        for end in range(start, len(base_patterns)):
            combined = (
                base_patterns[end] if end == start
                else combined + "\n" + base_patterns[end]
            )
            if combined == current:
                return current
            if len(combined) > len(current):
                break
    if ordinal < len(base_patterns):
        return base_patterns[ordinal]
    return None


def paired_component_rows(
    en_path, zh_path, category, review_base=None, changed_keys=None
):
    en_entries = textdb_rows(en_path)
    zh_entries = textdb_rows(zh_path)
    base_zh_entries = (
        revision_textdb_rows(zh_path, review_base)
        if review_base else zh_entries
    )
    en = {entry.canonical_key: entry for entry in en_entries}
    zh = {entry.canonical_key: entry for entry in zh_entries}
    base_zh = {
        entry.canonical_key: entry for entry in base_zh_entries
    }
    if en.keys() != zh.keys():
        raise RuntimeError(
            f"{category} key mismatch: missing={sorted(en.keys()-zh.keys())} "
            f"extra={sorted(zh.keys()-en.keys())}"
        )
    try:
        input_name = str(en_path.relative_to(ROOT))
    except ValueError:
        input_name = str(en_path)
    rows = []
    for key in sorted(en):
        en_values = physical_candidates(en[key])
        zh_values = physical_candidates(zh[key])
        base_values = (
            physical_candidates(base_zh[key]) if key in base_zh else []
        )
        if len(en_values) != len(zh_values):
            raise RuntimeError(
                f"{category}:{key} physical count mismatch "
                f"{len(en_values)} != {len(zh_values)}"
            )
        for ordinal, (en_variant, zh_variant) in enumerate(
            zip(en_values, zh_values)
        ):
            en_weight, english = en_variant
            zh_weight, chinese = zh_variant
            if en_weight != zh_weight:
                raise RuntimeError(
                    f"{category}:{key}:{ordinal} weight mismatch "
                    f"{en_weight} != {zh_weight}"
                )
            en_markers = re.findall(r"@[A-Za-z_][A-Za-z0-9_]*@", english)
            zh_markers = re.findall(r"@[A-Za-z_][A-Za-z0-9_]*@", chinese)
            if Counter(en_markers) != Counter(zh_markers):
                raise RuntimeError(
                    f"{category}:{key}:{ordinal} recursive token mismatch"
                )
            en_placeholders = Counter(re.findall(r"%\d*\$?[a-zA-Z]", english))
            zh_placeholders = Counter(re.findall(r"%\d*\$?[a-zA-Z]", chinese))
            if en_placeholders != zh_placeholders:
                raise RuntimeError(
                    f"{category}:{key}:{ordinal} placeholder mismatch"
                )
            rows.append({
                "identity": f"{category}:{key}:{ordinal:04d}",
                "category": category,
                "lifecycle": "current",
                "english_source": english,
                "_pre_review_chinese": _pre_review_variant_value(
                    chinese, ordinal, base_values
                ),
                "current_chinese": chinese,
                "producer": f"TextDB weighted key {key} physical ordinal",
                "consumer": (
                    "finite grammar/component materialization; final "
                    "procedural string explicitly non-enumerable"
                ),
                "input": input_name,
                "_metadata": {
                    "grammar_key": key,
                    "physical_ordinal": ordinal,
                    "weight": en_weight,
                },
                "_conclusion": (
                    "adjust" if changed_keys
                    and (key, ordinal) in changed_keys else "keep"
                ),
            })
    return rows


def changed_physical_ordinals(path, review_base):
    before_entries = {
        entry.canonical_key: physical_candidates(entry)
        for entry in revision_textdb_rows(path, review_base)
    }
    after_entries = {
        entry.canonical_key: physical_candidates(entry)
        for entry in textdb_rows(path)
    }
    changed = set()
    for key in before_entries.keys() | after_entries.keys():
        before = before_entries.get(key, [])
        after = after_entries.get(key, [])
        for ordinal in range(max(len(before), len(after))):
            if (before[ordinal] if ordinal < len(before) else None) != (
                after[ordinal] if ordinal < len(after) else None
            ):
                changed.add((key, ordinal))
    return changed


def evidence_source_paths(row):
    category = row["category"]
    input_path = row["input"]
    paths = [input_path]
    if category == "unrand":
        paths.extend([
            "crawl-ref/source/dat/i18n/zh/source.txt",
            "crawl-ref/source/dat/descript/unrand.txt",
            "crawl-ref/source/dat/descript/zh/unrand.txt",
        ])
    elif category == "unident":
        paths.append("crawl-ref/source/dat/descript/zh/unident.txt")
    elif category in {"appearance", "special"}:
        if input_path != "crawl-ref/source/zh-scroll-appearance.cc":
            paths.append("crawl-ref/source/dat/i18n/zh/source.txt")
    elif category in {"gizmo", "randart-component", "randart-grammar"}:
        paths.append(input_path.replace(
            "crawl-ref/source/dat/database/",
            "crawl-ref/source/dat/database/zh/",
        ))
    elif category == "item-description":
        paths.append("crawl-ref/source/dat/descript/zh/items.txt")
    return sorted(set(paths))


def conclusion_reason(row):
    conclusion = row["_conclusion"]
    changed_fields = []
    if row.get("_pre_review_chinese") != row.get("current_chinese"):
        changed_fields.append("display/component Chinese")
    metadata = row.get("_metadata", {})
    if (
        metadata.get("description_pre_review_chinese")
        != metadata.get("description_current_chinese")
    ):
        changed_fields.append("long-description Chinese")
    changed = ", ".join(changed_fields) or "no adopted semantic field"
    boundary = (
        f"{row['identity']} at {row['producer']} -> {row['consumer']}"
    )
    if conclusion == "keep":
        return (
            f"keep: {boundary} has {changed} differing from the review base; "
            "the adopted rendering preserves the accepted meaning, "
            "terminology, grammar identity, and gameplay-facing consumer."
        )
    if conclusion == "adjust":
        return (
            f"adjust: {boundary} changes {changed}; the candidate adopts that "
            "targeted wording or structural correction while preserving the "
            "same gameplay identity."
        )
    if conclusion == "retranslate":
        return (
            f"retranslate: {boundary} changes {changed}; the candidate "
            "replaces the review-base Chinese rendering to restore semantic "
            "or glossary fidelity."
        )
    if conclusion == "defer terminology":
        return (
            "defer terminology: no final wording is adopted until the "
            "terminology authority records a ruling."
        )
    if conclusion == "defer implementation":
        return (
            "defer implementation: the wording cannot safely land until the "
            "display/identity implementation boundary is repaired."
        )
    raise RuntimeError(
        f"unsupported terminal conclusion for {row['identity']}: {conclusion}"
    )


def build_source_evidence(rows, review_base):
    relative_paths = sorted({
        relative
        for row in rows
        for relative in evidence_source_paths(row)
    })
    result = {}
    for relative in relative_paths:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(
                f"required candidate evidence input is missing: {relative}"
            )
        result[relative] = {
            "path": relative,
            "review_base_sha256": sha_bytes(
                git_revision_bytes(path, review_base)
            ),
            "current_sha256": sha(path),
        }
    return result


def evidence_card(row, source_evidence):
    source_files = []
    for relative in evidence_source_paths(row):
        source_files.append(source_evidence[relative])
    metadata = {
        "category": row["category"],
        **row.get("_metadata", {}),
    }
    return {
        "identity": row["identity"],
        "lifecycle": row["lifecycle"],
        "english_source": row["english_source"],
        "pre_review_chinese": row.get("_pre_review_chinese"),
        "current_chinese": row["current_chinese"],
        "adopted_english": row["english_source"],
        "adopted_chinese": row["current_chinese"],
        "producer": row["producer"],
        "consumer": row["consumer"],
        "metadata": metadata,
        "input": row["input"],
        "source_files": source_files,
        "terminal_conclusion": row["_conclusion"],
        "semantic_reason": conclusion_reason(row),
        "reentry_trigger": (
            "Re-review if the English source, adopted Chinese, lifecycle, "
            "producer/consumer, glossary, grammar metrics, or source SHA "
            "changes."
        ),
    }


def build_extended_inventory(review_base=ISSUE29_REVIEW_BASE):
    review_base = resolve_commit(review_base)
    candidate_head = resolve_commit("HEAD")
    ordinary = build_inventory()
    source_db = source_entries(ZH_SOURCE_DIR)
    base_source_db = source_entries_at_revision(
        ZH_SOURCE_DIR, review_base
    )
    description_en = SRC / "dat/descript/items.txt"
    description_zh = SRC / "dat/descript/zh/items.txt"
    unident_en = SRC / "dat/descript/unident.txt"
    unident_zh = SRC / "dat/descript/zh/unident.txt"
    desc_db = {
        entry.canonical_key: runtime_normalize_value(entry.value)
        for entry in textdb_rows(SRC / "dat/descript/zh/unrand.txt")
    }
    base_desc_db = {
        entry.canonical_key: runtime_normalize_value(entry.value)
        for entry in revision_textdb_rows(
            SRC / "dat/descript/zh/unrand.txt", review_base
        )
    }

    rows = []
    rows.extend(unrand_rows(
        desc_db, source_db, base_desc_db, base_source_db, review_base
    ))

    changed_unident = changed_textdb_keys(unident_zh, review_base)
    en_unident = {e.canonical_key: e for e in textdb_rows(unident_en)}
    zh_unident = {e.canonical_key: e for e in textdb_rows(unident_zh)}
    base_zh_unident = {
        e.canonical_key: e
        for e in revision_textdb_rows(unident_zh, review_base)
    }
    if en_unident.keys() != zh_unident.keys() or len(en_unident) != 7:
        raise RuntimeError("unident EN/ZH key inventory drift")
    for key in sorted(en_unident):
        rows.append({
            "identity": f"unident:{key}",
            "category": "unident",
            "lifecycle": "current",
            "english_source": runtime_normalize_value(en_unident[key].value),
            "_pre_review_chinese": runtime_normalize_value(
                base_zh_unident[key].value
            ),
            "current_chinese": runtime_normalize_value(zh_unident[key].value),
            "producer": f"DescriptionDB key {key}",
            "consumer": "unidentified item description",
            "input": str(unident_en.relative_to(ROOT)),
            "_metadata": {"description_key": key},
            "_conclusion": (
                "retranslate" if key in changed_unident else "keep"
            ),
        })

    rows.extend(unidentified_appearance_rows(source_db, base_source_db))
    rows.extend(special_item_rows(source_db, base_source_db))

    gizmo_en = SRC / "dat/database/gizmo.txt"
    gizmo_zh = SRC / "dat/database/zh/gizmo.txt"
    rows.extend(paired_component_rows(
        gizmo_en, gizmo_zh, "gizmo", review_base,
        changed_physical_ordinals(gizmo_zh, review_base),
    ))

    en_items = {e.canonical_key: e for e in textdb_rows(description_en)}
    zh_items = {e.canonical_key: e for e in textdb_rows(description_zh)}
    base_zh_items = {
        e.canonical_key: e
        for e in revision_textdb_rows(description_zh, review_base)
    }
    allowed_zh_extra = {"athame"}
    if set(en_items) - set(zh_items) or set(zh_items) - set(en_items) != (
        allowed_zh_extra
    ):
        raise RuntimeError(
            "ordinary description EN/ZH key mismatch outside explicit "
            "athame compatibility key"
        )
    changed_items = changed_textdb_keys(description_zh, review_base)
    for key in sorted(en_items):
        rows.append({
            "identity": f"item-description:{key}",
            "category": "item-description",
            "lifecycle": "current",
            "english_source": runtime_normalize_value(en_items[key].value),
            "_pre_review_chinese": runtime_normalize_value(
                base_zh_items[key].value
            ),
            "current_chinese": runtime_normalize_value(zh_items[key].value),
            "producer": f"DescriptionDB key {key}",
            "consumer": "item_def::name(DESC_DBNAME) -> getLongDescription",
            "input": str(description_en.relative_to(ROOT)),
            "_metadata": {"description_key": key},
            "_conclusion": "adjust" if key in changed_items else "keep",
        })

    randart_files = [
        "randname.txt", "rand_wpn.txt", "rand_arm.txt", "rand_all.txt"
    ]
    randart_metrics = {}
    for filename in randart_files:
        en_randart = textdb_rows(SRC / "dat/database" / filename)
        zh_randart = textdb_rows(SRC / "dat/database/zh" / filename)
        randart_metrics[filename] = validate_randart_metrics(
            filename, en_randart, zh_randart
        )
        component_rows = paired_component_rows(
            SRC / "dat/database" / filename,
            SRC / "dat/database/zh" / filename,
            "randart-component", review_base,
        )
        rows.extend(component_rows)
        for entry in en_randart:
            rows.append({
                "identity": f"randart-grammar:{filename}:{entry.canonical_key}",
                "category": "randart-grammar",
                "lifecycle": "current",
                "english_source": entry.raw_key,
                "_pre_review_chinese": entry.raw_key,
                "current_chinese": entry.raw_key,
                "producer": f"RandartDB key {entry.raw_key}",
                "consumer": (
                    "make_artefact_name recursive grammar; final string "
                    "is intentionally non-enumerable and opaque display"
                ),
                "input": f"crawl-ref/source/dat/database/{filename}",
                "_metadata": {
                    "grammar_file": filename,
                    "grammar_key": entry.canonical_key,
                },
                "_conclusion": "keep",
            })

    identities = [row["identity"] for row in rows]
    duplicates = sorted(
        identity for identity, count in Counter(identities).items()
        if count > 1
    )
    counts = Counter(row["category"] for row in rows)
    expected_counts = {
        "unrand": 142,
        "unident": 7,
        "appearance": 186,
        "special": 23,
        "gizmo": 539,
        "item-description": 307,
        "randart-component": 2440,
        "randart-grammar": 115,
    }
    if dict(counts) != expected_counts:
        raise RuntimeError(
            f"Issue 29 category inventory drift: {dict(counts)}"
        )
    unrand_zh = {
        entry.canonical_key
        for entry in textdb_rows(SRC / "dat/descript/zh/unrand.txt")
    }
    unrand_en = {
        entry.canonical_key
        for entry in textdb_rows(SRC / "dat/descript/unrand.txt")
    }
    allowed_unrand_extra = {
        'athame "fimbulwinter"',
        "fire dragon occultist's scales",
        "ice dragon arcanist's scales",
        "swamp witch's dragon scales",
    }
    if unrand_zh - unrand_en != allowed_unrand_extra:
        raise RuntimeError("unrand compatibility key classification drift")

    source_evidence = build_source_evidence(rows, review_base)
    public_rows = [evidence_card(row, source_evidence) for row in rows]
    digest = hashlib.sha256(json.dumps(
        public_rows, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"),
    ).encode()).hexdigest()
    input_paths = [
        SRC / "art-data.txt", SRC / "item-name.cc",
        SRC / "zh-scroll-appearance.cc", unident_en, unident_zh,
        description_en, description_zh,
        ZH_SOURCE,
        SRC / "dat/descript/unrand.txt",
        SRC / "dat/descript/zh/unrand.txt",
        gizmo_en, gizmo_zh,
        *[
            SRC / "dat/database" / filename
            for filename in randart_files
        ],
        *[
            SRC / "dat/database/zh" / filename
            for filename in randart_files
        ],
    ]
    current_input_sha = {
        str(path.relative_to(ROOT)): sha(path) for path in input_paths
    }
    review_base_input_sha = {
        str(path.relative_to(ROOT)): sha_bytes(
            git_revision_bytes(path, review_base)
        )
        for path in input_paths
    }
    randart_totals = {
        key: sum(metrics[key] for metrics in randart_metrics.values())
        for key in [
            "grammar_keys", "physical_variant_identities",
            "raw_nonempty_grammar_lines", "explicit_weight_marker_lines",
            "continuation_lines", "weight_mass",
        ]
    }
    expected_randart_totals = {
        "grammar_keys": 115,
        "physical_variant_identities": 2440,
        "raw_nonempty_grammar_lines": 2734,
        "explicit_weight_marker_lines": 293,
        "continuation_lines": 1,
        "weight_mass": 27304,
    }
    if randart_totals != expected_randart_totals:
        raise RuntimeError(
            f"randart aggregate metric drift: {randart_totals}"
        )
    payload = {
        "schema": "dcss-item-extended-review-inventory-v2",
        "baseline": review_base,
        "candidate_head": candidate_head,
        "glossary_sha256": sha(ROOT / "docs/glossary.md"),
        "ordinary_v1": {
            "schema": ordinary["schema"],
            "count": ordinary["count"],
            "inventory_sha256": ordinary["inventory_sha256"],
            "category_counts": ordinary["category_counts"],
        },
        "input_sha256": {
            "review_base": review_base_input_sha,
            "current": current_input_sha,
        },
        "scope": {
            "lifecycle": {
                "unrand": "121 current / 19 compatibility / 2 internal",
                "all_other_rows": "current unless explicitly stated",
            },
            "excluded": [
                "procedural final randart strings",
                "procedural final unidentified appearance combinations",
                "procedural final gizmo serial/name combinations",
            ],
            "exclusion_reason": (
                "runtime names depend on weighted recursion, player/world "
                "inputs, pseudo-words, serials, or combinatorial assembly; "
                "finite keys, physical ordinals, tokens and grammar are frozen"
            ),
            "randart_cache_audit": {
                "ARTEFACT_NAME_KEY": (
                    "opaque display cache consumed by get_artefact_name and "
                    "item_def::name; stable gameplay identity remains "
                    "base_type/sub_type/artefact properties"
                ),
                "ARTEFACT_APPEAR_KEY": (
                    "opaque unidentified display cache; no TextDB/protocol "
                    "reverse lookup consumer"
                ),
            },
            "randart_component_metrics": {
                "definition": {
                    "physical_variant_identities": (
                        "production blank-line weighted variants; these 2440 "
                        "objects are the review identities"
                    ),
                    "raw_nonempty_grammar_lines": (
                        "all non-comment, non-empty grammar lines; the plan's "
                        "2734 includes 293 w:N lines and one continuation line"
                    ),
                },
                "per_file": randart_metrics,
                "totals": randart_totals,
            },
            "ordinary_description_slots": {
                "count": ordinary["count"],
                "mapping": [
                    {
                        "identity": row["identity"],
                        "dbname_key": row["english_source_name"],
                        "lifecycle": row["lifecycle"],
                    }
                    for row in ordinary["rows"]
                ],
            },
            "compatibility_key_exceptions": {
                "items_zh_only": sorted(allowed_zh_extra),
                "unrand_zh_only": sorted(allowed_unrand_extra),
            },
        },
        "count": len(public_rows),
        "category_counts": expected_counts,
        "duplicates": duplicates,
        "inventory_sha256": digest,
        "development_reports": DEVELOPMENT_REPORTS,
        "rows": public_rows,
    }
    return payload, public_rows


TERMINAL_CONCLUSIONS = {
    "keep", "adjust", "retranslate",
    "defer terminology", "defer implementation",
}
REQUIRED_CARD_FIELDS = {
    "identity", "lifecycle", "english_source", "pre_review_chinese",
    "current_chinese", "adopted_english", "adopted_chinese", "producer",
    "consumer", "metadata", "input", "source_files",
    "terminal_conclusion", "semantic_reason", "reentry_trigger",
}
REVIEW_ARTIFACT_BEGIN = "<!-- BEGIN ITEM REVIEW ARTIFACT v1 -->"
REVIEW_ARTIFACT_END = "<!-- END ITEM REVIEW ARTIFACT v1 -->"


def parse_review_results(review_input):
    rows = []
    in_cards = False
    saw_cards = False
    for line_number, line in enumerate(
        review_input.text.splitlines(), start=1
    ):
        if line == "```jsonl":
            if in_cards or saw_cards:
                raise RuntimeError("duplicate evidence-card JSONL block")
            in_cards = True
            saw_cards = True
            continue
        if in_cards and line == "```":
            in_cards = False
            continue
        if not in_cards:
            continue
        if not line:
            raise RuntimeError(
                f"blank evidence-card line at {line_number}"
            )
        try:
            row = json.loads(line)
        except json.JSONDecodeError as error:
            raise RuntimeError(
                f"invalid evidence-card JSON at line {line_number}"
            ) from error
        if not isinstance(row, dict):
            raise RuntimeError(
                f"evidence card at line {line_number} is not an object"
            )
        rows.append(row)
    if in_cards:
        raise RuntimeError("unterminated evidence-card JSONL block")
    if not saw_cards:
        raise RuntimeError("evidence-card JSONL block is missing")
    return rows


def parse_review_header(review_input):
    text = review_input.text
    patterns = {
        "inventory_sha256": r"^- Inventory SHA-256: `([0-9a-f]{64})`$",
        "glossary_sha256": r"^- Glossary SHA-256: `([0-9a-f]{64})`$",
        "baseline": r"^- Review base: `([0-9a-f]{40})`$",
        "count": r"^- Inventory rows: `([0-9]+)`$",
    }
    result = {}
    for field, pattern in patterns.items():
        matches = re.findall(pattern, text, re.MULTILINE)
        result[field] = matches[0] if len(matches) == 1 else None
        result[field + "_header_count"] = len(matches)
    if result["count"] is not None:
        result["count"] = int(result["count"])
    return result


def review_violations(
    inventory_rows,
    review_rows,
    inventory=None,
    header=None,
    review_input=None,
):
    inventory_ids = [
        row.get("identity", "<missing>") for row in inventory_rows
    ]
    review_ids = [row.get("identity", "<missing>") for row in review_rows]
    inventory_set = set(inventory_ids)
    review_set = set(review_ids)
    missing_required = sorted(
        f"{row.get('identity', '<missing>')}:{field}"
        for row in review_rows
        for field in REQUIRED_CARD_FIELDS - set(row)
    )
    invalid_terminal = sorted(
        row.get("identity", "<missing>") for row in review_rows
        if row.get("terminal_conclusion") not in TERMINAL_CONCLUSIONS
    )
    invalid_deferral = sorted(
        row.get("identity", "<missing>") for row in review_rows
        if str(row.get("terminal_conclusion", "")).startswith("defer ")
        and (
            not row.get("semantic_reason")
            or row.get("semantic_reason") == "not applicable"
            or not row.get("reentry_trigger")
            or row.get("reentry_trigger") == "not applicable"
        )
    )
    inventory_by_id = {
        row["identity"]: row for row in inventory_rows
        if "identity" in row
    }
    review_by_id = {
        row["identity"]: row for row in review_rows
        if "identity" in row
    }
    mismatched = sorted(
        identity for identity in inventory_set & review_set
        if inventory_by_id.get(identity) != review_by_id.get(identity)
    )
    violations = {
        "inventory_duplicates": sorted(
            key for key, count in Counter(inventory_ids).items() if count > 1
        ),
        "review_duplicates": sorted(
            key for key, count in Counter(review_ids).items() if count > 1
        ),
        "inventory_minus_review": sorted(inventory_set - review_set),
        "review_minus_inventory": sorted(review_set - inventory_set),
        "missing_required_fields": missing_required,
        "mismatched_evidence_cards": mismatched,
        "invalid_terminal_conclusions": invalid_terminal,
        "invalid_deferrals": invalid_deferral,
    }
    if inventory is not None:
        header = header or {}
        expected_header = {
            "inventory_sha256": inventory["inventory_sha256"],
            "glossary_sha256": inventory["glossary_sha256"],
            "baseline": inventory["baseline"],
            "count": inventory["count"],
        }
        violations["header_mismatches"] = sorted(
            field for field, expected in expected_header.items()
            if header.get(field) != expected
            or header.get(field + "_header_count") != 1
        )
        if review_input is not None:
            violations["artifact_mismatch"] = (
                []
                if review_input.text == render_review_results(
                    inventory, review_rows
                )
                else ["review artifact is not the exact canonical rendering"]
            )
    return violations


def review_artifact_summary(inventory, rows):
    counts = Counter(row["terminal_conclusion"] for row in rows)
    metrics = inventory["scope"]["randart_component_metrics"]["totals"]
    return {
        "baseline": inventory["baseline"],
        "glossary_sha256": inventory["glossary_sha256"],
        "inventory_count": inventory["count"],
        "inventory_sha256": inventory["inventory_sha256"],
        "randart_production_boundary": metrics,
        "terminal_conclusion_counts": dict(sorted(counts.items())),
    }


def render_review_results(inventory, rows):
    summary = json.dumps(
        review_artifact_summary(inventory, rows),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    lines = [
        "# Item translation review",
        "",
        REVIEW_ARTIFACT_BEGIN,
        summary,
        REVIEW_ARTIFACT_END,
        "",
        f"- Inventory SHA-256: `{inventory['inventory_sha256']}`",
        f"- Glossary SHA-256: `{inventory['glossary_sha256']}`",
        f"- Review base: `{inventory['baseline']}`",
        f"- Inventory rows: `{inventory['count']}`",
        "",
        "## Evidence cards",
        "",
        "```jsonl",
    ]
    for row in rows:
        lines.append(json.dumps(
            row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ))
    lines.append("```")
    return "\n".join(lines) + "\n"


def write_review_results(path, inventory, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_review_results(inventory, rows),
        encoding="utf-8",
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="write the full JSON inventory to this path (default: stdout)",
    )
    parser.add_argument(
        "--scope",
        choices=("ordinary-v1", "issue29-v2"),
        default="ordinary-v1",
        help="select the isolated inventory boundary (default: ordinary-v1)",
    )
    parser.add_argument(
        "--review-base",
        help=(
            "target commit for issue29-v2 before/after evidence "
            f"(default: {ISSUE29_REVIEW_BASE})"
        ),
    )
    parser.add_argument(
        "--review-results",
        type=Path,
        help="validate exact Issue 29 inventory/review identity coverage",
    )
    parser.add_argument(
        "--write-review-results",
        type=Path,
        help="mechanically write Issue 29 evidence cards",
    )
    args = parser.parse_args(argv)

    try:
        if args.scope == "issue29-v2":
            payload, internal_rows = build_extended_inventory(
                args.review_base or ISSUE29_REVIEW_BASE
            )
            if args.write_review_results:
                write_review_results(
                    args.write_review_results, payload, internal_rows
                )
            if args.review_results:
                review_input = load_review_input(ROOT, args.review_results)
                payload["review_input"] = review_input_metadata(review_input)
                review = parse_review_results(review_input)
                review_header = parse_review_header(review_input)
                payload["review_violations"] = review_violations(
                    payload["rows"],
                    review,
                    payload,
                    review_header,
                    review_input,
                )
        else:
            if (
                args.review_results or args.write_review_results
                or args.review_base
            ):
                raise RuntimeError(
                    "review options are valid only for --scope issue29-v2"
                )
            payload = build_inventory()
    except (
        AttributeError,
        OSError,
        KeyError,
        RuntimeError,
        ValueError,
        subprocess.SubprocessError,
    ) as error:
        print(f"ERROR: item-name inventory could not be built: {error}",
              file=sys.stderr)
        return 2

    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)

    summary = {key: payload[key] for key in [
        "baseline", "candidate_head", "glossary_sha256",
        "inventory_sha256", "count",
        "category_counts", "duplicates", "missing_identities",
        "unexpected_identities", "missing_chinese", "missing_forms",
    ] if key in payload}
    if "review_violations" in payload:
        summary["review_violations"] = payload["review_violations"]
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    blocking_keys = (
        "duplicates", "missing_identities", "unexpected_identities",
        "missing_chinese", "missing_forms",
    )
    blocked = any(payload.get(key) for key in blocking_keys)
    if "review_violations" in payload:
        blocked = blocked or any(payload["review_violations"].values())
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
