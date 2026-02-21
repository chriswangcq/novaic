# Round 001 Runtime State Contracts (Runtime Team)

## Purpose

Define runtime lifecycle/state interfaces provided by Runtime Orchestrator and consumed by other services during repo split.

## Provider and consumers

- provider: `Runtime Team` (`novaic-backend/runtime_orchestrator/**`)
- primary consumers:
  - `API Team` (gateway startup and runtime dependency health gates)
  - `Agent Runtime Team` (retry/idempotency behavior on runtime lifecycle operations)
  - `Desktop Team` (operability checks and replay diagnostics)

## Lifecycle states

- `active`
- `completed`
- `failed`

## Allowed transitions

- `active -> completed`
- `active -> failed`
- `completed -> active` (wake/reopen flow only)

## Disallowed transitions

- `completed -> failed`
- `failed -> completed`
- `failed -> active` (must get/create a new active runtime)

## Interface contract table

| interface | contract/location | provider guarantee | consumer expectation |
|---|---|---|---|
| Runtime orchestrator internal health | `contracts/openapi/runtime-orchestrator-internal.v1.yaml` (`GET /internal/health`) | returns `200` with `{status: ok}` when service is healthy | gateway and non-author replay scripts can gate startup on health readiness |
| Get or create active runtime | `runtime_orchestrator` API + repository semantics (`get-or-create`) | same `(agent_id, subagent_id)` returns one active runtime in retry paths | caller retries are idempotent; no duplicate active runtime creation |
| Set runtime status (CAS semantics) | runtime lifecycle status transition API (`set-status`) | transition succeeds only when `expected_status` matches current state | retries do not regress state after first successful transition |
| Wake runtime | runtime lifecycle API (`wake`) | only `completed -> active` reopen path is valid; non-destructive when already active/missing | callers can safely retry wake without corrupting status model |
| Runtime list ordering | runtime query APIs (`active`/`list` and batch) | deterministic ordering (`created_at ASC`, tie-breaker by `runtime_id ASC`) and batch output follows input order | consumers can perform stable replay comparisons |

## Replay baseline (Round 001)

- startup contract replay:
  - `cd novaic-backend && pytest -q tests/contract/test_runtime_orchestrator_process_startup.py`
- lifecycle consistency replay:
  - `cd novaic-backend && pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`

## Consumer impact note

- Repo split must preserve runtime lifecycle status semantics and deterministic query behavior; otherwise:
  - gateway startup/health coupling may regress,
  - agent retry/idempotency assumptions may break,
  - desktop/runtime diagnostics may become non-replayable.
