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

# CI must read upstream tags before any version-generating build. Discover
# exact refs first: a fetch refspec may contain only one wildcard, whereas
# '*-a[0-9]*' is a tag-list pattern with two.
if [[ "${1:-}" == "--fetch-upstream-tags" && $# == 1 ]]; then
    upstream_url=https://github.com/crawl/crawl
    refs=$(git ls-remote --tags --refs "$upstream_url" 'refs/tags/*-a[0-9]*') \
        || die "failed to list upstream alpha tags"
    refspecs=()
    while read -r object ref; do
        if [[ "$ref" =~ ^refs/tags/[0-9]+\.[0-9]+-a[0-9]+$ ]]; then
            refspecs+=("$ref:$ref")
        fi
    done <<< "$refs"
    [[ ${#refspecs[@]} -gt 0 ]] || die "upstream alpha tag list is empty"
    git fetch --no-tags "$upstream_url" "${refspecs[@]}" \
        || die "failed to fetch upstream alpha tags"
elif [[ $# != 0 ]]; then
    die "usage: ensure_version_info.sh [--fetch-upstream-tags]"
fi

describe_flags=(--match '*-a[0-9]*' --match '*-trunk-[0-9][0-9][0-9]')
trunk_tag_re='^[0-9]+\.[0-9]+-trunk-(00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})$'

if [[ "${GITHUB_REF_TYPE:-}" == "tag" ]]; then
    tag="${GITHUB_REF_NAME:-}"
    commit="${GITHUB_SHA:-}"

    [[ "$tag" =~ $trunk_tag_re || "$tag" =~ ^0\.34\.1-zh[1-9][0-9]*-[1-9][0-9]*-(00[1-9]|0[1-9][0-9]|[1-9][0-9]{2})$ ]] \
        || die "release tag must match X.Y-trunk-NNN or 0.34.1-zhA-B-CCC (001-999)"
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

    if [[ "$tag" =~ $trunk_tag_re ]]; then
        alpha_tag=$(git describe --abbrev=0 --match '*-a[0-9]*' "$commit" 2>/dev/null) \
            || die "cannot find an annotated upstream alpha tag for $commit"
        [[ "$alpha_tag" =~ ^([0-9]+\.[0-9]+)-a[0-9]+$ ]] \
            || die "invalid upstream alpha tag $alpha_tag"
        [[ "${tag%%-trunk-*}" == "${BASH_REMATCH[1]}" ]] \
            || die "trunk major version ${tag%%-trunk-*} differs from upstream $alpha_tag"
    fi

    printf '%s\n' "$tag" > "$release_ver"
    echo "Prepared release version $tag at $commit"
else
    git describe --abbrev=0 --match '*-a[0-9]*' HEAD >/dev/null 2>&1 \
        || die "cannot find an annotated upstream alpha tag for HEAD"
    version=$(git describe "${describe_flags[@]}" 2>/dev/null) \
        || die "cannot describe development version"
    printf '%s\n' "$version" > "$release_ver"
fi
