# P623: Sandbox SDK API and Wire Boundary Residue

Status: done
Parent: P621
Root: P000
Source Ticket: T617 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P623
Body: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P623/README.md
Ticket(s): T618

## Problem
Audit `novaic-sandbox-sdk` production code for execution/session APIs, local fallback, subprocess/process execution, host path/mount manipulation, and base64 stdout/stderr wire decoding.

## Success Criteria
- Records exact scans over `novaic-sandbox-sdk` for subprocess/process/local/fallback/host/mount/base64/stdout/stderr/compat terms.
- Cites source slices for the public client API and any wire encode/decode handling.
- Classifies each hit as intended SDK wire handling, test fixture, risky fallback, or removable residue.
- Creates a remediation follow-up if SDK exposes active local execution or public byte leakage.

## Subproblems
- none

## Results
- R613

## Latest Check
C654

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P623/README.md
- Ticket T618: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P623/tickets/T618.md
- Result R613: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P623/results/R613.md
- Check C654: problems/P000/children/P005/children/P553/children/P565/children/P621/children/P623/checks/C654.md

## Follow-ups
- none
