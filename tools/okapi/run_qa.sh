#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OKAPI_HOME="${OKAPI_HOME:-$HOME/opt/okapi}"
BUILD_DIR="$ROOT_DIR/tools/okapi/build"

if [[ ! -d "$OKAPI_HOME/lib" ]]; then
  echo "Okapi installation not found: $OKAPI_HOME" >&2
  exit 2
fi
if [[ $# -lt 2 || $# -gt 4 ]]; then
  echo "Usage: $0 <input.xlf> <report.xml> [glossary.tsv] [blacklist.tsv]" >&2
  exit 2
fi

mkdir -p "$BUILD_DIR"
javac -encoding UTF-8 -cp "$OKAPI_HOME/lib/*" -d "$BUILD_DIR" \
  "$ROOT_DIR/tools/okapi/OkapiQaRunner.java"

input="$1"
report="$2"
glossary="${3:-}"
blacklist="${4:-}"
if [[ -n "$blacklist" ]]; then
  java -Djava.awt.headless=true -cp "$BUILD_DIR:$OKAPI_HOME/lib/*" \
    OkapiQaRunner "$input" "$report" "$blacklist"
else
  java -Djava.awt.headless=true -cp "$BUILD_DIR:$OKAPI_HOME/lib/*" \
    OkapiQaRunner "$input" "$report"
fi

if [[ -n "$glossary" ]]; then
  terms_report="${report%.xml}.terms.json"
  if [[ "$terms_report" == "$report" ]]; then
    terms_report="${report}.terms.json"
  fi
  python3 "$ROOT_DIR/tools/okapi/check_terms.py" \
    "$input" "$glossary" "$terms_report"
fi
