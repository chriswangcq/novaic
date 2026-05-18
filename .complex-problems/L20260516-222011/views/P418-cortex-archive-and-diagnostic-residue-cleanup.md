# P418: Cortex archive and diagnostic residue cleanup

Status: done
Parent: P404
Root: P000
Source Ticket: T405 (split)
Source Check: none
Package: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418
Body: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/README.md
Ticket(s): T418

## Problem
Cortex archive, summary, diagnostic, and projection paths may contain generation/active-state residue that is safe as audit metadata but dangerous if used as live authority.

## Success Criteria
- Inspect archive, summary, diagnostic, and projection hits from the Cortex inventory.
- Remove any live compatibility fallback that reintroduces active-state authority.
- Explicitly classify safe diagnostic/projection/counter fields.
- Add or update tests if archive/diagnostic behavior changes.
- Confirm historical docs or archived summaries are not mistaken for live runtime code.

## Subproblems
- P431: Problem: Cortex archive/direct diagnostics inventory
- P432: Problem: Cortex direct scope-end contract cleanup
- P433: Problem: Cortex archive projection cleanup

## Results
- R415

## Latest Check
C441

## Bodies
- Problem: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/README.md
- Ticket T418: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/tickets/T418.md
- Result R415: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/results/R415.md
- Check C441: problems/P000/children/P004/children/P278/children/P283/children/P329/children/P404/children/P418/checks/C441.md

## Follow-ups
- none
