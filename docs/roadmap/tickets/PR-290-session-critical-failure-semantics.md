# PR-290 — Session Critical Failure Semantics

Status: Closed

## Goal

Remove soft-failure fallbacks that make the harness look successful while
durable session state, inbox, or outbox writes failed.

## Scope

- Identify `return []`, `return 1`, broad `except Exception`, and swallowed
  ledger errors on critical paths.
- Convert critical persistence failures to explicit exceptions or failed
  delivery contracts.
- Keep non-critical observability failures separated from state correctness.

## Dependencies

- PR-289 thin coordinator helps isolate critical boundaries.

## Risks

- Tightening failure semantics can expose flaky tests or hidden production
  assumptions.
- Need to preserve idempotent retries.

## Acceptance Criteria

- Critical input/event/outbox writes do not silently succeed on exception.
- Tests cover persistence failure for dispatch and finalize paths.
- Non-critical logging/trace failures remain non-blocking only if documented.

## Verification

- Targeted failure injection tests.
- Grep review for swallowed exceptions in session harness modules.

## Closure Notes

- Split because critical failure semantics spans multiple boundaries:
  - PR-290A: transition ledger writes hard-fail.
  - PR-290B: input query/consumption fallbacks.
  - PR-290C: generation fallback semantics.
  - PR-290D: pending projection observability failures.
- All child tickets are now closed. Critical authoritative paths now propagate
  failures; pending projection is explicitly documented as non-critical derived
  observability.
