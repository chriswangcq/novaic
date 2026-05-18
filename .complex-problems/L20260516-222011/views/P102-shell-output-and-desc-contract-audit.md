# P102: Shell Output and Desc Contract Audit

Status: done
Parent: P002
Root: P000
Source Ticket: T096 (split)
Source Check: none
Package: problems/P000/children/P002/children/P102
Body: problems/P000/children/P002/children/P102/README.md
Ticket(s): T097

## Problem
Shell execution should expose bounded terminal text, preserve useful monitor `desc`, and avoid raw binary/base64 payloads in LLM-visible tool results.

## Success Criteria
- Inspect shell output contract implementation and tests.
- Verify `desc` is accepted and surfaced safely.
- Verify truncation/bounded terminal text behavior.
- Fix or route any gap found.

## Subproblems
- none

## Results
- R095

## Latest Check
C109

## Bodies
- Problem: problems/P000/children/P002/children/P102/README.md
- Ticket T097: problems/P000/children/P002/children/P102/tickets/T097.md
- Result R095: problems/P000/children/P002/children/P102/results/R095.md
- Check C109: problems/P000/children/P002/children/P102/checks/C109.md

## Follow-ups
- none
