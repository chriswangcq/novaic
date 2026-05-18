# P697: Semantic, app, and device service boundary classification

Status: done
Parent: P684
Root: P000
Source Ticket: T689 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/README.md
Ticket(s): T698

## Problem
Classify Cortex, Gateway, Business, Device, and related wrappers as semantic/app/device-facing services. Verify their entrypoints, launch surfaces, and dependency boundaries relative to Queue/Runtime and the foundational Blob/LogicalFS/Sandbox services.

## Success Criteria
- Cortex, Gateway, Business, Device, and wrappers each have role, entrypoint, and dependency-boundary evidence.
- Cortex is checked specifically as a semantic state/context service, not a long-term owner of file/sandbox infrastructure.
- Gateway/Business/Device launch and wrapper roles are separated from queue/runtime worker roles.
- Any stale or misleading claims found during classification are patched or recorded.

## Subproblems
- P705: Cortex semantic state/context boundary classification
- P706: Gateway and app edge service boundary classification
- P707: Business service and subscriber boundary classification
- P708: Device/devicectl and artifact-display boundary classification
- P709: Semantic/app/device service residue cleanup and verification

## Results
- R808

## Latest Check
C857

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/README.md
- Ticket T698: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/tickets/T698.md
- Result R808: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/results/R808.md
- Check C857: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/checks/C857.md

## Follow-ups
- none
