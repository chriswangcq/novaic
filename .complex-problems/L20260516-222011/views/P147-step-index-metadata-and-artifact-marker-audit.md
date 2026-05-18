# P147: step index metadata and artifact marker audit

Status: done
Parent: P142
Root: P000
Source Ticket: T129 (split)
Source Check: none
Package: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P147
Body: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P147/README.md
Ticket(s): T132

## Problem
`steps/_index.jsonl` is the compact navigation layer for step history. It must contain enough metadata to reconstruct and inspect tool activity without opening large step payloads: `step_ref`, `payload_ref`, tool/status/duration fields, and a marker for artifact-bearing observations.

This child belongs under `P142` because an incomplete index forces future agents to load full step files or raw payloads, undoing the pointer-oriented contract.

## Success Criteria
- Source pointers map `write_step` index row construction and `read_step_index`.
- Evidence proves index rows include stable `step_ref` and `payload_ref`.
- Evidence proves index rows include tool/status and duration metadata when available.
- Evidence proves artifact-bearing observations are marked compactly in the index.
- Any silent-corruption behavior in index reading is either justified or fixed.

## Subproblems
- none

## Results
- R127

## Latest Check
C141

## Bodies
- Problem: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P147/README.md
- Ticket T132: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P147/tickets/T132.md
- Result R127: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P147/results/R127.md
- Check C141: problems/P000/children/P003/children/P126/children/P134/children/P142/children/P147/checks/C141.md

## Follow-ups
- none
