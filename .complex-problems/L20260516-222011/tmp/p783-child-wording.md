# Runtime Business Device Wording Cleanup

## Problem

Patch low-risk source docstrings/comments that misstate ownership boundaries without changing runtime behavior.

## Success Criteria

- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` wording no longer calls Cortex the single gateway to agent storage.
- `novaic-business/business/internal/message.py` cancellation wording does not imply direct Queue bypass.
- `novaic-device/device/config_agents_db.py` stale CASCADE cleanup comment is corrected or removed.
- `novaic-device/device/entity_store.py` historical Entangled wording is inspected and patched only if active/misleading.
- Focused import/compile checks pass for touched Python files.

