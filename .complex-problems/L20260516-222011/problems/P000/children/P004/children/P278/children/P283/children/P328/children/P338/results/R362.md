# Remaining Stack And Finalize Reason Archive Boundary Parent Result

## Summary

P338 completed through child problems P366-P369. Finalize/session-ended diagnostics now bind `finalize_reason`, `remaining_stack`, and generation to explicit scope/session identity across session finalize, wake-finalize saga payloads, runtime archive handling, recovery archive, and Cortex archive persistence.

## Child Results

- P366/R350/C372 mapped the initial finalize diagnostics boundary.
- P367/R351/C375 audited stale finalize behavior and, through P370/R352/C374, hardened missing assertions.
- P368/R360/C383 fixed Cortex archive diagnostics binding and persistence.
- P369/R361/C384 aggregate-verified finalize diagnostics and fixed repo-level bool-generation coercion.

## Final State

- `SessionRepository.session_ended(...)` requires explicit `finalize_reason`, positive generation, and object-shaped `remaining_stack`.
- Stale finalize attempts are rejected without recording `session_finalized`.
- `wake_finalize` carries explicit diagnostics to both `session.ended` and `cortex.scope_end`.
- Recovery archive outbox requires positive generation and `remaining_stack`.
- Cortex persists valid archive diagnostics under nested `archive_diagnostics`.

## Verification

- Runtime focused finalize/recovery/compensation suite: 57 passed.
- Runtime wider scope-end suite: 61 passed.
- Cortex archive/context suite: 80 passed in P374 and 55 passed in P369 final verification subset.
- Residue scans checked `remaining_stack`, `finalize_reason`, `ended_at`, generation defaults, and active lookup around finalize/archive paths.

## Residual Note

No follow-up is needed for P338.
