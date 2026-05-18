# Runtime Cortex Business Device Source Residue Remediation

## Problem

Patch precise active source comments/docstrings/compatibility paths discovered in Runtime, Cortex, Business, and Device source without broad source churn.

## Success Criteria

- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` no longer overstates Cortex as the single gateway to agent storage.
- `novaic-cortex/novaic_cortex/step_result_projection.py` direct inline image/data URL display compatibility is narrowed or removed if the final contract is BlobRef-only.
- `novaic-business/business/internal/message.py` cancellation wording does not imply direct Queue bypass.
- `novaic-device/device/config_agents_db.py` stale CASCADE cleanup comment is corrected or removed.
- `novaic-device/device/entity_store.py` historical Entangled wording is inspected and narrowed only if active/misleading.
- Focused tests or import checks cover touched modules.
