# P352 Check: Runtime Finalize Enforcement Aggregate Verification

## Verdict

`success`

## Criteria Map

- Focused tests across react contracts, cortex handlers, session-ended delivery, repository finalize, recovery/compensation, and pending restart: satisfied with `170 passed`.
- Source guards for `session_generation or 0` in finalize-producing runtime paths: satisfied after inspection and P365 cleanup.
- Residual risks and follow-ups recorded if mutation path remains partially guarded: satisfied; no remaining P352-scoped mutation gap found.

## Evidence

- Compile succeeded for the relevant runtime/queue identity modules.
- Focused aggregate suite passed: `170 passed in 0.95s`.
- Direct `wake_finalize` and `CORTEX_SCOPE_END` paths require positive generation before mutation.
- React contract defaults to zero were already removed and covered by tests.
- Recovery/compensation and startup rebuild generation fallbacks were fixed under P351/P365.
- Remaining `generation or 0` hits are reject-path metadata or runtime-state sentinel reads, not finalize-producing identity synthesis.

## Stress Test

The check intentionally included indirect paths:

- React finalize trigger builders.
- Wake finalize payload builders.
- Cortex scope-end archive handler.
- Session-ended handler/client/route/repository finalize.
- Recovery archive and compensation outbox.
- Pending inbox restart/attach boundaries.
- Startup rebuild projector and stale test residue guards.

## Residual Risk

No known P352-scoped residual risk remains.
