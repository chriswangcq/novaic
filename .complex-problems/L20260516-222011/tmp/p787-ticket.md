# Runtime Business Device Wording Cleanup Ticket

## Problem Definition

Patch low-risk source comments/docstrings in Runtime, Business, and Device so they no longer imply stale service ownership boundaries.

## Proposed Solution

Read and minimally edit:

- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
- `novaic-business/business/internal/message.py`
- `novaic-device/device/config_agents_db.py`
- `novaic-device/device/entity_store.py`

Only patch `entity_store.py` if the exact wording is active and misleading.

## Acceptance Criteria

- Cortex bridge wording is precise about Runtime using Cortex APIs for scope/context/workspace operations, not all agent storage.
- Business cancellation wording does not imply a direct Queue bypass.
- Device config cleanup comments do not preserve stale table-cleanup guidance.
- Entity store wording is inspected and, if needed, narrowed.
- Python compile/import checks pass for touched files.

## Verification Plan

Use `rg` and focused file reads before patching, then run `python -m py_compile` or package-specific focused checks for touched Python files. Re-run targeted `rg` for stale phrases.
