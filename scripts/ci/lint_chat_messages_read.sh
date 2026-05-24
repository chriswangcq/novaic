#!/usr/bin/env bash
#
# ``chat_messages.read`` is a UI-only field.
#
# Runtime / subscriber / assembler / healthworker code must not read or
# write ``chat_messages.read`` as a semantic signal. Authoritative
# "consumed" / "in-flight" signals live in ``lifecycle`` and
# ``scope.meta.input_message_ids``.
#
# Background: ``read`` historically leaked from "UI red-dot" into
# "runtime just-consumed-this-msg" and back again; the 2026-04-17
# "hihi" incident (runtime scanning ``read=0`` to reconstruct inputs
# and replaying 11 old messages per round) was a direct consequence.
# The read path is closed; this lint prevents re-introduction.
#
# The ban covers file globs that belong to the "consumer SSOT" layer:
#   - novaic-agent-runtime/task_queue/**        (runtime)
#   - novaic-business/business/subscribers/**   (DispatchSubscriber)
#   - novaic-business/business/workers/**       (HealthWorker)
#   - novaic-common/common/wake/**              (Assembler)
#
# It deliberately does NOT cover:
#   - novaic-business/business/internal/**  (UI-facing HTTP layer, read
#     is legitimately rendered + flipped there)
#   - Entangled schema/entity_store (row passthrough)
#   - tests/ / docs/
#
# Allowlist entries must be current, explicitly owned exceptions.
set -e

# Patterns match "read" as a semantic dict/kwarg value at values 0 or 1.
PATTERNS=(
    '"read"\s*:\s*"?[01]"?'
    '\bread\s*=\s*"?[01]"?'
)

ALLOWLIST_FILES=(
)

SEARCH_DIRS=(
    'novaic-agent-runtime/task_queue'
    'novaic-business/business/subscribers'
    'novaic-business/business/workers'
    'novaic-common/common/wake'
)

violations=0
for PATTERN in "${PATTERNS[@]}"; do
    for DIR in "${SEARCH_DIRS[@]}"; do
        [[ -d "$DIR" ]] || continue
        HITS=$(rg -l --pcre2 -U "$PATTERN" --glob '*.py' "$DIR" 2>/dev/null || true)
        for f in $HITS; do
            ok=0
            for a in "${ALLOWLIST_FILES[@]}"; do
                [[ "$f" == *"$a"* ]] && ok=1
            done
            if [[ $ok -eq 0 ]]; then
                echo "BAN: $f — chat_messages.read is UI-only (R10)"
                echo "     pattern matched: $PATTERN"
                echo "     if this is a legitimate UI-facing write, move it outside"
                echo "     the consumer SSOT search dirs or add an owned allowlist entry."
                violations=$((violations + 1))
            fi
        done
    done
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "R10 (Consumer SSOT): runtime/subscriber/assembler/healthworker"
    echo "code must not read or write chat_messages.read. Use lifecycle"
    echo "or scope.meta.input_message_ids instead. See"
    echo "docs/architecture/message-wake-principles.md §R10."
    exit 1
fi
echo "chat_messages_read lint OK"
