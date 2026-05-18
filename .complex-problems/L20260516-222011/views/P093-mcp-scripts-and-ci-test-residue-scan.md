# P093: MCP scripts and CI test residue scan

Status: done
Parent: P067
Root: P000
Source Ticket: T082 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093
Body: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/README.md
Ticket(s): T086

## Problem
MCP tests and repository scripts/CI tests may contain stale skip/TODO/FIXME/compat/fallback/legacy fixtures or policy comments that need classification.

## Success Criteria
- Scan MCP tests and scripts/CI test files for residue markers.
- Classify hits as intentional guard/policy vocabulary, harmless fixture text, or stale residue.
- Clean tiny stale residue when safe.
- Run focused MCP/script tests or explicit no-code-change verification.

## Subproblems
- P094: MCP Test Residue Scan
- P095: Scripts and CI Helper Residue Scan
- P096: MCP Scripts CI Final Residue Sweep

## Results
- R086

## Latest Check
C100

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/README.md
- Ticket T086: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/tickets/T086.md
- Result R086: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/results/R086.md
- Check C100: problems/P000/children/P001/children/P009/children/P017/children/P067/children/P093/checks/C100.md

## Follow-ups
- none
