# PR-167A — Dedicated Environment Entity Schema and Contract Guardrails

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-167 |
| Repos | `novaic-common`, `novaic-business`, docs |
| Depends on | PR-167 |

## Goal

Add the dedicated Environment entity contract and Business schema registrations without switching the hot agent loop yet.

## Current-State Analysis

Business currently registers `messages` and `execution-logs` as stream entities. Environment repository wraps `messages`. This ticket only creates the target Environment entities so later tickets can move repository/service callers behind them without ambiguity.

## Implementation Checklist

- [x] Common contract lists dedicated Environment entity names and required fields.
- [x] Business schema registers:
  - `environment-events`
  - `environment-im-messages`
  - `environment-notifications`
  - `environment-resource-refs`
- [x] Entity schemas include agent, sender/channel/thread, lifecycle, idempotency, and timestamps where relevant.
- [x] Resource refs store only locator/ref metadata, not raw payload.
- [x] Tests guard schema presence and raw payload exclusion.
- [x] Deploy Business schema registration and record evidence.

## Verification Plan

```bash
cd novaic-common && pytest -q tests/test_environment_contract.py
cd ../novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_schema_contracts.py tests/test_environment_repository.py
cd .. && ./deploy business && ./deploy status
```

## Done Criteria

- Target entities exist in code and tests.
- No hot path behavior changes yet.
- Later PR-167B can write to these entities without inventing new names or shape.

## Completion Evidence

- `cd novaic-common && PYTHONPATH=. pytest -q tests/test_environment_contract.py` → 7 passed.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q tests/test_environment_schema_contracts.py tests/test_environment_repository.py` → 18 passed.
- `cd novaic-common && PYTHONPATH=.:../novaic-agent-runtime pytest -q` → 122 passed.
- `cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q` → 201 passed, 2 warnings.
- `./deploy business` restarted all backend services successfully.
- `./deploy status` showed Entangled, Gateway, Business, Device, Queue, Storage, Cortex, workers, and Relay healthy.
- Production schema import smoke verified the four dedicated entity names, tables, id fields, key params, and ordering from `/opt/novaic/services/novaic-business`.
