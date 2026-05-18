# P749: Cross-service semantic residue discovery and classification

Status: done
Parent: P709
Root: P000
Source Ticket: T742 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/README.md
Ticket(s): T743

## Problem
Find and classify remaining semantic residue across docs, scripts, app resources, generated assets, and service code. The goal is evidence, not patching: identify which references are active and misleading, generated copies, historical docs, intentional lower-level protocols, or harmless tests.

## Success Criteria
- Targeted scans cover service-boundary terms for Cortex, Gateway, Business, Device/devicectl, Queue, Runtime, Blob, LogicalFS, Sandboxd, shell, display, and VMuse/VmControl.
- Findings are grouped by file/surface and classified as active, stale, generated, historical, lower-level protocol, or test/fixture.
- Exact remediation candidates are listed for the next child problem.
- Broad risky areas are called out instead of silently accepted.

## Subproblems
- P752: Active docs and scripts semantic residue discovery
- P753: Service code semantic residue discovery
- P754: App resource and generated asset semantic residue discovery

## Results
- R766

## Latest Check
C812

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/README.md
- Ticket T743: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/tickets/T743.md
- Result R766: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/results/R766.md
- Check C812: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/checks/C812.md

## Follow-ups
- none
