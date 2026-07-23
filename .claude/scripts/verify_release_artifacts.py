#!/usr/bin/env python3
"""Fail-closed validation for the DCSS Chinese Windows release archive."""

from __future__ import annotations

import argparse
import hashlib
import re
import stat
import zipfile
from dataclasses import dataclass, replace
from pathlib import Path, PurePosixPath


RELEASE_TAG_RE = re.compile(r"0\.34\.1-zh[1-9][0-9]*\Z")
COMMIT_RE = re.compile(r"[0-9a-f]{40}\Z")
ZH_DATA_TREES = (
    "crawl-ref/source/dat/i18n/zh",
    "crawl-ref/source/dat/database/zh",
    "crawl-ref/source/dat/descript/zh",
)


class ReleaseArtifactError(RuntimeError):
    """Raised when a release archive violates the closed-world contract."""


@dataclass(frozen=True)
class ContentSource:
    member: str
    source: str
    normalize_crlf: bool = False


@dataclass(frozen=True)
class ArtifactRule:
    filename: str
    archive_type: str
    root: str
    required_files: tuple[str, ...]
    executable_files: tuple[str, ...]
    content_sources: tuple[ContentSource, ...]
    data_root: str
    normalize_text_crlf: bool


def artifact_rules(tag: str) -> tuple[ArtifactRule, ...]:
    major = ".".join(tag.split("-", 1)[0].split(".")[:2])
    windows_root = f"stone_soup-tiles-{major}"
    return (
        ArtifactRule(
            filename=f"stone_soup-{tag}-tiles-win32.zip",
            archive_type="zip",
            root=windows_root,
            required_files=(
                f"{windows_root}/crawl.exe",
                f"{windows_root}/dat/i18n/zh/source.txt",
                f"{windows_root}/dat/tiles/MapleMono-NF-CN-Regular.ttf",
                f"{windows_root}/docs/license/LICENSE-Maple-Mono.txt",
                f"{windows_root}/settings/init.txt",
                f"{windows_root}/LICENSE",
            ),
            executable_files=(),
            content_sources=(
                ContentSource(
                    f"{windows_root}/dat/i18n/zh/source.txt",
                    "crawl-ref/source/dat/i18n/zh/source.txt",
                    normalize_crlf=True,
                ),
                ContentSource(
                    f"{windows_root}/dat/tiles/MapleMono-NF-CN-Regular.ttf",
                    "crawl-ref/source/dat/tiles/MapleMono-NF-CN-Regular.ttf",
                ),
                ContentSource(
                    f"{windows_root}/docs/license/LICENSE-Maple-Mono.txt",
                    "docs/fonts/LICENSE-Maple-Mono.txt",
                ),
                ContentSource(
                    f"{windows_root}/settings/init.txt",
                    "crawl-ref/settings/init.txt",
                    normalize_crlf=True,
                ),
                ContentSource(f"{windows_root}/LICENSE", "LICENSE"),
            ),
            data_root=f"{windows_root}/dat",
            normalize_text_crlf=True,
        ),
    )


def release_rules(tag: str, source_root: Path) -> tuple[ArtifactRule, ...]:
    data_source_root = source_root / "crawl-ref/source/dat"
    tree_files: list[Path] = []
    for relative_tree in ZH_DATA_TREES:
        tree = source_root / relative_tree
        if tree.is_symlink() or not tree.is_dir():
            raise ReleaseArtifactError(
                f"required ZH data tree is missing or unsafe: {relative_tree!r}"
            )
        files: list[Path] = []
        for entry in tree.rglob("*"):
            if entry.is_symlink():
                raise ReleaseArtifactError(
                    f"symbolic link in required ZH data tree: "
                    f"{entry.relative_to(source_root).as_posix()!r}"
                )
            if entry.is_dir():
                continue
            if not entry.is_file():
                raise ReleaseArtifactError(
                    f"special entry in required ZH data tree: "
                    f"{entry.relative_to(source_root).as_posix()!r}"
                )
            files.append(entry)
        if not files:
            raise ReleaseArtifactError(
                f"required ZH data tree is empty: {relative_tree!r}"
            )
        tree_files.extend(sorted(files))

    expanded: list[ArtifactRule] = []
    for rule in artifact_rules(tag):
        sources = {contract.member: contract for contract in rule.content_sources}
        required = list(rule.required_files)
        for source in tree_files:
            data_relative = source.relative_to(data_source_root).as_posix()
            member = f"{rule.data_root}/{data_relative}"
            contract = ContentSource(
                member,
                source.relative_to(source_root).as_posix(),
                normalize_crlf=(
                    rule.normalize_text_crlf
                    and source.suffix.lower() in (".txt", ".des")
                ),
            )
            existing = sources.get(member)
            if existing is not None and existing != contract:
                raise ReleaseArtifactError(
                    f"conflicting content contract for archive member {member!r}"
                )
            sources[member] = contract
            if member not in required:
                required.append(member)
        expanded.append(
            replace(
                rule,
                required_files=tuple(required),
                content_sources=tuple(sources.values()),
            )
        )
    return tuple(expanded)


def _validate_member_names(
    names: list[str], *, root: str, archive_name: str
) -> None:
    seen: set[str] = set()
    seen_casefolded: set[str] = set()
    root_prefix = f"{root}/"
    for name in names:
        if not name or "\\" in name or "//" in name:
            raise ReleaseArtifactError(
                f"{archive_name}: invalid archive member path {name!r}"
            )
        canonical = name.rstrip("/")
        raw_parts = canonical.split("/")
        path = PurePosixPath(canonical)
        if (
            path.is_absolute()
            or any(part in ("", ".", "..") for part in raw_parts)
        ):
            raise ReleaseArtifactError(
                f"{archive_name}: unsafe archive member path {name!r}"
            )
        if canonical in seen:
            raise ReleaseArtifactError(
                f"{archive_name}: duplicate archive member {canonical!r}"
            )
        folded = canonical.casefold()
        if folded in seen_casefolded:
            raise ReleaseArtifactError(
                f"{archive_name}: case-insensitive member collision {canonical!r}"
            )
        seen.add(canonical)
        seen_casefolded.add(folded)
        if canonical != root and not canonical.startswith(root_prefix):
            raise ReleaseArtifactError(
                f"{archive_name}: member outside expected root {root!r}: "
                f"{canonical!r}"
            )


def _validate_zh_member_set(
    archive_name: str,
    members: list[tuple[str, bool]],
    rule: ArtifactRule,
) -> None:
    expected_files = {
        contract.member
        for contract in rule.content_sources
        if any(
            contract.source.startswith(f"{tree}/")
            for tree in ZH_DATA_TREES
        )
    }
    prefixes = tuple(
        f"{rule.data_root}/"
        f"{Path(tree).relative_to('crawl-ref/source/dat').as_posix()}"
        for tree in ZH_DATA_TREES
    )
    expected_directories: set[str] = set()
    for filename in expected_files:
        parent = PurePosixPath(filename).parent
        while any(
            str(parent) == prefix or str(parent).startswith(f"{prefix}/")
            for prefix in prefixes
        ):
            expected_directories.add(str(parent))
            parent = parent.parent

    for name, is_directory in members:
        canonical = name.rstrip("/")
        if not any(
            canonical == prefix or canonical.startswith(f"{prefix}/")
            for prefix in prefixes
        ):
            continue
        expected = expected_directories if is_directory else expected_files
        if canonical not in expected:
            kind = "directory" if is_directory else "file"
            raise ReleaseArtifactError(
                f"{archive_name}: unexpected ZH archive {kind}: "
                f"{canonical!r}"
            )


def _validate_zip(path: Path, rule: ArtifactRule, source_root: Path) -> None:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            _validate_member_names(
                [info.filename for info in infos],
                root=rule.root,
                archive_name=path.name,
            )
            _validate_zh_member_set(
                path.name,
                [(info.filename, info.is_dir()) for info in infos],
                rule,
            )
            permissions: dict[str, int] = {}
            for info in infos:
                raw_mode = (info.external_attr >> 16) & 0o177777
                file_type = raw_mode & 0o170000
                if file_type == stat.S_IFLNK:
                    raise ReleaseArtifactError(
                        f"{path.name}: symbolic links are not allowed: "
                        f"{info.filename!r}"
                    )
                if file_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ReleaseArtifactError(
                        f"{path.name}: special members are not allowed: "
                        f"{info.filename!r}"
                    )
                permissions[info.filename.rstrip("/")] = raw_mode & 0o777
            corrupt = archive.testzip()
            if corrupt is not None:
                raise ReleaseArtifactError(
                    f"{path.name}: corrupt ZIP member {corrupt!r}"
                )
            sizes = {
                info.filename.rstrip("/"): info.file_size
                for info in infos
                if not info.is_dir()
            }
            content = {
                contract.member: archive.read(contract.member)
                for contract in rule.content_sources
                if contract.member in sizes
            }
    except (OSError, zipfile.BadZipFile) as error:
        raise ReleaseArtifactError(f"{path.name}: invalid ZIP: {error}") from error
    _validate_required_files(path.name, sizes, rule.required_files)
    _validate_executables(path.name, permissions, rule.executable_files)
    _validate_content_sources(path.name, content, rule.content_sources, source_root)


def _validate_required_files(
    archive_name: str, sizes: dict[str, int], required_files: tuple[str, ...]
) -> None:
    for required in required_files:
        if required not in sizes:
            raise ReleaseArtifactError(
                f"{archive_name}: missing required file {required!r}"
            )
        if sizes[required] <= 0:
            raise ReleaseArtifactError(
                f"{archive_name}: required file is empty: {required!r}"
            )


def _validate_executables(
    archive_name: str, permissions: dict[str, int], executable_files: tuple[str, ...]
) -> None:
    for executable in executable_files:
        if permissions.get(executable, 0) & 0o111 == 0:
            raise ReleaseArtifactError(
                f"{archive_name}: executable bit is missing: {executable!r}"
            )


def _validate_content_sources(
    archive_name: str,
    content: dict[str, bytes],
    contracts: tuple[ContentSource, ...],
    source_root: Path,
) -> None:
    for contract in contracts:
        source = source_root / contract.source
        if source.is_symlink() or not source.is_file():
            raise ReleaseArtifactError(
                f"{archive_name}: required source file is missing or unsafe: "
                f"{contract.source!r}"
            )
        expected = source.read_bytes()
        if not expected:
            raise ReleaseArtifactError(
                f"{archive_name}: required source file is empty: {contract.source!r}"
            )
        actual = content.get(contract.member)
        if actual is None:
            continue
        if contract.normalize_crlf:
            actual = actual.replace(b"\r\n", b"\n")
        if actual != expected:
            raise ReleaseArtifactError(
                f"{archive_name}: archived content differs from "
                f"{contract.source!r}: {contract.member!r}"
            )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_release(
    artifacts_dir: Path,
    source_root: Path,
    tag: str,
    commit: str,
    checksums_path: Path,
    manifest_path: Path,
) -> None:
    if RELEASE_TAG_RE.fullmatch(tag) is None:
        raise ReleaseArtifactError(
            "release tag must match the first-release convention "
            "'0.34.1-zhN' with N >= 1"
        )
    if COMMIT_RE.fullmatch(commit) is None:
        raise ReleaseArtifactError("commit must be a lowercase 40-character SHA-1")
    if not artifacts_dir.is_dir():
        raise ReleaseArtifactError(
            f"artifact directory does not exist: {artifacts_dir}"
        )
    if source_root.is_symlink() or not source_root.is_dir():
        raise ReleaseArtifactError(
            f"source root does not exist or is unsafe: {source_root}"
        )

    entries = list(artifacts_dir.iterdir())
    symlinks = sorted(path.name for path in entries if path.is_symlink())
    if symlinks:
        raise ReleaseArtifactError(
            f"symbolic links in artifact set are not allowed: {symlinks}"
        )

    rules = release_rules(tag, source_root)
    expected = {rule.filename for rule in rules}
    actual = {path.name for path in entries if path.is_file()}
    directories = sorted(path.name for path in entries if path.is_dir())
    if directories:
        raise ReleaseArtifactError(
            f"unexpected directories in artifact set: {directories}"
        )
    special_entries = sorted(
        path.name
        for path in entries
        if not path.is_file() and not path.is_dir() and not path.is_symlink()
    )
    if special_entries:
        raise ReleaseArtifactError(
            f"special entries in artifact set are not allowed: {special_entries}"
        )
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        raise ReleaseArtifactError(
            f"artifact set mismatch; missing={missing}, unexpected={unexpected}"
        )

    for rule in rules:
        path = artifacts_dir / rule.filename
        if rule.archive_type == "zip":
            _validate_zip(path, rule, source_root)
        else:
            raise ReleaseArtifactError(
                f"{rule.filename}: unknown archive type {rule.archive_type!r}"
            )

    digests = [(rule.filename, _sha256(artifacts_dir / rule.filename)) for rule in rules]
    checksums = "".join(f"{digest}  {name}\n" for name, digest in digests)
    manifest = (
        f"Release tag: {tag}\n"
        f"Commit: {commit}\n"
        "Included: Windows Tiles\n"
        "Deferred: macOS (CI artifact only; acceptance environment unavailable); "
        "Linux (CI build only); Android "
        "(signed APK and physical-device acceptance pending)\n"
        "Artifacts:\n"
        + "".join(f"- {name}: sha256:{digest}\n" for name, digest in digests)
    )
    checksums_path.write_text(checksums, encoding="utf-8")
    manifest_path.write_text(manifest, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--checksums", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    try:
        validate_release(
            args.artifacts_dir,
            args.source_root,
            args.tag,
            args.commit,
            args.checksums,
            args.manifest,
        )
    except ReleaseArtifactError as error:
        parser.error(str(error))
    print(f"OK: validated 1 Windows release archive for {args.tag}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
