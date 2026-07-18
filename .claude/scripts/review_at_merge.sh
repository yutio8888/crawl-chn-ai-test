#!/bin/bash
# review_at_merge.sh — Read-only schema-v4 merge authorization validator.
#
# Usage (run from the clean target checkout):
#   bash .claude/scripts/review_at_merge.sh <candidate-branch> [target-branch]
#
# This command never builds, tests, creates, repairs, or updates review
# evidence. It prints the exact approved candidate OID for an ff-only merge.

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
    sed -n '2,8p' "$0"
    exit 0
fi
if [[ $# -gt 2 ]]; then
    echo "ERROR: unexpected arguments; schema-v2 --record-verdict is no longer authorization." >&2
    exit 20
fi

TARGET_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
    echo "ERROR: merge gate must run inside the target Git checkout." >&2
    exit 20
}
BUNDLE_SCRIPT="$TARGET_ROOT/.claude/scripts/review_bundle.py"
CLASSIFIER="$TARGET_ROOT/.claude/scripts/classify_reviewers.py"
for trusted in "$BUNDLE_SCRIPT" "$CLASSIFIER"; do
    [[ -f "$trusted" && ! -L "$trusted" ]] || {
        echo "ERROR: trusted target gate file is missing or unsafe: $trusted" >&2
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

START_TARGET_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${TARGET_BRANCH}^{commit}" 2>/dev/null) || {
    echo "ERROR: target branch does not name a commit: $TARGET_BRANCH" >&2
    exit 20
}
START_CANDIDATE_HEAD=$(git -C "$TARGET_ROOT" rev-parse --verify "${CANDIDATE_BRANCH}^{commit}" 2>/dev/null) || {
    echo "ERROR: candidate branch does not name a commit: $CANDIDATE_BRANCH" >&2
    exit 20
}

[[ "$(git -C "$TARGET_ROOT" rev-parse --verify HEAD)" == "$START_TARGET_HEAD" ]] || {
    echo "ERROR: target checkout HEAD does not match $TARGET_BRANCH." >&2
    exit 15
}
[[ -z "$(git -C "$TARGET_ROOT" status --porcelain=v1 --untracked-files=all)" ]] || {
    echo "ERROR: target checkout is dirty." >&2
    exit 15
}
git -C "$TARGET_ROOT" merge-base --is-ancestor \
    "$START_TARGET_HEAD" "$START_CANDIDATE_HEAD" || {
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
[[ "$(git -C "$WORKTREE_PATH" rev-parse --verify HEAD)" == "$START_CANDIDATE_HEAD" ]] || {
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
    --target "$START_TARGET_HEAD" \
    --candidate "$START_CANDIDATE_HEAD" \
    --glossary-sha256 "$GLOSSARY_SHA256" \
    --classifier "$CLASSIFIER") || exit $?
BUNDLE_ID=$(printf '%s' "$DESCRIPTION" | python3 -c \
    'import json,sys; print(json.load(sys.stdin)["bundle_id"])')
BUNDLE_PATH=$(printf '%s' "$DESCRIPTION" | python3 -c \
    'import json,sys; print(json.load(sys.stdin)["bundle_path"])')
REVIEWER_COUNT=$(printf '%s' "$DESCRIPTION" | python3 -c \
    'import json,sys; print(len(json.load(sys.stdin)["routing"]["reviewers"]))')

recheck_refs() {
    local target_now candidate_now
    target_now=$(git -C "$TARGET_ROOT" rev-parse --verify "${TARGET_BRANCH}^{commit}" 2>/dev/null || true)
    candidate_now=$(git -C "$TARGET_ROOT" rev-parse --verify "${CANDIDATE_BRANCH}^{commit}" 2>/dev/null || true)
    [[ "$target_now" == "$START_TARGET_HEAD" && "$candidate_now" == "$START_CANDIDATE_HEAD" ]]
}

echo "=== Read-only Schema-v4 Merge Gate ==="
echo "Target:    $TARGET_BRANCH @ $START_TARGET_HEAD"
echo "Candidate: $CANDIDATE_BRANCH @ $START_CANDIDATE_HEAD"
echo "Bundle:    $BUNDLE_ID"

if [[ "$REVIEWER_COUNT" -eq 0 ]]; then
    recheck_refs || {
        echo "ERROR: a branch ref moved during merge authorization." >&2
        exit 15
    }
    echo '{"approved":true,"exit_code":0,"state":"MERGEABLE","valid":true}'
    echo "Approved candidate OID: $START_CANDIDATE_HEAD"
    echo "Merge with: git merge --ff-only $START_CANDIDATE_HEAD"
    exit 0
fi

if [[ ! -d "$BUNDLE_PATH" ]]; then
    recheck_refs || {
        echo "ERROR: a branch ref moved during merge authorization." >&2
        exit 15
    }
    python3 - "$BUNDLE_ID" <<'PY'
import json, sys
print(json.dumps({
    "approved": False,
    "bundle_id": sys.argv[1],
    "exit_code": 11,
    "state": "FINAL_GATE_REQUIRED",
    "valid": False,
}, sort_keys=True, separators=(",", ":")))
PY
    echo "Final evidence is missing. Prepare readiness, then run review_final_gate.sh." >&2
    exit 11
fi

set +e
STATUS_JSON=$(python3 "$BUNDLE_SCRIPT" status \
    --repo "$WORKTREE_PATH" --bundle "$BUNDLE_ID" 2>&1)
STATUS_RC=$?
set -e

recheck_refs || {
    echo "$STATUS_JSON"
    echo "ERROR: a branch ref moved during merge authorization." >&2
    exit 15
}
printf '%s\n' "$STATUS_JSON"
if [[ "$STATUS_RC" -eq 0 ]]; then
    echo "Approved candidate OID: $START_CANDIDATE_HEAD"
    echo "Merge with: git merge --ff-only $START_CANDIDATE_HEAD"
else
    echo "Merge is not authorized; inspect the schema-v4 state above." >&2
fi
exit "$STATUS_RC"
