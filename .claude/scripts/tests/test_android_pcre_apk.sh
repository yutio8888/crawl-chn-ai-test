#!/usr/bin/env bash
# Black-box mutation tests for check_android_pcre_apk.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VALIDATOR="$REPO_ROOT/.claude/scripts/check_android_pcre_apk.sh"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf -- "$TMP_ROOT"' EXIT

command -v zip >/dev/null 2>&1 || {
    echo "zip is required for Android APK validator tests" >&2
    exit 1
}

FAKE_READELF="$TMP_ROOT/llvm-readelf"
cp /dev/stdin "$FAKE_READELF" <<'READELF'
#!/usr/bin/env bash
set -euo pipefail

: "${FAKE_READELF_SCENARIO:=success}"
mode="${1:-}"
[[ -n "${2:-}" && -f "$2" ]] || exit 40
if [[ "$FAKE_READELF_SCENARIO" == "readelf-failure" ]]; then
    echo "simulated llvm-readelf failure" >&2
    exit 41
fi

if [[ "$mode" == "--dynamic" ]]; then
    echo ' 0x0000000000000001 (NEEDED) Shared library: [libc++_shared.so]'
    if [[ "$FAKE_READELF_SCENARIO" != "missing-needed" ]]; then
        echo ' 0x0000000000000001 (NEEDED) Shared library: [libpcre.so]'
    fi
elif [[ "$mode" == "--dyn-syms" ]]; then
    symbols=(pcre_compile pcre_exec pcre_free)
    for symbol in "${symbols[@]}"; do
        if [[ "$FAKE_READELF_SCENARIO" != "missing-$symbol" ]]; then
            echo "    1: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND $symbol"
        fi
    done
    case "$FAKE_READELF_SCENARIO" in
        posix-regcomp|posix-regexec|posix-regfree)
            echo "    2: 0000000000000000     0 FUNC    GLOBAL DEFAULT  UND ${FAKE_READELF_SCENARIO#posix-}"
            ;;
    esac
else
    echo "unexpected llvm-readelf mode: $mode" >&2
    exit 42
fi
READELF
chmod +x "$FAKE_READELF"

make_apk()
{
    local apk="$1" mutation="$2"
    local root="$TMP_ROOT/apk-root-${apk##*/}"
    local abi
    rm -rf -- "$root"
    mkdir -p "$root"
    for abi in armeabi-v7a arm64-v8a x86 x86_64; do
        mkdir -p "$root/lib/$abi"
        printf 'ELF-main-%s\n' "$abi" > "$root/lib/$abi/libmain.so"
        printf 'ELF-pcre-%s\n' "$abi" > "$root/lib/$abi/libpcre.so"
    done

    case "$mutation" in
        success|duplicate-entry) : ;;
        missing-abi) rm -rf -- "$root/lib/x86_64" ;;
        extra-abi)
            mkdir -p "$root/lib/riscv64"
            printf 'ELF-main-riscv64\n' > "$root/lib/riscv64/libmain.so"
            printf 'ELF-pcre-riscv64\n' > "$root/lib/riscv64/libpcre.so"
            ;;
        missing-libmain) rm -- "$root/lib/x86/libmain.so" ;;
        missing-libpcre) rm -- "$root/lib/x86/libpcre.so" ;;
        *) echo "unknown APK mutation: $mutation" >&2; exit 2 ;;
    esac

    (cd "$root" && zip -q -r "$apk" lib)
    if [[ "$mutation" == "duplicate-entry" ]]; then
        python3 - "$apk" "$root/lib/x86_64/libmain.so" <<'PY'
import sys
import warnings
import zipfile

warnings.filterwarnings("ignore", message="Duplicate name:.*")
with zipfile.ZipFile(sys.argv[1], "a") as archive:
    archive.write(sys.argv[2], "lib/x86_64/libmain.so")
PY
    fi
}

PASS=0
FAIL=0

run_case()
{
    local label="$1" apk_mutation="$2" readelf_scenario="$3"
    local expected="$4" pattern="$5"
    local apk="$TMP_ROOT/$label.apk"
    local output="$TMP_ROOT/$label.out"
    local rc

    make_apk "$apk" "$apk_mutation"
    set +e
    (cd "$TMP_ROOT" && \
        FAKE_READELF_SCENARIO="$readelf_scenario" \
        bash "$VALIDATOR" --apk "$apk" --llvm-readelf "$FAKE_READELF") \
        > "$output" 2>&1
    rc=$?
    set -e

    if { [[ "$expected" == pass && $rc -eq 0 ]] \
         || [[ "$expected" == fail && $rc -ne 0 ]]; } \
        && grep -Eq "$pattern" "$output"; then
        PASS=$((PASS + 1))
        echo "PASS: $label"
    else
        FAIL=$((FAIL + 1))
        echo "FAIL: $label (exit $rc)" >&2
        cat "$output" >&2
    fi
}

run_case success success success pass 'PCRE contract passed'
run_case missing-abi missing-abi success fail 'ABI set mismatch'
run_case extra-abi extra-abi success fail 'ABI set mismatch'
run_case missing-libmain missing-libmain success fail 'lib/x86/libmain.so must occur exactly once'
run_case missing-libpcre missing-libpcre success fail 'lib/x86/libpcre.so must occur exactly once'
run_case duplicate-entry duplicate-entry success fail 'duplicate zip entries'
run_case missing-needed success missing-needed fail 'does not DT_NEEDED libpcre.so'

for symbol in pcre_compile pcre_exec pcre_free; do
    run_case "missing-$symbol" success "missing-$symbol" fail \
        "missing undefined $symbol"
done
for symbol in regcomp regexec regfree; do
    run_case "posix-$symbol" success "posix-$symbol" fail \
        "unexpectedly references POSIX $symbol"
done
run_case readelf-failure success readelf-failure fail \
    'llvm-readelf --dynamic failed'

INVALID_APK="$TMP_ROOT/invalid.apk"
printf 'not a zip\n' > "$INVALID_APK"
set +e
FAKE_READELF_SCENARIO=success \
    bash "$VALIDATOR" --apk "$INVALID_APK" --llvm-readelf "$FAKE_READELF" \
    > "$TMP_ROOT/invalid-zip.out" 2>&1
invalid_rc=$?
set -e
if [[ $invalid_rc -ne 0 ]] \
    && grep -Fq 'failed to enumerate APK zip entries' "$TMP_ROOT/invalid-zip.out"; then
    PASS=$((PASS + 1))
    echo "PASS: invalid-zip"
else
    FAIL=$((FAIL + 1))
    echo "FAIL: invalid-zip (exit $invalid_rc)" >&2
    cat "$TMP_ROOT/invalid-zip.out" >&2
fi

echo "Android PCRE APK validator tests: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]]
