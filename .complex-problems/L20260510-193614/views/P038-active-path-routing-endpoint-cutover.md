# P038: Active Path Routing Endpoint Cutover

Status: done
Parent: P020
Root: P000
Package: problems/P000/children/P004/children/P020/children/P038
Body: problems/P000/children/P004/children/P020/children/P038/README.md
Ticket(s): T035

## Problem
Non-stack endpoints such as `scope_write_assistant` and `steps_write` still call `resolve_active_scope_path(...)` to route writes to the active child scope. Even if these calls are not LIFO decisions, they are live runtime routing decisions and can keep filesystem stack walking on hot paths.

This belongs under Phase 3D because active-path routing must have an explicit boundary: either use SQLite active-stack projection for live routing, or be documented as non-stack repair/debug behavior. The user does not want hidden compatibility branches.

## Success Criteria
- `scope_write_assistant` writes to `read_active_stack_projection(...).active_scope_path`, not `resolve_active_scope_path(...)`.
- `steps_write` writes tool steps to `read_active_stack_projection(...).active_scope_path`, not `resolve_active_scope_path(...)`.
- Returned `scope_path` and event `scope_id` behavior remain compatible for root-only and nested active skill sessions.
- Tests cover assistant write and step write targeting a nested active scope after reconstructing Workspace/registry state from operational SQLite.

## Subproblems
- none

## Results
- R032

## Latest Check
C034

## Bodies
- Problem: problems/P000/children/P004/children/P020/children/P038/README.md
- Ticket T035: problems/P000/children/P004/children/P020/children/P038/tickets/T035.md
- Result R032: problems/P000/children/P004/children/P020/children/P038/results/R032.md
- Check C034: problems/P000/children/P004/children/P020/children/P038/checks/C034.md

## Follow-ups
- none
