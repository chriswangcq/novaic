# P607: Frontend Detail Modal and Raw JSON Boundary

Status: done
Parent: P604
Root: P000
Source Ticket: T597 (split)
Source Check: none
Package: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P607
Body: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P607/README.md
Ticket(s): T600

## Problem
Audit the Agent Monitor detail/modal/raw JSON surfaces to distinguish intentional raw inspection views from normal timeline previews, and ensure raw/detail rendering is escaped, bounded, and not confused with LLM request context.

## Success Criteria
- Records exact scans for detail modal, raw JSON tab, request/response body rendering, and bounds.
- Cites frontend slices showing HTML escaping, JSON stringification boundaries, or size limits.
- Separates inspect/debug raw views from normal user-facing timeline preview behavior.
- Creates a follow-up if raw/detail views can inject unescaped HTML or unbounded raw image/base64 text.

## Subproblems
- none

## Results
- R592

## Latest Check
C632

## Bodies
- Problem: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P607/README.md
- Ticket T600: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P607/tickets/T600.md
- Result R592: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P607/results/R592.md
- Check C632: problems/P000/children/P005/children/P553/children/P564/children/P575/children/P583/children/P601/children/P604/children/P607/checks/C632.md

## Follow-ups
- none
