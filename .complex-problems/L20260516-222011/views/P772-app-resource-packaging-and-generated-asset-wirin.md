# P772: App resource packaging and generated asset wiring discovery

Status: done
Parent: P768
Root: P000
Source Ticket: T760 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P772
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P772/README.md
Ticket(s): T763

## Problem
Discover whether app resource packaging/generation wiring copies, references, or ships stale VMuse/Sandbox/Blob/LogicalFS resource paths in ways that could preserve old behavior after source cleanup. This belongs under P768 because resource packaging decides what runtime bits reach the app bundle.

## Success Criteria
- Relevant resource copy, generated asset, and packaging wiring files are discovered with bounded commands.
- Hits for copied VMuse resources, FastMCP entrypoints, http server entrypoints, Blob, Sandbox, LogicalFS, display, and screenshot are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No resource/package wiring files are modified in this discovery child.

## Subproblems
- none

## Results
- R753

## Latest Check
C799

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P772/README.md
- Ticket T763: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P772/tickets/T763.md
- Result R753: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P772/results/R753.md
- Check C799: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P772/checks/C799.md

## Follow-ups
- none
