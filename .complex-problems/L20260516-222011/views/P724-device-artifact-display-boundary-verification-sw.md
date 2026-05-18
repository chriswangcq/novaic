# P724: Device/artifact/display boundary verification sweep

Status: done
Parent: P708
Root: P000
Source Ticket: T713 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P724
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P724/README.md
Ticket(s): T739

## Problem
Run focused verification after Device/artifact/display remediation to prove the final contract holds. This belongs under P708 because screenshots and media paths are high-risk: a small wrong wrapper can reintroduce base64 in context or make display no-op.

## Success Criteria
- Focused scans cover device screenshot, base64, blob URI, display projection, shell output, and tool-output contract terms.
- Relevant tests/lints pass or blockers are recorded with evidence.
- Remaining hits are classified as current contract, test guard, historical archive, or follow-up.
- No active unexamined large-media text leak remains in the swept surfaces.

## Subproblems
- P747: Post-remediation media-boundary scan
- P748: Focused media-boundary test sweep

## Results
- R734

## Latest Check
C779

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P724/README.md
- Ticket T739: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P724/tickets/T739.md
- Result R734: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P724/results/R734.md
- Check C779: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P724/checks/C779.md

## Follow-ups
- none
