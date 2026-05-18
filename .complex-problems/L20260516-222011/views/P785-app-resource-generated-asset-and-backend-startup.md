# P785: App Resource Generated Asset And Backend Startup Remediation

Status: done
Parent: P750
Root: P000
Source Ticket: T774 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/README.md
Ticket(s): T791

## Problem
Synchronize app resource/generated copies and fix stale App backend startup/package graph residue without creating source/generated divergence.

## Success Criteria
- VMuse source cleanup is synchronized into `novaic-app/src-tauri/resources/novaic-mcp-vmuse` and generated Apple asset copies when those copies remain committed.
- `novaic-app/scripts/start-backends.sh`, packaged backend scripts, and generated backend scripts reflect the current service topology or are explicitly marked dev-only if that is the correct role.
- `PORT_CORTEX=19996` versus `vmcontrol` port naming conflict is resolved.
- Backend binary/resource expectations match the scripts.
- Stale HD tools screenshot-to-LLM comment in VmControl Rust code is updated.
- Focused script/config checks run for startup/package graph.

## Subproblems
- P800: App VMuse resource copy sync
- P801: App generated VMuse asset copy sync
- P802: App backend startup graph cleanup
- P803: VmControl HD screenshot contract comment cleanup
- P811: Follow-up: remove stale VMuse main.py assumption from app sync script

## Results
- R794

## Latest Check
C844

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/README.md
- Ticket T791: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/tickets/T791.md
- Result R794: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/results/R794.md
- Check C842: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/checks/C842.md
- Check C844: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/checks/C844.md

## Follow-ups
- P811: Follow-up: remove stale VMuse main.py assumption from app sync script
