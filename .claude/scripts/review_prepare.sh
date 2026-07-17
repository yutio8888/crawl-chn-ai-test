#!/bin/bash
# review_prepare.sh — Create the immutable schema-v3 bundle before review.
#
# Usage (run from the clean target checkout):
#   bash .claude/scripts/review_prepare.sh <candidate-branch> [target-branch]

set -euo pipefail

unset BASH_ENV ENV CDPATH GIT_EXEC_PATH GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE
unset GIT_OBJECT_DIRECTORY GIT_ALTERNATE_OBJECT_DIRECTORIES GIT_COMMON_DIR
unset GIT_CEILING_DIRECTORIES GIT_DISCOVERY_ACROSS_FILESYSTEM GIT_EXTERNAL_DIFF
unset GIT_DIFF_OPTS PYTHONPATH PYTHONHOME LD_PRELOAD LD_LIBRARY_PATH
for env_name in ${!GIT_CONFIG_@}; do unset "$env_name"; done
unset -f git python3 sha256sum awk sed 2>/dev/null || true
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH
hash -r

if [[ $# -lt 1 || "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    sed -n '2,5p' "$0"
    exit 0
fi
if [[ $# -gt 2 || "${1:-}" == -* || "${2:-}" == -* ]]; then
    echo "ERROR: expected <candidate-branch> [target-branch]." >&2
    exit 20
fi

TARGET_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "ERROR: review preparation must run inside the target Git checkout." >&2
    exit 20
}
BUNDLE_SCRIPT="$TARGET_ROOT/.claude/scripts/review_bundle.py"
CLASSIFIER="$TARGET_ROOT/.claude/scripts/classify_reviewers.py"
for trusted in "$BUNDLE_SCRIPT" "$CLASSIFIER"; do
    [[ -f "$trusted" && ! -L "$trusted" ]] || {
        echo "ERROR: trusted target preparation file is missing or unsafe: $trusted" >&2
        exit 20
    }
done

CANDIDATE_BRANCH="$1"
TARGET_BRANCH="${2:-$(git -C "$TARGET_ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null || true)}"
[[ -n "$TARGET_BRANCH" ]] || {
    echo "ERROR: target branch is required from a detached checkout." >&2
    exit 20
}
[[ "$CANDIDATE_BRANCH" != "$TARGET_BRANCH" ]] || {
    echo "ERROR: candidate and target branches must differ." >&2
    exit 20
}

TARGET_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${TARGET_BRANCH}^{commit}" 2>/dev/null) || {
    echo "ERROR: target branch does not name a commit: $TARGET_BRANCH" >&2
    exit 20
}
CANDIDATE_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${CANDIDATE_BRANCH}^{commit}" 2>/dev/null) || {
    echo "ERROR: candidate branch does not name a commit: $CANDIDATE_BRANCH" >&2
    exit 20
}
[[ "$(git -C "$TARGET_ROOT" rev-parse --verify HEAD)" == "$TARGET_HEAD" ]] || {
    echo "ERROR: target checkout HEAD does not match $TARGET_BRANCH." >&2
    exit 15
}
[[ -z "$(git -C "$TARGET_ROOT" status --porcelain=v1 --untracked-files=all)" ]] || {
    echo "ERROR: target checkout is dirty." >&2
    exit 15
}
git -C "$TARGET_ROOT" merge-base --is-ancestor "$TARGET_HEAD" "$CANDIDATE_HEAD" || {
    echo "ERROR: target head is not an ancestor of candidate head." >&2
    exit 15
}

WORKTREE_PATH=$(git -C "$TARGET_ROOT" worktree list --porcelain | awk \
    -v wanted="refs/heads/$CANDIDATE_BRANCH" '
        $1 == "worktree" { path = substr($0, 10) }
        $1 == "branch" && $2 == wanted && !found { print path; found = 1 }
    ')
[[ -n "$WORKTREE_PATH" && -d "$WORKTREE_PATH" ]] || {
    echo "ERROR: candidate branch must be checked out in a linked worktree." >&2
    exit 15
}
[[ "$(git -C "$WORKTREE_PATH" rev-parse --verify HEAD)" == "$CANDIDATE_HEAD" ]] || {
    echo "ERROR: candidate worktree HEAD does not match the candidate ref." >&2
    exit 15
}
[[ -z "$(git -C "$WORKTREE_PATH" status --porcelain=v1 --untracked-files=all)" ]] || {
    echo "ERROR: candidate worktree is dirty; commit the exact review diff first." >&2
    exit 15
}

GLOSSARY="$WORKTREE_PATH/docs/glossary.md"
[[ -f "$GLOSSARY" && ! -L "$GLOSSARY" ]] || {
    echo "ERROR: candidate glossary is missing or unsafe: $GLOSSARY" >&2
    exit 15
}
GLOSSARY_SHA256=$(sha256sum "$GLOSSARY" | awk '{print $1}')

RESULT=$(python3 "$BUNDLE_SCRIPT" create \
    --repo "$WORKTREE_PATH" \
    --target "$TARGET_HEAD" \
    --candidate "$CANDIDATE_HEAD" \
    --glossary-sha256 "$GLOSSARY_SHA256" \
    --classifier "$CLASSIFIER")

FINAL_TARGET_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${TARGET_BRANCH}^{commit}" 2>/dev/null || true)
FINAL_CANDIDATE_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${CANDIDATE_BRANCH}^{commit}" 2>/dev/null || true)
if [[ "$FINAL_TARGET_HEAD" != "$TARGET_HEAD" || "$FINAL_CANDIDATE_HEAD" != "$CANDIDATE_HEAD" ]]; then
    echo "ERROR: a branch ref moved while the review bundle was being prepared." >&2
    exit 15
fi

printf '%s\n' "$RESULT"
