# P032: Phase 3C3 Skill Begin Parent Selection SQLite Cutover

Status: done
Parent: P019
Root: P000
Package: problems/P000/children/P004/children/P019/children/P032
Body: problems/P000/children/P004/children/P019/children/P032/README.md
Ticket(s): T028

## Problem
`skill_begin` still chooses the parent scope by resolving the active path from file-walk state. It must choose the parent/top scope from SQLite active-stack projection so new child scopes attach under the operational control-plane authority.

## Success Criteria
- Successful `skill_begin` determines parent path from SQLite active-stack projection.
- Empty projection attaches the first child under the root path.
- Non-empty projection attaches the child under the top frame `scope_path`.
- Error branches preserve existing response shape.
- Tests prove begin parent selection still works after constructing a fresh Workspace/registry against the same operational SQLite database.

## Subproblems
- none

## Results
- R025

## Latest Check
C027

## Bodies
- Problem: problems/P000/children/P004/children/P019/children/P032/README.md
- Ticket T028: problems/P000/children/P004/children/P019/children/P032/tickets/T028.md
- Result R025: problems/P000/children/P004/children/P019/children/P032/results/R025.md
- Check C027: problems/P000/children/P004/children/P019/children/P032/checks/C027.md

## Follow-ups
- none
