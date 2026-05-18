# Runtime attach active generation validation

## Problem

`novaic-agent-runtime/queue_service/session_repo.py` still coerces active session generation with `int(current_active.get("generation") or 0)` in the attach path. That can silently turn malformed or missing active state into generation `0`.

## Success Criteria

- Runtime attach active session generation uses the existing positive generation validator.
- Focused runtime tests still pass for attach/finalize/session state behavior.
- Source guard no longer reports this raw attach-path coercion.
- This belongs under P385 because it closes the runtime half of the residual live generation coercion list.
