#!/usr/bin/env python3
"""Audit the Phase 1 manifest and require an up-to-date generated sidecar."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from generate_message_overlay import (ManifestError, _read, load_manifest,
                                      render_sidecar, validate_manifest)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--sidecar", type=Path, required=True)
    args = parser.parse_args()
    try:
        manifest = validate_manifest(load_manifest(args.manifest),
                                     _read(args.inventory))
        expected = render_sidecar(manifest)
        actual = args.sidecar.read_text(encoding="utf-8")
    except (ManifestError, OSError, UnicodeError) as exc:
        print(f"message overlay audit error: {exc}", file=sys.stderr)
        return 2
    if actual != expected:
        print("message overlay audit error: generated sidecar drift", file=sys.stderr)
        return 1
    print("message overlay audit: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
