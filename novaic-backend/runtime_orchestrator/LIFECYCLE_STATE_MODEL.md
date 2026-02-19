# Runtime Lifecycle State Model

This document defines the runtime lifecycle contract for Runtime Orchestrator.

## Goals

- Keep runtime status transitions consistent and deterministic
- Make repeated lifecycle operations idempotent when possible
- Prevent invalid state regressions in concurrent/retry scenarios

## Runtime Statuses

- `active`: runtime is currently running and can accept new work
- `completed`: runtime finished the current execution flow successfully
- `failed`: runtime terminated with an error

## Allowed Transitions

- `active -> completed`
- `active -> failed`
- `completed -> active` (wake/reopen flow only)

Disallowed examples:

- `completed -> failed`
- `failed -> completed`
- `failed -> active` (must create/get a new active runtime instead)

## Lifecycle Operations

### 1. Start Runtime

- Preferred API: `POST /internal/runtimes/get-or-create`
- Contract:
  - If an active runtime already exists for `(agent_id, subagent_id)`, return it
  - If none exists, create one and return it
- Idempotency:
  - Repeated calls with same `(agent_id, subagent_id)` return the same active runtime
  - Response includes `just_created` to distinguish creation vs reuse

### 2. Stop Runtime

- Stop is represented by status transition from `active` to terminal status:
  - success path: `active -> completed`
  - error path: `active -> failed`
- Preferred API: `POST /internal/runtimes/{runtime_id}/set-status`
- Consistency control:
  - CAS-style guard via `expected_status`
  - Caller retries must not force invalid transition if state has already moved

### 3. Wake Runtime

- `POST /internal/runtimes/{runtime_id}/wake` transitions `completed -> active`
- If runtime is already active or missing, operation is non-destructive and returns skipped semantics

## Deterministic Query Rules

- `GET /internal/runtimes/active` and `GET /internal/runtimes/list`
  - active runtimes are returned in stable order by `created_at ASC, runtime_id ASC`
- `POST /internal/runtimes/batch`
  - output order must follow input `runtime_ids` order

## Retry and Idempotency Expectations

- Repeated `get-or-create` should never produce multiple active runtimes for the same `(agent_id, subagent_id)` in sequential retry scenarios
- Repeated `set-status` with old `expected_status` should fail safely (or be treated as already applied when state already equals `new_status`)
- Repeated `summarized` and `need-rest` operations are idempotent by design

## Baseline Verification Scenarios

- Same `(agent_id, subagent_id)` calls `get-or-create` twice -> same `runtime_id`
- Transition `active -> completed` then retry same CAS transition -> no rollback, status remains `completed`
- Multiple active runtimes with identical `created_at` still return in deterministic order
