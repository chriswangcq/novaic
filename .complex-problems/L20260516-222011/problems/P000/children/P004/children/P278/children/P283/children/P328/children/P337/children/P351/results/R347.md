# T348 Result: Recovery Compensation Finalize Identity

## Child Problems Closed

- P361: Recovery compensation finalize source map.
- P362: Compensation wake_finalize generation preservation.
- P363: Session recovery missing identity handling.
- P364: Recovery compensation finalize aggregate verification.
  - P364 initially found a startup rebuild identity fallback.
  - Follow-up P365 removed the fallback and closed successfully.

## Implemented Outcome

- Wake saga failure compensation now creates `wake_finalize` only when the failed saga context carries positive explicit `session_generation`.
- Missing, zero, boolean, non-numeric, and non-positive generation values no longer synthesize finalize mutation work.
- Recovery archive scope-end work now requires positive generation from the suspected-dead event path.
- Recovery archive publisher rejects invalid generation before publishing `CORTEX_SCOPE_END`.
- Startup rebuild no longer fabricates generation `1` for running saga contexts with missing generation.
- Stale attach-flow tests were updated to reflect the current outbox-recording path and assert the old direct publish naming is absent.

## Verification

- Compensation/recovery focused tests passed during P362 and P363.
- P364 aggregate verification passed after P365 closure.
- Final aggregate suite after P365: `96 passed in 0.71s`.
- Residue searches no longer find production startup rebuild generation defaulting or old attach publish implementation naming.

## Gap

No P351-scoped gap remains.
