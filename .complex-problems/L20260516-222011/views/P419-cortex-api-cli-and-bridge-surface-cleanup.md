# P419: Cortex API CLI and bridge surface cleanup

Status: done
Parent: P404
Root: P000
Source Ticket: T405 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/README.md
Ticket(s): T422

## Problem
Cortex API, CLI, and runtime bridge surfaces may expose or accept compatibility-shaped payloads even if internal lifecycle code is clean.

## Success Criteria
- Inspect Cortex API/CLI/bridge surfaces from the inventory.
- Ensure live callers must pass explicit generation/session/scope authority where required.
- Remove stale compatibility branches that infer active state from old storage shape.
- Add focused boundary tests for any changed API/CLI/bridge surface.
- Confirm shell/agent-facing behavior still returns pointer-oriented outputs rather than large inline payloads.

## Subproblems
- P434: Problem: Cortex API surface cleanup
- P435: Problem: Cortex CLI and shell capability cleanup
- P436: Problem: Cortex bridge surface cleanup

## Results
- R428

## Latest Check
C454

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/README.md
- Ticket T422: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/tickets/T422.md
- Result R428: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/results/R428.md
- Check C454: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P419/checks/C454.md

## Follow-ups
- none
