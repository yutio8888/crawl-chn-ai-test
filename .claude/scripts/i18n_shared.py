#!/usr/bin/env python3
"""Shared utilities for i18n tools — unified source.txt parser and helpers."""

from __future__ import annotations

import ctypes
import ctypes.util
import hashlib
import os
import posixpath
import re
import shutil
import stat
import subprocess
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple


CPP_SOURCE_EXTENSIONS = frozenset({
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp", ".hxx",
})
DEFAULT_SCAN_SKIP_DIRS = frozenset({
    ".git", ".worktrees", "worktrees", "__pycache__", "contrib",
})
CPP_AST_SCAN_SKIP_DIRS = DEFAULT_SCAN_SKIP_DIRS | frozenset({
    "catch2-tests", "rltiles", "util",
})


class AuditRootError(RuntimeError):
    """The bound candidate-data root is missing, unsafe, or inconsistent."""


class AuditInputError(RuntimeError):
    """A review input is not an immutable regular UTF-8 Git blob."""


FULL_GIT_OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
TRUSTED_SYSTEM_PATH = (
    "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
)
GIT_BINARY = shutil.which("git", path=TRUSTED_SYSTEM_PATH) or "/usr/bin/git"
UNSAFE_GIT_ENV = frozenset({
    "BASH_ENV",
    "ENV",
    "CDPATH",
    "GIT_EXEC_PATH",
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_CEILING_DIRECTORIES",
    "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    "GIT_EXTERNAL_DIFF",
    "GIT_DIFF_OPTS",
    "LD_PRELOAD",
    "LD_LIBRARY_PATH",
    "PYTHONHOME",
    "PYTHONPATH",
})


@dataclass(frozen=True)
class AuditInput:
    """One immutable, single-read review input."""

    audit_commit: Optional[str]
    logical_path: str
    relative_path: str
    bytes: bytes
    text: str
    sha256: str


def trusted_git_environment() -> dict[str, str]:
    """Return a deterministic environment for repository object reads."""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in UNSAFE_GIT_ENV and not key.startswith("GIT_")
    }
    env.update({
        "PATH": TRUSTED_SYSTEM_PATH,
        "LC_ALL": "C",
        "LANG": "C",
        "GIT_NO_REPLACE_OBJECTS": "1",
    })
    return env


def _git_toplevel(path: Path, label: str) -> Path:
    try:
        output = subprocess.check_output(
            [GIT_BINARY, "-C", str(path), "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.PIPE,
            env=trusted_git_environment(),
        ).strip()
    except (OSError, subprocess.SubprocessError) as error:
        raise AuditRootError(
            f"{label} is not inside a readable Git worktree: {path}"
        ) from error
    if not output:
        raise AuditRootError(f"{label} Git top-level is empty: {path}")
    return Path(output).resolve()


def resolve_audit_root(default_root: Path) -> Path:
    """Resolve candidate data without allowing target-code/root confusion."""
    configured = os.environ.get("ZH_VERIFY_AUDIT_ROOT")
    if configured is None:
        return default_root.resolve()
    candidate = Path(configured)
    if not candidate.is_absolute():
        raise AuditRootError("ZH_VERIFY_AUDIT_ROOT must be an absolute path")
    try:
        candidate = candidate.resolve(strict=True)
    except OSError as error:
        raise AuditRootError(
            f"ZH_VERIFY_AUDIT_ROOT cannot be resolved: {configured}"
        ) from error
    if not candidate.is_dir():
        raise AuditRootError(
            f"ZH_VERIFY_AUDIT_ROOT is not a directory: {candidate}"
        )
    candidate_top = _git_toplevel(candidate, "ZH_VERIFY_AUDIT_ROOT")
    if candidate_top != candidate:
        raise AuditRootError(
            "ZH_VERIFY_AUDIT_ROOT must equal its real Git top-level: "
            f"{candidate} != {candidate_top}"
        )
    cwd_top = _git_toplevel(Path.cwd(), "current working directory")
    if cwd_top != candidate:
        raise AuditRootError(
            "ZH_VERIFY_AUDIT_ROOT must equal the current working directory "
            f"Git top-level: {candidate} != {cwd_top}"
        )
    return candidate


def _normalized_git_path(value: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or "\x00" in value
        or "\\" in value
        or value.startswith("/")
    ):
        raise AuditInputError("Git blob path must be a normalized relative path")
    normalized = posixpath.normpath(value)
    if (
        normalized != value
        or normalized in ("", ".")
        or any(part in ("", ".", "..") for part in normalized.split("/"))
    ):
        raise AuditInputError("Git blob path must be a normalized relative path")
    return normalized


def _run_git_bytes(repo: Path, *args: str) -> bytes:
    try:
        return subprocess.check_output(
            [GIT_BINARY, "-C", str(repo), *args],
            stderr=subprocess.PIPE,
            env=trusted_git_environment(),
        )
    except (OSError, subprocess.CalledProcessError) as error:
        message = ""
        if isinstance(error, subprocess.CalledProcessError):
            message = error.stderr.decode("utf-8", errors="replace").strip()
        raise AuditInputError(message or f"git {' '.join(args)} failed") from error


def read_regular_git_blob(
    repo: os.PathLike[str] | str,
    full_oid: str,
    normalized_path: str,
    *,
    with_mode: bool = False,
) -> bytes | tuple[str, bytes]:
    """Read one exact regular-file blob from an immutable commit.

    The checkout may be at a different commit.  Tree metadata is inspected
    without following worktree paths, and the blob object named by that tree
    entry is read exactly once.
    """
    if not isinstance(full_oid, str) or not FULL_GIT_OID_RE.fullmatch(full_oid):
        raise AuditInputError("Git commit must be a full lowercase object ID")
    relative_path = _normalized_git_path(normalized_path)
    repo_path = Path(repo)
    resolved = _run_git_bytes(
        repo_path, "rev-parse", "--verify", f"{full_oid}^{{commit}}"
    ).decode("ascii", errors="strict").strip()
    if resolved != full_oid:
        raise AuditInputError("Git commit must be its complete object ID")
    raw = _run_git_bytes(
        repo_path,
        "ls-tree",
        "-z",
        full_oid,
        "--",
        relative_path,
    )
    records = [record for record in raw.split(b"\0") if record]
    if len(records) != 1:
        raise AuditInputError(
            f"Git blob is missing or ambiguous: {full_oid}:{relative_path}"
        )
    try:
        header, listed_path = records[0].split(b"\t", 1)
        mode, entry_type, object_id = header.decode("ascii").split(" ")
        listed = listed_path.decode("utf-8", errors="strict")
    except (UnicodeDecodeError, ValueError) as error:
        raise AuditInputError("invalid Git tree metadata") from error
    if listed != relative_path:
        raise AuditInputError(
            f"Git tree path mismatch: {listed!r} != {relative_path!r}"
        )
    if entry_type != "blob" or mode not in ("100644", "100755"):
        raise AuditInputError(
            f"Git entry is not a regular file: {full_oid}:{relative_path}"
        )
    data = _run_git_bytes(repo_path, "cat-file", "blob", object_id)
    return (mode, data) if with_mode else data


def _review_relative_path(
    audit_root: Path,
    logical_path: os.PathLike[str] | str,
) -> tuple[str, Path]:
    root = Path(os.path.abspath(os.fspath(audit_root)))
    supplied = Path(logical_path)
    absolute = (
        Path(os.path.abspath(os.fspath(supplied)))
        if supplied.is_absolute()
        else root / supplied
    )
    try:
        relative = absolute.relative_to(root).as_posix()
    except ValueError as error:
        raise AuditInputError(
            f"review input is outside audit root: {logical_path}"
        ) from error
    relative = _normalized_git_path(relative)
    return relative, absolute


def _read_regular_worktree_file(path: Path, audit_root: Path) -> bytes:
    current = audit_root
    try:
        relative_parts = path.relative_to(audit_root).parts
    except ValueError as error:
        raise AuditInputError(f"review input is outside audit root: {path}") from error
    for component in relative_parts[:-1]:
        current = current / component
        try:
            parent_info = os.lstat(current)
        except OSError as error:
            raise AuditInputError(
                f"review input parent cannot be inspected: {current}"
            ) from error
        if stat.S_ISLNK(parent_info.st_mode) or not stat.S_ISDIR(
            parent_info.st_mode
        ):
            raise AuditInputError(
                f"review input parent is not a real directory: {current}"
            )
    try:
        info = os.lstat(path)
    except OSError as error:
        raise AuditInputError(f"review input cannot be inspected: {path}") from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise AuditInputError(f"review input is not a regular file: {path}")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    try:
        fd = os.open(path, flags)
    except OSError as error:
        raise AuditInputError(f"review input cannot be opened: {path}") from error
    try:
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)
        ):
            raise AuditInputError(
                f"review input changed between inspection and open: {path}"
            )
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(fd)


def load_review_input(
    audit_root: os.PathLike[str] | str,
    logical_path: os.PathLike[str] | str,
) -> AuditInput:
    """Load one ledger from its bound Git blob or by one safe development read."""
    root = Path(os.path.abspath(os.fspath(audit_root)))
    if _git_toplevel(root, "audit root") != root.resolve():
        raise AuditInputError(f"audit root is not its Git top-level: {root}")
    relative_path, worktree_path = _review_relative_path(root, logical_path)
    audit_commit = os.environ.get("ZH_VERIFY_AUDIT_COMMIT")
    if audit_commit is not None:
        if not FULL_GIT_OID_RE.fullmatch(audit_commit):
            raise AuditInputError(
                "ZH_VERIFY_AUDIT_COMMIT must be a full lowercase object ID"
            )
        try:
            head = subprocess.check_output(
                [
                    GIT_BINARY,
                    "-C",
                    str(root),
                    "rev-parse",
                    "--verify",
                    "HEAD^{commit}",
                ],
                text=True,
                stderr=subprocess.PIPE,
                env=trusted_git_environment(),
            ).strip()
        except (OSError, subprocess.CalledProcessError) as error:
            raise AuditInputError("audit root HEAD cannot be resolved") from error
        if audit_commit != head:
            raise AuditInputError(
                "ZH_VERIFY_AUDIT_COMMIT does not equal audit root HEAD: "
                f"{audit_commit} != {head}"
            )
        data = read_regular_git_blob(root, audit_commit, relative_path)
    else:
        data = _read_regular_worktree_file(worktree_path, root)
    if not isinstance(data, bytes):
        raise AuditInputError("internal Git blob read returned invalid data")
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise AuditInputError(
            f"review input is not strict UTF-8: {relative_path}"
        ) from error
    return AuditInput(
        audit_commit=audit_commit,
        logical_path=relative_path,
        relative_path=relative_path,
        bytes=data,
        text=text,
        sha256=hashlib.sha256(data).hexdigest(),
    )


def review_input_metadata(value: AuditInput) -> dict:
    """Return stable inventory metadata for one already-loaded review input."""
    return {
        "audit_commit": value.audit_commit,
        "logical_path": value.logical_path,
        "input_sha256": value.sha256,
    }


@dataclass
class ScanCoverage:
    """Fail-visible discovery/read accounting shared by i18n scanners."""

    discovered: int = 0
    scanned: int = 0
    failed: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "discovered": self.discovered,
            "scanned": self.scanned,
            "failed": list(self.failed),
        }


def discover_source_files(root: str, extensions=CPP_SOURCE_EXTENSIONS,
                          skip_dirs=DEFAULT_SCAN_SKIP_DIRS) -> List[str]:
    """Return a deterministic source-file inventory or raise on bad input."""
    root = os.path.abspath(root)
    if not os.path.exists(root):
        raise FileNotFoundError(root)
    if os.path.isfile(root):
        if os.path.splitext(root)[1].lower() not in extensions:
            raise ValueError(f"not a supported source file: {root}")
        return [root]
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        for name in sorted(filenames):
            if os.path.splitext(name)[1].lower() in extensions:
                files.append(os.path.join(dirpath, name))
    return files


def read_utf8(path: str) -> str:
    """Read source strictly so encoding/read failures cannot look clean."""
    with open(path, "r", encoding="utf-8", errors="strict") as stream:
        return stream.read()


def has_relevant_parse_error(root, source: bytes) -> bool:
    """Ignore only recoverable standalone preprocessor directive errors."""
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_missing:
            return True
        if node.type == "ERROR":
            fragment = source[node.start_byte:node.end_byte].lstrip()
            line_start = source.rfind(b"\n", 0, node.start_byte) + 1
            line_end = source.find(b"\n", node.end_byte)
            if line_end < 0:
                line_end = len(source)
            line = source[line_start:line_end].lstrip()

            # tree-sitter-cpp can split one preprocessor directive into
            # multiple ERROR nodes (for example '#if TAG == 34' and '34').
            if fragment.startswith(b"#") or line.startswith(b"#"):
                stack.extend(node.children)
                continue

            # This is a standard pointer-to-member invocation. The bundled
            # grammar currently emits an ERROR node for the operator token.
            if (b"this->*" in line
                    and (fragment.strip().startswith(b"this->*")
                         or fragment.strip().startswith(b"->*"))):
                stack.extend(node.children)
                continue

            return True
        stack.extend(node.children)
    return False

# libc towlower for parity with C++ database.cc lowercase_string()
_libc = None
def _get_towlower():
    global _libc
    if _libc is None:
        libc_path = ctypes.util.find_library('c')
        if libc_path:
            _libc = ctypes.CDLL(libc_path)
            _libc.towlower.argtypes = [ctypes.c_uint]
            _libc.towlower.restype = ctypes.c_uint
    return _libc.towlower if _libc else None


@dataclass
class Entry:
    """A single source.txt entry (one %%%% block).

    Represents a key-value pair from a source.txt-format file. The key is
    the English lookup text; the value is the Chinese translation. Both
    may contain literal control characters (\\n, \\t, \\r).

    Attributes:
        key: The English lookup key (original case, no lowercase).
        value: The Chinese translation. Multi-line values are joined with \\n.
            Empty translations are represented as '' (not None).
        key_line: 1-indexed line number of the EN key in the source file.
        value_line: 1-indexed line number of the first ZH value line.
        source_file: Path to the source file.
    """
    key: str
    value: str
    key_line: int
    value_line: int
    source_file: Path = field(default=Path('.'))

    @property
    def is_empty(self) -> bool:
        """True if the translation value is empty or whitespace-only."""
        return not self.value.strip()


def _unescape_hash(s: str) -> str:
    """Convert source.txt \\# escape back to literal #.

    In source.txt, EN keys that start with '#' are written as '\\#' so
    they are not mistaken for comment lines. This converts them back.
    """
    if s.startswith('\\#'):
        return '#' + s[2:]
    return s


def parse_entries(filepath, lowercase_keys=True, unescape_hash=True,
                  require_zh=True) -> list:
    """Parse a %%%%-separated text database file into Entry objects.

    Handles:
        - %%%% block separators (leading/trailing whitespace stripped)
        - Multi-line values (physical newlines joined as \\n)
        - # comment lines (skipped when encountered before a key)
        - \\# escape for key lines starting with literal #
        - Empty blocks (skipped)
        - Blocks with only a key but no value (value is '')

    Args:
        filepath: Path to the source file.
        lowercase_keys: If True, lowercase the key (matching C++ GDBM behavior).
        unescape_hash: If True, convert \\# back to # on key lines.
        require_zh: If True, blocks with no ZH value are still included.

    Returns:
        List of Entry objects in file order.
    """
    entries = []
    if not os.path.exists(filepath):
        return entries

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    key = None
    key_line = 0
    value_line = 0
    value_lines = []
    in_entry = False
    source_path = Path(filepath)

    for line_num, line in enumerate(lines, start=1):
        stripped = line.rstrip('\n').rstrip('\r')

        # Comments are always metadata, never part of entry data
        if stripped.startswith('#'):
            continue

        # %%%% separator — flush current entry
        if stripped.strip() == '%%%%':
            if key is not None:
                value = '\n'.join(value_lines).rstrip('\n')
                entries.append(Entry(
                    key=key,
                    value=value,
                    key_line=key_line,
                    value_line=value_line or key_line + 1,
                    source_file=source_path,
                ))
            key = None
            value_lines = []
            in_entry = True
            continue

        if not in_entry:
            continue

        # First non-empty, non-comment line after %%%% is the key
        if key is None:
            if stripped:
                # Handle \# escape
                if unescape_hash:
                    stripped = _unescape_hash(stripped)
                if lowercase_keys:
                    key = stripped.lower()
                else:
                    key = stripped
                key_line = line_num
        else:
            # Subsequent lines are part of the value
            value_lines.append(stripped)
            if value_line == 0:
                value_line = line_num

    # Flush the last entry
    if key is not None:
        value = '\n'.join(value_lines).rstrip('\n')
        entries.append(Entry(
            key=key,
            value=value,
            key_line=key_line,
            value_line=value_line or key_line + 1,
            source_file=source_path,
        ))

    return entries


# ═══════════════════════════════════════════════════════════════════════
# Backward-compatible interface
# ═══════════════════════════════════════════════════════════════════════


def parse_source_txt(filepath: str) -> OrderedDict:
    """Parse source.txt and return OrderedDict of key -> translation.

    Backward-compatible wrapper around parse_entries(). Keys are lowercased
    to match C++ runtime behavior (case-insensitive lookups via GDBM).

    Use parse_entries() for new code that needs line numbers or per-entry
    metadata.

    Returns:
        OrderedDict with keys in file insertion order.
    """
    entries = parse_entries(filepath, lowercase_keys=True, unescape_hash=True)
    result = OrderedDict()
    for entry in entries:
        result[entry.key] = entry.value
    return result


# ═══════════════════════════════════════════════════════════════════════
# Issue 66 — SourceDB canonical key collision detection
# ═══════════════════════════════════════════════════════════════════════


@dataclass
class PhysicalEntry:
    """A source.txt entry preserving the raw physical key.

    Unlike Entry, this preserves the exact key line as-is (no stripping,
    no lowercasing, no unescape_hash). Used for SourceDB canonical key
    collision detection (Issue 66).

    Attributes:
        raw_key: The physical key line as read (no strip, no transform).
        value: The Chinese translation (multi-line joined with \\n).
        canonical_key: lowercase(raw_key) — the SourceDB canonical form.
        key_line: 1-indexed line number of the key in the source file.
        value_line: 1-indexed line number of the first value line.
        source_file: Path to the source file.
        order: Appearance order (1-based) in the parsed file.
    """
    raw_key: str
    value: str
    canonical_key: str
    key_line: int
    value_line: int
    order: int
    source_file: Path = field(default=Path('.'))

    @property
    def is_empty(self) -> bool:
        return not self.value.strip()


def parse_entries_physical(filepath: str) -> List[PhysicalEntry]:
    """Parse source.txt preserving raw physical keys.

    Canonical key rules (Issue 66 Section 2.1):
    1. raw_key = physical key line as read (no strip).
    2. SourceDB uses trim_keys=false; whitespace belongs to key.
    3. Canonical key = lowercase_string(raw_key). NO \\# decode, NO key unescape.
    4. NO context prefix for source.txt entries (plain key space).

    Returns:
        List of PhysicalEntry in file order.
    """
    entries = []
    if not os.path.exists(filepath):
        return entries

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    raw_key = None
    key_line = 0
    value_line = 0
    value_lines = []
    in_entry = False
    order = 0
    source_path = Path(filepath)

    for line_num, line in enumerate(lines, start=1):
        # Remove line ending for processing, but preserve leading whitespace
        processed = line.rstrip('\n').rstrip('\r')

        # Comments are metadata, skip
        if processed.startswith('#'):
            continue

        # %%%% separator — flush current entry
        # C++ database.cc: !line.compare(0, 4, "%%%%") — starts-with match
        if processed.startswith('%%%%'):
            if raw_key is not None:
                order += 1
                value = '\n'.join(value_lines).rstrip('\n')
                canonical = lowercase_string(raw_key)
                entries.append(PhysicalEntry(
                    raw_key=raw_key,
                    value=value,
                    canonical_key=canonical,
                    key_line=key_line,
                    value_line=value_line or key_line + 1,
                    order=order,
                    source_file=source_path,
                ))
            raw_key = None
            value_lines = []
            value_line = 0
            in_entry = True
            continue

        if not in_entry:
            continue

        # First non-empty line after %%%% is the key — keep raw
        if raw_key is None:
            if processed:
                # raw_key = the physical line content, no transform
                raw_key = processed
                key_line = line_num
        else:
            # C++ database.cc: trim_string_right(line) — strips " \t\n\r" only
            trimmed = processed.rstrip(" \t\n\r")
            value_lines.append(trimmed)
            if value_line == 0:
                value_line = line_num

    # Flush last entry
    if raw_key is not None:
        order += 1
        value = '\n'.join(value_lines).rstrip('\n')
        canonical = lowercase_string(raw_key)
        entries.append(PhysicalEntry(
            raw_key=raw_key,
            value=value,
            canonical_key=canonical,
            key_line=key_line,
            value_line=value_line or key_line + 1,
            order=order,
            source_file=source_path,
        ))

    return entries


# ── Canonical key helpers ──────────────────────────────────────────


def lowercase_string(s: str) -> str:
    """DCSS lowercase_string() — matches C++ stringutil.cc lowercase_string().

    Rules (per C++ implementation):
      - ASCII A-Z: hardcode to a-z (locale-independent, never Turkish dotless i)
      - CJK U+2E80..U+9FFF: pass through unchanged (no case concept)
      - Other non-ASCII without uppercase/lowercase: pass through unchanged
      - Other non-ASCII with case: use str.lower() (towlower equivalent)
    """
    towlower = _get_towlower()
    result = []
    for c in s:
        if 'A' <= c <= 'Z':
            result.append(chr(ord(c) + 32))
        else:
            cp = ord(c)
            if 0x2E80 <= cp <= 0x9FFF:
                result.append(c)
            elif cp > 0x7F and not c.isupper() and not c.islower():
                result.append(c)
            elif towlower and cp > 0x7F:
                # Use libc towlower for non-ASCII case mapping (C++ parity)
                # This handles Turkish İ (U+0130) correctly: → 'i' (single cp)
                lower_cp = towlower(cp)
                if lower_cp != cp and lower_cp != 0:
                    result.append(chr(lower_cp))
                else:
                    result.append(c)
            else:
                result.append(c.lower())
    return ''.join(result)


def compute_canonical_key(raw_key: str) -> str:
    """Compute SourceDB canonical key from raw_key.

    Per Issue 66 Section 2.1 Rule 3:
        Canonical key = DCSS lowercase_string(raw_key)
    NO \\# decode, NO key unescape.
    """
    return lowercase_string(raw_key)


def i18n_escape_key(key: str) -> str:
    """Escape special characters for SourceDB key storage.

    Escapes: backslash (\\), carriage return (\\r), newline (\\n), tab (\\t).
    Produces the representation stored in the database.
    """
    result = key.replace('\\', '\\\\')
    result = result.replace('\r', '\\r')
    result = result.replace('\n', '\\n')
    result = result.replace('\t', '\\t')
    return result


def i18n_unescape_value(value: str) -> str:
    """Unescape source.txt escape sequences — matches C++ database.cc.

    Single-pass left-to-right scanner like C++ i18n_unescape_value():
      \\\\ → \\, \\n → \\n, \\r → \\r, \\t → \\t
      Unknown escapes: \\X → X (drop backslash, keep next char)
    """
    out = []
    i = 0
    while i < len(value):
        if value[i] == '\\' and i + 1 < len(value):
            nxt = value[i + 1]
            if nxt == 'n':
                out.append('\n')
            elif nxt == 'r':
                out.append('\r')
            elif nxt == 't':
                out.append('\t')
            elif nxt == '\\':
                out.append('\\')
            else:
                out.append(nxt)  # unknown: drop backslash, keep char
            i += 2
        else:
            out.append(value[i])
            i += 1
    return ''.join(out)


# ── Value normalization for collision comparison ───────────────────


def trim_string_right(s: str) -> str:
    """C++ trim_string_right(): strip trailing space, tab, newline, CR only."""
    # Explicit character set, NOT rstrip() default (which removes Unicode whitespace)
    while s and s[-1] in " \t\n\r":
        s = s[:-1]
    return s


def trim_leading_newlines(s: str) -> str:
    """C++ _trim_leading_newlines(): strip leading LF only."""
    return s.lstrip('\n')


def source_normalize_value(value: str) -> str:
    """Normalize value for source-level comparison.

    Applies: trim_string_right, trim_leading_newlines, trailing CR/LF removal.
    Does NOT unescape i18n escape sequences.
    """
    v = trim_string_right(value)
    v = trim_leading_newlines(v)
    # Remove trailing \r and \n characters
    v = v.rstrip('\r\n')
    return v


def runtime_normalize_value(value: str) -> str:
    """Normalize value for runtime-level comparison.

    Applies source_normalize_value() plus i18n_unescape_value().
    """
    v = source_normalize_value(value)
    v = i18n_unescape_value(v)
    return v


def classify_value_relation(values: List[str], normalize_fn) -> str:
    """Classify a list of values as 'equal' or 'different' after normalization.

    Args:
        values: List of raw value strings.
        normalize_fn: Normalization function to apply.

    Returns:
        'equal' if all normalized values are identical, else 'different'.
    """
    if not values:
        return 'equal'
    normalized = [normalize_fn(v) for v in values]
    first = normalized[0]
    for v in normalized[1:]:
        if v != first:
            return 'different'
    return 'equal'


# ── Group fingerprint ──────────────────────────────────────────────


def compute_group_fingerprint(definitions: list) -> str:
    """Compute deterministic SHA-256 fingerprint for a collision group.

    Definitions sorted by (order, raw_key) for determinism.
    Each definition contributes: raw_key + '\\x00' + value + '\\x00'
    """
    h = hashlib.sha256()
    sorted_defs = sorted(definitions, key=lambda d: (d.order, d.raw_key))
    for d in sorted_defs:
        h.update(d.raw_key.encode('utf-8'))
        h.update(b'\x00')
        h.update(d.value.encode('utf-8'))
        h.update(b'\x00')
    return h.hexdigest()
