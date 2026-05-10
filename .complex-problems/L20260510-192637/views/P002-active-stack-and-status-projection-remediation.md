# P002: Active Stack And Status Projection Remediation

Status: done
Parent: P000
Root: P000
Package: problems/P000/children/P002
Body: problems/P000/children/P002/README.md
Ticket(s): T002

## Problem
LLM context now reads ContextEvents, but active stack/status still walks materialized projection files such as `steps/_index.jsonl` and scope `meta.json`. This is acceptable as a projection, but not perfect if the target is a unified state model.

## Success Criteria
- Decide whether active stack/status should be an event-derived projection, SQLite projection, or Workspace projection.
- Define migration path from projection walking to the chosen model.
- Include compatibility removal and tests proving skill_begin/skill_end/finalize status derives from the new model.

## Subproblems
- none

## Results
- R001

## Latest Check
C001

## Bodies
- Problem: problems/P000/children/P002/README.md
- Ticket T002: problems/P000/children/P002/tickets/T002.md
- Result R001: problems/P000/children/P002/results/R001.md
- Check C001: problems/P000/children/P002/checks/C001.md

## Follow-ups
- none
