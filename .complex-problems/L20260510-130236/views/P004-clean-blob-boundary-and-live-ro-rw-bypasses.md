# P004: Clean Blob boundary and live RO/RW bypasses

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P004
Body: problems/P000/children/P004/README.md
Ticket(s): T004

## Problem
Blob remains a cheap byte/object file server. Direct Blob access is allowed for
attachments, display bytes, artifact bytes, downloads, and LogicalFS persistence
internals. It must not remain as a live Cortex/shell `RO` / `RW` authority or
hidden fallback path.

## Success Criteria
- Direct Blob object calls are audited and either accepted as cheap-byte use or
- moved behind LogicalFS for live `RO` / `RW`.
- Tests or guard scripts fail on new direct live `RO` / `RW` Blob bypasses.
- Documentation and code comments do not imply Blob owns live workspace
- semantics.
- No display/download path depends on LogicalFS handles.

## Subproblems
- P006: Audit direct Blob and object API usage
- P007: Add Blob live RO/RW bypass guardrails
- P008: Clean stale Blob workspace ownership language
- P009: Verify Blob boundary cleanup

## Results
- R013

## Latest Check
C013

## Bodies
- Problem: problems/P000/children/P004/README.md
- Ticket T004: problems/P000/children/P004/tickets/T004.md
- Result R013: problems/P000/children/P004/results/R013.md
- Check C013: problems/P000/children/P004/checks/C013.md

## Follow-ups
- none
