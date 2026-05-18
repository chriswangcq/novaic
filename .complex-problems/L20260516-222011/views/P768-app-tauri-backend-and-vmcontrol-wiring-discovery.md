# P768: App Tauri backend and VmControl wiring discovery

Status: done
Parent: P754
Root: P000
Source Ticket: T758 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/README.md
Ticket(s): T760

## Problem
Discover whether `novaic-app/src-tauri` Rust/backend scripts and VmControl setup/startup paths still point at stale VMuse/Sandbox/Blob/LogicalFS entrypoints or imply outdated device/display/shell ownership. This belongs under P754 because app backend wiring decides what shipped resources actually run.

## Success Criteria
- Relevant Tauri Rust, setup, backend startup, and resource wiring files are discovered with bounded commands.
- Suspicious hits around `http_server`, FastMCP, VMuse, devicectl, display, screenshot, Blob, Sandbox, and LogicalFS are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Tauri/app wiring files are modified in this discovery child.

## Subproblems
- P770: App Tauri Rust VmControl route wiring discovery
- P771: App backend script and launch wiring discovery
- P772: App resource packaging and generated asset wiring discovery

## Results
- R754

## Latest Check
C800

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/README.md
- Ticket T760: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/tickets/T760.md
- Result R754: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/results/R754.md
- Check C800: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/checks/C800.md

## Follow-ups
- none
