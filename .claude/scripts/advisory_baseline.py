#!/usr/bin/env python3
"""Compare scanner JSON findings with a stable, line-number-free baseline."""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path
from typing import Any


IDENTITY_FIELDS = ("file", "rule", "risk", "literal", "receiver", "wrapped")


def identity(finding: dict[str, Any]) -> str:
    payload = {key: finding.get(key) for key in IDENTITY_FIELDS}
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def load_findings(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    findings = payload.get("findings")
    if not isinstance(findings, list):
        raise ValueError(f"{path}: missing findings array")
    return findings


def load_baseline(path: Path) -> collections.Counter[str]:
    if not path.exists():
        return collections.Counter()
    with path.open(encoding="utf-8") as stream:
        payload = json.load(stream)
    if payload.get("schema_version") != 1:
        raise ValueError(f"{path}: unsupported baseline schema")
    return collections.Counter({str(k): int(v) for k, v in payload["findings"].items()})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--write", action="store_true", help="replace baseline from input")
    args = parser.parse_args()

    findings = load_findings(args.input)
    current = collections.Counter(identity(item) for item in findings)
    if args.write:
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "scanner": "scan_string_concat.py --skip-low",
            "identity_fields": list(IDENTITY_FIELDS),
            "findings": dict(sorted(current.items())),
        }
        args.baseline.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"Baseline written: {sum(current.values())} advisory finding(s)")
        return 0

    baseline = load_baseline(args.baseline)
    new = current - baseline
    existing = current & baseline
    resolved = baseline - current
    print(f"Existing baseline warnings: {sum(existing.values())}")
    print(f"New warnings introduced by diff: {sum(new.values())}")
    print(f"Resolved baseline warnings: {sum(resolved.values())}")
    if new:
        print("New advisory findings:")
        remaining = new.copy()
        for finding in findings:
            key = identity(finding)
            if remaining[key] <= 0:
                continue
            remaining[key] -= 1
            location = f"{finding.get('file')}:{finding.get('line')}"
            detail = finding.get("literal") or finding.get("receiver") or "<no detail>"
            print(f"  [{finding.get('risk', 'WARN')}] {location} "
                  f"{finding.get('rule')}: {detail}")
    # Advisory findings never become a blocking failure here.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
