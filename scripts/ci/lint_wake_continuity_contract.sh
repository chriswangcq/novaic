#!/usr/bin/env bash
#
# PR-83 — Cortex minimal continuity guard.
#
# The live continuity model is intentionally small:
#   active scope expanded -> closed scope folded by summary.md
#   summary.md is written from skill_end(report=...)
#
# This lint keeps old implicit-continuity field names out of active source.
# It deliberately avoids spelling the banned names as single literals here,
# so plain repo grep can still be used as a smoke check.

set -u

SCAN_PATHS=(
    "novaic-agent-runtime"
    "novaic-business"
    "novaic-cortex/novaic_cortex"
    "novaic-common"
    "novaic-app/src/data/entities"
)

BAN_PATTERNS=(
    "handoff""_notes"
    "historical""_summary"
)

violations=0
filtered=""

for path in "${SCAN_PATHS[@]}"; do
    [[ -d "$path" ]] || continue
    for pattern in "${BAN_PATTERNS[@]}"; do
        out=$(rg -n --no-heading -w \
            -e "$pattern" \
            --glob '!**/tests/**' \
            --glob '!**/test_*.py' \
            --glob '!**/__pycache__/**' \
            --glob '!**/*.pyc' \
            "$path" 2>/dev/null || true)
        if [[ -n "$out" ]]; then
            filtered+="$out"$'\n'
            while IFS= read -r line; do
                [[ -n "$line" ]] && violations=$((violations + 1))
            done <<< "$out"
        fi
    done
done

if [[ $violations -gt 0 ]]; then
    echo "BAN: retired implicit-continuity fields appeared in active source:"
    echo ""
    echo "$filtered" | sed 's/^/  /'
    echo ""
    echo "Use Cortex folded scope summaries instead: skill_end(report=...) -> summary.md."
    exit 1
fi

echo "wake_continuity_contract lint OK (minimal Cortex continuity)"
