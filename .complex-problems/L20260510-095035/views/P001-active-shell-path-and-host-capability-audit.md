# P001: Active Shell Path And Host Capability Audit

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P001
Body: problems/P000/children/P001/README.md
Ticket(s): T001

## Problem
Before editing, map the current active Cortex shell path, hidden temp-projection dependencies, and local host filesystem capabilities. The implementation must not be based on wishful assumptions about `/cortex`, FUSE, or mount namespace support.

## Success Criteria
- Identify the current entry points and active functions for shell execution.
- Identify all old temp-projection and command-string gating logic to delete or move.
- Identify local host support for true `/cortex` mount semantics.
- Record the exact implementation constraints that child tickets must obey.

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
