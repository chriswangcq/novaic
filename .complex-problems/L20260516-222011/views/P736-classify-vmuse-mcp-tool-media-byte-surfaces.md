# P736: Classify VMuse MCP tool media-byte surfaces

Status: done
Parent: P734
Root: P000
Source Ticket: T724 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/README.md
Ticket(s): T726

## Problem
Classify media/base64 output paths in the standalone `novaic-mcp-vmuse` MCP tool layer, especially `main.py`, `tools/desktop.py`, `tools/browser.py`, and any small missed imports such as `tools/windows.py`. We need to separate legitimate MCP image transport from shell/runtime history contract violations.

## Success Criteria
- Each MCP tool module with base64/image hits is inspected and classified with file pointers.
- Screenshot, aim screenshot, browser screenshot, and window/media-related base64 surfaces are classified by function or module.
- The result states whether the surfaces are standalone MCP/plugin behavior, active runtime shell behavior, or remediation candidates.
- Any dead or misleading imports are listed as cleanup candidates.

## Subproblems
- P738: Classify VMuse desktop screenshot MCP surfaces
- P739: Classify VMuse browser and window MCP media surfaces

## Results
- R718

## Latest Check
C762

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/README.md
- Ticket T726: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/tickets/T726.md
- Result R718: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/results/R718.md
- Check C762: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/checks/C762.md

## Follow-ups
- none
