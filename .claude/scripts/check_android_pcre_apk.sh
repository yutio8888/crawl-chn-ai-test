#!/usr/bin/env bash
# Validate the packaged Android native libraries and PCRE linkage contract.

set -euo pipefail

APK=""
LLVM_READELF=""
EXPECTED_ABIS=(arm64-v8a armeabi-v7a x86 x86_64)

usage()
{
    cat <<'EOF'
Usage: check_android_pcre_apk.sh --apk PATH --llvm-readelf PATH

Checks the final APK's exact ABI set, required native libraries, and libmain.so
dynamic PCRE dependencies and undefined-symbol contract.
EOF
}

die()
{
    echo "ERROR: $*" >&2
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --apk)
            [[ $# -ge 2 ]] || die "--apk requires a path"
            APK="$2"
            shift 2
            ;;
        --llvm-readelf)
            [[ $# -ge 2 ]] || die "--llvm-readelf requires a path"
            LLVM_READELF="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            die "unknown option: $1"
            ;;
    esac
done

[[ -n "$APK" && -f "$APK" ]] || die "APK not found: ${APK:-<missing --apk>}"
[[ -n "$LLVM_READELF" && -x "$LLVM_READELF" ]] \
    || die "llvm-readelf is not executable: ${LLVM_READELF:-<missing --llvm-readelf>}"
command -v unzip >/dev/null 2>&1 || die "unzip is required"

TMP_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TMP_ROOT"' EXIT
ENTRY_LIST="$TMP_ROOT/entries.txt"
unzip -Z1 "$APK" > "$ENTRY_LIST" || die "failed to enumerate APK zip entries"
[[ -s "$ENTRY_LIST" ]] || die "APK zip entry list is empty"

DUPLICATES="$(LC_ALL=C sort "$ENTRY_LIST" | uniq -d)"
[[ -z "$DUPLICATES" ]] \
    || die "APK contains duplicate zip entries: $(tr '\n' ' ' <<<"$DUPLICATES")"

ACTUAL_ABIS="$(
    awk -F/ '$1 == "lib" && NF >= 3 { print $2 }' "$ENTRY_LIST" \
        | LC_ALL=C sort -u | paste -sd ' ' -
)"
[[ "$ACTUAL_ABIS" == "${EXPECTED_ABIS[*]}" ]] \
    || die "APK ABI set mismatch: expected '${EXPECTED_ABIS[*]}', got '$ACTUAL_ABIS'"

for abi in "${EXPECTED_ABIS[@]}"; do
    for library in libmain.so libpcre.so; do
        entry="lib/$abi/$library"
        count="$(grep -Fxc -- "$entry" "$ENTRY_LIST" || true)"
        [[ "$count" -eq 1 ]] \
            || die "$entry must occur exactly once in the APK (found $count)"
    done

    main_so="$TMP_ROOT/$abi-libmain.so"
    dynamic="$TMP_ROOT/$abi-dynamic.txt"
    symbols="$TMP_ROOT/$abi-symbols.txt"
    unzip -p "$APK" "lib/$abi/libmain.so" > "$main_so" \
        || die "failed to extract lib/$abi/libmain.so"
    [[ -s "$main_so" ]] || die "lib/$abi/libmain.so is empty"
    "$LLVM_READELF" --dynamic "$main_so" > "$dynamic" \
        || die "llvm-readelf --dynamic failed for $abi/libmain.so"
    "$LLVM_READELF" --dyn-syms "$main_so" > "$symbols" \
        || die "llvm-readelf --dyn-syms failed for $abi/libmain.so"

    grep -Eq '\(NEEDED\).*Shared library: \[libpcre\.so\]' "$dynamic" \
        || die "$abi/libmain.so does not DT_NEEDED libpcre.so"

    for symbol in pcre_compile pcre_exec pcre_free; do
        grep -Eq "[[:space:]]UND[[:space:]]+${symbol}(@|[[:space:]]|$)" "$symbols" \
            || die "$abi/libmain.so is missing undefined $symbol"
    done
    for symbol in regcomp regexec regfree; do
        if grep -Eq "[[:space:]]UND[[:space:]]+${symbol}(@|[[:space:]]|$)" "$symbols"; then
            die "$abi/libmain.so unexpectedly references POSIX $symbol"
        fi
    done
done

echo "Android APK PCRE contract passed: $APK"
echo "ABIs: ${EXPECTED_ABIS[*]}"
