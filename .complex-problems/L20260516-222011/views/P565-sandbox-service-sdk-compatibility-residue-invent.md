# P565: Sandbox Service SDK Compatibility Residue Inventory

Status: done
Parent: P553
Root: P000
Source Ticket: T557 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P565
Body: problems/P000/children/P005/children/P553/children/P565/README.md
Ticket(s): T615

## Problem
Search sandbox service, sandbox core, and sandbox SDK code for compatibility branches, direct host path exposure, mount bypasses, or legacy execution paths that could bypass the sandboxd boundary. This belongs under P553 because sandboxd should be the only process execution service while LogicalFS supplies the mounted file view.

## Success Criteria
- Records exact static scan commands and outputs.
- Classifies sandbox service/core/SDK compatibility and path-mount hits as intended, risky, removable, or follow-up.
- Confirms stdout/stderr base64 is only sandboxd wire encoding, not public LLM history.
- Captures any high-confidence risky residue for P554 remediation.

## Subproblems
- P620: Sandbox Service Execution Boundary Residue
- P621: Sandbox SDK Client Boundary Residue
- P622: Sandbox Wire Base64 and Mount Residue Classification

## Results
- R622

## Latest Check
C663

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P565/README.md
- Ticket T615: problems/P000/children/P005/children/P553/children/P565/tickets/T615.md
- Result R622: problems/P000/children/P005/children/P553/children/P565/results/R622.md
- Check C663: problems/P000/children/P005/children/P553/children/P565/checks/C663.md

## Follow-ups
- none
