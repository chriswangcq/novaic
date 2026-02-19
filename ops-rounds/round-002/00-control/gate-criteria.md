# Round 002 Gate Criteria

## Gate A - Build and Test
- Each team-owned component must pass targeted `lint/test/build`.
- Evidence must include command list and pass summary.

## Gate B - Contract and Interface
- API Team publishes env var spec and API surface inventory.
- Platform Team updates contract baseline and compatibility matrix.
- Cross-team caller/callee contract changes are documented.

## Gate C - Operability
- Runtime startup healthcheck issue resolved and verified.
- Desktop team delivers RC installer + clean-machine startup report.
- Storage-A/B provide runnable backup/restore script and one validation run.

## Gate D - Reliability
- Agent Runtime provides cross-process or persisted idempotency strategy evidence.
- Tools Team provides concurrency/timeout behavior under load evidence.

## Fail Conditions
- Any open P0 finding
- Missing evidence for claimed completion
- Critical deliverable marked done but not reproducible from files
