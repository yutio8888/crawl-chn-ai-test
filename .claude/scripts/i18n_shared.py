#!/usr/bin/env python3
"""Shared utilities for i18n tools — unified source.txt parser and helpers."""

from __future__ import annotations

import ctypes
import ctypes.util
import contextvars
import fnmatch
import functools
import hashlib
import json
import os
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
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
    git_mode: Optional[str] = None
    git_blob_oid: Optional[str] = None


@dataclass(frozen=True)
class _GitTreeEntry:
    mode: str
    object_type: str
    object_id: str


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


def _read_regular_worktree_file(
    path: Path,
    audit_root: Path,
    *,
    with_mode: bool = False,
) -> bytes | tuple[str, bytes]:
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
        data = b"".join(chunks)
        mode = "100755" if opened.st_mode & 0o111 else "100644"
        return (mode, data) if with_mode else data
    finally:
        os.close(fd)


_AUDIT_COMMIT_FROM_ENV = object()


def _known_system_temp_alias(path: Path) -> Path:
    """Normalize only macOS's fixed system temp aliases."""
    if sys.platform != "darwin":
        return path
    for alias, target in (
        (Path("/tmp"), Path("/private/tmp")),
        (Path("/var"), Path("/private/var")),
    ):
        try:
            relative = path.relative_to(alias)
            link_target = os.readlink(alias)
        except (ValueError, OSError):
            continue
        expected = os.fspath(target).lstrip("/")
        if link_target in (expected, os.fspath(target)):
            return target / relative
    return path


def _external_development_root(path: Path) -> Path:
    """Choose a lexical trusted anchor without resolving the input path."""
    candidates = [
        _known_system_temp_alias(
            Path(os.path.abspath(tempfile.gettempdir()))
        ),
        _known_system_temp_alias(
            Path(os.path.abspath(os.fspath(Path.cwd())))
        ),
    ]
    containing = []
    for candidate in candidates:
        try:
            path.relative_to(candidate)
        except ValueError:
            continue
        containing.append(candidate)
    # Outside the two explicit development anchors, start at the filesystem
    # anchor so every parent component is checked rather than trusting an
    # already-traversed arbitrary parent path.
    root = max(
        containing,
        key=lambda value: len(value.parts),
        default=Path(path.anchor),
    )
    try:
        info = os.lstat(root)
    except OSError as error:
        raise AuditInputError(
            f"external development root cannot be inspected: {root}"
        ) from error
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise AuditInputError(
            f"external development root is not a real directory: {root}"
        )
    return root


class AuditSnapshot:
    """Frozen, cached production inputs for one audit invocation.

    Bound verification discovers paths from the exact candidate Git tree and
    reads every unique blob object at most once. Development mode discovers
    real worktree directories without following symlinks and reads every file
    through one checked descriptor. Both modes cache discovery and content so
    later backing-path changes cannot alter an already observed input.
    """

    def __init__(
        self,
        audit_root: os.PathLike[str] | str,
        audit_commit: object | Optional[str] = _AUDIT_COMMIT_FROM_ENV,
        *,
        require_head: bool = True,
    ) -> None:
        root = Path(os.path.abspath(os.fspath(audit_root)))
        try:
            resolved_root = root.resolve(strict=True)
        except OSError as error:
            raise AuditInputError(
                f"audit root cannot be resolved: {root}"
            ) from error
        if not resolved_root.is_dir():
            raise AuditInputError(f"audit root is not a directory: {root}")
        if _git_toplevel(resolved_root, "audit root") != resolved_root:
            raise AuditInputError(
                f"audit root is not its Git top-level: {resolved_root}"
            )
        self.root = resolved_root
        if audit_commit is _AUDIT_COMMIT_FROM_ENV:
            audit_commit = os.environ.get("ZH_VERIFY_AUDIT_COMMIT")
        if audit_commit is not None and not isinstance(audit_commit, str):
            raise AuditInputError("audit commit must be a string or None")
        self.audit_commit = audit_commit
        self._tree_entries: dict[str, _GitTreeEntry] = {}
        self._inputs: dict[str, AuditInput] = {}
        self._blob_cache: dict[str, bytes] = {}
        self._external_inputs: dict[str, AuditInput] = {}
        self._discoveries: dict[
            tuple[str, tuple[str, ...], bool], tuple[str, ...]
        ] = {}
        self._external_discoveries: dict[
            tuple[str, tuple[str, ...], bool], tuple[Path, ...]
        ] = {}

        if self.audit_commit is not None:
            if not FULL_GIT_OID_RE.fullmatch(self.audit_commit):
                raise AuditInputError(
                    "ZH_VERIFY_AUDIT_COMMIT must be a full lowercase object ID"
                )
            resolved = _run_git_bytes(
                self.root,
                "rev-parse",
                "--verify",
                f"{self.audit_commit}^{{commit}}",
            ).decode("ascii", errors="strict").strip()
            if resolved != self.audit_commit:
                raise AuditInputError(
                    "ZH_VERIFY_AUDIT_COMMIT must be its complete object ID"
                )
            if require_head:
                head = _run_git_bytes(
                    self.root,
                    "rev-parse",
                    "--verify",
                    "HEAD^{commit}",
                ).decode("ascii", errors="strict").strip()
                if self.audit_commit != head:
                    raise AuditInputError(
                        "ZH_VERIFY_AUDIT_COMMIT does not equal audit root HEAD: "
                        f"{self.audit_commit} != {head}"
                    )
            self._load_git_tree()

    @property
    def bound(self) -> bool:
        return self.audit_commit is not None

    def _load_git_tree(self) -> None:
        assert self.audit_commit is not None
        raw = _run_git_bytes(
            self.root,
            "ls-tree",
            "-r",
            "-t",
            "-z",
            "--full-tree",
            self.audit_commit,
        )
        entries: dict[str, _GitTreeEntry] = {}
        for record in (value for value in raw.split(b"\0") if value):
            try:
                header, raw_path = record.split(b"\t", 1)
                mode, object_type, object_id = (
                    header.decode("ascii", errors="strict").split(" ")
                )
                relative = raw_path.decode("utf-8", errors="strict")
            except (UnicodeDecodeError, ValueError) as error:
                raise AuditInputError("invalid Git tree metadata") from error
            relative = _normalized_git_path(relative)
            if relative in entries:
                raise AuditInputError(
                    f"duplicate path in Git tree: {relative}"
                )
            if not FULL_GIT_OID_RE.fullmatch(object_id):
                raise AuditInputError(
                    f"Git tree contains a non-full object ID: {relative}"
                )
            entries[relative] = _GitTreeEntry(
                mode=mode,
                object_type=object_type,
                object_id=object_id,
            )
        self._tree_entries = entries

    def _relative(self, logical_path: os.PathLike[str] | str) -> tuple[str, Path]:
        return _review_relative_path(self.root, logical_path)

    @staticmethod
    def _decode_input(
        *,
        audit_commit: Optional[str],
        relative: str,
        data: bytes,
        mode: Optional[str],
        blob_oid: Optional[str],
        logical: Optional[str] = None,
    ) -> AuditInput:
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            raise AuditInputError(
                f"review input is not strict UTF-8: {relative}"
            ) from error
        return AuditInput(
            audit_commit=audit_commit,
            logical_path=logical or relative,
            relative_path=relative,
            bytes=data,
            text=text,
            sha256=hashlib.sha256(data).hexdigest(),
            git_mode=mode,
            git_blob_oid=blob_oid,
        )

    def read(
        self,
        logical_path: os.PathLike[str] | str,
        *,
        allow_external_unbound: bool = False,
    ) -> AuditInput:
        """Return one cached regular UTF-8 input from this snapshot."""
        try:
            relative, worktree_path = self._relative(logical_path)
        except AuditInputError:
            if self.bound or not allow_external_unbound:
                raise
            diagnostic_path = os.path.normpath(
                os.path.abspath(os.fspath(logical_path))
            )
            worktree_path = _known_system_temp_alias(
                Path(diagnostic_path)
            )
            identity = os.path.normcase(os.fspath(worktree_path))
            cached_external = self._external_inputs.get(identity)
            if cached_external is not None:
                return cached_external
            mode, data = _read_regular_worktree_file(
                worktree_path,
                _external_development_root(worktree_path),
                with_mode=True,
            )
            loaded_external = self._decode_input(
                audit_commit=None,
                relative=os.path.normcase(os.fspath(worktree_path)),
                data=data,
                mode=mode,
                blob_oid=None,
                logical=diagnostic_path,
            )
            self._external_inputs[identity] = loaded_external
            return loaded_external
        cached = self._inputs.get(relative)
        if cached is not None:
            return cached

        if self.bound:
            entry = self._tree_entries.get(relative)
            if entry is None:
                raise AuditInputError(
                    f"Git blob is missing: {self.audit_commit}:{relative}"
                )
            if (
                entry.object_type != "blob"
                or entry.mode not in ("100644", "100755")
            ):
                raise AuditInputError(
                    "Git entry is not a regular file: "
                    f"{self.audit_commit}:{relative}"
                )
            data = self._blob_cache.get(entry.object_id)
            if data is None:
                data = _run_git_bytes(
                    self.root, "cat-file", "blob", entry.object_id
                )
                self._blob_cache[entry.object_id] = data
            loaded = self._decode_input(
                audit_commit=self.audit_commit,
                relative=relative,
                data=data,
                mode=entry.mode,
                blob_oid=entry.object_id,
            )
        else:
            mode, data = _read_regular_worktree_file(
                worktree_path, self.root, with_mode=True
            )
            loaded = self._decode_input(
                audit_commit=None,
                relative=relative,
                data=data,
                mode=mode,
                blob_oid=None,
            )
        self._inputs[relative] = loaded
        return loaded

    def text(
        self,
        logical_path: os.PathLike[str] | str,
        *,
        allow_external_unbound: bool = False,
    ) -> str:
        return self.read(
            logical_path,
            allow_external_unbound=allow_external_unbound,
        ).text

    def bytes(
        self,
        logical_path: os.PathLike[str] | str,
        *,
        allow_external_unbound: bool = False,
    ) -> bytes:
        return self.read(
            logical_path,
            allow_external_unbound=allow_external_unbound,
        ).bytes

    def sha256(
        self,
        logical_path: os.PathLike[str] | str,
        *,
        allow_external_unbound: bool = False,
    ) -> str:
        return self.read(
            logical_path,
            allow_external_unbound=allow_external_unbound,
        ).sha256

    def _bound_directory_exists(self, relative_directory: str) -> bool:
        if relative_directory == ".":
            return True
        entry = self._tree_entries.get(relative_directory)
        return bool(
            entry
            and entry.object_type == "tree"
            and entry.mode == "040000"
        )

    def _development_directory(self, directory: Path) -> None:
        current = self.root
        try:
            parts = directory.relative_to(self.root).parts
        except ValueError as error:
            raise AuditInputError(
                f"review directory is outside audit root: {directory}"
            ) from error
        for part in parts:
            current = current / part
            try:
                info = os.lstat(current)
            except OSError as error:
                raise AuditInputError(
                    f"review directory cannot be inspected: {current}"
                ) from error
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise AuditInputError(
                    f"review directory is not a real directory: {current}"
                )

    @staticmethod
    def _matches(
        relative_to_directory: str,
        patterns: tuple[str, ...],
        recursive: bool,
    ) -> bool:
        if not recursive and "/" in relative_to_directory:
            return False
        return any(
            fnmatch.fnmatchcase(
                PurePosixPath(relative_to_directory).name,
                pattern,
            )
            for pattern in patterns
        )

    def glob(
        self,
        directory: os.PathLike[str] | str,
        pattern: str | tuple[str, ...] | list[str],
        *,
        recursive: bool = False,
        allow_external_unbound: bool = False,
    ) -> tuple[Path, ...]:
        """Discover and preload matching regular files deterministically."""
        patterns = (
            (pattern,) if isinstance(pattern, str) else tuple(pattern)
        )
        if (
            not patterns
            or any(not value for value in patterns)
            or len(patterns) != len(set(patterns))
        ):
            raise AuditInputError(
                "review discovery patterns must be non-empty and unique"
            )
        try:
            relative_directory, worktree_directory = self._relative(directory)
        except AuditInputError:
            if self.bound or not allow_external_unbound:
                raise
            worktree_directory = _known_system_temp_alias(Path(os.path.normpath(
                os.path.abspath(os.fspath(directory))
            )))
            external_key = (
                os.path.normcase(os.fspath(worktree_directory)),
                patterns,
                recursive,
            )
            cached_external = self._external_discoveries.get(external_key)
            if cached_external is not None:
                return cached_external
            try:
                info = os.lstat(worktree_directory)
            except OSError as error:
                raise AuditInputError(
                    "external development directory cannot be inspected: "
                    f"{worktree_directory}"
                ) from error
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise AuditInputError(
                    "external development directory is not real: "
                    f"{worktree_directory}"
                )
            pending = [worktree_directory]
            external_selected: list[Path] = []
            while pending:
                current = pending.pop()
                try:
                    entries = sorted(
                        os.scandir(current), key=lambda item: item.name
                    )
                except OSError as error:
                    raise AuditInputError(
                        f"external directory cannot be enumerated: {current}"
                    ) from error
                for entry in entries:
                    path = Path(entry.path)
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError as error:
                        raise AuditInputError(
                            "external directory entry cannot be inspected: "
                            f"{path}"
                        ) from error
                    child = path.relative_to(worktree_directory).as_posix()
                    if stat.S_ISLNK(info.st_mode):
                        raise AuditInputError(
                            f"external directory contains a symlink: {path}"
                        )
                    if stat.S_ISDIR(info.st_mode):
                        if recursive:
                            pending.append(path)
                        continue
                    if not self._matches(child, patterns, recursive):
                        continue
                    if not stat.S_ISREG(info.st_mode):
                        raise AuditInputError(
                            "matching external input is not regular: "
                            f"{path}"
                        )
                    external_selected.append(path)
            external_selected.sort()
            for path in external_selected:
                self.read(
                    path,
                    allow_external_unbound=True,
                )
            frozen_external = tuple(external_selected)
            self._external_discoveries[external_key] = frozen_external
            return frozen_external
        key = (relative_directory, patterns, recursive)
        cached = self._discoveries.get(key)
        if cached is not None:
            return tuple(self.root / relative for relative in cached)

        prefix = "" if relative_directory == "." else (
            relative_directory + "/"
        )
        selected: list[str] = []
        if self.bound:
            if not self._bound_directory_exists(relative_directory):
                raise AuditInputError(
                    "Git directory is missing or non-directory: "
                    f"{self.audit_commit}:{relative_directory}"
                )
            for relative, entry in sorted(self._tree_entries.items()):
                if not relative.startswith(prefix):
                    continue
                child = relative[len(prefix):]
                if not child:
                    continue
                if not recursive and "/" in child:
                    continue
                if (
                    entry.object_type == "tree"
                    and entry.mode == "040000"
                ):
                    continue
                if (
                    entry.object_type != "blob"
                    or entry.mode not in ("100644", "100755")
                ):
                    raise AuditInputError(
                        "Git discovery contains a non-regular entry: "
                        f"{self.audit_commit}:{relative}"
                    )
                if self._matches(child, patterns, recursive):
                    selected.append(relative)
        else:
            self._development_directory(worktree_directory)
            pending = [worktree_directory]
            while pending:
                current = pending.pop()
                try:
                    entries = sorted(
                        os.scandir(current), key=lambda item: item.name
                    )
                except OSError as error:
                    raise AuditInputError(
                        f"review directory cannot be enumerated: {current}"
                    ) from error
                for entry in entries:
                    path = Path(entry.path)
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except OSError as error:
                        raise AuditInputError(
                            f"review directory entry cannot be inspected: {path}"
                        ) from error
                    child = path.relative_to(worktree_directory).as_posix()
                    if stat.S_ISLNK(info.st_mode):
                        raise AuditInputError(
                            f"review directory contains a symlink: {path}"
                        )
                    if stat.S_ISDIR(info.st_mode):
                        if recursive:
                            pending.append(path)
                        continue
                    if not self._matches(child, patterns, recursive):
                        continue
                    if not stat.S_ISREG(info.st_mode):
                        raise AuditInputError(
                            "matching review input is not a regular file: "
                            f"{path}"
                        )
                    selected.append(path.relative_to(self.root).as_posix())
            selected.sort()

        frozen = tuple(selected)
        for relative in frozen:
            self.read(relative)
        self._discoveries[key] = frozen
        return tuple(self.root / relative for relative in frozen)

    def input_manifest(self) -> dict:
        """Return path-normalized content metadata without clone-local paths."""
        return {
            "schema": "dcss-zh-audit-input-manifest-v1",
            "inputs": [
                {
                    "path": relative,
                    "mode": value.git_mode,
                    "sha256": value.sha256,
                }
                for relative, value in sorted(self._inputs.items())
            ],
            "discoveries": [
                {
                    "directory": directory,
                    "patterns": list(patterns),
                    "recursive": recursive,
                    "paths": list(paths),
                }
                for (directory, patterns, recursive), paths
                in sorted(self._discoveries.items())
            ],
        }

    def input_manifest_sha256(self) -> str:
        encoded = json.dumps(
            self.input_manifest(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def metadata(self) -> dict:
        return {
            "audit_commit": self.audit_commit,
            "input_manifest_sha256": self.input_manifest_sha256(),
            "input_manifest": self.input_manifest(),
        }


_BOUND_AUDIT_SNAPSHOTS: dict[tuple[str, str], AuditSnapshot] = {}
_ACTIVE_AUDIT_SNAPSHOT: contextvars.ContextVar[Optional[AuditSnapshot]] = (
    contextvars.ContextVar("active_audit_snapshot", default=None)
)


def get_audit_snapshot(
    audit_root: os.PathLike[str] | str,
) -> AuditSnapshot:
    """Return the active invocation snapshot or an exact bound singleton.

    Bound snapshots are immutable per candidate commit and may be shared for
    the process lifetime. Unbound snapshots are deliberately fresh outside an
    invocation scope so one development invocation cannot inherit another
    invocation's cached backing files.
    """
    root = Path(audit_root).resolve()
    commit = os.environ.get("ZH_VERIFY_AUDIT_COMMIT")
    active = _ACTIVE_AUDIT_SNAPSHOT.get()
    if active is not None:
        if active.root != root or active.audit_commit != commit:
            raise AuditInputError(
                "active audit snapshot does not match requested root/commit"
            )
        return active
    if commit is None:
        return AuditSnapshot(root, None)
    key = (os.fspath(root), commit)
    bound = _BOUND_AUDIT_SNAPSHOTS.get(key)
    if bound is None:
        bound = AuditSnapshot(root, commit)
        _BOUND_AUDIT_SNAPSHOTS[key] = bound
    return bound


@contextmanager
def audit_snapshot_scope(
    audit_root: os.PathLike[str] | str,
):
    """Share one frozen snapshot across a top-level audit invocation."""
    root = Path(audit_root).resolve()
    commit = os.environ.get("ZH_VERIFY_AUDIT_COMMIT")
    active = _ACTIVE_AUDIT_SNAPSHOT.get()
    if active is not None:
        if active.root != root or active.audit_commit != commit:
            raise AuditInputError(
                "nested audit snapshot scope changed root or commit"
            )
        yield active
        return
    snapshot = get_audit_snapshot(root)
    token = _ACTIVE_AUDIT_SNAPSHOT.set(snapshot)
    try:
        yield snapshot
    finally:
        _ACTIVE_AUDIT_SNAPSHOT.reset(token)


def audit_snapshot_invocation(audit_root):
    """Decorate one top-level audit entry point with a frozen input scope."""
    def decorate(function):
        @functools.wraps(function)
        def scoped(*args, **kwargs):
            with audit_snapshot_scope(audit_root):
                return function(*args, **kwargs)
        return scoped
    return decorate


def load_review_input(
    audit_root: os.PathLike[str] | str,
    logical_path: os.PathLike[str] | str,
    *,
    snapshot: Optional[AuditSnapshot] = None,
) -> AuditInput:
    """Load one ledger from a frozen candidate/development snapshot."""
    active = snapshot or get_audit_snapshot(audit_root)
    requested_root = Path(audit_root).resolve()
    if active.root != requested_root:
        raise AuditInputError(
            "review input snapshot root does not match requested audit root"
        )
    return active.read(logical_path)


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


# Frozen baseline of the pre-existing tree-sitter-cpp false positives in
# crawl-ref/source/directn.cc, caused by preprocessor conditionals splitting
# C++ constructs (if/else chains, class inheritance lists, ...).
#
# The exemption is bound to the real ERROR/missing nodes parsed from the
# baseline file itself: every entry is (physical line, node kind, text
# anchor). For ERROR nodes the anchor is the node's own text (matched as a
# prefix, since a later grammar may absorb more text into the node); for
# missing nodes the node text is empty, so the anchor is the missing token
# (node.type), the only text a missing node carries. The list below was
# probed from the baseline directn.cc (10 ERROR/missing nodes total; the
# three directive-fragment ERROR nodes at lines 2439/2441/2443 are exempted
# by the separate '#'-directive rule below, not by this list):
#
#   622  missing '}'   - #ifndef USE_TILE_LOCAL splits the else clause from
#                        its if; the '}' before the else body is reported
#                        missing on the 'str = "         " + fss[j]...' line
#   626  ERROR '}'     - orphan '}' closing the else body
#   1941 ERROR 'else'  - #ifdef DEBUG_DIAGNOSTICS splits a dangling else
#                        from its if, leaving an orphan 'else' node
#   2446 ERROR 'UIDir..' - #ifdef USE_TILE_LOCAL splits the class
#                        inheritance list; the constructor line right after
#                        #endif is mis-parsed as a labeled statement
#   2447 missing ';'   - the following member-init line then lacks a ';'
#   3721 ERROR '*' / '.' - unique_ptr dereference *env.level_vaults[...]
#                        inside #ifdef DEBUG_DIAGNOSTICS is mis-parsed as a
#                        declarator
#
# File identity is bound by the baseline content SHA-256: the scanner entry
# points do not thread the file path into has_relevant_parse_error(), so the
# only sound file binding available there is the exact baseline bytes. This
# is strictly stronger than a path match: a path-identical but modified
# directn.cc is never exempted, while a byte-identical copy (the directory
# entry scenario) is, which is exactly the identity the frozen pairs belong
# to. Generic text such as '}' or 'else' at a switch point in any other
# content therefore still fails closed.
#
# A node is exempt only when all of the following hold:
#   1. sha256(source) == the frozen baseline sha256 (the node's file is the
#      frozen baseline file);
#   2. the node's (line, kind, text anchor) matches a frozen pair exactly;
#   3. the node's line is a preprocessor switch point (inside a conditional
#      body or within _PREPROC_SWITCH_WINDOW lines after its #endif), the
#      retained window mechanism.
# Every other parse error still fails closed.
_PREPROCESSOR_BASELINE_DIRECTN = {
    "sha256": "85881f8e4ef82f7e92647655ab87390ab793b4066ee3f9b5e069c9d192361f5b",
    "nodes": frozenset({
        (622, "missing", b"}"),
        (626, "ERROR", b"}"),
        (1941, "ERROR", b"else"),
        (2446, "ERROR",
         b"UIDirectionChooserView(direction_chooser& dc) :"),
        (2447, "missing", b";"),
        (3721, "ERROR", b"*"),
        (3721, "ERROR", b"."),
    }),
}

# Window (in lines) after an #endif within which a matching frozen baseline
# node is still considered a preprocessor switch-point false positive.
_PREPROC_SWITCH_WINDOW = 4

# tree-sitter-cpp cannot be the directive source here: in the exact regions
# this exemption exists for (a conditional splitting a class inheritance
# list, an if/else chain, ...), the parser's ERROR recovery swallows the
# directive lines and emits no preproc node. Probing the bundled grammar on
# crawl-ref/source/directn.cc found only 42 preproc_if/preproc_ifdef/
# preproc_ifndef nodes for 87 actual conditional directives, including no
# node for the #ifdef USE_TILE_LOCAL at line 2439 whose post-#endif window
# covers the frozen baseline lines 2446/2447. Directive discovery therefore
# uses a complete phase-2 lexer (backslash-newline splicing, raw-string
# prefixes/delimiters/terminators, continuation-aware comments, string and
# char literals) instead of tree-sitter nodes.
_PREPROCESSOR_CONDITIONAL_KEYWORDS = frozenset({
    b"if", b"ifdef", b"ifndef", b"elif", b"else", b"endif",
})
_RAW_STRING_PREFIXES = (b"R\"", b"u8R\"", b"uR\"", b"UR\"", b"LR\"")
_RAW_STRING_DELIMITER_MAX = 16


def _is_identifier_byte(ch: int) -> bool:
    """ASCII identifier character: _ [0-9] [A-Z] [a-z]."""
    return (ch == 0x5F
            or 0x30 <= ch <= 0x39
            or 0x41 <= ch <= 0x5A
            or 0x61 <= ch <= 0x7A)


def _phase2_splice(source: bytes):
    """Delete backslash-newline splices (C++ translation phases 1 and 2).

    Returns (logical, line_of) where `logical` is the spliced, normalized
    translation unit and ``line_of[i]`` is the 1-indexed physical line
    number of ``logical[i]`` in the original file. A splice is a backslash
    byte immediately followed by a new-line; LF (\\n), CRLF (\\r\\n), and
    bare CR (\\r) terminators are all recognized. Splices may occur
    anywhere — inside comments, string literals, or raw-string prefixes,
    delimiters, and terminators — exactly as the standard's phase-2
    deletion requires, so every later lexical check runs on the assembled
    logical line.

    Phase-1 end-of-line normalization is applied at the same time: LF,
    CRLF, and bare CR are all end-of-line indicators (C++ [lex.phases] p1
    introduces new-line characters for end-of-line indicators), so every
    EOL sequence becomes a single '\\n' in the output and increments the
    physical line counter exactly once. Bare-CR files therefore get
    correct physical line numbers and real directive discovery instead of
    collapsing into one unterminated logical line.
    """
    out = bytearray()
    line_of = []
    line_no = 1
    i = 0
    n = len(source)
    while i < n:
        if (source[i] == 0x5C and i + 1 < n
                and source[i + 1] in (0x0A, 0x0D)):
            newline_end = i + 2
            if (source[i + 1] == 0x0D and newline_end < n
                    and source[newline_end] == 0x0A):
                newline_end += 1  # CRLF splice consumes both CR and LF
            i = newline_end
            line_no += 1
            continue
        if source[i] == 0x0D:
            # End-of-line indicator: normalize CRLF (and bare CR) to a
            # single '\n' and count exactly one physical line (CODE-005).
            out.append(0x0A)
            line_of.append(line_no)
            line_no += 1
            i += 2 if (i + 1 < n and source[i + 1] == 0x0A) else 1
            continue
        out.append(source[i])
        line_of.append(line_no)
        if source[i] == 0x0A:
            line_no += 1
        i += 1
    return bytes(out), line_of


def _skip_comment_trivia(logical: bytes, pos: int, n: int) -> int:
    """Advance past spaces and comments (phase-3 comment replacement).

    Returns the position of the first byte that is neither whitespace nor
    part of a comment, or `n`/the end-of-line position when everything
    after `pos` is trivia. A '/* ... */' comment is consumed across
    physical lines (the comment's interior newlines are comment text); a
    '//' comment runs to the end of the logical line and is consumed up
    to but not including its terminating '\\n'. Used only for directive
    condition scanning, where the standard replaces comments with one
    space before the first condition token is read (CODE-003).
    """
    while pos < n:
        if logical[pos] in b" \t\f\v\r":
            pos += 1
            continue
        if logical[pos:pos + 2] == b"/*":
            end = logical.find(b"*/", pos + 2)
            pos = n if end < 0 else end + 2
            continue
        if logical[pos:pos + 2] == b"//":
            end = logical.find(b"\n", pos + 2)
            return n if end < 0 else end
        break
    return pos


def _directive_events(source: bytes):
    """Yield (keyword, line_no, dead) for real conditional directives.

    Implements C++ phase-2 translation: the source is line-spliced first
    (backslash-newline, including CRLF and bare-CR variants), so a '//'
    comment, a string literal, or a raw-string prefix/delimiter/terminator
    continues across the splice, and raw string literals (R"...", u8R"...",
    uR"...", UR"...", LR"..." with optional delimiters) are recognized as
    opaque regions on the assembled logical line. Block/line comments plus
    "..." string and '...' char literals are tracked on the logical text.
    A '#' at the start of a physical line is a directive only when the line
    really starts a fresh logical line outside every such region. Directive
    names are case-sensitive: '#IF'/'#ENDIF' are not directives. 'dead' is
    True only for a literal '#if 0' / '#elif 0' condition.
    """
    logical, line_of = _phase2_splice(source)
    n = len(logical)
    pos = 0
    at_line_start = True
    while pos < n:
        ch = logical[pos]
        if at_line_start and ch in b" \t\f\v\r":
            pos += 1
            continue
        if at_line_start and ch == 0x23:  # '#'
            directive_line = line_of[pos]
            k = pos + 1
            while k < n and logical[k] in b" \t\f\v\r":
                k += 1
            m = k
            while m < n and _is_identifier_byte(logical[m]):
                m += 1
            keyword = logical[k:m]
            dead = False
            if keyword in (b"if", b"elif"):
                # The first token of the condition decides '#if 0' /
                # '#elif 0'; splicing already joined any continuation
                # into the logical token stream, and comments are
                # replaced first (phase 3), so '#if /* c */ 0' is dead
                # and a multi-line block comment is consumed wholesale
                # (its interior newlines are comment text, not directive
                # terminators).
                q = _skip_comment_trivia(logical, m, n)
                t = q
                while t < n and logical[t] not in b" \t\f\v\r\n":
                    t += 1
                dead = logical[q:t] == b"0"
            # Consume the rest of the logical directive line; a spliced
            # continuation can never start a new directive, and block
            # comments spanning physical lines are skipped wholesale so
            # their interior lines cannot forge directives (CODE-003).
            p = m
            while p < n:
                if logical[p:p + 2] == b"//":
                    end = logical.find(b"\n", p + 2)
                    p = n if end < 0 else end
                    break
                if logical[p:p + 2] == b"/*":
                    end = logical.find(b"*/", p + 2)
                    p = n if end < 0 else end + 2
                    continue
                if logical[p] == 0x0A:
                    break
                p += 1
            if p < n:
                p += 1
                at_line_start = True
            else:
                at_line_start = False
            if keyword in _PREPROCESSOR_CONDITIONAL_KEYWORDS:
                yield keyword, directive_line, dead
            pos = p
            continue
        if ch == 0x2F and pos + 1 < n and logical[pos + 1] == 0x2A:
            # /* block comment */ (splices inside were already removed)
            pos += 2
            closed = False
            while pos < n:
                if (logical[pos] == 0x2A and pos + 1 < n
                        and logical[pos + 1] == 0x2F):
                    pos += 2
                    closed = True
                    break
                pos += 1
            at_line_start = not closed
        elif ch == 0x2F and pos + 1 < n and logical[pos + 1] == 0x2F:
            # // line comment: a splice keeps it open, so it already runs
            # to the logical end of line
            pos += 2
            closed = False
            while pos < n:
                if logical[pos] == 0x0A:
                    pos += 1
                    at_line_start = True
                    closed = True
                    break
                pos += 1
            if not closed:
                at_line_start = False
        elif ch == 0x22:  # '"'
            raw = False
            for prefix in _RAW_STRING_PREFIXES:
                if pos + 1 >= len(prefix) and logical[
                        pos + 1 - len(prefix):pos + 1] == prefix:
                    prefix_start = pos + 1 - len(prefix)
                    if (prefix_start == 0
                            or not _is_identifier_byte(
                                logical[prefix_start - 1])):
                        raw = True
                        break
            if raw:
                # R"delim( ... )delim" on the spliced logical text
                q = pos + 1
                while q < n and logical[q] != 0x28:  # '('
                    q += 1
                delim = logical[pos + 1:q]
                if len(delim) > _RAW_STRING_DELIMITER_MAX:
                    delim = b""  # not a valid raw string: recover
                r = q + 1
                terminator = delim + b'"'
                while r < n:
                    if logical[r] == 0x29:  # ')'
                        if logical[r + 1:r + 1 + len(terminator)] == terminator:
                            break
                    r += 1
                if r < n:
                    pos = r + 1 + len(terminator)
                else:
                    pos = n
                at_line_start = False
            else:
                # "..." string literal (escapes; splices already removed)
                pos += 1
                closed = False
                while pos < n:
                    if logical[pos] == 0x5C:
                        pos += 2
                    elif logical[pos] == 0x22:
                        pos += 1
                        at_line_start = False
                        closed = True
                        break
                    elif logical[pos] == 0x0A:
                        # Unterminated across a raw newline: recover.
                        pos += 1
                        at_line_start = True
                        closed = True
                        break
                    else:
                        pos += 1
                if not closed:
                    at_line_start = False
        elif ch == 0x27:  # "'"
            pos += 1
            closed = False
            while pos < n:
                if logical[pos] == 0x5C:
                    pos += 2
                elif logical[pos] == 0x27:
                    pos += 1
                    at_line_start = False
                    closed = True
                    break
                elif logical[pos] == 0x0A:
                    pos += 1
                    at_line_start = True
                    closed = True
                    break
                else:
                    pos += 1
            if not closed:
                at_line_start = False
        elif ch == 0x0A:
            pos += 1
            at_line_start = True
        else:
            pos += 1
            at_line_start = False


def _preprocessor_switch_lines(source: bytes):
    """Line numbers at preprocessor conditional switch points.

    Conditional directives come from _directive_events(), a complete C++
    phase-2 lexer that honors backslash-newline splicing (LF, CRLF and
    bare-CR variants), raw-string prefixes/delimiters/terminators,
    continuation-aware comments, and string/char literals, so raw-string
    contents or line-spliced comments cannot forge directives. (tree-sitter
    nodes are not used: probing the bundled grammar showed the conditional
    that this exemption exists for — a #ifdef splitting a class inheritance
    list — is swallowed into ERROR nodes and emits no preproc node at all.)

    Returns a frozenset of 1-indexed line numbers that are either inside an
    active conditional body (between #if/#ifdef/#ifndef and the matching
    #endif, excluding directive lines themselves) or within
    _PREPROC_SWITCH_WINDOW lines after the #endif of a live conditional, or
    None when the directives cannot be paired (unmatched #if/#else/#elif/
    #endif), in which case callers must fail closed.

    The whole #if/#elif/#else/#endif chain is tracked: a #elif or #else
    that follows a branch already taken is dead, '#elif 0' is dead, and
    #else takes the inverse of the chain (dead when any earlier branch was
    taken). Dead branches dominate: lines inside a dead branch are
    subtracted even when an enclosing live span, a nested live span, or a
    preceding post-#endif window also covered them, and a conditional
    nested inside a dead branch contributes neither body nor post-#endif
    window. A second #else or a #elif after #else is rejected (None),
    matching g++, so the directive chain always fails closed (CODE-002).
    """
    inactive_depth = 0
    stack = []
    spans = []
    for keyword, directive_line, dead in _directive_events(source):
        if keyword in (b"if", b"ifdef", b"ifndef"):
            branch_active = not dead
            stack.append({
                "start": directive_line,
                "dead_if": dead,
                "branch_active": branch_active,
                "chain_taken": branch_active,
                "seen_else": False,
                "in_inactive_context": inactive_depth > 0,
                "cur_start": directive_line,
                "active": [],
                "inactive": [],
            })
            if not branch_active:
                inactive_depth += 1
        elif keyword in (b"elif", b"else"):
            if not stack:
                return None
            frame = stack[-1]
            if frame["seen_else"]:
                # A duplicate #else or a #elif after #else is rejected by
                # g++; no branch of such a chain is trustworthy (CODE-002).
                return None
            # Close the branch that just ended.
            (frame["active"] if frame["branch_active"]
             else frame["inactive"]).append(
                (frame["cur_start"] + 1, directive_line))
            if not frame["branch_active"]:
                inactive_depth -= 1
            # A branch after the chain was already taken is dead; '#elif 0'
            # is dead; #else takes the inverse of the chain.
            if keyword == b"else":
                branch_active = not frame["chain_taken"]
                frame["chain_taken"] = True
                frame["seen_else"] = True
            else:
                branch_active = (not frame["chain_taken"]) and (not dead)
                frame["chain_taken"] = (frame["chain_taken"]
                                        or branch_active)
            frame["branch_active"] = branch_active
            frame["cur_start"] = directive_line
            if not branch_active:
                inactive_depth += 1
        else:  # endif
            if not stack:
                return None
            frame = stack.pop()
            (frame["active"] if frame["branch_active"]
             else frame["inactive"]).append(
                (frame["cur_start"] + 1, directive_line))
            if not frame["branch_active"]:
                inactive_depth -= 1
            spans.append((frame, directive_line))
    if stack:
        return None
    add_lines = set()
    subtract_lines = set()
    for frame, endif_line in spans:
        if frame["in_inactive_context"]:
            continue
        if frame["dead_if"]:
            for start, end in frame["active"]:
                add_lines.update(range(start, end))
            for start, end in frame["inactive"]:
                subtract_lines.update(range(start, end))
        else:
            for start, end in frame["active"]:
                add_lines.update(range(start, end))
            for start, end in frame["inactive"]:
                # A live frame's only inactive branches are the ones after
                # the chain was already taken: their lines must never
                # become switch points, even when an enclosing live span
                # also covers them (CODE-001).
                subtract_lines.update(range(start, end))
            add_lines.update(range(
                endif_line + 1, endif_line + 1 + _PREPROC_SWITCH_WINDOW))
    return frozenset(add_lines.difference(subtract_lines))


def _matches_frozen_baseline_node(node, source: bytes, baseline: dict) -> bool:
    """True when this ERROR/missing node is one of the frozen baseline nodes.

    The frozen list stores (physical line, node kind, text anchor). For
    ERROR nodes the anchor is the node's own text and is matched as a
    prefix (a later grammar version may absorb more text into the node);
    for missing nodes the node text is empty, so the anchor is the missing
    token (node.type), the only text a missing node carries. Line numbers
    are physical 1-indexed lines, exactly as recorded when the baseline
    was probed.
    """
    line_no = source.count(b"\n", 0, node.start_byte) + 1
    if node.is_missing:
        return (line_no, "missing", node.type.encode("ascii")) \
            in baseline["nodes"]
    fragment = source[node.start_byte:node.end_byte].lstrip()
    return any(
        line_no == frozen_line
        and fragment.startswith(frozen_anchor)
        for frozen_line, frozen_kind, frozen_anchor in baseline["nodes"]
        if frozen_kind == "ERROR"
    )


def has_relevant_parse_error(root, source: bytes) -> bool:
    """Ignore only recoverable preprocessor/member-pointer false positives."""
    switch_lines = _preprocessor_switch_lines(source)
    if switch_lines is None:
        # Unmatched #if/#else/#elif/#endif (including duplicate #else and
        # #elif-after-#else): no switch point is trustworthy. Fail closed
        # immediately — an extra #endif alone produces no tree-sitter
        # ERROR/missing node, so continuing the walk would certify the
        # file as successfully scanned.
        return True
    baseline = _PREPROCESSOR_BASELINE_DIRECTN
    baseline_content = (
        hashlib.sha256(source).hexdigest() == baseline["sha256"]
    )
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_missing or node.type == "ERROR":
            line_start = source.rfind(b"\n", 0, node.start_byte) + 1
            line_end = source.find(b"\n", node.end_byte)
            if line_end < 0:
                line_end = len(source)
            line = source[line_start:line_end]

            # Known pre-existing false positives caused by a preprocessor
            # conditional splitting a C++ construct (if/else chain, class
            # inheritance list, ...). Exempt only the real frozen baseline
            # nodes: the node must belong to the exact frozen baseline
            # content, its (line, kind, text anchor) must match a frozen
            # pair, and its line must be a preprocessor switch point. A
            # generic '}' / 'else' line or the same line text in any other
            # file, at any other line, or with any other node text still
            # fails closed (CODE-004). This is the only exemption that
            # applies to missing nodes, which otherwise always fail
            # closed.
            if (baseline_content
                    and source.count(b"\n", 0, node.start_byte) + 1
                    in switch_lines
                    and _matches_frozen_baseline_node(node, source,
                                                      baseline)):
                stack.extend(node.children)
                continue

            if node.is_missing:
                return True

            fragment = source[node.start_byte:node.end_byte].lstrip()

            # tree-sitter-cpp can split one preprocessor directive into
            # multiple ERROR nodes (for example '#if TAG == 34' and '34').
            if fragment.startswith(b"#") or line.lstrip().startswith(b"#"):
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


def _text_input_lines(
    source: os.PathLike[str] | str | AuditInput,
) -> tuple[list[str], Path]:
    if isinstance(source, AuditInput):
        return source.text.splitlines(keepends=True), Path(source.logical_path)
    filepath = os.fspath(source)
    if not os.path.exists(filepath):
        return [], Path(filepath)
    with open(filepath, "r", encoding="utf-8", errors="strict") as stream:
        return stream.readlines(), Path(filepath)


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
    lines, source_path = _text_input_lines(filepath)
    if not lines:
        return entries

    key = None
    key_line = 0
    value_line = 0
    value_lines = []
    in_entry = False
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


def parse_entries_physical(
    filepath: os.PathLike[str] | str | AuditInput,
) -> List[PhysicalEntry]:
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
    lines, source_path = _text_input_lines(filepath)
    if not lines:
        return entries

    raw_key = None
    key_line = 0
    value_line = 0
    value_lines = []
    in_entry = False
    order = 0
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


def trim_string(s: str) -> str:
    """C++ trim_string(): strip leading and trailing space, tab, newline, CR
    only (stringutil.cc: erase leading run of " \t\n\r", then the trailing
    run of the same set).

    Mirrors the C++ edge cases exactly: an empty or all-whitespace string
    becomes empty. The character set is explicit -- NOT str.strip(), which
    would also remove Unicode whitespace.
    """
    s = s.lstrip(" \t\n\r")
    return trim_string_right(s)


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
