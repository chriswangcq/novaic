#!/usr/bin/env bash
#
# PR-41 (2026-04-21) — keep orphan eligibility in sync with the outbox
# trigger-type registry.
#
# Why
# ---
# Two sources of truth decide whether a chat_messages row is "an
# orphan worth waking for":
#
#   1. Write side — ``MESSAGES_DEF.outbox_trigger_types`` in
#      ``novaic-business/business/schema_push.py``. A type listed here
#      gets an ``message_outbox`` row co-inserted alongside the
#      ``chat_messages`` INSERT and stays ``lifecycle='pending'``
#      until a subscriber claims it. Anything else is born
#      ``lifecycle='consumed'`` (see
#      entangled/sql/entity_store.py::append) and never enters the
#      dispatch pipeline.
#
#   2. Read side — ``ORPHAN_ELIGIBLE_TYPES`` in
#      ``Entangled/packages/server-python/entangled/app/orphans.py``.
#      The orphan query filters ``type IN (…)`` so the HealthWorker
#      scanner never sees rows whose type has no consumer.
#
# If these two drift, we get back exactly the bug PR-41 exists to
# fix: a type that writes pending rows but has no consumer will
# either (a) spam the orphan view forever, or (b) silently vanish
# from the operator's radar depending on which list the new type
# landed in.
#
# This lint extracts both lists and requires them to match exactly.
#
# How
# ---
# Both sources use simple literal collections, so we grep them out
# directly rather than importing Python (CI should be able to run
# this without the novaic-business venv active).
#
# Pattern — Business side (outbox_trigger_types=…):
#   outbox_trigger_types={
#       "USER_MESSAGE": "user_message",
#       ...
#   },
#
# Pattern — Entangled side (ORPHAN_ELIGIBLE_TYPES=…):
#   ORPHAN_ELIGIBLE_TYPES: tuple[str, ...] = (
#       "USER_MESSAGE",
#       ...
#   )
#
# Anyone who adds a new type to one side and forgets the other
# gets a non-zero exit here.
set -euo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
BUSINESS_FILE="${REPO_ROOT}/novaic-business/business/schema_push.py"
ORPHANS_FILE="${REPO_ROOT}/Entangled/packages/server-python/entangled/app/orphans.py"

if [[ ! -f "$BUSINESS_FILE" ]]; then
  echo "ERROR: $BUSINESS_FILE not found — repo layout changed?"
  exit 1
fi
if [[ ! -f "$ORPHANS_FILE" ]]; then
  echo "ERROR: $ORPHANS_FILE not found — repo layout changed?"
  exit 1
fi

# Extract the trigger type keys from MESSAGES_DEF.outbox_trigger_types.
# Block starts at ``outbox_trigger_types={`` and ends at the matching ``}``.
# We only need the dict keys (the LHS of the mapping).
BUSINESS_KEYS=$(python3 - "$BUSINESS_FILE" <<'PY'
import re
import sys

src = open(sys.argv[1]).read()
m = re.search(r"outbox_trigger_types\s*=\s*\{([^}]*)\}", src)
if not m:
    print("ERROR_NO_MATCH", file=sys.stderr)
    sys.exit(2)
keys = re.findall(r'"([A-Z_]+)"\s*:', m.group(1))
for k in sorted(set(keys)):
    print(k)
PY
)

ORPHANS_KEYS=$(python3 - "$ORPHANS_FILE" <<'PY'
import re
import sys

src = open(sys.argv[1]).read()
m = re.search(r"ORPHAN_ELIGIBLE_TYPES[^=]*=\s*\(([^)]*)\)", src)
if not m:
    print("ERROR_NO_MATCH", file=sys.stderr)
    sys.exit(2)
keys = re.findall(r'"([A-Z_]+)"', m.group(1))
for k in sorted(set(keys)):
    print(k)
PY
)

if [[ "$BUSINESS_KEYS" != "$ORPHANS_KEYS" ]]; then
    echo "=========================================================="
    echo "outbox trigger type drift detected (PR-41 sync violation)."
    echo ""
    echo "MESSAGES_DEF.outbox_trigger_types in"
    echo "  $BUSINESS_FILE"
    echo "--------------------"
    echo "$BUSINESS_KEYS"
    echo ""
    echo "ORPHAN_ELIGIBLE_TYPES in"
    echo "  $ORPHANS_FILE"
    echo "--------------------"
    echo "$ORPHANS_KEYS"
    echo ""
    echo "These lists MUST be identical — see header of this script"
    echo "or docs/roadmap/tickets/PR-41-agent-reply-not-orphan-eligible.md"
    echo "for why."
    echo "=========================================================="
    exit 1
fi

echo "outbox-trigger ↔ orphan-eligible sync OK"
