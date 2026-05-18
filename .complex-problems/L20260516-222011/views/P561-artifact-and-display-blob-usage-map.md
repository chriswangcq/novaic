# P561: Artifact And Display Blob Usage Map

Status: done
Parent: P557
Root: P000
Source Ticket: T552 (split)
Source Check: none
Package: problems/P000/children/P005/children/P552/children/P557/children/P561
Body: problems/P000/children/P005/children/P552/children/P557/children/P561/README.md
Ticket(s): T555

## Problem
Separate intended cheap artifact/display blob usage from inappropriate blob-as-realtime-filesystem usage. This child belongs under P557 because blob should remain a cheap file server for artifacts, not the live RO/RW authority.

## Success Criteria
- Scans blob references across runtime, Cortex, sandbox, and docs.
- Classifies artifact/display usage versus real-time file semantics.
- Flags any blob usage that appears to proxy live RO/RW workspace state.
- Records exact commands and artifacts.

## Subproblems
- none

## Results
- R551

## Latest Check
C585

## Bodies
- Problem: problems/P000/children/P005/children/P552/children/P557/children/P561/README.md
- Ticket T555: problems/P000/children/P005/children/P552/children/P557/children/P561/tickets/T555.md
- Result R551: problems/P000/children/P005/children/P552/children/P557/children/P561/results/R551.md
- Check C585: problems/P000/children/P005/children/P552/children/P557/children/P561/checks/C585.md

## Follow-ups
- none
