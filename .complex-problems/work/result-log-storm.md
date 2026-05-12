# Log storm suppression result

## Summary

Implemented path-specific and dependency-level logging suppression for high-frequency successful worker polling.

## Done

- Added `quiet_noisy_dependency_loggers()` in service logging bootstrap.
- Set `httpx`, `httpcore`, and `uvicorn.access` to warning level during `install_service_logging()`.
- Added `should_log_internal_access()` to suppress successful `/api/queue/tasks/claim` and `/api/queue/sagas/claim` access logs.
- Kept failed claim requests visible.
- Added regression tests for dependency logger levels and hot-path access suppression.

## Verification

- Ran `PYTHONPATH=. pytest -q tests/test_log_context.py tests/test_caller_middleware.py`.
- Result: `21 passed in 0.27s`.

## Known Gaps

- Production verification still needs to happen after deployment.

## Artifacts

- `novaic-common/common/log_context.py`
- `novaic-common/common/middlewares/caller_logging.py`
- `novaic-common/tests/test_log_context.py`
- `novaic-common/tests/test_caller_middleware.py`
