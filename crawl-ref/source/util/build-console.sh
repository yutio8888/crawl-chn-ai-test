#!/bin/bash
# build-console.sh — Build WSL console binary with ccache
# Usage: bash util/build-console.sh [make-args...]
#
# Uses ccache automatically if available. Run from crawl-ref/source/.

set -euo pipefail

HERE="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$HERE"

echo "=== Building WSL Console ==="
echo "ccache: $(ccache -s 2>&1 | grep 'Cache size')"
make "$@" -j8
echo "=== Done ==="
ccache -s
