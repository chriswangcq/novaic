# P508 Remediation Decision

## Decision

No source remediation is required for P508.

## Why

The targeted sweep confirms the ownership boundaries found by P507:

- Cortex archive from recovery is only through `SessionOutboxDispatcher.RECOVERY_ARCHIVE_SCOPE -> CORTEX_SCOPE_END` or normal `wake_finalize` saga step.
- Session-owned wake saga creation is still limited to `SessionOutboxDispatcher._publish_create_wake_saga`; session repo and wake plan only build/write outbox effects.
- Wake-finalize failure records `SESSION_SUSPECTED_DEAD` through `SagaRepository`, and recovery shaping remains pure helper logic.
- Session-ended mutation remains owned by `SessionRepository.session_ended` via explicit handler/client/route boundaries.

## Watch Items Evaluated

1. `CortexBridge.scope_end` optional fields: no remediation. The bridge is generic; strictness lives in `task_queue/handlers/cortex_handlers.py` for the active task path.
2. Explicit unknown stack in compensation/recovery: no remediation. It is intentional when failed saga context lacks stack diagnostics, and it is encoded as `{"known": False, "depth": 0, "frames": []}` rather than silently omitted.

## Evidence

- P507 ownership map: `.complex-problems/L20260516-222011/tmp/p507/finalize-recovery-ownership-map.md`
- P508 targeted sweep: `.complex-problems/L20260516-222011/tmp/p508/remediation-decision-sweep.txt`
