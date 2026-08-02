#!/usr/bin/env python3
"""Synchronize generated policy blocks in Agent and Skill configuration.

This script edits configuration text only. It intentionally performs no C++
parsing; source anti-patterns belong to the existing AST scanners.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


DEFAULT_ROOT = Path(__file__).resolve().parents[2]
BEGIN = "<!-- BEGIN GENERATED: {name} -->"
END = "<!-- END GENERATED: {name} -->"

TARGETS = {
    "i18n-safety": [
        ".codex/agents/crawl-coder.toml",
        ".codex/agents/zh-code-reviewer.toml",
        ".pi/agents/crawl-coder.md",
        ".pi/agents/zh-code-reviewer.md",
    ],
    "review-contract": [
        ".codex/agents/zh-code-reviewer.toml",
        ".codex/agents/translation-reviewer.toml",
        ".pi/agents/zh-code-reviewer.md",
        ".pi/agents/translation-reviewer.md",
    ],
    "asset-ownership": [
        ".codex/agents/crawl-coder.toml",
        ".codex/agents/zh-translator.toml",
        ".pi/agents/crawl-coder.md",
        ".pi/agents/zh-translator.md",
    ],
    "verification-authoring": [
        ".codex/agents/crawl-coder.toml",
        ".codex/agents/zh-code-reviewer.toml",
        ".pi/agents/crawl-coder.md",
        ".pi/agents/zh-code-reviewer.md",
    ],
    "translation-integrity": [
        ".codex/agents/zh-translator.toml",
        ".pi/agents/zh-translator.md",
    ],
}


def policy_block(root: Path, name: str) -> str:
    body = (root / ".agents" / "policies" / f"{name}.md").read_text().rstrip()
    return f"{BEGIN.format(name=name)}\n{body}\n{END.format(name=name)}"


def replace_block(text: str, name: str, block: str) -> str:
    begin = BEGIN.format(name=name)
    end = END.format(name=name)
    start = text.find(begin)
    finish = text.find(end)
    if start < 0 or finish < 0 or finish < start:
        raise ValueError(f"missing or malformed generated block {name}")
    finish += len(end)
    return text[:start] + block + text[finish:]


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT,
                        help="repository whose policy/config text is checked or updated")
    args = parser.parse_args()
    root = args.root.resolve()

    stale: list[str] = []
    for name, targets in TARGETS.items():
        expected = policy_block(root, name)
        for relative in targets:
            path = root / relative
            original = path.read_text()
            try:
                updated = replace_block(original, name, expected)
            except ValueError as exc:
                stale.append(f"{relative}: {exc}")
                continue
            if updated == original:
                continue
            if args.write:
                path.write_text(updated)
            else:
                stale.append(f"{relative}: stale {name} block")

    if stale:
        print("Agent policy synchronization failed:", file=sys.stderr)
        for problem in stale:
            print(f"- {problem}", file=sys.stderr)
        return 1
    print("Agent policy blocks are synchronized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
