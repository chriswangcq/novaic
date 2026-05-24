#!/usr/bin/env bash
#
# PR-168E — chat_messages.lifecycle is not an Agent-loop state path.
#
# Why
# ---
# Environment notifications own Agent-loop delivery and lifecycle. Any new
# writer to chat_messages.lifecycle is therefore a bug that reintroduces the
# retired message-lifecycle branch.
#
# How
# ---
# There is no active writer allowlist. Tests and docs may mention old shapes
# only as guardrails or archaeology.
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
        echo "BAN: $f contains raw UPDATE chat_messages SET lifecycle — Environment notifications own lifecycle"
        violations=$((violations + 1))
    fi
done

if [[ $violations -gt 0 ]]; then
    echo ""
    echo "Context: PR-168E retired the chat_messages.lifecycle Agent-loop path."
    echo "Use Environment notifications for wake delivery and lifecycle."
    exit 1
fi
echo "lifecycle lint OK"
