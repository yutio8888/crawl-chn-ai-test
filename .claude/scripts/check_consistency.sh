#!/bin/bash
# check_consistency.sh — Cross-file translation consistency checker
#
# Six modes:
#   --rulings   : Check decisions.md rejected names don't persist (default)
#   --gods      : Verify all 28 god names are translated in ZH paths
#   --skills    : Verify all 14 skill school names are translated in ZH paths
#   --format    : Check %%%% separator count parity between EN and ZH database files
#   --spells    : Verify spell key consistency (duplicates, orphans, missing)
#   --database  : Verify @keyword@ reference integrity in database/zh/
#
# Usage:
#   cd ~/projects/crawl && bash .claude/scripts/check_consistency.sh
#   cd ~/projects/crawl && bash .claude/scripts/check_consistency.sh --rulings
#   cd ~/projects/crawl && bash .claude/scripts/check_consistency.sh --gods
#   cd ~/projects/crawl && bash .claude/scripts/check_consistency.sh --skills
#   cd ~/projects/crawl && bash .claude/scripts/check_consistency.sh --format
#   cd ~/projects/crawl && bash .claude/scripts/check_consistency.sh --database
#
# Suitable as a pre-commit hook or CI check.
# Add a new check_entity line for each new decisions.md ruling.

set -euo pipefail

SOURCEDIR="crawl-ref/source"
GREP_SCOPE=(--include='*.cc' --include='*.h' --include='*.txt')
EXCLUDE_PATTERN='worktrees|contrib/'

# Global flag: set to true when any violation is detected.
# In --strict mode, the script exits 1 if this is true at the end.
# Without --strict, the script always exits 0 (backward compatible).
violations_found=false

# ============================================================
# Mode 1: Ruling consistency — rejected names must not persist
# ============================================================

check_entity() {
    local label="$1" correct="$2"; shift 2
    echo "--- $label (correct: $correct) ---"
    for wrong in "$@"; do
        local found
        found=$(grep -rn "$wrong" "$SOURCEDIR" "${GREP_SCOPE[@]}" 2>/dev/null | grep -vE "$EXCLUDE_PATTERN" || true)
        if [ -n "$found" ]; then
            echo "  ❌ Found rejected name '$wrong':"
            echo "$found" | while IFS= read -r line; do
                echo "     $line"
            done
            violations_found=true
        else
            echo "  ✅ '$wrong' not found"
        fi
    done
}

check_english_residual() {
    # Check if English name still appears in ZH translation text (not keys/identifiers).
    # Only searches zh/ directories and flags lines that contain both the English name
    # AND CJK characters — i.e. Chinese translation text with residual English.
    # Lines without CJK chars are English DB keys/identifiers (Type IV protocol) — correct.
    local label="$1" en_name="$2" zh_name="$3"
    echo "--- $label (expected: $zh_name) ---"
    local found=""

    # Only search ZH translation directories, not source code or non-ZH languages
    local zh_dirs=(
        "$SOURCEDIR/dat/i18n/zh"
        "$SOURCEDIR/dat/descript/zh"
        "$SOURCEDIR/dat/database/zh"
    )

    for dir in "${zh_dirs[@]}"; do
        if [ ! -d "$dir" ]; then continue; fi
        local dir_found
        dir_found=$(grep -rn "$en_name" "$dir" --include='*.txt' 2>/dev/null || true)
        if [ -n "$dir_found" ]; then
            # Only flag lines that contain CJK characters (actual Chinese display text).
            # English-only lines are DB lookup keys, Lua identifiers, or translation
            # source keys — these MUST remain in English (Type IV/V protocol).
            local filtered
            filtered=$(echo "$dir_found" | grep -P '[\x{2E80}-\x{9FFF}\x{3400}-\x{4DBF}\x{F900}-\x{FAFF}]' || true)
            if [ -n "$filtered" ]; then
                found="${found}${found:+
}${filtered}"
            fi
        fi
    done

    if [ -n "$found" ]; then
        echo "  ⚠️  English name '$en_name' found in ZH translation text:"
        echo "$found" | while IFS= read -r line; do
            echo "     $line"
        done
        violations_found=true
    else
        echo "  ✅ '$en_name' fully translated to '$zh_name'"
    fi
}

do_rulings() {
    echo "=== Mode 1: Ruling consistency check ==="
    echo ""

    # D-A-001: Sif Muna
    check_entity "Sif Muna"     "西芙·穆娜"   "席夫·穆纳"

    # D-A-002: Trog
    check_entity "Trog"         "特洛格"       "特洛戈"

    # D-A-003: Kikubaaqudgha
    check_entity "Kikubaaqudgha" "奇库巴库哈" "奇库巴库加"

    # D-B-004: conj_verb must not be called on Chinese strings
    # Check for conj_verb called with Chinese string arguments (pattern: conj_verb("中...))
    echo "--- conj_verb with Chinese strings (should be none) ---"
    local cv_found
    cv_found=$(grep -rn 'conj_verb(' "$SOURCEDIR" "${GREP_SCOPE[@]}" 2>/dev/null | grep -vE "$EXCLUDE_PATTERN" || true)
    # Filter: show only lines where a Chinese string (CJK char) appears near conj_verb
    local cv_zh
    cv_zh=$(echo "$cv_found" | grep -P '[\x{2E80}-\x{9FFF}]' || true)
    if [ -n "$cv_zh" ]; then
        echo "  ❌ conj_verb called with Chinese string:"
        echo "$cv_zh" | while IFS= read -r line; do echo "     $line"; done
        violations_found=true
    else
        echo "  ✅ No conj_verb calls with Chinese strings detected"
    fi
    echo "  ℹ️  All conj_verb calls (verify manually): $(echo "$cv_found" | wc -l) occurrences"
    echo "$cv_found" | while IFS= read -r line; do echo "     $line"; done

    echo ""
    echo "=== Rulings check complete ==="
}

# ============================================================
# Mode 2a: God name full glossary check (28 gods)
# ============================================================

do_gods() {
    echo "=== Mode 2a: God name full consistency ==="
    echo ""

    check_english_residual "Zin"            "Zin"            "辛"
    check_english_residual "The Shining One" "The Shining One" "光辉者"
    check_english_residual "Kikubaaqudgha"  "Kikubaaqudgha"  "奇库巴库哈"
    check_english_residual "Yredelemnul"    "Yredelemnul"    "伊莱德莱姆努尔"
    check_english_residual "Xom"            "Xom"            "佐姆"
    check_english_residual "Vehumet"        "Vehumet"        "维胡梅特"
    check_english_residual "Okawaru"        "Okawaru"        "奥卡瓦鲁"
    check_english_residual "Makhleb"        "Makhleb"        "马科列布"
    check_english_residual "Sif Muna"       "Sif Muna"       "西芙·穆娜"
    check_english_residual "Trog"           "Trog"           "特洛格"
    check_english_residual "Nemelex Xobeh"  "Nemelex Xobeh"  "尼姆雷斯·索布"
    check_english_residual "Elyvilon"       "Elyvilon"       "艾利维隆"
    check_english_residual "Lugonu"         "Lugonu"         "卢格努"
    check_english_residual "Beogh"          "Beogh"          "比欧弗"
    check_english_residual "Jiyva"          "Jiyva"          "吉瓦"
    check_english_residual "Fedhas"         "Fedhas"         "费德哈"
    check_english_residual "Cheibriados"    "Cheibriados"    "切布理亚多"
    check_english_residual "Ashenzari"      "Ashenzari"      "艾申扎利"
    check_english_residual "Dithmenos"      "Dithmenos"      "迪斯姆诺"
    check_english_residual "Gozag"          "Gozag"          "哥萨戈"
    check_english_residual "Qazlal"         "Qazlal"         "卡兹拉尔"
    check_english_residual "Ru"             "Ru"             "入"
    check_english_residual "Pakellas"       "Pakellas"       "帕克拉斯"
    check_english_residual "Uskayaw"        "Uskayaw"        "乌斯卡亚"
    check_english_residual "Hepliaklqana"   "Hepliaklqana"   "惠普利亚卡纳"
    check_english_residual "Ignis"          "Ignis"          "曳焰"
    check_english_residual "Wu Jian"        "Wu Jian"        "无间门派"
    check_english_residual "Zot"            "Zot"            "佐特"

    echo ""
    echo "=== Gods check complete ==="
}

# ============================================================
# Mode 2b: Skill school name full glossary check (14 schools)
# ============================================================

do_skills() {
    echo "=== Mode 2b: Skill school name full consistency ==="
    echo ""

    check_english_residual "Conjurations"   "Conjurations"   "咒法系"
    check_english_residual "Summonings"     "Summonings"     "召唤系"
    check_english_residual "Necromancy"     "Necromancy"     "死灵系"
    check_english_residual "Transmutations" "Transmutations" "变化系"
    check_english_residual "Fire Magic"     "Fire Magic"     "火焰魔法"
    check_english_residual "Ice Magic"      "Ice Magic"      "寒冰魔法"
    check_english_residual "Air Magic"      "Air Magic"      "风魔法"
    check_english_residual "Earth Magic"    "Earth Magic"    "大地魔法"
    check_english_residual "Poison Magic"   "Poison Magic"   "毒素魔法"
    check_english_residual "Hexes"          "Hexes"          "咒术系"
    check_english_residual "Charms"         "Charms"         "附魔系"
    check_english_residual "Summoning"      "Summoning"      "召唤系"
    check_english_residual "Translocation"  "Translocation"  "传送系"
    check_english_residual "Alchemy"        "Alchemy"        "炼金系"

    echo ""
    echo "=== Skills check complete ==="
}

# ============================================================
# Mode 3: Format integrity — %%%% separator count parity
# ============================================================

do_format() {
    echo "=== Mode 3: Format integrity check ==="
    echo ""

    local zh_dir="$SOURCEDIR/dat/database/zh"
    local en_dir="$SOURCEDIR/dat/database"
    local issues=0

    if [ ! -d "$zh_dir" ]; then
        echo "  ❌ ZH database directory not found: $zh_dir"
        return 1
    fi

    for zh_file in "$zh_dir"/*.txt; do
        local basename
        basename=$(basename "$zh_file")
        local en_file="$en_dir/$basename"

        if [ -f "$en_file" ]; then
            local en_count zh_count
            # Count %%%% lines (lines that are exactly %%%%)
            en_count=$(grep -c '^%%%%$' "$en_file" 2>/dev/null || echo 0)
            zh_count=$(grep -c '^%%%%$' "$zh_file" 2>/dev/null || echo 0)

            if [ "$en_count" != "$zh_count" ]; then
                echo "  ❌ $basename: %%%% count mismatch (EN: $en_count, ZH: $zh_count)"
                issues=$((issues + 1))
                violations_found=true
            fi
        fi
    done

    if [ "$issues" -eq 0 ]; then
        echo "  ✅ All ZH database files have matching %%%% counts"
    else
        echo "  ⚠️  $issues file(s) with %%%% mismatch"
    fi

    echo ""
    echo "=== Format check complete ==="
}

# ============================================================
# Mode 4: Spell key consistency
# ============================================================

do_spells() {
    echo "=== Mode 4: Spell key consistency check ==="
    echo ""

    local zh_file="$SOURCEDIR/dat/descript/zh/spells.txt"
    local en_file="$SOURCEDIR/dat/descript/spells.txt"
    local issues=0

    if [ ! -f "$zh_file" ]; then
        echo "  ❌ ZH spells file not found: $zh_file"
        return 1
    fi
    if [ ! -f "$en_file" ]; then
        echo "  ❌ EN spells file not found: $en_file"
        return 1
    fi

    local zh_keys en_keys
    zh_keys=$(grep 'spell$' "$zh_file" | sort)
    en_keys=$(grep 'spell$' "$en_file" | sort)

    # 1. Duplicate keys
    echo "--- Duplicate keys ---"
    local dups
    dups=$(grep 'spell$' "$zh_file" | sort | uniq -d)
    if [ -n "$dups" ]; then
        echo "$dups" | while IFS= read -r dup; do
            echo "  ❌ Duplicate: $dup"
        done
        issues=$((issues + 1))
        violations_found=true
    else
        echo "  ✅ No duplicate keys"
    fi

    # 2. Orphan keys (ZH has, EN doesn't)
    echo "--- Orphan keys (ZH only) ---"
    local orphans
    orphans=$(comm -23 <(echo "$zh_keys") <(echo "$en_keys"))
    if [ -n "$orphans" ]; then
        echo "$orphans" | while IFS= read -r orphan; do
            echo "  ⚠️  $orphan"
        done
        issues=$((issues + 1))
        violations_found=true
    else
        echo "  ✅ No orphan keys"
    fi

    # 3. Missing keys (EN has, ZH doesn't)
    echo "--- Missing keys (EN only) ---"
    local missing
    missing=$(comm -13 <(echo "$zh_keys") <(echo "$en_keys"))
    if [ -n "$missing" ]; then
        echo "$missing" | while IFS= read -r miss; do
            echo "  ⚠️  $miss"
        done
        issues=$((issues + 1))
        violations_found=true
    else
        echo "  ✅ No missing keys"
    fi

    echo ""
    if [ "$issues" -eq 0 ]; then
        echo "  ✅ Spell keys fully consistent with EN"
    else
        echo "  ⚠️  $issues issue(s) found"
    fi
    echo ""
    echo "=== Spells check complete ==="
}

# ============================================================
# Mode 5: Database @keyword@ integrity
# ============================================================

# Keywords provided by C++ runtime — never defined in any .txt file
RUNTIME_KEYWORDS=(
    # God/skills
    "random_god" "random_god_chaotic" "random_god_evil" "random_god_good"
    "random_skill" "random_skill_magic" "random_skill_mundane"
    # Player
    "player_genus" "player_species" "player_death" "player_doom"
    "player_name" "branch_name"
    # Body parts
    "feet" "hands" "hand" "head" "hand_conj"
    # Items
    "your_item" "Your_item" "your_hands" "your_weapon"
    # Monster
    "the_monster" "The_monster" "the_monster_possessive"
    "The_monster_possessive" "possessive" "killer_name"
    "short_monster_name_"
    # Features
    "the_feature" "The_feature" "staircase"
    # RANDGEN
    "RANDGEN"
    # Books
    "_subject_" "_the_subject_" "level" "book_name" "book_noun"
    # Names
    "ancestor name" "any orc name" "bland name"
    # Random body parts
    "random_body_part_any_plural" "random_body_part_any_singular"
    "random_body_part_external_plural" "random_body_part_external_singular"
    "random_body_part_internal_plural" "random_body_part_internal_singular"
    # Misc runtime
    "sparkling_message"
)

is_runtime_keyword() {
    local key="$1"
    for rk in "${RUNTIME_KEYWORDS[@]}"; do
        [ "$key" = "$rk" ] && return 0
    done
    return 1
}

do_database() {
    echo "=== Mode 5: Database @keyword@ integrity check ==="
    echo ""

    local zh_dir="$SOURCEDIR/dat/database/zh"
    local en_dir="$SOURCEDIR/dat/database"
    local issues=0

    if [ ! -d "$zh_dir" ]; then
        echo "  ❌ ZH database directory not found: $zh_dir"
        return 1
    fi

    # Pre-build full EN key index (all keys across all EN database files)
    local en_keys_all
    en_keys_all=$(mktemp)
    for en_file in "$en_dir"/*.txt; do
        [ -f "$en_file" ] || continue
        awk '!/^%%%%$/ && !/^$/ && !/^ / && !/^#/ {
            line=$0
            gsub(/^ +| +$/, "", line)
            if (match(line, /@[^@]+@/)) {
                key=substr(line, 1, RSTART-1)
                gsub(/^ +| +$/, "", key)
                if (key != "") print key
            } else {
                if (line !~ /^w:[0-9]/ && line !~ /^{{/ && line !~ /^if / && line !~ /^else/ && line !~ /^end$/)
                    print line
            }
        }' "$en_file" >> "$en_keys_all"
    done
    local en_keys_sorted
    en_keys_sorted=$(sort -u "$en_keys_all" 2>/dev/null || true)
    rm -f "$en_keys_all"

    for zh_file in "$zh_dir"/*.txt; do
        local basename
        basename=$(basename "$zh_file")
        local en_file="$en_dir/$basename"

        # Extract all @keyword@ references from ZH file (exclude comment lines)
        local zh_refs
        zh_refs=$(grep -v '^#' "$zh_file" | grep -oP '@[a-zA-Z_][a-zA-Z_0-9 ]*@' | \
                  sed 's/^@//;s/@$//' | sort -u || true)

        # Build ZH key index and EN same-file key index
        local zh_keys en_same_keys
        zh_keys=$(awk '!/^%%%%$/ && !/^$/ && !/^ / && !/^#/ {
            line=$0; gsub(/^ +| +$/, "", line)
            if (match(line, /@[^@]+@/)) {
                key=substr(line, 1, RSTART-1); gsub(/^ +| +$/, "", key)
                if (key != "") print key
            } else {
                if (line !~ /^w:[0-9]/ && line !~ /^{{/ && line !~ /^if / && line !~ /^else/ && line !~ /^end$/)
                    print line
            }
        }' "$zh_file" | sort -u || true)

        if [ -f "$en_file" ]; then
            en_same_keys=$(awk '!/^%%%%$/ && !/^$/ && !/^ / && !/^#/ {
                line=$0; gsub(/^ +| +$/, "", line)
                if (match(line, /@[^@]+@/)) {
                    key=substr(line, 1, RSTART-1); gsub(/^ +| +$/, "", key)
                    if (key != "") print key
                } else {
                    if (line !~ /^w:[0-9]/ && line !~ /^{{/ && line !~ /^if / && line !~ /^else/ && line !~ /^end$/)
                        print line
                }
            }' "$en_file" | sort -u || true)
        else
            en_same_keys=""
        fi

        local file_issues=0
        for ref in $zh_refs; do
            # Skip runtime keywords
            if is_runtime_keyword "$ref"; then
                continue
            fi

            # Check 1: defined in ZH same file?
            if echo "$zh_keys" | grep -qFx "$ref"; then
                continue
            fi

            # Check 2: defined in EN same file?
            if [ -n "$en_same_keys" ] && echo "$en_same_keys" | grep -qFx "$ref"; then
                continue
            fi

            # Check 3: defined in any EN database file?
            if echo "$en_keys_sorted" | grep -qFx "$ref"; then
                continue
            fi

            # Not found anywhere
            if [ "$file_issues" -eq 0 ]; then
                echo "  ❌ $basename:"
            fi
            echo "     @$ref@ — not defined in ZH, EN same file, or any EN database"
            file_issues=$((file_issues + 1))
            issues=$((issues + 1))
            violations_found=true
        done
    done

    if [ "$issues" -eq 0 ]; then
        echo "  ✅ All @keyword@ references have matching definitions"
    else
        echo ""
        echo "  ⚠️  $issues unresolved @keyword@ reference(s)"
    fi

    echo ""
    echo "=== Database @keyword@ check complete ==="
}

# ============================================================
# Main — parse mode and --strict flag
# ============================================================

MODE="--rulings"
STRICT_MODE=false

while [ $# -gt 0 ]; do
    case "$1" in
        --strict) STRICT_MODE=true; shift ;;
        --rulings|--gods|--skills|--format|--spells|--database|--all)
            MODE="$1"; shift ;;
        *)
            echo "Usage: $0 [--rulings|--gods|--skills|--format|--spells|--database|--all] [--strict]"
            echo ""
            echo "  --rulings   Check rejected translations from decisions.md (default)"
            echo "  --gods      Verify all 28 god names translated in ZH paths"
            echo "  --skills    Verify all 14 skill school names translated in ZH paths"
            echo "  --format    Check %%%% separator count parity"
            echo "  --spells    Verify spell key consistency (duplicates, orphans, missing)"
            echo "  --database  Verify @keyword@ reference integrity in database/zh/"
            echo "  --all       Run all modes"
            echo "  --strict    Exit with non-zero code when violations are found"
            echo "              (default: always exit 0 for backward compatibility)"
            exit 1
            ;;
    esac
done

case "$MODE" in
    --rulings)
        do_rulings
        ;;
    --gods)
        do_gods
        ;;
    --skills)
        do_skills
        ;;
    --format)
        do_format
        ;;
    --spells)
        do_spells
        ;;
    --database)
        do_database
        ;;
    --all)
        do_rulings
        echo ""
        do_gods
        echo ""
        do_skills
        echo ""
        do_format
        echo ""
        do_spells
        echo ""
        do_database
        ;;
esac

# In strict mode, exit 1 if any violation was detected.
# Without --strict, always exit 0 (backward compatible).
if [ "$STRICT_MODE" = true ] && [ "$violations_found" = true ]; then
    echo ""
    echo "❌ Consistency violations found (strict mode)."
    exit 1
fi
exit 0
