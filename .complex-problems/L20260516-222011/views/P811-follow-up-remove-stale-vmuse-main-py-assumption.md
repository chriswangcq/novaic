# P811: Follow-up: remove stale VMuse main.py assumption from app sync script

Status: done
Parent: P785
Root: P000
Source Ticket: none (none)
Source Check: C842
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P811
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P811/README.md
Ticket(s): T803

## Problem
`novaic-app/scripts/sync-vmuse-resource.sh` still validates the source VMuse repo by checking for `src/novaic_mcp_vmuse/main.py`. The cleaned VMuse package removed that FastMCP-style entrypoint, so the script now encodes an obsolete contract and can block or mislead future app resource/generated synchronization.

## Success Criteria
- `rg -n "src/novaic_mcp_vmuse/main\\.py|main\\.py" novaic-app/scripts/sync-vmuse-resource.sh` returns no stale validation hit.
- The sync script validates a current source file such as `src/novaic_mcp_vmuse/http_server.py` or another explicit HTTP contract marker.
- Running `novaic-app/scripts/sync-vmuse-resource.sh` succeeds, or an explicit equivalent check proves the same path if running it would cause unrelated generated churn.
- Resource and generated VMuse copies remain synchronized with each other after the fix.
- Focused stale marker scans for FastMCP/SSE/stdio/direct-media residue remain clean outside intentional contract tests.

## Subproblems
- none

## Results
- R795

## Latest Check
C843

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P811/README.md
- Ticket T803: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P811/tickets/T803.md
- Result R795: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P811/results/R795.md
- Check C843: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P785/children/P811/checks/C843.md

## Follow-ups
- none
