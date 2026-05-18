# P754: App resource and generated asset semantic residue discovery

Status: done
Parent: P749
Root: P000
Source Ticket: T743 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/README.md
Ticket(s): T758

## Problem
Audit app resource copies and generated assets for semantic residue while distinguishing source-of-truth files from synchronized generated copies.

## Success Criteria
- Scans cover `novaic-app` resource and generated asset locations relevant to VMuse, Device, display, and shell tooling.
- Findings distinguish generated copies from source-of-truth code and docs.
- Required sync/remediation candidates are listed for the remediation child.
- No generated assets are manually patched in this discovery child.

## Subproblems
- P767: App VMuse copied resource sync discovery
- P768: App Tauri backend and VmControl wiring discovery
- P769: App frontend and Monitor output contract discovery

## Results
- R765

## Latest Check
C811

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/README.md
- Ticket T758: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/tickets/T758.md
- Result R765: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/results/R765.md
- Check C811: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/checks/C811.md

## Follow-ups
- none
