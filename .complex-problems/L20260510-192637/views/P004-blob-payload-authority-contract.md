# P004: Blob Payload Authority Contract

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T004

## Problem
Large tool payload bytes are stored in Blob Service while Workspace holds semantic refs. This is probably correct, but the authority contract must be explicit so Blob does not become a hidden semantic store.

## Success Criteria
- Define Blob as raw byte/artifact authority only.
- Define where semantic metadata and lifecycle refs live.
- Specify verification for payload fetch, missing blob behavior, retention, and cleanup.

## Subproblems
- none

## Results
- R003

## Latest Check
C003

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T004: problems/P000/children/P004/tickets/T004.md
- Result R003: problems/P000/children/P004/results/R003.md
- Check C003: problems/P000/children/P004/checks/C003.md

## Follow-ups
- none
