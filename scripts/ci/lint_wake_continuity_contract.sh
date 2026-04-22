#!/usr/bin/env bash
#
# PR-45.2 / P6-13 FOLLOW-UP — Wake Continuity Contract (R9 text layer).
#
# R9 (see docs/architecture/message-wake-principles.md §R9) guarantees
# that short-term memory crosses scope sleep/wake via two paired
# fields on the ``subagents`` row:
#
#   * ``handoff_notes``       — LLM-authored resume instructions
#                               (producer: ``subagent_rest`` tool)
#   * ``historical_summary``  — auto-rolled conversation digest
#                               (producer: rest-saga summarizer)
#
# Both flow through the same dispatch path:
#
#   Producer           →  Business (PATCH subagents)
#                     →  DispatchSubscriber._resolve_continuity
#                         (or HealthWorker recovery path)
#                     →  outbox payload.metadata.{handoff_notes, historical_summary}
#                     →  Assembler session.init payload
#                     →  runtime session_init → _build_wake_continuity_messages
#                     →  <HANDOFF_NOTES> / <HISTORICAL_SUMMARY> system msgs
#
# The *contract* this lint enforces: consumer-layer code (subscriber,
# health worker, runtime session-init handler) that names either key
# MUST also name the other in the same file. A regression where a
# maintainer adds e.g. ``for key in ("handoff_notes",):`` on the
# forwarding seam silently drops ``historical_summary`` all the way to
# the LLM and turns R9 into a half-implemented invariant — the class
# of bug that motivated the whole P6 phase.
#
# This lint does NOT enforce pairing on the producer side (where
# single-key writes are intentional: ``_exec_subagent_rest`` writes
# only ``handoff_notes``; the rest-saga summarizer writes only
# ``historical_summary``). Those files are explicitly allowlisted.
#
# Why a text-grep lint instead of a type check: the keys are stringly
# typed across a service boundary (Python → HTTP JSON → runtime
# payload), so static typing cannot see the drop. A grep on the
# watched file set is the narrowest thing that would have caught the
# 2026-04-22 "handoff_notes reached consumer but historical_summary
# did not" class of regression if it had existed at the time.
#
# Allowlist additions require:
#   1. A comment naming the ticket and reason.
#   2. An entry in docs/roadmap/tickets/reviews/PR-45-review.md §五
#      explaining why the file is asymmetric on purpose.
#
# References:
#   - PR-45 review §3.3 ambiguity (resolver silent on outcome)
#   - PR-45.1 observability log (closes the resolve → log gap)
#   - docs/architecture/message-wake-principles.md §R9
#
set -e

KEYS=(handoff_notes historical_summary)

# Consumer-layer files. Any file here that references EITHER key must
# reference BOTH. A new file in these dirs that introduces one key
# without the other is a contract violation.
WATCH_GLOBS=(
    'novaic-business/business/subscribers/*.py'
    'novaic-business/business/workers/*.py'
    'novaic-agent-runtime/task_queue/workers/*.py'
    'novaic-agent-runtime/task_queue/handlers/runtime_handlers.py'
    'novaic-agent-runtime/task_queue/handlers/context_handlers.py'
    'novaic-common/common/wake/*.py'
)

# Files that are legitimately single-key (producer side or
# deprecated/scoped narrowly). Each entry must reference a ticket.
ALLOWLIST_FILES=(
    # _exec_subagent_rest (PR-49) — LLM tool writes ONLY handoff_notes
    # via Business PATCH. historical_summary is written by the
    # rest-saga summarizer path, not by the LLM. Asymmetry intentional.
    'novaic-agent-runtime/task_queue/handlers/tool_handlers.py'
)

violations=0

for glob in "${WATCH_GLOBS[@]}"; do
    for f in $glob; do
        [[ -f "$f" ]] || continue

        # Skip allowlisted files.
        skip=0
        for a in "${ALLOWLIST_FILES[@]}"; do
            [[ "$f" == *"$a"* ]] && skip=1
        done
        [[ $skip -eq 1 ]] && continue

        # Skip test files (they legitimately assert on single-key flows).
        [[ "$f" == *test_* ]] && continue
        [[ "$f" == */tests/* ]] && continue

        has_handoff=$(rg -c '\bhandoff_notes\b' "$f" 2>/dev/null || echo 0)
        has_summary=$(rg -c '\bhistorical_summary\b' "$f" 2>/dev/null || echo 0)

        # Neither key present → file is not in the contract; skip.
        if [[ "$has_handoff" == "0" && "$has_summary" == "0" ]]; then
            continue
        fi

        # Both present → contract honored.
        if [[ "$has_handoff" != "0" && "$has_summary" != "0" ]]; then
            continue
        fi

        # Exactly one → violation.
        echo "BAN: $f — wake-continuity contract broken (R9)"
        if [[ "$has_handoff" == "0" ]]; then
            echo "     references historical_summary but NOT handoff_notes."
        else
            echo "     references handoff_notes but NOT historical_summary."
        fi
        echo "     Both keys must flow together through the consumer path."
        echo "     If asymmetry is intentional, add the file to ALLOWLIST_FILES"
        echo "     in scripts/ci/lint_wake_continuity_contract.sh with a"
        echo "     ticket reference, and update PR-45-review.md §五."
        violations=$((violations + 1))
    done
done

# Additional guard: if ANY consumer-layer file iterates a tuple like
# ``for key in ("handoff_notes",):`` (one key only), flag it. This
# catches the specific regression shape — a loop that was supposed to
# forward BOTH keys but forgot one — even if the file also mentions
# the other key elsewhere in a docstring or comment.
for glob in "${WATCH_GLOBS[@]}"; do
    for f in $glob; do
        [[ -f "$f" ]] || continue
        [[ "$f" == *test_* ]] && continue
        [[ "$f" == */tests/* ]] && continue

        # Allowlist: skip tool_handlers (asymmetric producer).
        skip=0
        for a in "${ALLOWLIST_FILES[@]}"; do
            [[ "$f" == *"$a"* ]] && skip=1
        done
        [[ $skip -eq 1 ]] && continue

        # Match:  for <name> in ("handoff_notes",):     (single-key tuple)
        # Match:  for <name> in ("historical_summary",):
        # Does NOT match the legitimate pair form.
        HITS=$(rg -n --pcre2 \
            'for\s+\w+\s+in\s+\(\s*"(?:handoff_notes|historical_summary)"\s*,?\s*\)\s*:' \
            "$f" 2>/dev/null || true)
        if [[ -n "$HITS" ]]; then
            echo "BAN: $f — single-key continuity loop (R9 drop regression)"
            echo "$HITS" | sed 's/^/     /'
            echo "     Loops over continuity keys MUST include both"
            echo "     handoff_notes and historical_summary together."
            violations=$((violations + 1))
        fi
    done
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "R9 (Wake Continuity): handoff_notes and historical_summary are"
    echo "paired fields in the consumer path. Dropping one silently"
    echo "half-breaks wake continuity with no runtime error. See"
    echo "docs/architecture/message-wake-principles.md §R9 and"
    echo "docs/roadmap/tickets/reviews/PR-45-review.md §五."
    exit 1
fi

echo "wake_continuity_contract lint OK"
