#!/usr/bin/env bash
#
# PR-55 REWRITE (2026-04-23) — Wake Continuity Contract (R9 state
# layer only) + R-ZOMBIE re-introduction guard.
#
# History: this lint originally (PR-45.2 / P6-13) enforced that any
# file touching the R9 *text* layer referenced BOTH ``handoff_notes``
# and ``historical_summary`` so a partial-forwarding regression
# couldn't half-break wake continuity. PR-55 retired the text layer:
# ``subagent_rest`` was never in ``BUILTIN_TOOL_SCHEMAS``,
# ``generate_simple_summary`` silently returned empty, and both
# columns were NULL for the field's entire production lifetime. See
# ``docs/roadmap/tickets/PR-55-phantom-summary-pipeline-cleanup.md``.
#
# This rewrite flips the contract: the text-layer keys are now
# *retired*, and this script's job is to keep them retired. Any
# reference outside the retirement-trail allowlist (tolerant-
# migration shims in source, tests that assert the retired shape,
# this file) trips R-ZOMBIE. Documentation is excluded entirely —
# ticket docs and postscripts legitimately name the retired keys.
#
# If a future design brings back an LLM-authored resume-note column:
#
#   1. Register the driving tool in ``novaic-cortex/.../tool_schemas.py::BUILTIN_TOOL_SCHEMAS``.
#   2. Use a new column name (not re-using the retired pair).
#   3. Update this lint with the new column + ticket reference.
#
# The R9 state layer (``<PREV_SCOPE_TAIL>`` via ``last_scope_id`` +
# ``previous_scope_id`` metadata rename) is not paired — a single key
# flows end-to-end — so no pairing check applies to it.
#
set -u

# Source trees to check (binary code, not docs).
SCAN_PATHS=(
    "novaic-agent-runtime"
    "novaic-business"
    "novaic-cortex"
    "novaic-common"
    "novaic-device"
    "Entangled/packages/server-python/entangled"
)

# Files allowed to mention the retired keys from within SCAN_PATHS.
# Each is either a tolerant-migration shim with retirement comments
# only, or a test that asserts the retired-key-is-dropped shape.
read -r -d '' ALLOWLIST <<'EOF' || true
novaic-business/business/schema_push.py
novaic-business/business/internal/subagent.py
novaic-business/business/internal/subagent_utils.py
novaic-business/business/internal/helpers.py
novaic-business/business/subscribers/dispatch_subscriber.py
Entangled/packages/server-python/entangled/sql/subagent_state.py
novaic-agent-runtime/task_queue/client.py
novaic-agent-runtime/task_queue/sagas/subagent_rest.py
novaic-agent-runtime/task_queue/sagas/subagent_wake.py
novaic-agent-runtime/task_queue/workers/scheduler_worker.py
novaic-agent-runtime/task_queue/workers/health_worker.py
novaic-agent-runtime/task_queue/handlers/runtime_handlers.py
novaic-agent-runtime/task_queue/handlers/subagent_handlers.py
novaic-agent-runtime/task_queue/handlers/tool_handlers.py
novaic-common/common/tools/definitions.py
EOF

violations=0
raw=""
for path in "${SCAN_PATHS[@]}"; do
    [[ -d "$path" ]] || continue
    out=$(rg -n --no-heading -w \
        -e 'handoff_notes' -e 'historical_summary' \
        --glob '!**/tests/**' \
        --glob '!**/test_*.py' \
        "$path" 2>/dev/null || true)
    [[ -n "$out" ]] && raw+="$out"$'\n'
done

filtered=""
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    file="${line%%:*}"
    skip=0
    while IFS= read -r allow; do
        [[ -z "$allow" ]] && continue
        if [[ "$file" == "$allow" || "$file" == *"/$allow" ]]; then
            skip=1
            break
        fi
    done <<< "$ALLOWLIST"
    [[ $skip -eq 1 ]] && continue
    filtered+="$line"$'\n'
    violations=$((violations + 1))
done <<< "$raw"

if [[ $violations -gt 0 ]]; then
    echo "BAN: retired R9 text-layer key(s) re-introduced outside the"
    echo "     retirement-trail allowlist (see PR-55):"
    echo ""
    echo "$filtered" | sed 's/^/  /'
    echo ""
    echo "R-ZOMBIE (docs/architecture/message-wake-principles.md §二):"
    echo "the keys handoff_notes / historical_summary are retired."
    echo "PR-55 deleted their producer/consumer pipeline. If re-"
    echo "introducing a wake-continuity text column, use a NEW name"
    echo "(not handoff_notes / historical_summary) and register the"
    echo "driving LLM tool in tool_schemas.py::BUILTIN_TOOL_SCHEMAS."
    exit 1
fi

echo "wake_continuity_contract lint OK (retirement-trail guard)"
