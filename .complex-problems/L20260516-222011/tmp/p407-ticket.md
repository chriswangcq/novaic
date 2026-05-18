# Runtime session authority cleanup ticket

## Problem Definition

Runtime session-authority files still appear in the compatibility guard output. These hits must be inspected so live session mutation paths cannot silently infer, default, or accept stale generation.

## Proposed Solution

Audit and, if needed, patch:

- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/queue_service/session_fsm.py`
- `novaic-agent-runtime/queue_service/session_outbox.py`
- `novaic-agent-runtime/queue_service/session_recovery.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/session_observed_events.py`
- `novaic-agent-runtime/queue_service/queue_audit.py`

Classify each hit from the P402 guards as explicit validator, safe audit/projection reader, or dangerous residue. Patch dangerous live paths and add focused tests.

## Acceptance Criteria

- All session-authority runtime hits from P402 are classified.
- Live session mutation paths require explicit positive/non-negative generation as appropriate.
- Any changed live boundary has focused regression tests.
- Session-authority guards no longer report unclassified generation compatibility residue.

## Verification Plan

- Inspect P402 guard outputs and source files with line references.
- Run targeted `rg` guards over the session-authority file set.
- Run focused tests around session repo/FSM/outbox/recovery/ledger/audit if code changes.
- If no implementation change is needed, record a file-evidence matrix.

## Risks

- Audit/projection readers may legitimately parse historical event state; do not over-patch read-only paths into breaking behavior unless they influence live mutation.
- Session generation `0` may be valid for no-active/generic state but not for active session authority; classification must be precise.

## Assumptions

- No missing/stale generation compatibility is required for live session mutation.
- Read-only audit/projection classification is acceptable only with clear evidence that it cannot clear/restart/archive active state.
