# P022 success check

## Result IDs

- R018

## Evidence

- R018 extends the projector snapshot with stream watermark fields.
- Focused tests pass: `68 passed in 0.12s`.
- Full Cortex suite passes: `423 passed in 0.70s`.
- Static scan found no forbidden projector dependency patterns.

## Criteria Map

- Snapshot exposes `stream_id`, `root_scope_id`, `first_seq`, and `applied_seq`: satisfied.
- Ordered contiguous replay succeeds: satisfied by existing projection tests and updated basic watermark test.
- Empty replay still returns an empty deterministic snapshot: satisfied by updated empty snapshot test.
- Mixed stream id, duplicate seq, seq gaps, and out-of-order seq fail with `ContextEventProjectionError`: satisfied by new tests.
- Focused ContextEvent tests pass: satisfied by `68 passed`.

## Execution Map

- T019 produced R018.
- R018 changed only the pure projector and its tests.
- No endpoint/read-path integration occurred.

## Stress Test

- The new tests cover valid replay plus invalid first seq, mixed stream, duplicate seq, gap, and out-of-order replay.
- Full Cortex suite confirms the new snapshot shape does not regress existing code.

## Residual Risk

- None for the replay watermark contract.
- Live read-path cutover remains intentionally open in Phase 4.

## Verdict

Success. R018 closes P022.
