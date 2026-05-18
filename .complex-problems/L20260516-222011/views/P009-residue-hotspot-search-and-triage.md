# P009: Residue hotspot search and triage

Status: done
Parent: P001
Root: P000
Source Ticket: T001 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009
Body: problems/P000/children/P001/children/P009/README.md
Ticket(s): T008

## Problem
Search for stale, misleading, or old-path residue across active code/tests/docs: compatibility shims, direct tool names that should be shell CLI, old `/tmp/novaic-cortex-sandbox-*` path dependencies, base64/image leakage, TODO/FIXME, fallback/backdoor wording, and disabled/skipped tests.

## Success Criteria
- Residue searches use bounded `rg` patterns and record evidence pointers.
- Hits are triaged into active issue, benign historical ledger/doc, or candidate for another child problem.
- High-confidence tiny cleanup can be fixed only if directly supported by evidence and tests.
- Result lists concrete follow-up targets for the specialized child problems.

## Subproblems
- P015: Direct tool and hidden harness residue scan
- P016: Ephemeral path and media payload leakage scan
- P017: Fallback compatibility and TODO residue scan

## Results
- R093

## Latest Check
C107

## Bodies
- Problem: problems/P000/children/P001/children/P009/README.md
- Ticket T008: problems/P000/children/P001/children/P009/tickets/T008.md
- Result R093: problems/P000/children/P001/children/P009/results/R093.md
- Check C107: problems/P000/children/P001/children/P009/checks/C107.md

## Follow-ups
- none
