# PR-149 — Retire Business Notebook / Quadrant Task / Drive Profile Surfaces

| Field | Value |
| --- | --- |
| Status | `[ ]` |
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

1. [ ] Inventory live callers from Runtime, App, Business, and docs.
2. [ ] Decide per surface: keep as explicit product feature or remove.
3. [ ] For removed surfaces, delete endpoints, schemas, client wrappers, docs, and tests.
4. [ ] For kept surfaces, rename/describe them as product data, not Agent memory or Cortex continuity.
5. [ ] Add guardrail preventing notebook/task/drive profile surfaces from being exposed as LLM tools or Cortex context producers.

## Unit / Guardrail Tests

- [ ] Business tests updated for kept/removed routes.
- [ ] Schema push tests updated.
- [ ] Guardrail confirms `notebook_*`, `task_*`, `drive_update_profile`, and quadrant task concepts do not appear in LLM tools / Cortex ownership paths.

## Smoke / Deploy

- [ ] Business tests pass.
- [ ] App build/typecheck passes if imports are touched.
- [ ] Deploy Business.
- [ ] Production smoke: Agent chat still works and LLM tools list excludes notebook/task/drive tools.
- [ ] Production evidence: removed endpoints return 404 or are absent from OpenAPI/internal router, depending on API policy.

## Git / Merge

- [ ] Commit in each touched repo.
- [ ] Parent repo submodule bump / docs commit.
- [ ] Push `main`.
- [ ] Mark this ticket `[deployed]` only after deploy evidence is collected.

