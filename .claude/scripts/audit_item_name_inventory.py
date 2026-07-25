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

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "crawl-ref/source"
ZH_SOURCE = SRC / "dat/i18n/zh/source.txt"
ZH_SOURCE_DIR = ZH_SOURCE.parent

sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_shared import parse_entries_physical, runtime_normalize_value


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
            if frame["tag"] and condition is not None:
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
        forms = {"verbose": verbose[value], "terse": terse[value], "adj": adj[value]}
        rows.append({
            "identity": f"weapon_brand:{identity}",
            "category": "weapon_brand",
            "lifecycle": (
                "compatibility" if forms["verbose"] == "obsolescence"
                else "internal" if identity == "SPWPN_CONFUSE"
                else "current"
            ),
            "english_source_name": forms["verbose"],
            "translation_key": forms["verbose"],
            "current_chinese_name": db.get(forms["verbose"].lower(),
                                           forms["verbose"]),
            "translation_present": forms["verbose"].lower() in db,
            "runtime_lookup": True,
            "forms": {
                form: {"en": key, "zh": db.get(key.lower())}
                for form, key in forms.items()
            },
        })

    # Armour ego: verbose and terse forms share an enum identity.
    # Split the two branches explicitly to avoid the generic parser replacing
    # verbose cases with terse cases.
    tr_body = function_body(item_name, "special_armour_type_name")
    def branch_cases(body, marker):
        part = body.split(marker, 1)[0] if marker else body
        return {
            identity: literal
            for identity, literal in re.findall(
                r"case\s+(SPARM_[A-Z0-9_]+)\s*:\s*return\s+T_?\(\"([^\"]+)\"\)\s*;",
                part,
            )
        }
    tr_verbose_part = tr_body.split("else", 1)[0]
    tr_terse_part = tr_body.split("else", 1)[1]
    tr_verbose = branch_cases(tr_verbose_part, None)
    tr_terse = branch_cases(tr_terse_part, None)
    for compatibility_identity in (
        "SPARM_RUNNING", "SPARM_JUMPING", "SPARM_CLOUD_IMMUNE"
    ):
        tr_verbose[compatibility_identity] = "obsolescence"
        tr_terse[compatibility_identity] = "obsolete"
    en_verbose = tr_verbose
    en_terse = tr_terse
    for identity in sorted(en_verbose):
        forms = {
            "verbose": en_verbose[identity],
            "terse": en_terse.get(identity),
        }
        rows.append({
            "identity": f"armour_ego:{identity}",
            "category": "armour_ego",
            "lifecycle": (
                "compatibility" if forms["verbose"] == "obsolescence"
                else "current"
            ),
            "english_source_name": forms["verbose"],
            "translation_key": forms["verbose"],
            "current_chinese_name": db.get(forms["verbose"].lower(),
                                           forms["verbose"]),
            "translation_present": forms["verbose"].lower() in db,
            "runtime_lookup": True,
            "forms": {
                form: {"en": key, "zh": db.get(key.lower()) if key else None}
                for form, key in forms.items()
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


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="write the full JSON inventory to this path (default: stdout)",
    )
    args = parser.parse_args(argv)

    try:
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
        "baseline", "glossary_sha256", "inventory_sha256", "count",
        "category_counts", "duplicates", "missing_identities",
        "unexpected_identities", "missing_chinese", "missing_forms",
    ]}
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    return 1 if any(
        payload[key] for key in
        (
            "duplicates", "missing_identities", "unexpected_identities",
            "missing_chinese", "missing_forms",
        )
    ) else 0


if __name__ == "__main__":
    sys.exit(main())
