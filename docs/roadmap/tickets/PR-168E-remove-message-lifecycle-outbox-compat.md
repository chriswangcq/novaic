# PR-168E — Remove Message-Lifecycle / Outbox Notification Compatibility

> Historical ticket archive: this closed ticket/review may mention retired paths such as `message_outbox`, `SPAWN_SUBAGENT`, or removed subagent tools. Do not use it as current architecture or backlog; see `docs/roadmap/message-wake-refactor.md`, `docs/roadmap/agent-perception-action-architecture.md`, and `docs/roadmap/tickets/PR-210-maintenance-tail-cleanup.md`.


| Field | Value |
| --- | --- |
| Status | `[x]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-168 |
| Repos | `novaic-agent-runtime`, `novaic-business`, `novaic-common`, `Entangled`, scripts, docs |
| Depends on | PR-168D |

## Goal

Physically remove the old agent-loop notification compatibility path after Environment notifications became the owner of wake triggering and lifecycle.

## Current-State Analysis

PR-168C moved subscriber dispatch to Environment notification dispatch leases, and PR-168D moved Runtime session/finalize to Environment notification claim/processed transitions. The remaining old path is outside the hot loop but still active code:

- Runtime `HealthWorkerSync` now only recovers Queue/Saga timeouts.
- Business no longer exposes bulk transition, orphaned, stuck-claimed, ghost-scope, or message-trace endpoints.
- `messages` schema no longer declares `outbox_trigger_types`.
- Entangled no longer exposes `/v1/outbox`, `/v1/orphans`, `/v1/stuck-claimed`, `/v1/messages/*`, or message-transition history routes.
- Entangled no longer has `message_outbox` schema/coinsert support.

## Small Tickets

- [x] PR-168E1 — Runtime HealthWorker keeps only Queue/Saga timeout recovery.
- [x] PR-168E2 — Business removes old internal message lifecycle/outbox notification endpoints.
- [x] PR-168E3 — Common/Business message schema stops declaring outbox trigger types.
- [x] PR-168E4 — Entangled removes old outbox/orphan/stuck/message-lifecycle routes and schema support.
- [x] PR-168E5 — Add guardrails so the retired path cannot regrow.

## Verification Plan

- Runtime targeted + full tests.
- Business targeted + full tests.
- Common contract tests.
- Entangled targeted tests/build for route registration and schema behavior.
- `rg` guard over live code forbidding `bulk-transition`, `messages/orphaned`, `messages/stuck-claimed`, `/v1/outbox`, and non-empty message outbox trigger mappings outside historical docs.
- Deploy affected services and smoke-check that user message send still creates Environment notification and chat projection without using outbox.

## Done Criteria

- New user/subagent/system messages trigger Agent loop only through Environment notifications.
- No Runtime service calls old message lifecycle/outbox notification endpoints.
- No Business internal API exposes old message lifecycle/outbox notification control surfaces.
- No new `message_outbox` rows are produced by chat message projection.
- Historical docs may mention old tickets, but active code and tests no longer keep the retired branch alive.

## Implementation Notes

- Runtime `HealthWorkerSync` no longer imports Business client code and only calls Queue `/api/queue/recover/all`.
- Runtime `session.init` / `scope_end` use Environment notification transitions (`claim` / `processed` / `failed`).
- Business `business/internal/message.py` is now presentation-only for chat projection helpers.
- Common `message_lifecycle.json` no longer contains `outbox_trigger_types`.
- Entangled removed:
  - `entangled/app/outbox.py`
  - `entangled/app/orphans.py`
  - `entangled/app/stuck_claimed.py`
  - `entangled/app/message_state.py`
  - `entangled/sql/message_state.py`
  - `SqlEntityDef.outbox_trigger_types`
  - `SqlEntityStore` `message_outbox` schema and coinsert code.

## Verification

- Local tests:
  - Entangled: `PYTHONPATH=packages/server-python pytest -q packages/server-python/tests` → 52 passed.
  - Common: `PYTHONPATH=.:../novaic-agent-runtime pytest -q` → 122 passed.
  - Business: `PYTHONPATH=.:../novaic-common pytest -q` → 147 passed, 1 warning.
  - Runtime: `PYTHONPATH=.:../novaic-common pytest -q` → 170 passed.
- Static/guard checks:
  - `python -m py_compile` for changed Entangled/Business/Runtime modules passed.
  - `bash scripts/ci/lint_lifecycle.sh` passed.
  - `bash scripts/ci/lint_lifecycle_loop_ownership.sh` passed.
  - `bash scripts/ci/lint_agent_loop_path.sh` passed.
  - `python scripts/ci/check_no_internal_async.py` passed.
  - Entangled route smoke confirmed old routes absent and subagent transition route still present.
- Deployment:
  - `./deploy services` succeeded on `api.gradievo.com`.
  - `./deploy status` showed all backend services healthy.
  - Remote source guard found no retired path strings in active service source.
  - Remote route smoke confirmed retired routes absent.
  - Production DB was backed up to `/opt/novaic/data/entangled-pr168e-drop-old-message-lifecycle-20260502210713.db`; old `message_outbox` and `message_state_transitions` tables were dropped and remained absent after services restarted.
