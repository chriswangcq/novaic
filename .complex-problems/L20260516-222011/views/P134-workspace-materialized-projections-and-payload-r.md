# P134: Workspace materialized projections and payload reference map

Status: done
Parent: P126
Root: P000
Source Ticket: T122 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134
Body: problems/P000/children/P003/children/P126/children/P134/README.md
Ticket(s): T127

## Problem
Workspace files such as `context.jsonl`, `steps/*.json`, `_index.jsonl`, and `payloads/*.json` are materialized observability and retrieval surfaces. Their authority relative to ContextEvents and LLM context must be verified.

## Success Criteria
- `workspace.py` context append, step write, index write, and payload write/read functions are mapped.
- Tool step write behavior is verified to require payload/payload_ref rather than inline raw result.
- `context.jsonl` and context projection write paths are classified as active source, debug projection, compatibility, or stale.
- Tests covering payload externalization, step indexes, and context writes are identified and run.
- Any stale or misleading materialized projection path is removed or split for cleanup.

## Subproblems
- P141: Workspace payload store and blob externalization map
- P142: Workspace tool step normalization and index map
- P143: Workspace context.jsonl projection map
- P144: Cortex API materialization call-site map

## Results
- R142

## Latest Check
C156

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/README.md
- Ticket T127: problems/P000/children/P003/children/P126/children/P134/tickets/T127.md
- Result R142: problems/P000/children/P003/children/P126/children/P134/results/R142.md
- Check C156: problems/P000/children/P003/children/P126/children/P134/checks/C156.md

## Follow-ups
- none
