# P798: VMuse CLI and package metadata HTTP contract

Status: done
Parent: P795
Root: P000
Source Ticket: T786 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P798
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P798/README.md
Ticket(s): T789

## Problem
After deleting the FastMCP module, source CLI/package comments must point to the HTTP server contract and stop advertising FastMCP/SSE/stdio entry behavior.

## Success Criteria
- Source CLI `serve` delegates to `novaic_mcp_vmuse.http_server.main` or equivalent HTTP server entry.
- Source CLI/info/version output no longer mentions FastMCP, SSE, stdio, or `.main import mcp`.
- Source package comments no longer tell callers to import `mcp` from `.main`.
- Package metadata remains installable with the `novaic` console script.

## Subproblems
- none

## Results
- R778

## Latest Check
C825

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P798/README.md
- Ticket T789: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P798/tickets/T789.md
- Result R778: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P798/results/R778.md
- Check C825: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P709/children/P750/children/P784/children/P793/children/P795/children/P798/checks/C825.md

## Follow-ups
- none
