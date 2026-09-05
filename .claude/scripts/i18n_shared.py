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


# Issue #120: repository-relative path, exact node text and local context.
# Probe line numbers in comments are evidence only, never matching keys.
# Contexts explain conditional splits; macros use parse_cpp_annotations.
_PREPROCESSOR_PATTERNS = {
    "crawl-ref/source/directn.cc": (
        # L622: `#ifndef USE_TILE_LOCAL` 切开 if/else，恢复时提前结束 else 块；现有窗口内
        ('missing', b'}',
         b'                {\n'
         b'                    str = "         " + fss[j].tostring();\n'
         b'                    me = new MenuEntry(str, MEL_ITEM, 1);\n'),
        # L626: 上述提前结束使真正闭括号孤立；现有窗口内
        ('ERROR', b'}',
         b'                    me->data = (void*)&mi;\n'
         b'                }\n'
         b'#endif\n'),
        # L1941: `DEBUG_DIAGNOSTICS` 分支末尾的 else 与 endif 后语句分离；现有窗口内
        ('ERROR', b'else',
         b'        _debug_describe_feature_at(target());\n'
         b'    else\n'
         b'#endif\n'),
        # L2439: 类继承列表被条件指令切开；现有 directive 规则处理
        ('ERROR', b'#ifdef USE_TILE_LOCAL\n    : public',
         b'class UIDirectionChooserView\n'
         b'#ifdef USE_TILE_LOCAL\n'
         b'    : public ui::Widget\n'
         b'#else\n'),
        # L2441: 同一继承列表的另一分支；现有 directive 规则处理
        ('ERROR', b'#else\n    : public ui',
         b'    : public ui::Widget\n'
         b'#else\n'
         b'    : public ui::OverlayWidget\n'
         b'#endif\n'),
        # L2443: 同一继承列表结束指令；现有 directive 规则处理
        ('ERROR', b'#endif',
         b'    : public ui::OverlayWidget\n'
         b'#endif\n'
         b'{\n'),
        # L2446: 类头恢复失败，构造函数被误读；现有窗口内
        ('ERROR', b'UIDirectionChooserView(direction_chooser& dc) :',
         b'public:\n'
         b'    UIDirectionChooserView(direction_chooser& dc) :\n'
         b'        m_dc(dc), old_target(dc.target())\n'),
        # L2447: 上述恢复把成员初始化列表当作需要分号的语句；现有窗口内
        ('missing', b';',
         b'    UIDirectionChooserView(direction_chooser& dc) :\n'
         b'        m_dc(dc), old_target(dc.target())\n'
         b'    {\n'),
        # L3721: DEBUG_DIAGNOSTICS 内直接初始化被误读为声明符，* 无法归约。
        ('ERROR', b'*',
         b'    {\n'
         b'        const vault_placement &vp(*env.level_vaults[map_index]);\n'
         b'        const coord_def br = vp.pos + vp.size - 1;\n'),
        # L3721: 同一初始化被误读后的成员访问恢复错误；现有窗口内
        ('ERROR', b'.',
         b'    {\n'
         b'        const vault_placement &vp(*env.level_vaults[map_index]);\n'
         b'        const coord_def br = vp.pos + vp.size - 1;\n'),
    ),
    "crawl-ref/source/main.cc": (
        # L235: 条件分支内的 GNU 属性与 endif 后 main 声明分离；现有窗口内
        ('ERROR', b'__attribute__((externally_visible))',
         b'// from this treatment.\n'
         b'__attribute__((externally_visible))\n'
         b'# endif\n'),
        # L2041: 构造函数参数中的位或表达式被条件切开；现有 directive 规则处理
        ('ERROR', b'#ifdef USE_TILE_LOCAL',
         b'                | MF_ARROWS_SELECT | MF_WRAP | MF_INIT_HOVER\n'
         b'#ifdef USE_TILE_LOCAL\n'
         b'                | MF_SPECIAL_MINUS // doll editor (why?)\n'),
        # L2043: 上述参数表达式的条件结束；现有 directive 规则处理
        ('ERROR', b'#endif',
         b'                | MF_SPECIAL_MINUS // doll editor (why?)\n'
         b'#endif\n'
         b'                ),\n'),
        # L2400: USE_TILE_WEB 内的 else 与前面的 if 分隔，调用被误读为声明；现有窗口内
        ('ERROR', b'tiles.',
         b'        else\n'
         b'            tiles.send_dump_info("command", you.your_name);\n'
         b'#endif\n'),
    ),
    "crawl-ref/source/menu.cc": (
        # L115: 构造函数成员初始化列表中插入指令；现有 directive 规则处理
        ('ERROR', b'#ifdef USE_TILE_LOCAL',
         b'\n'
         b'#ifdef USE_TILE_LOCAL\n'
         b'    , m_font_entry(tiles.get_crt_font()), m_text_buf(m_font_entry)\n'),
        # L117: 上述初始化列表的条件结束；现有 directive 规则处理
        ('ERROR', b'#endif',
         b'    , m_font_entry(tiles.get_crt_font()), m_text_buf(m_font_entry)\n'
         b'#endif\n'
         b'    {\n'),
        # L791: `if (min_column_width <= 0)` 的语句体从下一行 ifdef 开始，恢复时误报缺少分号；节点在指令之前，不在窗口内
        ('missing', b';',
         b'    int min_column_width = m_menu->m_ui.menu->get_min_col_width();\n'
         b'    if (min_column_width <= 0)\n'
         b'#ifdef USE_TILE_LOCAL\n'),
        # L2397: 声明名与初始化值被 ifdef 切开；节点起点不在窗口内，现有 directive 规则也不匹配
        ('ERROR', b'indent\n#ifdef',
         b'    // the title only (TODO)\n'
         b'    const int indent\n'
         b'#ifdef USE_TILE_LOCAL\n'
         b'        = 0; // tiles does line-wrapping inside the text\n'),
        # L2401: 上述声明的 else 分支留下孤立初始化符；现有 lexer 将该分支从窗口扣除
        ('ERROR', b'=',
         b'#else\n'
         b'        = static_cast<int>(_get_text_preface().size());\n'
         b'    width -= indent;\n'),
        # L2810: 声明与初始化值被下一行 ifdef 切开；节点在指令之前，不在窗口内
        ('ERROR', b'const int width =',
         b'    // min width is explicitly set.\n'
         b'    const int width =\n'
         b'#ifdef USE_TILE_LOCAL\n'),
        # L2987: set_scroll 参数表达式被条件切开；现有 directive 规则处理
        ('ERROR', b'#ifdef USE_TILE_LOCAL',
         b'    m_ui.scroller->set_scroll(y1\n'
         b'#ifdef USE_TILE_LOCAL\n'
         b'            - UI_SCROLLER_SHADE_SIZE / 2\n'),
        # L2989: 上述参数表达式的条件结束；现有 directive 规则处理
        ('ERROR', b'#endif',
         b'            - UI_SCROLLER_SHADE_SIZE / 2\n'
         b'#endif\n'
         b'            );\n'),
    ),
}

# Window (in lines) after an #endif within which a matching registered
# node is still considered a preprocessor switch-point false positive.
_PREPROC_SWITCH_WINDOW = 4

# tree-sitter-cpp cannot be the directive source here: in the exact regions
# this exemption exists for (a conditional splitting a class inheritance
# list, an if/else chain, ...), the parser's ERROR recovery swallows the
# directive lines and emits no preproc node. Probing the bundled grammar on
# crawl-ref/source/directn.cc found only 42 preproc_if/preproc_ifdef/
# preproc_ifndef nodes for 87 actual conditional directives, including no
# node for the #ifdef USE_TILE_LOCAL at line 2439 whose post-#endif window
    # covers the baseline probe lines 2446/2447. Directive discovery therefore
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


def _raw_prefix_at_output(out: bytearray) -> bool:
    """True when the accumulated spliced text ends with a raw prefix.

    The opening quote of a raw string literal is not in ``out`` yet, so
    the check matches the prefix stem (R, u8R, uR, UR, LR) at the end of
    the emitted text and requires that the stem is not itself part of a
    longer identifier, mirroring _raw_prefix_here() on the assembled
    logical line (CODE-001).
    """
    for prefix in _RAW_STRING_PREFIXES:
        stem = prefix[:-1]
        if len(out) >= len(stem) and bytes(out[-len(stem):]) == stem:
            prefix_start = len(out) - len(stem)
            if (prefix_start == 0
                    or not _is_identifier_byte(out[prefix_start - 1])):
                return True
    return False


def _phase2_splice(source: bytes):
    """Delete backslash-newline splices (C++ translation phases 1 and 2).

    Returns (logical, line_of) where `logical` is the spliced, normalized
    translation unit and ``line_of[i]`` is the 1-indexed physical line
    number of ``logical[i]`` in the original file. A splice is a backslash
    byte immediately followed by a new-line; LF (\n), CRLF (\r\n), and
    bare CR (\r) terminators are all recognized. Splices may occur
    anywhere outside raw-string literals — inside comments, ordinary
    string/char literals, and raw-string prefixes — exactly as the
    standard's phase-2 deletion requires, so every later lexical check
    runs on the assembled logical line.

    Raw-string literals (R"...", u8R"...", uR"...", UR"...", LR"..." with
    an optional d-char-sequence) are the one region where phase-2
    deletion does not apply: g++ keeps a backslash-newline inside a
    raw-string body — and inside the opening/closing delimiter pair — as
    literal text, so the literal's ')d-seq"' terminator is matched on the
    raw characters (a splice there would invent a terminator g++ never
    sees; for example R"x(\n)x\\<newline>" is an unterminated raw string
    to g++, not a legal terminated literal). The splice scan therefore
    tracks raw-string literal state (prefix + delimiter pair + body) and
    resumes ordinary splicing only after the closing delimiter. Comments
    and ordinary literals are tracked so a quote inside them cannot open
    a raw string, and a raw-string prefix itself still splices before
    its opening quote (R\\<newline>"(...)" is a legal raw string).

    Phase-1 end-of-line normalization is applied at the same time in
    every state, including raw-string bodies: LF, CRLF, and bare CR are
    all end-of-line indicators (C++ [lex.phases] p1 introduces new-line
    characters for end-of-line indicators), so every EOL sequence becomes
    a single '\n' in the output and increments the physical line counter
    exactly once — exactly the single '\n' g++ stores for a CRLF inside a
    raw string. Bare-CR files therefore get correct physical line numbers
    and real directive discovery instead of collapsing into one
    unterminated logical line.
    """
    out = bytearray()
    line_of = []
    line_no = 1
    i = 0
    n = len(source)
    # Lexical state: 0 normal, 1 line comment, 2 block comment,
    # 3 string literal, 4 char literal, 5 raw-string opening delimiter
    # (between the opening quote and '('), 6 raw-string body.
    state = 0
    raw_delim = b""
    while i < n:
        ch = source[i]
        # Phase-2 splice: a backslash immediately followed by a new-line
        # is deleted everywhere except inside raw-string literals (body
        # and delimiter pair), where it is literal text (CODE-001).
        if (ch == 0x5C and i + 1 < n
                and source[i + 1] in (0x0A, 0x0D)
                and state != 5 and state != 6):
            newline_end = i + 2
            if (source[i + 1] == 0x0D and newline_end < n
                    and source[newline_end] == 0x0A):
                newline_end += 1  # CRLF splice consumes both CR and LF
            i = newline_end
            line_no += 1
            continue
        if ch == 0x0D:
            # Phase-1 end-of-line normalization applies in every state,
            # including raw-string bodies: CRLF (and bare CR) becomes a
            # single '\n' and counts exactly one physical line (CODE-005).
            out.append(0x0A)
            line_of.append(line_no)
            line_no += 1
            if state == 5 and len(raw_delim) <= _RAW_STRING_DELIMITER_MAX:
                raw_delim += b"\n"
            i += 2 if (i + 1 < n and source[i + 1] == 0x0A) else 1
            if state == 1:
                state = 0
            continue
        if ch == 0x0A:
            out.append(ch)
            line_of.append(line_no)
            line_no += 1
            i += 1
            if state == 5 and len(raw_delim) <= _RAW_STRING_DELIMITER_MAX:
                raw_delim += b"\n"
            if state == 1:
                state = 0  # a // comment ends at the new-line
            elif state in (3, 4):
                # Unterminated ordinary literal: recover at the raw
                # new-line, the same recovery _skip_quoted() applies.
                state = 0
            continue
        if state == 1:
            out.append(ch)
            line_of.append(line_no)
            i += 1
            continue
        if state == 2:
            if ch == 0x2A and i + 1 < n and source[i + 1] == 0x2F:
                out.append(source[i])
                line_of.append(line_no)
                out.append(source[i + 1])
                line_of.append(line_no)
                i += 2
                state = 0
                continue
            out.append(ch)
            line_of.append(line_no)
            i += 1
            continue
        if state in (3, 4):
            quote = 0x22 if state == 3 else 0x27
            if ch == 0x5C:
                # Complete backslash-run handling: phase 2 deletes only
                # the LAST backslash of a run of consecutive backslashes
                # when it is immediately followed by a new-line (only the
                # last backslash on a physical source line is eligible
                # for a splice), and that deletion happens before string
                # parsing. g++/clang++ therefore accept
                #   const char *s = "\\<LF>#ifdef FAKE";
                # as the single logical line "\#ifdef FAKE" (the trailing
                # backslash+LF splice vanishes first, then the surviving
                # backslash escapes '#'). The old escape-pair branch
                # consumed '\\' as a pair and kept the LF, forging an
                # unmatched '#ifdef' directive on a file g++ accepts
                # (CODE-001).
                run_end = i + 1
                while run_end < n and source[run_end] == 0x5C:
                    run_end += 1
                if run_end < n and source[run_end] in (0x0A, 0x0D):
                    # Phase-2 splice of the trailing backslash + new-line
                    # (LF, CRLF or bare CR).
                    newline_end = run_end + 1
                    if (source[run_end] == 0x0D and newline_end < n
                            and source[newline_end] == 0x0A):
                        newline_end += 1  # CRLF splice consumes both
                    surviving = run_end - 1 - i
                    # The surviving backslashes form escape pairs; an
                    # even survivor leaves the byte after the spliced
                    # new-line unescaped (it may close the literal).
                    if surviving:
                        out.extend(b"\\\\" * (surviving // 2))
                        line_of.extend([line_no]
                                       * (2 * (surviving // 2)))
                    i = newline_end
                    line_no += 1
                    if surviving % 2 == 1:
                        # The lone survivor escapes the next byte that
                        # survives phase 2: skip any immediately
                        # following backslash-newline splices, then
                        # consume the escaped byte (which may be the
                        # closing quote, in which case the literal stays
                        # open, exactly as g++ parses the spliced text).
                        out.append(0x5C)
                        line_of.append(line_no)
                        while (i < n and source[i] == 0x5C
                               and i + 1 < n
                               and source[i + 1] in (0x0A, 0x0D)):
                            i += 2
                            if (source[i - 1] == 0x0D and i < n
                                    and source[i] == 0x0A):
                                i += 1  # CRLF splice
                            line_no += 1
                        if i < n:
                            out.append(source[i])
                            line_of.append(line_no)
                            i += 1
                    continue
                if i + 1 < n:
                    # Escape: copy the backslash and the escaped byte.
                    out.append(source[i])
                    line_of.append(line_no)
                    out.append(source[i + 1])
                    line_of.append(line_no)
                    i += 2
                    continue
                # Lone trailing backslash at end of input.
                out.append(ch)
                line_of.append(line_no)
                i += 1
                continue
            out.append(ch)
            line_of.append(line_no)
            i += 1
            if ch == quote:
                state = 0
            continue
        if state == 5:
            # Raw-string opening delimiter region: backslash-EOL is
            # literal text here too (g++ rejects a backslash inside the
            # delimiter), so only phase-1 EOL normalization applies.
            out.append(ch)
            line_of.append(line_no)
            i += 1
            if ch == 0x28:  # '('
                if len(raw_delim) > _RAW_STRING_DELIMITER_MAX:
                    # Over-long d-char-sequence: recover the same way
                    # _skip_raw_string() does (search for ')"').
                    raw_delim = b""
                state = 6
            elif len(raw_delim) <= _RAW_STRING_DELIMITER_MAX:
                raw_delim += bytes((ch,))
            continue
        if state == 6:
            # Raw-string body: fully literal, no phase-2 splicing; the
            # terminator ')d-seq"' is matched on the raw characters.
            terminator = b")" + raw_delim + b'"'
            if (ch == 0x29 and i + len(terminator) <= n
                    and source[i:i + len(terminator)] == terminator):
                # Closing delimiter found: copy it (phase-1 EOL
                # normalization still applies inside it) and resume
                # ordinary splicing after it (CODE-001).
                j = 0
                while j < len(terminator):
                    byte = source[i + j]
                    if byte == 0x0D:
                        out.append(0x0A)
                        line_of.append(line_no)
                        line_no += 1
                        j += 2 if (j + 1 < len(terminator)
                                   and source[i + j + 1] == 0x0A) else 1
                    elif byte == 0x0A:
                        out.append(byte)
                        line_of.append(line_no)
                        line_no += 1
                        j += 1
                    else:
                        out.append(byte)
                        line_of.append(line_no)
                        j += 1
                i += len(terminator)
                state = 0
                continue
            out.append(ch)
            line_of.append(line_no)
            i += 1
            continue
        # state 0 (normal): enter comment/literal states and splice.
        if ch == 0x2F and i + 1 < n and source[i + 1] == 0x2F:
            out.append(source[i])
            line_of.append(line_no)
            out.append(source[i + 1])
            line_of.append(line_no)
            i += 2
            state = 1
            continue
        if ch == 0x2F and i + 1 < n and source[i + 1] == 0x2A:
            out.append(source[i])
            line_of.append(line_no)
            out.append(source[i + 1])
            line_of.append(line_no)
            i += 2
            state = 2
            continue
        if ch == 0x22:
            if _raw_prefix_at_output(out):
                # R"...", u8R"...", uR"...", UR"...", LR"...": the whole
                # literal (delimiter pair and body) is tracked so its
                # backslash-EOL bytes stay literal (CODE-001).
                out.append(ch)
                line_of.append(line_no)
                i += 1
                raw_delim = b""
                state = 5
                continue
            out.append(ch)
            line_of.append(line_no)
            i += 1
            state = 3
            continue
        if ch == 0x27:
            out.append(ch)
            line_of.append(line_no)
            i += 1
            state = 4
            continue
        out.append(ch)
        line_of.append(line_no)
        i += 1
    return bytes(out), line_of


def _normalize_eol(source: bytes) -> bytes:
    """Normalize CRLF and bare CR to LF (phase-1 end-of-line normalization).

    Line-count preserving: every end-of-line indicator (LF, CRLF, bare
    CR) becomes exactly one '\n', so a byte's physical line number is the
    same in the raw and the normalized bytes. The lexer (_phase2_splice)
    applies the same normalization while splicing; this helper exposes
    the identical mapping so the tree-sitter input and the frozen
    baseline binding use the same bytes the lexer sees (CODE-003).
    """
    out = bytearray()
    i = 0
    n = len(source)
    while i < n:
        if source[i] == 0x0D:
            out.append(0x0A)
            i += 2 if (i + 1 < n and source[i + 1] == 0x0A) else 1
            continue
        out.append(source[i])
        i += 1
    return bytes(out)


def _line_of_byte(source: bytes, byte_offset: int) -> int:
    """1-indexed physical line containing ``source[byte_offset]``.

    Counts LF, CRLF and bare CR each as exactly one end-of-line indicator
    -- the same phase-1 mapping _phase2_splice() applies -- so tree-sitter
    byte offsets into a CRLF or bare-CR file resolve to the same physical
    lines the lexer reports for its directives. The lexer and tree-sitter
    therefore share one line mapping for every line-ending style
    (CODE-003).
    """
    line = 1
    i = 0
    limit = min(byte_offset, len(source))
    while i < limit:
        if source[i] == 0x0A:
            line += 1
        elif source[i] == 0x0D:
            line += 1
            if i + 1 < limit and source[i + 1] == 0x0A:
                i += 1
        i += 1
    return line


def _line_span(source: bytes, start_byte: int, end_byte: int):
    """(start, end) byte span of the physical line(s) containing the node.

    EOL-agnostic counterpart of the \n-based line extraction: LF, CRLF
    and bare CR are all end-of-line indicators, so the span boundaries
    match the physical lines _line_of_byte() reports (CODE-003).
    """
    n = len(source)
    start = 0
    i = 0
    while i < start_byte and i < n:
        if source[i] == 0x0A:
            start = i + 1
        elif source[i] == 0x0D:
            start = i + 1
            if i + 1 < n and source[i + 1] == 0x0A:
                i += 1
        i += 1
    end = n
    i = end_byte
    while i < n:
        if source[i] in (0x0A, 0x0D):
            end = i
            break
        i += 1
    return start, end


def _skip_block_comment(logical: bytes, pos: int, n: int) -> int:
    """Skip a '/* ... */' comment; ``pos`` points at '/*'.

    Returns the position just after the closing '*/', or `n` when the
    comment is unterminated. The comment's interior newlines are comment
    text, so a block comment is consumed across physical lines.
    """
    pos += 2
    while pos < n:
        if (logical[pos] == 0x2A and pos + 1 < n
                and logical[pos + 1] == 0x2F):
            return pos + 2
        pos += 1
    return n


def _skip_line_comment(logical: bytes, pos: int, n: int) -> int:
    """Skip a '//' comment; ``pos`` points at '//'.

    Returns the position of the terminating '\n' (exclusive), or `n`
    when the comment runs to the end of the logical text.
    """
    end = logical.find(b"\n", pos + 2)
    return n if end < 0 else end


def _raw_prefix_here(logical: bytes, pos: int, n: int) -> bool:
    """True when a raw-string prefix ends at ``pos`` (the opening quote).

    Recognizes R\", u8R\", uR\", UR\", LR\" and requires that the prefix
    is not itself part of a longer identifier.
    """
    for prefix in _RAW_STRING_PREFIXES:
        if pos + 1 >= len(prefix) and logical[
                pos + 1 - len(prefix):pos + 1] == prefix:
            prefix_start = pos + 1 - len(prefix)
            if (prefix_start == 0
                    or not _is_identifier_byte(logical[prefix_start - 1])):
                return True
    return False


def _skip_raw_string(logical: bytes, pos: int, n: int) -> int:
    """Skip an R\"delim( ... )delim\" literal; ``pos`` is the opening quote.

    Returns the position just after the closing delimiter, or `n` when
    the literal is unterminated. The interior (including any newlines) is
    opaque literal text.
    """
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
                return r + 1 + len(terminator)
        r += 1
    return n


def _skip_quoted(logical: bytes, pos: int, n: int) -> int:
    """Skip a "..." string or '...' char literal; ``pos`` is the quote.

    Handles backslash escapes; returns the position just after the
    closing quote, or the position of the terminating '\n' / `n` when the
    literal is unterminated (recovery at the raw newline).
    """
    quote = logical[pos]
    pos += 1
    while pos < n:
        if logical[pos] == 0x5C:
            pos += 2
        elif logical[pos] == quote:
            return pos + 1
        elif logical[pos] == 0x0A:
            return pos
        else:
            pos += 1
    return n


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
            pos = _skip_block_comment(logical, pos, n)
            continue
        if logical[pos:pos + 2] == b"//":
            return _skip_line_comment(logical, pos, n)
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
    really starts a fresh logical line outside every such region; leading
    comments are phase-3 trivia, so '/* c */ #if 1' is a directive (the
    comment is replaced by one space and the '#' stays the first token),
    and comments between '#' and the directive name (or inside it) are
    replaced the same way, so '#/**/if 1' is '#if 1' (CODE-002). Directive
    names are case-sensitive: '#IF'/'#ENDIF' are not directives. 'dead' is
    True only for a literal '#if 0' / '#elif 0' condition. The rest of a
    directive line is consumed with full literal state: '//' and '/*' are
    recognized only outside string, char and raw-string literals, so a
    legal '#define S "/*"' never truncates the line at literal text
    (CODE-001).
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
            # The directive name is read after phase-3 comment
            # replacement: trivia and comments between '#' and the name
            # are one space, so '#/**/if' and '# /* c */ if' are '#if'.
            # A '//' comment runs to the end of the logical line, so no
            # name follows it (the directive is a null directive).
            k = pos + 1
            while k < n:
                if logical[k] in b" \t\f\v\r":
                    k += 1
                    continue
                if logical[k:k + 2] == b"/*":
                    k = _skip_block_comment(logical, k, n)
                    continue
                if logical[k:k + 2] == b"//":
                    k = _skip_line_comment(logical, k, n)
                    break
                break
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
                # terminators). A comment adjacent to the token also
                # ends it: '#if 0/**/' and '#if 0//comment' (both
                # accepted by g++ with a dead body) read '0' because the
                # phase-3 comment becomes one space (CODE-002).
                q = _skip_comment_trivia(logical, m, n)
                t = q
                while t < n and logical[t] not in b" \t\f\v\r\n":
                    if logical[t:t + 2] in (b"/*", b"//"):
                        break
                    t += 1
                dead = logical[q:t] == b"0"
            # Consume the rest of the logical directive line; a spliced
            # continuation can never start a new directive, and block
            # comments spanning physical lines are skipped wholesale so
            # their interior lines cannot forge directives (CODE-003).
            # The scan tracks literal state: '//' and '/*' inside string,
            # char and raw-string literals are literal text, not
            # comments, so '#define S "/*"' ends at its own newline and
            # later directives are still discovered (CODE-001).
            p = m
            while p < n:
                if logical[p] == 0x0A:
                    break
                if (logical[p] == 0x2F
                        and logical[p + 1:p + 2] in (b"*", b"/")):
                    if logical[p + 1] == 0x2A:
                        p = _skip_block_comment(logical, p, n)
                    else:
                        p = _skip_line_comment(logical, p, n)
                        break
                    continue
                if logical[p] == 0x22:
                    if _raw_prefix_here(logical, p, n):
                        p = _skip_raw_string(logical, p, n)
                    else:
                        p = _skip_quoted(logical, p, n)
                    continue
                if logical[p] == 0x27:
                    p = _skip_quoted(logical, p, n)
                    continue
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
            # /* block comment */ (splices inside were already removed).
            # Phase 3 replaces the whole comment with one space, so it
            # neither starts nor ends a token run: 'at_line_start' is
            # preserved, keeping a '#' after a leading comment the first
            # token of the logical line while a mid-line '#' stays a
            # non-directive (CODE-002).
            pos = _skip_block_comment(logical, pos, n)
        elif ch == 0x2F and pos + 1 < n and logical[pos + 1] == 0x2F:
            # // line comment: a splice keeps it open, so it already runs
            # to the logical end of line
            pos = _skip_line_comment(logical, pos, n)
            if pos < n:
                pos += 1
                at_line_start = True
            else:
                at_line_start = False
        elif ch == 0x22:  # '"'
            if _raw_prefix_here(logical, pos, n):
                # R"delim( ... )delim" on the spliced logical text
                pos = _skip_raw_string(logical, pos, n)
            else:
                # "..." string literal (escapes; splices already removed)
                pos = _skip_quoted(logical, pos, n)
            at_line_start = False
        elif ch == 0x27:  # "'"
            pos = _skip_quoted(logical, pos, n)
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


def _matches_preprocessor_node(node, source, patterns, switch_lines, events):
    """Match a registered node and its complete local source context.

    Existing live-body/post-endif windows are retained. Only a registered
    context containing a real lexer directive can extend that window to
    the preceding lines or an else branch. No global window is widened.
    Exact node text prevents a recovery node absorbing new broken syntax.
    """
    kind = "missing" if node.is_missing else node.type
    anchor = (node.type.encode("ascii") if node.is_missing else
              source[node.start_byte:node.end_byte])
    line = _line_of_byte(source, node.start_byte)
    for expected_kind, expected_anchor, context in patterns:
        if (kind, anchor) != (expected_kind, expected_anchor):
            continue
        start = source.rfind(context, 0, node.start_byte + len(context))
        if start < 0 or not (start <= node.start_byte <= start + len(context)):
            continue
        if node.end_byte > start + len(context):
            continue
        if line in switch_lines:
            return True
        first = _line_of_byte(source, start)
        last = _line_of_byte(source, start + len(context))
        if any(first <= directive <= last
               and abs(line - directive) <= _PREPROC_SWITCH_WINDOW
               for _, directive, _ in events):
            return True
    return False


def parse_cpp_annotations(parser, source: bytes):
    """Parse known annotations and local macros without losing offsets.

    The first tree identifies actual function declarations/definitions, so
    text in comments, literals and macro bodies is never rewritten. Only the
    complete declaration prefixes observed in Crawl are supported. Unknown
    annotations and all body syntax remain for normal fail-closed validation.
    The returned tree indexes the original bytes: annotations become spaces,
    never deleted text, and callers still inspect/report the original source.
    """
    tree = parser.parse(source)
    normalized = bytearray(source)
    changed = False
    stack = [tree.root_node]
    identifiers = []
    literals = []
    prefixes = (
        rb"(?P<annotation>NORETURN)\s+(?:static\s+)?void\s+",
        rb"static\s+void\s+(?P<annotation>CALLBACK)\s+",
        rb"(?P<annotation>JNIEXPORT)\s+void\s+(?P<calling>JNICALL)\s+",
    )
    while stack:
        node = stack.pop()
        if node.type in ("comment", "char_literal", "raw_string_literal",
                         "preproc_def", "preproc_function_def", "preproc_arg"):
            continue
        if node.type == "string_literal":
            literals.append((node.start_byte, node.end_byte))
            continue
        if (node.type == "identifier"
                and source[node.start_byte:node.end_byte] == b"CRAWL"):
            identifiers.append(node)
        if node.type == "call_expression":
            function = node.child_by_field_name("function")
            args = node.child_by_field_name("arguments")
            if (function is not None and function.type == "identifier"
                    and source[function.start_byte:function.end_byte] == b"va_arg"
                    and args is not None):
                # Scheme 3 precursor: retain the complete expression argument
                # (and its findings/errors); only make the type operand an
                # ordinary expression placeholder. Unsupported type syntax
                # stays untouched. Never consume a semicolon or newline.
                comma = source.rfind(b",", args.start_byte, args.end_byte)
                operand = source[comma + 1:args.end_byte - 1]
                if (comma >= args.start_byte and re.fullmatch(
                        rb"[ \t]*[A-Za-z_]\w*(?:(?:[ \t]+|::)[A-Za-z_]\w*)*"
                        rb"[ \t]*[*&]*[ \t]*", operand)):
                    type_tree = parser.parse(b"using __va_type = " + operand + b";")
                    if not type_tree.root_node.has_error:
                        begin = comma + 1
                        normalized[begin:args.end_byte - 1] = (
                            b"0" + b" " * (len(operand) - 1))
                        changed = True
        if node.type in ("function_definition", "declaration"):
            declarator = node.child_by_field_name("declarator")
            if declarator is not None and declarator.type == "function_declarator":
                prefix = source[node.start_byte:declarator.start_byte]
                for pattern in prefixes:
                    match = re.fullmatch(pattern, prefix)
                    if match is None:
                        continue
                    if "calling" in match.groupdict():
                        parent = node.parent
                        if parent is None or parent.type != "linkage_specification":
                            continue
                        linkage = parent.child_by_field_name("value")
                        if linkage is None or source[linkage.start_byte:linkage.end_byte] != b'"C"':
                            continue
                    for name, text in match.groupdict().items():
                        begin = node.start_byte + match.start(name)
                        normalized[begin:begin + len(text)] = b" " * len(text)
                    changed = True
                    break
        stack.extend(node.children)
    # Scheme 3 precursor: only an AST identifier adjacent to an actual
    # string literal, with whitespace between them, denotes this object
    # macro. Comments, raw-string contents and longer identifiers cannot
    # trigger it. Five bytes remain five bytes; no source location moves.
    for node in identifiers:
        if any((end <= node.start_byte
                and not source[end:node.start_byte].strip())
               or (node.end_byte <= begin
                   and not source[node.end_byte:begin].strip())
               for begin, end in literals):
            normalized[node.start_byte:node.end_byte] = b'""   '
            changed = True
    return parser.parse(bytes(normalized)) if changed else tree


def preprocessor_patterns_for_path(filepath):
    """Registered repository-relative identity, including exported copies."""
    path = Path(filepath).as_posix() if filepath is not None else ""
    return next((entries for relative, entries in _PREPROCESSOR_PATTERNS.items()
                 if path == relative or path.endswith("/" + relative)), ())


def has_relevant_parse_error(root, source: bytes, filepath=None) -> bool:
    """Ignore only recoverable preprocessor/member-pointer false positives."""
    switch_lines = _preprocessor_switch_lines(source)
    if switch_lines is None:
        # Unmatched #if/#else/#elif/#endif (including duplicate #else and
        # #elif-after-#else): no switch point is trustworthy. Fail closed
        # immediately — an extra #endif alone produces no tree-sitter
        # ERROR/missing node, so continuing the walk would certify the
        # file as successfully scanned.
        return True
    patterns = preprocessor_patterns_for_path(filepath)
    events = tuple(_directive_events(source)) if patterns else ()
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_missing or node.type == "ERROR":
            line_start, line_end = _line_span(source, node.start_byte,
                                              node.end_byte)
            line = source[line_start:line_end]

            # Path, exact node/context and a lexer-discovered conditional
            # window must all match, including for missing tokens.
            if _matches_preprocessor_node(node, source, patterns,
                                          switch_lines, events):
                stack.extend(node.children)
                continue

            if node.is_missing:
                return True

            fragment = source[node.start_byte:node.end_byte].lstrip()

            # tree-sitter-cpp can split one preprocessor directive into
            # multiple ERROR nodes (for example '#if TAG == 34' and '34').
            if not patterns and (fragment.startswith(b"#")
                                 or line.lstrip().startswith(b"#")):
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
