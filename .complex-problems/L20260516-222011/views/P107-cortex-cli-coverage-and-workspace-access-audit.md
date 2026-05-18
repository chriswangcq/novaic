# P107: Cortex CLI Coverage and Workspace Access Audit

Status: done
Parent: P103
Root: P000
Source Ticket: T098 (split)
Source Check: none
Package: problems/P000/children/P002/children/P103/children/P107
Body: problems/P000/children/P002/children/P103/children/P107/README.md
Ticket(s): T106

## Problem
Cortex payload and workspace access must be usable from shell through stable CLI commands and stable `/cortex/ro`/`/cortex/rw` paths, without requiring agents to depend on ephemeral backing paths or direct non-shell tools.

## Success Criteria
- Locate Cortex CLI implementation and shell capability documentation for payload read/search/summarize/qa and workspace access.
- Verify stable path guidance is present and old ephemeral-path usage is blocked or discouraged.
- Run focused tests for Cortex payload/workspace shell contract if present.
- Fix missing or misleading Cortex CLI coverage if bounded.

## Subproblems
- P113: Cortex Payload CLI Coverage Audit
- P114: Cortex Stable Workspace Path Contract Audit

## Results
- R112

## Latest Check
C126

## Bodies
- Problem: problems/P000/children/P002/children/P103/children/P107/README.md
- Ticket T106: problems/P000/children/P002/children/P103/children/P107/tickets/T106.md
- Result R112: problems/P000/children/P002/children/P103/children/P107/results/R112.md
- Check C126: problems/P000/children/P002/children/P103/children/P107/checks/C126.md

## Follow-ups
- none
