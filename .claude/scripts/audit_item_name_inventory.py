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
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

SCRIPT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_shared import (  # noqa: E402
    AuditInputError,
    AuditRootError,
    AuditSnapshot,
    audit_snapshot_invocation,
    get_audit_snapshot,
    resolve_audit_root,
    trusted_git_environment,
)

try:
    ROOT = resolve_audit_root(SCRIPT_ROOT)
except AuditRootError as error:
    print(f"ERROR: invalid audit root: {error}", file=sys.stderr)
    raise SystemExit(2)

SRC = ROOT / "crawl-ref/source"
ZH_SOURCE = SRC / "dat/i18n/zh/source.txt"
ZH_SOURCE_DIR = ZH_SOURCE.parent
ISSUE29_REVIEW_BASE = "01dc9911ec9948aff661f6ec0b9b0a798fcf909d"
QUALITY_M1_RUN_ID = "m1-item-description-v1"
QUALITY_M1_SEED = "dcss-zh-quality-m0-item-description-v1"
QUALITY_M1_REVIEW_BASE_ADJUST_COUNT = 6
QUALITY_M1_ADOPTED_ADJUST_COUNT = 4
QUALITY_M1_ADOPTED_KEEP_COUNT = 6
QUALITY_M1_SHARD_SIZE = 4
QUALITY_M1_OUTPUT_ROOT = ROOT / ".artifacts/i18n/quality"
QUALITY_M1_FORBIDDEN_EVALUATOR_FIELDS = frozenset({
    "adopted_chinese",
    "expected_correction_chinese",
    "historical_expected_severity",
    "pre_review_chinese",
    "revision_kind",
    "semantic_reason",
    "terminal_conclusion",
})

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
ITEM_PRODUCER_CONSUMER_EVIDENCE = (
    (
        "Fixed artefact descriptions and quotes query TextDB with "
        "`get_unrand_name_en()`; localized true names remain display-only."
    ),
    (
        "Gizmos persist canonical English `ARTEFACT_NAME_KEY` plus a finite "
        "recursive physical-ordinal recipe. Current-locale rendering uses "
        "zero RNG; old saves without a recipe retain their old opaque display "
        "string as a safe fallback."
    ),
    (
        "Randart `ARTEFACT_NAME_KEY` and `ARTEFACT_APPEAR_KEY` are opaque "
        "display caches. Their consumers do not reverse-map them to gameplay "
        "identity; base/subtype and artefact properties remain authoritative."
    ),
)
DEVELOPMENT_NON_OVERWRITE_STATEMENT = (
    "所有失败与告警均保留在上述原始报告中；"
    "失败的开发运行未被后续通过记录覆盖或删除。"
)

from i18n_shared import (
    compute_canonical_key,
    i18n_escape_key,
    load_review_input,
    parse_entries_physical,
    review_input_metadata,
    runtime_normalize_value,
)


def audit_snapshot():
    return get_audit_snapshot(ROOT)


def sha(path, snapshot=None):
    return (snapshot or audit_snapshot()).sha256(
        path, allow_external_unbound=True
    )


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def resolve_commit(revision, root=ROOT):
    if not revision:
        raise RuntimeError("review base is required")
    try:
        return subprocess.check_output(
            [
                "git", "-C", str(root), "rev-parse", "--verify",
                f"{revision}^{{commit}}",
            ],
            text=True,
            stderr=subprocess.PIPE,
            env=trusted_git_environment(),
        ).strip()
    except subprocess.CalledProcessError as error:
        raise RuntimeError(f"invalid review base: {revision}") from error


_REVISION_SNAPSHOTS = {}


def revision_snapshot(revision, root=ROOT):
    """Return one cached immutable snapshot for an exact historical commit."""
    resolved = resolve_commit(revision, root)
    repository = Path(root).resolve()
    key = (os.fspath(repository), resolved)
    snapshot = _REVISION_SNAPSHOTS.get(key)
    if snapshot is None:
        snapshot = AuditSnapshot(
            repository, resolved, require_head=False
        )
        _REVISION_SNAPSHOTS[key] = snapshot
    return snapshot


def git_revision_bytes(path, revision, root=ROOT):
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as error:
        raise RuntimeError(f"path is outside review repository: {path}") from error
    try:
        return revision_snapshot(revision, root).bytes(relative)
    except (AuditInputError, RuntimeError, ValueError) as error:
        raise RuntimeError(
            f"required review-base input is missing: {revision}:{relative}"
        ) from error


def git_revision_text(path, revision, root=ROOT):
    try:
        return git_revision_bytes(path, revision, root).decode(
            "utf-8", errors="strict"
        )
    except UnicodeDecodeError as error:
        raise RuntimeError(
            f"review-base input is not UTF-8: {revision}:{path}"
        ) from error


def source_files(directory, snapshot=None):
    """Return localized SourceDB inputs in the production load order."""
    active = snapshot or audit_snapshot()
    source = Path(os.path.abspath(os.fspath(directory))) / "source.txt"
    files = list(active.glob(
        directory,
        "*.txt",
        allow_external_unbound=True,
    ))
    source_file = next(
        (path for path in files if path.name == "source.txt"),
        None,
    )
    if source_file is None:
        raise FileNotFoundError(f"required SourceDB input is missing: {source}")
    files.sort(key=lambda path: path.name)
    return [
        source_file,
        *(path for path in files if path != source_file),
    ]


def source_entries(directory, snapshot=None):
    # Localized SourceDB loads source.txt first, then every other sorted .txt
    # file with trim_keys=false. DBM_REPLACE makes the final exact canonical
    # key definition authoritative.
    active = snapshot or audit_snapshot()
    result = {}
    for path in source_files(directory, active):
        for entry in parse_entries_physical(active.read(
            path, allow_external_unbound=True
        )):
            result[entry.canonical_key] = runtime_normalize_value(entry.value)
    return result


def tag_major_version(snapshot=None):
    text = (snapshot or audit_snapshot()).text(
        SRC / "tag-version.h", allow_external_unbound=True
    )
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


def active_source(path, snapshot=None):
    """Select TAG_MAJOR_VERSION branches without preprocessing full Crawl.

    Full C++ preprocessing depends on generated build headers such as
    art-enum.h, which are intentionally absent in a fresh worktree. The item
    name producers only need their TAG_MAJOR_VERSION branches selected; other
    preprocessor conditions are left inclusive for the literal parser.
    """
    active_snapshot = snapshot or audit_snapshot()
    version = tag_major_version(active_snapshot)
    output = []
    stack = []
    active = True
    for line in active_snapshot.text(
        path, allow_external_unbound=True
    ).splitlines(keepends=True):
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


def enum_constants(headers, enum_names, snapshot=None):
    active = snapshot or audit_snapshot()
    source = "\n".join(f'#include "{header}"' for header in headers)
    with tempfile.TemporaryDirectory(prefix="dcss-item-audit-") as directory:
        include_root = Path(directory) / "include"
        include_root.mkdir()
        pending = list(dict.fromkeys([*headers, "tag-version.h"]))
        copied = set()
        while pending:
            header = pending.pop(0)
            if header in copied:
                continue
            if (
                Path(header).is_absolute()
                or ".." in Path(header).parts
            ):
                raise RuntimeError(
                    f"unsafe quoted include in enum probe: {header}"
                )
            payload = active.read(SRC / header)
            destination = include_root / header
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload.bytes)
            copied.add(header)
            for dependency in re.findall(
                r'(?m)^\s*#\s*include\s+"([^"]+)"',
                payload.text,
            ):
                pending.append(
                    (PurePosixPath(header).parent / dependency).as_posix()
                )
        probe = Path(directory) / "enums.cc"
        probe.write_text(source, encoding="utf-8")
        raw = subprocess.run(
            ["clang++", "-std=c++17", "-I", str(include_root),
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


@audit_snapshot_invocation(ROOT)
def build_inventory():
    snapshot = audit_snapshot()
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
        "baseline": snapshot.audit_commit or resolve_commit("HEAD"),
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
        "audit_snapshot": snapshot.metadata(),
    }
    encoded_rows = json.dumps(rows, ensure_ascii=False, sort_keys=True,
                              separators=(",", ":")).encode()
    payload["inventory_sha256"] = hashlib.sha256(encoded_rows).hexdigest()
    return payload


def textdb_rows(path, snapshot=None):
    active = snapshot or audit_snapshot()
    entries = parse_entries_physical(active.read(
        path, allow_external_unbound=True
    ))
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


def revision_textdb_rows(path, revision):
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError as error:
        raise RuntimeError(
            f"path is outside review repository: {path}"
        ) from error
    return parse_entries_physical(
        revision_snapshot(revision).read(relative)
    )


def source_entries_at_revision(directory, revision):
    try:
        relative = directory.relative_to(ROOT).as_posix()
    except ValueError as error:
        raise RuntimeError(
            f"SourceDB directory is outside review repository: {directory}"
        ) from error
    historical = revision_snapshot(revision)
    paths = sorted(
        historical.glob(relative, "*.txt"),
        key=lambda path: path.name,
    )
    source = historical.root / relative / "source.txt"
    if source not in paths:
        raise RuntimeError(
            f"required review-base SourceDB input is missing: "
            f"{revision}:{relative}/source.txt"
        )
    paths = [source, *(path for path in paths if path != source)]
    result = {}
    for path in paths:
        for entry in parse_entries_physical(historical.read(path)):
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


@audit_snapshot_invocation(ROOT)
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
        try:
            current_sha = sha(path)
        except AuditInputError as error:
            raise RuntimeError(
                f"required candidate evidence input is missing: {relative}"
            ) from error
        result[relative] = {
            "path": relative,
            "review_base_sha256": sha_bytes(
                git_revision_bytes(path, review_base)
            ),
            "current_sha256": current_sha,
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


def source_db_dependency_spec(row):
    """Return the localized SourceDB lookup made by one inventory row.

    The key and fallback mirror the row construction above.  A None return
    means that the row is not produced through localized SourceDB lookup.
    """
    category = row["category"]
    english = row["english_source"]
    if category == "unrand":
        context = None
    elif category == "appearance":
        if row["input"] == "crawl-ref/source/zh-scroll-appearance.cc":
            return None
        english = "" if english == "(empty component)" else english
        context = None
    elif category == "special":
        if str(row["identity"]).startswith("special:RUNE_"):
            context = "rune_name"
        else:
            context = None
    elif category != "unrand":
        return None
    candidates = []
    if context and english:
        runtime_key = f"{context}|{english}"
        escaped_key = i18n_escape_key(runtime_key)
        candidates.append({
            "branch": "context",
            "lookup_key": escaped_key,
            "canonical_key": compute_canonical_key(escaped_key),
        })
    if english:
        escaped_english = i18n_escape_key(english)
        candidates.append({
            "branch": "plain",
            "lookup_key": escaped_english,
            "canonical_key": compute_canonical_key(escaped_english),
        })
    return {
        "lookup_kind": "C_" if context else "T_",
        "context": context,
        "english": english,
        "candidates": candidates,
    }


def source_db_definition_chains(directory, requested_keys, snapshot=None):
    """Freeze complete production-ordered definitions for logical keys.

    Occurrence ordinals are scoped to one canonical key in one file.  They do
    not drift when an unrelated entry is inserted elsewhere in that file.
    File ordering is represented by the production rule and relative path,
    rather than a numeric whole-directory ordinal that unrelated files could
    shift.
    """
    active = snapshot or audit_snapshot()
    keys = sorted(set(requested_keys))
    chains = {key: [] for key in keys}
    key_set = set(keys)
    for path in source_files(directory, active):
        relative = path.relative_to(ROOT).as_posix()
        load_order = (
            "source.txt-first"
            if path.name == "source.txt"
            else f"sorted-txt:{path.name}"
        )
        occurrences = Counter()
        for entry in parse_entries_physical(active.read(
            path, allow_external_unbound=True
        )):
            key = entry.canonical_key
            if key not in key_set:
                continue
            ordinal = occurrences[key]
            occurrences[key] += 1
            chains[key].append({
                "canonical_key": key,
                "raw_key": entry.raw_key,
                "runtime_value": runtime_normalize_value(entry.value),
                "path": relative,
                "load_order": load_order,
                "occurrence_ordinal": ordinal,
                "winner": False,
            })
    for definitions in chains.values():
        if definitions:
            definitions[-1]["winner"] = True
    return chains


def source_db_dependency(spec, chains):
    """Resolve the production C_()/T_() candidate chain and EN fallback."""
    candidates = []
    selected = None
    for candidate_spec in spec["candidates"]:
        definitions = (
            [] if selected is not None
            else chains[candidate_spec["canonical_key"]]
        )
        winner_index = len(definitions) - 1 if definitions else None
        if selected is not None:
            candidate_state = "not-evaluated"
        elif definitions:
            value = definitions[-1]["runtime_value"]
            candidate_state = "empty" if value == "" else "value"
            if candidate_state == "value":
                selected = (candidate_spec["branch"], candidate_state, value)
        else:
            candidate_state = "missing"
        candidates.append({
            **candidate_spec,
            "state": candidate_state,
            "winner_index": winner_index,
            "definitions": definitions,
        })
    if selected is None:
        selected = ("english", "fallback", spec["english"])
    selected_branch, state, resolved = selected
    return {
        "schema": "dcss-localized-sourcedb-dependency-v1",
        "lookup_kind": spec["lookup_kind"],
        "context": spec["context"],
        "english": spec["english"],
        "candidates": candidates,
        "fallback": {
            "branch": "english",
            "runtime_value": spec["english"],
        },
        "selected_branch": selected_branch,
        "state": state,
        "resolved_value": resolved,
    }


V3_DECISION_FIELDS = (
    "lifecycle", "english_source", "pre_review_chinese",
    "current_chinese", "adopted_english", "adopted_chinese", "producer",
    "consumer", "metadata", "input", "terminal_conclusion",
    "semantic_reason", "reentry_trigger",
)


def v3_decision_cards(rows, v2_rows, source_directory=ZH_SOURCE_DIR,
                      snapshot=None):
    """Project candidate rows into canonical v3 decisions and dependencies."""
    v2_by_identity = {row["identity"]: row for row in v2_rows}
    if len(v2_by_identity) != len(v2_rows):
        raise RuntimeError("v3 decision projection has duplicate identities")
    specs = {
        row["identity"]: source_db_dependency_spec(row)
        for row in rows
    }
    chains = source_db_definition_chains(
        source_directory,
        (
            candidate["canonical_key"]
            for spec in specs.values() if spec is not None
            for candidate in spec["candidates"]
        ),
        snapshot=snapshot,
    )
    cards = []
    for row in rows:
        identity = row["identity"]
        try:
            source = v2_by_identity[identity]
        except KeyError as error:
            raise RuntimeError(
                f"v3 decision projection is missing v2 identity: {identity}"
            ) from error
        decision = {field: source[field] for field in V3_DECISION_FIELDS}
        decision["reentry_trigger"] = (
            "Re-review if this identity's logical source dependencies, "
            "decision fields, or glossary authority change."
        )
        spec = specs[identity]
        dependencies = []
        if spec is not None:
            dependency = source_db_dependency(spec, chains)
            dependencies.append(dependency)
            decision["english_source"] = dependency["english"]
            decision["adopted_english"] = dependency["english"]
            decision["current_chinese"] = dependency["resolved_value"]
            decision["adopted_chinese"] = dependency["resolved_value"]
        cards.append({
            "identity": identity,
            "decision": decision,
            "source_dependencies": dependencies,
        })
    return sorted(cards, key=lambda card: card["identity"])


def v3_decision_digest(rows):
    encoded = json.dumps(
        sorted(rows, key=lambda card: card["identity"]),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha_bytes(encoded)


@audit_snapshot_invocation(ROOT)
def build_extended_inventory(review_base=ISSUE29_REVIEW_BASE,
                             *, return_source_rows=False):
    snapshot = audit_snapshot()
    review_base = resolve_commit(review_base)
    historical = revision_snapshot(review_base)
    candidate_head = snapshot.audit_commit or resolve_commit("HEAD")
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
        "audit_snapshot": snapshot.metadata(),
        "review_base_snapshot": historical.metadata(),
    }
    if return_source_rows:
        return payload, public_rows, rows
    return payload, public_rows


@audit_snapshot_invocation(ROOT)
def build_extended_inventory_v3(review_base=ISSUE29_REVIEW_BASE):
    """Build the explicit transitional v3 decision inventory."""
    payload, public_rows, source_rows = build_extended_inventory(
        review_base, return_source_rows=True
    )
    v3_rows = v3_decision_cards(
        source_rows, public_rows, snapshot=audit_snapshot()
    )
    payload["schema"] = "dcss-item-extended-review-inventory-v3"
    payload["candidate_inventory_sha256"] = payload.pop("inventory_sha256")
    payload["rows"] = v3_rows
    payload["decision_inventory_sha256"] = v3_decision_digest(v3_rows)
    payload["inventory_sha256"] = payload["decision_inventory_sha256"]
    payload["input_manifest_sha256"] = payload["audit_snapshot"][
        "input_manifest_sha256"
    ]
    return payload, v3_rows


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
REVIEW_ARTIFACT_BEGIN = "<!-- BEGIN ITEM REVIEW ARTIFACT v2 -->"
REVIEW_ARTIFACT_END = "<!-- END ITEM REVIEW ARTIFACT v2 -->"


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
        "development_reports": inventory["development_reports"],
        "glossary_sha256": inventory["glossary_sha256"],
        "inventory_count": inventory["count"],
        "inventory_sha256": inventory["inventory_sha256"],
        "randart_production_boundary": metrics,
        "terminal_conclusion_counts": dict(sorted(counts.items())),
    }


def development_history_lines(inventory):
    reports = inventory.get("development_reports")
    if reports != DEVELOPMENT_REPORTS:
        raise RuntimeError(
            "item development report provenance differs from the canonical "
            "four-report history"
        )
    lines = [
        "## Producer / consumer implementation evidence",
        "",
        *(f"- {evidence}" for evidence in ITEM_PRODUCER_CONSUMER_EVIDENCE),
        "",
        "## Raw development reports",
        "",
    ]
    for report in reports:
        lines.append(
            f"- `{report['path']}` — profile={report['profile']}; "
            f"status={report['status']}; "
            f"blocking_failures={report['blocking_failures']}; "
            f"{report['note']}."
        )
    lines.extend(["", DEVELOPMENT_NON_OVERWRITE_STATEMENT, ""])
    return lines


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
        *development_history_lines(inventory),
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


V3_REVIEW_ARTIFACT_BEGIN = "<!-- BEGIN ITEM REVIEW ARTIFACT v3 -->"
V3_REVIEW_ARTIFACT_END = "<!-- END ITEM REVIEW ARTIFACT v3 -->"
V3_CARD_FIELDS = {"identity", "decision", "source_dependencies"}
V3_DECISION_FIELD_SET = set(V3_DECISION_FIELDS)
V3_DEPENDENCY_FIELDS = {
    "schema", "lookup_kind", "context", "english", "candidates",
    "fallback", "selected_branch", "state", "resolved_value",
}
V3_CANDIDATE_FIELDS = {
    "branch", "lookup_key", "canonical_key", "state", "winner_index",
    "definitions",
}
V3_DEFINITION_FIELDS = {
    "canonical_key", "raw_key", "runtime_value", "path", "load_order",
    "occurrence_ordinal", "winner",
}


def _canonical_relative_path(value, label):
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label} is not a canonical relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or ".." in path.parts:
        raise RuntimeError(f"{label} is not a canonical relative path")


def validate_v3_decision_cards(rows):
    """Fail closed on unknown, incomplete, or non-canonical v3 state."""
    if not isinstance(rows, list):
        raise RuntimeError("v3 evidence cards are not a list")
    identities = []
    for card_index, card in enumerate(rows):
        label = f"v3 card[{card_index}]"
        if not isinstance(card, dict) or set(card) != V3_CARD_FIELDS:
            raise RuntimeError(f"{label} has unknown or missing fields")
        identity = card["identity"]
        if not isinstance(identity, str) or not identity:
            raise RuntimeError(f"{label} identity is invalid")
        identities.append(identity)
        decision = card["decision"]
        if (
            not isinstance(decision, dict)
            or set(decision) != V3_DECISION_FIELD_SET
        ):
            raise RuntimeError(
                f"{identity} decision has unknown or missing fields"
            )
        if decision["terminal_conclusion"] not in TERMINAL_CONCLUSIONS:
            raise RuntimeError(
                f"{identity} decision has invalid terminal conclusion"
            )
        if decision["reentry_trigger"] != (
            "Re-review if this identity's logical source dependencies, "
            "decision fields, or glossary authority change."
        ):
            raise RuntimeError(f"{identity} reentry trigger is not v3")
        if not isinstance(decision["metadata"], dict):
            raise RuntimeError(f"{identity} decision metadata is invalid")
        _canonical_relative_path(decision["input"], f"{identity} input")
        dependencies = card["source_dependencies"]
        if not isinstance(dependencies, list) or len(dependencies) > 1:
            raise RuntimeError(f"{identity} source dependencies are invalid")
        for dependency in dependencies:
            if (
                not isinstance(dependency, dict)
                or set(dependency) != V3_DEPENDENCY_FIELDS
                or dependency["schema"]
                != "dcss-localized-sourcedb-dependency-v1"
            ):
                raise RuntimeError(
                    f"{identity} dependency has unknown or missing fields"
                )
            lookup_kind = dependency["lookup_kind"]
            context = dependency["context"]
            english = dependency["english"]
            if (
                lookup_kind not in {"C_", "T_"}
                or not isinstance(english, str)
                or (
                    lookup_kind == "C_"
                    and (not isinstance(context, str) or not context)
                )
                or (lookup_kind == "T_" and context is not None)
            ):
                raise RuntimeError(f"{identity} lookup call is invalid")
            fallback = dependency["fallback"]
            if fallback != {
                "branch": "english", "runtime_value": english,
            }:
                raise RuntimeError(f"{identity} fallback is invalid")
            if (
                decision["english_source"] != english
                or decision["adopted_english"] != english
            ):
                raise RuntimeError(
                    f"{identity} decision does not match runtime English"
                )
            expected_candidates = []
            if context is not None and english:
                expected_candidates.append((
                    "context", i18n_escape_key(f"{context}|{english}")
                ))
            if english:
                expected_candidates.append((
                    "plain", i18n_escape_key(english)
                ))
            candidates = dependency["candidates"]
            if (
                not isinstance(candidates, list)
                or len(candidates) != len(expected_candidates)
            ):
                raise RuntimeError(f"{identity} lookup candidates are invalid")
            selected = None
            for candidate_index, (candidate, expected) in enumerate(zip(
                candidates, expected_candidates
            )):
                evaluated = selected is None
                expected_branch, expected_lookup_key = expected
                if (
                    not isinstance(candidate, dict)
                    or set(candidate) != V3_CANDIDATE_FIELDS
                    or candidate["branch"] != expected_branch
                    or candidate["lookup_key"] != expected_lookup_key
                    or candidate["canonical_key"]
                    != compute_canonical_key(expected_lookup_key)
                ):
                    raise RuntimeError(
                        f"{identity} lookup candidate is invalid"
                    )
                key = candidate["canonical_key"]
                definitions = candidate["definitions"]
                if not isinstance(definitions, list):
                    raise RuntimeError(f"{identity} definitions are invalid")
                per_file = Counter()
                order_keys = []
                for definition_index, definition in enumerate(definitions):
                    if (
                        not isinstance(definition, dict)
                        or set(definition) != V3_DEFINITION_FIELDS
                    ):
                        raise RuntimeError(
                            f"{identity} definition has unknown or missing fields"
                        )
                    if (
                        definition["canonical_key"] != key
                        or not isinstance(definition["raw_key"], str)
                        or compute_canonical_key(definition["raw_key"]) != key
                    ):
                        raise RuntimeError(
                            f"{identity} definition canonical key mismatch"
                        )
                    path = definition["path"]
                    _canonical_relative_path(
                        path,
                        f"{identity} candidate[{candidate_index}]"
                        f".definition[{definition_index}].path",
                    )
                    name = PurePosixPath(path).name
                    expected_load_order = (
                        "source.txt-first" if name == "source.txt"
                        else f"sorted-txt:{name}"
                    )
                    if definition["load_order"] != expected_load_order:
                        raise RuntimeError(
                            f"{identity} definition load order is invalid"
                        )
                    expected_ordinal = per_file[path]
                    if definition["occurrence_ordinal"] != expected_ordinal:
                        raise RuntimeError(
                            f"{identity} definition occurrence order is invalid"
                        )
                    per_file[path] += 1
                    if (
                        not isinstance(definition["runtime_value"], str)
                        or not isinstance(definition["winner"], bool)
                    ):
                        raise RuntimeError(
                            f"{identity} definition value is invalid"
                        )
                    order_keys.append((
                        0 if name == "source.txt" else 1,
                        "" if name == "source.txt" else name,
                        expected_ordinal,
                    ))
                if order_keys != sorted(order_keys):
                    raise RuntimeError(
                        f"{identity} definition chain is unordered"
                    )
                expected_winner = (
                    len(definitions) - 1 if definitions else None
                )
                if candidate["winner_index"] != expected_winner or [
                    index for index, definition in enumerate(definitions)
                    if definition["winner"]
                ] != ([] if expected_winner is None else [expected_winner]):
                    raise RuntimeError(f"{identity} winner is invalid")
                if not evaluated:
                    if definitions:
                        raise RuntimeError(
                            f"{identity} unevaluated candidate has definitions"
                        )
                    expected_state = "not-evaluated"
                elif definitions:
                    expected_value = definitions[-1]["runtime_value"]
                    expected_state = (
                        "empty" if expected_value == "" else "value"
                    )
                    if expected_state == "value":
                        selected = (
                            expected_branch, expected_state, expected_value
                        )
                else:
                    expected_state = "missing"
                if candidate["state"] != expected_state:
                    raise RuntimeError(
                        f"{identity} lookup candidate state is invalid"
                    )
            if selected is None:
                selected = ("english", "fallback", english)
            if (
                dependency["selected_branch"] != selected[0]
                or dependency["state"] != selected[1]
                or dependency["resolved_value"] != selected[2]
            ):
                raise RuntimeError(f"{identity} dependency state is invalid")
            if (
                decision["current_chinese"] != selected[2]
                or decision["adopted_chinese"] != selected[2]
            ):
                raise RuntimeError(
                    f"{identity} dependency does not match current or "
                    "adopted Chinese"
                )
    if len(set(identities)) != len(identities):
        raise RuntimeError("v3 evidence cards have duplicate identities")
    if identities != sorted(identities):
        raise RuntimeError("v3 evidence cards are not canonically ordered")


def parse_review_results_v3(review_input):
    text = review_input.text
    if (
        text.count(V3_REVIEW_ARTIFACT_BEGIN) != 1
        or text.count(V3_REVIEW_ARTIFACT_END) != 1
        or REVIEW_ARTIFACT_BEGIN in text
        or REVIEW_ARTIFACT_END in text
        or re.search(r"ITEM REVIEW ARTIFACT v(?!3\b)", text)
    ):
        raise RuntimeError("unknown or mixed item review schema")
    rows = parse_review_results(review_input)
    validate_v3_decision_cards(rows)
    return rows


def parse_review_header_v3(review_input):
    patterns = {
        "decision_inventory_sha256": (
            r"^- Decision inventory SHA-256: `([0-9a-f]{64})`$"
        ),
        "glossary_sha256": r"^- Glossary SHA-256: `([0-9a-f]{64})`$",
        "baseline": r"^- Review base: `([0-9a-f]{40})`$",
        "count": r"^- Decision rows: `([0-9]+)`$",
        "schema": r"^- Review schema: `(dcss-item-review-decisions-v3)`$",
    }
    result = {}
    for field, pattern in patterns.items():
        matches = re.findall(pattern, review_input.text, re.MULTILINE)
        result[field] = matches[0] if len(matches) == 1 else None
        result[field + "_header_count"] = len(matches)
    if result["count"] is not None:
        result["count"] = int(result["count"])
    return result


def review_violations_v3(inventory_rows, review_rows, inventory, header,
                         review_input=None):
    validate_v3_decision_cards(inventory_rows)
    validate_v3_decision_cards(review_rows)
    inventory_ids = [row["identity"] for row in inventory_rows]
    review_ids = [row["identity"] for row in review_rows]
    expected_header = {
        "decision_inventory_sha256": inventory[
            "decision_inventory_sha256"
        ],
        "glossary_sha256": inventory["glossary_sha256"],
        "baseline": inventory["baseline"],
        "count": inventory["count"],
        "schema": "dcss-item-review-decisions-v3",
    }
    violations = {
        "inventory_duplicates": sorted(
            key for key, count in Counter(inventory_ids).items() if count > 1
        ),
        "review_duplicates": sorted(
            key for key, count in Counter(review_ids).items() if count > 1
        ),
        "inventory_minus_review": sorted(set(inventory_ids) - set(review_ids)),
        "review_minus_inventory": sorted(set(review_ids) - set(inventory_ids)),
        "decision_mismatches": sorted(
            identity for identity, left, right in zip(
                inventory_ids, inventory_rows, review_rows
            ) if identity != right["identity"] or left != right
        ) if len(inventory_rows) == len(review_rows) else ["row-count"],
        "header_mismatches": sorted(
            field for field, expected in expected_header.items()
            if header.get(field) != expected
            or header.get(field + "_header_count") != 1
        ),
    }
    if review_input is not None:
        violations["artifact_mismatch"] = (
            [] if review_input.text == render_review_results_v3(
                inventory, review_rows
            ) else ["review artifact is not the exact canonical v3 rendering"]
        )
    return violations


def review_artifact_summary_v3(inventory, rows):
    return {
        "baseline": inventory["baseline"],
        "decision_inventory_sha256": inventory[
            "decision_inventory_sha256"
        ],
        "glossary_sha256": inventory["glossary_sha256"],
        "review_schema": "dcss-item-review-decisions-v3",
        "row_count": len(rows),
        "terminal_conclusion_counts": dict(sorted(Counter(
            row["decision"]["terminal_conclusion"] for row in rows
        ).items())),
    }


def render_review_results_v3(inventory, rows):
    validate_v3_decision_cards(rows)
    summary = json.dumps(
        review_artifact_summary_v3(inventory, rows),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    lines = [
        "# Item translation review decisions",
        "",
        V3_REVIEW_ARTIFACT_BEGIN,
        summary,
        V3_REVIEW_ARTIFACT_END,
        "",
        "- Review schema: `dcss-item-review-decisions-v3`",
        f"- Decision inventory SHA-256: `{inventory['decision_inventory_sha256']}`",
        f"- Glossary SHA-256: `{inventory['glossary_sha256']}`",
        f"- Review base: `{inventory['baseline']}`",
        f"- Decision rows: `{inventory['count']}`",
        "",
        "## Evidence cards",
        "",
        "```jsonl",
    ]
    lines.extend(json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) for row in rows)
    lines.append("```")
    return "\n".join(lines) + "\n"


def quality_m1_canonical_json_bytes(value):
    return (json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n").encode("utf-8")


def quality_m1_digest(data):
    return hashlib.sha256(data).hexdigest()


def quality_m1_read_input(path, label):
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"{label} must be a regular, non-symlink file")
    data = path.read_bytes()
    if not data:
        raise RuntimeError(f"{label} must not be empty")
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RuntimeError(f"{label} must be valid UTF-8") from error
    return data


def quality_m1_require_relative_path(value, label):
    if not isinstance(value, str) or not value:
        raise RuntimeError(f"{label} must be a non-empty relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != value
    ):
        raise RuntimeError(f"{label} is not a canonical relative path")


def quality_m1_population(inventory):
    required = {
        "baseline", "candidate_head", "category_counts",
        "glossary_sha256", "inventory_sha256", "review_input",
        "review_violations", "rows", "schema",
    }
    missing = sorted(required - set(inventory))
    if missing:
        raise RuntimeError(
            f"quality M1 inventory is missing fields: {missing}"
        )
    violations = inventory["review_violations"]
    if not isinstance(violations, dict) or any(violations.values()):
        raise RuntimeError(
            "quality M1 requires an exact, violation-free review artifact"
        )
    review_input = inventory["review_input"]
    if not isinstance(review_input, dict):
        raise RuntimeError("quality M1 review input metadata is invalid")
    review_input_sha = review_input.get("input_sha256")
    if not re.fullmatch(r"[0-9a-f]{64}", str(review_input_sha)):
        raise RuntimeError("quality M1 review input digest is invalid")
    rows = sorted(
        (
            row for row in inventory["rows"]
            if row.get("metadata", {}).get("category")
            == "item-description"
        ),
        key=lambda row: row["identity"],
    )
    expected_count = inventory["category_counts"].get("item-description")
    if expected_count != len(rows):
        raise RuntimeError(
            "quality M1 item-description population count mismatch"
        )
    identities = [row["identity"] for row in rows]
    if len(identities) != len(set(identities)):
        raise RuntimeError(
            "quality M1 item-description identities are not unique"
        )
    for row in rows:
        if set(row) != REQUIRED_CARD_FIELDS:
            missing_fields = sorted(REQUIRED_CARD_FIELDS - set(row))
            unknown_fields = sorted(set(row) - REQUIRED_CARD_FIELDS)
            raise RuntimeError(
                f"quality M1 evidence-card fields differ for "
                f"{row.get('identity')!r}: missing={missing_fields}, "
                f"unknown={unknown_fields}"
            )
        key = row["metadata"].get("description_key")
        if row["identity"] != f"item-description:{key}":
            raise RuntimeError(
                f"quality M1 description identity mismatch: "
                f"{row['identity']}"
            )
        if row["lifecycle"] != "current":
            raise RuntimeError(
                f"quality M1 unsupported lifecycle: {row['identity']}"
            )
        if row["adopted_english"] != row["english_source"]:
            raise RuntimeError(
                f"quality M1 English revision drift: {row['identity']}"
            )
        if row["current_chinese"] != row["adopted_chinese"]:
            raise RuntimeError(
                f"quality M1 adopted/current drift: {row['identity']}"
            )
        conclusion = row["terminal_conclusion"]
        changed = row["pre_review_chinese"] != row["adopted_chinese"]
        if conclusion not in {"adjust", "keep"}:
            raise RuntimeError(
                f"quality M1 unsupported terminal conclusion: "
                f"{row['identity']}={conclusion}"
            )
        if changed != (conclusion == "adjust"):
            raise RuntimeError(
                f"quality M1 conclusion/revision mismatch: "
                f"{row['identity']}"
            )
        for index, source in enumerate(row["source_files"]):
            quality_m1_require_relative_path(
                source.get("path"),
                f"{row['identity']} source_files[{index}].path",
            )
    identity_bytes = ("\n".join(identities) + "\n").encode("utf-8")
    return {
        "category": "item-description",
        "contract": "dcss-zh-quality-m1-population-v1",
        "identity_sha256": quality_m1_digest(identity_bytes),
        "inventory_schema": inventory["schema"],
        "inventory_sha256": inventory["inventory_sha256"],
        "item_count": len(rows),
        "items": rows,
        "review_base": inventory["baseline"],
        "review_input_sha256": review_input_sha,
    }


def quality_m1_rank(seed, pool, identity):
    return quality_m1_digest(
        f"{seed}|{pool}|{identity}".encode("utf-8")
    )


def quality_m1_selection(rows, seed=QUALITY_M1_SEED):
    adjust = sorted(
        (row for row in rows if row["terminal_conclusion"] == "adjust"),
        key=lambda row: (
            quality_m1_rank(seed, "adjust", row["identity"]),
            row["identity"],
        ),
    )
    keep = sorted(
        (row for row in rows if row["terminal_conclusion"] == "keep"),
        key=lambda row: (
            quality_m1_rank(seed, "keep", row["identity"]),
            row["identity"],
        ),
    )
    adjust_required = (
        QUALITY_M1_REVIEW_BASE_ADJUST_COUNT
        + QUALITY_M1_ADOPTED_ADJUST_COUNT
    )
    if len(adjust) < adjust_required:
        raise RuntimeError(
            "quality M1 has too few changed adjust revisions"
        )
    if len(keep) < QUALITY_M1_ADOPTED_KEEP_COUNT:
        raise RuntimeError("quality M1 has too few adopted keep revisions")
    selected = [
        (row, "review-base")
        for row in adjust[:QUALITY_M1_REVIEW_BASE_ADJUST_COUNT]
    ]
    selected.extend(
        (row, "adopted")
        for row in adjust[
            QUALITY_M1_REVIEW_BASE_ADJUST_COUNT:adjust_required
        ]
    )
    selected.extend(
        (row, "adopted")
        for row in keep[:QUALITY_M1_ADOPTED_KEEP_COUNT]
    )
    selected.sort(key=lambda item: (
        quality_m1_rank(
            seed,
            "order",
            f"{item[0]['identity']}|{item[1]}",
        ),
        item[0]["identity"],
    ))
    identities = [row["identity"] for row, _revision in selected]
    if len(identities) != len(set(identities)):
        raise RuntimeError(
            "quality M1 selected the same identity more than once"
        )
    return selected


def quality_m1_forbidden_fields(value, location="$identity"):
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_location = f"{location}.{key}"
            if key in QUALITY_M1_FORBIDDEN_EVALUATOR_FIELDS:
                found.append(child_location)
            found.extend(quality_m1_forbidden_fields(
                child, child_location
            ))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(quality_m1_forbidden_fields(
                child, f"{location}[{index}]"
            ))
    return found


def quality_m1_evaluator_bundle_digest(files, evaluator_files):
    payload = bytearray(b"dcss-zh-quality-m1-evaluator-bundle-v1\0")
    for name in evaluator_files:
        payload.extend(name.encode("utf-8"))
        payload.extend(b"\0")
        payload.extend(files[name])
        payload.extend(b"\0")
    return quality_m1_digest(bytes(payload))


def build_quality_m1_files(
    inventory,
    prompt_bytes,
    context_bytes,
    decisions_sha256,
    seed=QUALITY_M1_SEED,
):
    for data, label in (
        (prompt_bytes, "quality M1 prompt"),
        (context_bytes, "quality M1 context"),
    ):
        if not data:
            raise RuntimeError(f"{label} must not be empty")
        try:
            data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise RuntimeError(f"{label} must be valid UTF-8") from error
    if not re.fullmatch(r"[0-9a-f]{64}", str(decisions_sha256)):
        raise RuntimeError("quality M1 decisions digest is invalid")
    population = quality_m1_population(inventory)
    population_bytes = quality_m1_canonical_json_bytes(population)
    population_sha256 = quality_m1_digest(population_bytes)
    selected = quality_m1_selection(population["items"], seed)
    blind_items = []
    truth_items = []
    for ordinal, (row, revision_kind) in enumerate(selected, start=1):
        case_id = f"M0-{ordinal:03d}"
        chinese = (
            row["pre_review_chinese"]
            if revision_kind == "review-base"
            else row["adopted_chinese"]
        )
        blind_item = {
            "case_id": case_id,
            "chinese": chinese,
            "consumer": row["consumer"],
            "english": row["adopted_english"],
            "identity": row["identity"],
            "lifecycle": row["lifecycle"],
            "metadata": row["metadata"],
            "producer": row["producer"],
            "source_files": row["source_files"],
        }
        blind_items.append(blind_item)
        truth_item = {
            "case_id": case_id,
            "evaluated_chinese_sha256": quality_m1_digest(
                chinese.encode("utf-8")
            ),
            "historical_expected_severity": (
                "needs_fix"
                if revision_kind == "review-base"
                else "unadjudicated"
            ),
            "identity": row["identity"],
            "packet_item_sha256": quality_m1_digest(
                quality_m1_canonical_json_bytes(blind_item)
            ),
            "revision_kind": revision_kind,
            "semantic_reason": row["semantic_reason"],
            "terminal_conclusion": row["terminal_conclusion"],
        }
        if revision_kind == "review-base":
            truth_item["expected_correction_chinese"] = (
                row["adopted_chinese"]
            )
        truth_items.append(truth_item)
    prompt_sha256 = quality_m1_digest(prompt_bytes)
    context_sha256 = quality_m1_digest(context_bytes)
    blind_packet = {
        "baseline_head": inventory["candidate_head"],
        "context_sha256": context_sha256,
        "decisions_sha256": decisions_sha256,
        "glossary_sha256": inventory["glossary_sha256"],
        "inventory_sha256": inventory["inventory_sha256"],
        "items": blind_items,
        "packet_contract": "dcss-zh-quality-m1-blind-packet-v1",
        "population_identity_sha256": population["identity_sha256"],
        "population_sha256": population_sha256,
        "prompt_sha256": prompt_sha256,
        "review_base": inventory["baseline"],
        "run_id": QUALITY_M1_RUN_ID,
        "scope": {
            "case_count": len(blind_items),
            "category": "item-description",
        },
    }
    blind_bytes = quality_m1_canonical_json_bytes(blind_packet)
    blind_sha256 = quality_m1_digest(blind_bytes)
    truth = {
        "blind_packet_sha256": blind_sha256,
        "contract": "dcss-zh-quality-m1-truth-v1",
        "items": truth_items,
        "population_sha256": population_sha256,
        "run_id": QUALITY_M1_RUN_ID,
    }
    truth_bytes = quality_m1_canonical_json_bytes(truth)
    truth_sha256 = quality_m1_digest(truth_bytes)
    files = {
        "blind-packet.json": blind_bytes,
        "context.txt": context_bytes,
        "population.json": population_bytes,
        "prompt.md": prompt_bytes,
        "truth.json": truth_bytes,
    }
    shard_names = []
    shard_count = (
        len(blind_items) + QUALITY_M1_SHARD_SIZE - 1
    ) // QUALITY_M1_SHARD_SIZE
    for shard_offset in range(0, len(blind_items), QUALITY_M1_SHARD_SIZE):
        shard_index = shard_offset // QUALITY_M1_SHARD_SIZE + 1
        shard_items = blind_items[
            shard_offset:shard_offset + QUALITY_M1_SHARD_SIZE
        ]
        name = f"blind-shard-{shard_index:02d}.json"
        shard_names.append(name)
        files[name] = quality_m1_canonical_json_bytes({
            "item_count": len(shard_items),
            "items": shard_items,
            "packet_contract": "dcss-zh-quality-m1-blind-shard-v1",
            "parent_packet_contract": blind_packet["packet_contract"],
            "parent_packet_sha256": blind_sha256,
            "shard_count": shard_count,
            "shard_index": shard_index,
        })
    evaluator_files = ["prompt.md", "context.txt", *shard_names]
    commitment = {
        "blind_packet_sha256": blind_sha256,
        "commitment_contract": "dcss-zh-quality-m1-commitment-v1",
        "context_sha256": context_sha256,
        "decisions_sha256": decisions_sha256,
        "evaluator_bundle_sha256": quality_m1_evaluator_bundle_digest(
            files, evaluator_files
        ),
        "glossary_sha256": inventory["glossary_sha256"],
        "inventory_sha256": inventory["inventory_sha256"],
        "population_identity_sha256": population["identity_sha256"],
        "population_sha256": population_sha256,
        "prompt_sha256": prompt_sha256,
        "review_base": inventory["baseline"],
        "run_id": QUALITY_M1_RUN_ID,
        "selection": {
            "adopted_adjust_count": QUALITY_M1_ADOPTED_ADJUST_COUNT,
            "adopted_keep_count": QUALITY_M1_ADOPTED_KEEP_COUNT,
            "algorithm": (
                "sha256(seed|pool|identity), then "
                "sha256(seed|order|identity|revision-kind)"
            ),
            "before_after_pair_in_same_run": False,
            "case_count": len(blind_items),
            "identity_unique": True,
            "review_base_adjust_count": (
                QUALITY_M1_REVIEW_BASE_ADJUST_COUNT
            ),
            "seed": seed,
            "shard_size": QUALITY_M1_SHARD_SIZE,
        },
        "truth_bytes": len(truth_bytes),
        "truth_sha256": truth_sha256,
    }
    files["commitment.json"] = quality_m1_canonical_json_bytes(commitment)
    roles = {
        "blind-packet.json": "audit",
        "commitment.json": "audit",
        "context.txt": "evaluator",
        "population.json": "sealed",
        "prompt.md": "evaluator",
        "truth.json": "sealed",
        **{name: "evaluator" for name in shard_names},
    }
    artifacts = []
    for name in sorted(files):
        artifacts.append({
            "bytes": len(files[name]),
            "path": name,
            "role": roles[name],
            "sha256": quality_m1_digest(files[name]),
        })
    manifest = {
        "artifacts": artifacts,
        "audit_files": ["blind-packet.json", "commitment.json"],
        "contract": "dcss-zh-quality-m1-manifest-v1",
        "evaluator_files": evaluator_files,
        "run_id": QUALITY_M1_RUN_ID,
        "sealed_files": ["population.json", "truth.json"],
    }
    files["manifest.json"] = quality_m1_canonical_json_bytes(manifest)
    validate_quality_m1_files(files)
    return files


def quality_m1_load_canonical(files, name):
    try:
        value = json.loads(files[name].decode("utf-8", errors="strict"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError(f"quality M1 {name} is not valid JSON") from error
    if quality_m1_canonical_json_bytes(value) != files[name]:
        raise RuntimeError(f"quality M1 {name} is not canonical JSON")
    return value


def validate_quality_m1_files(files):
    manifest = quality_m1_load_canonical(files, "manifest.json")
    artifact_names = {item["path"] for item in manifest["artifacts"]}
    if artifact_names != set(files) - {"manifest.json"}:
        raise RuntimeError("quality M1 manifest artifact membership mismatch")
    for artifact in manifest["artifacts"]:
        quality_m1_require_relative_path(
            artifact["path"], "quality M1 artifact path"
        )
        data = files[artifact["path"]]
        if artifact["bytes"] != len(data):
            raise RuntimeError(
                f"quality M1 artifact size mismatch: {artifact['path']}"
            )
        if artifact["sha256"] != quality_m1_digest(data):
            raise RuntimeError(
                f"quality M1 artifact digest mismatch: {artifact['path']}"
            )
    parent = quality_m1_load_canonical(files, "blind-packet.json")
    population = quality_m1_load_canonical(files, "population.json")
    truth = quality_m1_load_canonical(files, "truth.json")
    commitment = quality_m1_load_canonical(files, "commitment.json")
    shard_names = [
        name for name in manifest["evaluator_files"]
        if name.startswith("blind-shard-")
    ]
    if manifest["evaluator_files"] != [
        "prompt.md", "context.txt", *shard_names
    ]:
        raise RuntimeError("quality M1 evaluator file order mismatch")
    if set(manifest["sealed_files"]) != {"population.json", "truth.json"}:
        raise RuntimeError("quality M1 sealed file classification mismatch")
    evaluator_json = [parent]
    merged_items = []
    for expected_index, name in enumerate(shard_names, start=1):
        shard = quality_m1_load_canonical(files, name)
        evaluator_json.append(shard)
        if shard["shard_index"] != expected_index:
            raise RuntimeError("quality M1 shard index mismatch")
        if shard["shard_count"] != len(shard_names):
            raise RuntimeError("quality M1 shard count mismatch")
        if shard["parent_packet_sha256"] != quality_m1_digest(
            files["blind-packet.json"]
        ):
            raise RuntimeError("quality M1 shard parent digest mismatch")
        if shard["item_count"] != len(shard["items"]):
            raise RuntimeError("quality M1 shard item count mismatch")
        if len(shard["items"]) > QUALITY_M1_SHARD_SIZE:
            raise RuntimeError("quality M1 shard exceeds bounded size")
        merged_items.extend(shard["items"])
    if merged_items != parent["items"]:
        raise RuntimeError("quality M1 shards do not reconstruct parent")
    leaked = []
    for index, value in enumerate(evaluator_json):
        leaked.extend(quality_m1_forbidden_fields(
            value, f"$evaluator[{index}]"
        ))
    if leaked:
        raise RuntimeError(
            f"quality M1 evaluator label leak: {sorted(leaked)}"
        )
    identities = [item["identity"] for item in parent["items"]]
    if len(identities) != len(set(identities)):
        raise RuntimeError("quality M1 parent identities are not unique")
    expected_case_ids = [
        f"M0-{index:03d}" for index in range(1, len(identities) + 1)
    ]
    if [item["case_id"] for item in parent["items"]] != expected_case_ids:
        raise RuntimeError("quality M1 parent case order is invalid")
    if parent["population_sha256"] != quality_m1_digest(
        files["population.json"]
    ):
        raise RuntimeError("quality M1 population digest mismatch")
    if parent["population_identity_sha256"] != population[
        "identity_sha256"
    ]:
        raise RuntimeError("quality M1 population identity digest mismatch")
    if parent["prompt_sha256"] != quality_m1_digest(files["prompt.md"]):
        raise RuntimeError("quality M1 prompt digest mismatch")
    if parent["context_sha256"] != quality_m1_digest(
        files["context.txt"]
    ):
        raise RuntimeError("quality M1 context digest mismatch")
    blind_sha256 = quality_m1_digest(files["blind-packet.json"])
    truth_sha256 = quality_m1_digest(files["truth.json"])
    if truth["blind_packet_sha256"] != blind_sha256:
        raise RuntimeError("quality M1 truth/packet binding mismatch")
    if commitment["blind_packet_sha256"] != blind_sha256:
        raise RuntimeError("quality M1 commitment/packet binding mismatch")
    if commitment["truth_sha256"] != truth_sha256:
        raise RuntimeError("quality M1 truth commitment mismatch")
    if commitment["truth_bytes"] != len(files["truth.json"]):
        raise RuntimeError("quality M1 truth byte count mismatch")
    if commitment["evaluator_bundle_sha256"] != (
        quality_m1_evaluator_bundle_digest(
            files, manifest["evaluator_files"]
        )
    ):
        raise RuntimeError("quality M1 evaluator bundle digest mismatch")
    if len(truth["items"]) != len(parent["items"]):
        raise RuntimeError("quality M1 truth coverage mismatch")
    for packet_item, truth_item in zip(parent["items"], truth["items"]):
        if (
            truth_item["case_id"] != packet_item["case_id"]
            or truth_item["identity"] != packet_item["identity"]
            or truth_item["packet_item_sha256"] != quality_m1_digest(
                quality_m1_canonical_json_bytes(packet_item)
            )
        ):
            raise RuntimeError("quality M1 truth item binding mismatch")
        revision = truth_item["revision_kind"]
        expected = truth_item["historical_expected_severity"]
        if revision == "review-base":
            if (
                expected != "needs_fix"
                or "expected_correction_chinese" not in truth_item
            ):
                raise RuntimeError(
                    "quality M1 review-base truth is incomplete"
                )
        elif revision == "adopted":
            if (
                expected != "unadjudicated"
                or "expected_correction_chinese" in truth_item
            ):
                raise RuntimeError(
                    "quality M1 adopted candidate was mislabeled clean"
                )
        else:
            raise RuntimeError("quality M1 truth revision kind is invalid")


def quality_m1_output_directory(path):
    candidate = path if path.is_absolute() else ROOT / path
    candidate = candidate.resolve()
    allowed = QUALITY_M1_OUTPUT_ROOT.resolve()
    try:
        relative = candidate.relative_to(allowed)
    except ValueError as error:
        raise RuntimeError(
            "quality M1 output must be under .artifacts/i18n/quality"
        ) from error
    if not relative.parts:
        raise RuntimeError("quality M1 output must name a run directory")
    return candidate


def write_quality_m1_bundle(path, files):
    output = quality_m1_output_directory(path)
    if output.exists() or output.is_symlink():
        raise RuntimeError("quality M1 output directory already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir()
    for name in sorted(files):
        quality_m1_require_relative_path(name, "quality M1 output filename")
        (output / name).write_bytes(files[name])
    return output


def verify_quality_m1_bundle(path, expected_files):
    output = quality_m1_output_directory(path)
    if output.is_symlink() or not output.is_dir():
        raise RuntimeError(
            "quality M1 verification target must be a regular directory"
        )
    actual_files = {}
    for child in output.iterdir():
        if child.is_symlink() or not child.is_file():
            raise RuntimeError(
                f"quality M1 bundle contains a non-regular entry: "
                f"{child.name}"
            )
        actual_files[child.name] = child.read_bytes()
    if set(actual_files) != set(expected_files):
        raise RuntimeError(
            "quality M1 bundle file membership differs from expected"
        )
    for name in sorted(expected_files):
        if actual_files[name] != expected_files[name]:
            raise RuntimeError(
                f"quality M1 bundle byte mismatch: {name}"
            )
    validate_quality_m1_files(actual_files)
    return output


def write_review_results(path, inventory, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_review_results(inventory, rows),
        encoding="utf-8",
    )


def write_review_results_v3(path, inventory, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_review_results_v3(inventory, rows),
        encoding="utf-8",
    )


@audit_snapshot_invocation(ROOT)
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
        "--review-schema",
        choices=("v2", "v3"),
        default="v2",
        help=(
            "explicit review artifact schema for issue29-v2; v2 remains the "
            "transitional default until ledger migration"
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
    quality_action = parser.add_mutually_exclusive_group()
    quality_action.add_argument(
        "--quality-m1-output-dir",
        type=Path,
        help=(
            "materialize the deterministic item-description M1 bundle "
            "under .artifacts/i18n/quality"
        ),
    )
    quality_action.add_argument(
        "--verify-quality-m1",
        type=Path,
        help=(
            "rebuild and byte-verify an existing deterministic M1 bundle "
            "under .artifacts/i18n/quality"
        ),
    )
    parser.add_argument(
        "--quality-prompt",
        type=Path,
        help="exact UTF-8 evaluator prompt for a quality M1 bundle",
    )
    parser.add_argument(
        "--quality-context",
        type=Path,
        help="exact UTF-8 terminology context for a quality M1 bundle",
    )
    parser.add_argument(
        "--quality-seed",
        default=QUALITY_M1_SEED,
        help=(
            "deterministic M1 selection seed "
            f"(default: {QUALITY_M1_SEED})"
        ),
    )
    args = parser.parse_args(argv)
    quality_requested = bool(
        args.quality_m1_output_dir or args.verify_quality_m1
    )
    if quality_requested and (
        args.scope != "issue29-v2"
        or args.review_schema != "v2"
        or not args.review_results
        or not args.quality_prompt
        or not args.quality_context
    ):
        parser.error(
            "quality M1 requires --scope issue29-v2, --review-results, "
            "--quality-prompt, and --quality-context"
        )
    if not quality_requested and (
        args.quality_prompt or args.quality_context
    ):
        parser.error(
            "--quality-prompt/--quality-context require a quality M1 action"
        )

    try:
        if args.scope == "issue29-v2":
            builder = (
                build_extended_inventory_v3
                if args.review_schema == "v3"
                else build_extended_inventory
            )
            payload, internal_rows = builder(
                args.review_base or ISSUE29_REVIEW_BASE
            )
            if args.write_review_results:
                if args.review_schema == "v3":
                    write_review_results_v3(
                        args.write_review_results, payload, internal_rows
                    )
                else:
                    write_review_results(
                        args.write_review_results, payload, internal_rows
                    )
            if args.review_results:
                review_input = load_review_input(
                    ROOT,
                    args.review_results,
                    snapshot=audit_snapshot(),
                )
                payload["review_input"] = review_input_metadata(review_input)
                if args.review_schema == "v3":
                    review = parse_review_results_v3(review_input)
                    review_header = parse_review_header_v3(review_input)
                    payload["review_violations"] = review_violations_v3(
                        payload["rows"],
                        review,
                        payload,
                        review_header,
                        review_input,
                    )
                else:
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
                or args.review_base or args.review_schema != "v2"
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

    payload["audit_snapshot"] = audit_snapshot().metadata()
    quality_summary = None
    if quality_requested:
        try:
            prompt_bytes = quality_m1_read_input(
                args.quality_prompt, "quality M1 prompt"
            )
            context_bytes = quality_m1_read_input(
                args.quality_context, "quality M1 context"
            )
            files = build_quality_m1_files(
                payload,
                prompt_bytes,
                context_bytes,
                sha(ROOT / "docs/decisions.md"),
                seed=args.quality_seed,
            )
            requested_dir = (
                args.quality_m1_output_dir or args.verify_quality_m1
            )
            bundle_dir = quality_m1_output_directory(requested_dir)
            if args.output:
                inventory_output = (
                    args.output
                    if args.output.is_absolute()
                    else ROOT / args.output
                ).resolve()
                if (
                    inventory_output == bundle_dir
                    or bundle_dir in inventory_output.parents
                ):
                    raise RuntimeError(
                        "inventory --output must be outside the quality "
                        "M1 bundle directory"
                    )
            if args.quality_m1_output_dir:
                output_dir = write_quality_m1_bundle(
                    args.quality_m1_output_dir, files
                )
                operation = "materialize"
            else:
                output_dir = verify_quality_m1_bundle(
                    args.verify_quality_m1, files
                )
                operation = "verify"
            commitment = json.loads(
                files["commitment.json"].decode("utf-8")
            )
            quality_summary = {
                "directory": output_dir.relative_to(ROOT).as_posix(),
                "manifest_sha256": quality_m1_digest(
                    files["manifest.json"]
                ),
                "operation": operation,
                "truth_sha256": commitment["truth_sha256"],
            }
        except (
            AttributeError,
            OSError,
            KeyError,
            RuntimeError,
            ValueError,
        ) as error:
            print(
                f"ERROR: quality M1 bundle could not be built or verified: "
                f"{error}",
                file=sys.stderr,
            )
            return 2
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    elif not quality_requested:
        sys.stdout.write(encoded)

    summary = {key: payload[key] for key in [
        "baseline", "candidate_head", "glossary_sha256",
        "inventory_sha256", "count",
        "category_counts", "duplicates", "missing_identities",
        "unexpected_identities", "missing_chinese", "missing_forms",
    ] if key in payload}
    if "review_violations" in payload:
        summary["review_violations"] = payload["review_violations"]
    if quality_summary:
        summary["quality_m1"] = quality_summary
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
