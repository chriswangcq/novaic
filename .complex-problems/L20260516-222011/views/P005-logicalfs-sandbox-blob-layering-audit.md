# P005: LogicalFS sandbox blob layering audit

Status: done
Parent: P000
Root: P000
Source Ticket: T000 (split)
Source Check: none
Package: problems/P000/children/P005
Body: problems/P000/children/P005/README.md
Ticket(s): T549

## Problem
Audit and optimize the current layering among Cortex, LogicalFS, sandbox service, sandbox core, and blob service. Ensure real-time RO/RW file semantics go through LogicalFS/sandbox as intended while cheap durable artifacts use blob, with no old direct materialization bypasses.

## Success Criteria
- Layer boundaries and current imports/calls are inspected.
- Direct fallback/backdoor paths are searched.
- Any stale fallback or misleading compatibility route is removed or documented as current necessity.
- Tests or static checks verify the intended layering where feasible.

## Subproblems
- P552: LogicalFS Sandbox Blob Topology Map
- P553: LogicalFS Sandbox Blob Fallback Residue Inventory
- P554: LogicalFS Sandbox Blob Layering Remediation
- P555: LogicalFS Sandbox Blob Layering Final Verification

## Results
- R655

## Latest Check
C697

## Bodies
- Problem: problems/P000/children/P005/README.md
- Ticket T549: problems/P000/children/P005/tickets/T549.md
- Result R655: problems/P000/children/P005/results/R655.md
- Check C697: problems/P000/children/P005/checks/C697.md

## Follow-ups
- none
