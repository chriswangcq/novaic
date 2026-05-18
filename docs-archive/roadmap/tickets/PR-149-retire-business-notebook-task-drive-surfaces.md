# PR-149 — Retire Business Notebook / Quadrant Task / Drive Profile Surfaces

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-01 |
| Repos | novaic-business, novaic-app if surfaced, docs |
| Depends on | PR-148 |

## Goal

Clarify whether Business should still expose agent notebook, four-quadrant task, growth log, and drive profile APIs/entities. If no current product surface uses them, physically remove the endpoints/schema and add guardrails so they do not re-enter the Agent prompt/tool path.

## Why This Matters

These surfaces came from earlier self-drive / memory / task concepts. They are no longer LLM tools and should not pretend to be Cortex continuity. If they remain, they need explicit product ownership; otherwise they are expensive live-code residue.

## Current Suspects

- `novaic-business/business/internal/agent.py`
  - notebook write/list/read/update
  - drive update profile / relationship
- `novaic-business/business/internal/task.py`
  - quadrant task APIs
  - growth log API
- `novaic-business/business/schema_push.py`
  - `agent-notebook`, `agent-tasks`, related product entities
- App settings/product pages if they still expose these entities.

## Implementation Plan

1. [x] Inventory live callers from Runtime, App, Business, and docs.
2. [x] Decide per surface: keep `agent-tools` as explicit product config; remove notebook/task/growth/memory surfaces.
3. [x] For removed surfaces, delete endpoints, schemas, client wrappers, docs, and tests.
4. [x] For kept surfaces, rename/describe them as product data, not Agent memory or Cortex continuity.
5. [x] Add guardrail preventing notebook/task/drive profile surfaces from being exposed as LLM tools or Cortex ownership paths.

## Unit / Guardrail Tests

- [x] Business tests updated for kept/removed routes.
- [x] Schema push tests updated.
- [x] Guardrail confirms `notebook_*`, `task_*`, `drive_update_profile`, and quadrant task concepts do not appear in LLM tools / Cortex ownership paths.

## Smoke / Deploy

- [x] Business tests pass: `python3 -m pytest tests` → 174 passed.
- [x] App build/typecheck passes: `npm run build`; App unit tests: `npm run test:unit -- --run` → 30 passed.
- [x] Deploy Business: `./deploy business`.
- [x] Deploy App frontend OTA: `./deploy frontend`.
- [x] Production smoke: Business `/health` returns healthy; removed notebook/task/drive endpoints return 404.
- [x] Production evidence: deployed Business active code grep has no retired markers outside guardrail tests.

## Git / Merge

- [x] Commit in each touched repo:
  - `novaic-business` `55afda3 business: retire agent self-drive surfaces`
  - `novaic-app` `468faf7 app: remove agent memory settings surface`
- [x] Parent repo submodule bump / docs commit.
- [x] Push `main`.
- [x] Mark this ticket `[deployed]` only after deploy evidence is collected.

## Closure Evidence

- Removed Business APIs:
  - `/internal/agents/{agent_id}/notebook/*`
  - `/internal/agents/{agent_id}/notebook-summary`
  - `/internal/agents/{agent_id}/drive`
  - `/internal/agents/{agent_id}/drive/update-profile`
  - `/internal/agents/{agent_id}/drive/update`
  - `/internal/agents/{agent_id}/drive/increment-interaction`
  - `/internal/agents/{agent_id}/quadrant-tasks*`
  - `/internal/agents/{agent_id}/growth-logs`
- Removed Business entities from active schema:
  - `agent-notebook`
  - `agent-memory`
  - `agent-tasks`
  - `agent-tools.growth_log`
  - `agent-tools.drive_config`
- Removed App surface:
  - `AgentMemorySection`
  - `agentMemoryStore`
  - `agent-memory` nav subscriptions
  - `agent_memory_*` locale keys
- Production smoke after deploy:
  - `GET http://127.0.0.1:19998/health` on server → `{"status":"healthy","service":"business","version":"0.3.0"}`
  - retired notebook/task/drive endpoints returned `404`.
