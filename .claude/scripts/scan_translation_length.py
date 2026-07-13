#!/usr/bin/env python3
"""Find translated source.txt entries whose rendered lines may be too long.

This is an advisory check.  It estimates terminal/tile columns using Unicode
East Asian Width (CJK characters count as two columns), and checks each
explicit ``\\n``-separated segment independently.  It cannot replace a
renderer test because actual width depends on the selected font and window.

Examples:
    python3 scan_translation_length.py \
        --source-txt crawl-ref/source/dat/i18n/zh/source.txt
    python3 scan_translation_length.py --threshold 56 --fail-on-risk ...
"""

import argparse
import os
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import parse_entries


def display_width(text: str) -> int:
    """Estimate display columns; control escapes are not displayed."""
    width = 0
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text) and text[i + 1] in "ntr":
            i += 2
            continue
        category = unicodedata.category(text[i])
        if category in {"Cc", "Cf"}:
            i += 1
            continue
        width += 2 if unicodedata.east_asian_width(text[i]) in {"W", "F"} else 1
        i += 1
    return width


def split_literal_newlines(text: str) -> list[str]:
    """Split on unescaped literal ``\\n`` controls."""
    parts, current, i = [], [], 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            if text[i + 1] == "\\":
                current.extend(text[i:i + 2])
                i += 2
                continue
            if text[i + 1] == "n":
                parts.append("".join(current))
                current = []
                i += 2
                continue
        current.append(text[i])
        i += 1
    parts.append("".join(current))
    return parts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-txt", required=True)
    parser.add_argument("--threshold", type=int, default=56,
                        help="estimated columns for a high-risk segment (default: 56)")
    parser.add_argument("--warning-threshold", type=int, default=None,
                        help="estimated columns for a warning (default: threshold - 8)")
    parser.add_argument("--fail-on-risk", action="store_true",
                        help="return 1 when a high-risk segment is found")
    args = parser.parse_args()
    warning = args.warning_threshold or max(1, args.threshold - 8)
    if warning >= args.threshold:
        parser.error("--warning-threshold must be less than --threshold")

    entries = parse_entries(args.source_txt)
    findings = []
    for entry in entries:
        if entry.is_empty:
            continue
        segments = split_literal_newlines(entry.value)
        widths = [display_width(segment) for segment in segments]
        max_width = max(widths, default=0)
        if max_width >= args.threshold:
            severity = "HIGH"
        elif max_width >= warning:
            severity = "WARN"
        else:
            continue
        segment_no = widths.index(max_width) + 1
        # Use the key line: i18n_shared.value_line is intentionally optimized
        # for parity checks and may point at the first physical value line.
        findings.append((severity, entry.key_line, max_width, segment_no, entry.key))

    findings.sort(key=lambda item: (-item[2], item[1]))
    print(f"translation-length: {len(findings)} potential risk(s)")
    print(f"thresholds: WARN >= {warning} columns, HIGH >= {args.threshold} columns")
    for severity, line, width, segment, key in findings:
        preview = key.replace("\\n", " ")
        if len(preview) > 100:
            preview = preview[:97] + "..."
        print(f"[{severity}] L{line} segment {segment}: ~{width} columns | {preview}")

    high = sum(item[0] == "HIGH" for item in findings)
    print(f"summary: {high} HIGH, {len(findings) - high} WARN")
    return 1 if args.fail_on_risk and high else 0


if __name__ == "__main__":
    raise SystemExit(main())
