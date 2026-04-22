#!/usr/bin/env bash
#
# P6-12 / R10 — ``chat_messages.read`` is a UI-only field.
#
# Runtime / subscriber / assembler / healthworker code must not read or
# write ``chat_messages.read`` as a semantic signal. Authoritative
# "consumed" / "in-flight" signals live in ``lifecycle`` (PR-21 state
# machine) and ``scope.meta.input_message_ids`` (PR-46 SSOT).
#
# Background: ``read`` historically leaked from "UI red-dot" into
# "runtime just-consumed-this-msg" and back again; the 2026-04-17
# "hihi" incident (runtime scanning ``read=0`` to reconstruct inputs
# and replaying 11 old messages per round) was a direct consequence.
# PR-46 closed the read path; this lint prevents re-introduction.
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
# Allowlist entries are the known P6-12 survivors, each with a sunset
# follow-up tracked in the P6-12 ticket. New entries require a ticket
# reference in the comment directly above the line.
set -e

# Patterns match "read" as a semantic dict/kwarg value at values 0 or 1.
PATTERNS=(
    '"read"\s*:\s*"?[01]"?'
    '\bread\s*=\s*"?[01]"?'
)

# Files allowed to keep legacy read references (documented survivors
# per docs/roadmap/tickets/P6-12-chat-messages-read-ui-only.md).
ALLOWLIST_FILES=(
    # Runtime context_handlers — UI-compat write-through + replay filter
    # (both sunset follow-ups in P6-12); legacy fallback scan is
    # CONTEXT_READ_BY_IDS=0 kill-switched.
    'novaic-agent-runtime/task_queue/handlers/context_handlers.py'
    # chat_reply tool initializes AGENT_REPLY row with read=1 so UI does
    # not flag agent's own outbound messages as unread. Init, not a
    # semantic read. P6-12 FOLLOW-UP-4 tracks removal once UI migrates
    # off the `read` column entirely.
    'novaic-agent-runtime/task_queue/handlers/tool_handlers.py'
    # SESSION_CHECK_NEW_MESSAGES is a dead handler (see deprecation
    # docstring). P6-12 FOLLOW-UP tracks removal.
    'novaic-agent-runtime/task_queue/handlers/runtime_handlers.py'
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
                echo "     if this is a legitimate UI-compat write, add the file to"
                echo "     ALLOWLIST_FILES in scripts/ci/lint_chat_messages_read.sh"
                echo "     with a ticket reference, then update"
                echo "     docs/roadmap/tickets/P6-12-chat-messages-read-ui-only.md §一."
                violations=$((violations + 1))
            fi
        done
    done
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "R10 (Consumer SSOT): runtime/subscriber/assembler/healthworker"
    echo "code must not read or write chat_messages.read. Use lifecycle"
    echo "(message_state.transition, PR-21) or scope.meta.input_message_ids"
    echo "(PR-46) instead. See docs/architecture/message-wake-principles.md"
    echo "§R10 and docs/roadmap/tickets/P6-12-chat-messages-read-ui-only.md."
    exit 1
fi
echo "chat_messages_read lint OK"
