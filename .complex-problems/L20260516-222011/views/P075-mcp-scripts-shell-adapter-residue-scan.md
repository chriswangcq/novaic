# P075: MCP scripts shell adapter residue scan

Status: done
Parent: P071
Root: P000
Source Ticket: T064 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/README.md
Ticket(s): T073

## Problem
MCP adapter and scripts may still expose old direct tool names, fallback shell behavior, base64 media text, or stale compatibility comments after the shell/blob/display contract change.

## Success Criteria
- Focused scans cover `novaic-mcp-vmuse` and relevant top-level scripts for legacy, fallback, compat, migration, TODO/FIXME, direct tool names, base64, and blob/display terms.
- Hits are classified as active adapter path, test fixture, intentional guard, or stale residue.
- Safe tiny cleanup is applied directly if found.
- Focused MCP/script checks pass or no-code-change verification is explicit.

## Subproblems
- P082: Scan and clean MCP/VMuse adapter residue
- P083: Scan and clean Cortex shell CLI adapter residue
- P084: Run final MCP/script shell-adapter scan and focused tests

## Results
- R070

## Latest Check
C083

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/README.md
- Ticket T073: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/tickets/T073.md
- Result R070: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/results/R070.md
- Check C083: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/children/P075/checks/C083.md

## Follow-ups
- none
