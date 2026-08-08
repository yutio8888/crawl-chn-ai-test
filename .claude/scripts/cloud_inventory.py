#!/usr/bin/env python3
"""Deterministic read-only cloud inventory for the R1 (cloud names/descriptions)
batch review.

Identity source: the cloud_type enum in crawl-ref/source/cloud-type.h.
Name source: the clouds[] data table in crawl-ref/source/cloud.cc (terse and
verbose names are the first two string literals after each `// CLOUD_X,`
marker). Display names go through T_() (dat/i18n/zh/source.txt) and long
descriptions are looked up by `<terse name> cloud` in dat/descript/clouds.txt
(EN) and dat/descript/zh/clouds.txt (ZH).

Outputs a JSON inventory (rebuildable, temporary artifact) and a coverage
report proving: every enum member has a name entry, every name has a T_ key
(or is reported missing), every description key in EN exists in ZH (and vice
versa, so language-side orphans are detected), and a producer/consumer map
derived from code greps.

Usage:
  python3 .claude/scripts/cloud_inventory.py --inventory-output /tmp/cloud-inventory.json
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "crawl-ref" / "source"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_enum(path: Path) -> list[str]:
    """Return the CLOUD_* enum member names in declaration order."""
    txt = path.read_text()
    m = re.search(r"enum cloud_type\s*\{(.*?)\};", txt, re.S)
    if not m:
        raise SystemExit(f"cannot parse cloud_type enum in {path}")
    body = m.group(1)
    names = []
    for line in body.splitlines():
        line = line.split("//")[0].strip()
        if not line or line.startswith("#"):
            continue
        for tok in line.rstrip(",").split(","):
            tok = tok.strip().split("=")[0].strip()
            if tok.startswith("CLOUD_"):
                names.append(tok)
    return names


def parse_cloud_data(path: Path) -> dict[str, dict]:
    """Extract {enum: {terse, verbose}} from the clouds[] table by matching
    each `// CLOUD_X,` comment with the following `{ "terse", "verbose" }`."""
    txt = path.read_text()
    out: dict[str, dict] = {}
    marker_re = re.compile(r"//\s*(CLOUD_[A-Z0-9_]+)\s*,?")
    entry_re = re.compile(r"\{\s*\"([^\"]*)\"\s*(?:,\s*\"([^\"]*)\")?")
    lines = txt.splitlines()
    i = 0
    while i < len(lines):
        mm = marker_re.search(lines[i])
        if mm:
            enum = mm.group(1)
            # find the `{ "terse"` entry within the next few lines
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("{ \"") \
                    and j < i + 6:
                j += 1
            if j < len(lines):
                em = entry_re.search(lines[j])
                if em:
                    terse = em.group(1)
                    verbose = em.group(2)
                    out[enum] = {"terse": terse, "verbose": verbose}
                    i = j
                    continue
        i += 1
    return out


def parse_t_key(path: Path) -> dict[str, str]:
    """Parse source.txt: plain keys (no context prefix) -> ZH value."""
    txt = path.read_text()
    entries: dict[str, str] = {}
    blocks = re.split(r"%%%%", txt)
    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        first, _, rest = block.partition("\n")
        key = first.strip()
        if not key or "|" in key:  # context-prefixed keys (verb|...) excluded
            continue
        value = "\n".join(line for line in rest.splitlines()
                          if line.strip()) if rest else ""
        entries[key] = value
    return entries


def parse_db_keys(path: Path) -> dict[str, str]:
    """Parse a TextDB file: `%%%%` blocks, key = first line, value = rest."""
    txt = path.read_text()
    entries: dict[str, str] = {}
    blocks = re.split(r"%%%%", txt)
    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        first, _, rest = block.partition("\n")
        key = first.strip()
        if not key:
            continue
        entries[key] = rest.strip()
    return entries


def grep_producers(enum: str) -> list[str]:
    """Find code locations that create this cloud type (read-only grep)."""
    pats = [rf"place_cloud\s*\(\s*{enum}", rf"big_cloud\s*\(\s*{enum}"]
    hits = []
    for pat in pats:
        r = subprocess.run(
            ["grep", "-rn", "-E", pat, str(SRC)],
            capture_output=True, text=True, cwd=ROOT)
        for line in r.stdout.splitlines():
            if "/cloud.cc:" in line or "/cloud-type.h:" in line:
                continue
            rel = line.replace(str(SRC) + "/", "")
            hits.append(rel)
    return hits


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory-output", default="/tmp/cloud-inventory.json")
    args = ap.parse_args()

    enum_path = SRC / "cloud-type.h"
    data_path = SRC / "cloud.cc"
    source_txt = SRC / "dat" / "i18n" / "zh" / "source.txt"
    desc_en = SRC / "dat" / "descript" / "clouds.txt"
    desc_zh = SRC / "dat" / "descript" / "zh" / "clouds.txt"

    enums = parse_enum(enum_path)
    names = parse_cloud_data(data_path)
    t = parse_t_key(source_txt)
    db_en = parse_db_keys(desc_en)
    db_zh = parse_db_keys(desc_zh)

    # enum members without a data-table entry
    missing_data = [e for e in enums if e not in names]
    # data-table entries without enum members (unused leftovers)
    extra_data = [e for e in names if e not in enums]

    inventory = []
    for enum in enums:
        if enum not in names:
            inventory.append({
                "identity": f"cloud:{enum}", "lifecycle": "no_data_entry",
                "terse_en": None, "verbose_en": None,
                "terse_zh": None, "verbose_zh": None,
                "desc_key": None, "desc_en": False, "desc_zh": False,
                "producers": [], "missing_t_key": None,
            })
            continue
        terse = names[enum]["terse"]
        verbose = names[enum]["verbose"]
        desc_key = terse + " cloud"
        entry = {
            "identity": f"cloud:{enum}",
            "terse_en": terse,
            "verbose_en": verbose,
            "terse_zh": t.get(terse),
            "verbose_zh": t.get(verbose) if verbose else None,
            "desc_key": desc_key,
            "desc_en": desc_key in db_en,
            "desc_zh": desc_key in db_zh,
            "producers": grep_producers(enum),
            "missing_t_key": None if terse in t
                              or enum in ("CLOUD_NONE", "CLOUD_RANDOM_SMOKE",
                                          "CLOUD_RANDOM", "CLOUD_DEBUGGING")
                              else terse,
        }
        inventory.append(entry)

    # language-side-only description keys (ZH has no EN counterpart)
    zh_only_keys = sorted(set(db_zh) - set(db_en))
    en_only_keys = sorted(set(db_en) - set(db_zh))
    # T_ key coverage for names referenced by the data table
    name_keys = set()
    for e in inventory:
        if e["terse_en"]:
            name_keys.add(e["terse_en"])
        if e["verbose_en"]:
            name_keys.add(e["verbose_en"])
    missing_names = sorted(k for k in name_keys if k not in t)

    payload = {
        "baseline": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=ROOT).stdout.strip(),
        "glossary_sha256": sha256_file(ROOT / "docs" / "glossary.md"),
        "digests": {
            "cloud-type.h": sha256_file(enum_path),
            "cloud.cc": sha256_file(data_path),
            "source.txt": sha256_file(source_txt),
            "clouds.txt": sha256_file(desc_en),
            "zh/clouds.txt": sha256_file(desc_zh),
        },
        "enum_members": enums,
        "missing_data_entries": missing_data,
        "extra_data_entries": extra_data,
        "zh_only_desc_keys": zh_only_keys,
        "en_only_desc_keys": en_only_keys,
        "missing_t_keys": missing_names,
        "inventory": inventory,
    }
    digest = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    payload["inventory_sha256"] = digest

    out = Path(args.inventory_output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1))

    print(f"inventory sha256: {digest}")
    print(f"enum members: {len(enums)}")
    print(f"data entries: {len(names)}")
    print(f"missing data entries: {missing_data}")
    print(f"extra data entries: {extra_data}")
    print(f"missing T_ keys: {missing_names}")
    print(f"desc keys: EN-only={en_only_keys} ZH-only={zh_only_keys}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
