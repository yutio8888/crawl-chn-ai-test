#!/usr/bin/env python3
"""Check Agent/Skill policy drift without duplicating C++ AST scanners."""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import sys


SCRIPT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOTS = [SCRIPT_ROOT / ".codex" / "agents",
                SCRIPT_ROOT / ".claude" / "agents",
                SCRIPT_ROOT / ".claude" / "skills",
                SCRIPT_ROOT / ".opencode" / "agents",
                SCRIPT_ROOT / ".opencode" / "skills"]

FORBIDDEN = {
    r"Double T_\(\) for Static Arrays": "obsolete persistent T_ pattern",
    r"\bstatic\b[^;]{0,1200}\bT_\(\s*\"": "persistent static T_ initializer",
    r"\bP0\s*\(functional|\bP1\s*\(quality": "obsolete P0/P1 finding model",
    r"Evocations\s*=\s*[\u3400-\u9fff]": "hard-coded terminology rule",
    r"Do\s+\*{0,2}(?:NOT|not)\*{0,2}\s+summarize,\s*filter,\s*or\s*interpret":
        "ban on required log interpretation",
    r"Codex\s*<noreply@anthropic\.com>": "invalid Codex commit trailer",
}


def config_files(root: Path) -> list[Path]:
    result: list[Path] = []
    config_roots = [root / ".codex" / "agents", root / ".claude" / "agents",
                    root / ".claude" / "skills", root / ".opencode" / "agents",
                    root / ".opencode" / "skills"]
    for config_root in config_roots:
        result.extend(path for path in config_root.rglob("*") if path.is_file()
                      and path.suffix in {".md", ".toml"})
    return sorted(result)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=SCRIPT_ROOT,
                        help="candidate repository whose generated config is checked")
    args = parser.parse_args()
    root = args.root.resolve()
    problems: list[str] = []
    sync = subprocess.run(
        [sys.executable, str(SCRIPT_ROOT / ".claude/scripts/sync_agent_policies.py"),
         "--check", "--root", str(root)],
        cwd=root, text=True, capture_output=True,
    )
    if sync.returncode:
        problems.extend(line for line in sync.stderr.splitlines() if line.startswith("- "))

    for path in config_files(root):
        text = path.read_text()
        for pattern, reason in FORBIDDEN.items():
            if re.search(pattern, text, re.MULTILINE | re.DOTALL):
                problems.append(f"- {path.relative_to(root)}: {reason}")

    if problems:
        print("Agent/Skill configuration policy check failed:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("Agent/Skill configuration policy check passed.")
    print("C++ source anti-patterns remain delegated to the AST scanners.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
