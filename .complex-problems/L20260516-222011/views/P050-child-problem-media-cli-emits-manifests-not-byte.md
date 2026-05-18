# P050: Child Problem: media CLI emits manifests, not bytes

Status: done
Parent: P048
Root: P000
Source Ticket: T041 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P050
Body: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P050/README.md
Ticket(s): T042

## Problem
Screenshot and media CLI commands must return concise terminal text plus blob/artifact manifests. Active CLI paths must not print raw base64, data URLs, or large binary JSON fields to stdout where they enter shell observations and Cortex step text.

## Success Criteria
- `devicectl` screenshot/media paths emit `tool-output.v1`-style manifests or equivalent blob/artifact pointers.
- No active screenshot/media CLI stdout path contains raw `screenshot` base64 payloads, `data:image/*;base64`, or unbounded media bytes.
- Focused CLI tests or scans prove the stdout contract.

## Subproblems
- none

## Results
- R037

## Latest Check
C047

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P050/README.md
- Ticket T042: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P050/tickets/T042.md
- Result R037: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P050/results/R037.md
- Check C047: problems/P000/children/P001/children/P009/children/P016/children/P048/children/P050/checks/C047.md

## Follow-ups
- none
