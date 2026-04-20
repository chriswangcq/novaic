#!/usr/bin/env bash
#
# PR-30 (2026-04-15) — ban any re-introduction of the four legacy
# chat_messages columns that were dropped after PR-21 (lifecycle state
# machine) had stabilised.
#
# Why
# ---
# ``chat_messages.{processed,claimed_by,claimed_at,status}`` were the
# pre-PR-21 way to track dispatch state. Production ran them in parallel
# with ``lifecycle`` for one release, the live data was migrated by
# ``backfill_lifecycle()``, and PR-30 drops the columns + rewrites every
# Python writer to skip them. If a follow-up PR re-introduces any of
# these names, we'd be back to the dual-source bug class that PR-21 was
# built to eliminate (orphan-scan misses claimed rows, transition() and
# raw UPDATE drift apart, etc.).
#
# This lint covers two things:
#   1. Schema declarations (``F.text("status", ...)`` and friends in
#      ``business/schema_push.py``).
#   2. Row writers (``"status": "..."`` literal keys in dicts that get
#      passed to ``store.append("messages", ...)``).
#
# The pattern set is deliberately narrow — common English words like
# "status" and "processed" appear all over the codebase as variable
# names; we only flag occurrences in ``business/`` schemas and writers
# that target the messages table. ``read`` is intentionally NOT here:
# it tracks user-visible read receipts, not dispatch state.
#
# Allowlist
# ---------
# * Entangled migration helpers (legacy column DROP + backfill).
# * tests/ — fixtures still construct legacy-shaped rows to drive backfill.
# * docs/ — RFC text references the column names.
set -e

# Match a chat_messages row literal (rough heuristic: the dict has both
# ``"agent_id"`` and one of the banned legacy keys close by) and the
# four schema declarations.
# Narrow patterns: ``processed`` / ``claimed_by`` / ``claimed_at`` are
# *only* chat_messages columns (no name collisions with other entities),
# so banning them in any schema or row literal is safe. ``status`` we
# can't ban globally — subagents / drafts / agent_records all legitimately
# use a column called ``status`` — so we only catch the
# ``"status": "sent"`` literal, which is the dispatch-default value
# unique to chat_messages writers.
PATTERNS=(
    'F\.text\("(claimed_by|claimed_at)"'
    'F\.int_\("processed"'
    '"processed"\s*:\s*[01]'
    '"claimed_by"\s*:\s*"'
    '"claimed_at"\s*:\s*"'
    '"status"\s*:\s*"sent"'
)

ALLOWLIST=(
    'Entangled/packages/server-python/entangled/sql/message_state.py'
    'Entangled/packages/server-python/entangled/sql/entity_store.py'
    'tests/'
    'docs/'
    'scripts/ci/lint_legacy_message_columns.sh'
)

violations=0
for PATTERN in "${PATTERNS[@]}"; do
    HITS=$(rg -l --pcre2 -U "$PATTERN" \
              --glob '*.py' \
              novaic-business novaic-agent-runtime Entangled 2>/dev/null || true)
    for f in $HITS; do
        ok=0
        for a in "${ALLOWLIST[@]}"; do
            [[ "$f" == *"$a"* ]] && ok=1
        done
        if [[ $ok -eq 0 ]]; then
            echo "BAN: $f re-introduces a dropped chat_messages column"
            echo "     pattern matched: $PATTERN"
            violations=$((violations + 1))
        fi
    done
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "Context: PR-30 dropped chat_messages.{processed,claimed_by,"
    echo "claimed_at,status}. Use ``lifecycle`` (via Entangled's"
    echo "POST /v1/messages/{id}/transition) for dispatch state and"
    echo "``read`` for user-facing unread receipts. See"
    echo "docs/roadmap/tickets/PR-30-drop-legacy-message-fields.md."
    exit 1
fi
echo "legacy_message_columns lint OK"
