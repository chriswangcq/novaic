# Deploy and production smoke result

## Summary

Deployed the repaired common, runtime, and business code to api.gradievo.com and ran a live IM dispatch smoke against agent `822af016-31a1-49bb-b529-9b8f539a0831`.

## Done

- Deployed all backend services with `./deploy services`; restart and fresh-smoke passed for Entangled, Gateway, Business, Device, Queue Service, Blob Service, Cortex, task workers, saga workers, session outbox, saga outbox, health, scheduler, and subscriber.
- Sent live smoke IM notification `18c14d716c0a` with marker `[smoke] dispatch repair verification v4 2026-05-08T11:18:07Z`.
- Verified Entangled stored the IM message and environment notification.
- Verified Queue recorded exactly one `input_received` and exactly one `dispatch_wake_start_queued` for `18c14d716c0a`.
- Verified Runtime created wake scope `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0`, `session.init` succeeded, `im_read` executed successfully, and LLM calls continued in the wake.
- Verified after the dispatch TTL that `environment_notifications.dispatch_attempts` remained `1` and no duplicate Queue input event was created.

## Verification

- Local tests passed:
  - `novaic-business`: `PYTHONPATH=. pytest -q tests/test_dispatch_subscriber.py tests/test_environment_repository.py tests/test_im_aggregation.py` -> `65 passed`.
  - `novaic-common`: `PYTHONPATH=. pytest -q tests/test_assembler_sync.py tests/test_database_scoped_busy_timeout.py` -> `18 passed`.
  - `novaic-agent-runtime`: `PYTHONPATH=. pytest -q tests/test_pr259_generic_fsm_store_outbox.py tests/test_pr344_queue_claim_busy_handling.py tests/test_pr345_recovery_background_defer.py tests/test_pr233_active_inbox_dispatch.py tests/test_pr248_attach_outbox_cutover.py` -> `24 passed`.
- Deploy passed:
  - `./deploy services` completed successfully.
  - Fresh-smoke logs were fresh for all required backend and runtime processes.
- Production smoke evidence:
  - Notification row: `18c14d716c0a | claimed | claim_scope_id=2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0 | dispatch_claim_id=delivered:subscriber | dispatch_attempts=1`.
  - Session events: `input_received = 1`, `dispatch_wake_start_queued = 1`.
  - Runtime tasks include successful `session.init`, `im_read`, `context.append`, and `llm.call` for scope `2c4fbe39-8ff6-4b8e-b5c8-3bd13e0690d0`.

## Gaps

None found in the dispatch path covered by this ticket. The smoke did not assert user-visible natural-language reply text because the purpose of this repair was Environment notification delivery into Queue/Runtime; it did confirm Runtime loop execution beyond `im_read` and successful LLM calls.

## Artifacts

- Code changes: `novaic-common/common/db/database.py`, `novaic-common/common/wake/assembler.py`, `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`, `novaic-agent-runtime/queue_service/queue_db.py`, `novaic-agent-runtime/queue_service/saga_repo.py`, `novaic-agent-runtime/queue_service/routes.py`, `novaic-business/business/environment.py`, `novaic-business/business/subscribers/dispatch_subscriber.py`.
- Tests added/updated across `novaic-common/tests`, `novaic-agent-runtime/tests`, and `novaic-business/tests`.
