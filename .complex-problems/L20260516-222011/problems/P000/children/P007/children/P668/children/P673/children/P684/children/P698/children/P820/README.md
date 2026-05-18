# Queue service residual standalone entrypoint audit

## Problem

`novaic-agent-runtime/queue_service/main.py` is a standalone FastAPI app with `if __name__` block. All launch scripts use `main_novaic.py queue-service` instead. Determine if queue_service/main.py is needed for direct testing or is dead code.

## Success Criteria

- queue_service/main.py is classified as active (with rationale) or deleted.
- If deleted, no import or test references break.
- Relevant tests pass.
