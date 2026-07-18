#!/bin/bash
# deploy.sh — cross-compile DCSS tiles + deploy to Windows target
#
# Usage:
#   bash .claude/scripts/deploy.sh [target_dir]
#   bash .claude/scripts/deploy.sh --validate-init <init_file>
#
# Default target_dir: ${DCSS_DEPLOY_ROOT:-.artifacts}/windows-tiles
# Override with an argument, DCSS_WINDOWS_DEPLOY_DIR, or .dcss-paths.conf.
#
# Builds from .worktrees/mingw-tiles (auto-synced) to keep .o files
# separate from the WSL console build in the main worktree.
# Uses ccache automatically if available.
#
# Steps:
#   1. Validate the versioned/local Chinese config and required Maple font
#   2. Sync .worktrees/mingw-tiles to current HEAD
#   3. Cross-compile Windows tiles binary (with ccache)
#   4. Copy crawl.exe, dat/, init.txt, and the configured font to target
#   5. Verify the deployed Chinese runtime assets
#   6. Clear saves/db/ cache so BerkeleyDB regenerates from updated text files

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
source "$SCRIPT_DIR/lib/path_utils.sh"
WT="$REPO_ROOT/.worktrees/mingw-tiles"
WT_SOURCE="$WT/crawl-ref/source"
MAPLE_FONT="MapleMono-NF-CN-Regular.ttf"
VERSIONED_INIT="$REPO_ROOT/crawl-ref/source/init.zh.txt"
LOCAL_INIT="$REPO_ROOT/crawl-ref/source/init.txt"

effective_init_value() {
    local init_file="$1"
    local option="$2"

    awk -v wanted="$option" '
        function trim(value) {
            sub(/^[[:space:]]+/, "", value)
            sub(/[[:space:]]+$/, "", value)
            return value
        }
        {
            line = $0
            sub(/\r$/, "", line)
            sub(/[[:space:]]*#.*/, "", line)
            equals = index(line, "=")
            if (!equals)
                next
            name = trim(substr(line, 1, equals - 1))
            value = trim(substr(line, equals + 1))
            if (name ~ /:$/) {
                sub(/[[:space:]]*:[[:space:]]*$/, "", name)
                aliases[name] = value
                next
            }
            if (name in aliases)
                name = aliases[name]
            if (name != wanted)
                next
            last = value
            found = 1
        }
        END {
            if (!found)
                exit 1
            print last
        }
    ' "$init_file"
}

validate_chinese_init() {
    local init_file="$1"
    local role actual

    actual="$(effective_init_value "$init_file" language)" || return 1
    [ "$actual" = "zh" ] || return 1
    for role in crt msg stat tip lbl; do
        actual="$(effective_init_value "$init_file" "tile_font_${role}_file")" \
            || return 1
        [ "$actual" = "dat/tiles/$MAPLE_FONT" ] || return 1
    done
}

if [ "${1:-}" = "--validate-init" ]; then
    if [ "$#" -ne 2 ]; then
        echo "Usage: $0 --validate-init <init_file>" >&2
        exit 2
    fi
    if validate_chinese_init "$2"; then
        echo "Chinese init configuration is valid: $2"
        exit 0
    fi
    echo "ERROR: effective Chinese init configuration is invalid: $2" >&2
    exit 1
fi

dcss_load_repo_path_config "$REPO_ROOT" "${DCSS_PATH_CONFIG:-}"
DEPLOY_ROOT="${DCSS_DEPLOY_ROOT:-.artifacts}"
TARGET_INPUT="${1:-${DCSS_WINDOWS_DEPLOY_DIR:-$DEPLOY_ROOT/windows-tiles}}"
TARGET="$(dcss_resolve_repo_path "$REPO_ROOT" "$TARGET_INPUT")"

echo "=== Deploying to $TARGET ==="

# Validate mingw-tiles worktree exists
if [ ! -d "$WT_SOURCE" ]; then
    echo "ERROR: mingw-tiles worktree not found at $WT"
    echo "Create it with: cd $REPO_ROOT && git worktree add .worktrees/mingw-tiles --detach chn-0.34.1-base"
    exit 1
fi

# 1. Build and validate the exact deployment config before an expensive build.
if [ ! -f "$VERSIONED_INIT" ] || ! validate_chinese_init "$VERSIONED_INIT"; then
    echo "ERROR: versioned Chinese init template is missing or invalid: $VERSIONED_INIT" >&2
    exit 1
fi

DEPLOY_INIT="$(mktemp /tmp/crawl-deploy-init.XXXXXX)"
cleanup() {
    rm -f "$DEPLOY_INIT"
}
trap cleanup EXIT

# Preserve user preferences, then append the canonical Chinese options so they
# are the final effective assignments even when the local file uses duplicates
# or include directives.
if [ -f "$LOCAL_INIT" ]; then
    cp "$LOCAL_INIT" "$DEPLOY_INIT"
else
    : > "$DEPLOY_INIT"
fi
printf '\n# Enforced Chinese deployment options (must remain last).\n' >> "$DEPLOY_INIT"
cat "$VERSIONED_INIT" >> "$DEPLOY_INIT"
INIT_SOURCE="$DEPLOY_INIT"
if ! validate_chinese_init "$INIT_SOURCE"; then
    echo "ERROR: failed to construct an effective Chinese deployment config." >&2
    exit 1
fi

FONT_SOURCE=""
for candidate in \
    "$REPO_ROOT/crawl-ref/source/dat/tiles/$MAPLE_FONT" \
    "$REPO_ROOT/crawl-ref/source/contrib/fonts/$MAPLE_FONT" \
    "$WT_SOURCE/dat/tiles/$MAPLE_FONT" \
    "$WT_SOURCE/contrib/fonts/$MAPLE_FONT"
do
    if [ -s "$candidate" ]; then
        FONT_SOURCE="$candidate"
        break
    fi
done
if [ -z "$FONT_SOURCE" ]; then
    echo "ERROR: required Chinese tiles font not found: $MAPLE_FONT" >&2
    echo "Install it under crawl-ref/source/dat/tiles/ or crawl-ref/source/contrib/fonts/." >&2
    exit 1
fi
echo "[1/6] Chinese deployment assets validated."
echo "       init: local preferences + $VERSIONED_INIT final overrides"
echo "       font: $FONT_SOURCE"

# 2. Sync worktree to main worktree HEAD (local only)
MAIN_HEAD="$(cd "$REPO_ROOT" && git rev-parse HEAD)"
echo "[2/6] Syncing mingw-tiles worktree to $MAIN_HEAD..."
cd "$WT"
if [ -n "$(git status --porcelain --untracked-files=all)" ]; then
    echo "ERROR: $WT has local changes; refusing destructive sync." >&2
    echo "Commit, stash, or remove them explicitly, then retry." >&2
    exit 1
fi
git reset --hard "$MAIN_HEAD"
echo "       Now at: $(git rev-parse --short HEAD)"

# 3. Cross-compile with ccache
echo "[3/6] Cross-compiling Windows tiles with ccache..."
cd "$WT_SOURCE"
make CROSSHOST=x86_64-w64-mingw32 TILES=y -j8

# 4. Copy binary and data.
echo "[4/6] Copying crawl.exe and data files..."
mkdir -p "$TARGET"
cp crawl.exe "$TARGET/"
mkdir -p "$TARGET/dat"
cp -r dat/* "$TARGET/dat/"
mkdir -p "$TARGET/dat/tiles"
cp "$INIT_SOURCE" "$TARGET/init.txt"
cp "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"

# 5. Fail closed if the target does not contain the exact required assets.
echo "[5/6] Verifying deployed Chinese runtime assets..."
test -s "$TARGET/crawl.exe"
validate_chinese_init "$TARGET/init.txt"
cmp -s "$INIT_SOURCE" "$TARGET/init.txt"
cmp -s "$FONT_SOURCE" "$TARGET/dat/tiles/$MAPLE_FONT"

# 6. Clear DB cache to force regeneration from updated text files.
#    BerkeleyDB caches text file content in saves/db/*.db; if only the
#    C++ binary changed but text files have unchanged mtimes, the cache
#    won't auto-rebuild and stale data persists.
echo "[6/6] Clearing DB cache..."
rm -rf "$TARGET/saves/db/"

echo "=== Done: $TARGET/crawl.exe ($(stat -c%s "$TARGET/crawl.exe") bytes) ==="
echo "ccache stats:"
ccache -s 2>/dev/null || true
