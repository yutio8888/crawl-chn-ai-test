#!/usr/bin/env python3
"""Convert the historical concatenated JSON stream into canonical JSONL.

The original bytes are preserved in ``<path>.v1.raw``. Legacy records remain
available for history but are explicitly marked and cannot satisfy merge gates.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def decode_stream(text: str) -> list[dict]:
    decoder = json.JSONDecoder()
    records: list[dict] = []
    pos = 0
    while pos < len(text):
        while pos < len(text) and text[pos].isspace():
            pos += 1
        if pos >= len(text):
            break
        record, pos = decoder.raw_decode(text, pos)
        if not isinstance(record, dict):
            raise ValueError("review record must be a JSON object")
        records.append(record)
    return records


def migrate(path: Path) -> int:
    original = path.read_text(encoding="utf-8")
    records = decode_stream(original)
    backup = path.with_name(path.name + ".v1.raw")
    if not backup.exists():
        backup.write_text(original, encoding="utf-8")

    lines = []
    for record in records:
        if record.get("agent_type") == "test":
            continue
        if record.get("schema_version") != 2:
            record = dict(record)
            record["schema_version"] = 1
            record["legacy"] = True
        lines.append(json.dumps(record, ensure_ascii=False, separators=(",", ":")))

    temp = path.with_name(path.name + ".tmp")
    temp.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    os.replace(temp, path)
    return len(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default=".claude/metrics/review-log.jsonl")
    args = parser.parse_args()
    count = migrate(Path(args.path))
    print(f"OK: migrated {count} review record(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
