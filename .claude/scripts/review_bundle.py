#!/usr/bin/env python3
"""Create and validate immutable schema-v4 review evidence bundles.

Bundle evidence is shared by all linked worktrees through Git's common
directory.  Every persisted JSON object is canonical and write-once; callers
that perform a final approval should hold :func:`final_gate` for the complete
check-and-act interval.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterator


TRUSTED_SYSTEM_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
GIT_BINARY = shutil.which("git", path=TRUSTED_SYSTEM_PATH) or "/usr/bin/git"
TRUSTED_CLASSIFIER_PATH = ".claude/scripts/classify_reviewers.py"
UNSAFE_CHILD_ENV_EXACT = frozenset(
    {
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
        "MAKEFLAGS",
        "MFLAGS",
        "MAKEFILES",
        "CC",
        "CXX",
        "CFLAGS",
        "CXXFLAGS",
        "CPPFLAGS",
        "LDFLAGS",
    }
)

BUNDLE_SCHEMA = "dcss-zh-review-bundle-v4"
READINESS_SCHEMA = "dcss-zh-review-readiness-v2"
FINDINGS_INPUT_SCHEMA = "dcss-zh-review-findings-v1"
VERIFICATION_CONTRACT = "dcss-zh-review-v4"
LEGACY_BUNDLE_SCHEMA = "dcss-zh-review-bundle-v3"
LEGACY_READINESS_SCHEMA = "dcss-zh-review-readiness-v1"
ATTEMPT_COMPLETION_SCHEMA = "dcss-zh-final-attempt-v1"
FINAL_APPROVAL_SCHEMA = "dcss-zh-final-approval-v1"
RUNNING_SCHEMA = "dcss-zh-final-running-v1"
CONTRACT_SCHEMA = "dcss-zh-final-gate-contract-v1"
CONTROL_PLANE_SCHEMA = "dcss-zh-control-plane-v1"
EVIDENCE_PARTS = ("zh-review-evidence", "v4")
LEGACY_EVIDENCE_PARTS = ("zh-review-evidence", "v3")
IDENTITY_FIELDS = (
    "schema",
    "target_head",
    "candidate_head",
    "diff_sha256",
    "glossary_sha256",
)
MANIFEST_FIELDS = frozenset((*IDENTITY_FIELDS, "routing_sha256"))
READINESS_FIELDS = frozenset(
    (
        "schema",
        "bundle_id",
        "bundle_sha256",
        "routing_sha256",
        "reviewer",
        "findings",
        "ready",
    )
)
LEGACY_FINDING_FIELDS = frozenset(("blocker", "needs_fix", "suggestion"))
FINDINGS_INPUT_FIELDS = frozenset(
    ("schema", "bundle_id", "bundle_sha256", "routing_sha256", "reviewer", "findings")
)
FINDING_FIELDS = frozenset(("id", "severity", "file", "line", "evidence", "impact", "fix"))
TRANSLATION_FINDING_FIELDS = frozenset((*FINDING_FIELDS, "english", "chinese"))
FINDING_SEVERITIES = frozenset(("blocker", "needs_fix", "suggestion"))
MAX_FINDINGS_INPUT_BYTES = 1024 * 1024
MAX_FINDINGS = 200
MAX_FINDING_ID_LENGTH = 64
MAX_FINDING_FILE_LENGTH = 512
MAX_FINDING_TEXT_LENGTH = 4000
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ROLE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
FINDING_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.+:-]{0,191}$")
LOCK_NAME = ".bundle.lock"
RUNNING_NAME = "running.json"
APPROVAL_NAME = "final-approval.json"
COMPLETION_NAME = "completion.json"

MERGEABLE = 0
READINESS_REQUIRED = 10
FINAL_GATE_REQUIRED = 11
FINAL_GATE_RUNNING = 12
FINAL_APPROVAL_REQUIRED = 13
EVIDENCE_FAILED = 14
STALE_EVIDENCE = 15
INVALID_EVIDENCE = 16
INTERNAL_ERROR = 20
LEGACY_READ_ONLY = 17

STATE_NAMES = {
    MERGEABLE: "MERGEABLE",
    READINESS_REQUIRED: "READINESS_REQUIRED",
    FINAL_GATE_REQUIRED: "FINAL_GATE_REQUIRED",
    FINAL_GATE_RUNNING: "FINAL_GATE_RUNNING",
    FINAL_APPROVAL_REQUIRED: "FINAL_APPROVAL_REQUIRED",
    EVIDENCE_FAILED: "EVIDENCE_FAILED",
    STALE_EVIDENCE: "STALE_EVIDENCE",
    INVALID_EVIDENCE: "INVALID_EVIDENCE",
    INTERNAL_ERROR: "INTERNAL_ERROR",
    LEGACY_READ_ONLY: "LEGACY_READ_ONLY",
}


class ReviewBundleError(ValueError):
    """Base class for a fail-closed review bundle error."""


class ContentConflictError(ReviewBundleError):
    """A deterministic object already exists with different content."""


class UnsafeObjectError(ReviewBundleError):
    """An evidence path contains a symlink, temporary, or special object."""


class StaleEvidenceError(ReviewBundleError):
    """A dead running marker or abandoned staging object requires recovery."""


def canonical_json_bytes(value: Any) -> bytes:
    """Return the schema's canonical UTF-8 JSON representation."""
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ReviewBundleError(f"value is not canonical JSON: {exc}") from exc
    return text.encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _trusted_child_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in list(environment):
        if name in UNSAFE_CHILD_ENV_EXACT or name.startswith(
            ("GIT_CONFIG_", "ZH_VERIFY_", "ZH_RUNTIME_")
        ):
            environment.pop(name, None)
    environment["PATH"] = TRUSTED_SYSTEM_PATH
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment


def _run_git(repo: os.PathLike[str] | str, *args: str) -> bytes:
    proc = subprocess.run(
        [GIT_BINARY, *args],
        cwd=os.fspath(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=_trusted_child_environment(),
    )
    if proc.returncode:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ReviewBundleError(message or f"git {' '.join(args)} failed")
    return proc.stdout


def _git_text(repo: os.PathLike[str] | str, *args: str) -> str:
    try:
        return _run_git(repo, *args).decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as exc:
        raise ReviewBundleError("git returned non-UTF-8 path metadata") from exc


def git_top_level(repo: os.PathLike[str] | str = ".") -> Path:
    value = _git_text(repo, "rev-parse", "--path-format=absolute", "--show-toplevel")
    path = Path(value)
    _require_directory(path, "Git top-level")
    return path


def git_common_dir(repo: os.PathLike[str] | str = ".") -> Path:
    """Resolve the absolute common directory shared by linked worktrees."""
    value = _git_text(
        repo, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    path = Path(value)
    if not path.is_absolute():
        raise ReviewBundleError("git-common-dir was not absolute")
    _require_directory(path, "Git common directory")
    return path


def resolve_commit(repo: os.PathLike[str] | str, revision: str) -> str:
    if not revision or revision.startswith("-"):
        raise ReviewBundleError("revision must be a non-option Git revision")
    value = _git_text(repo, "rev-parse", "--verify", f"{revision}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40,64}", value):
        raise ReviewBundleError(f"Git returned an invalid commit id: {value!r}")
    return value


def diff_bytes(repo: os.PathLike[str] | str, base: str, head: str) -> bytes:
    """Return raw stdout from the required immutable binary diff command."""
    return _run_git(
        repo,
        "diff",
        "--no-ext-diff",
        "--no-textconv",
        "--binary",
        "--full-index",
        f"{base}..{head}",
        "--",
    )


def diff_sha256(repo: os.PathLike[str] | str, base: str, head: str) -> str:
    return sha256_bytes(diff_bytes(repo, base, head))


def _utc_timestamp_ns() -> str:
    return f"{time.time_ns()}"


def _safe_relative_path(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ReviewBundleError(f"{label} must be a non-empty relative path")
    path = Path(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ReviewBundleError(f"{label} must be a normalized relative path")
    normalized = path.as_posix()
    if normalized != value.replace(os.sep, "/"):
        raise ReviewBundleError(f"{label} must be a normalized relative path")
    return normalized


def _assert_checkout(
    repo: os.PathLike[str] | str, expected_head: str, label: str
) -> Path:
    top = git_top_level(repo)
    actual_head = resolve_commit(top, "HEAD")
    if actual_head != expected_head:
        raise ReviewBundleError(
            f"{label} checkout HEAD does not match bundle: {actual_head} != {expected_head}"
        )
    dirty = _run_git(top, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if dirty:
        raise ReviewBundleError(f"{label} checkout is dirty: {top}")
    return top


def _assert_ancestor(
    repo: os.PathLike[str] | str, target_head: str, candidate_head: str
) -> None:
    proc = subprocess.run(
        [GIT_BINARY, "merge-base", "--is-ancestor", target_head, candidate_head],
        cwd=os.fspath(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=_trusted_child_environment(),
    )
    if proc.returncode == 1:
        raise ReviewBundleError("bundle target_head is not an ancestor of candidate_head")
    if proc.returncode:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ReviewBundleError(message or "git merge-base --is-ancestor failed")


def _git_blob(
    repo: os.PathLike[str] | str, commit: str, relative_path: str
) -> tuple[str, bytes]:
    relative_path = _safe_relative_path(relative_path, "control-plane path")
    raw = _run_git(repo, "ls-tree", "-z", commit, "--", relative_path)
    records = [record for record in raw.split(b"\0") if record]
    if len(records) != 1:
        raise ReviewBundleError(
            f"control-plane file is absent from target commit: {relative_path}"
        )
    try:
        header, listed_path = records[0].split(b"\t", 1)
        mode, object_type, object_id = header.decode("ascii").split(" ")
        listed = listed_path.decode("utf-8", errors="strict")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ReviewBundleError("invalid git tree metadata for control-plane file") from exc
    if listed != relative_path or object_type != "blob" or mode not in ("100644", "100755"):
        raise UnsafeObjectError(
            f"control-plane entry is not a regular target-head file: {relative_path}"
        )
    return mode, _run_git(repo, "cat-file", "blob", object_id)


def _path_under_checkout(
    checkout: Path, supplied: os.PathLike[str] | str, label: str
) -> tuple[Path, str]:
    raw = Path(supplied)
    path = raw if raw.is_absolute() else checkout / raw
    path = Path(os.path.abspath(os.fspath(path)))
    top = Path(os.path.abspath(os.fspath(checkout)))
    try:
        relative = path.relative_to(top).as_posix()
    except ValueError as exc:
        raise ReviewBundleError(f"{label} must be under the target checkout") from exc
    relative = _safe_relative_path(relative, label)
    current = top
    for part in Path(relative).parts:
        current = current / part
        info = _lstat(current)
        if info is None:
            raise ReviewBundleError(f"{label} does not exist: {current}")
        if stat.S_ISLNK(info.st_mode):
            raise UnsafeObjectError(f"{label} path may not contain symlinks: {current}")
    _require_regular_file(path, label)
    return path, relative


def _lstat(path: Path) -> os.stat_result | None:
    try:
        return path.lstat()
    except FileNotFoundError:
        return None


def _require_directory(path: Path, label: str = "directory") -> None:
    info = _lstat(path)
    if info is None:
        raise ReviewBundleError(f"{label} does not exist: {path}")
    if stat.S_ISLNK(info.st_mode):
        raise UnsafeObjectError(f"{label} may not be a symlink: {path}")
    if not stat.S_ISDIR(info.st_mode):
        raise UnsafeObjectError(f"{label} is not a directory: {path}")


def _require_regular_file(path: Path, label: str = "file") -> os.stat_result:
    info = _lstat(path)
    if info is None:
        raise ReviewBundleError(f"{label} does not exist: {path}")
    if stat.S_ISLNK(info.st_mode):
        raise UnsafeObjectError(f"{label} may not be a symlink: {path}")
    if not stat.S_ISREG(info.st_mode):
        raise UnsafeObjectError(f"{label} is not a regular file: {path}")
    return info


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _ensure_child_directory(parent: Path, name: str) -> Path:
    if not name or name in (".", "..") or "/" in name or os.sep in name:
        raise ReviewBundleError(f"invalid evidence directory name: {name!r}")
    _require_directory(parent)
    child = parent / name
    info = _lstat(child)
    if info is None:
        try:
            os.mkdir(child, 0o700)
            _fsync_directory(parent)
        except FileExistsError:
            pass
        info = _lstat(child)
    if info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise UnsafeObjectError(f"evidence directory is unsafe: {child}")
    return child


def evidence_root(
    repo: os.PathLike[str] | str = ".", *, create: bool = False
) -> Path:
    common = git_common_dir(repo)
    root = common
    for part in EVIDENCE_PARTS:
        if create:
            root = _ensure_child_directory(root, part)
        else:
            root = root / part
            _require_directory(root, "review evidence directory")
    return root


def legacy_evidence_root(repo: os.PathLike[str] | str = ".") -> Path:
    """Return the historical schema-v3 evidence root without creating it."""
    root = git_common_dir(repo)
    for part in LEGACY_EVIDENCE_PARTS:
        root = root / part
        _require_directory(root, "legacy review evidence directory")
    return root


def _is_temp_name(name: str) -> bool:
    lower = name.lower()
    return (
        lower.startswith(".tmp")
        or lower.startswith("tmp-")
        or lower.startswith(".staging-")
        or lower.startswith("staging-")
        or lower.endswith(".tmp")
        or ".tmp-" in lower
    )


def _reject_unsafe_objects(directory: Path, *, reject_temp_names: bool = True) -> None:
    _require_directory(directory)
    with os.scandir(directory) as entries:
        for entry in entries:
            path = Path(entry.path)
            if entry.is_symlink():
                raise UnsafeObjectError(f"symlink evidence object rejected: {path}")
            if reject_temp_names and _is_temp_name(entry.name):
                raise UnsafeObjectError(f"temporary evidence object rejected: {path}")
            if entry.is_dir(follow_symlinks=False):
                _reject_unsafe_objects(path, reject_temp_names=reject_temp_names)
            elif not entry.is_file(follow_symlinks=False):
                raise UnsafeObjectError(f"special evidence object rejected: {path}")


def _read_regular_bytes(path: Path) -> bytes:
    before = _require_regular_file(path)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            raise UnsafeObjectError(f"evidence object changed while opening: {path}")
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        os.close(fd)


def _rename_noreplace(source: Path, target: Path) -> None:
    """Atomically rename without replacing an existing deterministic object."""
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is not None:
        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
        result = renameat2(
            -100,
            os.fsencode(source),
            -100,
            os.fsencode(target),
            1,  # RENAME_NOREPLACE
        )
        if result == 0:
            return
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise FileExistsError(error, os.strerror(error), os.fspath(target))
        if error not in (errno.ENOSYS, errno.EINVAL):
            raise OSError(error, os.strerror(error), os.fspath(target))

    # Portable fail-closed fallback.  link() performs the no-replace atomic
    # publication; unlinking the source completes the same-directory move.
    os.link(source, target, follow_symlinks=False)
    os.unlink(source)


def atomic_write_once(path: os.PathLike[str] | str, data: bytes) -> bool:
    """Durably publish *data* once; return False for identical existing data."""
    if not isinstance(data, bytes):
        raise TypeError("atomic_write_once data must be bytes")
    target = Path(path)
    parent = target.parent
    _require_directory(parent, "evidence object parent")

    existing = _lstat(target)
    if existing is not None:
        if stat.S_ISLNK(existing.st_mode) or not stat.S_ISREG(existing.st_mode):
            raise UnsafeObjectError(f"deterministic evidence object is unsafe: {target}")
        if _read_regular_bytes(target) == data:
            return False
        raise ContentConflictError(f"deterministic evidence content conflict: {target}")

    temp = parent / f".tmp-{target.name}-{os.getpid()}-{secrets.token_hex(8)}"
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(temp, flags, 0o600)
    published = False
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        os.close(fd)
        fd = -1
        try:
            _rename_noreplace(temp, target)
            published = True
        except FileExistsError:
            current = _lstat(target)
            if current is None or stat.S_ISLNK(current.st_mode) or not stat.S_ISREG(current.st_mode):
                raise UnsafeObjectError(
                    f"deterministic evidence object raced with unsafe content: {target}"
                )
            if _read_regular_bytes(target) != data:
                raise ContentConflictError(
                    f"deterministic evidence content conflict: {target}"
                )
            return False
        _fsync_directory(parent)
        return True
    finally:
        if fd >= 0:
            os.close(fd)
        if not published:
            info = _lstat(temp)
            if info is not None:
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                    raise UnsafeObjectError(f"temporary object became unsafe: {temp}")
                os.unlink(temp)


def _atomic_publish_directory(source: Path, target: Path) -> None:
    """Publish a fully fsynced staging directory without replacing evidence."""
    _require_directory(source, "attempt staging directory")
    _require_directory(target.parent, "attempts directory")
    libc = ctypes.CDLL(None, use_errno=True)
    renameat2 = getattr(libc, "renameat2", None)
    if renameat2 is None:
        raise OSError(errno.ENOSYS, "atomic no-replace directory rename is unavailable")
    renameat2.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    renameat2.restype = ctypes.c_int
    result = renameat2(-100, os.fsencode(source), -100, os.fsencode(target), 1)
    if result:
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise ContentConflictError(f"attempt id already exists: {target.name}")
        raise OSError(error, os.strerror(error), os.fspath(target))
    _fsync_directory(target.parent)


def _fsync_tree(directory: Path) -> None:
    _require_directory(directory, "attempt staging directory")
    with os.scandir(directory) as entries:
        for entry in entries:
            path = Path(entry.path)
            if entry.is_symlink():
                raise UnsafeObjectError(f"staging symlink rejected: {path}")
            if entry.is_dir(follow_symlinks=False):
                _fsync_tree(path)
            elif entry.is_file(follow_symlinks=False):
                flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
                fd = os.open(path, flags)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            else:
                raise UnsafeObjectError(f"staging special object rejected: {path}")
    _fsync_directory(directory)


def _remove_staging_directory(path: Path) -> None:
    """Remove only a validated, bundle-local staging directory."""
    if not path.name.startswith(".staging-"):
        raise UnsafeObjectError(f"refusing to remove non-staging path: {path}")
    info = _lstat(path)
    if info is None:
        return
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise UnsafeObjectError(f"staging recovery target is unsafe: {path}")
    _reject_unsafe_objects(path, reject_temp_names=False)
    shutil.rmtree(path)
    _fsync_directory(path.parent)


@contextlib.contextmanager
def bundle_lock(
    bundle_directory: os.PathLike[str] | str,
    *,
    exclusive: bool = True,
    blocking: bool = True,
) -> Iterator[int]:
    """Hold the bundle-level advisory flock used by writers and final gates."""
    directory = Path(bundle_directory)
    _require_directory(directory, "bundle directory")
    lock_path = directory / LOCK_NAME
    create_flags = (
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    created = False
    try:
        fd = os.open(lock_path, create_flags, 0o600)
        created = True
    except FileExistsError:
        before = _require_regular_file(lock_path, "bundle lock")
        fd = os.open(
            lock_path,
            os.O_RDWR | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        opened = os.fstat(fd)
        if (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino):
            os.close(fd)
            raise UnsafeObjectError("bundle lock changed while opening")
    if created:
        _fsync_directory(directory)
    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    if not blocking:
        operation |= fcntl.LOCK_NB
    try:
        fcntl.flock(fd, operation)
        yield fd
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def _validate_sha256(value: str, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        raise ReviewBundleError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _validate_routing(routing: Any, target_head: str, candidate_head: str) -> list[str]:
    if not isinstance(routing, dict):
        raise ReviewBundleError("classifier output must be a JSON object")
    source = routing.get("source")
    if not isinstance(source, dict) or source.get("type") != "git":
        raise ReviewBundleError("routing must identify its immutable git source")
    if source.get("base") != target_head or source.get("head") != candidate_head:
        raise ReviewBundleError("routing source is not bound to the exact target/candidate heads")
    reviewers = routing.get("reviewers")
    if not isinstance(reviewers, list):
        raise ReviewBundleError("routing.reviewers must be a list")
    result: list[str] = []
    for role in reviewers:
        if not isinstance(role, str) or not ROLE_RE.fullmatch(role):
            raise ReviewBundleError(f"invalid reviewer role in routing: {role!r}")
        if role in result:
            raise ReviewBundleError(f"duplicate reviewer role in routing: {role}")
        result.append(role)
    return result


def generate_routing(
    repo: os.PathLike[str] | str,
    classifier: os.PathLike[str] | str,
    target_head: str,
    candidate_head: str,
) -> dict[str, Any]:
    """Execute a trusted classifier for the exact immutable commit pair."""
    top = git_top_level(repo)
    classifier_path = Path(classifier)
    if not classifier_path.is_absolute():
        classifier_path = top / classifier_path
    info = _require_regular_file(classifier_path, "trusted classifier")
    if stat.S_ISLNK(info.st_mode):  # Kept explicit for audit readability.
        raise UnsafeObjectError(f"trusted classifier may not be a symlink: {classifier_path}")
    if classifier_path.suffix == ".py":
        command = [sys.executable, os.fspath(classifier_path)]
    elif os.access(classifier_path, os.X_OK):
        command = [os.fspath(classifier_path)]
    else:
        raise ReviewBundleError("trusted classifier is not executable")
    command.extend(
        (
            "--repo",
            os.fspath(top),
            "--base",
            target_head,
            "--head",
            candidate_head,
        )
    )
    proc = subprocess.run(
        command,
        cwd=top,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=_trusted_child_environment(),
    )
    if proc.returncode:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ReviewBundleError(message or "trusted classifier failed")
    try:
        routing = json.loads(proc.stdout.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewBundleError(f"trusted classifier emitted invalid JSON: {exc}") from exc
    _validate_routing(routing, target_head, candidate_head)
    # Round-tripping now guarantees that persisted routing contains only JSON
    # values and that its hash is independent of classifier whitespace.
    canonical_json_bytes(routing)
    return routing


def generate_routing_from_target(
    repo: os.PathLike[str] | str,
    target_head: str,
    candidate_head: str,
) -> dict[str, Any]:
    """Execute the classifier blob committed at the immutable target head."""
    top = git_top_level(repo)
    _mode, classifier_bytes = _git_blob(
        top, target_head, TRUSTED_CLASSIFIER_PATH
    )
    command = [
        sys.executable,
        "-",
        "--repo",
        os.fspath(top),
        "--base",
        target_head,
        "--head",
        candidate_head,
    ]
    proc = subprocess.run(
        command,
        cwd=top,
        input=classifier_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=_trusted_child_environment(),
    )
    if proc.returncode:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ReviewBundleError(message or "target-head classifier failed")
    try:
        routing = json.loads(proc.stdout.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewBundleError(
            f"target-head classifier emitted invalid JSON: {exc}"
        ) from exc
    _validate_routing(routing, target_head, candidate_head)
    canonical_json_bytes(routing)
    return routing


def _identity_from_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    return {field: manifest[field] for field in IDENTITY_FIELDS}


def _prepare_bundle(
    repo: os.PathLike[str] | str,
    target: str,
    candidate: str,
    glossary_sha256: str,
    classifier: os.PathLike[str] | str,
    *,
    check_clean: bool,
) -> dict[str, Any]:
    glossary_sha256 = _validate_sha256(glossary_sha256, "glossary_sha256")
    target_head = resolve_commit(repo, target)
    candidate_head = resolve_commit(repo, candidate)
    _assert_ancestor(repo, target_head, candidate_head)
    if check_clean:
        candidate_top = _assert_checkout(repo, candidate_head, "candidate")
        actual_glossary_sha256 = _candidate_glossary_sha256(candidate_top)
        if actual_glossary_sha256 != glossary_sha256:
            raise ReviewBundleError(
                "supplied glossary_sha256 does not match the candidate checkout"
            )
    digest = diff_sha256(repo, target_head, candidate_head)
    routing = generate_routing(repo, classifier, target_head, candidate_head)
    routing_bytes = canonical_json_bytes(routing)
    trusted_routing = generate_routing_from_target(
        repo, target_head, candidate_head
    )
    if canonical_json_bytes(trusted_routing) != routing_bytes:
        raise ReviewBundleError(
            "supplied classifier output does not match the target-head classifier"
        )
    routing_digest = sha256_bytes(routing_bytes)
    manifest = {
        "schema": BUNDLE_SCHEMA,
        "target_head": target_head,
        "candidate_head": candidate_head,
        "diff_sha256": digest,
        "glossary_sha256": glossary_sha256,
        "routing_sha256": routing_digest,
    }
    identity = _identity_from_manifest(manifest)
    bundle_id = sha256_bytes(canonical_json_bytes(identity))
    manifest_bytes = canonical_json_bytes(manifest)
    common = git_common_dir(repo)
    path = common.joinpath(*EVIDENCE_PARTS, bundle_id)
    return {
        "bundle": manifest,
        "bundle_id": bundle_id,
        "bundle_path": os.fspath(path),
        "bundle_sha256": sha256_bytes(manifest_bytes),
        "routing": routing,
    }


def describe_bundle(
    repo: os.PathLike[str] | str,
    target: str,
    candidate: str,
    glossary_sha256: str,
    classifier: os.PathLike[str] | str,
    *,
    check_clean: bool = True,
) -> dict[str, Any]:
    """Describe the deterministic bundle without writing evidence."""
    return _prepare_bundle(
        repo,
        target,
        candidate,
        glossary_sha256,
        classifier,
        check_clean=check_clean,
    )


def _reject_unknown_top_level(bundle_path: Path) -> None:
    allowed = {
        LOCK_NAME,
        "bundle.json",
        "routing.json",
        "readiness",
        "attempts",
        RUNNING_NAME,
        APPROVAL_NAME,
    }
    with os.scandir(bundle_path) as entries:
        for entry in entries:
            if entry.name not in allowed:
                raise UnsafeObjectError(f"unknown bundle object rejected: {entry.path}")
            if entry.name in ("readiness", "attempts"):
                if not entry.is_dir(follow_symlinks=False):
                    raise UnsafeObjectError(f"bundle child is not a directory: {entry.path}")
            elif not entry.is_file(follow_symlinks=False):
                raise UnsafeObjectError(f"bundle object is not a regular file: {entry.path}")


def create_bundle(
    repo: os.PathLike[str] | str,
    target: str,
    candidate: str,
    glossary_sha256: str,
    classifier: os.PathLike[str] | str,
) -> dict[str, Any]:
    """Create a deterministic, immutable bundle and routing record."""
    description = _prepare_bundle(
        repo,
        target,
        candidate,
        glossary_sha256,
        classifier,
        check_clean=True,
    )
    root = evidence_root(repo, create=True)
    bundle_path = _ensure_child_directory(root, description["bundle_id"])
    with bundle_lock(bundle_path):
        _reject_unsafe_objects(bundle_path)
        _reject_unknown_top_level(bundle_path)
        routing_created = atomic_write_once(
            bundle_path / "routing.json", canonical_json_bytes(description["routing"])
        )
        bundle_created = atomic_write_once(
            bundle_path / "bundle.json", canonical_json_bytes(description["bundle"])
        )
        status = _validate_bundle_locked(repo, bundle_path, check_clean=True)
    result = dict(description)
    result.update(status)
    result["created"] = {
        "bundle": bundle_created,
        "routing": routing_created,
    }
    return result


def _resolve_bundle_path(
    repo: os.PathLike[str] | str, bundle: os.PathLike[str] | str
) -> Path:
    raw = Path(bundle)
    if raw.is_absolute() or len(raw.parts) > 1:
        path = Path(os.path.abspath(os.fspath(raw)))
        roots: list[Path] = []
        for resolver in (evidence_root, legacy_evidence_root):
            try:
                roots.append(Path(os.path.abspath(os.fspath(resolver(repo)))))
            except ReviewBundleError:
                pass
        if path.parent not in roots:
            raise ReviewBundleError("bundle path is outside the v3/v4 evidence roots")
    else:
        path = git_common_dir(repo).joinpath(*EVIDENCE_PARTS, raw)
        if _lstat(path) is None:
            path = git_common_dir(repo).joinpath(*LEGACY_EVIDENCE_PARTS, raw)
    if not SHA256_RE.fullmatch(path.name):
        raise ReviewBundleError("bundle selector must end in its 64-character bundle id")
    _require_directory(path, "bundle directory")
    return path


def _load_canonical_object(path: Path) -> tuple[dict[str, Any], bytes]:
    data = _read_regular_bytes(path)
    try:
        value = json.loads(data.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewBundleError(f"invalid JSON evidence object {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReviewBundleError(f"evidence object must be a JSON object: {path}")
    if canonical_json_bytes(value) != data:
        raise ReviewBundleError(f"evidence object is not canonical JSON: {path}")
    return value, data


def _validate_count(value: Any, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReviewBundleError(f"{label} must be a non-negative integer")
    return value


def _validate_finding_text(value: Any, label: str, *, limit: int) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise ReviewBundleError(f"{label} must be non-empty UTF-8 text")
    if len(value) > limit:
        raise ReviewBundleError(f"{label} exceeds the {limit}-character limit")
    return value


def _validate_findings(findings: Any, reviewer: str) -> list[dict[str, Any]]:
    if not isinstance(findings, list):
        raise ReviewBundleError("findings must be a JSON array")
    if len(findings) > MAX_FINDINGS:
        raise ReviewBundleError(f"findings exceeds the {MAX_FINDINGS}-item limit")
    required_fields = (
        TRANSLATION_FINDING_FIELDS
        if reviewer == "translation-reviewer"
        else FINDING_FIELDS
    )
    result: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, finding in enumerate(findings):
        label = f"findings[{index}]"
        if not isinstance(finding, dict):
            raise ReviewBundleError(f"{label} fields do not match the reviewer schema")
        actual_fields = frozenset(finding)
        if actual_fields != required_fields:
            missing = sorted(required_fields - actual_fields)
            unknown = sorted(actual_fields - required_fields)
            detail = []
            if missing:
                detail.append("missing " + ", ".join(missing))
            if unknown:
                detail.append("unknown " + ", ".join(unknown))
            raise ReviewBundleError(
                f"{label} fields do not match the reviewer schema: {'; '.join(detail)}"
            )
        finding_id = finding.get("id")
        if not isinstance(finding_id, str) or not FINDING_ID_RE.fullmatch(finding_id):
            raise ReviewBundleError(f"{label}.id is invalid")
        if finding_id in seen_ids:
            raise ReviewBundleError(f"duplicate finding id: {finding_id}")
        seen_ids.add(finding_id)
        if finding.get("severity") not in FINDING_SEVERITIES:
            raise ReviewBundleError(f"{label}.severity is invalid")
        _validate_finding_text(
            finding.get("file"), f"{label}.file", limit=MAX_FINDING_FILE_LENGTH
        )
        _safe_relative_path(finding["file"], f"{label}.file")
        line = finding.get("line")
        if isinstance(line, bool) or not isinstance(line, int) or not 1 <= line <= 10_000_000:
            raise ReviewBundleError(f"{label}.line must be an integer from 1 to 10000000")
        for field in ("evidence", "impact", "fix"):
            _validate_finding_text(
                finding.get(field), f"{label}.{field}", limit=MAX_FINDING_TEXT_LENGTH
            )
        if reviewer == "translation-reviewer":
            for field in ("english", "chinese"):
                _validate_finding_text(
                    finding.get(field), f"{label}.{field}", limit=MAX_FINDING_TEXT_LENGTH
                )
        result.append(dict(finding))
    return result


def _load_findings_input(
    path: os.PathLike[str] | str,
    *,
    reviewer: str,
    bundle_id: str,
    bundle_sha256: str,
    routing_sha256: str,
) -> list[dict[str, Any]]:
    input_path = Path(path)
    info = _require_regular_file(input_path, "findings JSON")
    if info.st_size > MAX_FINDINGS_INPUT_BYTES:
        raise ReviewBundleError(
            f"findings JSON exceeds the {MAX_FINDINGS_INPUT_BYTES}-byte limit"
        )
    data = _read_regular_bytes(input_path)
    if len(data) > MAX_FINDINGS_INPUT_BYTES:
        raise ReviewBundleError(
            f"findings JSON exceeds the {MAX_FINDINGS_INPUT_BYTES}-byte limit"
        )
    try:
        value = json.loads(data.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewBundleError(f"findings JSON is invalid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict) or frozenset(value) != FINDINGS_INPUT_FIELDS:
        raise ReviewBundleError("findings JSON fields do not match the input schema")
    if canonical_json_bytes(value) != data:
        raise ReviewBundleError("findings JSON is not canonical JSON")
    expected = {
        "schema": FINDINGS_INPUT_SCHEMA,
        "reviewer": reviewer,
        "bundle_id": bundle_id,
        "bundle_sha256": bundle_sha256,
        "routing_sha256": routing_sha256,
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise ReviewBundleError(f"findings JSON {field} binding failed")
    return _validate_findings(value.get("findings"), reviewer)


def _parse_contract(data: bytes, label: str = "final-gate contract") -> dict[str, Any]:
    try:
        contract = json.loads(data.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReviewBundleError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    required_fields = {
        "schema",
        "verification_contract",
        "control_plane_files",
        "phase_plan",
    }
    if not isinstance(contract, dict) or frozenset(contract) != frozenset(required_fields):
        raise ReviewBundleError(f"{label} fields do not match the trusted schema")
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ReviewBundleError(f"unsupported {label} schema")
    verification_contract = contract.get("verification_contract")
    if not isinstance(verification_contract, str) or not verification_contract:
        raise ReviewBundleError("verification_contract must be a non-empty string")
    files = contract.get("control_plane_files")
    if not isinstance(files, list) or not files:
        raise ReviewBundleError("control_plane_files must be a non-empty list")
    normalized_files = [
        _safe_relative_path(path, "control_plane_files entry") for path in files
    ]
    if normalized_files != sorted(set(normalized_files)):
        raise ReviewBundleError("control_plane_files must be sorted and unique")
    phases = contract.get("phase_plan")
    if not isinstance(phases, list) or not phases:
        raise ReviewBundleError("phase_plan must be a non-empty list")
    seen: set[str] = set()
    allowed_when = {
        "always",
        "review_profile",
        "risk_cpp_i18n",
        "risk_cjk_runtime",
        "risk_message_overlay",
    }
    for phase in phases:
        allowed_fields = {"id", "required", "when", "allow_skip"}
        if not isinstance(phase, dict) or not set(phase).issubset(allowed_fields):
            raise ReviewBundleError("phase_plan contains an invalid phase object")
        if not {"id", "required", "when"}.issubset(phase):
            raise ReviewBundleError("phase_plan phase is missing required fields")
        phase_id = phase.get("id")
        if not isinstance(phase_id, str) or not ROLE_RE.fullmatch(phase_id):
            raise ReviewBundleError(f"invalid phase id: {phase_id!r}")
        if phase_id in seen:
            raise ReviewBundleError(f"duplicate phase id: {phase_id}")
        seen.add(phase_id)
        if not isinstance(phase.get("required"), bool):
            raise ReviewBundleError(f"phase required flag is invalid: {phase_id}")
        if phase.get("when") not in allowed_when:
            raise ReviewBundleError(f"phase condition is invalid: {phase_id}")
        if "allow_skip" in phase and not isinstance(phase["allow_skip"], bool):
            raise ReviewBundleError(f"phase allow_skip flag is invalid: {phase_id}")
        if phase.get("required") and phase.get("allow_skip"):
            raise ReviewBundleError(f"required phase may not allow skip: {phase_id}")
    return contract


def _control_plane_from_commit(
    repo: os.PathLike[str] | str,
    target_head: str,
    contract_path: str,
    verifier_path: str,
) -> dict[str, Any]:
    contract_mode, contract_bytes = _git_blob(repo, target_head, contract_path)
    contract = _parse_contract(contract_bytes)
    files = contract["control_plane_files"]
    if (
        contract_path not in files
        or verifier_path not in files
        or TRUSTED_CLASSIFIER_PATH not in files
    ):
        raise ReviewBundleError(
            "control_plane_files must include the trusted contract, verifier, and classifier"
        )
    records = []
    for relative_path in files:
        mode, data = _git_blob(repo, target_head, relative_path)
        records.append(
            {
                "mode": mode,
                "path": relative_path,
                "sha256": sha256_bytes(data),
                "size": len(data),
            }
        )
    manifest = {
        "schema": CONTROL_PLANE_SCHEMA,
        "target_head": target_head,
        "files": records,
    }
    return {
        "contract": contract,
        "contract_bytes": contract_bytes,
        "contract_mode": contract_mode,
        "contract_sha256": sha256_bytes(contract_bytes),
        "control_plane": manifest,
        "control_plane_sha256": sha256_bytes(canonical_json_bytes(manifest)),
    }


def _phase_plan_for_metadata(
    contract: dict[str, Any], metadata: dict[str, Any]
) -> list[dict[str, Any]]:
    risks: dict[str, bool] = {}
    for name in ("risk_cpp_i18n", "risk_cjk_runtime", "risk_message_overlay"):
        value = metadata.get(name)
        if not isinstance(value, bool):
            raise ReviewBundleError(f"verification metadata {name} must be boolean")
        risks[name] = value
    selected = []
    for phase in contract["phase_plan"]:
        condition = phase["when"]
        active = condition in ("always", "review_profile") or risks.get(
            condition, False
        )
        if active:
            selected.append(phase)
    return selected


def _artifact_paths(metadata: dict[str, Any], attempt_path: Path) -> list[str]:
    artifacts = metadata.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ReviewBundleError("verification metadata is missing artifacts")
    seen: set[str] = set()
    result: list[str] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict) or frozenset(artifact) != frozenset(
            ("path", "size", "sha256")
        ):
            raise ReviewBundleError("verification artifact fields are invalid")
        relative = _safe_relative_path(artifact.get("path"), "artifact path")
        if relative in ("metadata.json", COMPLETION_NAME) or relative in seen:
            raise ReviewBundleError(f"duplicate or reserved artifact path: {relative}")
        seen.add(relative)
        size = artifact.get("size")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ReviewBundleError(f"artifact size is invalid: {relative}")
        digest = _validate_sha256(artifact.get("sha256"), f"artifact {relative} sha256")
        path = attempt_path / relative
        info = _require_regular_file(path, f"artifact {relative}")
        data = _read_regular_bytes(path)
        if info.st_size != size or len(data) != size:
            raise ReviewBundleError(f"artifact size mismatch: {relative}")
        if sha256_bytes(data) != digest:
            raise ReviewBundleError(f"artifact SHA-256 mismatch: {relative}")
        result.append(relative)
    if "verify.log" not in seen:
        raise ReviewBundleError("verification metadata must bind verify.log")
    actual: set[str] = set()
    actual_directories: set[str] = set()
    for root, directories, files in os.walk(attempt_path, followlinks=False):
        root_path = Path(root)
        for name in directories:
            directory_path = root_path / name
            info = _lstat(directory_path)
            if info is None or stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise UnsafeObjectError(f"unsafe artifact directory: {directory_path}")
            actual_directories.add(directory_path.relative_to(attempt_path).as_posix())
        for name in files:
            path = root_path / name
            _require_regular_file(path, "attempt object")
            actual.add(path.relative_to(attempt_path).as_posix())
    expected = set(result) | {"metadata.json", COMPLETION_NAME}
    if actual != expected:
        raise UnsafeObjectError(
            f"attempt contains unknown or missing objects: {sorted(actual ^ expected)}"
        )
    expected_directories: set[str] = set()
    for relative in result:
        parent = Path(relative).parent
        while parent != Path("."):
            expected_directories.add(parent.as_posix())
            parent = parent.parent
    if actual_directories != expected_directories:
        raise UnsafeObjectError(
            "attempt contains unknown or missing artifact directories: "
            f"{sorted(actual_directories ^ expected_directories)}"
        )
    return result


def _validate_metadata(
    metadata: dict[str, Any],
    attempt_path: Path,
    completion: dict[str, Any],
    manifest: dict[str, Any],
    contract_info: dict[str, Any],
) -> None:
    if metadata.get("schema_version") != 3:
        raise ReviewBundleError("only schema-v3 final verification metadata is accepted")
    if metadata.get("verification_contract") != contract_info["contract"].get(
        "verification_contract"
    ):
        raise ReviewBundleError("verification contract binding failed")
    if metadata.get("run_id") != attempt_path.name:
        raise ReviewBundleError("verification run_id does not match attempt directory")
    if metadata.get("profile") != "review" or metadata.get("scope") != "full":
        raise ReviewBundleError("final verification must use profile=review and scope=full")
    expected = {
        "base": manifest["target_head"],
        "head": manifest["candidate_head"],
        "diff_sha256": manifest["diff_sha256"],
        "glossary_sha256": manifest["glossary_sha256"],
        "routing_sha256": manifest["routing_sha256"],
        "control_plane_sha256": contract_info["control_plane_sha256"],
    }
    for field, value in expected.items():
        if metadata.get(field) != value:
            raise ReviewBundleError(f"verification metadata {field} binding failed")
    if metadata.get("runtime_mode") != "catch2":
        raise ReviewBundleError(
            "bound review/full verification reported the wrong runtime mode"
        )
    status_value = metadata.get("status")
    if status_value not in ("pass", "fail", "interrupted"):
        raise ReviewBundleError("completed verification metadata has invalid status")
    if completion.get("outcome") != status_value:
        raise ReviewBundleError("attempt outcome does not match verification metadata")
    exit_code = completion.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int) or exit_code < 0:
        raise ReviewBundleError("attempt exit_code is invalid")
    if "exit_code" in metadata and metadata.get("exit_code") != exit_code:
        raise ReviewBundleError("metadata and completion exit codes differ")
    failures = metadata.get("failures")
    failures = _validate_count(failures, "verification failures")
    if status_value == "pass":
        if exit_code != 0 or failures != 0:
            raise ReviewBundleError("pass status is inconsistent with exit/failure count")
    elif exit_code == 0 or failures == 0:
        raise ReviewBundleError("non-pass status is inconsistent with exit/failure count")

    expected_plan = _phase_plan_for_metadata(contract_info["contract"], metadata)
    phases = metadata.get("phases")
    if not isinstance(phases, list) or len(phases) != len(expected_plan):
        raise ReviewBundleError("verification phase plan is incomplete")
    for actual, planned in zip(phases, expected_plan):
        if not isinstance(actual, dict) or frozenset(actual) != frozenset(
            ("id", "required", "status", "exit_code")
        ):
            raise ReviewBundleError("verification phase fields are invalid")
        if actual.get("id") != planned["id"] or actual.get("required") is not planned["required"]:
            raise ReviewBundleError("verification phase plan does not match trusted contract")
        phase_status = actual.get("status")
        phase_exit = actual.get("exit_code")
        if isinstance(phase_exit, bool) or not isinstance(phase_exit, int) or phase_exit < 0:
            raise ReviewBundleError(f"verification phase exit is invalid: {planned['id']}")
        if phase_status == "pass":
            if phase_exit != 0:
                raise ReviewBundleError(f"passing phase has nonzero exit: {planned['id']}")
        elif phase_status == "fail":
            if phase_exit == 0:
                raise ReviewBundleError(f"failed phase has zero exit: {planned['id']}")
        elif phase_status == "skip":
            if planned["required"] or not planned.get("allow_skip", False) or phase_exit != 0:
                raise ReviewBundleError(f"illegal verification phase skip: {planned['id']}")
        else:
            raise ReviewBundleError(f"invalid verification phase status: {planned['id']}")
        if planned["required"] and phase_status != "pass" and status_value == "pass":
            raise ReviewBundleError(f"required phase did not pass: {planned['id']}")
    if status_value == "pass" and any(
        phase["status"] == "fail" for phase in phases
    ):
        raise ReviewBundleError("pass metadata contains a failed phase")
    _artifact_paths(metadata, attempt_path)


def _attempt_digest(path: Path) -> str:
    records = []
    for root, directories, files in os.walk(path, followlinks=False):
        root_path = Path(root)
        directories.sort()
        files.sort()
        for name in files:
            file_path = root_path / name
            data = _read_regular_bytes(file_path)
            records.append(
                {
                    "path": file_path.relative_to(path).as_posix(),
                    "sha256": sha256_bytes(data),
                    "size": len(data),
                }
            )
    return sha256_bytes(canonical_json_bytes(records))


def _proc_start_token(pid: int) -> str | None:
    try:
        fields = Path(f"/proc/{pid}/stat").read_text(encoding="ascii").split()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None
    return fields[21] if len(fields) > 21 else None


def _boot_id() -> str | None:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(
            encoding="ascii"
        ).strip()
    except (FileNotFoundError, OSError, UnicodeDecodeError):
        return None


def _running_marker_live(marker: dict[str, Any]) -> bool:
    pid = marker.get("pid")
    token = marker.get("proc_start")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise ReviewBundleError("running marker pid is invalid")
    if not isinstance(token, str) or not token:
        raise ReviewBundleError("running marker process token is invalid")
    boot_id = marker.get("boot_id")
    if not isinstance(boot_id, str) or not boot_id:
        raise ReviewBundleError("running marker boot id is invalid")
    return _boot_id() == boot_id and _proc_start_token(pid) == token


def _load_running_marker(bundle_path: Path, bundle_id: str) -> dict[str, Any] | None:
    path = bundle_path / RUNNING_NAME
    if _lstat(path) is None:
        return None
    marker, _ = _load_canonical_object(path)
    fields = {
        "schema",
        "bundle_id",
        "operation_id",
        "pid",
        "proc_start",
        "boot_id",
        "staging_name",
        "target_head",
        "candidate_head",
        "routing_sha256",
        "started_ns",
    }
    if frozenset(marker) != frozenset(fields) or marker.get("schema") != RUNNING_SCHEMA:
        raise ReviewBundleError("running marker fields are invalid")
    if marker.get("bundle_id") != bundle_id:
        raise ReviewBundleError("running marker bundle binding failed")
    operation_id = marker.get("operation_id")
    if not isinstance(operation_id, str) or not RUN_ID_RE.fullmatch(operation_id):
        raise ReviewBundleError("running marker operation_id is invalid")
    expected_staging = f".staging-{operation_id}"
    if marker.get("staging_name") != expected_staging:
        raise ReviewBundleError("running marker staging binding failed")
    if not isinstance(marker.get("started_ns"), str) or not marker["started_ns"].isdigit():
        raise ReviewBundleError("running marker timestamp is invalid")
    return marker


def _validate_attempt_directory(
    repo: os.PathLike[str] | str,
    attempt_path: Path,
    manifest: dict[str, Any],
    bundle_id: str,
) -> dict[str, Any]:
    if not RUN_ID_RE.fullmatch(attempt_path.name):
        raise UnsafeObjectError(f"invalid attempt directory name: {attempt_path.name}")
    _require_directory(attempt_path, "attempt directory")
    completion, completion_bytes = _load_canonical_object(
        attempt_path / COMPLETION_NAME
    )
    fields = {
        "schema",
        "bundle_id",
        "attempt_id",
        "outcome",
        "exit_code",
        "metadata_sha256",
        "routing_sha256",
        "contract_path",
        "verifier_path",
        "contract_sha256",
        "control_plane_sha256",
        "completed",
    }
    if frozenset(completion) != frozenset(fields):
        raise ReviewBundleError(f"attempt completion fields are invalid: {attempt_path.name}")
    if completion.get("schema") != ATTEMPT_COMPLETION_SCHEMA or completion.get("completed") is not True:
        raise ReviewBundleError(f"attempt completion marker is invalid: {attempt_path.name}")
    if completion.get("bundle_id") != bundle_id or completion.get("attempt_id") != attempt_path.name:
        raise ReviewBundleError(f"attempt bundle/run binding failed: {attempt_path.name}")
    if completion.get("routing_sha256") != manifest["routing_sha256"]:
        raise ReviewBundleError(f"attempt routing binding failed: {attempt_path.name}")
    contract_path = _safe_relative_path(completion.get("contract_path"), "contract_path")
    verifier_path = _safe_relative_path(completion.get("verifier_path"), "verifier_path")
    contract_info = _control_plane_from_commit(
        repo, manifest["target_head"], contract_path, verifier_path
    )
    if completion.get("contract_sha256") != contract_info["contract_sha256"]:
        raise ReviewBundleError(f"attempt contract digest failed: {attempt_path.name}")
    if completion.get("control_plane_sha256") != contract_info["control_plane_sha256"]:
        raise ReviewBundleError(f"attempt control-plane digest failed: {attempt_path.name}")
    metadata, metadata_bytes = _load_canonical_object(attempt_path / "metadata.json")
    if completion.get("metadata_sha256") != sha256_bytes(metadata_bytes):
        raise ReviewBundleError(f"attempt metadata digest failed: {attempt_path.name}")
    _validate_metadata(metadata, attempt_path, completion, manifest, contract_info)
    outcome = completion["outcome"]
    if outcome not in ("pass", "fail", "interrupted"):
        raise ReviewBundleError(f"attempt outcome is invalid: {attempt_path.name}")
    return {
        "attempt_id": attempt_path.name,
        "attempt_sha256": _attempt_digest(attempt_path),
        "completion_sha256": sha256_bytes(completion_bytes),
        "metadata_sha256": sha256_bytes(metadata_bytes),
        "outcome": outcome,
        "exit_code": completion["exit_code"],
        "contract_sha256": contract_info["contract_sha256"],
        "control_plane_sha256": contract_info["control_plane_sha256"],
    }


def _validate_attempts(
    repo: os.PathLike[str] | str,
    bundle_path: Path,
    manifest: dict[str, Any],
    bundle_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any] | None, dict[str, Any] | None]:
    attempts_dir = bundle_path / "attempts"
    info = _lstat(attempts_dir)
    marker = _load_running_marker(bundle_path, bundle_id)
    if info is None:
        if marker is not None:
            raise StaleEvidenceError("running marker has no attempts directory")
        return [], None, None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise UnsafeObjectError("attempts evidence path is unsafe")
    attempts: list[dict[str, Any]] = []
    staging_names: list[str] = []
    with os.scandir(attempts_dir) as entries:
        for entry in entries:
            if entry.is_symlink():
                raise UnsafeObjectError(f"attempt symlink rejected: {entry.path}")
            if entry.name.startswith(".staging-"):
                if not entry.is_dir(follow_symlinks=False):
                    raise UnsafeObjectError(f"attempt staging object is unsafe: {entry.path}")
                staging_names.append(entry.name)
                continue
            if not entry.is_dir(follow_symlinks=False):
                raise UnsafeObjectError(f"unknown attempts object rejected: {entry.path}")
            attempts.append(
                _validate_attempt_directory(repo, Path(entry.path), manifest, bundle_id)
            )
    attempts.sort(key=lambda item: item["attempt_id"])
    passing = [attempt for attempt in attempts if attempt["outcome"] == "pass"]
    if len(passing) > 1:
        raise ReviewBundleError("conflicting successful final verification attempts")
    if marker is None:
        if staging_names:
            raise StaleEvidenceError("abandoned final verification staging exists")
        return attempts, passing[0] if passing else None, None
    if staging_names != [marker["staging_name"]]:
        raise StaleEvidenceError("running marker and staging directories conflict")
    if marker.get("target_head") != manifest["target_head"]:
        raise ReviewBundleError("running marker target binding failed")
    if marker.get("candidate_head") != manifest["candidate_head"]:
        raise ReviewBundleError("running marker candidate binding failed")
    if marker.get("routing_sha256") != manifest["routing_sha256"]:
        raise ReviewBundleError("running marker routing binding failed")
    if not _running_marker_live(marker):
        raise StaleEvidenceError("final verification running marker is stale")
    return attempts, passing[0] if passing else None, marker


def _validate_approval(
    bundle_path: Path,
    manifest: dict[str, Any],
    bundle_id: str,
    bundle_sha256: str,
    readiness_sha256: dict[str, str],
    passing_attempt: dict[str, Any] | None,
) -> dict[str, Any] | None:
    path = bundle_path / APPROVAL_NAME
    if _lstat(path) is None:
        return None
    approval, approval_bytes = _load_canonical_object(path)
    fields = {
        "schema",
        "verdict",
        "bundle_id",
        "bundle_sha256",
        "routing_sha256",
        "attempt_id",
        "attempt_sha256",
        "readiness",
        "contract_sha256",
        "control_plane_sha256",
    }
    if frozenset(approval) != frozenset(fields):
        raise ReviewBundleError("final approval fields are invalid")
    if approval.get("schema") != FINAL_APPROVAL_SCHEMA or approval.get("verdict") != "go":
        raise ReviewBundleError("final approval verdict/schema is invalid")
    expected = {
        "bundle_id": bundle_id,
        "bundle_sha256": bundle_sha256,
        "routing_sha256": manifest["routing_sha256"],
    }
    for field, value in expected.items():
        if approval.get(field) != value:
            raise ReviewBundleError(f"final approval {field} binding failed")
    if passing_attempt is None:
        raise ReviewBundleError("final approval has no valid passing attempt")
    attempt_expected = {
        "attempt_id": passing_attempt["attempt_id"],
        "attempt_sha256": passing_attempt["attempt_sha256"],
        "contract_sha256": passing_attempt["contract_sha256"],
        "control_plane_sha256": passing_attempt["control_plane_sha256"],
    }
    for field, value in attempt_expected.items():
        if approval.get(field) != value:
            raise ReviewBundleError(f"final approval {field} binding failed")
    readiness = approval.get("readiness")
    expected_readiness = [
        {"reviewer": reviewer, "sha256": readiness_sha256[reviewer]}
        for reviewer in sorted(readiness_sha256)
    ]
    if readiness != expected_readiness:
        raise ReviewBundleError("final approval readiness binding failed")
    result = dict(approval)
    result["approval_sha256"] = sha256_bytes(approval_bytes)
    return result


def _validate_bundle_locked(
    repo: os.PathLike[str] | str, bundle_path: Path, *, check_clean: bool
) -> dict[str, Any]:
    _reject_unknown_top_level(bundle_path)
    manifest, manifest_bytes = _load_canonical_object(bundle_path / "bundle.json")
    if frozenset(manifest) != MANIFEST_FIELDS:
        raise ReviewBundleError("bundle manifest fields do not match the supported schema")
    schema = manifest.get("schema")
    if schema not in (BUNDLE_SCHEMA, LEGACY_BUNDLE_SCHEMA):
        raise ReviewBundleError("unsupported review bundle schema")
    legacy = schema == LEGACY_BUNDLE_SCHEMA
    expected_root_parts = LEGACY_EVIDENCE_PARTS if legacy else EVIDENCE_PARTS
    expected_root = Path(
        os.path.abspath(os.fspath(git_common_dir(repo).joinpath(*expected_root_parts)))
    )
    actual_root = Path(os.path.abspath(os.fspath(bundle_path.parent)))
    if actual_root != expected_root:
        raise ReviewBundleError(
            f"{schema} bundle is stored outside its required evidence namespace"
        )
    target_head = manifest.get("target_head")
    candidate_head = manifest.get("candidate_head")
    if not isinstance(target_head, str) or resolve_commit(repo, target_head) != target_head:
        raise ReviewBundleError("bundle target_head is not an immutable commit id")
    if not isinstance(candidate_head, str) or resolve_commit(repo, candidate_head) != candidate_head:
        raise ReviewBundleError("bundle candidate_head is not an immutable commit id")
    _validate_sha256(manifest.get("diff_sha256"), "diff_sha256")
    _validate_sha256(manifest.get("glossary_sha256"), "glossary_sha256")
    _validate_sha256(manifest.get("routing_sha256"), "routing_sha256")
    if diff_sha256(repo, target_head, candidate_head) != manifest["diff_sha256"]:
        raise ReviewBundleError("bundle diff_sha256 does not match the raw binary diff")
    _assert_ancestor(repo, target_head, candidate_head)
    identity = _identity_from_manifest(manifest)
    expected_id = sha256_bytes(canonical_json_bytes(identity))
    if bundle_path.name != expected_id:
        raise ReviewBundleError("bundle directory id does not match its identity fields")
    routing, routing_bytes = _load_canonical_object(bundle_path / "routing.json")
    reviewers = _validate_routing(routing, target_head, candidate_head)
    if sha256_bytes(routing_bytes) != manifest["routing_sha256"]:
        raise ReviewBundleError("routing_sha256 does not match routing.json")
    trusted_routing = generate_routing_from_target(
        repo, target_head, candidate_head
    )
    if canonical_json_bytes(trusted_routing) != routing_bytes:
        raise ReviewBundleError(
            "routing.json does not match the target-head classifier"
        )
    if check_clean:
        candidate_top = _assert_checkout(repo, candidate_head, "candidate")
        if _candidate_glossary_sha256(candidate_top) != manifest["glossary_sha256"]:
            raise ReviewBundleError(
                "candidate glossary SHA-256 does not match the bundle manifest"
            )

    bundle_digest = sha256_bytes(manifest_bytes)
    records: dict[str, dict[str, Any]] = {}
    readiness_sha256: dict[str, str] = {}
    finding_counts: dict[str, dict[str, int]] = {}
    readiness_dir = bundle_path / "readiness"
    readiness_info = _lstat(readiness_dir)
    if readiness_info is not None:
        if stat.S_ISLNK(readiness_info.st_mode) or not stat.S_ISDIR(readiness_info.st_mode):
            raise UnsafeObjectError("readiness evidence path is unsafe")
        expected_names = {f"{reviewer}.json": reviewer for reviewer in reviewers}
        with os.scandir(readiness_dir) as entries:
            for entry in entries:
                reviewer = expected_names.get(entry.name)
                if reviewer is None:
                    raise UnsafeObjectError(f"unexpected readiness object: {entry.path}")
                record, record_bytes = _load_canonical_object(Path(entry.path))
                if frozenset(record) != READINESS_FIELDS:
                    raise ReviewBundleError(f"invalid readiness fields for {reviewer}")
                expected_readiness_schema = (
                    LEGACY_READINESS_SCHEMA if legacy else READINESS_SCHEMA
                )
                if record.get("schema") != expected_readiness_schema:
                    raise ReviewBundleError(f"invalid readiness schema for {reviewer}")
                if record.get("bundle_id") != expected_id:
                    raise ReviewBundleError(f"readiness bundle binding failed for {reviewer}")
                if record.get("bundle_sha256") != bundle_digest:
                    raise ReviewBundleError(f"readiness bundle hash failed for {reviewer}")
                if record.get("routing_sha256") != manifest["routing_sha256"]:
                    raise ReviewBundleError(f"readiness routing binding failed for {reviewer}")
                if record.get("reviewer") != reviewer:
                    raise ReviewBundleError(f"readiness reviewer binding failed for {reviewer}")
                findings = record.get("findings")
                if legacy:
                    if not isinstance(findings, dict) or frozenset(findings) != LEGACY_FINDING_FIELDS:
                        raise ReviewBundleError(f"invalid legacy readiness findings for {reviewer}")
                    blocker = _validate_count(findings.get("blocker"), "findings.blocker")
                    needs_fix = _validate_count(findings.get("needs_fix"), "findings.needs_fix")
                    suggestion = _validate_count(
                        findings.get("suggestion"), "findings.suggestion"
                    )
                else:
                    validated_findings = _validate_findings(findings, reviewer)
                    blocker = sum(
                        finding["severity"] == "blocker" for finding in validated_findings
                    )
                    needs_fix = sum(
                        finding["severity"] == "needs_fix" for finding in validated_findings
                    )
                    suggestion = sum(
                        finding["severity"] == "suggestion" for finding in validated_findings
                    )
                expected_ready = blocker == 0 and needs_fix == 0
                if record.get("ready") is not expected_ready:
                    raise ReviewBundleError(f"readiness verdict is inconsistent for {reviewer}")
                records[reviewer] = record
                readiness_sha256[reviewer] = sha256_bytes(record_bytes)
                finding_counts[reviewer] = {
                    "blocker": blocker,
                    "needs_fix": needs_fix,
                    "suggestion": suggestion,
                }

    ready_reviewers = [role for role in reviewers if records.get(role, {}).get("ready") is True]
    missing_reviewers = [role for role in reviewers if role not in records]
    not_ready_reviewers = [
        role for role in reviewers if role in records and not records[role]["ready"]
    ]
    ready = not missing_reviewers and not not_ready_reviewers
    attempts, passing_attempt, running_marker = _validate_attempts(
        repo, bundle_path, manifest, expected_id
    )
    approval = _validate_approval(
        bundle_path,
        manifest,
        expected_id,
        bundle_digest,
        readiness_sha256,
        passing_attempt,
    )
    if legacy:
        exit_code = LEGACY_READ_ONLY
    elif running_marker is not None:
        exit_code = FINAL_GATE_RUNNING
    elif not ready:
        exit_code = READINESS_REQUIRED
    elif approval is not None:
        exit_code = MERGEABLE
    elif passing_attempt is not None:
        exit_code = FINAL_APPROVAL_REQUIRED
    elif attempts:
        exit_code = EVIDENCE_FAILED
    else:
        exit_code = FINAL_GATE_REQUIRED
    return {
        "bundle_id": expected_id,
        "bundle_path": os.fspath(bundle_path),
        "bundle_sha256": bundle_digest,
        "target_head": target_head,
        "candidate_head": candidate_head,
        "diff_sha256": manifest["diff_sha256"],
        "glossary_sha256": manifest["glossary_sha256"],
        "routing_sha256": manifest["routing_sha256"],
        "required_reviewers": reviewers,
        "ready_reviewers": ready_reviewers,
        "missing_reviewers": missing_reviewers,
        "not_ready_reviewers": not_ready_reviewers,
        "readiness_sha256": readiness_sha256,
        "finding_counts": finding_counts,
        "attempts": attempts,
        "passing_attempt": passing_attempt,
        "approved": approval is not None,
        "sealed": approval is not None,
        "approval": approval,
        "state": STATE_NAMES[exit_code],
        "exit_code": exit_code,
        "ready": ready,
        "valid": True,
        "legacy_read_only": legacy,
    }


def validate_bundle(
    repo: os.PathLike[str] | str,
    bundle: os.PathLike[str] | str,
    *,
    check_clean: bool = True,
) -> dict[str, Any]:
    path = _resolve_bundle_path(repo, bundle)
    with bundle_lock(path, exclusive=False):
        return _validate_bundle_locked(repo, path, check_clean=check_clean)


def status_bundle(
    repo: os.PathLike[str] | str,
    bundle: os.PathLike[str] | str,
) -> dict[str, Any]:
    try:
        path = _resolve_bundle_path(repo, bundle)
        try:
            with bundle_lock(path, exclusive=False, blocking=False):
                return _validate_bundle_locked(repo, path, check_clean=True)
        except BlockingIOError:
            marker = _load_running_marker(path, path.name)
            if marker is not None:
                if not _running_marker_live(marker):
                    raise StaleEvidenceError("final verification running marker is stale")
                attempts = path / "attempts"
                staging = attempts / marker["staging_name"]
                _require_directory(staging, "active final verification staging")
            return {
                "bundle_id": path.name,
                "bundle_path": os.fspath(path),
                "state": STATE_NAMES[FINAL_GATE_RUNNING],
                "exit_code": FINAL_GATE_RUNNING,
                "ready": True,
                "valid": True,
                "approved": False,
                "sealed": False,
                "operation_id": marker.get("operation_id") if marker else None,
            }
    except StaleEvidenceError as exc:
        return {
            "bundle_id": Path(bundle).name,
            "state": STATE_NAMES[STALE_EVIDENCE],
            "exit_code": STALE_EVIDENCE,
            "ready": False,
            "valid": False,
            "approved": False,
            "sealed": False,
            "error": str(exc),
        }
    except ReviewBundleError as exc:
        return {
            "bundle_id": Path(bundle).name,
            "state": STATE_NAMES[INVALID_EVIDENCE],
            "exit_code": INVALID_EVIDENCE,
            "ready": False,
            "valid": False,
            "approved": False,
            "sealed": False,
            "error": str(exc),
        }
    except OSError as exc:
        return {
            "bundle_id": Path(bundle).name,
            "state": STATE_NAMES[INTERNAL_ERROR],
            "exit_code": INTERNAL_ERROR,
            "ready": False,
            "valid": False,
            "approved": False,
            "sealed": False,
            "error": str(exc),
        }


def record_readiness(
    repo: os.PathLike[str] | str,
    bundle: os.PathLike[str] | str,
    reviewer: str,
    findings_json: os.PathLike[str] | str,
) -> dict[str, Any]:
    path = _resolve_bundle_path(repo, bundle)
    with bundle_lock(path):
        status = _validate_bundle_locked(repo, path, check_clean=True)
        if status.get("legacy_read_only"):
            raise ReviewBundleError("schema-v3 bundles are historical read-only evidence")
        if reviewer not in status["required_reviewers"]:
            raise ReviewBundleError(f"reviewer role is not required by routing: {reviewer}")
        findings = _load_findings_input(
            findings_json,
            reviewer=reviewer,
            bundle_id=status["bundle_id"],
            bundle_sha256=status["bundle_sha256"],
            routing_sha256=status["routing_sha256"],
        )
        readiness_dir = _ensure_child_directory(path, "readiness")
        record = {
            "schema": READINESS_SCHEMA,
            "bundle_id": status["bundle_id"],
            "bundle_sha256": status["bundle_sha256"],
            "routing_sha256": status["routing_sha256"],
            "reviewer": reviewer,
            "findings": findings,
            "ready": not any(
                finding["severity"] in ("blocker", "needs_fix")
                for finding in findings
            ),
        }
        created = atomic_write_once(
            readiness_dir / f"{reviewer}.json", canonical_json_bytes(record)
        )
        result = _validate_bundle_locked(repo, path, check_clean=True)
    result["recorded_reviewer"] = reviewer
    result["readiness_created"] = created
    return result


def _candidate_glossary_sha256(candidate_top: Path) -> str:
    path = candidate_top / "docs/glossary.md"
    _require_regular_file(path, "candidate glossary")
    return sha256_bytes(_read_regular_bytes(path))


def _check_final_inputs(
    candidate_repo: os.PathLike[str] | str,
    target_repo: os.PathLike[str] | str,
    status: dict[str, Any],
    verifier: os.PathLike[str] | str,
    contract: os.PathLike[str] | str,
) -> dict[str, Any]:
    candidate_top = _assert_checkout(
        candidate_repo, status["candidate_head"], "candidate"
    )
    target_top = _assert_checkout(target_repo, status["target_head"], "target")
    _assert_ancestor(candidate_top, status["target_head"], status["candidate_head"])
    if diff_sha256(candidate_top, status["target_head"], status["candidate_head"]) != status[
        "diff_sha256"
    ]:
        raise ReviewBundleError("candidate binary diff changed from bundle manifest")
    if _candidate_glossary_sha256(candidate_top) != status["glossary_sha256"]:
        raise ReviewBundleError("candidate glossary SHA-256 changed from bundle manifest")
    verifier_path, verifier_relative = _path_under_checkout(
        target_top, verifier, "trusted verifier"
    )
    contract_path, contract_relative = _path_under_checkout(
        target_top, contract, "trusted contract"
    )
    control = _control_plane_from_commit(
        candidate_top,
        status["target_head"],
        contract_relative,
        verifier_relative,
    )
    if control["contract"].get("verification_contract") != VERIFICATION_CONTRACT:
        raise ReviewBundleError(
            f"schema-v4 final verification requires {VERIFICATION_CONTRACT}"
        )
    for record in control["control_plane"]["files"]:
        working_path, relative = _path_under_checkout(
            target_top, target_top / record["path"], "control-plane file"
        )
        if relative != record["path"]:
            raise ReviewBundleError("control-plane working path normalization failed")
        data = _read_regular_bytes(working_path)
        if len(data) != record["size"] or sha256_bytes(data) != record["sha256"]:
            raise ReviewBundleError(
                f"target control-plane file differs from target HEAD: {relative}"
            )
    return {
        "candidate_top": candidate_top,
        "target_top": target_top,
        "verifier_path": verifier_path,
        "verifier_relative": verifier_relative,
        "contract_path": contract_path,
        "contract_relative": contract_relative,
        **control,
    }


def _verifier_command(path: Path) -> list[str]:
    if os.access(path, os.X_OK):
        return [os.fspath(path)]
    if path.suffix == ".py":
        return [sys.executable, os.fspath(path)]
    if path.suffix == ".sh":
        return ["bash", os.fspath(path)]
    raise ReviewBundleError("trusted verifier is not executable")


def _operation_id() -> str:
    return f"attempt-{_utc_timestamp_ns()}-{os.getpid()}-{secrets.token_hex(6)}"


def _unlink_running_marker(bundle_path: Path) -> None:
    path = bundle_path / RUNNING_NAME
    info = _lstat(path)
    if info is None:
        return
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise UnsafeObjectError("running marker became unsafe")
    os.unlink(path)
    _fsync_directory(bundle_path)


def _recover_stale_locked(bundle_path: Path, bundle_id: str) -> None:
    attempts_dir = _ensure_child_directory(bundle_path, "attempts")
    marker = _load_running_marker(bundle_path, bundle_id)
    if marker is not None and _running_marker_live(marker):
        raise ReviewBundleError("live final verification may not be recovered")
    staging: list[Path] = []
    with os.scandir(attempts_dir) as entries:
        for entry in entries:
            if entry.name.startswith(".staging-"):
                staging.append(Path(entry.path))
    if marker is not None:
        expected = attempts_dir / marker["staging_name"]
        if staging and expected not in staging:
            raise StaleEvidenceError("stale marker conflicts with staging residue")
    if marker is None and not staging:
        return
    for path in staging:
        _remove_staging_directory(path)
    _unlink_running_marker(bundle_path)


def _run_verifier_process(
    command: list[str], candidate_top: Path, process_log: Path
) -> tuple[int, int | None]:
    interrupted: list[int] = []
    interrupted_at: list[float] = []
    parent_pid = os.getpid()

    def child_setup() -> None:
        # A SIGKILLed gate must not leave an untracked verifier writing into a
        # staging directory that a later explicit recovery may remove.
        libc = ctypes.CDLL(None, use_errno=True)
        prctl = getattr(libc, "prctl", None)
        if prctl is not None:
            prctl(1, signal.SIGKILL, 0, 0, 0)  # PR_SET_PDEATHSIG
        if os.getppid() != parent_pid:
            os.kill(os.getpid(), signal.SIGKILL)
        os.setsid()

    with process_log.open("wb") as output:
        process = subprocess.Popen(
            command,
            cwd=candidate_top,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            preexec_fn=child_setup,
            env=_trusted_child_environment(),
        )
        previous: dict[int, Any] = {}

        def handle(signum: int, _frame: Any) -> None:
            if not interrupted:
                interrupted.append(signum)
                interrupted_at.append(time.monotonic())
                try:
                    os.killpg(process.pid, signum)
                except ProcessLookupError:
                    pass

        try:
            for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
                try:
                    previous[signum] = signal.signal(signum, handle)
                except ValueError:
                    previous.clear()
                    break
            while True:
                try:
                    return_code = process.wait(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    if interrupted_at and time.monotonic() - interrupted_at[0] > 5:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
        finally:
            for signum, handler in previous.items():
                signal.signal(signum, handler)
            output.flush()
            os.fsync(output.fileno())
    if return_code < 0:
        return_code = 128 + abs(return_code)
    return return_code, interrupted[0] if interrupted else None


def _find_verifier_run(output_root: Path) -> Path | None:
    runs: list[Path] = []
    if _lstat(output_root) is None:
        return None
    _require_directory(output_root, "verifier output directory")
    with os.scandir(output_root) as entries:
        for entry in entries:
            path = Path(entry.path)
            if entry.is_symlink():
                raise UnsafeObjectError(f"verifier output symlink rejected: {path}")
            if entry.is_dir(follow_symlinks=False):
                if _lstat(path / "metadata.json") is not None:
                    runs.append(path)
            elif not entry.is_file(follow_symlinks=False):
                raise UnsafeObjectError(f"verifier output special object rejected: {path}")
    if len(runs) > 1:
        raise ReviewBundleError("verifier produced multiple run directories")
    return runs[0] if runs else None


def _synthetic_failure_metadata(
    operation_id: str,
    status: dict[str, Any],
    contract_info: dict[str, Any],
    exit_code: int,
    interrupted: bool,
) -> dict[str, Any]:
    outcome = "interrupted" if interrupted else "fail"
    seed = {
        "risk_cpp_i18n": False,
        "risk_cjk_runtime": False,
        "risk_message_overlay": False,
    }
    phases = []
    for planned in _phase_plan_for_metadata(contract_info["contract"], seed):
        if planned["required"]:
            phase_status = "fail"
            phase_exit = exit_code or 1
        elif planned.get("allow_skip", False):
            phase_status = "skip"
            phase_exit = 0
        else:
            phase_status = "fail"
            phase_exit = exit_code or 1
        phases.append(
            {
                "id": planned["id"],
                "required": planned["required"],
                "status": phase_status,
                "exit_code": phase_exit,
            }
        )
    return {
        "schema_version": 3,
        "verification_contract": contract_info["contract"]["verification_contract"],
        "run_id": operation_id,
        "status": outcome,
        "profile": "review",
        "scope": "full",
        "base": status["target_head"],
        "head": status["candidate_head"],
        "diff_sha256": status["diff_sha256"],
        "glossary_sha256": status["glossary_sha256"],
        "routing_sha256": status["routing_sha256"],
        "control_plane_sha256": contract_info["control_plane_sha256"],
        "risk_cpp_i18n": False,
        "risk_cjk_runtime": False,
        "risk_message_overlay": False,
        "runtime_mode": "catch2",
        "phases": phases,
        "artifacts": [],
        "failures": max(1, sum(phase["status"] == "fail" for phase in phases)),
    }


def _copy_attempt_snapshot(
    stage: Path,
    operation_id: str,
    process_log: Path,
    status: dict[str, Any],
    contract_info: dict[str, Any],
    exit_code: int,
    interrupted_signal: int | None,
) -> tuple[Path, str]:
    output_root = stage / "verifier-output"
    source_run = _find_verifier_run(output_root)
    metadata: dict[str, Any]
    if source_run is None or interrupted_signal is not None:
        metadata = _synthetic_failure_metadata(
            operation_id,
            status,
            contract_info,
            exit_code or 1,
            interrupted_signal is not None,
        )
        run_id = operation_id
        source_verify = b"" if source_run is None else _read_regular_bytes(
            source_run / "verify.log"
        )
    else:
        raw_metadata = _read_regular_bytes(source_run / "metadata.json")
        try:
            metadata = json.loads(raw_metadata.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReviewBundleError(f"verifier metadata is invalid: {exc}") from exc
        if not isinstance(metadata, dict):
            raise ReviewBundleError("verifier metadata must be a JSON object")
        run_id = metadata.get("run_id")
        if not isinstance(run_id, str) or not RUN_ID_RE.fullmatch(run_id):
            raise ReviewBundleError("verifier run_id is invalid")
        source_verify = _read_regular_bytes(source_run / "verify.log")

    publish = stage / run_id
    os.mkdir(publish, 0o700)
    process_bytes = _read_regular_bytes(process_log)
    verify_bytes = source_verify
    if process_bytes:
        if verify_bytes and not verify_bytes.endswith(b"\n"):
            verify_bytes += b"\n"
        verify_bytes += b"=== verifier stdout/stderr ===\n" + process_bytes
    if not verify_bytes:
        verify_bytes = b"(verifier produced no output)\n"

    copied_artifacts: list[dict[str, Any]] = []
    if source_run is not None:
        artifacts = metadata.get("artifacts")
        if not isinstance(artifacts, list):
            raise ReviewBundleError("verifier metadata artifacts are invalid")
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                raise ReviewBundleError("verifier artifact entry is invalid")
            relative = _safe_relative_path(artifact.get("path"), "verifier artifact path")
            if relative == "verify.log":
                continue
            source = source_run / relative
            data = _read_regular_bytes(source)
            destination = publish / relative
            destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            atomic_write_once(destination, data)
            copied_artifacts.append(
                {"path": relative, "size": len(data), "sha256": sha256_bytes(data)}
            )
    atomic_write_once(publish / "verify.log", verify_bytes)
    metadata["artifacts"] = sorted(
        copied_artifacts
        + [{"path": "verify.log", "size": len(verify_bytes), "sha256": sha256_bytes(verify_bytes)}],
        key=lambda item: item["path"],
    )
    metadata_bytes = canonical_json_bytes(metadata)
    atomic_write_once(publish / "metadata.json", metadata_bytes)
    completion_exit = exit_code
    if metadata.get("status") != "pass" and completion_exit == 0:
        completion_exit = 1
    completion = {
        "schema": ATTEMPT_COMPLETION_SCHEMA,
        "bundle_id": status["bundle_id"],
        "attempt_id": run_id,
        "outcome": metadata.get("status"),
        "exit_code": completion_exit,
        "metadata_sha256": sha256_bytes(metadata_bytes),
        "routing_sha256": status["routing_sha256"],
        "contract_path": contract_info["contract_relative"],
        "verifier_path": contract_info["verifier_relative"],
        "contract_sha256": contract_info["contract_sha256"],
        "control_plane_sha256": contract_info["control_plane_sha256"],
        "completed": True,
    }
    atomic_write_once(publish / COMPLETION_NAME, canonical_json_bytes(completion))
    _fsync_tree(publish)
    return publish, run_id


def _publish_approval(
    bundle_path: Path, status: dict[str, Any], attempt: dict[str, Any]
) -> bool:
    approval = {
        "schema": FINAL_APPROVAL_SCHEMA,
        "verdict": "go",
        "bundle_id": status["bundle_id"],
        "bundle_sha256": status["bundle_sha256"],
        "routing_sha256": status["routing_sha256"],
        "attempt_id": attempt["attempt_id"],
        "attempt_sha256": attempt["attempt_sha256"],
        "readiness": [
            {"reviewer": reviewer, "sha256": status["readiness_sha256"][reviewer]}
            for reviewer in sorted(status["readiness_sha256"])
        ],
        "contract_sha256": attempt["contract_sha256"],
        "control_plane_sha256": attempt["control_plane_sha256"],
    }
    return atomic_write_once(
        bundle_path / APPROVAL_NAME, canonical_json_bytes(approval)
    )


def run_final(
    repo: os.PathLike[str] | str,
    bundle: os.PathLike[str] | str,
    target_repo: os.PathLike[str] | str,
    verifier: os.PathLike[str] | str,
    contract: os.PathLike[str] | str,
    *,
    retry_failed: bool = False,
    recover_stale: bool = False,
) -> dict[str, Any]:
    """Run or reuse the one trusted final verification and seal its approval."""
    bundle_path = _resolve_bundle_path(repo, bundle)
    with bundle_lock(bundle_path, exclusive=True):
        try:
            status = _validate_bundle_locked(repo, bundle_path, check_clean=True)
        except StaleEvidenceError:
            if not recover_stale:
                raise
            _recover_stale_locked(bundle_path, bundle_path.name)
            status = _validate_bundle_locked(repo, bundle_path, check_clean=True)
        if status.get("legacy_read_only"):
            raise ReviewBundleError("schema-v3 bundles cannot create new merge authorization")
        if not status["ready"]:
            return status
        if status["exit_code"] == FINAL_GATE_RUNNING:
            raise ReviewBundleError("live final verification is already running")
        if status["approved"]:
            return status
        trusted = _check_final_inputs(
            repo, target_repo, status, verifier, contract
        )
        if status["passing_attempt"] is not None:
            _publish_approval(bundle_path, status, status["passing_attempt"])
            return _validate_bundle_locked(repo, bundle_path, check_clean=True)
        if status["attempts"] and not retry_failed:
            return status

        operation_id = _operation_id()
        attempts_dir = _ensure_child_directory(bundle_path, "attempts")
        staging_name = f".staging-{operation_id}"
        stage = attempts_dir / staging_name
        os.mkdir(stage, 0o700)
        _fsync_directory(attempts_dir)
        output_root = stage / "verifier-output"
        os.mkdir(output_root, 0o700)
        process_log = stage / "process.log"
        marker = {
            "schema": RUNNING_SCHEMA,
            "bundle_id": status["bundle_id"],
            "operation_id": operation_id,
            "pid": os.getpid(),
            "proc_start": _proc_start_token(os.getpid()) or "unavailable",
            "boot_id": _boot_id() or "unavailable",
            "staging_name": staging_name,
            "target_head": status["target_head"],
            "candidate_head": status["candidate_head"],
            "routing_sha256": status["routing_sha256"],
            "started_ns": _utc_timestamp_ns(),
        }
        atomic_write_once(
            bundle_path / RUNNING_NAME, canonical_json_bytes(marker)
        )
        command = _verifier_command(trusted["verifier_path"])
        command.extend(
            (
                "--profile",
                "review",
                "--base",
                status["target_head"],
                "--head",
                status["candidate_head"],
                "--scope",
                "full",
                "--output-dir",
                os.fspath(output_root),
                "--routing-sha256",
                status["routing_sha256"],
                "--control-plane-sha256",
                trusted["control_plane_sha256"],
            )
        )
        try:
            exit_code, interrupted_signal = _run_verifier_process(
                command, trusted["candidate_top"], process_log
            )
            post_status = _validate_bundle_locked(
                repo, bundle_path, check_clean=False
            )
            _check_final_inputs(repo, target_repo, post_status, verifier, contract)
            publish, run_id = _copy_attempt_snapshot(
                stage,
                operation_id,
                process_log,
                status,
                trusted,
                exit_code,
                interrupted_signal,
            )
            # Validate the complete staging snapshot before its no-replace rename.
            _validate_attempt_directory(
                repo, publish, {
                    "target_head": status["target_head"],
                    "candidate_head": status["candidate_head"],
                    "diff_sha256": status["diff_sha256"],
                    "glossary_sha256": status["glossary_sha256"],
                    "routing_sha256": status["routing_sha256"],
                }, status["bundle_id"]
            )
            _atomic_publish_directory(publish, attempts_dir / run_id)
        finally:
            _remove_staging_directory(stage)
            _unlink_running_marker(bundle_path)

        result = _validate_bundle_locked(repo, bundle_path, check_clean=True)
        if result["passing_attempt"] is not None:
            _check_final_inputs(repo, target_repo, result, verifier, contract)
            _publish_approval(bundle_path, result, result["passing_attempt"])
            result = _validate_bundle_locked(repo, bundle_path, check_clean=True)
        return result


@contextlib.contextmanager
def final_gate(
    repo: os.PathLike[str] | str,
    bundle: os.PathLike[str] | str,
    *,
    require_ready: bool = True,
) -> Iterator[dict[str, Any]]:
    """Hold an exclusive bundle lock across final validation and caller action."""
    path = _resolve_bundle_path(repo, bundle)
    with bundle_lock(path, exclusive=True):
        status = _validate_bundle_locked(repo, path, check_clean=True)
        if status.get("legacy_read_only"):
            raise ReviewBundleError("schema-v3 bundles cannot authorize final actions")
        if require_ready and not status["ready"]:
            raise ReviewBundleError("bundle is valid but not ready for final approval")
        yield status


def _add_repo_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=".", help="Git worktree (default: current directory)")


def _add_create_arguments(parser: argparse.ArgumentParser) -> None:
    _add_repo_argument(parser)
    parser.add_argument("--target", "--base", dest="target", required=True)
    parser.add_argument("--candidate", "--head", dest="candidate", required=True)
    parser.add_argument("--glossary-sha256", required=True)
    parser.add_argument("--classifier", "--classifier-path", dest="classifier", required=True)


def _add_bundle_selector(parser: argparse.ArgumentParser) -> None:
    _add_repo_argument(parser)
    parser.add_argument("--bundle", "--bundle-id", dest="bundle", required=True)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    describe = subparsers.add_parser("describe", help="describe a deterministic bundle")
    _add_create_arguments(describe)
    create = subparsers.add_parser("create", help="create immutable bundle evidence")
    _add_create_arguments(create)
    readiness = subparsers.add_parser(
        "record-readiness", help="record immutable readiness for one routed reviewer"
    )
    _add_bundle_selector(readiness)
    readiness.add_argument("--reviewer", "--reviewer-role", dest="reviewer", required=True)
    readiness.add_argument("--findings-json", required=True)
    status = subparsers.add_parser("status", help="show validated aggregate readiness")
    _add_bundle_selector(status)
    validate = subparsers.add_parser("validate", help="validate all immutable evidence")
    _add_bundle_selector(validate)
    run_final_parser = subparsers.add_parser(
        "run-final", help="run/reuse final verification and seal merge approval"
    )
    _add_bundle_selector(run_final_parser)
    run_final_parser.add_argument("--target-repo", required=True)
    run_final_parser.add_argument("--verifier", required=True)
    run_final_parser.add_argument("--contract", required=True)
    run_final_parser.add_argument("--retry-failed", action="store_true")
    run_final_parser.add_argument("--recover-stale", action="store_true")
    return parser.parse_args(argv)


def _emit_json(value: Any) -> None:
    sys.stdout.buffer.write(canonical_json_bytes(value))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "describe":
            result = describe_bundle(
                args.repo,
                args.target,
                args.candidate,
                args.glossary_sha256,
                args.classifier,
            )
        elif args.command == "create":
            result = create_bundle(
                args.repo,
                args.target,
                args.candidate,
                args.glossary_sha256,
                args.classifier,
            )
        elif args.command == "record-readiness":
            result = record_readiness(
                args.repo,
                args.bundle,
                args.reviewer,
                args.findings_json,
            )
        elif args.command == "status":
            result = status_bundle(args.repo, args.bundle)
        elif args.command == "validate":
            result = validate_bundle(args.repo, args.bundle)
        elif args.command == "run-final":
            result = run_final(
                args.repo,
                args.bundle,
                args.target_repo,
                args.verifier,
                args.contract,
                retry_failed=args.retry_failed,
                recover_stale=args.recover_stale,
            )
        else:  # pragma: no cover - argparse enforces the command set.
            raise ReviewBundleError(f"unsupported command: {args.command}")
    except StaleEvidenceError as exc:
        if args.command == "run-final":
            result = {
                "bundle_id": Path(args.bundle).name,
                "state": STATE_NAMES[STALE_EVIDENCE],
                "exit_code": STALE_EVIDENCE,
                "ready": False,
                "valid": False,
                "approved": False,
                "sealed": False,
                "error": str(exc),
            }
            _emit_json(result)
            return STALE_EVIDENCE
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except (OSError, ReviewBundleError) as exc:
        if args.command == "run-final":
            code = INTERNAL_ERROR if isinstance(exc, OSError) else INVALID_EVIDENCE
            result = {
                "bundle_id": Path(args.bundle).name,
                "state": STATE_NAMES[code],
                "exit_code": code,
                "ready": False,
                "valid": False,
                "approved": False,
                "sealed": False,
                "error": str(exc),
            }
            _emit_json(result)
            return code
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    _emit_json(result)
    if args.command in ("status", "run-final"):
        return result["exit_code"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
