# P198: Projection branch inventory and classification

Status: done
Parent: P187
Root: P000
Source Ticket: T188 (split)
Source Check: none
Package: problems/P000/children/P003/children/P127/children/P187/children/P198
Body: problems/P000/children/P003/children/P127/children/P187/children/P198/README.md
Ticket(s): T189

## Problem
Before deleting or preserving any branch, we need a precise inventory of projection-related production and test branches. The risk is hidden residue: old nested wrappers, legacy MCP arrays, duplicate converters, or stale tests may look harmless while still steering future changes.

## Success Criteria
- Search production and tests for projection-related branches, including `display_files`, `_projection`, `tool-output.v1`, `_mcp_content`, `image_url`, `data:image`, `base64`, `llm_content`, nested `result` wrappers, and artifact manifest handling.
- Produce a classification table for suspicious branches: active, test-only, compatibility, or stale.
- Identify exact file/line references for any branch that should be removed in a child problem.
- Avoid changing code in this inventory problem.

## Subproblems
- P202: Cortex projection branch inventory
- P203: Runtime and factory projection branch inventory
- P204: Projection test branch inventory

## Results
- R190

## Latest Check
C204

## Bodies
- Problem: problems/P000/children/P003/children/P127/children/P187/children/P198/README.md
- Ticket T189: problems/P000/children/P003/children/P127/children/P187/children/P198/tickets/T189.md
- Result R190: problems/P000/children/P003/children/P127/children/P187/children/P198/results/R190.md
- Check C204: problems/P000/children/P003/children/P127/children/P187/children/P198/checks/C204.md

## Follow-ups
- none
