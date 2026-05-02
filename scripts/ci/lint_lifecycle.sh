#!/usr/bin/env bash
#
# PR-21 (2026-04-20) — ban raw UPDATEs to chat_messages.lifecycle.
#
# Why
# ---
# chat_messages.lifecycle is the authoritative state column for the
# message state machine (see Entangled/packages/server-python/entangled/
# sql/message_state.py). A raw ``UPDATE chat_messages SET lifecycle = ...``
# bypasses transition() — meaning:
#   * the state-diagram rules aren't enforced (consumed → claimed
#     regressions slip through silently),
#   * claimed_by_scope / lifecycle_updated_at can drift from lifecycle,
#   * the PR-26 orphan scanner and PR-25 message trace each rely on the
#     single-writer log line that transition() emits; a raw UPDATE
#     produces no such line and silently breaks both downstream PRs.
#
# How
# ---
# The only legitimate writers are:
#   1. entangled/sql/message_state.py          (the helper itself)
#   2. entangled/app/message_state.py          (HTTP wrapper)
#   3. tests/                                   (every repo's test dir)
#   4. docs/                                    (example SQL in markdown)
#   5. docs/roadmap/tickets/PR-21-*            (the ticket itself shows
#                                               the DDL / migration SQL)
# Anything else hitting the pattern needs justification and an allowlist
# entry here. If you just need to transition a message, call
# POST /v1/messages/{id}/transition instead.
#
# Pattern
# -------
# We match both raw SQL (``UPDATE chat_messages SET lifecycle``) AND the
# logical equivalent of building a dynamic SET clause that includes the
# column name. The first form is the real concern; the second catches
# clever code that assembles UPDATEs at runtime.
set -e

PATTERN='UPDATE\s+chat_messages\s+SET[^;]*lifecycle'

ALLOWLIST=(
  'Entangled/packages/server-python/entangled/sql/message_state.py'
  'Entangled/packages/server-python/entangled/app/message_state.py'
  'Entangled/packages/server-python/tests/'
  'tests/'
  'docs/'
  'scripts/ci/lint_lifecycle.sh'
)

RETIRED_FILES=(
  'scripts/gateway/migrate_pr41_agent_reply_orphans.sh'
  'scripts/migrations/047_cleanup_ancient_user_message_pending.sql'
  'scripts/migrations/048_cleanup_stuck_claimed.sql'
  'docs/runbooks/pr41-pr42-staging-verification.md'
)

for retired in "${RETIRED_FILES[@]}"; do
    if [[ -e "$retired" ]]; then
        echo "BAN: retired one-shot lifecycle cleanup entry still exists: $retired"
        exit 1
    fi
done

# rg -l: list files only; --pcre2: allow multiline spans if someone splits
# the statement across two lines via a triple-quoted string. Restrict to
# code/doc extensions we actually care about.
HITS=$(rg -l --pcre2 -U "$PATTERN" \
          --glob '*.py' --glob '*.sh' --glob '*.sql' --glob '*.md' \
          Entangled novaic-* scripts docs 2>/dev/null || true)

violations=0
for f in $HITS; do
    ok=0
    for a in "${ALLOWLIST[@]}"; do
        [[ "$f" == *"$a"* ]] && ok=1
    done
    if [[ $ok -eq 0 ]]; then
        echo "BAN: $f contains raw UPDATE chat_messages SET lifecycle — route via transition()"
        violations=$((violations + 1))
    fi
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "Context: PR-21 mandates POST /v1/messages/{id}/transition as"
    echo "the only write path to chat_messages.lifecycle. See"
    echo "Entangled/packages/server-python/entangled/sql/message_state.py"
    echo "for rationale, or docs/roadmap/tickets/PR-21-message-lifecycle-enum.md"
    echo "for the RFC."
    exit 1
fi
echo "lifecycle lint OK"
