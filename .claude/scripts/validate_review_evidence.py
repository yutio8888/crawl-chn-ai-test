#!/usr/bin/env python3
"""Validate that a merge verdict is backed by an immutable review run."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


VERDICT_CANON = {
    "Go": "go",
    "Conditional Go": "conditional-go",
    "No-Go": "no-go",
    "go": "go",
    "conditional-go": "conditional-go",
    "no-go": "no-go",
}


def fail(message: str) -> None:
    raise ValueError(message)


def load_record(path: Path, review_id: str) -> dict:
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            fail(f"invalid JSONL at {path}:{lineno}: {exc}")
        if record.get("review_id") == review_id:
            return record
    fail(f"review_id not found: {review_id}")


def validate(args: argparse.Namespace) -> dict:
    record = load_record(Path(args.log), args.review_id)
    record_hash = hashlib.sha256(json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    if record.get("schema_version") != 2 or record.get("legacy"):
        fail("only non-legacy schema_version=2 records can approve a merge")
    if record.get("trigger") != "merge-time":
        fail("review trigger must be merge-time")

    expected = {
        "base": args.base,
        "head": args.head,
        "diff_hash": args.diff_hash,
    }
    for key, value in expected.items():
        if record.get(key) != value:
            fail(f"review {key} does not match current merge range")

    verdict = VERDICT_CANON.get(record.get("verdict"))
    if verdict != args.verdict:
        fail("record verdict does not match requested verdict")
    findings = record.get("findings", {})
    blockers = findings.get("blocker")
    needs_fix = findings.get("needs_fix")
    if not isinstance(blockers, int) or not isinstance(needs_fix, int):
        fail("review finding counts are invalid")
    required_verdict = "no-go" if blockers else ("conditional-go" if needs_fix else "go")
    if verdict != required_verdict:
        fail(f"findings require verdict={required_verdict}, got {verdict}")
    if verdict == "no-go":
        fail("No-Go records cannot approve a merge")

    run_id = record.get("run_id")
    raw_log = Path(record.get("raw_log", ""))
    glossary_hash = record.get("glossary_sha256")
    if not run_id or not raw_log.is_file() or not glossary_hash:
        fail("review record is missing run_id, raw log, or glossary hash")

    metadata_path = Path(record.get(
        "run_metadata", f".claude/metrics/verify/{run_id}/metadata.json"))
    if not metadata_path.is_file():
        fail(f"run metadata not found: {metadata_path}")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("status") != "pass":
        fail("review run did not complete with status=pass")
    for key, value in expected.items():
        if metadata.get(key) != value:
            fail(f"run metadata {key} does not match current merge range")
    if metadata.get("glossary_sha256") != glossary_hash:
        fail("review record and run metadata glossary hashes differ")

    raw_hash = hashlib.sha256(raw_log.read_bytes()).hexdigest()
    if record.get("raw_log_sha256") and record["raw_log_sha256"] != raw_hash:
        fail("raw review log hash does not match review record")

    return {
        "review_id": args.review_id,
        "run_id": run_id,
        "raw_log": str(raw_log),
        "raw_log_sha256": raw_hash,
        "review_record_sha256": record_hash,
        "glossary_sha256": glossary_hash,
        "verdict": verdict,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=".claude/metrics/review-log.jsonl")
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--diff-hash", required=True)
    parser.add_argument("--verdict", choices=("go", "conditional-go"), required=True)
    args = parser.parse_args()
    try:
        result = validate(args)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
