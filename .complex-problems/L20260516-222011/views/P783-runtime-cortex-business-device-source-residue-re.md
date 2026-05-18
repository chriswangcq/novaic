# P783: Runtime Cortex Business Device Source Residue Remediation

Status: done
Parent: P750
Root: P000
Source Ticket: T774 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/README.md
Ticket(s): T776

## Problem
Patch precise active source comments/docstrings/compatibility paths discovered in Runtime, Cortex, Business, and Device source without broad source churn.

## Success Criteria
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` no longer overstates Cortex as the single gateway to agent storage.
- `novaic-cortex/novaic_cortex/step_result_projection.py` direct inline image/data URL display compatibility is narrowed or removed if the final contract is BlobRef-only.
- `novaic-business/business/internal/message.py` cancellation wording does not imply direct Queue bypass.
- `novaic-device/device/config_agents_db.py` stale CASCADE cleanup comment is corrected or removed.
- `novaic-device/device/entity_store.py` historical Entangled wording is inspected and narrowed only if active/misleading.
- Focused tests or import checks cover touched modules.

## Subproblems
- P787: Runtime Business Device Wording Cleanup
- P788: Cortex Step Result Projection BlobRef Contract Cleanup

## Results
- R772

## Latest Check
C818

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/README.md
- Ticket T776: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/tickets/T776.md
- Result R772: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/results/R772.md
- Check C818: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/checks/C818.md

## Follow-ups
- none
