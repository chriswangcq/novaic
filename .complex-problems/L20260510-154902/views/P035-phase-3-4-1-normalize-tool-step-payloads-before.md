# P035: Phase 3.4.1: Normalize tool step payloads before event emission

Status: done
Parent: P026
Root: P000
Package: problems/P000/children/P004/children/P026/children/P035
Body: problems/P000/children/P004/children/P026/children/P035/README.md
Ticket(s): T031

## Problem
`Workspace.write_step` currently mutates incoming step dictionaries by externalizing inline payloads and replacing `payload_ref`. Event emission needs the final normalized step data before writing `ToolStepRecorded`.

## Success Criteria
- A reusable normalization path produces final step data without hiding mutation inside legacy write-only code.
- Payload-bearing steps expose final `payload_ref` before event append.
- Existing validation rules for tool steps remain intact.
- Focused tests cover payload and non-payload steps.

## Subproblems
- none

## Results
- R028

## Latest Check
C030

## Bodies
- Problem: problems/P000/children/P004/children/P026/children/P035/README.md
- Ticket T031: problems/P000/children/P004/children/P026/children/P035/tickets/T031.md
- Result R028: problems/P000/children/P004/children/P026/children/P035/results/R028.md
- Check C030: problems/P000/children/P004/children/P026/children/P035/checks/C030.md

## Follow-ups
- none
