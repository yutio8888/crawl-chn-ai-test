#!/usr/bin/env python3
"""
audit_data_i18n.py — Check data-driven translation coverage.

Scans runtime-translated data sources that i18n_extract.py misses because
the T_() call uses a variable (not a string literal):

1. Monster names from dat/mons/*.yaml (translated via T_(en.c_str()) at runtime)
2. Duration strings from duration-data.h (translated via T_(endmsg) at runtime)
3. Feature names from feature-data.h (translated via T_(get_feature_def().name))
"""

import re
import os
import sys
from collections import OrderedDict

# Use shared parser for consistency with scan_i18n.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import parse_source_txt



def check_monster_names(source_dir: str, source_txt: str):
    """Check monster YAML names against source.txt + zh_monster_name() map."""
    mons_dir = os.path.join(source_dir, 'dat/mons')
    if not os.path.isdir(mons_dir):
        print("ERROR: Monster directory not found:", mons_dir)
        return 1

    yaml_names = set()
    for fn in os.listdir(mons_dir):
        if fn.endswith('.yaml'):
            fpath = os.path.join(mons_dir, fn)
            with open(fpath, 'r') as f:
                content = f.read()
            m = re.search(r'name:\s*"(.+)"', content)
            if m:
                yaml_names.add(m.group(1))

    # Parse source.txt
    src_entries = parse_source_txt(source_txt)

    # Parse zh_monster_name() static map from mon-util.cc
    mon_util_cc = os.path.join(source_dir, 'mon-util.cc')
    zh_map = {}
    if os.path.exists(mon_util_cc):
        with open(mon_util_cc, 'r') as f:
            mon_util = f.read()
        for m in re.finditer(r'\{\s*"([^"]+)",\s*"([^"]+)"\s*\}', mon_util):
            zh_map[m.group(1)] = m.group(2)

    covered = set()
    covered_by_src = set()
    covered_by_zh = set()
    missing = []

    for name in yaml_names:
        found = False
        if name.lower() in src_entries:
            covered_by_src.add(name)
            found = True
        if name in zh_map:
            covered_by_zh.add(name)
            found = True
        if found:
            covered.add(name)
        else:
            missing.append(name)

    print(f"\n--- Monster name translation coverage ---")
    print(f"Total monster YAML names: {len(yaml_names)}")
    print(f"  Covered (source.txt): {len(covered_by_src)}")
    print(f"  Covered (zh_map only): {len(covered_by_zh - covered_by_src)}")
    print(f"  Covered total: {len(covered)} ({100*len(covered)//len(yaml_names)}%)")
    print(f"  MISSING (no translation): {len(missing)}")
    if missing:
        print("  Missing entries:")
        for m in missing[:15]:
            print(f"    - {m}")
        if len(missing) > 15:
            print(f"    ... and {len(missing) - 15} more")

    return 0 if not missing else 1


def check_duration_strings(source_dir: str, source_txt: str):
    """Check duration-data.h string literals against source.txt."""
    dur_h = os.path.join(source_dir, 'duration-data.h')
    if not os.path.exists(dur_h):
        print("ERROR: duration-data.h not found:", dur_h)
        return 1

    with open(dur_h, 'r') as f:
        content = f.read()

    # Extract sentence-like strings (capital letter start, punctuation end)
    sentences = set(re.findall(r'"([A-Z][^"]{3,}?[.!?])"', content))

    src_entries = parse_source_txt(source_txt)
    missing = sorted(sentences - set(src_entries.keys()))

    print(f"\n--- Duration string translation coverage ---")
    print(f"Total duration sentence strings: {len(sentences)}")
    print(f"  Covered (source.txt): {len(sentences) - len(missing)}")
    print(f"  MISSING: {len(missing)}")
    if missing:
        print("  Missing entries:")
        for m in missing[:10]:
            print(f"    - {m}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")

    return 0 if not missing else 1


def check_feature_names(source_dir: str, source_txt: str):
    """Check feature-data.h feature descriptions against source.txt."""
    feat_h = os.path.join(source_dir, 'feature-data.h')
    if not os.path.exists(feat_h):
        return 1

    with open(feat_h, 'r') as f:
        content = f.read()

    # Extract feature name strings
    feat_names = set(re.findall(r'"([a-z][^"]{3,}?[^"]*)"', content))
    # Filter out non-descriptive strings (short codes, internal)
    feat_names = {f for f in feat_names if ' ' in f and len(f) > 10}

    src_entries = parse_source_txt(source_txt)
    missing = sorted(feat_names - set(src_entries.keys()))

    print(f"\n--- Feature name translation coverage ---")
    print(f"Total feature description strings: {len(feat_names)}")
    print(f"  Covered (source.txt): {len(feat_names) - len(missing)}")
    print(f"  MISSING: {len(missing)}")
    if missing:
        for m in missing[:10]:
            print(f"    - {m}")
        if len(missing) > 10:
            print(f"    ... and {len(missing) - 10} more")

    return 0 if not missing else 1


def main():
    if len(sys.argv) < 3:
        print("Usage: audit_data_i18n.py <source_dir> --source-txt <source.txt>")
        print("  Checks data-driven translation coverage (monsters, durations, features)")
        sys.exit(2)

    source_dir = sys.argv[1]
    if sys.argv[2] != '--source-txt' or len(sys.argv) < 4:
        print("ERROR: expected --source-txt <file>")
        sys.exit(2)
    source_txt = sys.argv[3]

    rc = 0
    rc |= check_monster_names(source_dir, source_txt)
    rc |= check_duration_strings(source_dir, source_txt)
    rc |= check_feature_names(source_dir, source_txt)

    print(f"\n=== audit_data_i18n.py complete (exit {rc}) ===")
    return rc


if __name__ == '__main__':
    sys.exit(main())
