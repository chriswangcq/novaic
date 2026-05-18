# step index metadata and artifact marker audit

## Problem

`steps/_index.jsonl` is the compact navigation layer for step history. It must contain enough metadata to reconstruct and inspect tool activity without opening large step payloads: `step_ref`, `payload_ref`, tool/status/duration fields, and a marker for artifact-bearing observations.

This child belongs under `P142` because an incomplete index forces future agents to load full step files or raw payloads, undoing the pointer-oriented contract.

## Success Criteria

- Source pointers map `write_step` index row construction and `read_step_index`.
- Evidence proves index rows include stable `step_ref` and `payload_ref`.
- Evidence proves index rows include tool/status and duration metadata when available.
- Evidence proves artifact-bearing observations are marked compactly in the index.
- Any silent-corruption behavior in index reading is either justified or fixed.
