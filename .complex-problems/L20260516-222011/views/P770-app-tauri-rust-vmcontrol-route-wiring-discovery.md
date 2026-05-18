# P770: App Tauri Rust VmControl route wiring discovery

Status: done
Parent: P768
Root: P000
Source Ticket: T760 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P770
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P770/README.md
Ticket(s): T761

## Problem
Discover whether `novaic-app/src-tauri` Rust VmControl/setup routes still start stale VMuse/FastMCP/direct-media entrypoints or imply outdated ownership for device/display/shell, Blob, Sandbox, or LogicalFS. This belongs under P768 because Rust routes decide which VM service and command paths the packaged app invokes.

## Success Criteria
- Relevant Rust route/setup files under `novaic-app/src-tauri` are discovered with bounded commands.
- Hits for `http_server`, FastMCP, VMuse, devicectl, display, screenshot, Blob, Sandbox, LogicalFS, shell, and artifact are classified.
- Exact remediation candidates are listed, or absence is explicitly recorded.
- No Rust/Tauri files are modified in this discovery child.

## Subproblems
- none

## Results
- R751

## Latest Check
C797

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P770/README.md
- Ticket T761: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P770/tickets/T761.md
- Result R751: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P770/results/R751.md
- Check C797: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P749/children/P754/children/P768/children/P770/checks/C797.md

## Follow-ups
- none
