# P071: App business MCP adapter fallback compatibility residue scan

Status: done
Parent: P066
Root: P000
Source Ticket: T060 (split)
Source Check: none
Package: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071
Body: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/README.md
Ticket(s): T064

## Problem
App, business, and MCP adapter code may still preserve old direct-tool, fallback, or compatibility branches that are no longer part of the current shell/CLI-facing architecture.

## Success Criteria
- Focused scans cover `novaic-app`, `novaic-business`, `novaic-mcp-vmuse`, and scripts for fallback, compat, legacy, migration, TODO/FIXME, pass, skip, and direct-tool residue.
- Hits are classified as active risk, intentional UI/test compatibility, benign adapter, or stale residue.
- Safe tiny cleanup is applied directly if discovered.
- Touched areas receive focused tests/lint or explicit no-code-change verification.

## Subproblems
- P073: App monitor UI fallback compatibility residue scan
- P074: Business dispatch adapter residue scan
- P075: MCP scripts shell adapter residue scan

## Results
- R071

## Latest Check
C084

## Bodies
- Problem: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/README.md
- Ticket T064: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/tickets/T064.md
- Result R071: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/results/R071.md
- Check C084: problems/P000/children/P001/children/P009/children/P017/children/P066/children/P071/checks/C084.md

## Follow-ups
- none
