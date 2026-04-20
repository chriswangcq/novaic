#!/usr/bin/env bash
#
# PR-28 (2026-04-15) — ban raw status writes on the ``subagents`` entity.
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
#   * the PR-28 transition log line is never emitted, so PR-31's
#     state-transition log table will have holes,
#   * the transition metric counter is never bumped, so the runbook
#     "dump subagent state churn" loses visibility into stuck subagents.
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
set -e

# Two patterns; we want to catch both direct store.update calls and the
# runtime-side entity_update helper.
PATTERNS=(
    'store\.update\([^)]*subagents[^)]*status'
    'entity_update\([^)]*subagents[^)]*status'
    '\.update\([^)]*"subagents"[^)]*"status"'
)

ALLOWLIST=(
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

violations=0
for PATTERN in "${PATTERNS[@]}"; do
    HITS=$(rg -l --pcre2 -U "$PATTERN" \
              --glob '*.py' \
              novaic-* 2>/dev/null || true)
    for f in $HITS; do
        ok=0
        for a in "${ALLOWLIST[@]}"; do
            [[ "$f" == *"$a"* ]] && ok=1
        done
        if [[ $ok -eq 0 ]]; then
            echo "BAN: $f writes subagents.status outside subagent_state.transition()"
            echo "     pattern matched: $PATTERN"
            violations=$((violations + 1))
        fi
    done
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "Context: PR-28 mandates business.internal.subagent_state.transition()"
    echo "as the only write path to subagents.status. See"
    echo "novaic-business/business/internal/subagent_state.py for the ALLOWED"
    echo "matrix and the mark_* convenience helpers, or"
    echo "docs/roadmap/tickets/PR-28-subagent-state-machine.md for the RFC."
    exit 1
fi
echo "subagent_status lint OK"
