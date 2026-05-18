# P787: Runtime Business Device Wording Cleanup

Status: done
Parent: P783
Root: P000
Source Ticket: T776 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P787
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P787/README.md
Ticket(s): T777

## Problem
Patch low-risk source docstrings/comments that misstate ownership boundaries without changing runtime behavior.

## Success Criteria
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py` wording no longer calls Cortex the single gateway to agent storage.
- `novaic-business/business/internal/message.py` cancellation wording does not imply direct Queue bypass.
- `novaic-device/device/config_agents_db.py` stale CASCADE cleanup comment is corrected or removed.
- `novaic-device/device/entity_store.py` historical Entangled wording is inspected and patched only if active/misleading.
- Focused import/compile checks pass for touched Python files.

## Subproblems
- none

## Results
- R768

## Latest Check
C814

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P787/README.md
- Ticket T777: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P787/tickets/T777.md
- Result R768: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P787/results/R768.md
- Check C814: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P787/checks/C814.md

## Follow-ups
- none
