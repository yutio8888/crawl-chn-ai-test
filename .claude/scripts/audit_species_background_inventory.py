#!/usr/bin/env python3
"""Freeze the production species/background inventory for ZH review.

The inventory is derived from the active save-compatible enums and the YAML
data consumed by the species/job generators.  It deliberately does not use
Wiki page counts or a hand-maintained identity list.
"""

import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "crawl-ref/source"
SPECIES_DIR = SRC / "dat/species"
JOBS_DIR = SRC / "dat/jobs"
ZH_SOURCE_DIR = SRC / "dat/i18n/zh"
SPECIES_ENUMS = SRC / "util/species-gen/species-type-header.txt"
JOB_ENUMS = SRC / "util/job-gen/job-type-header.txt"
DEPRECATED_JOBS = SRC / "util/job-gen/job-data-deprecated-jobs.txt"
EN_SPECIES_DESCRIPTIONS = SRC / "dat/descript/species.txt"
ZH_SPECIES_DESCRIPTIONS = SRC / "dat/descript/zh/species.txt"
EN_BACKGROUND_DESCRIPTIONS = SRC / "dat/descript/backgrounds.txt"
ZH_BACKGROUND_DESCRIPTIONS = SRC / "dat/descript/zh/backgrounds.txt"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_item_name_inventory import (  # noqa: E402
    active_source,
    function_body,
    sha,
    source_entries,
    source_files,
    tag_major_version,
)
from i18n_shared import (  # noqa: E402
    parse_entries_physical,
    runtime_normalize_value,
)


def relative(path):
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_yaml_rows(directory, prefix):
    rows = []
    for path in sorted(directory.glob("*.yaml"), key=lambda item: item.name):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"expected one YAML mapping in {relative(path)}")
        identity = data.get("enum")
        if not isinstance(identity, str) or not identity.startswith(prefix):
            raise ValueError(f"invalid enum in {relative(path)}: {identity!r}")
        if not isinstance(data.get("name"), str):
            raise ValueError(f"missing English name in {relative(path)}")
        rows.append((path, data))
    return rows


def enum_identities(path, prefix):
    """Return concrete enum identities from the active TAG branch."""
    identities = []
    for line in active_source(path).splitlines():
        match = re.match(
            rf"^\s*({re.escape(prefix)}[A-Z0-9_]+)\s*(=.+)?\s*,", line
        )
        if match and match.group(2) is None:
            identities.append(match.group(1))
    if not identities:
        raise RuntimeError(f"no {prefix} identities parsed from {relative(path)}")
    return identities


def deprecated_job_rows(path=DEPRECATED_JOBS):
    """Parse the compatibility-only job records consumed by job-gen."""
    text = active_source(path)
    rows = []
    pattern = re.compile(
        r"\{\s*(JOB_[A-Z0-9_]+)\s*,\s*\{\s*"
        r'"([^"]+)"\s*,\s*"([^"]+)"',
        re.MULTILINE,
    )
    for identity, short_name, name in pattern.findall(text):
        rows.append({
            "enum": identity,
            "short_name": short_name,
            "name": name,
            "TAG_MAJOR_VERSION": tag_major_version(),
            "compatibility_source": relative(path),
        })
    return rows


def description_entries(path):
    entries = parse_entries_physical(str(path))
    duplicates = sorted(
        key for key, count in Counter(
            entry.canonical_key for entry in entries
        ).items() if count > 1
    )
    effective = {}
    for entry in entries:
        effective[entry.canonical_key] = runtime_normalize_value(entry.value)
    return effective, duplicates


def species_context_overrides(path=SRC / "species.cc"):
    """Parse the narrow C_() overrides in species::name()."""
    body = function_body(active_source(path), "name")
    pattern = re.compile(
        r"if\s*\(\s*speci\s*==\s*(SP_[A-Z0-9_]+)\s*\)\s*"
        r'return\s+C_\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*\)\s*;'
    )
    overrides = {
        identity: f"{context}|{name}"
        for identity, context, name in pattern.findall(body)
    }
    if body.count("C_(") != len(overrides):
        raise RuntimeError("unparsed contextual species-name producer")
    return overrides


def translated_form(db, english, key=None):
    lookup = (key or english).lower()
    return {
        "english": english,
        "lookup_key": key or english,
        "chinese": db.get(lookup),
        "translation_present": bool(db.get(lookup)),
    }


def species_rows(db, descriptions):
    en_desc, zh_desc = descriptions
    overrides = species_context_overrides()
    rows = []
    for path, data in load_yaml_rows(SPECIES_DIR, "SP_"):
        identity = data["enum"]
        if "TAG_MAJOR_VERSION" in data:
            lifecycle = "compatibility"
        elif data.get("difficulty") is False:
            lifecycle = "current_variant"
        else:
            lifecycle = "current_playable"
        name = data["name"]
        forms = {
            "plain": translated_form(db, name, overrides.get(identity)),
        }
        for form, field in (("adjective", "adjective"), ("genus", "genus")):
            if data.get(field):
                forms[form] = translated_form(db, data[field])
        desc_key = name.lower() if lifecycle == "current_playable" else None
        rows.append({
            "identity": f"species:{identity}",
            "category": "species",
            "lifecycle": lifecycle,
            "english_source_name": name,
            "current_chinese_name": forms["plain"]["chinese"],
            "short_name": data.get("short_name", name[:2]),
            "forms": forms,
            "description_key": name if desc_key else None,
            "english_description": en_desc.get(desc_key) if desc_key else None,
            "chinese_description": zh_desc.get(desc_key) if desc_key else None,
            "source_file": relative(path),
            "production_data": data,
        })
    return rows


def background_rows(db, descriptions):
    en_desc, zh_desc = descriptions
    rows = []
    data_rows = [
        (path, data, "current_playable")
        for path, data in load_yaml_rows(JOBS_DIR, "JOB_")
    ]
    data_rows.extend(
        (DEPRECATED_JOBS, data, "compatibility")
        for data in deprecated_job_rows()
    )
    for path, data, lifecycle in data_rows:
        name = data["name"]
        form = translated_form(db, name)
        desc_key = name.lower() if lifecycle == "current_playable" else None
        rows.append({
            "identity": f"background:{data['enum']}",
            "category": "background",
            "lifecycle": lifecycle,
            "english_source_name": name,
            "current_chinese_name": form["chinese"],
            "short_name": data.get("short_name", name[:2]),
            "forms": {"plain": form},
            "description_key": name if desc_key else None,
            "english_description": en_desc.get(desc_key) if desc_key else None,
            "chinese_description": zh_desc.get(desc_key) if desc_key else None,
            "source_file": relative(path),
            "production_data": data,
        })
    return rows


def expected_identities():
    return {
        *(f"species:{identity}" for identity in enum_identities(
            SPECIES_ENUMS, "SP_"
        )),
        *(f"background:{identity}" for identity in enum_identities(
            JOB_ENUMS, "JOB_"
        )),
    }


def inventory_violations(
    rows,
    expected=None,
    description_duplicates=None,
    description_keys=None,
):
    expected = expected if expected is not None else {
        row["identity"] for row in rows
    }
    identities = [row["identity"] for row in rows]
    actual = set(identities)
    current = [
        row for row in rows if row["lifecycle"] == "current_playable"
    ]
    expected_desc = {
        category: {
            row["description_key"].lower()
            for row in current
            if row["category"] == category and row.get("description_key")
        }
        for category in ("species", "background")
    }
    description_duplicates = description_duplicates or {}
    description_keys = description_keys or {}
    return {
        "duplicates": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "missing_identities": sorted(expected - actual),
        "unexpected_identities": sorted(actual - expected),
        "missing_chinese_names": sorted(
            row["identity"] for row in rows
            if not row.get("current_chinese_name")
        ),
        "missing_chinese_forms": sorted(
            f"{row['identity']}:{form}"
            for row in rows
            for form, value in row.get("forms", {}).items()
            if not value.get("translation_present")
        ),
        "missing_english_descriptions": sorted(
            row["identity"] for row in current
            if not row.get("english_description")
        ),
        "missing_chinese_descriptions": sorted(
            row["identity"] for row in current
            if not row.get("chinese_description")
        ),
        "duplicate_description_keys": {
            name: sorted(keys)
            for name, keys in sorted(description_duplicates.items())
            if keys
        },
        "unexpected_description_keys": {
            name: sorted(keys - expected_desc[
                "species" if name.endswith("species") else "background"
            ])
            for name, keys in sorted(description_keys.items())
            if keys - expected_desc[
                "species" if name.endswith("species") else "background"
            ]
        },
    }


def build_inventory():
    db = source_entries(ZH_SOURCE_DIR)
    en_species, dup_en_species = description_entries(
        EN_SPECIES_DESCRIPTIONS
    )
    zh_species, dup_zh_species = description_entries(
        ZH_SPECIES_DESCRIPTIONS
    )
    en_backgrounds, dup_en_backgrounds = description_entries(
        EN_BACKGROUND_DESCRIPTIONS
    )
    zh_backgrounds, dup_zh_backgrounds = description_entries(
        ZH_BACKGROUND_DESCRIPTIONS
    )
    rows = [
        *species_rows(db, (en_species, zh_species)),
        *background_rows(db, (en_backgrounds, zh_backgrounds)),
    ]
    rows.sort(key=lambda row: row["identity"])
    violations = inventory_violations(
        rows,
        expected_identities(),
        {
            "english_species": dup_en_species,
            "chinese_species": dup_zh_species,
            "english_backgrounds": dup_en_backgrounds,
            "chinese_backgrounds": dup_zh_backgrounds,
        },
        {
            "english_species": set(en_species),
            "chinese_species": set(zh_species),
            "english_backgrounds": set(en_backgrounds),
            "chinese_backgrounds": set(zh_backgrounds),
        },
    )
    inputs = [
        *source_files(ZH_SOURCE_DIR),
        *sorted(SPECIES_DIR.glob("*.yaml")),
        *sorted(JOBS_DIR.glob("*.yaml")),
        SPECIES_ENUMS,
        JOB_ENUMS,
        DEPRECATED_JOBS,
        SRC / "species.cc",
        EN_SPECIES_DESCRIPTIONS,
        ZH_SPECIES_DESCRIPTIONS,
        EN_BACKGROUND_DESCRIPTIONS,
        ZH_BACKGROUND_DESCRIPTIONS,
        ROOT / "docs/glossary.md",
    ]
    payload = {
        "schema": "dcss-species-background-review-inventory-v1",
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
                "active current and TAG compatibility species identities",
                "active current and TAG compatibility background identities",
                "species plain/adjective/genus display forms",
                "background display names",
                "current playable species/background descriptions",
                "species aptitudes, stats, size, restrictions and mutations",
                "background stats, skills, equipment, spells and god starts",
            ],
            "excluded": [
                "balance changes and strategy advice",
                "independent ability and mutation identity conclusions",
                "independent item and spell name re-review",
                "Wiki-derived identity counts",
            ],
        },
        "count": len(rows),
        "category_counts": {
            category: sum(row["category"] == category for row in rows)
            for category in ("species", "background")
        },
        "lifecycle_counts": {
            lifecycle: sum(row["lifecycle"] == lifecycle for row in rows)
            for lifecycle in sorted({row["lifecycle"] for row in rows})
        },
        **violations,
        "rows": rows,
    }
    encoded = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    payload["inventory_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def has_violations(payload):
    keys = (
        "duplicates",
        "missing_identities",
        "unexpected_identities",
        "missing_chinese_names",
        "missing_chinese_forms",
        "missing_english_descriptions",
        "missing_chinese_descriptions",
        "duplicate_description_keys",
        "unexpected_description_keys",
    )
    return any(payload[key] for key in keys)


def review_coverage(payload, path):
    """Prove one evidence-card row and terminal conclusion per identity."""
    text = path.read_text(encoding="utf-8")
    rows = re.findall(
        r"^\|\s*`((?:species:SP|background:JOB)_[A-Z0-9_]+)`"
        r"\s*\|.*?\|\s*([^|\n]+?)\s*\|\s*$",
        text,
        re.MULTILINE,
    )
    identities = [identity for identity, _conclusion in rows]
    conclusions = {
        identity: conclusion.strip() for identity, conclusion in rows
    }
    expected = {row["identity"] for row in payload["rows"]}
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
            identity for identity in actual
            if not conclusions.get(identity)
        ),
        "coverage_equal": (
            len(identities) == len(expected)
            and actual == expected
            and all(conclusions.values())
        ),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="write the full JSON inventory to this path (default: stdout)",
    )
    parser.add_argument(
        "--review-results",
        type=Path,
        help=(
            "also prove exact evidence-card/terminal-conclusion coverage "
            "(use docs/species-background-review-results.md for Issue 26)"
        ),
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
        yaml.YAMLError,
        subprocess.SubprocessError,
    ) as error:
        print(
            f"ERROR: species/background inventory could not be built: {error}",
            file=sys.stderr,
        )
        return 2
    if args.review_results:
        try:
            payload["review_coverage"] = review_coverage(
                payload, args.review_results
            )
        except (OSError, ValueError) as error:
            print(
                f"ERROR: review coverage could not be checked: {error}",
                file=sys.stderr,
            )
            return 2
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    summary_keys = (
        "baseline",
        "glossary_sha256",
        "inventory_sha256",
        "count",
        "category_counts",
        "lifecycle_counts",
        "duplicates",
        "missing_identities",
        "unexpected_identities",
        "missing_chinese_names",
        "missing_chinese_forms",
        "missing_english_descriptions",
        "missing_chinese_descriptions",
        "duplicate_description_keys",
        "unexpected_description_keys",
    )
    if "review_coverage" in payload:
        summary_keys = (*summary_keys, "review_coverage")
    print(
        json.dumps(
            {key: payload[key] for key in summary_keys},
            ensure_ascii=False,
            indent=2,
        ),
        file=sys.stderr,
    )
    coverage_failed = (
        "review_coverage" in payload
        and not payload["review_coverage"]["coverage_equal"]
    )
    return 1 if has_violations(payload) or coverage_failed else 0


if __name__ == "__main__":
    sys.exit(main())
