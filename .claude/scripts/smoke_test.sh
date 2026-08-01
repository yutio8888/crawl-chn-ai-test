#!/bin/bash
# smoke_test.sh — Headless crawl smoke test for fatal i18n issues.
#
# Starts crawl in ZH mode and checks startup output for three fatal
# categories:
#   1. Protocol leaks — English identifiers in ZH output
#   2. English residue — core UI text still in English
#   3. Crashes — segfault, assertion, abort
#
# Exit codes:
#   0 — normal run, no issues found (or empty output with 0 exit)
#   1 — protocol leak, English residue, or crash detected
#   2 — binary or portable timeout helper missing
#   124 — child timeout (output still scanned for issues)
#
# Note: crawl's ncurses console mode reads from /dev/tty, not stdin,
# so we cannot drive in-game navigation via pipes. This test checks
# startup output only (init messages, Lua errors, crash traces).
# Interactive testing requires manual gameplay or an expect-based driver.
#
# Exits non-zero when a blocking protocol leak, English residue, or crash is
# detected. Integration: verify_zh.sh risk gate.

set -euo pipefail

SOURCE_DIR="crawl-ref/source"
CRAWL="$SOURCE_DIR/crawl"
ZH_OUT="/tmp/crawl_smoke_zh_$$.txt"
# Long enough for first-run TextDB cache regeneration inside the isolated
# CRAWL_DIR: with an empty cache, database.cc:355-405 regenerates all parent
# DBs plus their zh children before the UI appears, and the Debug binary is
# slower. The 124 contract is unchanged: a real hang still times out and the
# transcript is still scanned.
TIMEOUT_SEC=60
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TIMEOUT_RUNNER="$SCRIPT_DIR/run_with_timeout.py"

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# Exit 2 if binary missing
if [ ! -x "$CRAWL" ]; then
    echo "Crawl binary not found at $CRAWL" >&2
    exit 2
fi

# Exit 2 if the repository-owned timeout helper is missing
if [ ! -f "$TIMEOUT_RUNNER" ]; then
    echo "Portable timeout helper not found at $TIMEOUT_RUNNER" >&2
    exit 2
fi

# Isolate crawl's writable user directory into a fresh temp dir. Without
# this, macOS falls back to ~/Library/Application Support/Dungeon Crawl Stone
# Soup (initfile.cc:4730-4736), which sandboxed runners cannot write, so
# TextDB regeneration dies at file_lock creation (files.cc:4072-4073 via
# database.cc:382) with "Unable to open lock file ...: Operation not
# permitted". CRAWL_DIR redirects saves/cache/morgue/macro/crash output. In
# builds without DATA_DIR_PATH it can also take part in config/data
# discovery: find_crawlrc() checks <crawl_dir>/init.txt first
# (initfile.cc:2201) and files.cc:433 lists crawl_dir as the first data
# search base. This fresh temp dir is empty, so those lookups fall back to
# crawl_base and to the source init.txt (via datafile_path,
# initfile.cc:2245-2247); data loading is unchanged.
SMOKE_CRAWL_DIR="$(mktemp -d /tmp/crawl_smoke_dir.XXXXXX)" || exit 2

# Temporary init state. INIT_BAK records the backup path when the original
# init.txt is moved aside; INIT_TMP marks the path as test-owned before the
# temporary 'language = zh' write begins. The cleanup trap is registered
# BEFORE any init.txt modification, so if the mv/echo below fails the trap
# still removes the temp CRAWL_DIR and any partial temporary init.txt, while
# restoring a backed-up original instead of deleting it.
INIT_BAK=""
INIT_TMP=""
INIT_BAK_PATH="$SOURCE_DIR/.init.txt.smoke-bak"
TIMEOUT_PID=""

cleanup() {
    local rc="$1"

    # Disable all handlers before cleanup so it is safe to call from a signal
    # handler and from EXIT without recursion.
    trap - EXIT INT TERM HUP

    if [ -n "$INIT_TMP" ]; then
        rm -f "$SOURCE_DIR/init.txt" || true
    fi
    if [ -n "$INIT_BAK" ] && [ -f "$INIT_BAK" ] && [ ! -L "$INIT_BAK" ]; then
        mv "$INIT_BAK" "$SOURCE_DIR/init.txt" || true
    fi
    rm -rf "$SMOKE_CRAWL_DIR" || true
    rm -f "$ZH_OUT" || true
    stty sane 2>/dev/null || true

    return "$rc"
}

handle_signal() {
    local signal="$1"
    local rc=1
    local waited=0

    # Do not let a second signal interrupt the bounded child reaping below.
    trap - INT TERM HUP
    case "$signal" in
        INT)  rc=130 ;;
        TERM) rc=143 ;;
        HUP)  rc=129 ;;
    esac

    if [ -n "$TIMEOUT_PID" ]; then
        kill -"$signal" "$TIMEOUT_PID" 2>/dev/null || true
        while kill -0 "$TIMEOUT_PID" 2>/dev/null && [ "$waited" -lt 20 ]; do
            sleep 0.05
            waited=$((waited + 1))
        done
        if kill -0 "$TIMEOUT_PID" 2>/dev/null; then
            kill -KILL "$TIMEOUT_PID" 2>/dev/null || true
        fi
        wait "$TIMEOUT_PID" 2>/dev/null || true
        TIMEOUT_PID=""
    fi
    cleanup "$rc"
    exit "$rc"
}

trap 'cleanup "$?"' EXIT
trap 'handle_signal INT' INT
trap 'handle_signal TERM' TERM
trap 'handle_signal HUP' HUP

# Fail closed if a previous interrupted run left any backup artifact. In
# particular, -L catches a dangling symlink that -e would miss. This check is
# intentionally unconditional, even when init.txt itself is absent.
if [ -e "$INIT_BAK_PATH" ] || [ -L "$INIT_BAK_PATH" ]; then
    echo "Refusing to overwrite existing init backup at $INIT_BAK_PATH" >&2
    exit 2
fi

# Only a missing path or an ordinary, non-symlink file is safe to replace.
# Never follow a symlink or redirect shell output into a directory/special
# file supplied at the repository-owned init path.
if [ -L "$SOURCE_DIR/init.txt" ]; then
    echo "Refusing to modify symlink at $SOURCE_DIR/init.txt" >&2
    exit 2
fi
if [ -e "$SOURCE_DIR/init.txt" ] && [ ! -f "$SOURCE_DIR/init.txt" ]; then
    echo "Refusing to modify non-regular file at $SOURCE_DIR/init.txt" >&2
    exit 2
fi

if [ -e "$SOURCE_DIR/init.txt" ]; then
    INIT_BAK="$INIT_BAK_PATH"
    mv "$SOURCE_DIR/init.txt" "$INIT_BAK" || exit 2
fi

INIT_TMP="$SOURCE_DIR/init.txt"
echo 'language = zh' > "$SOURCE_DIR/init.txt"

# Run crawl inside a PTY via run_with_timeout.py --pty-transcript.
# A bare non-PTY launch cannot satisfy ncurses (initscr()/tcgetattr(0))
# and exits 1 in non-interactive sessions (see libunix.cc:838-865).
# The PTY transcript captures stdout+stderr+terminal output into $ZH_OUT;
# the three scans below still read that file. TERM/LANG/LC_ALL mirror the
# proven PTY bot path in post_zh_runtime.sh:256. We don't try to drive
# in-game UI (ncurses reads /dev/tty). The test catches: startup crashes,
# Lua init errors, protocol strings in printf/fprintf-based messages.
# Child exit preserved: 0 normal, 124 timeout (output still scanned).
CHILD_RC=0
LC_ALL=C.UTF-8 LANG=C.UTF-8 TERM=xterm CRAWL_DIR="$SMOKE_CRAWL_DIR" \
    python3 "$TIMEOUT_RUNNER" --timeout "$TIMEOUT_SEC" \
    --pty-transcript "$ZH_OUT" -- \
    "$CRAWL" &
TIMEOUT_PID=$!
if wait "$TIMEOUT_PID"; then
    CHILD_RC=0
else
    CHILD_RC=$?
fi
TIMEOUT_PID=""

# Acceptable: 0 (normal exit) or 124 (timeout). Any other rc/signal → exit 1.
if [ "$CHILD_RC" -ne 0 ] && [ "$CHILD_RC" -ne 124 ]; then
    echo "Crawl exited with unexpected code $CHILD_RC — possible crash or error" >&2
    exit 1
fi

ERRORS=0

echo "=== Crawl Smoke Test (ZH mode, startup output only) ==="
echo ""

# ── Check 1: Protocol leaks ──────────────────────────────────────────
# Lua identifiers and .des tags that must never appear in ZH output.
echo "--- Protocol leaks ---"
PROTOCOL_PATTERNS=(
    '\.des([^[:alnum:]_]|$)'
    'you\.race([^[:alnum:]_]|$)'
    'you\.god([^[:alnum:]_]|$)'
)
PROTOCOL_COUNT=0
for pat in "${PROTOCOL_PATTERNS[@]}"; do
    if grep -qEn "$pat" "$ZH_OUT" 2>/dev/null; then
        echo "  PROTOCOL: $pat"
        grep -nE "$pat" "$ZH_OUT" | head -5 | sed 's/^/     /'
        PROTOCOL_COUNT=$((PROTOCOL_COUNT + 1))
        ERRORS=$((ERRORS + 1))
    fi
done
if [ "$PROTOCOL_COUNT" -eq 0 ]; then
    echo "  No protocol leaks"
fi

# ── Check 2: English residue ─────────────────────────────────────────
# Core UI labels that should be translated in ZH mode.
# Word-boundary matching (no ^ anchor) — output may contain CSI escapes.
echo "--- English residue ---"
EN_UI=(
    'Hit Points([^[:alnum:]_]|$)'
    'Magic Points([^[:alnum:]_]|$)'
    'Strength([^[:alnum:]_]|$)'
    'Intelligence([^[:alnum:]_]|$)'
    'Dexterity([^[:alnum:]_]|$)'
    'Armour Class([^[:alnum:]_]|$)'
    'Evasion([^[:alnum:]_]|$)'
    'Shield([^[:alnum:]_]|$)'
)
RESIDUE_COUNT=0
for pat in "${EN_UI[@]}"; do
    if grep -qEn "$pat" "$ZH_OUT" 2>/dev/null; then
        echo "  RESIDUE: $pat"
        RESIDUE_COUNT=$((RESIDUE_COUNT + 1))
        ERRORS=$((ERRORS + 1))
    fi
done
if [ "$RESIDUE_COUNT" -eq 0 ]; then
    echo "  No English residue in core UI"
fi

# ── Check 3: Crashes ──────────────────────────────────────────────────
echo "--- Crashes ---"
if grep -qiE '(Segmentation fault|Aborted|assertion failed|core dumped|SIGSEGV|SIGABRT)' "$ZH_OUT" 2>/dev/null; then
    echo "  CRASH detected"
    grep -niE '(Segmentation fault|Aborted|assertion failed)' "$ZH_OUT" | head -10 | sed 's/^/     /'
    ERRORS=$((ERRORS + 1))
else
    echo "  No crashes"
fi

# ── Cleanup ───────────────────────────────────────────────────────────
# trap handles init.txt restore and temp file removal

echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "Smoke test passed"
else
    echo "Smoke test: $ERRORS error category(ies)"
    exit 1
fi
exit 0
