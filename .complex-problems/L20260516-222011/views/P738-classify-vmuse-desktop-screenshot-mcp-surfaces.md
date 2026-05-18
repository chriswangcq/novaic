# P738: Classify VMuse desktop screenshot MCP surfaces

Status: done
Parent: P736
Root: P000
Source Ticket: T726 (split)
Source Check: none
Package: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/children/P738
Body: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/children/P738/README.md
Ticket(s): T727

## Problem
Classify the VMuse desktop screenshot and aim screenshot path across `novaic-mcp-vmuse/src/novaic_mcp_vmuse/main.py` and `tools/desktop.py`. These paths base64-encode screenshots and convert them to FastMCP image content, and need a clear boundary status.

## Success Criteria
- `main.py` desktop screenshot and mouse aim wrappers are inspected with file/function pointers.
- `tools/desktop.py` screenshot and aim result construction are inspected with file/function pointers.
- The result states whether these are standalone MCP image transport, current shell/runtime behavior, or remediation candidates.
- Dead or misleading comments/imports found in this path are listed.

## Subproblems
- none

## Results
- R716

## Latest Check
C760

## Bodies
- Problem: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/children/P738/README.md
- Ticket T727: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/children/P738/tickets/T727.md
- Result R716: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/children/P738/results/R716.md
- Check C760: problems/P000/children/P007/children/P668/children/P673/children/P684/children/P697/children/P708/children/P722/children/P728/children/P732/children/P734/children/P736/children/P738/checks/C760.md

## Follow-ups
- none
