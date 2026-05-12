# Log storm suppression check

## Summary

The code-level log storm suppression problem is solved locally. Deployment verification remains in the deploy child problem.

## Evidence

- `install_service_logging()` now calls `quiet_noisy_dependency_loggers()`.
- Hot claim success paths are suppressed by `should_log_internal_access()`.
- Failed claim statuses still return true for logging.
- Targeted common tests passed.

## Criteria Map

- Dependency loggers warning-level: met by test assertions for `httpx`, `httpcore`, and `uvicorn.access`.
- Successful claim logs suppressed: met by test assertions for task/saga claim status 200/204.
- Failed claim logs preserved: met by test assertions for status 500/429.
- Tests cover behavior: met by `21 passed`.

## Execution Map

- Changes are in shared logging infrastructure and middleware, not worker business logic.

## Stress Test

- The exact hot paths seen in production logs are covered: `/api/queue/tasks/claim` and `/api/queue/sagas/claim`.

## Residual Risk

- Other high-frequency Cortex object reads may still be verbose in service-specific logs if they are not dependency access logs; production log inspection after deploy will catch this.

## Result IDs

- R002
