# Cortex Archive Diagnostics Persistence Parent Result

## Summary

P373 completed through child problems P375-P377. Cortex now persists explicit runtime archive diagnostics in `WakeArchived` context events as nested `archive_diagnostics`, while preserving the existing top-level semantic `remaining_stack` list for context projection.

## Child Results

- P375/R355/C378 mapped the persistence source path and identified the safe nested diagnostics shape.
- P376/R356/C379 implemented nested `archive_diagnostics` persistence and focused Cortex tests.
- P377/R357/C380 verified runtime/Cortex aggregate behavior and residue scans.

## Final State

- Runtime diagnostic fields reach Cortex from active and recovery archive paths.
- Cortex request validation rejects incomplete or invalid diagnostic requests.
- Cortex context events persist explicit `session_generation`, `finalize_reason`, diagnostic `remaining_stack`, and `round_num` when diagnostics are supplied.
- Pure structural Cortex scope-end callers remain valid without hidden active-generation inference.

## Verification

- Runtime focused suite: 61 passed.
- Cortex focused suite: 80 passed.
- Source scans found no active-generation synthesis in Cortex archive diagnostics and confirmed diagnostic stack data is nested under `archive_diagnostics`.

## Residual Note

No follow-up is needed for P373. Aggregate P368 verification remains in sibling P374.
