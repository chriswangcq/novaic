# P001: Create LogicalFS substrate package

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
LogicalFS needs a business-agnostic substrate that understands only snapshot/view/patch contracts, materialization, diffing, path sanitization, and view handles. This package must not know Cortex, agentctl, subagents, or process execution.

## Success Criteria
- `novaic-logicalfs` package exists with explicit DTOs for snapshot, file entries, writable layout, env overlay, view handle, and patch.
- Package can materialize a snapshot to local RO/RW roots and produce a patch from RW changes.
- Package has unit tests for materialization, deletion/change diffing, layout env, cwd validation, and path sanitization.
- Package imports no Cortex, sandbox core, sandbox sdk, agent runtime, agentctl, or product business modules.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/children/P001/README.md
- Ticket T001: problems/P000/children/P001/tickets/T001.md
- Result R000: problems/P000/children/P001/results/R000.md
- Check C000: problems/P000/children/P001/checks/C000.md

## Follow-ups
- none
