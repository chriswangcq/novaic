#!/usr/bin/env bash
#
# Ban re-introduction of the pre-PR-21 chat_messages dispatch-state
# columns (``processed``/``claimed_by``/``claimed_at``/``status``).
# The lifecycle state machine (``lifecycle`` + ``claimed_by_scope``)
# is now the only dispatch-state surface; re-adding any of the old
# columns would split writes across two sources and regress the exact
# bug class PR-21 eliminated (orphan scan misses claimed rows, raw
# UPDATEs drift apart from transition(), etc.).
#
# This lint covers two things:
#   1. Schema declarations (``F.text("status", ...)`` and friends in
#      ``business/schema_push.py``).
#   2. Row writers (``"status": "..."`` literal keys in dicts that get
#      passed to ``store.append("messages", ...)``).
#
# The pattern set is deliberately narrow — common English words like
# "status" and "processed" appear all over the codebase as variable
# names; we only flag occurrences in schemas and writers that target
# the messages table. ``read`` is intentionally NOT here: it tracks
# user-visible read receipts, not dispatch state.
set -e

# Match a chat_messages row literal (rough heuristic: the dict has both
# ``"agent_id"`` and one of the banned retired keys close by) and the
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
    'tests/'
    'docs/'
    'scripts/ci/lint_retired_message_columns.sh'
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
    echo "Context: chat_messages.{processed,claimed_by,claimed_at,status}"
    echo "are banned. Use ``lifecycle`` (via Entangled's"
    echo "POST /v1/messages/{id}/transition) for dispatch state and"
    echo "``read`` for user-facing unread receipts. See"
    echo "the retired-message-fields roadmap note."
    exit 1
fi
echo "retired_message_columns lint OK"
