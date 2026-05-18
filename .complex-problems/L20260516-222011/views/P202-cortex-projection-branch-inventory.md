# P202: Cortex projection branch inventory

Status: done
Parent: P198
Root: P000
Source Ticket: T189 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P198/children/P202
Body: problems/P000/children/P003/children/P127/children/P187/children/P198/children/P202/README.md
Ticket(s): T190

## Problem
Cortex is responsible for parsing step/tool result payloads and producing history/display projections. We need to classify Cortex projection branches before any stale cleanup.

## Success Criteria
- Inventory `novaic-cortex/novaic_cortex/step_result_projection.py` and related API projection call sites.
- Classify suspicious Cortex branches involving `tool-output.v1`, `llm_content`, `_mcp_content`, display files, data URLs, artifact manifests, and truncation.
- Identify stale Cortex cleanup candidates with exact file/line evidence.
- Do not edit code in this inventory problem.

## Subproblems
- none

## Results
- R185

## Latest Check
C199

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P198/children/P202/README.md
- Ticket T190: problems/P000/children/P003/children/P127/children/P187/children/P198/children/P202/tickets/T190.md
- Result R185: problems/P000/children/P003/children/P127/children/P187/children/P198/children/P202/results/R185.md
- Check C199: problems/P000/children/P003/children/P127/children/P187/children/P198/children/P202/checks/C199.md

## Follow-ups
- none
