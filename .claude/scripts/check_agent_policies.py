#!/usr/bin/env python3
"""Check Agent/Skill policy drift without duplicating C++ AST scanners."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
CONFIG_ROOTS = [ROOT / ".codex" / "agents", ROOT / ".opencode" / "agents",
                ROOT / ".opencode" / "skills"]

FORBIDDEN = {
    r"Double T_\(\) for Static Arrays": "obsolete persistent T_ pattern",
    r"\bstatic\b[^;]{0,1200}\bT_\(\s*\"": "persistent static T_ initializer",
    r"\bP0\s*\(functional|\bP1\s*\(quality": "obsolete P0/P1 finding model",
    r"Evocations\s*=\s*[\u3400-\u9fff]": "hard-coded terminology rule",
    r"Do\s+\*{0,2}(?:NOT|not)\*{0,2}\s+summarize,\s*filter,\s*or\s*interpret":
        "ban on required log interpretation",
    r"Codex\s*<noreply@anthropic\.com>": "invalid Codex commit trailer",
}


def config_files() -> list[Path]:
    result: list[Path] = []
    for root in CONFIG_ROOTS:
        result.extend(path for path in root.rglob("*") if path.is_file()
                      and path.suffix in {".md", ".toml"})
    return sorted(result)


def main() -> int:
    problems: list[str] = []
    sync = subprocess.run(
        [sys.executable, str(ROOT / ".claude/scripts/sync_agent_policies.py"), "--check"],
        cwd=ROOT, text=True, capture_output=True,
    )
    if sync.returncode:
        problems.extend(line for line in sync.stderr.splitlines() if line.startswith("- "))

    for path in config_files():
        text = path.read_text()
        for pattern, reason in FORBIDDEN.items():
            if re.search(pattern, text, re.MULTILINE | re.DOTALL):
                problems.append(f"- {path.relative_to(ROOT)}: {reason}")

    if problems:
        print("Agent/Skill configuration policy check failed:", file=sys.stderr)
        print("\n".join(problems), file=sys.stderr)
        return 1
    print("Agent/Skill configuration policy check passed.")
    print("C++ source anti-patterns remain delegated to the AST scanners.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
