# P142: Workspace tool step normalization and index map

Status: done
Parent: P134
Root: P000
Source Ticket: T127 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/README.md
Ticket(s): T129

## Problem
Tool steps are materialized in `steps/*.json` and indexed in `steps/_index.jsonl`. This path must reject inline raw results, externalize raw payloads, preserve stable step refs, and expose compact index metadata.

## Success Criteria
- `normalize_step`, `write_step`, and `write_step_projection` are mapped with source pointers.
- Tool steps are verified to reject inline `result` and require an observation percept.
- Raw `payload` writes are verified to require `payload_ref`, externalize if needed, and mirror actual `payload_ref` into observation.
- Step index entries are verified to include `step_ref`, `payload_ref`, duration/tool/status, and artifact marker where applicable.

## Subproblems
- P145: normalize_step observation contract audit
- P146: write_step payload_ref mirroring audit
- P147: step index metadata and artifact marker audit
- P148: write_step_projection call-site boundary audit

## Results
- R132

## Latest Check
C146

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/README.md
- Ticket T129: problems/P000/children/P003/children/P126/children/P134/children/P142/tickets/T129.md
- Result R132: problems/P000/children/P003/children/P126/children/P134/children/P142/results/R132.md
- Check C146: problems/P000/children/P003/children/P126/children/P134/children/P142/checks/C146.md

## Follow-ups
- none
