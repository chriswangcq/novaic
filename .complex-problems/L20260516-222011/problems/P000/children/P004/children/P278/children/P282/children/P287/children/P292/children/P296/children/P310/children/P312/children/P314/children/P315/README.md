# Remove stale attach task_id assumption

## Problem

`SessionRepository.dispatch()` still logs `result["task_id"]` after attach dispatch. The attach worker-only cutover intentionally returns an outbox-pending result with `outbox_id`, so this stale assumption crashes dispatch before the result can be returned.

## Success Criteria

- Attach dispatch logging no longer reads `result["task_id"]`.
- The log line reports durable worker-owned delivery information such as `outbox_id` and `delivery`.
- The active attach result still returns `delivery=outbox_pending`, `outbox_id`, `saga_id`, and `scope_id`.
- No eager attach publish path is reintroduced.
