#!/bin/bash
# review_final_gate.sh — Run the single locked schema-v4 final verification.
#
# Usage:
#   bash .claude/scripts/review_final_gate.sh <candidate-branch> [target-branch]
#       [--retry-failed] [--recover-stale]
#
# Run from the clean target checkout. The candidate must be checked out in a
# clean linked worktree and already have a complete immutable readiness bundle.

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
    sed -n '2,10p' "$0"
    exit 0
fi

TARGET_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "ERROR: final gate must run inside the target Git checkout." >&2
    exit 20
}
BUNDLE_SCRIPT="$TARGET_ROOT/.claude/scripts/review_bundle.py"
CLASSIFIER="$TARGET_ROOT/.claude/scripts/classify_reviewers.py"
VERIFIER="$TARGET_ROOT/.claude/scripts/verify_zh.sh"
CONTRACT="$TARGET_ROOT/.claude/scripts/data/review_verification_contract_v5.json"

CANDIDATE_BRANCH="$1"
shift
TARGET_BRANCH=$(git -C "$TARGET_ROOT" symbolic-ref --quiet --short HEAD 2>/dev/null || true)
if [[ $# -gt 0 && "${1:-}" != --* ]]; then
    TARGET_BRANCH="$1"
    shift
fi
[[ -n "$TARGET_BRANCH" ]] || {
    echo "ERROR: target branch is required from a detached checkout." >&2
    exit 20
}

EXTRA_ARGS=()
for arg in "$@"; do
    case "$arg" in
        --retry-failed|--recover-stale) EXTRA_ARGS+=("$arg") ;;
        *) echo "ERROR: unknown option: $arg" >&2; exit 20 ;;
    esac
done

for required in "$BUNDLE_SCRIPT" "$CLASSIFIER" "$VERIFIER" "$CONTRACT"; do
    [[ -f "$required" && ! -L "$required" ]] || {
        echo "ERROR: trusted target control-plane file is missing or unsafe: $required" >&2
        exit 20
    }
done

TARGET_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${TARGET_BRANCH}^{commit}" 2>/dev/null) || {
    echo "ERROR: target branch does not name a commit: $TARGET_BRANCH" >&2
    exit 20
}
CANDIDATE_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${CANDIDATE_BRANCH}^{commit}" 2>/dev/null) || {
    echo "ERROR: candidate branch does not name a commit: $CANDIDATE_BRANCH" >&2
    exit 20
}

CURRENT_TARGET_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify HEAD)
[[ "$CURRENT_TARGET_HEAD" == "$TARGET_HEAD" ]] || {
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
    echo "ERROR: candidate worktree is dirty." >&2
    exit 15
}

GLOSSARY="$WORKTREE_PATH/docs/glossary.md"
[[ -f "$GLOSSARY" && ! -L "$GLOSSARY" ]] || {
    echo "ERROR: candidate glossary is missing or unsafe: $GLOSSARY" >&2
    exit 15
}
GLOSSARY_SHA256=$(sha256sum "$GLOSSARY" | awk '{print $1}')

DESCRIPTION=$(python3 "$BUNDLE_SCRIPT" describe \
    --repo "$WORKTREE_PATH" \
    --target "$TARGET_HEAD" \
    --candidate "$CANDIDATE_HEAD" \
    --glossary-sha256 "$GLOSSARY_SHA256" \
    --classifier "$CLASSIFIER") || exit $?
BUNDLE_ID=$(printf '%s' "$DESCRIPTION" | python3 -c \
    'import json,sys; print(json.load(sys.stdin)["bundle_id"])')

echo "=== Schema-v4 Final Review Gate ==="
echo "Target:    $TARGET_BRANCH @ $TARGET_HEAD"
echo "Candidate: $CANDIDATE_BRANCH @ $CANDIDATE_HEAD"
echo "Bundle:    $BUNDLE_ID"

set +e
RESULT=$(python3 "$BUNDLE_SCRIPT" run-final \
    --repo "$WORKTREE_PATH" \
    --bundle "$BUNDLE_ID" \
    --target-repo "$TARGET_ROOT" \
    --verifier "$VERIFIER" \
    --contract "$CONTRACT" \
    ${EXTRA_ARGS+"${EXTRA_ARGS[@]}"} 2>&1)
RESULT_RC=$?
set -e
printf '%s\n' "$RESULT"

FINAL_TARGET_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${TARGET_BRANCH}^{commit}" 2>/dev/null || true)
FINAL_CANDIDATE_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${CANDIDATE_BRANCH}^{commit}" 2>/dev/null || true)
if [[ "$FINAL_TARGET_HEAD" != "$TARGET_HEAD" || "$FINAL_CANDIDATE_HEAD" != "$CANDIDATE_HEAD" ]]; then
    echo "ERROR: a branch ref moved while the final gate was running." >&2
    exit 15
fi
exit "$RESULT_RC"
