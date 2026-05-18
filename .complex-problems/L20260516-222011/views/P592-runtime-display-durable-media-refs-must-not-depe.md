# P592: Runtime display durable media refs must not depend on inline bytes

Status: done
Parent: P588
Root: P000
Source Ticket: none (none)
Source Check: C606
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/children/P592
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/children/P592/README.md
Ticket(s): T578

## Problem
The first P588 implementation removed persisted base64 for inline images, but still derived `image_ref` from `_mcp_content[].data`. This leaves a hidden dependency on inline bytes and fails for large images or future display implementations that return BlobRef metadata without inline image data.

## Success Criteria
- `_display_durable_payload` creates image references from `file_url`, `mime_type`, and `size` when the result represents an image BlobRef.
- Inline `_mcp_content[].data` is never required to create durable `image_ref`.
- Tests cover both a small inline image and a large image/text-placeholder result.
- Durable payload remains base64-free in both cases.

## Subproblems
- none

## Results
- R571

## Latest Check
C607

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/children/P592/README.md
- Ticket T578: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/children/P592/tickets/T578.md
- Result R571: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/children/P592/results/R571.md
- Check C607: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P586/children/P588/children/P592/checks/C607.md

## Follow-ups
- none
