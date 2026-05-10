# Phase 3.6 legacy source write cleanup result

## Summary

Phase 3.6 completed. Legacy source-like write paths were demoted to projection-named materialization, runtime direct lifecycle bypasses were removed, a consolidated event authority test was added, and remaining legacy filesystem writes were statically audited/classified.

## Done

- P042/R037 routed active event-wired API endpoints through projection-named Workspace methods.
- P043/R046 removed runtime direct structural lifecycle helpers and migrated tests.
- P044/R047 added the consolidated Phase 3 write-path authority test.
- P045/R048 audited remaining legacy filesystem writes and deleted unused `Workspace.write_context`.

## Verification

- Active API generic write scan returned no matches.
- Runtime lifecycle bypass scan found no runtime helper definitions/call sites.
- Authority test passed and uses `ContextEventStore` as evidence.
- Full Cortex suite passed after the final cleanup: `446 passed in 0.84s`.

## Known Gaps

- None for Phase 3.6. Read-path cutover will decide when transitional projection files/methods can be physically deleted.

## Artifacts

- Child result: R037
- Child result: R046
- Child result: R047
- Child result: R048
