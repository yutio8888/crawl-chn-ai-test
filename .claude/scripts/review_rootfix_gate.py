#!/usr/bin/env python3
"""Run the one-edge candidate-root regression-test bootstrap gate.

This gate is deliberately narrower than the normal final gate.  It is valid
only for DCSS-ZH-ROOTFIX-2026-07-29 and only after the corrected policy commit
P2 has been installed by the repository owner.  Normal schema-v4 routing and
readiness are reused.  The sole candidate-sourced control blob is
tests/test_monster_name_ssot.py; every other F2 tree object must equal P2.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
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
import tempfile
import time
import types
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple


# The main script is always compiled from its explicit source path.  Redirect
# every subsequent repository-local import away from ignored checkout
# __pycache__ objects before review_bundle (and its i18n_shared dependency) is
# imported.  Bytecode writing is disabled, so this unpredictable path remains
# absent and acts only as an isolated cache lookup namespace.
_PYCACHE_PARENT = Path("/private/tmp" if sys.platform == "darwin" else "/tmp")
PRIVATE_PYCACHE_PREFIX = _PYCACHE_PARENT / (
    f"dcss-rootfix-pycache-{os.getpid()}-{secrets.token_hex(16)}"
)
_UNSET_MARKER_SNAPSHOT = object()
_UNSET_FILE_SNAPSHOT = object()
sys.pycache_prefix = os.fspath(PRIVATE_PYCACHE_PREFIX)
sys.dont_write_bytecode = True

SCRIPT_DIR = Path(__file__).resolve().parent
rb: Any = None
_TEST_MODE = __name__ != "__main__"
_TRUSTED_POLICY_HEAD: str | None = None
_TRUSTED_SOURCE_BLOBS: dict[str, bytes] = {}


EXCEPTION_ID = "DCSS-ZH-ROOTFIX-2026-07-29"
BASE_C = "8aae77c60a5e537e76c7b252c6a311fade4264c2"
POLICY_P = "0abfe2b3d60d18d6dc3bca7f8079a44bb4a002e0"
APPROVAL_SCHEMA = "dcss-zh-rootfix-approval-v1"
COMPLETION_SCHEMA = "dcss-zh-rootfix-attempt-v2"
ARTIFACT_SCHEMA = "dcss-zh-rootfix-artifacts-v2"
RUNNING_SCHEMA = "dcss-zh-rootfix-running-v1"
PROCESS_SCHEMA = "dcss-zh-rootfix-process-v1"
PROCESS_RECORD_NAMES = {
    "candidate_test": "candidate-process.json",
    "code_profile": "profile-process.json",
}
PROFILE_CONTRACT_PATH = ".claude/scripts/data/review_verification_contract_v5.json"
PROFILE_PHASE_LABELS = (
    ("policy-sync", "Agent/Skill policy synchronization"),
    ("source-db-static", "Source/DB static integrity"),
    ("code-static", "Code verification (post-coder.sh)"),
    ("message-overlay-static", "TextDB message overlay static audit"),
)
ROOT_ATOMIC_TEMP_RE = re.compile(
    r"^\.tmp-(?P<kind>running|approval)\.json-"
    r"(?P<writer_pid>[1-9][0-9]*)-(?P<writer_token>[0-9a-f]{16})$"
)
ROOT_ATOMIC_QUARANTINE_RE = re.compile(
    r"^\.recover-(?P<kind>running|approval)\.json-"
    r"(?P<writer_pid>[1-9][0-9]*)-(?P<writer_token>[0-9a-f]{16})-"
    r"(?P<recovery_pid>[1-9][0-9]*)-"
    r"(?P<recovery_token>[0-9a-f]{16})$"
)
ROOT_ATOMIC_ARCHIVE_RE = re.compile(
    r"^recovered-(?P<source>tmp|recover)-"
    r"(?P<kind>running|approval)\.json-"
    r"(?P<writer_pid>[1-9][0-9]*)-"
    r"(?P<writer_token>[0-9a-f]{16})-"
    r"(?P<content_sha256>[0-9a-f]{64})-"
    r"(?P<recovery_pid>[1-9][0-9]*)-"
    r"(?P<recovery_token>[0-9a-f]{16})$"
)
RUNNING_MARKER_ARCHIVE_RE = re.compile(
    r"^retired-running-"
    r"(?P<operation_id>attempt-[1-9][0-9]*-[1-9][0-9]*-"
    r"[0-9a-f]{12})-"
    r"(?P<attempt_sha256>[0-9a-f]{64}|none)-"
    r"(?P<content_sha256>[0-9a-f]{64})-"
    r"(?P<recovery_pid>[1-9][0-9]*)-"
    r"(?P<recovery_token>[0-9a-f]{16})\.json$"
)
STAGING_ARCHIVE_RE = re.compile(
    r"^retired-staging-"
    r"(?P<operation_id>attempt-[1-9][0-9]*-[1-9][0-9]*-"
    r"[0-9a-f]{12})-"
    r"(?P<tree_sha256>[0-9a-f]{64})-"
    r"(?P<recovery_pid>[1-9][0-9]*)-"
    r"(?P<recovery_token>[0-9a-f]{16})$"
)
MAX_ROOT_ATOMIC_BYTES = 1024 * 1024
ROOTFIX_ATTEMPT_ID_RE = re.compile(
    r"^attempt-[1-9][0-9]*-[1-9][0-9]*-[0-9a-f]{12}$"
)
EVIDENCE_PARTS = ("zh-review-evidence", "rootfix-v1")
RECOVERY_ARCHIVE_PART = "rootfix-recovered-v1"
APPROVAL_NAME = "approval.json"
RUNNING_NAME = "running.json"
GATE_PATH = ".claude/scripts/review_rootfix_gate.py"
BUNDLE_PATH = ".claude/scripts/review_bundle.py"
I18N_SHARED_PATH = ".claude/scripts/i18n_shared.py"
TEST_PATH = ".claude/scripts/tests/test_monster_name_ssot.py"
VERIFIER_PATH = ".claude/scripts/verify_zh.sh"
REVIEWER = "zh-code-reviewer"
OLD_FIXTURE_PARENT = b'dir=REPO_ROOT / ".claude"'
NEW_FIXTURE_PARENT = b'dir=audit.ROOT / ".claude"'
POLICY_MANIFEST = (
    ".agents/policies/review-contract.md",
    ".claude/agents/translation-reviewer.md",
    ".claude/agents/zh-code-reviewer.md",
    ".claude/scripts/review_rootfix_gate.py",
    ".claude/scripts/tests/test_review_rootfix_gate.py",
    ".claude/skills/translation-reviewer.md",
    ".claude/skills/zh-code-reviewer.md",
    ".codex/agents/translation-reviewer.toml",
    ".codex/agents/zh-code-reviewer.toml",
    ".opencode/agents/translation-reviewer.md",
    ".opencode/agents/zh-code-reviewer.md",
    ".opencode/skills/translation-reviewer/SKILL.md",
    ".opencode/skills/zh-code-reviewer/SKILL.md",
    ".pi/agents/translation-reviewer.md",
    ".pi/agents/zh-code-reviewer.md",
    "docs/zh-testing.md",
)
POLICY_MANIFEST_SHA256 = hashlib.sha256(
    ("".join(f"{path}\n" for path in POLICY_MANIFEST)).encode("utf-8")
).hexdigest()
NEW_POLICY_PATHS = frozenset(
    (
        ".claude/scripts/review_rootfix_gate.py",
        ".claude/scripts/tests/test_review_rootfix_gate.py",
    )
)
APPROVAL_FIELDS = frozenset(
    (
        "schema",
        "exception_id",
        "base_c",
        "policy_head",
        "candidate_head",
        "bundle_id",
        "bundle_sha256",
        "diff_sha256",
        "glossary_sha256",
        "routing_sha256",
        "readiness",
        "policy_manifest_sha256",
        "candidate_test",
        "attempts",
        "attempt_id",
        "attempt_sha256",
        "verdict",
    )
)


class RootfixError(RuntimeError):
    """A fail-closed rootfix gate rejection."""


class StaleRootfixError(RootfixError):
    """Rootfix staging exists but no live operation owns it."""


class RootfixSignalInterrupt(KeyboardInterrupt):
    """A catchable gate-boundary signal deferred through durable retirement."""

    def __init__(self, signum: int):
        super().__init__(signum)
        self.signum = signum


class RootfixEstablishedTerminalInterrupt(RootfixSignalInterrupt):
    """A deferred signal carrying an already validated attempt terminal."""

    def __init__(
        self,
        signum: int,
        terminal: tuple[str, int, str | None, int | None],
    ):
        super().__init__(signum)
        self.terminal = terminal


class FileSnapshot(NamedTuple):
    """One no-follow descriptor read plus its immutable pathname identity."""

    path: Path
    data: bytes
    dev: int
    ino: int
    size: int
    sha256: str
    mtime_ns: int
    ctime_ns: int


class ArchiveSeal(NamedTuple):
    """Identity which a just-published recovery object must retain."""

    path: Path
    dev: int
    ino: int
    size: int
    sha256: str
    kind: str

    def __fspath__(self) -> str:
        return os.fspath(self.path)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def parent(self) -> Path:
        return self.path.parent

    def exists(self) -> bool:
        return self.path.exists()


class DirectoryHandle:
    """A held directory descriptor and its first observed identity."""

    def __init__(self, path: Path, fd: int, dev: int, ino: int) -> None:
        self.path = path
        self.fd = fd
        self.dev = dev
        self.ino = ino

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


class EvidenceContext:
    """Held descriptors for the active evidence root and attempts directory."""

    def __init__(
        self,
        root: DirectoryHandle,
        attempts: DirectoryHandle | None,
    ) -> None:
        self.root = root
        self.attempts = attempts

    def close(self) -> None:
        if self.attempts is not None:
            self.attempts.close()
        self.root.close()


class RootInventorySnapshot(NamedTuple):
    """The single mechanically bound first observation of active evidence."""

    root_identity: tuple[int, int]
    attempts_identity: tuple[int, int] | None
    marker: FileSnapshot | None
    approval: FileSnapshot | None
    atomic_temps: tuple[FileSnapshot, ...]


def _identity(info: os.stat_result) -> tuple[int, int]:
    return info.st_dev, info.st_ino


def _content_identity(
    info: os.stat_result,
) -> tuple[int, int, int, int, int]:
    """Identity plus kernel-maintained content-change generations."""

    return (
        info.st_dev,
        info.st_ino,
        info.st_size,
        info.st_mtime_ns,
        info.st_ctime_ns,
    )


def _directory_flags() -> int:
    return (
        os.O_RDONLY
        | getattr(os, "O_DIRECTORY", 0)
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )


def _open_directory_path(path: Path, label: str) -> DirectoryHandle:
    fd = -1
    retained = False
    try:
        before = os.lstat(path)
        if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
            raise RootfixError(f"{label} is unsafe: {path}")
        fd = os.open(path, _directory_flags())
        opened = os.fstat(fd)
        after = os.lstat(path)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(after.st_mode)
            or _identity(opened) != _identity(before)
            or _identity(after) != _identity(opened)
        ):
            raise RootfixError(f"{label} changed while opening: {path}")
        retained = True
        return DirectoryHandle(path, fd, opened.st_dev, opened.st_ino)
    except OSError as error:
        raise RootfixError(f"{label} cannot be opened: {path}") from error
    finally:
        if fd >= 0 and not retained:
            os.close(fd)


def _open_child_directory(
    parent: DirectoryHandle,
    name: str,
    label: str,
    *,
    create: bool = False,
) -> DirectoryHandle:
    if not name or name in (".", "..") or "/" in name or os.sep in name:
        raise RootfixError(f"{label} name is invalid: {name!r}")
    _validate_directory_handle(parent, label=f"{label} parent")
    try:
        before = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    except FileNotFoundError:
        if not create:
            raise
        try:
            os.mkdir(name, 0o700, dir_fd=parent.fd)
            os.fsync(parent.fd)
        except FileExistsError:
            pass
        before = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise RootfixError(f"{label} is unsafe: {parent.path / name}")
    fd = -1
    try:
        fd = os.open(name, _directory_flags(), dir_fd=parent.fd)
        opened = os.fstat(fd)
        after = os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
        if (
            not stat.S_ISDIR(opened.st_mode)
            or not stat.S_ISDIR(after.st_mode)
            or _identity(opened) != _identity(before)
            or _identity(after) != _identity(opened)
        ):
            raise RootfixError(
                f"{label} changed while opening: {parent.path / name}"
            )
        return DirectoryHandle(
            parent.path / name,
            fd,
            opened.st_dev,
            opened.st_ino,
        )
    except BaseException as error:
        if fd >= 0:
            os.close(fd)
        if not isinstance(error, OSError):
            raise
        raise RootfixError(
            f"{label} cannot be opened: {parent.path / name}"
        ) from error


def _validate_directory_handle(
    directory: DirectoryHandle,
    *,
    parent: DirectoryHandle | None = None,
    name: str | None = None,
    label: str = "rootfix directory",
) -> None:
    if directory.fd < 0:
        raise RootfixError(f"{label} descriptor is closed")
    try:
        descriptor = os.fstat(directory.fd)
        pathname = (
            os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
            if parent is not None and name is not None
            else os.lstat(directory.path)
        )
    except OSError as error:
        raise RootfixError(f"{label} identity cannot be revalidated") from error
    expected = (directory.dev, directory.ino)
    if (
        not stat.S_ISDIR(descriptor.st_mode)
        or not stat.S_ISDIR(pathname.st_mode)
        or _identity(descriptor) != expected
        or _identity(pathname) != expected
    ):
        raise RootfixError(f"{label} identity changed")


def _directory_generation(
    directory: DirectoryHandle,
    *,
    parent: DirectoryHandle | None = None,
    name: str | None = None,
    label: str = "rootfix directory",
) -> tuple[int, int, int, int, int]:
    """Bind a held directory's identity and kernel content generation."""

    _validate_directory_handle(
        directory,
        parent=parent,
        name=name,
        label=label,
    )
    try:
        descriptor = os.fstat(directory.fd)
        pathname = (
            os.stat(name, dir_fd=parent.fd, follow_symlinks=False)
            if parent is not None and name is not None
            else os.lstat(directory.path)
        )
    except OSError as error:
        raise RootfixError(
            f"{label} generation cannot be observed"
        ) from error
    descriptor_generation = _content_identity(descriptor)
    if descriptor_generation != _content_identity(pathname):
        raise RootfixError(f"{label} changed while observing generation")
    return descriptor_generation


def _require_directory_generation(
    directory: DirectoryHandle,
    expected: tuple[int, int, int, int, int],
    *,
    parent: DirectoryHandle | None = None,
    name: str | None = None,
    label: str = "rootfix directory",
) -> None:
    if _directory_generation(
        directory,
        parent=parent,
        name=name,
        label=label,
    ) != expected:
        raise RootfixError(f"{label} contents changed during enumeration")


def _open_evidence_context(
    root: Path,
    *,
    create_attempts: bool,
    require_attempts: bool = False,
) -> EvidenceContext:
    root_handle = _open_directory_path(root, "rootfix evidence root")
    attempts: DirectoryHandle | None = None
    try:
        try:
            attempts = _open_child_directory(
                root_handle,
                "attempts",
                "rootfix attempts",
                create=create_attempts,
            )
        except FileNotFoundError:
            if require_attempts:
                raise RootfixError("rootfix attempts directory is missing")
        return EvidenceContext(root_handle, attempts)
    except BaseException:
        if attempts is not None:
            attempts.close()
        root_handle.close()
        raise


def _validate_evidence_context(context: EvidenceContext) -> None:
    _validate_directory_handle(context.root, label="rootfix evidence root")
    if context.attempts is not None:
        _validate_directory_handle(
            context.attempts,
            parent=context.root,
            name="attempts",
            label="rootfix attempts",
        )


def _read_regular_at(
    directory: DirectoryHandle,
    name: str,
    label: str,
    *,
    expected: os.stat_result | None = None,
    max_bytes: int | None = None,
) -> FileSnapshot:
    """Read once from an O_NOFOLLOW fd and bind before/open/after identity."""

    _validate_directory_handle(directory, label=f"{label} parent")
    fd = -1
    try:
        before = os.stat(name, dir_fd=directory.fd, follow_symlinks=False)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or (
                expected is not None
                and _identity(before) != _identity(expected)
            )
            or (max_bytes is not None and before.st_size > max_bytes)
        ):
            raise RootfixError(f"{label} identity, type, size or link count is unsafe")
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        fd = os.open(name, flags, dir_fd=directory.fd)
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_nlink != 1
            or _identity(opened) != _identity(before)
            or _content_identity(opened) != _content_identity(before)
        ):
            raise RootfixError(f"{label} changed while opening")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if max_bytes is not None and total > max_bytes:
                raise RootfixError(f"{label} exceeds its size limit")
            chunks.append(chunk)
        data = b"".join(chunks)
        after_descriptor = os.fstat(fd)
        after_path = os.stat(
            name, dir_fd=directory.fd, follow_symlinks=False
        )
        if (
            not stat.S_ISREG(after_descriptor.st_mode)
            or not stat.S_ISREG(after_path.st_mode)
            or after_descriptor.st_nlink != 1
            or after_path.st_nlink != 1
            or _content_identity(after_descriptor)
            != _content_identity(opened)
            or _content_identity(after_path)
            != _content_identity(opened)
            or after_descriptor.st_size != len(data)
            or after_path.st_size != len(data)
        ):
            raise RootfixError(f"{label} changed while reading")
        return FileSnapshot(
            directory.path / name,
            data,
            opened.st_dev,
            opened.st_ino,
            len(data),
            hashlib.sha256(data).hexdigest(),
            opened.st_mtime_ns,
            opened.st_ctime_ns,
        )
    except OSError as error:
        raise RootfixError(f"{label} cannot be read safely") from error
    finally:
        if fd >= 0:
            os.close(fd)


def _read_regular_snapshot(
    path: Path,
    label: str,
    *,
    max_bytes: int | None = None,
) -> FileSnapshot:
    parent = _open_directory_path(path.parent, f"{label} parent")
    try:
        return _read_regular_at(
            parent,
            path.name,
            label,
            max_bytes=max_bytes,
        )
    finally:
        parent.close()


def _snapshot_writer_stream(
    path: Path,
    stream: Any,
    label: str,
) -> FileSnapshot:
    """Bind bytes written through a held FD to the final pathname identity."""

    try:
        stream.flush()
        os.fsync(stream.fileno())
        descriptor_before = os.fstat(stream.fileno())
        pathname_before = os.lstat(path)
        if (
            not stat.S_ISREG(descriptor_before.st_mode)
            or not stat.S_ISREG(pathname_before.st_mode)
            or descriptor_before.st_nlink != 1
            or pathname_before.st_nlink != 1
            or _content_identity(pathname_before)
            != _content_identity(descriptor_before)
        ):
            raise RootfixError(
                f"{label} writer descriptor no longer names the evidence path"
            )
        stream.seek(0)
        data = stream.read()
        descriptor_after = os.fstat(stream.fileno())
        pathname_after = os.lstat(path)
        if (
            not isinstance(data, bytes)
            or not stat.S_ISREG(descriptor_after.st_mode)
            or not stat.S_ISREG(pathname_after.st_mode)
            or descriptor_after.st_nlink != 1
            or pathname_after.st_nlink != 1
            or _content_identity(descriptor_after)
            != _content_identity(descriptor_before)
            or _content_identity(pathname_after)
            != _content_identity(descriptor_before)
            or descriptor_after.st_size != len(data)
            or pathname_after.st_size != len(data)
        ):
            raise RootfixError(
                f"{label} changed between writer completion and snapshot"
            )
        return FileSnapshot(
            path,
            data,
            descriptor_after.st_dev,
            descriptor_after.st_ino,
            len(data),
            hashlib.sha256(data).hexdigest(),
            descriptor_after.st_mtime_ns,
            descriptor_after.st_ctime_ns,
        )
    except OSError as error:
        raise RootfixError(
            f"{label} writer snapshot cannot be established"
        ) from error


def _read_regular_bytes(path: Path, label: str = "rootfix file") -> bytes:
    return _read_regular_snapshot(path, label).data


def _atomic_rename_noreplace_at(
    source_directory: DirectoryHandle,
    source_name: str,
    target_directory: DirectoryHandle,
    target_name: str,
) -> None:
    """Atomically rename between held directories without replacement."""

    _validate_directory_handle(source_directory)
    _validate_directory_handle(target_directory)
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
            source_directory.fd,
            os.fsencode(source_name),
            target_directory.fd,
            os.fsencode(target_name),
            1,
        )
        if result == 0:
            return
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise FileExistsError(error, os.strerror(error), target_name)
        if error not in (errno.ENOSYS, errno.EINVAL):
            raise OSError(error, os.strerror(error), target_name)

    renameatx_np = getattr(libc, "renameatx_np", None)
    if renameatx_np is not None:
        renameatx_np.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameatx_np.restype = ctypes.c_int
        result = renameatx_np(
            source_directory.fd,
            os.fsencode(source_name),
            target_directory.fd,
            os.fsencode(target_name),
            0x00000004,
        )
        if result == 0:
            return
        error = ctypes.get_errno()
        if error == errno.EEXIST:
            raise FileExistsError(error, os.strerror(error), target_name)
        if error not in (errno.ENOSYS, errno.EINVAL, errno.ENOTSUP):
            raise OSError(error, os.strerror(error), target_name)
    raise OSError(errno.ENOSYS, "atomic no-replace renameat is unavailable")


def _atomic_write_once_at(
    directory: DirectoryHandle,
    name: str,
    data: bytes,
) -> bool:
    """Durably publish a regular file relative to a held directory."""

    if not isinstance(data, bytes):
        raise TypeError("atomic write-once data must be bytes")
    if not name or name in (".", "..") or "/" in name or os.sep in name:
        raise RootfixError("atomic write-once target name is invalid")
    _validate_directory_handle(directory)
    try:
        existing_info = os.stat(
            name, dir_fd=directory.fd, follow_symlinks=False
        )
    except FileNotFoundError:
        existing_info = None
    if existing_info is not None:
        current = _read_regular_at(
            directory,
            name,
            "deterministic rootfix evidence",
            expected=existing_info,
            max_bytes=MAX_ROOT_ATOMIC_BYTES,
        )
        if current.data == data:
            return False
        raise RootfixError(
            f"deterministic rootfix evidence conflicts: {directory.path / name}"
        )

    temporary = f".tmp-{name}-{os.getpid()}-{secrets.token_hex(8)}"
    flags = (
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    fd = os.open(temporary, flags, 0o600, dir_fd=directory.fd)
    created = os.fstat(fd)
    if (
        not stat.S_ISREG(created.st_mode)
        or created.st_nlink != 1
        or created.st_size != 0
    ):
        os.close(fd)
        raise RootfixError("rootfix atomic temporary was not created safely")
    try:
        view = memoryview(data)
        while view:
            written = os.write(fd, view)
            view = view[written:]
        os.fsync(fd)
        written_info = os.fstat(fd)
        if (
            _identity(written_info) != _identity(created)
            or written_info.st_nlink != 1
            or written_info.st_size != len(data)
        ):
            raise RootfixError(
                "rootfix atomic temporary changed while writing"
            )
        try:
            _atomic_rename_noreplace_at(
                directory, temporary, directory, name
            )
        except FileExistsError:
            current = _read_regular_at(
                directory,
                name,
                "deterministic rootfix evidence",
                max_bytes=MAX_ROOT_ATOMIC_BYTES,
            )
            if current.data != data:
                raise RootfixError(
                    "deterministic rootfix evidence raced with conflicting content"
                )
            raise RootfixError(
                "deterministic rootfix evidence raced with identical content; "
                "the unpublished temporary is retained"
            )
        current = _read_regular_at(
            directory,
            name,
            "published deterministic rootfix evidence",
            expected=created,
            max_bytes=MAX_ROOT_ATOMIC_BYTES,
        )
        if current.data != data:
            raise RootfixError(
                "published deterministic rootfix evidence changed"
            )
        os.fsync(directory.fd)
        return True
    finally:
        # Never unlink an unpublished pathname after a failure: no portable
        # unlink-by-inode primitive exists, so a check-then-unlink cleanup
        # could delete an attacker-supplied replacement.  The residue stays
        # available for explicit stale recovery (or in the retained staging
        # tree) and therefore remains auditable.
        os.close(fd)


def _bootstrap_environment() -> dict[str, str]:
    """Return the minimal Git environment used before repository imports."""

    environment = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
        "LANG": "C",
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    for name in (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_REPLACE_REF_BASE",
        "GIT_CEILING_DIRECTORIES",
        "GIT_DISCOVERY_ACROSS_FILESYSTEM",
    ):
        environment.pop(name, None)
    return environment


def _bootstrap_git(
    repo: Path,
    *arguments: str,
    input_data: bytes | None = None,
) -> bytes:
    git = shutil.which(
        "git",
        path="/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin",
    )
    if git is None:
        raise RootfixError("trusted Git executable is unavailable")
    process = subprocess.run(
        [git, "-C", os.fspath(repo), *arguments],
        input=input_data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_bootstrap_environment(),
        check=False,
    )
    if process.returncode:
        message = process.stderr.decode(
            "utf-8", errors="replace"
        ).strip()
        raise RootfixError(
            message or f"bootstrap git {' '.join(arguments)} failed"
        )
    return process.stdout


def _bootstrap_commit(repo: Path) -> str:
    try:
        value = _bootstrap_git(repo, "rev-parse", "--verify", "HEAD").decode(
            "ascii", errors="strict"
        ).strip()
    except UnicodeDecodeError as error:
        raise RootfixError("bootstrap target HEAD is not ASCII") from error
    if re.fullmatch(r"[0-9a-f]{40,64}", value) is None:
        raise RootfixError("bootstrap target HEAD is invalid")
    return value


def _bootstrap_top(repo: Path) -> Path:
    try:
        value = _bootstrap_git(
            repo, "rev-parse", "--show-toplevel"
        ).decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as error:
        raise RootfixError(
            "bootstrap target root is not strict UTF-8"
        ) from error
    if not value or not Path(value).is_absolute():
        raise RootfixError("bootstrap target root is invalid")
    try:
        return Path(value).resolve(strict=True)
    except OSError as error:
        raise RootfixError(
            "bootstrap target root cannot be resolved"
        ) from error


def _bootstrap_git_blob(
    repo: Path,
    commit: str,
    path: str,
) -> tuple[str, bytes]:
    raw = _bootstrap_git(repo, "ls-tree", "-z", commit, "--", path)
    records = [record for record in raw.split(b"\0") if record]
    if len(records) != 1:
        raise RootfixError(f"trusted bootstrap blob is missing: {path}")
    metadata, separator, raw_path = records[0].partition(b"\t")
    fields = metadata.split()
    if (
        not separator
        or len(fields) != 3
        or fields[1] != b"blob"
        or raw_path != os.fsencode(path)
    ):
        raise RootfixError(f"trusted bootstrap tree entry is invalid: {path}")
    try:
        mode = fields[0].decode("ascii", errors="strict")
        oid = fields[2].decode("ascii", errors="strict")
    except UnicodeDecodeError as error:
        raise RootfixError(
            f"trusted bootstrap tree entry is invalid: {path}"
        ) from error
    if (
        mode not in ("100644", "100755")
        or re.fullmatch(r"[0-9a-f]{40,64}", oid) is None
    ):
        raise RootfixError(f"trusted bootstrap blob mode is invalid: {path}")
    return mode, _bootstrap_git(repo, "cat-file", "blob", oid)


def _exec_trusted_module(
    name: str,
    path: Path,
    source: bytes,
) -> types.ModuleType:
    try:
        text = source.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RootfixError(
            f"trusted module is not strict UTF-8: {path}"
        ) from error
    module = types.ModuleType(name)
    module.__file__ = os.fspath(path)
    module.__package__ = ""
    module.__cached__ = os.fspath(
        PRIVATE_PYCACHE_PREFIX / f"{name}.trusted.pyc"
    )
    previous = sys.modules.get(name)
    sys.modules[name] = module
    try:
        exec(
            compile(text, os.fspath(path), "exec", dont_inherit=True),
            module.__dict__,
        )
    except BaseException:
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
        raise
    return module


def _load_trusted_repository_modules(target_repo: Path) -> None:
    """Compile repository helpers only from one exact target Git commit."""

    global rb, _TRUSTED_POLICY_HEAD, _TRUSTED_SOURCE_BLOBS
    target_top = _bootstrap_top(target_repo)
    policy_head = _bootstrap_commit(target_top)
    _, shared_source = _bootstrap_git_blob(
        target_top, policy_head, I18N_SHARED_PATH
    )
    _, bundle_source = _bootstrap_git_blob(
        target_top, policy_head, BUNDLE_PATH
    )
    _, verifier_source = _bootstrap_git_blob(
        target_top, policy_head, VERIFIER_PATH
    )
    _, contract_source = _bootstrap_git_blob(
        target_top, policy_head, PROFILE_CONTRACT_PATH
    )
    shared_path = target_top / I18N_SHARED_PATH
    bundle_path = target_top / BUNDLE_PATH
    _exec_trusted_module("i18n_shared", shared_path, shared_source)
    rb = _exec_trusted_module(
        "review_bundle", bundle_path, bundle_source
    )
    _TRUSTED_POLICY_HEAD = policy_head
    _TRUSTED_SOURCE_BLOBS = {
        I18N_SHARED_PATH: shared_source,
        BUNDLE_PATH: bundle_source,
        VERIFIER_PATH: verifier_source,
        PROFILE_CONTRACT_PATH: contract_source,
    }


def _git(repo: Path, *arguments: str) -> bytes:
    process = subprocess.run(
        [rb.GIT_BINARY, "-C", os.fspath(repo), *arguments],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=rb._trusted_child_environment(),
        check=False,
    )
    if process.returncode:
        message = process.stderr.decode("utf-8", errors="replace").strip()
        raise RootfixError(message or f"git {' '.join(arguments)} failed")
    return process.stdout


def _git_text(repo: Path, *arguments: str) -> str:
    try:
        return _git(repo, *arguments).decode("utf-8", errors="strict").strip()
    except UnicodeDecodeError as error:
        raise RootfixError("git returned non-UTF-8 text") from error


def _profile_diff_hash(
    repo: Path,
    target_head: str,
    candidate_head: str,
) -> str:
    diff = _git(
        repo,
        "diff",
        "--binary",
        f"{target_head}..{candidate_head}",
        "--",
    )
    raw = _bootstrap_git(repo, "hash-object", "--stdin", input_data=diff)
    try:
        value = raw.decode("ascii", errors="strict").strip()
    except UnicodeDecodeError as error:
        raise RootfixError("profile diff hash is not ASCII") from error
    if re.fullmatch(r"[0-9a-f]{40,64}", value) is None:
        raise RootfixError("profile diff hash is invalid")
    return value


def _bind_runtime_status(
    status: dict[str, Any],
    candidate_top: Path,
    candidate_test: dict[str, Any],
) -> dict[str, Any]:
    bound = dict(status)
    if (
        _TEST_MODE
        and re.fullmatch(
            r"[0-9a-f]{40,64}",
            str(status.get("_rootfix_profile_diff_hash", "")),
        )
        is not None
    ):
        profile_diff_hash = status["_rootfix_profile_diff_hash"]
    else:
        profile_diff_hash = _profile_diff_hash(
            candidate_top,
            status["target_head"],
            status["candidate_head"],
        )
    bound["_rootfix_profile_diff_hash"] = profile_diff_hash
    bound["_rootfix_candidate_blob_sha256"] = candidate_test[
        "candidate_blob_sha256"
    ]
    return bound


def _single_parent(repo: Path, commit: str, label: str) -> str:
    fields = _git_text(repo, "rev-list", "--parents", "-n", "1", commit).split()
    if len(fields) != 2 or fields[0] != commit:
        raise RootfixError(f"{label} must be one commit with exactly one parent")
    return fields[1]


def _changed_paths(repo: Path, base: str, head: str) -> tuple[str, ...]:
    data = _git(
        repo,
        "diff",
        "--no-renames",
        "--name-only",
        "-z",
        f"{base}..{head}",
        "--",
    )
    try:
        paths = tuple(
            path.decode("utf-8", errors="strict")
            for path in data.split(b"\0")
            if path
        )
    except UnicodeDecodeError as error:
        raise RootfixError("changed path is not strict UTF-8") from error
    if paths != tuple(sorted(set(paths))):
        raise RootfixError("changed paths are not normalized, sorted, and unique")
    return paths


def _tree_entry(
    repo: Path, commit: str, path: str
) -> tuple[str, str, str] | None:
    data = _git(repo, "ls-tree", "-z", commit, "--", path)
    records = [record for record in data.split(b"\0") if record]
    if not records:
        return None
    if len(records) != 1:
        raise RootfixError(f"ambiguous Git tree entry: {commit}:{path}")
    try:
        header, listed = records[0].split(b"\t", 1)
        mode, kind, object_id = header.decode("ascii").split()
        listed_path = listed.decode("utf-8", errors="strict")
    except (UnicodeDecodeError, ValueError) as error:
        raise RootfixError("invalid Git tree metadata") from error
    if listed_path != path:
        raise RootfixError(f"Git tree path mismatch: {listed_path} != {path}")
    return mode, kind, object_id


def _validate_policy_modes(repo: Path, policy_head: str) -> None:
    for path in POLICY_MANIFEST:
        base_entry = _tree_entry(repo, BASE_C, path)
        policy_entry = _tree_entry(repo, policy_head, path)
        if policy_entry is None:
            raise RootfixError(f"P2 is missing frozen manifest path: {path}")
        policy_mode, policy_kind, _ = policy_entry
        if policy_kind != "blob" or policy_mode not in ("100644", "100755"):
            raise RootfixError(f"P2 manifest path is not a regular file: {path}")
        if path in NEW_POLICY_PATHS:
            if base_entry is not None or policy_mode != "100644":
                raise RootfixError(
                    f"new rootfix gate path has an invalid base entry or mode: {path}"
                )
        elif (
            base_entry is None
            or base_entry[0] != policy_mode
            or base_entry[1] != policy_kind
        ):
            raise RootfixError(f"P2 changed the existing file mode or type: {path}")


def _validate_policy_lineage(repo: Path, policy_head: str) -> None:
    if _single_parent(repo, POLICY_P, "P") != BASE_C:
        raise RootfixError(f"installed P^ must equal Base C {BASE_C}")
    if _single_parent(repo, policy_head, "P2") != POLICY_P:
        raise RootfixError(f"P2^ must equal installed P {POLICY_P}")
    if _changed_paths(repo, BASE_C, POLICY_P) != POLICY_MANIFEST:
        raise RootfixError(
            "Base C..P does not equal the frozen 16-path manifest"
        )
    if _changed_paths(repo, POLICY_P, policy_head) != POLICY_MANIFEST:
        raise RootfixError(
            "P..P2 does not equal the frozen 16-path correction manifest"
        )
    if _changed_paths(repo, BASE_C, policy_head) != POLICY_MANIFEST:
        raise RootfixError(
            "Base C..P2 contains a path outside the frozen manifest"
        )
    _validate_policy_modes(repo, policy_head)


def _require_clean_checkout(repo: Path, commit: str, label: str) -> Path:
    try:
        return rb._assert_checkout(repo, commit, label)
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(str(error)) from error


def _candidate_test_record(
    repo: Path, policy_head: str, candidate_head: str
) -> tuple[dict[str, Any], bytes]:
    try:
        policy_mode, policy_blob = rb.read_regular_git_blob(
            repo, policy_head, TEST_PATH, with_mode=True
        )
        candidate_mode, candidate_blob = rb.read_regular_git_blob(
            repo, candidate_head, TEST_PATH, with_mode=True
        )
    except (OSError, rb.AuditInputError) as error:
        raise RootfixError(str(error)) from error
    if policy_mode != candidate_mode:
        raise RootfixError("F2 changed the candidate-test file mode")
    if policy_blob.count(OLD_FIXTURE_PARENT) != 1:
        raise RootfixError(
            "P2 test does not contain exactly one approved fixture parent"
        )
    if NEW_FIXTURE_PARENT in policy_blob:
        raise RootfixError("P2 test already contains the candidate-root fixture parent")
    expected = policy_blob.replace(
        OLD_FIXTURE_PARENT, NEW_FIXTURE_PARENT, 1
    )
    if candidate_blob != expected:
        raise RootfixError(
            "F2 test blob is not the exact approved one-line replacement"
        )
    return (
        {
            "path": TEST_PATH,
            "mode": candidate_mode,
            "policy_blob_sha256": hashlib.sha256(policy_blob).hexdigest(),
            "candidate_blob_sha256": hashlib.sha256(candidate_blob).hexdigest(),
            "replacement_count": 1,
        },
        candidate_blob,
    )


def _validate_trusted_gate(
    repo: Path, target_top: Path, policy_head: str
) -> None:
    if (
        _TRUSTED_POLICY_HEAD != policy_head
        or not _TRUSTED_SOURCE_BLOBS
    ):
        raise RootfixError(
            "repository helpers were not loaded from the exact P2 commit"
        )
    expected_gate = target_top / GATE_PATH
    expected_bundle = target_top / BUNDLE_PATH
    expected_shared = target_top / I18N_SHARED_PATH
    actual_gate = Path(__file__).absolute()
    actual_bundle = Path(rb.__file__).absolute()
    shared = sys.modules.get("i18n_shared")
    actual_shared = (
        Path(shared.__file__).absolute()
        if shared is not None and getattr(shared, "__file__", None)
        else None
    )
    if (
        actual_gate != expected_gate
        or actual_bundle != expected_bundle
        or actual_shared != expected_shared
    ):
        raise RootfixError(
            "rootfix gate and repository helpers must execute from P2 target"
        )
    for working_path, relative, label in (
        (actual_gate, GATE_PATH, "rootfix gate"),
        (actual_bundle, BUNDLE_PATH, "review bundle"),
        (actual_shared, I18N_SHARED_PATH, "i18n shared helper"),
        (
            target_top / PROFILE_CONTRACT_PATH,
            PROFILE_CONTRACT_PATH,
            "rootfix code-profile contract",
        ),
        (
            target_top / VERIFIER_PATH,
            VERIFIER_PATH,
            "rootfix verifier",
        ),
    ):
        try:
            working_bytes = _read_regular_bytes(working_path, label)
            mode, committed = rb.read_regular_git_blob(
                repo, policy_head, relative, with_mode=True
            )
        except (OSError, rb.AuditInputError, rb.ReviewBundleError) as error:
            raise RootfixError(str(error)) from error
        if mode not in ("100644", "100755") or working_bytes != committed:
            raise RootfixError(f"{label} differs from the P2 Git blob")
        loaded = _TRUSTED_SOURCE_BLOBS.get(relative)
        if loaded is not None and loaded != committed:
            raise RootfixError(
                f"{label} loaded bytes differ from the P2 Git blob"
            )


def _worktree_records(repo: Path) -> list[dict[str, str]]:
    data = _git(repo, "worktree", "list", "--porcelain", "-z")
    records: list[dict[str, str]] = []
    for raw_record in data.split(b"\0\0"):
        if not raw_record:
            continue
        fields: dict[str, str] = {}
        for raw_field in raw_record.split(b"\0"):
            if not raw_field:
                continue
            try:
                field = raw_field.decode("utf-8", errors="strict")
            except UnicodeDecodeError as error:
                raise RootfixError("worktree metadata is not strict UTF-8") from error
            name, separator, value = field.partition(" ")
            if not name or name in fields:
                raise RootfixError("worktree metadata fields are invalid")
            fields[name] = value if separator else ""
        if "worktree" not in fields or "HEAD" not in fields:
            raise RootfixError("worktree metadata is incomplete")
        records.append(fields)
    if not records:
        raise RootfixError("target Git worktree inventory is empty")
    return records


def _validate_linked_worktree(
    target_top: Path,
    candidate_top: Path,
    candidate_head: str,
) -> None:
    if (
        target_top == candidate_top
        or Path(os.path.realpath(target_top))
        == Path(os.path.realpath(candidate_top))
    ):
        raise RootfixError("P2 target and F2 candidate must be distinct worktrees")
    try:
        target_common = rb.git_common_dir(target_top)
        candidate_common = rb.git_common_dir(candidate_top)
        target_info = os.stat(target_common, follow_symlinks=False)
        candidate_info = os.stat(candidate_common, follow_symlinks=False)
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(str(error)) from error
    if (
        Path(os.path.realpath(target_common))
        != Path(os.path.realpath(candidate_common))
        or (target_info.st_dev, target_info.st_ino)
        != (candidate_info.st_dev, candidate_info.st_ino)
    ):
        raise RootfixError(
            "P2 target and F2 candidate do not share one Git common directory"
        )

    candidate_physical = Path(os.path.realpath(candidate_top))
    matches = []
    for record in _worktree_records(target_top):
        listed = record["worktree"]
        if not listed or not Path(listed).is_absolute():
            raise RootfixError("target worktree inventory contains a non-absolute path")
        if Path(os.path.realpath(listed)) == candidate_physical:
            matches.append(record)
    if len(matches) != 1:
        raise RootfixError(
            "F2 candidate is not uniquely listed by the P2 target worktree inventory"
        )
    if matches[0]["HEAD"] != candidate_head:
        raise RootfixError("P2 target worktree inventory binds F2 to a different HEAD")


def _validate_topology(
    candidate_repo: Path,
    target_repo: Path,
    status: dict[str, Any],
) -> tuple[Path, Path, dict[str, Any], bytes]:
    policy_head = status["target_head"]
    candidate_head = status["candidate_head"]
    target_top = _require_clean_checkout(target_repo, policy_head, "P2 target")
    candidate_top = _require_clean_checkout(
        candidate_repo, candidate_head, "F2 candidate"
    )
    _validate_linked_worktree(target_top, candidate_top, candidate_head)
    _validate_trusted_gate(target_top, target_top, policy_head)
    _validate_policy_lineage(candidate_top, policy_head)
    if _single_parent(candidate_top, candidate_head, "F2") != policy_head:
        raise RootfixError("F2^ must equal the exact approved P2 OID")
    if _changed_paths(candidate_top, policy_head, candidate_head) != (TEST_PATH,):
        raise RootfixError("P2..F2 does not equal the frozen one-path manifest")
    candidate_test, candidate_blob = _candidate_test_record(
        candidate_top, policy_head, candidate_head
    )
    return target_top, candidate_top, candidate_test, candidate_blob


def _validate_bundle_status(status: dict[str, Any]) -> None:
    if status.get("legacy_read_only"):
        raise RootfixError("legacy review evidence is not accepted")
    if status.get("routing_files") != [TEST_PATH]:
        raise RootfixError("bundle routing scope is not the exact F2 test path")
    if status.get("required_reviewers") != [REVIEWER]:
        raise RootfixError("bundle must route exactly one zh-code-reviewer")
    if status.get("ready_reviewers") != [REVIEWER] or not status.get("ready"):
        raise RootfixError("exact reviewer readiness-v3 is incomplete")
    counts = status.get("finding_counts", {}).get(REVIEWER)
    if not isinstance(counts, dict):
        raise RootfixError("reviewer finding counts are missing")
    if counts.get("blocker") != 0 or counts.get("needs_fix") != 0:
        raise RootfixError("reviewer readiness contains blocking findings")
    if status.get("attempts") or status.get("passing_attempt") is not None:
        raise RootfixError("normal final attempts may not be reused by rootfix")
    if status.get("approved") or status.get("approval") is not None:
        raise RootfixError("normal final approval may not be reused by rootfix")
    if status.get("state") != "FINAL_GATE_REQUIRED":
        raise RootfixError("bundle is not at the exact post-readiness boundary")


def _safe_directory(parent: Path, name: str) -> Path:
    path = parent / name
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        try:
            os.mkdir(path, 0o700)
            rb._fsync_directory(parent)
        except FileExistsError:
            pass
        info = os.lstat(path)
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise RootfixError(f"unsafe evidence directory: {path}")
    return path


def _evidence_path(repo: Path, bundle_id: str, *, create: bool) -> Path:
    common = rb.git_common_dir(repo)
    if create:
        root = _safe_directory(common, EVIDENCE_PARTS[0])
        rootfix = _safe_directory(root, EVIDENCE_PARTS[1])
        return _safe_directory(rootfix, bundle_id)
    root = common / EVIDENCE_PARTS[0]
    rootfix = root / EVIDENCE_PARTS[1]
    evidence = rootfix / bundle_id
    try:
        rb._require_directory(root, "review evidence root")
        rb._require_directory(rootfix, "rootfix evidence root")
        rb._require_directory(evidence, "rootfix bundle evidence")
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(str(error)) from error
    return evidence


def _recovery_archive_path(
    repo: Path,
    bundle_id: str,
    *,
    create: bool,
) -> Path | None:
    if rb.RUN_ID_RE.fullmatch(bundle_id) is None:
        raise RootfixError("rootfix recovery archive bundle ID is invalid")
    common = rb.git_common_dir(repo)
    root = common / EVIDENCE_PARTS[0]
    archive_root = root / RECOVERY_ARCHIVE_PART
    archive = archive_root / bundle_id
    if create:
        root = _safe_directory(common, EVIDENCE_PARTS[0])
        archive_root = _safe_directory(root, RECOVERY_ARCHIVE_PART)
        return _safe_directory(archive_root, bundle_id)

    try:
        root_info = rb._lstat(root)
        if root_info is None:
            return None
        rb._require_directory(root, "review evidence root")
        archive_root_info = rb._lstat(archive_root)
        if archive_root_info is None:
            return None
        rb._require_directory(
            archive_root, "rootfix recovery archive root"
        )
        archive_info = rb._lstat(archive)
        if archive_info is None:
            return None
        rb._require_directory(
            archive, "rootfix bundle recovery archive"
        )
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(str(error)) from error
    return archive


def _process_record_payload(
    status: dict[str, Any],
    attempt_id: str,
    phase: str,
    pid: int,
    pgid: int,
    command: list[str],
    *,
    proc_start: str | None = None,
    boot_id: str | None = None,
) -> dict[str, Any]:
    if proc_start is None:
        proc_start = rb._proc_start_token(pid)
    if boot_id is None:
        boot_id = rb._boot_id()
    if not proc_start or not boot_id:
        raise RootfixError(
            "rootfix child process identity cannot be established"
        )
    return {
        "schema": PROCESS_SCHEMA,
        "exception_id": EXCEPTION_ID,
        "bundle_id": status["bundle_id"],
        "attempt_id": attempt_id,
        "phase": phase,
        "pid": pid,
        "pgid": pgid,
        "proc_start": proc_start,
        "boot_id": boot_id,
        "command_sha256": hashlib.sha256(
            rb.canonical_json_bytes(command)
        ).hexdigest(),
        "started_ns": str(time.time_ns()),
    }


def _validate_process_record_value(
    record: Any,
    status: dict[str, Any],
    attempt_id: str,
    phase: str,
    command: list[str] | None = None,
) -> dict[str, Any]:
    fields = frozenset(
        (
            "schema",
            "exception_id",
            "bundle_id",
            "attempt_id",
            "phase",
            "pid",
            "pgid",
            "proc_start",
            "boot_id",
            "command_sha256",
            "started_ns",
        )
    )
    if not isinstance(record, dict) or frozenset(record) != fields:
        raise RootfixError("rootfix child process record fields are invalid")
    bindings = {
        "schema": PROCESS_SCHEMA,
        "exception_id": EXCEPTION_ID,
        "bundle_id": status["bundle_id"],
        "attempt_id": attempt_id,
        "phase": phase,
    }
    for field, expected in bindings.items():
        if record.get(field) != expected:
            raise RootfixError(
                f"rootfix child process record {field} binding failed"
            )
    pid = record.get("pid")
    pgid = record.get("pgid")
    if (
        isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid <= 0
        or isinstance(pgid, bool)
        or not isinstance(pgid, int)
        or pgid != pid
    ):
        raise RootfixError("rootfix child process pid/pgid is invalid")
    for field in ("proc_start", "boot_id", "started_ns"):
        value = record.get(field)
        if not isinstance(value, str) or not value:
            raise RootfixError(
                f"rootfix child process {field} is invalid"
            )
    if not record["started_ns"].isdigit():
        raise RootfixError("rootfix child process timestamp is invalid")
    digest = record.get("command_sha256")
    if (
        not isinstance(digest, str)
        or re.fullmatch(r"[0-9a-f]{64}", digest) is None
    ):
        raise RootfixError("rootfix child process command digest is invalid")
    if (
        command is not None
        and digest
        != hashlib.sha256(rb.canonical_json_bytes(command)).hexdigest()
    ):
        raise RootfixError("rootfix child process command binding failed")
    return record


def _process_group_exists(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def _process_record_live(record: dict[str, Any]) -> bool:
    pgid = record["pgid"]
    if not _process_group_exists(pgid):
        return False
    current_boot = rb._boot_id()
    if current_boot and current_boot != record["boot_id"]:
        raise RootfixError(
            "live process group conflicts with a different boot identity"
        )
    current_start = rb._proc_start_token(record["pid"])
    if current_start is not None and current_start != record["proc_start"]:
        raise RootfixError(
            "live process group conflicts with a reused process identity"
        )
    return True


def _terminate_surviving_process_group(
    record: dict[str, Any],
) -> None:
    """Kill only the exact recorded group, never a PID-reused successor."""

    pgid = record["pgid"]
    if not _process_group_exists(pgid):
        return
    current_boot = rb._boot_id()
    if not current_boot or current_boot != record["boot_id"]:
        raise RootfixError(
            "surviving process group boot identity cannot be proven"
        )
    current_start = rb._proc_start_token(record["pid"])
    if current_start is not None and current_start != record["proc_start"]:
        raise RootfixError(
            "surviving process group PID was reused; refusing to signal"
        )
    if current_start is None:
        try:
            os.kill(record["pid"], 0)
        except ProcessLookupError:
            pass
        except PermissionError as error:
            raise RootfixError(
                "surviving process group PID identity cannot be proven"
            ) from error
        else:
            raise RootfixError(
                "surviving process group PID identity cannot be proven"
            )
    try:
        os.killpg(pgid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except PermissionError as error:
        raise RootfixError(
            "surviving rootfix process group cannot be signalled"
        ) from error
    deadline = time.monotonic() + 5
    while (
        _process_group_exists(pgid)
        and time.monotonic() < deadline
    ):
        time.sleep(0.05)
    if _process_group_exists(pgid):
        raise RootfixError(
            "rootfix child process group survived completion"
        )


def _load_stage_process_records(
    stage: Path | DirectoryHandle,
    status: dict[str, Any],
    attempt_id: str,
) -> dict[str, dict[str, Any]]:
    owned = not isinstance(stage, DirectoryHandle)
    handle = (
        _open_directory_path(Path(stage), "rootfix staging")
        if owned
        else stage
    )
    assert isinstance(handle, DirectoryHandle)
    result: dict[str, dict[str, Any]] = {}
    try:
        for phase, name in PROCESS_RECORD_NAMES.items():
            try:
                info = os.stat(
                    name, dir_fd=handle.fd, follow_symlinks=False
                )
            except FileNotFoundError:
                continue
            snapshot = _read_regular_at(
                handle,
                name,
                "rootfix child process record",
                expected=info,
                max_bytes=MAX_ROOT_ATOMIC_BYTES,
            )
            record = _canonical_snapshot_object(
                snapshot.data, "rootfix child process record"
            )
            result[phase] = _validate_process_record_value(
                record,
                status,
                attempt_id,
                phase,
            )
        _validate_directory_handle(handle, label="rootfix staging")
        return result
    finally:
        if owned:
            handle.close()


def _require_no_live_stage_processes(
    stage: Path | DirectoryHandle,
    status: dict[str, Any],
    attempt_id: str,
) -> None:
    for phase, record in _load_stage_process_records(
        stage, status, attempt_id
    ).items():
        if _process_record_live(record):
            raise StaleRootfixError(
                f"live rootfix {phase} process group may not be recovered"
            )


def _child_release_wrapper() -> str:
    return (
        "import os\n"
        "import sys\n"
        "fd = int(sys.argv[1])\n"
        "try:\n"
        "    release = os.read(fd, 1)\n"
        "finally:\n"
        "    os.close(fd)\n"
        "if release != b'R':\n"
        "    os._exit(125)\n"
        "os.execvpe(sys.argv[2], sys.argv[2:], os.environ)\n"
    )


def _run_process(
    command: list[str],
    cwd: Path,
    output: Path,
    environment: dict[str, str],
    *,
    stdin_path: Path | None = None,
    stdin_bytes: bytes | None = None,
    stage: Path | DirectoryHandle | None = None,
    status: dict[str, Any] | None = None,
    attempt_id: str | None = None,
    phase: str | None = None,
    evidence_command: list[str] | None = None,
    output_seals: dict[str, FileSnapshot] | None = None,
    deferred_signals: list[int] | None = None,
    after_snapshot: Any = None,
) -> tuple[int, int | None]:
    process_binding = (stage, status, attempt_id, phase)
    if any(item is not None for item in process_binding) and any(
        item is None for item in process_binding
    ):
        raise RootfixError("rootfix process binding is incomplete")
    if phase is not None and phase not in PROCESS_RECORD_NAMES:
        raise RootfixError(f"rootfix process phase is invalid: {phase}")
    interrupted: list[int] = []
    deferred: list[int] = []
    interrupted_at: list[float] = []
    original_forwarded = [False]
    terminal_reached = [False]
    parent_pid = os.getpid()

    def child_setup() -> None:
        libc = ctypes.CDLL(None, use_errno=True)
        prctl = getattr(libc, "prctl", None)
        if prctl is not None:
            prctl(1, signal.SIGKILL, 0, 0, 0)  # PR_SET_PDEATHSIG
        if os.getppid() != parent_pid:
            os.kill(os.getpid(), signal.SIGKILL)
        os.setsid()

    output_flags = (
        os.O_RDWR
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    output_fd = os.open(output, output_flags, 0o600)
    output_snapshot: FileSnapshot | None = None
    return_code: int | None = None
    input_stream = None
    try:
        if stdin_path is not None and stdin_bytes is not None:
            raise RootfixError(
                "rootfix process input has conflicting sources"
            )
        input_data = stdin_bytes
        if stdin_path is not None:
            input_data = _read_regular_snapshot(
                stdin_path, "rootfix process input"
            ).data
        if input_data is not None:
            if not isinstance(input_data, bytes):
                raise RootfixError("rootfix process input must be bytes")
            input_stream = tempfile.TemporaryFile(mode="w+b")
            input_stream.write(input_data)
            input_stream.flush()
            input_stream.seek(0)
        with os.fdopen(output_fd, "w+b") as stream:
            output_fd = -1
            process: subprocess.Popen[Any] | None = None
            process_identity: dict[str, Any] | None = None
            previous: dict[int, Any] = {}
            release_read = -1
            release_write = -1
            released = [False]

            def signal_group(signum: int) -> None:
                if process is None:
                    return
                try:
                    os.killpg(process.pid, signum)
                except ProcessLookupError:
                    return
                except PermissionError as error:
                    if process.poll() is None:
                        raise RootfixError(
                            "rootfix child process group cannot be signalled"
                        ) from error

            def handle(signum: int, _frame: Any) -> None:
                if terminal_reached[0]:
                    if not interrupted and not deferred:
                        deferred.append(signum)
                    return
                if not interrupted:
                    interrupted.append(signum)
                    interrupted_at.append(time.monotonic())
                    # SIGINT lets Python TemporaryDirectory contexts in any
                    # descendant of the profile process tree unwind.  Keep
                    # the initiating signal separately for evidence and send
                    # it only as the next escalation if cleanup stalls.
                    graceful_signal = signal.SIGINT
                    original_forwarded[0] = signum == graceful_signal
                    if released[0]:
                        signal_group(graceful_signal)

            try:
                for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
                    try:
                        previous[signum] = signal.signal(signum, handle)
                    except ValueError:
                        previous.clear()
                        break
                release_read, release_write = os.pipe()
                wrapper_command = [
                    sys.executable,
                    "-c",
                    _child_release_wrapper(),
                    str(release_read),
                    *command,
                ]
                process = subprocess.Popen(
                    wrapper_command,
                    cwd=cwd,
                    stdin=(
                        input_stream
                        if input_stream is not None
                        else subprocess.DEVNULL
                    ),
                    stdout=stream,
                    stderr=subprocess.STDOUT,
                    env=environment,
                    preexec_fn=child_setup,
                    pass_fds=(release_read,),
                )
                os.close(release_read)
                release_read = -1
                pre_release_interrupted = False
                try:
                    pgid = os.getpgid(process.pid)
                    proc_start = rb._proc_start_token(process.pid)
                    boot_id = rb._boot_id()
                    if (
                        pgid != process.pid
                        or not proc_start
                        or not boot_id
                    ):
                        raise RootfixError(
                            "rootfix child process identity "
                            "cannot be established"
                        )
                    process_identity = {
                        "pid": process.pid,
                        "pgid": pgid,
                        "proc_start": proc_start,
                        "boot_id": boot_id,
                    }
                    if stage is not None:
                        assert status is not None
                        assert attempt_id is not None
                        assert phase is not None
                        stage_owned = not isinstance(stage, DirectoryHandle)
                        stage_handle = (
                            _open_directory_path(
                                Path(stage), "rootfix staging"
                            )
                            if stage_owned
                            else stage
                        )
                        assert isinstance(stage_handle, DirectoryHandle)
                        try:
                            record = _process_record_payload(
                                status,
                                attempt_id,
                                phase,
                                process.pid,
                                pgid,
                                (
                                    evidence_command
                                    if evidence_command is not None
                                    else command
                                ),
                                proc_start=proc_start,
                                boot_id=boot_id,
                            )
                            _atomic_write_once_at(
                                stage_handle,
                                PROCESS_RECORD_NAMES[phase],
                                rb.canonical_json_bytes(record),
                            )
                            _validate_directory_handle(
                                stage_handle,
                                label="rootfix staging",
                            )
                        finally:
                            if stage_owned:
                                stage_handle.close()
                    try:
                        os.write(release_write, b"R")
                        released[0] = True
                    except BrokenPipeError:
                        if not interrupted:
                            raise
                        pre_release_interrupted = True
                except BaseException:
                    if interrupted:
                        pre_release_interrupted = True
                    try:
                        signal_group(signal.SIGKILL)
                    except RootfixError:
                        try:
                            process.kill()
                        except ProcessLookupError:
                            pass
                    process.wait()
                    if not pre_release_interrupted:
                        raise
                finally:
                    os.close(release_write)
                    release_write = -1
                if pre_release_interrupted:
                    return_code = process.wait()
                    terminal_reached[0] = True
                else:
                    if interrupted:
                        signal_group(signal.SIGINT)
                    while True:
                        try:
                            return_code = process.wait(timeout=0.2)
                            terminal_reached[0] = True
                            break
                        except subprocess.TimeoutExpired:
                            elapsed = (
                                time.monotonic() - interrupted_at[0]
                                if interrupted_at
                                else 0
                            )
                            if (
                                interrupted
                                and elapsed > 3
                                and not original_forwarded[0]
                            ):
                                signal_group(interrupted[0])
                                original_forwarded[0] = True
                            if interrupted_at and elapsed > 5:
                                signal_group(signal.SIGKILL)
                if process_identity is None:
                    raise RootfixError(
                        "rootfix child process identity was not retained"
                    )
                _terminate_surviving_process_group(process_identity)
            finally:
                if release_read >= 0:
                    os.close(release_read)
                if release_write >= 0:
                    os.close(release_write)
                handoff_error: BaseException | None = None
                try:
                    output_snapshot = _snapshot_writer_stream(
                        output,
                        stream,
                        f"rootfix {phase or 'child'} raw log",
                    )
                    if output_seals is not None:
                        if output.name in output_seals:
                            raise RootfixError(
                                "duplicate rootfix raw-log writer seal"
                            )
                        output_seals[output.name] = output_snapshot
                    if after_snapshot is not None:
                        if return_code is None:
                            raise RootfixError(
                                "rootfix child terminal is unavailable "
                                "at snapshot handoff"
                            )
                        normalized_return = (
                            128 + interrupted[0]
                            if interrupted
                            else (
                                128 + abs(return_code)
                                if return_code < 0
                                else return_code
                            )
                        )
                        after_snapshot(
                            normalized_return,
                            interrupted[0] if interrupted else None,
                        )
                except BaseException as error:
                    handoff_error = error
                finally:
                    try:
                        for signum, handler in previous.items():
                            signal.signal(signum, handler)
                    except BaseException as error:
                        if handoff_error is None:
                            handoff_error = error
                if deferred_signals is not None and deferred:
                    deferred_signals.append(deferred[0])
                if deferred and handoff_error is not None:
                    raise RootfixSignalInterrupt(deferred[0]) from None
                if handoff_error is not None:
                    raise handoff_error
    finally:
        if input_stream is not None:
            input_stream.close()
        if output_fd >= 0:
            os.close(output_fd)
    if interrupted:
        return_code = 128 + interrupted[0]
    elif return_code < 0:
        return_code = 128 + abs(return_code)
    if output_snapshot is None:
        raise RootfixError("rootfix child raw-log writer seal is missing")
    return return_code, interrupted[0] if interrupted else None


def _artifact_snapshot_handle(
    root: DirectoryHandle,
    expected_file_seals: dict[str, FileSnapshot] | None = None,
) -> tuple[list[str], list[dict[str, Any]], dict[str, bytes]]:
    directories: list[str] = []
    records: list[dict[str, Any]] = []
    blobs: dict[str, bytes] = {}
    opened_children: list[DirectoryHandle] = []
    directory_generations: list[
        tuple[DirectoryHandle, tuple[int, int, int, int, int]]
    ] = []
    file_generations: list[
        tuple[DirectoryHandle, str, FileSnapshot]
    ] = []

    def walk(current: DirectoryHandle, prefix: Path) -> None:
        generation = _directory_generation(
            current, label="rootfix artifact directory"
        )
        directory_generations.append((current, generation))
        try:
            with os.scandir(current.fd) as stream:
                entries = sorted(
                    (
                        (entry.name, entry.stat(follow_symlinks=False))
                        for entry in stream
                    ),
                    key=lambda item: item[0],
                )
        except OSError as error:
            raise RootfixError(
                "rootfix artifact tree cannot be fully enumerated"
            ) from error
        child_directories: list[tuple[str, os.stat_result]] = []
        child_files: list[tuple[str, os.stat_result]] = []
        for name, info in entries:
            if stat.S_ISLNK(info.st_mode):
                raise RootfixError(
                    f"unsafe rootfix artifact symlink: {current.path / name}"
                )
            if stat.S_ISDIR(info.st_mode):
                child_directories.append((name, info))
            elif stat.S_ISREG(info.st_mode):
                child_files.append((name, info))
            else:
                raise RootfixError(
                    f"unsafe rootfix artifact object: {current.path / name}"
                )

        for name, _ in child_directories:
            directories.append((prefix / name).as_posix())
        for name, info in child_files:
            snapshot = _read_regular_at(
                current,
                name,
                "rootfix artifact",
                expected=info,
            )
            relative = (prefix / name).as_posix()
            expected_seal = (
                expected_file_seals.get(relative)
                if expected_file_seals is not None
                else None
            )
            if expected_seal is not None and (
                (snapshot.dev, snapshot.ino)
                != (expected_seal.dev, expected_seal.ino)
                or snapshot.size != expected_seal.size
                or snapshot.sha256 != expected_seal.sha256
                or snapshot.data != expected_seal.data
                or snapshot.mtime_ns != expected_seal.mtime_ns
                or snapshot.ctime_ns != expected_seal.ctime_ns
            ):
                raise RootfixError(
                    f"rootfix artifact differs from its writer seal: {relative}"
                )
            records.append(
                {
                    "path": relative,
                    "sha256": snapshot.sha256,
                    "size": snapshot.size,
                    "mtime_ns": str(snapshot.mtime_ns),
                    "ctime_ns": str(snapshot.ctime_ns),
                }
            )
            blobs[relative] = snapshot.data
            file_generations.append((current, name, snapshot))
        for name, info in child_directories:
            child = _open_child_directory(
                current,
                name,
                "rootfix artifact directory",
            )
            opened_children.append(child)
            if (child.dev, child.ino) != _identity(info):
                raise RootfixError(
                    f"rootfix artifact directory changed: {child.path}"
                )
            walk(child, prefix / name)

    try:
        walk(root, Path())
        for parent, name, snapshot in file_generations:
            try:
                info = os.stat(
                    name,
                    dir_fd=parent.fd,
                    follow_symlinks=False,
                )
            except OSError as error:
                raise RootfixError(
                    f"rootfix artifact changed after reading: "
                    f"{parent.path / name}"
                ) from error
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_nlink != 1
                or _content_identity(info)
                != (
                    snapshot.dev,
                    snapshot.ino,
                    snapshot.size,
                    snapshot.mtime_ns,
                    snapshot.ctime_ns,
                )
            ):
                raise RootfixError(
                    f"rootfix artifact changed after reading: "
                    f"{parent.path / name}"
                )
        for directory, generation in reversed(directory_generations):
            _require_directory_generation(
                directory,
                generation,
                label="rootfix artifact directory",
            )
        if expected_file_seals is not None and (
            set(expected_file_seals) - set(blobs)
        ):
            raise RootfixError("rootfix writer-sealed artifact is missing")
        return directories, records, blobs
    finally:
        for child in reversed(opened_children):
            child.close()


def _artifact_snapshot(
    root: Path | DirectoryHandle,
    expected_file_seals: dict[str, FileSnapshot] | None = None,
) -> tuple[list[str], list[dict[str, Any]], dict[str, bytes]]:
    if isinstance(root, DirectoryHandle):
        return _artifact_snapshot_handle(root, expected_file_seals)
    handle = _open_directory_path(root, "rootfix artifact root")
    try:
        return _artifact_snapshot_handle(handle, expected_file_seals)
    finally:
        handle.close()


def _artifact_inventory(
    root: Path | DirectoryHandle,
) -> tuple[list[str], list[dict[str, Any]]]:
    directories, records, _ = _artifact_snapshot(root)
    return directories, records


def _inventory_digest(
    directories: list[str],
    records: list[dict[str, Any]],
) -> str:
    return hashlib.sha256(
        rb.canonical_json_bytes(
            {"directories": directories, "files": records}
        )
    ).hexdigest()


def _attempt_digest(path: Path | DirectoryHandle) -> str:
    directories, records = _artifact_inventory(path)
    return _inventory_digest(directories, records)


def _canonical_snapshot_object(data: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(data.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RootfixError(f"{label} is not valid UTF-8 JSON") from error
    if not isinstance(value, dict):
        raise RootfixError(f"{label} must be a JSON object")
    if rb.canonical_json_bytes(value) != data:
        raise RootfixError(f"{label} is not canonical JSON")
    return value


def _profile_metadata_snapshot(
    data: bytes,
    label: str = "code profile metadata",
) -> dict[str, Any]:
    """Parse the retained verifier's deterministic JSON without ambiguity."""

    class DuplicateKeyError(ValueError):
        pass

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise DuplicateKeyError(key)
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise ValueError(value)

    try:
        value = json.loads(
            data.decode("utf-8", errors="strict"),
            object_pairs_hook=unique_object,
            parse_constant=reject_constant,
        )
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        DuplicateKeyError,
        ValueError,
    ) as error:
        raise RootfixError(
            f"{label} is not unambiguous strict UTF-8 JSON"
        ) from error
    if not isinstance(value, dict):
        raise RootfixError(f"{label} must be a JSON object")
    rendered = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    if data != rendered:
        raise RootfixError(
            f"{label} does not use the trusted verifier serialization"
        )
    return value


def _validate_profile_metadata_value(
    metadata: Any,
    status: dict[str, Any],
    *,
    run_path: Path | None = None,
    candidate_top: Path | None = None,
    run_files: dict[str, bytes] | None = None,
    expected_status: str = "pass",
) -> dict[str, Any]:
    if not isinstance(metadata, dict):
        raise RootfixError("code profile metadata must be a JSON object")
    expected_fields = frozenset(
        (
            "schema_version",
            "verification_contract",
            "run_id",
            "status",
            "profile",
            "scope",
            "base",
            "head",
            "diff_hash",
            "diff_sha256",
            "glossary_sha256",
            "routing_sha256",
            "control_plane_sha256",
            "risk_cpp_i18n",
            "risk_cjk_runtime",
            "risk_zh_test_runtime",
            "risk_message_overlay",
            "runtime_mode",
            "phases",
            "artifacts",
            "worktree",
            "started_at",
            "completed_at",
            "failures",
        )
    )
    if frozenset(metadata) != expected_fields:
        raise RootfixError("code profile metadata fields are incomplete")
    if expected_status not in ("pass", "fail", "interrupted"):
        raise RootfixError("expected code profile status is invalid")
    failures = metadata.get("failures")
    if (
        type(metadata.get("schema_version")) is not int
        or metadata["schema_version"] != 3
        or type(failures) is not int
        or (expected_status == "pass" and failures != 0)
        or (expected_status != "pass" and failures < 1)
    ):
        raise RootfixError(
            "code profile metadata integer fields are invalid"
        )
    for field in (
        "risk_cpp_i18n",
        "risk_cjk_runtime",
        "risk_zh_test_runtime",
        "risk_message_overlay",
    ):
        if type(metadata.get(field)) is not bool:
            raise RootfixError(
                f"code profile metadata {field} type is invalid"
            )
    expected = {
        "verification_contract": rb.VERIFICATION_CONTRACT,
        "profile": "code",
        "scope": "full",
        "base": status["target_head"],
        "head": status["candidate_head"],
        "diff_sha256": status["diff_sha256"],
        "glossary_sha256": status["glossary_sha256"],
        "routing_sha256": None,
        "control_plane_sha256": None,
        "risk_cpp_i18n": False,
        "risk_cjk_runtime": False,
        "risk_zh_test_runtime": False,
        "risk_message_overlay": False,
        "runtime_mode": "none",
        "status": expected_status,
    }
    for field, value in expected.items():
        if metadata.get(field) != value:
            raise RootfixError(f"code profile metadata {field} binding failed")
    run_id = metadata.get("run_id")
    if (
        not isinstance(run_id, str)
        or rb.RUN_ID_RE.fullmatch(run_id) is None
        or (run_path is not None and run_path.name != run_id)
    ):
        raise RootfixError("code profile metadata run_id binding failed")
    diff_hash = metadata.get("diff_hash")
    expected_diff_hash = status.get("_rootfix_profile_diff_hash")
    if (
        not isinstance(expected_diff_hash, str)
        or re.fullmatch(r"[0-9a-f]{40,64}", expected_diff_hash) is None
        or diff_hash != expected_diff_hash
    ):
        raise RootfixError(
            "code profile metadata diff_hash binding failed"
        )
    timestamps: dict[str, datetime] = {}
    for field in ("started_at", "completed_at"):
        value = metadata.get(field)
        if not isinstance(value, str) or not value:
            raise RootfixError(f"code profile metadata {field} is invalid")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as error:
            raise RootfixError(
                f"code profile metadata {field} is invalid"
            ) from error
        if parsed.tzinfo is None:
            raise RootfixError(
                f"code profile metadata {field} lacks a timezone"
            )
        timestamps[field] = parsed
    if timestamps["completed_at"] < timestamps["started_at"]:
        raise RootfixError(
            "code profile metadata completion precedes its start"
        )
    if candidate_top is not None:
        try:
            expected_worktree = os.fspath(candidate_top.resolve(strict=True))
        except OSError as error:
            raise RootfixError("candidate worktree cannot be resolved") from error
        if metadata.get("worktree") != expected_worktree:
            raise RootfixError("code profile metadata worktree binding failed")
    elif (
        not isinstance(metadata.get("worktree"), str)
        or not Path(metadata["worktree"]).is_absolute()
    ):
        raise RootfixError("code profile metadata worktree is invalid")

    if run_files is None and run_path is not None:
        run_directories, _, run_files = _artifact_snapshot(run_path)
        if run_directories:
            raise RootfixError(
                "code profile run contains unexpected directories"
            )

    try:
        contract_bytes = _TRUSTED_SOURCE_BLOBS.get(
            PROFILE_CONTRACT_PATH
        )
        if contract_bytes is None:
            raise RootfixError(
                "trusted code-profile contract snapshot is unavailable"
            )
        contract = rb._parse_contract(
            contract_bytes, "rootfix code-profile contract"
        )
    except rb.ReviewBundleError as error:
        raise RootfixError(str(error)) from error
    if contract.get("verification_contract") != rb.VERIFICATION_CONTRACT:
        raise RootfixError("rootfix code-profile contract version is invalid")
    always_phases = [
        phase["id"]
        for phase in contract["phase_plan"]
        if phase["when"] == "always"
    ]
    expected_phase_ids = [
        "policy-sync",
        "source-db-static",
        "code-static",
        "message-overlay-static",
    ]
    if always_phases != [
        "policy-sync",
        "source-db-static",
        "review-static",
        "message-overlay-static",
    ]:
        raise RootfixError("trusted production phase contract is unexpected")
    phases = metadata.get("phases")
    if (
        not isinstance(phases, list)
        or len(phases) > len(expected_phase_ids)
        or (
            expected_status == "pass"
            and len(phases) != len(expected_phase_ids)
        )
    ):
        raise RootfixError("code profile metadata phase plan is invalid")
    for actual, phase_id in zip(phases, expected_phase_ids):
        phase_status = (
            actual.get("status") if isinstance(actual, dict) else None
        )
        phase_exit = (
            actual.get("exit_code") if isinstance(actual, dict) else None
        )
        if (
            not isinstance(actual, dict)
            or frozenset(actual)
            != frozenset(("id", "required", "status", "exit_code"))
            or actual.get("id") != phase_id
            or type(actual.get("required")) is not bool
            or actual["required"] is not True
            or phase_status not in ("pass", "fail")
            or type(phase_exit) is not int
            or (phase_status == "pass" and phase_exit != 0)
            or (phase_status == "fail" and phase_exit <= 0)
            or (
                expected_status == "pass"
                and (phase_status != "pass" or phase_exit != 0)
            )
        ):
            raise RootfixError(
                f"code profile metadata phase binding failed: {phase_id}"
            )

    artifacts = metadata.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise RootfixError("code profile metadata artifacts are missing")
    seen: set[str] = set()
    artifact_paths: list[str] = []
    for artifact in artifacts:
        if (
            not isinstance(artifact, dict)
            or frozenset(artifact) != frozenset(("path", "size", "sha256"))
        ):
            raise RootfixError("code profile metadata artifact fields are invalid")
        try:
            relative = rb._safe_relative_path(
                artifact.get("path"), "rootfix profile artifact"
            )
            digest = rb._validate_sha256(
                artifact.get("sha256"),
                f"rootfix profile artifact {relative}",
            )
        except rb.ReviewBundleError as error:
            raise RootfixError(str(error)) from error
        size = artifact.get("size")
        if (
            relative in seen
            or isinstance(size, bool)
            or not isinstance(size, int)
            or size < 0
        ):
            raise RootfixError(
                f"code profile metadata artifact is invalid: {relative}"
            )
        seen.add(relative)
        artifact_paths.append(relative)
        if run_files is not None:
            data = run_files.get(relative)
            if (
                data is None
                or len(data) != size
                or hashlib.sha256(data).hexdigest() != digest
            ):
                raise RootfixError(
                    f"code profile artifact binding failed: {relative}"
                )
    artifact_inventory_valid = (
        artifact_paths == ["verify.log", "item-name-inventory.json"]
        if expected_status == "pass"
        else artifact_paths
        in (
            ["verify.log"],
            ["verify.log", "item-name-inventory.json"],
        )
    )
    if not artifact_inventory_valid:
        raise RootfixError(
            "code profile metadata artifact inventory is incomplete"
        )
    if run_files is not None:
        if set(run_files) != seen | {"metadata.json", "phases.tsv"}:
            raise RootfixError(
                "code profile output contains unknown or missing objects"
            )
        expected_tsv = "".join(
            f"{phase['id']}\t1\t{phase['status']}\t"
            f"{phase['exit_code']}\n"
            for phase in phases
        ).encode("utf-8")
        if run_files["phases.tsv"] != expected_tsv:
            raise RootfixError("code profile phases.tsv binding failed")
    return metadata


def _validate_profile_wrapper(
    data: bytes,
    metadata: dict[str, Any],
    expected_run_path: Path,
) -> None:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RootfixError(
            "code profile wrapper is not strict UTF-8"
        ) from error
    lines = text.splitlines()
    run_id = metadata["run_id"]
    expected_prefix = [
        f"run_id={run_id}",
        "profile=code",
        f"status={metadata['status']}",
        f"failures={metadata['failures']}",
        f"started_at={metadata['started_at']}",
        f"completed_at={metadata['completed_at']}",
    ]
    if (
        not text.endswith("\n")
        or len(lines) != 10
        or lines[:6] != expected_prefix
        or lines[8]
        != f"Summary: {metadata['failures']} blocking failure(s)"
        or lines[9] != "=== verify_zh.sh complete ==="
    ):
        raise RootfixError("code profile wrapper content is invalid")
    if not expected_run_path.is_absolute():
        raise RootfixError("code profile wrapper output root is not absolute")
    for line, filename in (
        (lines[6], "verify.log"),
        (lines[7], "metadata.json"),
    ):
        field = "report" if filename == "verify.log" else "metadata"
        expected = f"{field}={expected_run_path / filename}"
        if line != expected:
            raise RootfixError("code profile wrapper path binding failed")


def _validate_profile_report(
    data: bytes,
    metadata: dict[str, Any],
) -> None:
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RootfixError(
            "code profile report is not strict UTF-8"
        ) from error
    expected_header = (
        f"=== verify_zh.sh --profile code @ "
        f"{metadata['started_at']} ===\n"
        f"Run ID: {metadata['run_id']}\n"
        "Scope: full\n"
        "Risk: cpp_i18n=0 cjk_runtime=0 zh_test_runtime=0 "
        "message_overlay=0 explicit_full=0\n"
        f"Base: {metadata['base']}\n"
        f"Head: {metadata['head']}\n"
        f"Diff hash: {metadata['diff_hash']}\n"
        f"Diff SHA-256: {metadata['diff_sha256']}\n"
        f"Glossary SHA-256: {metadata['glossary_sha256']}\n"
        "\n"
    )
    if not text.startswith(expected_header):
        raise RootfixError("code profile report header binding failed")

    lines = text.splitlines()
    structured_prefixes = (
        "Run ID: ",
        "Scope: ",
        "Risk: ",
        "Base: ",
        "Head: ",
        "Diff hash: ",
        "Diff SHA-256: ",
        "Glossary SHA-256: ",
    )
    for prefix in structured_prefixes:
        if sum(line.startswith(prefix) for line in lines) != 1:
            raise RootfixError(
                "code profile report structured header is ambiguous"
            )

    phase_headers = [
        f"=== {label} ===" for _, label in PROFILE_PHASE_LABELS
    ]
    header_indexes: list[int] = []
    for header in phase_headers:
        indexes = [
            index for index, line in enumerate(lines) if line == header
        ]
        if len(indexes) > 1:
            raise RootfixError(
                "code profile report phase header is ambiguous"
            )
        if indexes:
            header_indexes.append(indexes[0])
        else:
            break
    if any(
        header in lines
        for header in phase_headers[len(header_indexes):]
    ):
        raise RootfixError("code profile report phase order is invalid")

    phases = metadata["phases"]
    if (
        len(header_indexes) < len(phases)
        or len(header_indexes) > len(phases) + 1
    ):
        raise RootfixError(
            "code profile report phase inventory is inconsistent"
        )
    for index, phase in enumerate(phases):
        if phase["id"] != PROFILE_PHASE_LABELS[index][0]:
            raise RootfixError(
                "code profile report phase metadata is inconsistent"
            )
        segment_end = (
            header_indexes[index + 1]
            if index + 1 < len(header_indexes)
            else len(lines)
        )
        result_lines = [
            line
            for line in lines[header_indexes[index] + 1:segment_end]
            if line == "RESULT: PASS"
            or re.fullmatch(r"RESULT: FAIL \(exit [1-9][0-9]*\)", line)
        ]
        expected_result = (
            "RESULT: PASS"
            if phase["status"] == "pass"
            else f"RESULT: FAIL (exit {phase['exit_code']})"
        )
        if result_lines != [expected_result]:
            raise RootfixError(
                f"code profile report phase result binding failed: "
                f"{phase['id']}"
            )
    if len(header_indexes) == len(phases) + 1:
        unfinished = lines[header_indexes[-1] + 1:]
        if any(
            line == "RESULT: PASS"
            or re.fullmatch(r"RESULT: FAIL \(exit [1-9][0-9]*\)", line)
            for line in unfinished
        ):
            raise RootfixError(
                "code profile report completed an unrecorded phase"
            )

    summary_lines = [
        index
        for index, line in enumerate(lines)
        if re.fullmatch(r"Summary: [0-9]+ blocking failure\(s\)", line)
    ]
    complete_lines = [
        index
        for index, line in enumerate(lines)
        if line == "=== verify_zh.sh complete ==="
    ]
    expected_summary = (
        f"Summary: {metadata['failures']} blocking failure(s)"
    )
    if metadata["status"] == "pass":
        if (
            summary_lines != [len(lines) - 2]
            or complete_lines != [len(lines) - 1]
            or lines[-2:] != [
                expected_summary,
                "=== verify_zh.sh complete ===",
            ]
            or not text.endswith("\n")
            or len(phases) != len(PROFILE_PHASE_LABELS)
        ):
            raise RootfixError(
                "code profile report terminal summary binding failed"
            )
    elif summary_lines or complete_lines:
        if (
            len(summary_lines) != 1
            or len(complete_lines) != 1
            or complete_lines[0] != summary_lines[0] + 1
            or not text.endswith("\n")
            or len(phases) != len(PROFILE_PHASE_LABELS)
        ):
            raise RootfixError(
                "code profile report terminal summary binding failed"
            )
        summary_match = re.fullmatch(
            r"Summary: ([0-9]+) blocking failure\(s\)",
            lines[summary_lines[0]],
        )
        assert summary_match is not None
        report_failures = int(summary_match.group(1))
        footer = lines[complete_lines[0] + 1:]
        if footer:
            if metadata["status"] != "fail":
                raise RootfixError(
                    "code profile report drift footer status is invalid"
                )
            kinds: list[str] = []
            for line in footer:
                head = re.fullmatch(
                    "ERROR: worktree HEAD changed during verification: "
                    f"{re.escape(metadata['head'])} -> "
                    r"([0-9a-f]{40}|<missing>)",
                    line,
                )
                glossary = re.fullmatch(
                    "ERROR: glossary changed during verification: "
                    f"{re.escape(metadata['glossary_sha256'])} -> "
                    r"([0-9a-f]{64}|<missing>)",
                    line,
                )
                if head is not None and head.group(1) != metadata["head"]:
                    kinds.append("head")
                elif (
                    glossary is not None
                    and glossary.group(1)
                    != metadata["glossary_sha256"]
                ):
                    kinds.append("glossary")
                else:
                    raise RootfixError(
                        "code profile report drift footer binding failed"
                    )
            if (
                kinds not in (["head"], ["glossary"], ["head", "glossary"])
                or metadata["failures"] != report_failures + 1
            ):
                raise RootfixError(
                    "code profile report drift footer binding failed"
                )
        else:
            expected_failures = (
                1 if report_failures == 0 else report_failures
            )
            if metadata["failures"] != expected_failures:
                raise RootfixError(
                    "code profile report terminal summary binding failed"
                )
    if not header_indexes:
        raise RootfixError("code profile report content binding failed")


def _validate_profile_process_log(
    data: bytes,
    metadata: dict[str, Any],
    expected_run_path: Path,
    report: bytes,
) -> None:
    """Bind parent-captured verifier stdout to the retained profile run."""

    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RootfixError(
            "code profile raw log is not strict UTF-8"
        ) from error
    run_id = metadata["run_id"]
    expected = (
        "\n"
        "=== verify-zh --profile code ===\n"
        f"Run ID: {run_id}\n"
        f"Report: {expected_run_path / 'verify.log'}\n"
        f"Metadata: {expected_run_path / 'metadata.json'}\n"
        "Wrapper: "
        f"{expected_run_path.parent / f'verify-code-{run_id}.log'}\n"
        f"Failures: {metadata['failures']}\n"
        "\n"
    )
    report_complete = b"\n=== verify_zh.sh complete ===\n" in report
    requires_complete = (
        metadata["status"] == "pass"
        or (metadata["status"] == "fail" and report_complete)
    )
    if (
        (requires_complete and text != expected)
        or (not requires_complete and not expected.startswith(text))
    ):
        raise RootfixError(
            "code profile raw log semantic binding failed"
        )


def _profile_metadata(
    output_root: Path,
    status: dict[str, Any],
    candidate_top: Path | None = None,
    expected_status: str = "pass",
) -> tuple[str, dict[str, Any]]:
    _, _, output_files = _artifact_snapshot(output_root)
    matches = sorted(
        relative
        for relative in output_files
        if (
            len(Path(relative).parts) == 2
            and Path(relative).name == "metadata.json"
        )
    )
    if len(matches) != 1:
        raise RootfixError("code profile did not produce exactly one metadata.json")
    relative = matches[0]
    path = output_root / relative
    data = output_files[relative]
    metadata = _profile_metadata_snapshot(data)
    validated = _validate_profile_metadata_value(
        metadata,
        status,
        run_path=path.parent,
        candidate_top=candidate_top,
        run_files={
            Path(name).relative_to(Path(relative).parent).as_posix(): blob
            for name, blob in output_files.items()
            if (
                Path(name) == Path(relative).parent
                or Path(relative).parent in Path(name).parents
            )
        },
        expected_status=expected_status,
    )
    wrapper_name = f"verify-code-{validated['run_id']}.log"
    wrapper = output_files.get(wrapper_name)
    if wrapper is None:
        raise RootfixError("code profile wrapper is missing")
    _validate_profile_wrapper(wrapper, validated, path.parent)
    report_name = (
        Path(relative).parent / "verify.log"
    ).as_posix()
    report = output_files.get(report_name)
    if report is None:
        raise RootfixError("code profile report is missing")
    _validate_profile_report(report, validated)
    return relative, validated


def _attempt_id() -> str:
    return (
        f"attempt-{time.time_ns()}-{os.getpid()}-"
        f"{secrets.token_hex(6)}"
    )


def _completion(
    outcome: str,
    exit_code: int,
    interrupted_signal: int | None = None,
) -> dict[str, Any]:
    return {
        "schema": COMPLETION_SCHEMA,
        "completed": True,
        "outcome": outcome,
        "exit_code": exit_code,
        "interrupted_signal": interrupted_signal,
    }


def _approval_payload(
    status: dict[str, Any],
    candidate_test: dict[str, Any],
    attempts: list[dict[str, str]],
    attempt_id: str,
    attempt_sha256: str,
) -> dict[str, Any]:
    return {
        "schema": APPROVAL_SCHEMA,
        "exception_id": EXCEPTION_ID,
        "base_c": BASE_C,
        "policy_head": status["target_head"],
        "candidate_head": status["candidate_head"],
        "bundle_id": status["bundle_id"],
        "bundle_sha256": status["bundle_sha256"],
        "diff_sha256": status["diff_sha256"],
        "glossary_sha256": status["glossary_sha256"],
        "routing_sha256": status["routing_sha256"],
        "readiness": [
            {
                "reviewer": REVIEWER,
                "sha256": status["readiness_sha256"][REVIEWER],
            }
        ],
        "policy_manifest_sha256": POLICY_MANIFEST_SHA256,
        "candidate_test": candidate_test,
        "attempts": attempts,
        "attempt_id": attempt_id,
        "attempt_sha256": attempt_sha256,
        "verdict": "go",
    }


def _publish_attempt(
    stage: Path | DirectoryHandle,
    attempts: Path | DirectoryHandle,
    attempt_id: str,
    attempt_sha256: str,
) -> tuple[Path, str]:
    owned_stage = not isinstance(stage, DirectoryHandle)
    owned_attempts = not isinstance(attempts, DirectoryHandle)
    attempts_handle = (
        _open_directory_path(Path(attempts), "rootfix attempts")
        if owned_attempts
        else attempts
    )
    assert isinstance(attempts_handle, DirectoryHandle)
    stage_handle = (
        _open_child_directory(
            attempts_handle,
            Path(stage).name,
            "rootfix staging",
        )
        if owned_stage
        else stage
    )
    assert isinstance(stage_handle, DirectoryHandle)
    source_name = stage_handle.path.name
    destination = attempts_handle.path / attempt_id
    try:
        try:
            _atomic_rename_noreplace_at(
                attempts_handle,
                source_name,
                attempts_handle,
                attempt_id,
            )
        except FileExistsError as error:
            raise RootfixError(
                f"rootfix attempt id already exists: {attempt_id}"
            ) from error
        os.fsync(attempts_handle.fd)
        stage_handle.path = destination
        _validate_directory_handle(
            stage_handle,
            parent=attempts_handle,
            name=attempt_id,
            label="published rootfix attempt",
        )
        if _attempt_digest(stage_handle) != attempt_sha256:
            raise RootfixError("rootfix attempt changed during publication")
        return destination, attempt_sha256
    finally:
        if owned_stage:
            stage_handle.close()
        if owned_attempts:
            attempts_handle.close()


def _expected_commands(status: dict[str, Any]) -> dict[str, list[str]]:
    return {
        "candidate_test": [
            "python3",
            f"{status['candidate_head']}:{TEST_PATH}",
        ],
        "code_profile": [
            "bash",
            VERIFIER_PATH,
            "--profile",
            "code",
            "--base",
            status["target_head"],
            "--head",
            status["candidate_head"],
            "--scope",
            "full",
            "--output-dir",
            "profile-output",
        ],
    }


def _write_attempt_artifacts(
    stage: Path | DirectoryHandle,
    commands: dict[str, list[str]],
    metadata_path: str | None,
) -> None:
    stage_path = stage.path if isinstance(stage, DirectoryHandle) else stage
    directories, artifacts = _artifact_inventory(stage)
    data = rb.canonical_json_bytes(
        {
            "schema": ARTIFACT_SCHEMA,
            "profile_metadata": (
                f"profile-output/{metadata_path}"
                if metadata_path is not None
                else None
            ),
            "commands": commands,
            "directories": directories,
            "artifacts": artifacts,
        }
    )
    if isinstance(stage, DirectoryHandle):
        _atomic_write_once_at(stage, "artifacts.json", data)
    else:
        rb.atomic_write_once(stage_path / "artifacts.json", data)


def _candidate_test_wrapper() -> str:
    return (
        "import signal\n"
        "import sys\n"
        "import types\n"
        "def _rootfix_interrupt(_signum, _frame):\n"
        "    raise KeyboardInterrupt\n"
        "for _rootfix_signal in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):\n"
        "    signal.signal(_rootfix_signal, _rootfix_interrupt)\n"
        "p = sys.argv[1]\n"
        "sys.argv = [p]\n"
        "source = sys.stdin.buffer.read()\n"
        "module = types.ModuleType('__main__')\n"
        "module.__file__ = p\n"
        "sys.modules['__main__'] = module\n"
        "exec(compile(source, p, 'exec'), module.__dict__)\n"
    )


def _run_attempt(
    stage: Path | DirectoryHandle,
    candidate_top: Path,
    status: dict[str, Any],
    candidate_test_blob: bytes,
    commands: dict[str, list[str]],
    artifact_seals: dict[str, FileSnapshot] | None = None,
) -> tuple[int, str | None, int | None]:
    if artifact_seals is None:
        artifact_seals = {}
    owned = not isinstance(stage, DirectoryHandle)
    handle = (
        _open_directory_path(Path(stage), "rootfix staging")
        if owned
        else stage
    )
    assert isinstance(handle, DirectoryHandle)
    stage_path = handle.path
    if not stage_path.name.startswith(".staging-"):
        raise RootfixError("rootfix staging name is invalid")
    attempt_id = stage_path.name[len(".staging-"):]
    if not _valid_operation_id(attempt_id):
        raise RootfixError("rootfix staging attempt ID is invalid")
    try:
        environment = rb._trusted_child_environment()
        environment.update(
            {
                "ZH_VERIFY_AUDIT_ROOT": os.fspath(candidate_top),
                "ZH_VERIFY_AUDIT_COMMIT": status["candidate_head"],
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPYCACHEPREFIX": os.fspath(
                    stage_path / ".candidate-pycache"
                ),
                "GIT_NO_REPLACE_OBJECTS": "1",
            }
        )
        python = (
            shutil.which("python3", path=environment["PATH"])
            or "/usr/bin/python3"
        )
        test_log = stage_path / "candidate-test.log"
        _atomic_write_once_at(
            handle, "candidate-test.py", candidate_test_blob
        )
        logical_commands = _expected_commands(status)
        commands["candidate_test"] = logical_commands["candidate_test"]
        candidate_deferred: list[int] = []
        test_rc, test_signal = _run_process(
            [
                python,
                "-c",
                _candidate_test_wrapper(),
                os.fspath(candidate_top / TEST_PATH),
            ],
            candidate_top,
            test_log,
            environment,
            stdin_bytes=candidate_test_blob,
            stage=handle,
            status=status,
            attempt_id=attempt_id,
            phase="candidate_test",
            evidence_command=logical_commands["candidate_test"],
            output_seals=artifact_seals,
            deferred_signals=candidate_deferred,
        )
        if candidate_deferred:
            raise RootfixSignalInterrupt(candidate_deferred[0])
        if test_rc:
            return test_rc, None, test_signal

        verifier_blob = _TRUSTED_SOURCE_BLOBS.get(VERIFIER_PATH)
        if verifier_blob is None or b"\0" in verifier_blob:
            raise RootfixError(
                "trusted verifier source snapshot is unavailable"
            )
        try:
            verifier_source = verifier_blob.decode(
                "utf-8", errors="strict"
            )
        except UnicodeDecodeError as error:
            raise RootfixError(
                "trusted verifier source is not strict UTF-8"
            ) from error
        commands["code_profile"] = logical_commands["code_profile"]
        os.mkdir("profile-output", 0o700, dir_fd=handle.fd)
        os.fsync(handle.fd)
        profile_output = stage_path / "profile-output"
        profile_log = stage_path / "code-profile.log"
        profile_environment = rb._trusted_child_environment()
        profile_environment.update(
            {
                "TERM": "xterm-256color",
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONPYCACHEPREFIX": os.fspath(
                    stage_path / ".profile-pycache"
                ),
                "GIT_NO_REPLACE_OBJECTS": "1",
            }
        )
        profile_command = [
            "bash",
            "-c",
            verifier_source,
            os.fspath(candidate_top / VERIFIER_PATH),
            "--profile",
            "code",
            "--base",
            status["target_head"],
            "--head",
            status["candidate_head"],
            "--scope",
            "full",
            "--output-dir",
            os.fspath(profile_output),
        ]
        profile_terminal: list[
            tuple[str, int, str | None, int | None]
        ] = []
        profile_validation_error: list[BaseException] = []
        profile_deferred: list[int] = []

        def validate_profile_handoff(
            profile_rc: int,
            profile_signal: int | None,
        ) -> None:
            expected_profile_status = (
                "interrupted"
                if profile_signal is not None
                else ("pass" if profile_rc == 0 else "fail")
            )
            try:
                metadata_path, _ = _profile_metadata(
                    profile_output,
                    status,
                    candidate_top,
                    expected_profile_status,
                )
                profile_terminal.append(
                    (
                        expected_profile_status,
                        profile_rc,
                        metadata_path,
                        profile_signal,
                    )
                )
            except BaseException as error:
                profile_validation_error.append(error)

        try:
            profile_rc, profile_signal = _run_process(
                profile_command,
                candidate_top,
                profile_log,
                profile_environment,
                stage=handle,
                status=status,
                attempt_id=attempt_id,
                phase="code_profile",
                evidence_command=logical_commands["code_profile"],
                output_seals=artifact_seals,
                deferred_signals=profile_deferred,
                after_snapshot=validate_profile_handoff,
            )
            if profile_deferred:
                if profile_terminal:
                    raise RootfixEstablishedTerminalInterrupt(
                        profile_deferred[0], profile_terminal[0]
                    )
                raise RootfixSignalInterrupt(profile_deferred[0])
            if profile_validation_error:
                raise profile_validation_error[0]
            if len(profile_terminal) != 1:
                raise RootfixError(
                    "code profile terminal handoff is incomplete"
                )
            terminal = profile_terminal[0]
            return terminal[1], terminal[2], terminal[3]
        except RootfixEstablishedTerminalInterrupt:
            raise
        except RootfixSignalInterrupt as error:
            if profile_terminal:
                raise RootfixEstablishedTerminalInterrupt(
                    error.signum, profile_terminal[0]
                ) from None
            raise
    finally:
        if owned:
            handle.close()


def _validate_attempt(
    path: Path | DirectoryHandle,
    expected_sha256: str | None,
    status: dict[str, Any],
    candidate_top: Path | None = None,
    candidate_blob_sha256: str | None = None,
    expected_artifact_seals: dict[str, FileSnapshot] | None = None,
) -> dict[str, Any]:
    directories, all_records, blobs = _artifact_snapshot(
        path, expected_artifact_seals
    )
    attempt_path = path.path if isinstance(path, DirectoryHandle) else path
    attempt_id = attempt_path.name
    if attempt_id.startswith(".staging-"):
        attempt_id = attempt_id[len(".staging-"):]
    if not _valid_operation_id(attempt_id):
        raise RootfixError("rootfix attempt ID is invalid")
    actual_sha256 = _inventory_digest(directories, all_records)
    if expected_sha256 is not None and actual_sha256 != expected_sha256:
        raise RootfixError("rootfix attempt digest mismatch")
    completion_bytes = blobs.get("completion.json")
    if completion_bytes is None:
        raise RootfixError("rootfix completion marker is missing")
    completion = _canonical_snapshot_object(
        completion_bytes, "rootfix completion marker"
    )
    if frozenset(completion) != frozenset(
        ("schema", "completed", "outcome", "exit_code", "interrupted_signal")
    ):
        raise RootfixError("rootfix completion fields are invalid")
    if (
        completion.get("schema") != COMPLETION_SCHEMA
        or completion.get("completed") is not True
    ):
        raise RootfixError("rootfix completion marker is invalid")
    outcome = completion.get("outcome")
    exit_code = completion.get("exit_code")
    interrupted_signal = completion.get("interrupted_signal")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        raise RootfixError("rootfix completion exit code is invalid")
    if outcome == "pass":
        if exit_code != 0 or interrupted_signal is not None:
            raise RootfixError("passing rootfix completion is inconsistent")
    elif outcome == "fail":
        if exit_code <= 0 or interrupted_signal is not None:
            raise RootfixError("failed rootfix completion is inconsistent")
    elif outcome == "interrupted":
        if (
            isinstance(interrupted_signal, bool)
            or not isinstance(interrupted_signal, int)
            or interrupted_signal not in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
            or exit_code != 128 + interrupted_signal
        ):
            raise RootfixError("interrupted rootfix completion is inconsistent")
    else:
        raise RootfixError("rootfix completion outcome is invalid")

    artifacts_bytes = blobs.get("artifacts.json")
    if artifacts_bytes is None:
        raise RootfixError("rootfix artifact inventory is missing")
    artifacts = _canonical_snapshot_object(
        artifacts_bytes, "rootfix artifact inventory"
    )
    if (
        frozenset(artifacts)
        != frozenset(
            (
                "schema",
                "profile_metadata",
                "commands",
                "directories",
                "artifacts",
            )
        )
        or artifacts.get("schema") != ARTIFACT_SCHEMA
    ):
        raise RootfixError("rootfix artifact schema is invalid")
    expected_commands = _expected_commands(status)
    allowed_commands = (
        {},
        {"candidate_test": expected_commands["candidate_test"]},
        expected_commands,
    )
    commands = artifacts.get("commands")
    if commands not in allowed_commands:
        raise RootfixError("rootfix command record is invalid")
    expected_raw_seals: set[str] = set()
    if "candidate_test" in commands:
        expected_raw_seals.add("candidate-test.log")
    if "code_profile" in commands:
        expected_raw_seals.add("code-profile.log")
    if (
        expected_artifact_seals is not None
        and set(expected_artifact_seals) != expected_raw_seals
    ):
        raise RootfixError(
            "rootfix raw-log writer-seal inventory is incomplete"
        )
    if candidate_blob_sha256 is None:
        candidate_blob_sha256 = status.get(
            "_rootfix_candidate_blob_sha256"
        )
    candidate_input = blobs.get("candidate-test.py")
    if candidate_blob_sha256 is not None:
        try:
            rb._validate_sha256(
                candidate_blob_sha256,
                "rootfix candidate test blob",
            )
        except rb.ReviewBundleError as error:
            raise RootfixError(str(error)) from error
        if (
            candidate_input is not None
            and hashlib.sha256(candidate_input).hexdigest()
            != candidate_blob_sha256
        ):
            raise RootfixError(
                "rootfix candidate-test.py differs from the committed F2 blob"
            )
    expected_process_phases = set(commands)
    actual_process_phases: set[str] = set()
    for process_phase, process_name in PROCESS_RECORD_NAMES.items():
        process_bytes = blobs.get(process_name)
        if process_bytes is None:
            continue
        record = _canonical_snapshot_object(
            process_bytes, "rootfix child process record"
        )
        record = _validate_process_record_value(
            record,
            status,
            attempt_id,
            process_phase,
            expected_commands[process_phase],
        )
        if _process_record_live(record):
            raise RootfixError(
                "published rootfix attempt retains a live process group"
            )
        actual_process_phases.add(process_phase)
    if actual_process_phases != expected_process_phases:
        raise RootfixError(
            "rootfix child process record inventory is incomplete"
        )
    metadata_path = artifacts.get("profile_metadata")
    if outcome == "pass":
        if commands != expected_commands:
            raise RootfixError("passing rootfix attempt omitted a required command")
    if "code_profile" in commands:
        if not isinstance(metadata_path, str):
            raise RootfixError("rootfix profile metadata path is missing")
        metadata_matches = sorted(
            relative
            for relative in blobs
            if (
                len(Path(relative).parts) == 3
                and Path(relative).parts[0] == "profile-output"
                and Path(relative).parts[2] == "metadata.json"
            )
        )
        if metadata_matches != [metadata_path]:
            raise RootfixError("rootfix profile metadata path is invalid")
        metadata_bytes = blobs[metadata_path]
        metadata = _profile_metadata_snapshot(metadata_bytes)
        metadata = _validate_profile_metadata_value(
            metadata,
            status,
            run_path=attempt_path / Path(metadata_path).parent,
            candidate_top=candidate_top,
            run_files={
                Path(relative).relative_to(
                    Path(metadata_path).parent
                ).as_posix(): data
                for relative, data in blobs.items()
                if Path(metadata_path).parent in Path(relative).parents
            },
            expected_status=outcome,
        )
        run_directory = Path(metadata_path).parent
        expected_directories = sorted(
            (
                "profile-output",
                run_directory.as_posix(),
            )
        )
        if directories != expected_directories:
            raise RootfixError(
                "passing rootfix profile directory inventory is not exact"
            )
        run_id = metadata["run_id"]
        expected_profile_files = {
            (run_directory / name).as_posix()
            for name in (
                {"metadata.json", "phases.tsv"}
                | {
                    artifact["path"]
                    for artifact in metadata["artifacts"]
                }
            )
        }
        expected_profile_files.add(
            f"profile-output/verify-code-{run_id}.log"
        )
        actual_profile_files = {
            relative
            for relative in blobs
            if Path(relative).parts[0] == "profile-output"
        }
        if actual_profile_files != expected_profile_files:
            raise RootfixError(
                "rootfix profile file inventory is not exact"
            )
        original_stage = (
            attempt_path.parent / f".staging-{attempt_id}"
        )
        expected_run_path = original_stage / run_directory
        _validate_profile_wrapper(
            blobs[f"profile-output/verify-code-{run_id}.log"],
            metadata,
            expected_run_path,
        )
        report_blob = blobs[(run_directory / "verify.log").as_posix()]
        _validate_profile_report(
            report_blob,
            metadata,
        )
        profile_log = blobs.get("code-profile.log")
        if profile_log is None:
            raise RootfixError("rootfix profile raw log is missing")
        _validate_profile_process_log(
            profile_log,
            metadata,
            expected_run_path,
            report_blob,
        )
    else:
        if metadata_path is not None:
            raise RootfixError(
                "rootfix attempt claims metadata without a profile command"
            )
        if directories or any(
            Path(relative).parts[0] == "profile-output"
            for relative in blobs
        ):
            raise RootfixError(
                "rootfix attempt contains profile output without a profile command"
            )
    if artifacts.get("directories") != directories:
        raise RootfixError("rootfix artifact directory inventory mismatch")
    allowed_top_files = {
        "artifacts.json",
        "completion.json",
        "candidate-test.py",
        "candidate-test.log",
        "code-profile.log",
        *PROCESS_RECORD_NAMES.values(),
    }
    actual_top_files = {
        relative
        for relative in blobs
        if len(Path(relative).parts) == 1
    }
    required_top_files = {"artifacts.json", "completion.json"}
    if "candidate_test" in commands:
        required_top_files.update(
            (
                "candidate-test.py",
                "candidate-test.log",
                PROCESS_RECORD_NAMES["candidate_test"],
            )
        )
    if "code_profile" in commands:
        required_top_files.update(
            (
                "code-profile.log",
                PROCESS_RECORD_NAMES["code_profile"],
            )
        )
    if actual_top_files != required_top_files:
        raise RootfixError(
            "rootfix attempt top-level evidence inventory is not exact"
        )
    if "candidate_test" in commands and candidate_input is None:
        raise RootfixError("rootfix committed candidate input is missing")
    if outcome == "pass" and candidate_blob_sha256 is None:
        raise RootfixError(
            "passing rootfix attempt lacks committed candidate blob binding"
        )
    for record in all_records:
        parts = Path(record["path"]).parts
        if len(parts) == 1:
            if parts[0] not in allowed_top_files:
                raise RootfixError(
                    f"unknown rootfix attempt file: {record['path']}"
                )
        elif parts[0] != "profile-output":
            raise RootfixError(
                f"unknown rootfix attempt file: {record['path']}"
            )
    expected_records = [
        record
        for record in all_records
        if record["path"] not in ("artifacts.json", "completion.json")
    ]
    if rb.canonical_json_bytes(
        artifacts.get("artifacts")
    ) != rb.canonical_json_bytes(expected_records):
        raise RootfixError("rootfix artifact inventory mismatch")
    return {
        "attempt_id": attempt_id,
        "sha256": actual_sha256,
        "outcome": outcome,
        "exit_code": exit_code,
        "interrupted_signal": interrupted_signal,
        "commands": commands,
        "metadata_path": metadata_path,
    }


def _attempt_paths(attempts: Path | DirectoryHandle) -> list[Path]:
    owned = not isinstance(attempts, DirectoryHandle)
    handle = (
        _open_directory_path(Path(attempts), "rootfix attempts")
        if owned
        else attempts
    )
    assert isinstance(handle, DirectoryHandle)
    paths: list[Path] = []
    try:
        generation = _directory_generation(
            handle, label="rootfix attempts"
        )
        with os.scandir(handle.fd) as entries:
            for entry in sorted(entries, key=lambda value: value.name):
                if (
                    not entry.name.startswith("attempt-")
                    or not rb.RUN_ID_RE.fullmatch(entry.name)
                ):
                    raise RootfixError(
                        f"unexpected rootfix attempt object: {entry.name}"
                    )
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    raise RootfixError(
                        f"unsafe rootfix attempt object: {handle.path / entry.name}"
                    )
                paths.append(handle.path / entry.name)
        _require_directory_generation(
            handle,
            generation,
            label="rootfix attempts",
        )
    finally:
        if owned:
            handle.close()
    return paths


def _published_attempts(
    attempts_path: Path | DirectoryHandle,
    status: dict[str, Any],
    candidate_top: Path | None = None,
    expected_sha256_by_id: dict[str, str] | None = None,
    *,
    allow_staging: bool = False,
) -> tuple[list[dict[str, str]], dict[str, Any] | None]:
    owned = not isinstance(attempts_path, DirectoryHandle)
    attempts = (
        _open_directory_path(Path(attempts_path), "rootfix attempts")
        if owned
        else attempts_path
    )
    assert isinstance(attempts, DirectoryHandle)
    records: list[dict[str, str]] = []
    passing: list[dict[str, Any]] = []
    staging_count = 0
    try:
        generation = _directory_generation(
            attempts, label="rootfix attempts"
        )
        with os.scandir(attempts.fd) as stream:
            entries = sorted(
                (
                    (entry.name, entry.stat(follow_symlinks=False))
                    for entry in stream
                ),
                key=lambda item: item[0],
            )
        for name, info in entries:
            if name.startswith(".staging-"):
                operation_id = name[len(".staging-"):]
                if (
                    not allow_staging
                    or not _valid_operation_id(operation_id)
                    or stat.S_ISLNK(info.st_mode)
                    or not stat.S_ISDIR(info.st_mode)
                ):
                    raise RootfixError(
                        f"unexpected rootfix attempt object: {name}"
                    )
                staging_count += 1
                if staging_count > 1:
                    raise RootfixError(
                        "multiple rootfix staging directories are forbidden"
                    )
                staging = _open_child_directory(
                    attempts,
                    name,
                    "rootfix staging",
                )
                try:
                    if (staging.dev, staging.ino) != _identity(info):
                        raise RootfixError(
                            "rootfix staging changed while opening"
                        )
                    _validate_directory_handle(
                        staging,
                        parent=attempts,
                        name=name,
                        label="rootfix staging",
                    )
                finally:
                    staging.close()
                continue
            if (
                not name.startswith("attempt-")
                or rb.RUN_ID_RE.fullmatch(name) is None
            ):
                raise RootfixError(
                    f"unexpected rootfix attempt object: {name}"
                )
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise RootfixError(
                    f"unsafe rootfix attempt object: {attempts.path / name}"
                )
            attempt = _open_child_directory(
                attempts,
                name,
                "published rootfix attempt",
            )
            try:
                if (attempt.dev, attempt.ino) != _identity(info):
                    raise RootfixError(
                        "published rootfix attempt changed while opening"
                    )
                expected_sha256 = (
                    expected_sha256_by_id.get(name)
                    if expected_sha256_by_id is not None
                    else None
                )
                if (
                    expected_sha256_by_id is not None
                    and expected_sha256 is None
                ):
                    raise RootfixError(
                        "published rootfix attempt lacks an external digest seal"
                    )
                validated = _validate_attempt(
                    attempt,
                    expected_sha256,
                    status,
                    candidate_top,
                )
                _validate_directory_handle(
                    attempt,
                    parent=attempts,
                    name=name,
                    label="published rootfix attempt",
                )
            finally:
                attempt.close()
            records.append(
                {
                    "attempt_id": validated["attempt_id"],
                    "sha256": validated["sha256"],
                }
            )
            if validated["outcome"] == "pass":
                passing.append(validated)
        _require_directory_generation(
            attempts,
            generation,
            label="rootfix attempts",
        )
    finally:
        if owned:
            attempts.close()
    if len(passing) > 1:
        raise RootfixError("multiple passing rootfix attempts are forbidden")
    return records, passing[0] if passing else None


def _validate_all_attempts(
    attempts_path: Path | DirectoryHandle,
    expected: Any,
    passing_id: str,
    passing_sha256: str,
    status: dict[str, Any],
    candidate_top: Path | None = None,
    expected_sha256_by_id: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(expected, list) or not expected:
        raise RootfixError("rootfix approval attempt inventory is missing")
    actual, passing = _published_attempts(
        attempts_path,
        status,
        candidate_top,
        expected_sha256_by_id,
    )
    if expected != actual:
        raise RootfixError("rootfix attempt inventory binding failed")
    if (
        passing is None
        or passing["attempt_id"] != passing_id
        or passing["sha256"] != passing_sha256
    ):
        raise RootfixError("passing attempt digest binding failed")
    return passing


def _require_attempt_history(
    expected: list[dict[str, str]],
    actual: list[dict[str, str]],
) -> None:
    """Require every attempt observed before execution to survive unchanged."""

    actual_by_id = {
        record["attempt_id"]: record["sha256"] for record in actual
    }
    for record in expected:
        if actual_by_id.get(record["attempt_id"]) != record["sha256"]:
            raise RootfixError(
                "pre-existing rootfix attempt history disappeared or changed"
            )


def _validate_attempt_marker_conservation(
    attempts: list[dict[str, str]],
    archive_objects: list[Path],
) -> None:
    retired: dict[str, list[str]] = {}
    for path in archive_objects:
        match = RUNNING_MARKER_ARCHIVE_RE.fullmatch(path.name)
        if match is None:
            continue
        operation_id = match.group("operation_id")
        retired.setdefault(operation_id, []).append(
            match.group("attempt_sha256")
        )
    duplicates = sorted(
        operation_id
        for operation_id, seals in retired.items()
        if len(seals) != 1
    )
    if duplicates:
        raise RootfixError(
            "duplicate retired rootfix running marker operation"
        )
    attempts_by_id = {
        attempt["attempt_id"]: attempt["sha256"] for attempt in attempts
    }
    for operation_id, seals in retired.items():
        sealed_sha256 = seals[0]
        if (
            sealed_sha256 != "none"
            and attempts_by_id.get(operation_id) != sealed_sha256
        ):
            raise RootfixError(
                "retired rootfix marker attempt digest is orphaned or mismatched"
            )
    for attempt in attempts:
        operation_id = attempt["attempt_id"]
        if retired.get(operation_id) != [attempt["sha256"]]:
            raise RootfixError(
                "published rootfix attempt lacks exactly one retired "
                f"digest-bound running marker: {operation_id}"
            )


def _sealed_attempt_digests(
    archive_objects: list[Path],
) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in archive_objects:
        match = RUNNING_MARKER_ARCHIVE_RE.fullmatch(path.name)
        if match is None:
            continue
        operation_id = match.group("operation_id")
        attempt_sha256 = match.group("attempt_sha256")
        if attempt_sha256 == "none":
            continue
        if operation_id in result:
            raise RootfixError(
                "duplicate retired rootfix attempt digest seal"
            )
        result[operation_id] = attempt_sha256
    return result


def _load_approval(
    root: Path | EvidenceContext,
    snapshot: FileSnapshot | None | object = _UNSET_FILE_SNAPSHOT,
) -> tuple[dict[str, Any], bytes]:
    context = root if isinstance(root, EvidenceContext) else None
    if snapshot is _UNSET_FILE_SNAPSHOT:
        if context is not None:
            try:
                info = os.stat(
                    APPROVAL_NAME,
                    dir_fd=context.root.fd,
                    follow_symlinks=False,
                )
            except FileNotFoundError as error:
                raise RootfixError("rootfix approval is missing") from error
            snapshot = _read_regular_at(
                context.root,
                APPROVAL_NAME,
                "rootfix approval",
                expected=info,
                max_bytes=MAX_ROOT_ATOMIC_BYTES,
            )
        else:
            snapshot = _read_regular_snapshot(
                Path(root) / APPROVAL_NAME,
                "rootfix approval",
                max_bytes=MAX_ROOT_ATOMIC_BYTES,
            )
    if snapshot is None:
        raise RootfixError("rootfix approval is missing")
    assert isinstance(snapshot, FileSnapshot)
    approval = _canonical_snapshot_object(
        snapshot.data, "rootfix approval"
    )
    data = snapshot.data
    if frozenset(approval) != APPROVAL_FIELDS:
        raise RootfixError("rootfix approval fields are invalid")
    if approval.get("schema") != APPROVAL_SCHEMA:
        raise RootfixError("rootfix approval schema is invalid")
    if approval.get("exception_id") != EXCEPTION_ID:
        raise RootfixError("rootfix exception binding failed")
    if approval.get("base_c") != BASE_C:
        raise RootfixError("rootfix Base C binding failed")
    if approval.get("verdict") != "go":
        raise RootfixError("rootfix approval verdict is invalid")
    if approval.get("policy_manifest_sha256") != POLICY_MANIFEST_SHA256:
        raise RootfixError("rootfix policy manifest binding failed")
    return approval, data


def _validate_approval(
    root: Path | EvidenceContext,
    status: dict[str, Any],
    candidate_test: dict[str, Any],
    archive_objects: list[Path],
    approval_snapshot: FileSnapshot | None | object = _UNSET_FILE_SNAPSHOT,
    candidate_top: Path | None = None,
) -> dict[str, Any]:
    owned = not isinstance(root, EvidenceContext)
    context = (
        _open_evidence_context(
            Path(root),
            create_attempts=False,
            require_attempts=True,
        )
        if owned
        else root
    )
    assert isinstance(context, EvidenceContext)
    try:
        inventory = _validate_evidence_objects(context, status)
        if approval_snapshot is _UNSET_FILE_SNAPSHOT:
            approval_snapshot = inventory.approval
        elif not _same_file_snapshot(
            approval_snapshot
            if isinstance(approval_snapshot, FileSnapshot)
            else None,
            inventory.approval,
        ):
            raise RootfixError(
                "rootfix approval presence or identity changed"
            )
        if (
            inventory.marker is not None
            or inventory.atomic_temps
            or inventory.approval is None
            or context.attempts is None
        ):
            raise RootfixError(
                "rootfix approval boundary contains stale or missing evidence"
            )
        approval, approval_bytes = _load_approval(
            context, inventory.approval
        )
        expected = _approval_payload(
            status,
            candidate_test,
            approval.get("attempts"),
            approval.get("attempt_id"),
            approval.get("attempt_sha256"),
        )
        if approval_bytes != rb.canonical_json_bytes(expected):
            raise RootfixError("rootfix approval identity binding failed")
        attempt_id = approval.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id.startswith("attempt-"):
            raise RootfixError("rootfix attempt id is invalid")
        attempt_seals = _sealed_attempt_digests(archive_objects)
        _validate_all_attempts(
            context.attempts,
            approval.get("attempts"),
            attempt_id,
            approval["attempt_sha256"],
            status,
            candidate_top,
            attempt_seals,
        )
        _validate_attempt_marker_conservation(
            approval["attempts"], archive_objects
        )
        final_inventory = _validate_evidence_objects(context, status)
        _validate_inventory_identity(
            inventory,
            final_inventory,
            marker="absent",
            approval="same",
            atomic_temps="absent",
        )
        return {
            "approved": True,
            "state": "ROOTFIX_MERGEABLE",
            "exit_code": 0,
            "bundle_id": status["bundle_id"],
            "policy_head": status["target_head"],
            "candidate_head": status["candidate_head"],
            "approval_sha256": hashlib.sha256(approval_bytes).hexdigest(),
            "attempt_id": attempt_id,
            "attempt_sha256": approval["attempt_sha256"],
        }
    finally:
        if owned:
            context.close()


def _root_atomic_parts(
    name: str,
) -> tuple[str, str, str, str] | None:
    for source, pattern in (
        ("tmp", ROOT_ATOMIC_TEMP_RE),
        ("recover", ROOT_ATOMIC_QUARANTINE_RE),
    ):
        match = pattern.fullmatch(name)
        if match is not None:
            return (
                source,
                match.group("kind"),
                match.group("writer_pid"),
                match.group("writer_token"),
            )
    return None


def _open_validated_root_atomic(
    path: Path,
    expected_snapshot: FileSnapshot | None = None,
) -> tuple[int, os.stat_result, str]:
    if _root_atomic_parts(path.name) is None:
        raise RootfixError(
            f"rootfix atomic temporary name is invalid: {path.name}"
        )
    fd = -1
    retained = False
    try:
        before = rb._require_regular_file(
            path, "rootfix atomic temporary"
        )
        if (
            before.st_size > MAX_ROOT_ATOMIC_BYTES
            or before.st_nlink != 1
            or (
                expected_snapshot is not None
                and _identity(before)
                != (expected_snapshot.dev, expected_snapshot.ino)
            )
        ):
            raise RootfixError(
                "rootfix atomic temporary size or link count is unsafe"
            )
        snapshot = _read_regular_snapshot(
            path,
            "rootfix atomic temporary",
            max_bytes=MAX_ROOT_ATOMIC_BYTES,
        )
        if (
            expected_snapshot is not None
            and not _same_file_snapshot(expected_snapshot, snapshot)
        ):
            raise RootfixError(
                "rootfix atomic temporary changed after first inventory"
            )
        data = snapshot.data
        after_read = rb._require_regular_file(
            path, "rootfix atomic temporary"
        )
        if (
            len(data) > MAX_ROOT_ATOMIC_BYTES
            or (after_read.st_dev, after_read.st_ino)
            != (before.st_dev, before.st_ino)
            or after_read.st_size > MAX_ROOT_ATOMIC_BYTES
            or after_read.st_nlink != 1
        ):
            raise RootfixError(
                "rootfix atomic temporary changed while reading"
            )

        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        fd = os.open(path, flags)
        opened = os.fstat(fd)
        current = os.lstat(path)
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(current.st_mode)
            or (opened.st_dev, opened.st_ino)
            != (after_read.st_dev, after_read.st_ino)
            or (current.st_dev, current.st_ino)
            != (opened.st_dev, opened.st_ino)
            or opened.st_size > MAX_ROOT_ATOMIC_BYTES
            or opened.st_nlink != 1
            or current.st_nlink != 1
        ):
            raise RootfixError(
                "rootfix atomic temporary changed before archival"
            )
        retained = True
        return fd, opened, hashlib.sha256(data).hexdigest()
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(
            f"rootfix atomic temporary cannot be validated: {path}"
        ) from error
    finally:
        if fd >= 0 and not retained:
            os.close(fd)


def _archive_root_atomic(
    path: Path,
    archive: Path,
    content_sha256: str,
) -> Path:
    parts = _root_atomic_parts(path.name)
    if parts is None:
        raise RootfixError(
            f"rootfix atomic temporary name is invalid: {path.name}"
        )
    source, kind, writer_pid, writer_token = parts
    try:
        rb._require_directory(
            archive, "rootfix bundle recovery archive"
        )
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(str(error)) from error
    for _ in range(16):
        destination = archive / (
            f"recovered-{source}-{kind}.json-{writer_pid}-{writer_token}-"
            f"{content_sha256}-"
            f"{os.getpid()}-{secrets.token_hex(8)}"
        )
        try:
            rb._atomic_rename_noreplace(path, destination)
            rb._fsync_directory(path.parent)
            rb._fsync_directory(archive)
            return destination
        except FileExistsError:
            continue
        except OSError as error:
            raise RootfixError(
                "rootfix atomic temporary cannot be archived"
            ) from error
    raise RootfixError(
        "rootfix atomic recovery archive name could not be allocated"
    )


def _validate_archived_root_atomic(
    path: Path,
    expected_identity: tuple[int, int] | None = None,
) -> str:
    match = ROOT_ATOMIC_ARCHIVE_RE.fullmatch(path.name)
    if match is None:
        raise RootfixError(
            f"rootfix recovery archive name is invalid: {path.name}"
        )
    try:
        snapshot = _read_regular_snapshot(
            path,
            "rootfix recovery archive object",
            max_bytes=MAX_ROOT_ATOMIC_BYTES,
        )
        if (
            expected_identity is not None
            and (snapshot.dev, snapshot.ino) != expected_identity
        ):
            raise RootfixError(
                "rootfix recovery archive identity, size or link count "
                "is unsafe"
            )
        actual_sha256 = snapshot.sha256
        if actual_sha256 != match.group("content_sha256"):
            raise RootfixError(
                "rootfix recovery archive content digest is invalid"
            )
        return actual_sha256
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(
            f"rootfix recovery archive object cannot be validated: {path}"
        ) from error


def _staging_tree_identity(
    stage: Path | DirectoryHandle,
) -> tuple[int, str]:
    directories, records = _artifact_inventory(stage)
    payload = rb.canonical_json_bytes(
        {"directories": directories, "files": records}
    )
    return len(payload), hashlib.sha256(payload).hexdigest()


def _validate_archived_staging(
    path: Path,
    status: dict[str, Any],
    expected_identity: tuple[int, int] | None = None,
) -> tuple[int, int, int, str]:
    match = STAGING_ARCHIVE_RE.fullmatch(path.name)
    if match is None:
        raise RootfixError(
            f"retired rootfix staging name is invalid: {path.name}"
        )
    parent = _open_directory_path(
        path.parent, "rootfix bundle recovery archive"
    )
    stage: DirectoryHandle | None = None
    try:
        stage = _open_child_directory(
            parent, path.name, "retired rootfix staging"
        )
        if expected_identity is not None and (
            stage.dev,
            stage.ino,
        ) != expected_identity:
            raise RootfixError(
                "retired rootfix staging identity changed"
            )
        operation_id = match.group("operation_id")
        _require_no_live_stage_processes(
            stage, status, operation_id
        )
        size, digest = _staging_tree_identity(stage)
        if digest != match.group("tree_sha256"):
            raise RootfixError(
                "retired rootfix staging tree digest is invalid"
            )
        _validate_directory_handle(
            stage,
            parent=parent,
            name=path.name,
            label="retired rootfix staging",
        )
        return stage.dev, stage.ino, size, digest
    finally:
        if stage is not None:
            stage.close()
        parent.close()


def _archive_validated_staging(
    stage: DirectoryHandle,
    attempts: DirectoryHandle,
    archive: Path,
    status: dict[str, Any],
    operation_id: str,
) -> ArchiveSeal:
    if (
        not _valid_operation_id(operation_id)
        or stage.path.name != f".staging-{operation_id}"
    ):
        raise RootfixError("rootfix staging archive binding is invalid")
    _validate_directory_handle(
        stage,
        parent=attempts,
        name=stage.path.name,
        label="rootfix staging",
    )
    _require_no_live_stage_processes(stage, status, operation_id)
    size, digest = _staging_tree_identity(stage)
    _validate_directory_handle(
        stage,
        parent=attempts,
        name=stage.path.name,
        label="rootfix staging",
    )
    archive_handle = _open_directory_path(
        archive, "rootfix bundle recovery archive"
    )
    destination: Path | None = None
    try:
        for _ in range(16):
            name = (
                f"retired-staging-{operation_id}-{digest}-"
                f"{os.getpid()}-{secrets.token_hex(8)}"
            )
            try:
                _atomic_rename_noreplace_at(
                    attempts,
                    stage.path.name,
                    archive_handle,
                    name,
                )
                destination = archive / name
                break
            except FileExistsError:
                continue
        if destination is None:
            raise RootfixError(
                "retired rootfix staging name could not be allocated"
            )
        os.fsync(attempts.fd)
        os.fsync(archive_handle.fd)
        stage.path = destination
        _validate_directory_handle(
            stage,
            parent=archive_handle,
            name=destination.name,
            label="retired rootfix staging",
        )
        final_size, final_digest = _staging_tree_identity(stage)
        if final_size != size or final_digest != digest:
            raise RootfixError(
                "rootfix staging changed during archival; "
                f"retained at {destination}"
            )
        _validate_directory_handle(
            stage,
            parent=archive_handle,
            name=destination.name,
            label="retired rootfix staging",
        )
        return ArchiveSeal(
            destination,
            stage.dev,
            stage.ino,
            final_size,
            final_digest,
            "staging",
        )
    except OSError as error:
        raise RootfixError(
            "rootfix staging archival failed; "
            f"retained at {destination}"
        ) from error
    finally:
        archive_handle.close()


def _validate_recovery_archive(
    archive: Path | None,
    status: dict[str, Any],
    required: tuple[ArchiveSeal, ...] | list[ArchiveSeal] = (),
) -> list[Path]:
    bundle_id = status["bundle_id"]
    if archive is None:
        if required:
            raise RootfixError(
                "required rootfix recovery archive disappeared"
            )
        return []
    if (
        archive.name != bundle_id
        or rb.RUN_ID_RE.fullmatch(bundle_id) is None
    ):
        raise RootfixError("rootfix recovery archive bundle binding failed")
    objects: list[Path] = []
    archive_handle: DirectoryHandle | None = None
    try:
        archive_handle = _open_directory_path(
            archive, "rootfix bundle recovery archive"
        )
        generation = _directory_generation(
            archive_handle,
            label="rootfix bundle recovery archive",
        )
        with os.scandir(archive_handle.fd) as stream:
            entries = sorted(
                (
                    (entry.name, entry.stat(follow_symlinks=False))
                    for entry in stream
                ),
                key=lambda item: item[0],
            )
        for name, info in entries:
            path = archive_handle.path / name
            if stat.S_ISLNK(info.st_mode):
                raise RootfixError(
                    "unexpected rootfix recovery archive object: "
                    f"{name}"
                )
            if (
                stat.S_ISDIR(info.st_mode)
                and STAGING_ARCHIVE_RE.fullmatch(name) is not None
            ):
                _validate_archived_staging(
                    path, status, _identity(info)
                )
            elif (
                stat.S_ISREG(info.st_mode)
                and ROOT_ATOMIC_ARCHIVE_RE.fullmatch(name)
                is not None
            ):
                _validate_archived_root_atomic(path, _identity(info))
            elif (
                stat.S_ISREG(info.st_mode)
                and
                RUNNING_MARKER_ARCHIVE_RE.fullmatch(name)
                is not None
            ):
                _validate_archived_running_marker(
                    path, status, _identity(info)
                )
            else:
                raise RootfixError(
                    "unexpected rootfix recovery archive object: "
                    f"{name}"
                )
            objects.append(path)
        by_path = {path: path for path in objects}
        for seal in required:
            if seal.kind not in ("running", "atomic", "staging"):
                raise RootfixError(
                    "required rootfix recovery seal type is invalid"
                )
            path = seal.path
            if path not in by_path:
                raise RootfixError(
                    "required recovered rootfix object disappeared: "
                    f"{path.name}"
                )
            if seal.kind == "staging":
                dev, ino, size, digest = _validate_archived_staging(
                    path, status, (seal.dev, seal.ino)
                )
                if (
                    (dev, ino) != (seal.dev, seal.ino)
                    or size != seal.size
                    or digest != seal.sha256
                ):
                    raise RootfixError(
                        "required recovered rootfix object changed: "
                        f"{path.name}"
                    )
            else:
                snapshot = _read_regular_snapshot(
                    path,
                    "required recovered rootfix object",
                    max_bytes=MAX_ROOT_ATOMIC_BYTES,
                )
                if (
                    (snapshot.dev, snapshot.ino) != (seal.dev, seal.ino)
                    or snapshot.size != seal.size
                    or snapshot.sha256 != seal.sha256
                ):
                    raise RootfixError(
                        "required recovered rootfix object changed: "
                        f"{path.name}"
                    )
                if (
                    seal.kind == "running"
                    and RUNNING_MARKER_ARCHIVE_RE.fullmatch(path.name) is None
                ) or (
                    seal.kind == "atomic"
                    and ROOT_ATOMIC_ARCHIVE_RE.fullmatch(path.name) is None
                ):
                    raise RootfixError(
                        "required recovered rootfix object type changed: "
                        f"{path.name}"
                    )
        _require_directory_generation(
            archive_handle,
            generation,
            label="rootfix bundle recovery archive",
        )
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(
            "rootfix recovery archive cannot be enumerated"
        ) from error
    finally:
        if archive_handle is not None:
            archive_handle.close()
    return sorted(objects)


def _validate_current_recovery_archive(
    repo: Path,
    status: dict[str, Any],
) -> tuple[Path | None, list[Path]]:
    archive = _recovery_archive_path(
        repo, status["bundle_id"], create=False
    )
    return archive, _validate_recovery_archive(archive, status)


def _archive_validated_root_atomic(
    path: Path,
    archive: Path,
    expected_snapshot: FileSnapshot | None = None,
) -> ArchiveSeal:
    fd, opened, content_sha256 = _open_validated_root_atomic(
        path, expected_snapshot
    )
    destination: Path | None = None
    try:
        destination = _archive_root_atomic(
            path, archive, content_sha256
        )
        moved = os.lstat(destination)
        descriptor = os.fstat(fd)
        expected = (opened.st_dev, opened.st_ino)
        if (
            stat.S_ISLNK(moved.st_mode)
            or not stat.S_ISREG(moved.st_mode)
            or (moved.st_dev, moved.st_ino) != expected
            or (descriptor.st_dev, descriptor.st_ino) != expected
            or moved.st_nlink != 1
            or descriptor.st_nlink != 1
            or moved.st_size > MAX_ROOT_ATOMIC_BYTES
        ):
            raise RootfixError(
                "rootfix atomic temporary changed during archival; "
                f"moved object retained at {destination}"
            )
        _validate_archived_root_atomic(destination, expected)
        final_path = os.lstat(destination)
        final_descriptor = os.fstat(fd)
        if (
            stat.S_ISLNK(final_path.st_mode)
            or not stat.S_ISREG(final_path.st_mode)
            or (final_path.st_dev, final_path.st_ino) != expected
            or (final_descriptor.st_dev, final_descriptor.st_ino)
            != expected
            or final_path.st_nlink != 1
            or final_descriptor.st_nlink != 1
        ):
            raise RootfixError(
                "rootfix atomic temporary changed after archival "
                f"validation; moved object retained at {destination}"
            )
        final_snapshot = _read_regular_snapshot(
            destination,
            "archived rootfix atomic temporary",
            max_bytes=MAX_ROOT_ATOMIC_BYTES,
        )
        if (
            (final_snapshot.dev, final_snapshot.ino) != expected
            or final_snapshot.sha256 != content_sha256
        ):
            raise RootfixError(
                "rootfix atomic temporary changed before seal publication"
            )
        return ArchiveSeal(
            destination,
            final_snapshot.dev,
            final_snapshot.ino,
            final_snapshot.size,
            final_snapshot.sha256,
            "atomic",
        )
    except OSError as error:
        raise RootfixError(
            "rootfix atomic temporary archival failed; "
            f"moved object retained at {destination}"
        ) from error
    finally:
        os.close(fd)


def _validate_evidence_objects(
    root: Path | EvidenceContext,
    status: dict[str, Any] | None = None,
    *,
    allow_atomic_temps: bool = False,
) -> RootInventorySnapshot:
    owned_context = not isinstance(root, EvidenceContext)
    context = (
        _open_evidence_context(Path(root), create_attempts=False)
        if owned_context
        else root
    )
    assert isinstance(context, EvidenceContext)
    allowed = {
        "attempts": "directory",
        APPROVAL_NAME: "file",
        RUNNING_NAME: "file",
    }
    marker: FileSnapshot | None = None
    approval: FileSnapshot | None = None
    atomic_temps: list[FileSnapshot] = []
    try:
        _validate_evidence_context(context)
        generation = _directory_generation(
            context.root, label="rootfix evidence root"
        )
        with os.scandir(context.root.fd) as entries:
            for entry in entries:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise RootfixError(
                        f"unsafe rootfix evidence object: {context.root.path / entry.name}"
                    )
                expected = allowed.get(entry.name)
                if expected is None:
                    if (
                        _root_atomic_parts(entry.name) is not None
                        and stat.S_ISREG(info.st_mode)
                        and info.st_size <= MAX_ROOT_ATOMIC_BYTES
                        and info.st_nlink == 1
                    ):
                        if not allow_atomic_temps:
                            raise StaleRootfixError(
                                "stale rootfix atomic temporary exists; "
                                "pass --recover-stale"
                            )
                        atomic_temps.append(
                            _read_regular_at(
                                context.root,
                                entry.name,
                                "rootfix atomic temporary",
                                expected=info,
                                max_bytes=MAX_ROOT_ATOMIC_BYTES,
                            )
                        )
                        continue
                    raise RootfixError(
                        f"unexpected rootfix evidence object: {entry.name}"
                    )
                if expected == "directory" and not stat.S_ISDIR(info.st_mode):
                    raise RootfixError(
                        "rootfix evidence directory is unsafe: "
                        f"{context.root.path / entry.name}"
                    )
                if expected == "file" and not stat.S_ISREG(info.st_mode):
                    raise RootfixError(
                        "rootfix evidence file is unsafe: "
                        f"{context.root.path / entry.name}"
                    )
                if entry.name == "attempts":
                    if context.attempts is None:
                        context.attempts = _open_child_directory(
                            context.root,
                            "attempts",
                            "rootfix attempts",
                        )
                    if (
                        context.attempts.dev,
                        context.attempts.ino,
                    ) != _identity(info):
                        raise RootfixError(
                            "rootfix attempts identity changed during inventory"
                        )
                elif entry.name == RUNNING_NAME:
                    marker = _read_regular_at(
                        context.root,
                        entry.name,
                        "rootfix running marker",
                        expected=info,
                        max_bytes=MAX_ROOT_ATOMIC_BYTES,
                    )
                    marker_value = _canonical_snapshot_object(
                        marker.data, "rootfix running marker"
                    )
                    if status is not None:
                        _validate_running_marker_payload(marker_value, status)
                elif entry.name == APPROVAL_NAME:
                    approval = _read_regular_at(
                        context.root,
                        entry.name,
                        "rootfix approval",
                        expected=info,
                        max_bytes=MAX_ROOT_ATOMIC_BYTES,
                    )
                    _canonical_snapshot_object(
                        approval.data, "rootfix approval"
                    )
        _require_directory_generation(
            context.root,
            generation,
            label="rootfix evidence root",
        )
        _validate_evidence_context(context)
    except OSError as error:
        raise RootfixError("rootfix evidence root cannot be enumerated") from error
    finally:
        if owned_context:
            context.close()
    return RootInventorySnapshot(
        (context.root.dev, context.root.ino),
        (
            (context.attempts.dev, context.attempts.ino)
            if context.attempts is not None
            else None
        ),
        marker,
        approval,
        tuple(sorted(atomic_temps, key=lambda item: item.path.name)),
    )


def _same_file_snapshot(
    expected: FileSnapshot | None,
    actual: FileSnapshot | None,
) -> bool:
    if expected is None or actual is None:
        return expected is actual
    return (
        expected.data == actual.data
        and expected.sha256 == actual.sha256
        and expected.size == actual.size
        and (expected.dev, expected.ino) == (actual.dev, actual.ino)
        and expected.mtime_ns == actual.mtime_ns
        and expected.ctime_ns == actual.ctime_ns
    )


def _validate_inventory_identity(
    expected: RootInventorySnapshot,
    actual: RootInventorySnapshot,
    *,
    marker: str = "same",
    approval: str = "same",
    atomic_temps: str = "same",
) -> None:
    file_policies = {"same", "absent", "removed", "any"}
    if marker not in file_policies or approval not in file_policies:
        raise RootfixError("rootfix inventory file policy is invalid")
    if atomic_temps not in {"same", "absent", "any"}:
        raise RootfixError("rootfix atomic inventory policy is invalid")
    if (
        expected.root_identity != actual.root_identity
        or expected.attempts_identity != actual.attempts_identity
    ):
        raise RootfixError(
            "rootfix evidence root or attempts directory identity changed"
        )
    policies = (
        ("running marker", expected.marker, actual.marker, marker),
        ("approval", expected.approval, actual.approval, approval),
    )
    for label, before, after, policy in policies:
        if policy == "same" and not _same_file_snapshot(before, after):
            raise RootfixError(
                f"rootfix {label} presence or identity changed"
            )
        if policy == "absent" and after is not None:
            raise RootfixError(f"rootfix {label} unexpectedly exists")
        if policy == "removed" and after is not None:
            raise RootfixError(f"rootfix {label} was not retired")
    if atomic_temps == "same":
        expected_atomic = [
            (item.path.name, item.dev, item.ino, item.sha256)
            for item in expected.atomic_temps
        ]
        actual_atomic = [
            (item.path.name, item.dev, item.ino, item.sha256)
            for item in actual.atomic_temps
        ]
        if expected_atomic != actual_atomic:
            raise RootfixError(
                "rootfix atomic temporary inventory changed"
            )
    elif atomic_temps == "absent" and actual.atomic_temps:
        raise RootfixError("rootfix atomic temporary was not retired")


def _running_marker_payload(
    status: dict[str, Any],
    operation_id: str,
    staging_name: str,
) -> dict[str, Any]:
    return {
        "schema": RUNNING_SCHEMA,
        "exception_id": EXCEPTION_ID,
        "bundle_id": status["bundle_id"],
        "operation_id": operation_id,
        "pid": os.getpid(),
        "proc_start": rb._proc_start_token(os.getpid()) or "unavailable",
        "boot_id": rb._boot_id() or "unavailable",
        "staging_name": staging_name,
        "policy_head": status["target_head"],
        "candidate_head": status["candidate_head"],
        "routing_sha256": status["routing_sha256"],
        "started_ns": str(time.time_ns()),
    }


def _valid_operation_id(value: Any) -> bool:
    return (
        isinstance(value, str)
        and ROOTFIX_ATTEMPT_ID_RE.fullmatch(value) is not None
    )


def _validate_running_marker_payload(
    marker: dict[str, Any],
    status: dict[str, Any],
) -> dict[str, Any]:
    fields = frozenset(
        (
            "schema",
            "exception_id",
            "bundle_id",
            "operation_id",
            "pid",
            "proc_start",
            "boot_id",
            "staging_name",
            "policy_head",
            "candidate_head",
            "routing_sha256",
            "started_ns",
        )
    )
    if frozenset(marker) != fields or marker.get("schema") != RUNNING_SCHEMA:
        raise RootfixError("rootfix running marker fields are invalid")
    bindings = {
        "exception_id": EXCEPTION_ID,
        "bundle_id": status["bundle_id"],
        "policy_head": status["target_head"],
        "candidate_head": status["candidate_head"],
        "routing_sha256": status["routing_sha256"],
    }
    for field, expected in bindings.items():
        if marker.get(field) != expected:
            raise RootfixError(
                f"rootfix running marker {field} binding failed"
            )
    operation_id = marker.get("operation_id")
    if (
        not _valid_operation_id(operation_id)
        or marker.get("staging_name") != f".staging-{operation_id}"
    ):
        raise RootfixError("rootfix running marker operation binding failed")
    if (
        not isinstance(marker.get("started_ns"), str)
        or not marker["started_ns"].isdigit()
    ):
        raise RootfixError("rootfix running marker timestamp is invalid")
    pid = marker.get("pid")
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise RootfixError("rootfix running marker pid is invalid")
    if (
        not isinstance(marker.get("proc_start"), str)
        or not marker["proc_start"]
    ):
        raise RootfixError(
            "rootfix running marker process token is invalid"
        )
    if (
        not isinstance(marker.get("boot_id"), str)
        or not marker["boot_id"]
    ):
        raise RootfixError("rootfix running marker boot id is invalid")
    return marker


def _load_running_marker_snapshot(
    root: Path | EvidenceContext,
    status: dict[str, Any],
) -> tuple[dict[str, Any], FileSnapshot] | None:
    context = root if isinstance(root, EvidenceContext) else None
    path = (
        context.root.path / RUNNING_NAME
        if context is not None
        else Path(root) / RUNNING_NAME
    )
    try:
        if context is not None:
            info = os.stat(
                RUNNING_NAME,
                dir_fd=context.root.fd,
                follow_symlinks=False,
            )
            snapshot = _read_regular_at(
                context.root,
                RUNNING_NAME,
                "rootfix running marker",
                expected=info,
                max_bytes=MAX_ROOT_ATOMIC_BYTES,
            )
        else:
            if rb._lstat(path) is None:
                return None
            snapshot = _read_regular_snapshot(
                path,
                "rootfix running marker",
                max_bytes=MAX_ROOT_ATOMIC_BYTES,
            )
    except FileNotFoundError:
        return None
    try:
        marker = _canonical_snapshot_object(
            snapshot.data, "rootfix running marker"
        )
        marker = _validate_running_marker_payload(marker, status)
        return marker, snapshot
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(
            "rootfix running marker cannot be validated"
        ) from error


def _marker_snapshot_from_file(
    snapshot: FileSnapshot | None,
    status: dict[str, Any],
) -> tuple[dict[str, Any], FileSnapshot] | None:
    if snapshot is None:
        return None
    marker = _canonical_snapshot_object(
        snapshot.data, "rootfix running marker"
    )
    return _validate_running_marker_payload(marker, status), snapshot


def _same_running_marker_snapshot(
    expected: tuple[dict[str, Any], FileSnapshot] | None,
    actual: tuple[dict[str, Any], FileSnapshot] | None,
) -> bool:
    if expected is None or actual is None:
        return expected is actual
    expected_marker, expected_file = expected
    actual_marker, actual_file = actual
    return (
        expected_marker == actual_marker
        and _same_file_snapshot(expected_file, actual_file)
    )


def _open_validated_running_marker(
    root: Path | EvidenceContext,
    status: dict[str, Any],
    expected_marker: dict[str, Any],
    expected_snapshot: (
        tuple[dict[str, Any], FileSnapshot] | None
    ) = None,
) -> tuple[int, os.stat_result, dict[str, Any], str]:
    context = root if isinstance(root, EvidenceContext) else None
    path = (
        context.root.path / RUNNING_NAME
        if context is not None
        else Path(root) / RUNNING_NAME
    )
    fd = -1
    retained = False
    try:
        snapshot = _load_running_marker_snapshot(root, status)
        if snapshot is None:
            raise RootfixError(
                "rootfix running marker disappeared before archival"
            )
        marker, file_snapshot = snapshot
        if marker != expected_marker:
            raise RootfixError(
                "rootfix running marker changed before archival"
            )
        if (
            expected_snapshot is not None
            and not _same_running_marker_snapshot(
                expected_snapshot, snapshot
            )
        ):
            raise RootfixError(
                "rootfix running marker identity changed before archival"
            )
        if (
            file_snapshot.size > MAX_ROOT_ATOMIC_BYTES
        ):
            raise RootfixError(
                "rootfix running marker size or link count is unsafe"
            )
        flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )
        fd = (
            os.open(
                RUNNING_NAME,
                flags,
                dir_fd=context.root.fd,
            )
            if context is not None
            else os.open(path, flags)
        )
        opened = os.fstat(fd)
        current = (
            os.stat(
                RUNNING_NAME,
                dir_fd=context.root.fd,
                follow_symlinks=False,
            )
            if context is not None
            else os.lstat(path)
        )
        if (
            not stat.S_ISREG(opened.st_mode)
            or not stat.S_ISREG(current.st_mode)
            or (opened.st_dev, opened.st_ino)
            != (file_snapshot.dev, file_snapshot.ino)
            or (current.st_dev, current.st_ino)
            != (opened.st_dev, opened.st_ino)
            or opened.st_size != file_snapshot.size
            or opened.st_nlink != 1
            or current.st_nlink != 1
        ):
            raise RootfixError(
                "rootfix running marker changed before archival"
            )
        retained = True
        return (
            fd,
            opened,
            marker,
            file_snapshot.sha256,
        )
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(
            "rootfix running marker cannot be validated"
        ) from error
    finally:
        if fd >= 0 and not retained:
            os.close(fd)


def _validate_archived_running_marker(
    path: Path,
    status: dict[str, Any],
    expected_identity: tuple[int, int] | None = None,
) -> dict[str, Any]:
    match = RUNNING_MARKER_ARCHIVE_RE.fullmatch(path.name)
    if match is None:
        raise RootfixError(
            f"retired rootfix running marker name is invalid: {path.name}"
        )
    try:
        snapshot = _read_regular_snapshot(
            path,
            "retired rootfix running marker",
            max_bytes=MAX_ROOT_ATOMIC_BYTES,
        )
        if (
            expected_identity is not None
            and (snapshot.dev, snapshot.ino) != expected_identity
        ):
            raise RootfixError(
                "retired rootfix running marker identity, size or link "
                "count is unsafe"
            )
        marker = _canonical_snapshot_object(
            snapshot.data, "retired rootfix running marker"
        )
        marker = _validate_running_marker_payload(marker, status)
        if (
            marker["operation_id"] != match.group("operation_id")
            or snapshot.sha256 != match.group("content_sha256")
        ):
            raise RootfixError(
                "retired rootfix running marker binding is invalid"
            )
        return marker
    except (OSError, rb.ReviewBundleError) as error:
        raise RootfixError(
            f"retired rootfix running marker cannot be validated: {path}"
        ) from error


def _archive_validated_running_marker(
    root: Path | EvidenceContext,
    archive: Path,
    status: dict[str, Any],
    expected_marker: dict[str, Any],
    expected_snapshot: (
        tuple[dict[str, Any], FileSnapshot] | None
    ) = None,
    attempt_sha256: str | None = None,
) -> ArchiveSeal:
    if (
        attempt_sha256 is not None
        and re.fullmatch(r"[0-9a-f]{64}", attempt_sha256) is None
    ):
        raise RootfixError("retired marker attempt digest is invalid")
    context = root if isinstance(root, EvidenceContext) else None
    root_path = context.root.path if context is not None else Path(root)
    path = root_path / RUNNING_NAME
    fd, opened, marker, content_sha256 = (
        _open_validated_running_marker(
            root, status, expected_marker, expected_snapshot
        )
    )
    destination: Path | None = None
    try:
        rb._require_directory(
            archive, "rootfix bundle recovery archive"
        )
        for _ in range(16):
            destination = archive / (
                f"retired-running-{marker['operation_id']}-"
                f"{attempt_sha256 or 'none'}-"
                f"{content_sha256}-{os.getpid()}-"
                f"{secrets.token_hex(8)}.json"
            )
            try:
                rb._atomic_rename_noreplace(path, destination)
                if context is not None:
                    os.fsync(context.root.fd)
                else:
                    rb._fsync_directory(root_path)
                rb._fsync_directory(archive)
                break
            except FileExistsError:
                destination = None
                continue
        if destination is None:
            raise RootfixError(
                "retired rootfix running marker name could not be allocated"
            )
        moved = os.lstat(destination)
        descriptor = os.fstat(fd)
        expected = (opened.st_dev, opened.st_ino)
        if (
            stat.S_ISLNK(moved.st_mode)
            or not stat.S_ISREG(moved.st_mode)
            or (moved.st_dev, moved.st_ino) != expected
            or (descriptor.st_dev, descriptor.st_ino) != expected
            or moved.st_nlink != 1
            or descriptor.st_nlink != 1
            or moved.st_size > MAX_ROOT_ATOMIC_BYTES
        ):
            raise RootfixError(
                "rootfix running marker changed during archival; "
                f"moved object retained at {destination}"
            )
        _validate_archived_running_marker(
            destination, status, expected
        )
        final_path = os.lstat(destination)
        final_descriptor = os.fstat(fd)
        if (
            stat.S_ISLNK(final_path.st_mode)
            or not stat.S_ISREG(final_path.st_mode)
            or (final_path.st_dev, final_path.st_ino) != expected
            or (final_descriptor.st_dev, final_descriptor.st_ino)
            != expected
            or final_path.st_nlink != 1
            or final_descriptor.st_nlink != 1
        ):
            raise RootfixError(
                "rootfix running marker changed after archival "
                f"validation; moved object retained at {destination}"
            )
        final_snapshot = _read_regular_snapshot(
            destination,
            "retired rootfix running marker",
            max_bytes=MAX_ROOT_ATOMIC_BYTES,
        )
        if (
            (final_snapshot.dev, final_snapshot.ino) != expected
            or final_snapshot.sha256 != content_sha256
        ):
            raise RootfixError(
                "rootfix running marker changed before seal publication"
            )
        return ArchiveSeal(
            destination,
            final_snapshot.dev,
            final_snapshot.ino,
            final_snapshot.size,
            final_snapshot.sha256,
            "running",
        )
    except OSError as error:
        raise RootfixError(
            "rootfix running marker archival failed; "
            f"moved object retained at {destination}"
        ) from error
    finally:
        os.close(fd)


def _attempt_directory_state(
    attempts: Path | DirectoryHandle,
) -> tuple[list[Path], list[Path]]:
    owned = not isinstance(attempts, DirectoryHandle)
    handle = (
        _open_directory_path(Path(attempts), "rootfix attempts")
        if owned
        else attempts
    )
    assert isinstance(handle, DirectoryHandle)
    published: list[Path] = []
    staging: list[Path] = []
    try:
        generation = _directory_generation(
            handle, label="rootfix attempts"
        )
        with os.scandir(handle.fd) as entries:
            for entry in entries:
                info = entry.stat(follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                    raise RootfixError(
                        f"unsafe rootfix attempt object: {handle.path / entry.name}"
                    )
                path = handle.path / entry.name
                if entry.name.startswith(".staging-"):
                    operation_id = entry.name[len(".staging-"):]
                    if not _valid_operation_id(operation_id):
                        raise RootfixError(
                            "unexpected rootfix staging object: "
                            f"{entry.name}"
                        )
                    staging.append(path)
                elif (
                    entry.name.startswith("attempt-")
                    and rb.RUN_ID_RE.fullmatch(entry.name)
                ):
                    published.append(path)
                else:
                    raise RootfixError(
                        f"unexpected rootfix attempt object: {entry.name}"
                    )
        _require_directory_generation(
            handle,
            generation,
            label="rootfix attempts",
        )
    except OSError as error:
        raise RootfixError("rootfix attempts cannot be enumerated") from error
    finally:
        if owned:
            handle.close()
    return sorted(published), sorted(staging)


def _recover_stale(
    root: Path | EvidenceContext,
    attempts: Path | DirectoryHandle,
    status: dict[str, Any],
    atomic_temps: list[FileSnapshot] | tuple[FileSnapshot, ...] | None = None,
    recovery_archive: Path | None = None,
    marker_snapshot: (
        tuple[dict[str, Any], FileSnapshot]
        | None
        | object
    ) = _UNSET_MARKER_SNAPSHOT,
    inventory_snapshot: RootInventorySnapshot | None = None,
) -> tuple[ArchiveSeal, ...]:
    owned = not isinstance(root, EvidenceContext)
    context = (
        _open_evidence_context(
            Path(root),
            create_attempts=False,
            require_attempts=True,
        )
        if owned
        else root
    )
    assert isinstance(context, EvidenceContext)
    if context.attempts is None:
        raise RootfixError("rootfix attempts directory is missing")
    attempts_handle = context.attempts
    if isinstance(attempts, DirectoryHandle):
        if (
            attempts.dev,
            attempts.ino,
        ) != (attempts_handle.dev, attempts_handle.ino):
            raise RootfixError("rootfix attempts handle binding failed")
    elif Path(attempts) != attempts_handle.path:
        raise RootfixError("rootfix attempts path binding failed")
    stage_handle: DirectoryHandle | None = None
    stage_operation_id: str | None = None
    try:
        if inventory_snapshot is None:
            inventory_snapshot = _validate_evidence_objects(
                context,
                status,
                allow_atomic_temps=True,
            )
        if isinstance(atomic_temps, RootInventorySnapshot):
            atomic_temps = atomic_temps.atomic_temps
        if atomic_temps is None:
            atomic_temps = inventory_snapshot.atomic_temps
        if marker_snapshot is _UNSET_MARKER_SNAPSHOT:
            marker_snapshot = _marker_snapshot_from_file(
                inventory_snapshot.marker, status
            )
        current_inventory = _validate_evidence_objects(
            context,
            status,
            allow_atomic_temps=True,
        )
        _validate_inventory_identity(
            inventory_snapshot,
            current_inventory,
        )
        current_marker_snapshot = _marker_snapshot_from_file(
            current_inventory.marker, status
        )
        if not _same_running_marker_snapshot(
            marker_snapshot, current_marker_snapshot
        ):
            raise RootfixError(
                "rootfix running marker presence or identity changed "
                "before stale recovery"
            )
        marker = (
            current_marker_snapshot[0]
            if current_marker_snapshot is not None
            else None
        )
        published, staging = _attempt_directory_state(attempts_handle)
        if marker is None and not staging and not atomic_temps:
            _validate_recovery_archive(recovery_archive, status)
            return ()
        if current_inventory.approval is not None:
            raise RootfixError(
                "approved rootfix evidence may not enter stale recovery"
            )
        attempt_sha256: str | None = None
        if marker is not None:
            try:
                live = rb._running_marker_live(marker)
            except rb.ReviewBundleError as error:
                raise RootfixError(str(error)) from error
            if live:
                raise RootfixError(
                    "live rootfix verification may not be recovered"
                )
            expected = attempts_handle.path / marker["staging_name"]
            published_match = [
                path for path in published if path.name == marker["operation_id"]
            ]
            if staging:
                if staging != [expected] or published_match:
                    raise StaleRootfixError(
                        "stale rootfix marker conflicts with attempt residue"
                    )
                stage_handle = _open_child_directory(
                    attempts_handle,
                    expected.name,
                    "stale rootfix staging",
                )
                stage_operation_id = marker["operation_id"]
                _require_no_live_stage_processes(
                    stage_handle,
                    status,
                    stage_operation_id,
                )
            elif len(published_match) == 1:
                raise StaleRootfixError(
                    "published rootfix attempt lacks a durable external "
                    "digest seal; stale recovery may not derive a new seal"
                )
            else:
                raise StaleRootfixError(
                    "stale rootfix marker has neither bound staging nor "
                    "published attempt"
                )
        elif len(staging) > 1:
            raise StaleRootfixError(
                "markerless rootfix recovery has multiple staging residues"
            )
        elif staging:
            operation_id = staging[0].name[len(".staging-"):]
            stage_handle = _open_child_directory(
                attempts_handle,
                staging[0].name,
                "markerless rootfix staging",
            )
            stage_operation_id = operation_id
            _require_no_live_stage_processes(
                stage_handle, status, operation_id
            )
        if (
            atomic_temps
            or marker is not None
            or stage_handle is not None
        ) and recovery_archive is None:
            raise RootfixError(
                "rootfix recovery archive is required for stale residue"
            )
        required: list[ArchiveSeal] = []
        if marker is not None:
            assert recovery_archive is not None
            required.append(
                _archive_validated_running_marker(
                    context,
                    recovery_archive,
                    status,
                    marker,
                    current_marker_snapshot,
                    attempt_sha256,
                )
            )
        for snapshot in atomic_temps:
            assert recovery_archive is not None
            required.append(
                _archive_validated_root_atomic(
                    snapshot.path,
                    recovery_archive,
                    snapshot,
                )
            )
        if stage_handle is not None:
            assert recovery_archive is not None
            assert stage_operation_id is not None
            required.append(
                _archive_validated_staging(
                    stage_handle,
                    attempts_handle,
                    recovery_archive,
                    status,
                    stage_operation_id,
                )
            )
        _validate_recovery_archive(
            recovery_archive, status, required
        )
        _validate_directory_handle(
            attempts_handle,
            parent=context.root,
            name="attempts",
            label="rootfix attempts",
        )
        _validate_recovery_archive(
            recovery_archive, status, required
        )
        final_inventory = _validate_evidence_objects(context, status)
        _validate_inventory_identity(
            inventory_snapshot,
            final_inventory,
            marker="removed",
            approval="same",
            atomic_temps="absent",
        )
        return tuple(required)
    finally:
        if stage_handle is not None:
            stage_handle.close()
        if owned:
            context.close()


def _require_no_stale_state(
    root: Path | EvidenceContext,
    attempts: Path | DirectoryHandle,
    status: dict[str, Any],
    inventory_snapshot: RootInventorySnapshot | None = None,
) -> None:
    owned = not isinstance(root, EvidenceContext)
    context = (
        _open_evidence_context(
            Path(root),
            create_attempts=False,
            require_attempts=True,
        )
        if owned
        else root
    )
    assert isinstance(context, EvidenceContext)
    if context.attempts is None:
        raise RootfixError("rootfix attempts directory is missing")
    try:
        inventory = (
            inventory_snapshot
            if inventory_snapshot is not None
            else _validate_evidence_objects(
                context,
                status,
                allow_atomic_temps=True,
            )
        )
        current = _validate_evidence_objects(
            context,
            status,
            allow_atomic_temps=True,
        )
        _validate_inventory_identity(inventory, current)
        if current.atomic_temps:
            raise StaleRootfixError(
                "stale rootfix atomic temporary exists; pass --recover-stale"
            )
        marker_snapshot = _marker_snapshot_from_file(
            current.marker, status
        )
        marker = (
            marker_snapshot[0] if marker_snapshot is not None else None
        )
        _, staging = _attempt_directory_state(context.attempts)
        if marker is not None:
            try:
                if rb._running_marker_live(marker):
                    raise RootfixError(
                        "live rootfix verification is already running"
                    )
            except rb.ReviewBundleError as error:
                raise RootfixError(str(error)) from error
            raise StaleRootfixError(
                "stale rootfix running marker exists; pass --recover-stale"
            )
        if staging:
            raise StaleRootfixError(
                "abandoned rootfix staging exists; pass --recover-stale"
            )
    finally:
        if owned:
            context.close()


def _seal_stage(
    stage: Path | DirectoryHandle,
    attempts: Path | DirectoryHandle,
    attempt_id: str,
    status: dict[str, Any],
    commands: dict[str, list[str]],
    metadata_path: str | None,
    outcome: str,
    exit_code: int,
    interrupted_signal: int | None,
    candidate_top: Path | None = None,
    artifact_seals: dict[str, FileSnapshot] | None = None,
) -> tuple[Path, str]:
    stage_path = stage.path if isinstance(stage, DirectoryHandle) else stage
    sealed_metadata_path = (
        f"profile-output/{metadata_path}"
        if metadata_path is not None
        else None
    )
    if rb._lstat(stage_path / "artifacts.json") is None:
        _write_attempt_artifacts(stage, commands, metadata_path)
    if rb._lstat(stage_path / "completion.json") is None:
        completion_bytes = rb.canonical_json_bytes(
            _completion(outcome, exit_code, interrupted_signal)
        )
        if isinstance(stage, DirectoryHandle):
            _atomic_write_once_at(
                stage, "completion.json", completion_bytes
            )
        else:
            rb.atomic_write_once(
                stage_path / "completion.json", completion_bytes
            )
    rb._fsync_tree(stage_path)
    validated = _validate_attempt(
        stage,
        None,
        status,
        candidate_top,
        expected_artifact_seals=artifact_seals,
    )
    if (
        validated["outcome"] != outcome
        or validated["exit_code"] != exit_code
        or validated["interrupted_signal"] != interrupted_signal
        or validated["commands"] != commands
        or validated["metadata_path"] != sealed_metadata_path
    ):
        raise RootfixError(
            "rootfix sealed attempt contradicts its established terminal"
        )
    return _publish_attempt(
        stage,
        attempts,
        attempt_id,
        validated["sha256"],
    )


def _execute_attempt_impl(
    root: Path | EvidenceContext,
    attempts: Path | DirectoryHandle,
    candidate_top: Path,
    status: dict[str, Any],
    candidate_test_blob: bytes,
    ensure_recovery_archive: Any,
    post_validate: Any,
) -> tuple[Path, str, int, ArchiveSeal]:
    owned = not isinstance(root, EvidenceContext)
    context = (
        _open_evidence_context(
            Path(root),
            create_attempts=False,
            require_attempts=True,
        )
        if owned
        else root
    )
    assert isinstance(context, EvidenceContext)
    if context.attempts is None:
        raise RootfixError("rootfix attempts directory is missing")
    attempts_handle = context.attempts
    if isinstance(attempts, DirectoryHandle):
        if (attempts.dev, attempts.ino) != (
            attempts_handle.dev,
            attempts_handle.ino,
        ):
            raise RootfixError("rootfix attempts handle binding failed")
    elif Path(attempts) != attempts_handle.path:
        raise RootfixError("rootfix attempts path binding failed")
    attempt_id = _attempt_id()
    stage_name = f".staging-{attempt_id}"
    os.mkdir(stage_name, 0o700, dir_fd=attempts_handle.fd)
    os.fsync(attempts_handle.fd)
    stage_handle = _open_child_directory(
        attempts_handle,
        stage_name,
        "rootfix staging",
    )
    stage = stage_handle.path
    marker = _running_marker_payload(
        status, attempt_id, stage.name
    )
    _atomic_write_once_at(
        context.root,
        RUNNING_NAME,
        rb.canonical_json_bytes(marker),
    )
    marker_snapshot = _load_running_marker_snapshot(context, status)
    if (
        marker_snapshot is None
        or marker_snapshot[0] != marker
    ):
        raise RootfixError(
            "rootfix running marker publication cannot be validated"
        )
    commands: dict[str, list[str]] = {}
    terminal: tuple[str, int, str | None, int | None] | None = None
    published = False
    destination: Path | None = None
    attempt_sha256: str | None = None
    exit_code = 2
    marker_seal: ArchiveSeal | None = None
    artifact_seals: dict[str, FileSnapshot] = {}
    publication_signal_mask: set[signal.Signals] | None = None
    primary_interrupt: BaseException | None = None
    catchable_signals = {
        signal.SIGINT,
        signal.SIGTERM,
        signal.SIGHUP,
    }

    def block_publication_signals() -> None:
        nonlocal publication_signal_mask
        if publication_signal_mask is not None:
            return
        try:
            publication_signal_mask = signal.pthread_sigmask(
                signal.SIG_BLOCK, catchable_signals
            )
        except (AttributeError, OSError) as error:
            raise RootfixError(
                "rootfix publication cannot mask catchable signals"
            ) from error

    try:
        try:
            exit_code, metadata_path, interrupted_signal = _run_attempt(
                stage_handle,
                candidate_top,
                status,
                candidate_test_blob,
                commands,
                artifact_seals,
            )
            profile_terminal = (
                (
                    "interrupted"
                    if interrupted_signal is not None
                    else ("pass" if exit_code == 0 else "fail")
                ),
                exit_code,
                metadata_path,
                interrupted_signal,
            )
            if interrupted_signal is not None:
                primary_interrupt = RootfixSignalInterrupt(
                    interrupted_signal
                )
            if exit_code == 0 and interrupted_signal is None:
                try:
                    post_validate()
                except (RootfixSignalInterrupt, KeyboardInterrupt):
                    terminal = profile_terminal
                    raise
            terminal = profile_terminal
            outcome = terminal[0]
            block_publication_signals()
            destination, attempt_sha256 = _seal_stage(
                stage_handle,
                attempts_handle,
                attempt_id,
                status,
                commands,
                metadata_path,
                outcome,
                exit_code,
                interrupted_signal,
                candidate_top,
                artifact_seals,
            )
            published = True
        except BaseException as error:
            if isinstance(error, RootfixEstablishedTerminalInterrupt):
                terminal = error.terminal
            if isinstance(
                error, (RootfixSignalInterrupt, KeyboardInterrupt)
            ):
                primary_interrupt = error
            stage_present = False
            try:
                current = os.stat(
                    stage_name,
                    dir_fd=attempts_handle.fd,
                    follow_symlinks=False,
                )
                stage_present = _identity(current) == (
                    stage_handle.dev,
                    stage_handle.ino,
                )
            except FileNotFoundError:
                pass
            except BaseException:
                if primary_interrupt is not None:
                    raise primary_interrupt
                raise
            if stage_present:
                if terminal is None and "code_profile" in commands:
                    # The profile has started, but no terminal has crossed
                    # the metadata/post-validation handoff.  Its partial or
                    # even complete-looking output cannot be reclassified.
                    # Keep marker + staging for explicit recovery and
                    # preserve the primary validation error or exact signal.
                    raise
                if terminal is not None:
                    (
                        outcome,
                        exit_code,
                        metadata_path,
                        interrupted_signal,
                    ) = terminal
                elif isinstance(error, RootfixSignalInterrupt):
                    interrupted_signal = error.signum
                    exit_code = 128 + interrupted_signal
                    outcome = "interrupted"
                    metadata_path = None
                elif isinstance(error, KeyboardInterrupt):
                    interrupted_signal = signal.SIGINT
                    exit_code = 128 + interrupted_signal
                    outcome = "interrupted"
                    metadata_path = None
                else:
                    interrupted_signal = None
                    exit_code = 2
                    outcome = "fail"
                    metadata_path = None
                try:
                    block_publication_signals()
                    destination, attempt_sha256 = _seal_stage(
                        stage_handle,
                        attempts_handle,
                        attempt_id,
                        status,
                        commands,
                        metadata_path,
                        outcome,
                        exit_code,
                        interrupted_signal,
                        candidate_top,
                        artifact_seals,
                    )
                    published = True
                except BaseException:
                    if primary_interrupt is not None:
                        raise primary_interrupt
                    raise
            else:
                try:
                    try:
                        published_info = os.stat(
                            attempt_id,
                            dir_fd=attempts_handle.fd,
                            follow_symlinks=False,
                        )
                    except FileNotFoundError:
                        published_info = None
                    if published_info is not None and stat.S_ISDIR(
                        published_info.st_mode
                    ):
                        stage_handle.path = (
                            attempts_handle.path / attempt_id
                        )
                        _validate_directory_handle(
                            stage_handle,
                            parent=attempts_handle,
                            name=attempt_id,
                            label="published rootfix attempt",
                        )
                        validated = _validate_attempt(
                            stage_handle,
                            None,
                            status,
                            candidate_top,
                            expected_artifact_seals=artifact_seals,
                        )
                        if terminal is not None:
                            (
                                terminal_outcome,
                                terminal_exit,
                                terminal_metadata,
                                terminal_signal,
                            ) = terminal
                            sealed_terminal_metadata = (
                                f"profile-output/{terminal_metadata}"
                                if terminal_metadata is not None
                                else None
                            )
                            if (
                                validated["outcome"]
                                != terminal_outcome
                                or validated["exit_code"]
                                != terminal_exit
                                or validated["interrupted_signal"]
                                != terminal_signal
                                or validated["commands"] != commands
                                or validated["metadata_path"]
                                != sealed_terminal_metadata
                            ):
                                raise RootfixError(
                                    "published rootfix attempt "
                                    "contradicts its established terminal"
                                )
                        destination = stage_handle.path
                        attempt_sha256 = validated["sha256"]
                        published = True
                except BaseException:
                    if primary_interrupt is not None:
                        raise primary_interrupt
                    raise
            if primary_interrupt is not None:
                raise primary_interrupt
            raise
    finally:
        try:
            try:
                if published:
                    if destination is None or attempt_sha256 is None:
                        raise RootfixError(
                            "published rootfix attempt lacks its immutable digest"
                        )
                    if publication_signal_mask is None:
                        raise RootfixError(
                            "published rootfix attempt lacks signal masking"
                        )
                    archive = ensure_recovery_archive()
                    marker_seal = _archive_validated_running_marker(
                        context,
                        archive,
                        status,
                        marker,
                        marker_snapshot,
                        attempt_sha256,
                    )
                    _validate_recovery_archive(
                        archive, status, [marker_seal]
                    )
            except BaseException:
                if primary_interrupt is None:
                    raise
        finally:
            try:
                try:
                    stage_handle.close()
                    if owned:
                        context.close()
                except BaseException:
                    if primary_interrupt is None:
                        raise
            finally:
                if publication_signal_mask is not None:
                    try:
                        signal.pthread_sigmask(
                            signal.SIG_SETMASK,
                            publication_signal_mask,
                        )
                    except RootfixSignalInterrupt:
                        if primary_interrupt is None:
                            raise
                    except (AttributeError, OSError) as error:
                        if primary_interrupt is None:
                            raise RootfixError(
                                "rootfix publication signal mask "
                                "cannot be restored"
                            ) from error
    if destination is None or attempt_sha256 is None or marker_seal is None:
        raise RootfixError("rootfix attempt publication is incomplete")
    if terminal is not None and terminal[3] is not None:
        raise RootfixSignalInterrupt(terminal[3])
    return destination, attempt_sha256, exit_code, marker_seal


def _execute_attempt(
    root: Path | EvidenceContext,
    attempts: Path | DirectoryHandle,
    candidate_top: Path,
    status: dict[str, Any],
    candidate_test_blob: bytes,
    ensure_recovery_archive: Any,
    post_validate: Any,
) -> tuple[Path, str, int, ArchiveSeal]:
    previous: dict[int, Any] = {}

    def interrupt(signum: int, _frame: Any) -> None:
        raise RootfixSignalInterrupt(signum)

    try:
        for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            previous[signum] = signal.signal(signum, interrupt)
        return _execute_attempt_impl(
            root,
            attempts,
            candidate_top,
            status,
            candidate_test_blob,
            ensure_recovery_archive,
            post_validate,
        )
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def _publish_approval_from_passing(
    root: Path | EvidenceContext,
    status: dict[str, Any],
    candidate_test: dict[str, Any],
    attempts: list[dict[str, str]],
    passing: dict[str, Any],
    baseline: RootInventorySnapshot | None = None,
) -> FileSnapshot:
    owned = not isinstance(root, EvidenceContext)
    context = (
        _open_evidence_context(
            Path(root),
            create_attempts=False,
            require_attempts=True,
        )
        if owned
        else root
    )
    assert isinstance(context, EvidenceContext)
    approval = _approval_payload(
        status,
        candidate_test,
        attempts,
        passing["attempt_id"],
        passing["sha256"],
    )
    data = rb.canonical_json_bytes(approval)
    try:
        before = _validate_evidence_objects(context, status)
        if baseline is not None:
            _validate_inventory_identity(
                baseline,
                before,
                marker="absent",
                approval="absent",
                atomic_temps="absent",
            )
        elif (
            before.marker is not None
            or before.approval is not None
            or before.atomic_temps
        ):
            raise RootfixError(
                "rootfix approval cannot be published over active evidence"
            )
        _atomic_write_once_at(context.root, APPROVAL_NAME, data)
        after = _validate_evidence_objects(context, status)
        if (
            after.marker is not None
            or after.atomic_temps
            or after.approval is None
            or after.approval.data != data
            or before.root_identity != after.root_identity
            or before.attempts_identity != after.attempts_identity
        ):
            raise RootfixError(
                "rootfix approval publication cannot be validated"
            )
        return after.approval
    finally:
        if owned:
            context.close()


def run_gate(
    candidate_repo: Path,
    target_repo: Path,
    bundle: str,
    *,
    retry_failed: bool = False,
    recover_stale: bool = False,
) -> dict[str, Any]:
    bundle_path = rb._resolve_bundle_path(candidate_repo, bundle)
    with rb.bundle_lock(bundle_path, exclusive=True):
        status = rb._validate_bundle_locked(
            candidate_repo, bundle_path, check_clean=True
        )
        _validate_bundle_status(status)
        _, candidate_top, candidate_test, candidate_test_blob = _validate_topology(
            candidate_repo, target_repo, status
        )
        status = _bind_runtime_status(
            status, candidate_top, candidate_test
        )
        root = _evidence_path(candidate_top, status["bundle_id"], create=True)
        context = _open_evidence_context(root, create_attempts=True)
        if context.attempts is None:
            context.close()
            raise RootfixError("rootfix attempts directory cannot be opened")

        def validate_current_recovery_archive() -> tuple[
            Path | None, list[Path]
        ]:
            return _validate_current_recovery_archive(
                candidate_top, status
            )

        def ensure_recovery_archive(
            required: tuple[ArchiveSeal, ...] | list[ArchiveSeal] = (),
        ) -> Path:
            archive, _ = validate_current_recovery_archive()
            if archive is None:
                archive = _recovery_archive_path(
                    candidate_top,
                    status["bundle_id"],
                    create=True,
                )
                assert archive is not None
            _validate_recovery_archive(archive, status, required)
            return archive
        try:
            required_archive: list[ArchiveSeal] = []
            recovery_archive, _ = validate_current_recovery_archive()
            initial = _validate_evidence_objects(
                context,
                status,
                allow_atomic_temps=recover_stale,
            )
            marker_snapshot = _marker_snapshot_from_file(
                initial.marker, status
            )
            if recover_stale:
                _, initial_staging = _attempt_directory_state(
                    context.attempts
                )
                if (
                    initial.atomic_temps
                    or marker_snapshot is not None
                    or initial_staging
                ):
                    recovery_archive = ensure_recovery_archive()
                required_archive.extend(
                    _recover_stale(
                        context,
                        context.attempts,
                        status,
                        initial.atomic_temps,
                        recovery_archive,
                        marker_snapshot,
                        initial,
                    )
                )
            else:
                _require_no_stale_state(
                    context,
                    context.attempts,
                    status,
                    initial,
                )
            boundary = _validate_evidence_objects(context, status)
            _validate_inventory_identity(
                initial,
                boundary,
                marker=("removed" if recover_stale else "same"),
                approval="same",
                atomic_temps=("absent" if recover_stale else "same"),
            )
            archive_path, archive_objects = (
                validate_current_recovery_archive()
            )
            _validate_recovery_archive(
                archive_path, status, required_archive
            )
            if boundary.approval is not None:
                result = _validate_approval(
                    context,
                    status,
                    candidate_test,
                    archive_objects,
                    boundary.approval,
                    candidate_top,
                )
                archive_path, archive_objects = (
                    validate_current_recovery_archive()
                )
                _validate_recovery_archive(
                    archive_path, status, required_archive
                )
                result = _validate_approval(
                    context,
                    status,
                    candidate_test,
                    archive_objects,
                    boundary.approval,
                    candidate_top,
                )
                return result

            attempt_seals = _sealed_attempt_digests(archive_objects)
            records, passing = _published_attempts(
                context.attempts,
                status,
                candidate_top,
                attempt_seals,
            )
            _validate_attempt_marker_conservation(
                records, archive_objects
            )
            preexisting_records = [dict(record) for record in records]
            if passing is not None:
                approval_snapshot = _publish_approval_from_passing(
                    context,
                    status,
                    candidate_test,
                    records,
                    passing,
                    boundary,
                )
                archive_path, archive_objects = (
                    validate_current_recovery_archive()
                )
                _validate_recovery_archive(
                    archive_path, status, required_archive
                )
                result = _validate_approval(
                    context,
                    status,
                    candidate_test,
                    archive_objects,
                    approval_snapshot,
                    candidate_top,
                )
                archive_path, archive_objects = (
                    validate_current_recovery_archive()
                )
                _validate_recovery_archive(
                    archive_path, status, required_archive
                )
                return _validate_approval(
                    context,
                    status,
                    candidate_test,
                    archive_objects,
                    approval_snapshot,
                    candidate_top,
                )
            if records and not retry_failed:
                raise RootfixError(
                    "failed rootfix evidence exists; pass --retry-failed explicitly"
                )

            def post_validate() -> None:
                post_status = rb._validate_bundle_locked(
                    candidate_repo, bundle_path, check_clean=True
                )
                _validate_bundle_status(post_status)
                (
                    _,
                    _,
                    post_candidate_test,
                    post_candidate_blob,
                ) = _validate_topology(
                    candidate_repo, target_repo, post_status
                )
                post_status = _bind_runtime_status(
                    post_status, candidate_top, post_candidate_test
                )
                if (
                    post_status != status
                    or post_candidate_test != candidate_test
                    or post_candidate_blob != candidate_test_blob
                ):
                    raise RootfixError(
                        "P2, F2, bundle or committed test changed during the gate"
                    )
                _validate_evidence_context(context)
                archive_path, _ = validate_current_recovery_archive()
                _validate_recovery_archive(
                    archive_path, status, required_archive
                )

            attempt_error: BaseException | None = None
            attempt_result: tuple[
                Path, str, int, ArchiveSeal
            ] | None = None
            try:
                attempt_result = _execute_attempt(
                    context,
                    context.attempts,
                    candidate_top,
                    status,
                    candidate_test_blob,
                    lambda: ensure_recovery_archive(required_archive),
                    post_validate,
                )
            except BaseException as error:
                attempt_error = error
            if attempt_result is not None:
                required_archive.append(attempt_result[3])
            archive_path, archive_objects = (
                validate_current_recovery_archive()
            )
            _validate_recovery_archive(
                archive_path, status, required_archive
            )
            post_attempt = _validate_evidence_objects(
                context,
                status,
                allow_atomic_temps=attempt_error is not None,
            )
            _validate_inventory_identity(
                boundary,
                post_attempt,
                marker=("any" if attempt_error is not None else "absent"),
                approval="absent",
                atomic_temps=(
                    "any" if attempt_error is not None else "absent"
                ),
            )
            attempt_seals = _sealed_attempt_digests(archive_objects)
            records, passing = _published_attempts(
                context.attempts,
                status,
                candidate_top,
                attempt_seals,
                allow_staging=attempt_error is not None,
            )
            _require_attempt_history(
                preexisting_records,
                records,
            )
            _validate_attempt_marker_conservation(
                records, archive_objects
            )
            if attempt_error is not None:
                raise attempt_error.with_traceback(
                    attempt_error.__traceback__
                )
            if attempt_result is None:
                raise RootfixError(
                    "rootfix attempt returned without a terminal result"
                )
            exit_code = attempt_result[2]
            if exit_code:
                raise RootfixError(
                    f"rootfix focused verification failed with exit {exit_code}"
                )
            if passing is None:
                raise RootfixError(
                    "passing rootfix attempt was not published"
                )
            approval_snapshot = _publish_approval_from_passing(
                context,
                status,
                candidate_test,
                records,
                passing,
                boundary,
            )
            archive_path, archive_objects = (
                validate_current_recovery_archive()
            )
            _validate_recovery_archive(
                archive_path, status, required_archive
            )
            result = _validate_approval(
                context,
                status,
                candidate_test,
                archive_objects,
                approval_snapshot,
                candidate_top,
            )
            archive_path, archive_objects = (
                validate_current_recovery_archive()
            )
            _validate_recovery_archive(
                archive_path, status, required_archive
            )
            return _validate_approval(
                context,
                status,
                candidate_test,
                archive_objects,
                approval_snapshot,
                candidate_top,
            )
        finally:
            context.close()


def check_gate(
    candidate_repo: Path,
    target_repo: Path,
    bundle: str,
) -> dict[str, Any]:
    bundle_path = rb._resolve_bundle_path(candidate_repo, bundle)
    with rb.bundle_lock(bundle_path, exclusive=False):
        status = rb._validate_bundle_locked(
            candidate_repo, bundle_path, check_clean=True
        )
        _validate_bundle_status(status)
        _, candidate_top, candidate_test, _ = _validate_topology(
            candidate_repo, target_repo, status
        )
        status = _bind_runtime_status(
            status, candidate_top, candidate_test
        )
        root = _evidence_path(candidate_top, status["bundle_id"], create=False)
        context = _open_evidence_context(
            root,
            create_attempts=False,
            require_attempts=True,
        )
        try:
            inventory = _validate_evidence_objects(context, status)
            _require_no_stale_state(
                context,
                context.attempts,
                status,
                inventory,
            )
            _, archive_objects = _validate_current_recovery_archive(
                candidate_top, status
            )
            result = _validate_approval(
                context,
                status,
                candidate_test,
                archive_objects,
                inventory.approval,
                candidate_top,
            )
            _, archive_objects = _validate_current_recovery_archive(
                candidate_top, status
            )
            return _validate_approval(
                context,
                status,
                candidate_test,
                archive_objects,
                inventory.approval,
                candidate_top,
            )
        finally:
            context.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("run", "check"):
        child = subparsers.add_parser(name)
        child.add_argument("--repo", required=True, type=Path)
        child.add_argument("--target-repo", required=True, type=Path)
        child.add_argument("--bundle", required=True)
        if name == "run":
            child.add_argument("--retry-failed", action="store_true")
            child.add_argument("--recover-stale", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        # Repository code is bootstrapped only from the checkout containing
        # this installed gate.  A caller-supplied --target-repo is validated
        # later and may never select code to execute before that boundary.
        _load_trusted_repository_modules(SCRIPT_DIR.parents[1])
        if args.command == "run":
            result = run_gate(
                args.repo,
                args.target_repo,
                args.bundle,
                retry_failed=args.retry_failed,
                recover_stale=args.recover_stale,
            )
        else:
            result = check_gate(args.repo, args.target_repo, args.bundle)
    except RootfixSignalInterrupt as error:
        exit_code = 128 + error.signum
        result = {
            "approved": False,
            "state": "ROOTFIX_INTERRUPTED",
            "exit_code": exit_code,
            "error": (
                "rootfix gate interrupted by "
                f"{signal.Signals(error.signum).name}"
            ),
        }
        data = (
            rb.canonical_json_bytes(result)
            if rb is not None
            else json.dumps(
                result,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        sys.stdout.buffer.write(data)
        return exit_code
    except KeyboardInterrupt:
        result = {
            "approved": False,
            "state": "ROOTFIX_INTERRUPTED",
            "exit_code": 130,
            "error": "rootfix gate interrupted",
        }
        data = (
            rb.canonical_json_bytes(result)
            if rb is not None
            else json.dumps(
                result,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
            + b"\n"
        )
        sys.stdout.buffer.write(data)
        return 130
    except Exception as error:
        result = {
            "approved": False,
            "state": "ROOTFIX_NO_GO",
            "exit_code": 2,
            "error": str(error),
        }
        data = json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8") + b"\n"
        sys.stdout.buffer.write(data)
        return 2
    sys.stdout.buffer.write(rb.canonical_json_bytes(result))
    return 0


if __name__ != "__main__":
    sys.path.insert(0, os.fspath(SCRIPT_DIR))
    import review_bundle as rb  # noqa: E402
    _TRUSTED_SOURCE_BLOBS = {
        I18N_SHARED_PATH: (SCRIPT_DIR / "i18n_shared.py").read_bytes(),
        BUNDLE_PATH: (SCRIPT_DIR / "review_bundle.py").read_bytes(),
        VERIFIER_PATH: (
            SCRIPT_DIR.parents[1] / VERIFIER_PATH
        ).read_bytes(),
        PROFILE_CONTRACT_PATH: (
            SCRIPT_DIR.parents[1] / PROFILE_CONTRACT_PATH
        ).read_bytes(),
    }
else:
    raise SystemExit(main())
