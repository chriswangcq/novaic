# P000: Audit LogicalFS RO/RW design documents

Status: done
Parent: none
Root: P000
Package: problems/P000
Body: problems/P000/README.md
Ticket(s): T000

## Problem
Audit the current LogicalFS / Blob / Cortex / Sandbox design documents against
the clarified architecture principle:

- Blob is a cheap file server for durable bytes, attachments, display bytes,
  artifact bytes, and object/blob references.
- LogicalFS is not a universal file service. It is the Cortex/shell live
  `RO` / `RW` semantic authority.
- Cortex/shell live `RO` / `RW` paths must go through LogicalFS.
- Display/download must go through Blob. If a live `RO` / `RW` file must be
  displayed or downloaded, it is exported/copied to Blob first; LogicalFS must
  not expose display/download handles.

Check the design docs for over-broad statements, contradictory ownership, stale
phrasing, and missing boundary language. Fix documentation gaps found during
the audit.

## Success Criteria
- The relevant docs consistently describe Blob as the cheap byte/file server.
- The relevant docs consistently describe LogicalFS as only the Cortex/shell
- live `RO` / `RW` authority.
- No audited doc claims LogicalFS owns display/download handles or all file
- services.
- Any remaining transitional code path is explicitly labeled transitional.
- The audit has a recorded result and success check with concrete evidence.

## Subproblems
- none

## Results
- R000

## Latest Check
C000

## Bodies
- Problem: problems/P000/README.md
- Ticket T000: problems/P000/tickets/T000.md
- Result R000: problems/P000/results/R000.md
- Check C000: problems/P000/checks/C000.md

## Follow-ups
- none
