# P771: App backend script and launch wiring discovery

Status: done
Parent: P768
Root: P000
Source Ticket: T760 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P771
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P771/README.md
Ticket(s): T762

## Problem
Discover whether app backend launch scripts, packaging scripts, and development orchestration still launch stale VMuse/FastMCP/direct-media entrypoints or bypass the intended shell/blob/display contract. This belongs under P768 because scripts can override otherwise-clean Rust route wiring.

## Success Criteria
- Relevant scripts under `novaic-app/scripts`, app package scripts, and Tauri backend launch helpers are discovered with bounded commands.
- Hits for VMuse, FastMCP, http server, devicectl, display, screenshot, Blob, Sandbox, LogicalFS, shell, and artifact are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No script/package files are modified in this discovery child.

## Subproblems
- none

## Results
- R752

## Latest Check
C798

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P771/README.md
- Ticket T762: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P771/tickets/T762.md
- Result R752: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P771/results/R752.md
- Check C798: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P771/checks/C798.md

## Follow-ups
- none
