# P585: Child Problem: Display BlobRef perception design and call-path map

Status: done
Parent: P584
Root: P000
Source Ticket: T574 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P585
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P585/README.md
Ticket(s): T575

## Problem
Before editing, identify the exact path from display executor result to Cortex step payload, step-result formatting, runtime step expansion, multimodal processing, and provider request construction. Choose the smallest clean boundary where BlobRef media can be resolved without storing base64 in durable payload.

## Success Criteria
- Records call-path slices with line references.
- Identifies the authoritative owner for Blob fetch at perception time.
- Produces an implementation plan that preserves current display image delivery and history text-only behavior.

## Subproblems
- none

## Results
- R569

## Latest Check
C605

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P585/README.md
- Ticket T575: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P585/tickets/T575.md
- Result R569: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P585/results/R569.md
- Check C605: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P580/children/P584/children/P585/checks/C605.md

## Follow-ups
- none
