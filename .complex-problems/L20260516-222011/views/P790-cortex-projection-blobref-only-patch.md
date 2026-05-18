# P790: Cortex Projection BlobRef-Only Patch

Status: done
Parent: P788
Root: P000
Source Ticket: T778 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/children/P790
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/children/P790/README.md
Ticket(s): T780

## Problem
Patch the projection behavior based on the inspection child so raw inline media/base64/data URLs are not preserved in LLM context while BlobRef/display manifest behavior remains intact.

## Success Criteria
- Unsafe inline media is scrubbed, summarized, or rejected in projected tool content.
- BlobRef and manifest-style display outputs remain available.
- Focused tests pass.
- Targeted scans confirm no active projection path emits raw image base64/data URLs.

## Subproblems
- none

## Results
- R770

## Latest Check
C816

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/children/P790/README.md
- Ticket T780: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/children/P790/tickets/T780.md
- Result R770: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/children/P790/results/R770.md
- Check C816: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P783/children/P788/children/P790/checks/C816.md

## Follow-ups
- none
