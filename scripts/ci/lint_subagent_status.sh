#!/usr/bin/env bash
#
# Ban raw status writes on the ``subagents`` entity and ban the retired
# ``/v1/state_transitions/subagent`` write endpoint. All transition writes
# must go via ``EntangledServiceClient.transition_subagent``.
#
# Why
# ---
# ``subagents.status`` is the authoritative state column for the subagent
# state machine (see novaic-business/business/internal/subagent_state.py).
# A direct ``store.update("subagents", ..., {"status": ...})`` (or the
# runtime equivalent, ``business_client.entity_update("subagents", ...,
# {"status": ...})`` without ``_transition_reason``) bypasses transition() —
# meaning:
#   * the ALLOWED matrix isn't enforced (completed → awake regressions slip
#     through silently),
#   * ancillary fields (need_rest, progress, error, result) drift from
#     status,
#   * the ``subagent_state_transitions`` history row is never written, so
#     downstream observability (trace replay, metric queries) has holes.
#
# The final path folds "update subagents.status + insert history row" into
# a single server-side endpoint ``POST /v1/subagents/{agent}/{sid}/transition``
# wrapped by ``EntangledServiceClient.transition_subagent``. The retired
# ``POST /v1/state_transitions/subagent`` endpoint must not return: it
# splits the status UPDATE and the history INSERT into two non-transactional
# calls and skips Entangled's ALLOWED matrix check.
#
# How
# ---
# The only legitimate writers are:
#   1. novaic-business/business/internal/subagent_state.py   (the module itself)
#   2. novaic-business/business/internal/entity.py           (generic PATCH
#                                                             proxy that routes
#                                                             status through
#                                                             transition())
#   3. tests/                                                 (every repo)
#   4. docs/                                                  (example code in
#                                                             markdown)
#   5. novaic-business/business/schema_push.py               (schema DDL — the
#                                                             DEFAULT 'sleeping'
#                                                             column decl is
#                                                             not a write)
# Anything else hitting the pattern needs justification and an allowlist
# entry here. If you just need to flip status, call
# ``business.internal.subagent_state.transition(...)`` (or one of the
# ``mark_*`` helpers) from Business-side code, or attach
# ``_transition_reason`` / ``_transition_actor`` to your entity_update
# payload from a worker.
#
# For the retired endpoint ban, only tests/docs and this guard may mention
# the write path.
set -e

violations=0

# ── Pass 1: direct writes to subagents.status ──────────────────────────────
#
# Catches both direct store.update calls and the runtime-side
# entity_update helper.
STATUS_PATTERNS=(
    'store\.update\([^)]*subagents[^)]*status'
    'entity_update\([^)]*subagents[^)]*status'
    '\.update\([^)]*"subagents"[^)]*"status"'
)

STATUS_ALLOWLIST=(
    'novaic-business/business/internal/subagent_state.py'
    'novaic-business/business/internal/entity.py'
    'novaic-business/business/schema_push.py'
    # Runtime's single canonical write path. It attaches
    # ``_transition_reason`` + ``_transition_actor`` to every payload; the
    # Business-side entity.py PATCH handler then routes them through
    # subagent_state.transition(). If you add another entity_update site,
    # do it via a helper in subagent_handlers.py instead of bypassing here.
    'novaic-agent-runtime/task_queue/handlers/subagent_handlers.py'
    'tests/'
    'docs/'
    'scripts/ci/lint_subagent_status.sh'
)

for PATTERN in "${STATUS_PATTERNS[@]}"; do
    HITS=$(rg -l --pcre2 -U "$PATTERN" \
              --glob '*.py' \
              novaic-* 2>/dev/null || true)
    for f in $HITS; do
        ok=0
        for a in "${STATUS_ALLOWLIST[@]}"; do
            [[ "$f" == *"$a"* ]] && ok=1
        done
        if [[ $ok -eq 0 ]]; then
            echo "BAN: $f writes subagents.status outside subagent_state.transition()"
            echo "     pattern matched: $PATTERN"
            violations=$((violations + 1))
        fi
    done
done

# ── Pass 2: retired ``/v1/state_transitions/subagent`` write endpoint ─────
#
# Two ways to hit the retired endpoint, both banned:
#   a. call the client helper: ``client.record_subagent_transition(...)``
#   b. raw POST with the literal path: anything matching the quoted string
#      ``"/v1/state_transitions/subagent"`` (exact match terminated by
#      a quote — the GET history endpoint is
#      ``f"/v1/state_transitions/subagent/{subagent_id}"`` where the
#      closing character is a slash, not a quote, so it does NOT match).
#
# The allowed replacement is ``EntangledServiceClient.transition_subagent``
# (PR-31b); it's atomic and goes through Entangled's ALLOWED matrix.
SHIM_PATTERNS=(
    '\.record_subagent_transition\s*\('
    '["'\'']/v1/state_transitions/subagent["'\'']'
)

SHIM_ALLOWLIST=(
    'tests/'
    'docs/'
    'scripts/ci/lint_subagent_status.sh'
)

for PATTERN in "${SHIM_PATTERNS[@]}"; do
    HITS=$(rg -l --pcre2 -U "$PATTERN" \
              --glob '*.py' \
              novaic-* Entangled/ 2>/dev/null || true)
    for f in $HITS; do
        ok=0
        for a in "${SHIM_ALLOWLIST[@]}"; do
            [[ "$f" == *"$a"* ]] && ok=1
        done
        if [[ $ok -eq 0 ]]; then
            echo "BAN: $f uses the retired subagent transition write endpoint"
            echo "     (POST /v1/state_transitions/subagent splits status + history"
            echo "      into two non-transactional writes — exactly what PR-31b closed)"
            echo "     pattern matched: $PATTERN"
            echo "     fix: EntangledServiceClient.transition_subagent(...)"
            violations=$((violations + 1))
        fi
    done
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "Context:"
    echo "  * business.internal.subagent_state.transition()"
    echo "    as the only write path to subagents.status. See"
    echo "    novaic-business/business/internal/subagent_state.py for the"
    echo "    ALLOWED matrix and the mark_* convenience helpers, or"
    echo "    docs/roadmap/tickets/PR-28-subagent-state-machine.md for the RFC."
    echo "  * EntangledServiceClient.transition_subagent"
    echo "    (novaic-common/common/entangled_client.py) for any transition write;"
    echo "    replaces the retired /v1/state_transitions/subagent write endpoint,"
    echo "    which split the atomic write. See"
    echo "    docs/roadmap/tickets/PR-31-state-transition-log-tables.md."
    exit 1
fi
echo "subagent_status lint OK (status writes + retired endpoint)"
