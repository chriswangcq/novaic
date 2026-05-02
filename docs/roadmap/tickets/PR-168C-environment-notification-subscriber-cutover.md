# PR-168C — Environment Notification Subscriber Cutover

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-168 |
| Repos | `novaic-business`, `scripts`, docs |
| Depends on | PR-168B |

## Goal

Switch the standalone subscriber from the old delivery queue path to dedicated Environment notification dispatch leases.

## Current-State Analysis

Before this ticket, the subscriber still claimed the old dispatch source and the startup script still described it as a message-outbox drain. PR-168B added the missing Environment dispatch lease fields, but the hot loop had not yet been moved.

The intended boundary is:

- Environment notification lifecycle remains semantic: `pending / claimed / processed / failed`.
- Subscriber owns only the dispatch lease: `dispatch_claim_id`, `dispatch_claimed_at`, `dispatch_attempts`, and `dispatch_error`.
- Runtime `session.init` and wake finalization own semantic claim/processed transitions.
- Subscriber does not write Cortex input ownership and does not call message lifecycle transition APIs.

## Implementation Checklist

- [x] Add `EnvironmentDispatchSource` to claim dispatchable Environment notifications.
- [x] Map `environment-notifications` + `environment-im-messages` to subscriber dispatch rows.
- [x] Add dispatch claim TTL behavior so stale dispatch leases become retryable without a second queue.
- [x] Remove subscriber Cortex client dependency from `main_subscriber.py` and `DispatchSubscriber`.
- [x] Remove the old stale-scope/message-lifecycle probe test path.
- [x] Update aggregation tests to use dispatch-source terminology.
- [x] Update `scripts/start.sh` so subscriber starts without `--cortex-url`.
- [x] Add guard tests preventing Cortex/message lifecycle ownership from growing back into subscriber.
- [x] Run unit tests, deploy, and smoke test the deployed path.

## Verification

- `cd novaic-business && python -m py_compile business/environment.py business/subscribers/dispatch_subscriber.py main_subscriber.py` → passed.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_repository.py tests/test_dispatch_subscriber.py tests/test_im_aggregation.py` → 58 passed.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q` → 189 passed, 2 warnings.
- `bash -n scripts/start.sh` → passed.
- `./deploy business` → all backend services restarted.
- `./deploy status` → service ports healthy and relay active.
- Production smoke on `/opt/novaic/services/novaic-business` verified deployed `EnvironmentDispatchSource.claim_batch` maps a user Environment message into a dispatch row and records the dispatch claim.
- Production subscriber process stayed resident after restart and, after its startup line, logged `environment-notifications/list` polling with zero `/v1/outbox/claim` calls.

## Completion Notes

PR-168C closes the subscriber-side wake trigger cutover. The remaining PR-168 work is Runtime finalization and physical deletion of old message-lifecycle/outbox compatibility surfaces that still exist outside the subscriber hot path.
