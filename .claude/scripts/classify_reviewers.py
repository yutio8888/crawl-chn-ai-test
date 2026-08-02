#!/usr/bin/env python3
"""Mechanically select reviewers for a DCSS change set.

The classifier is the single source of truth for the shared review pipeline.
It accepts either an immutable git range or an explicit file list and emits one
JSON object on stdout.
"""

from __future__ import annotations

import argparse
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path


CODE_REVIEWER = "zh-code-reviewer"
TRANSLATION_REVIEWER = "translation-reviewer"

TRANSLATION_PREFIXES = (
    "crawl-ref/source/dat/i18n/zh/",
    "crawl-ref/source/dat/descript/zh/",
    "crawl-ref/source/dat/database/zh/",
)
TRANSLATION_GOVERNANCE = {
    "docs/glossary.md",
    "docs/glossary.utf8",
    "docs/decisions.md",
    "docs/spell-naming-rules.md",
}
LOCALIZED_OVERLAY_PREFIX = ".claude/data/message-overlay/monspell"
POLICY_PREFIXES = (
    ".agents/",
    ".claude/",
    ".codex/",
    ".github/",
    ".pi/",
)
POLICY_FILES = {
    "AGENTS.md",
    "CODEX.md",
    "docs/build-workflow.md",
    "docs/dual-agent-workflow.md",
    "docs/zh-testing.md",
}
CODE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx",
    ".java", ".js", ".json", ".mk", ".pl", ".pm", ".py", ".rb",
    ".sh", ".toml", ".ts", ".yml", ".yaml",
}
CODE_BASENAMES = {"Makefile", "makefile", "CMakeLists.txt"}
REVIEW_RESULTS_RE = re.compile(r"^docs/[^/]+-review-results\.md$")


def normalize_path(raw: str) -> str:
    """Return a stable repository-relative POSIX path."""
    path = raw.strip().replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    if posixpath.isabs(path) or (len(path) >= 3 and path[1:3] == ":/"):
        raise ValueError(f"file path must be repository-relative: {raw!r}")
    if ".." in path.split("/"):
        raise ValueError(f"file path may not contain '..': {raw!r}")
    return posixpath.normpath(path) if path else ""


def classify_file(raw: str) -> tuple[str, str]:
    """Return (category, reason) for one repository-relative path."""
    path = normalize_path(raw)
    if not path or path == ".":
        return "ignored", "empty path"

    if REVIEW_RESULTS_RE.fullmatch(path):
        return "mixed", "complete translation review ledger"

    if path in TRANSLATION_GOVERNANCE:
        return "translation", "translation terminology/governance text"

    if path == LOCALIZED_OVERLAY_PREFIX + ".json" or path.startswith(
            LOCALIZED_OVERLAY_PREFIX + "/"):
        return "mixed", "localized overlay manifest/template"

    if any(path.startswith(prefix) for prefix in TRANSLATION_PREFIXES):
        if path.endswith(".txt"):
            return "translation", "Chinese i18n/TextDB text asset"
        # A non-text artifact under a translation tree can affect loading or
        # tooling assumptions, so fail safe to code review.
        return "code", "unrecognized file in Chinese translation tree"

    if path in POLICY_FILES or any(path.startswith(prefix) for prefix in POLICY_PREFIXES):
        return "code", "agent/workflow/policy infrastructure"

    # Anything unknown below crawl-ref/source can affect compilation, runtime,
    # data loading, or packaging.  This is intentionally broader than suffix
    # matching and is the principal fail-safe rule.
    if path.startswith("crawl-ref/source/"):
        return "code", "source-tree change (fail-safe)"

    name = posixpath.basename(path)
    suffix = Path(name).suffix.lower()
    if name in CODE_BASENAMES or suffix in CODE_SUFFIXES:
        return "code", "code or script implementation"

    return "ignored", "outside reviewer-owned paths"


def classify_files(raw_files: list[str], *, source: dict | None = None) -> dict:
    files = sorted({normalize_path(item) for item in raw_files if normalize_path(item)})
    classified = []
    has_code = False
    has_translation = False

    for path in files:
        category, reason = classify_file(path)
        classified.append({"path": path, "category": category, "reason": reason})
        has_code |= category == "code"
        has_translation |= category == "translation"
        if category == "mixed":
            has_code = True
            has_translation = True

    if has_code and has_translation:
        classification = "mixed"
        reviewers = [CODE_REVIEWER, TRANSLATION_REVIEWER]
    elif has_code:
        classification = "code"
        reviewers = [CODE_REVIEWER]
    elif has_translation:
        classification = "translation"
        reviewers = [TRANSLATION_REVIEWER]
    else:
        classification = "none"
        reviewers = []

    return {
        "schema_version": 2,
        "classification": classification,
        "reviewers": reviewers,
        "files": files,
        "classified_files": classified,
        "source": source or {"type": "files"},
    }


def git_changed_files(base: str, head: str, repo: str) -> list[str]:
    command = [
        "git", "-C", repo, "diff", "--no-renames", "--name-only", "-z",
        "--diff-filter=ACDMRTUXB", f"{base}..{head}", "--",
    ]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(message or "git diff failed")
    return [part.decode("utf-8", errors="strict") for part in proc.stdout.split(b"\0") if part]


def read_file_list(path: str) -> list[str]:
    if path == "-":
        return [line.rstrip("\n") for line in sys.stdin]
    return Path(path).read_text(encoding="utf-8").splitlines()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="base revision for base..head")
    parser.add_argument("--head", help="head revision for base..head")
    parser.add_argument("--repo", default=".", help="git repository (default: current directory)")
    parser.add_argument("--files", nargs="*", help="explicit changed file list")
    parser.add_argument("--files-from", help="newline-delimited file list, or - for stdin")
    args = parser.parse_args(argv)

    range_mode = args.base is not None or args.head is not None
    file_mode = args.files is not None or args.files_from is not None
    if range_mode and file_mode:
        parser.error("use either --base/--head or --files/--files-from, not both")
    if range_mode and not (args.base and args.head):
        parser.error("--base and --head must be supplied together")
    if not range_mode and not file_mode:
        parser.error("supply --base/--head or --files/--files-from")
    if args.files is not None and args.files_from is not None:
        parser.error("use either --files or --files-from")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.base is not None:
            files = git_changed_files(args.base, args.head, args.repo)
            source = {"type": "git", "base": args.base, "head": args.head}
        elif args.files_from is not None:
            files = read_file_list(args.files_from)
            source = {"type": "files", "files_from": args.files_from}
        else:
            files = args.files
            source = {"type": "files"}
        print(json.dumps(classify_files(files, source=source), ensure_ascii=False, sort_keys=True))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
