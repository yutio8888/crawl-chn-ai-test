#!/usr/bin/env bash
# Prepare release_ver while preserving the annotated identity of release tags.

set -euo pipefail

die() {
    echo "ensure_version_info: $*" >&2
    exit 1
}

repo_root=$(git rev-parse --show-toplevel 2>/dev/null) \
    || die "must run inside a Git worktree"
release_ver="$repo_root/crawl-ref/source/util/release_ver"

if [[ "${GITHUB_REF_TYPE:-}" == "tag" ]]; then
    tag="${GITHUB_REF_NAME:-}"
    commit="${GITHUB_SHA:-}"

    [[ "$tag" =~ ^0\.34\.1-zh[1-9][0-9]*-[1-9][0-9]*-(00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})$ ]] \
        || die "release tag must match 0.34.1-zhA-B-CCC with A and B >= 1 and CCC in 001-999"
    [[ "$commit" =~ ^[0-9a-f]{40}$ ]] \
        || die "GITHUB_SHA must be a lowercase 40-character commit SHA"

    # actions/checkout can replace an annotated tag ref with a lightweight ref
    # to its commit. Restore the exact remote tag object before git describe is
    # used by the Makefile and util/gen_ver.pl.
    git fetch --force --no-tags origin \
        "refs/tags/$tag:refs/tags/$tag" \
        || die "failed to fetch release tag $tag from origin"

    tag_type=$(git cat-file -t "$tag" 2>/dev/null) \
        || die "release tag $tag does not exist after fetch"
    [[ "$tag_type" == "tag" ]] \
        || die "release tag $tag must be annotated, got object type $tag_type"

    tag_commit=$(git rev-parse "$tag^{}" 2>/dev/null) \
        || die "release tag $tag cannot be dereferenced"
    [[ "$tag_commit" == "$commit" ]] \
        || die "release tag $tag points to $tag_commit, expected $commit"

    head_commit=$(git rev-parse HEAD 2>/dev/null) \
        || die "cannot resolve checkout HEAD"
    [[ "$head_commit" == "$commit" ]] \
        || die "checkout HEAD is $head_commit, expected $commit"

    described=$(git describe --exact-match "$commit" 2>/dev/null) \
        || die "git describe cannot resolve $commit as an exact annotated tag"
    [[ "$described" == "$tag" ]] \
        || die "git describe resolved $described, expected $tag"

    printf '%s\n' "$tag" > "$release_ver"
    echo "Prepared release version $tag at $commit"
else
    git describe 2>/dev/null > "$release_ver" \
        || printf '%s\n' "0.0.0-dev0" > "$release_ver"
fi
