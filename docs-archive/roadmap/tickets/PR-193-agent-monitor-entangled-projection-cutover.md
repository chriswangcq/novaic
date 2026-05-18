# PR-193 — Agent Monitor Entangled Projection Cutover

Status: closed

## Goal

Move the user-facing Agent Monitor from the old pull path:

`App useActivityTimeline polling -> agents.activity_timeline action -> Business HTTP -> Cortex /v1/trace/project`

to a product projection synced through Entangled entities.

## Non-goals

- Do not reintroduce `execution-logs` as the normal user monitor source.
- Do not subscribe the App to raw `subagents`.
- Do not keep a fallback polling path.
- Do not make the App know Cortex scope ids.

## Big Work Orders

1. [PR-193A — Agent Activity Entangled Entity Contracts](PR-193A-agent-activity-entangled-entity-contracts.md)
2. [PR-193B — Runtime Agent Activity Projection Write Path](PR-193B-runtime-agent-activity-projection-write-path.md)
3. [PR-193C — App Agent Monitor Entangled Read Path](PR-193C-app-agent-monitor-entangled-read-path.md)
4. [PR-193D — Delete Activity Timeline Action Hot Path](PR-193D-delete-activity-timeline-action-hot-path.md)
5. [PR-193E — Agent Monitor Projection Guardrails and Docs](PR-193E-agent-monitor-projection-guardrails-and-docs.md)

## Acceptance

- [x] Agent Monitor data is read from Entangled app cache.
- [x] Conversation route subscribes `agent-activity-records` and `agent-activity-participants`.
- [x] App code does not call `agents.activity_timeline`.
- [x] Business does not register or handle `agents.activity_timeline`.
- [x] Business/App hot path does not call Cortex `/v1/trace/project`.
- [x] Cortex no longer exposes `/v1/trace/project` as a product projection route.
- [x] Guard tests reject `execution-logs`, raw `subagents`, polling, and activity timeline action fallback.

## Closure

Closed 2026-05-03. Runtime now materializes public `agent-activity-records` and `agent-activity-participants` during the normal trace write path; App reads those entities from Entangled cache; the old `agents.activity_timeline` Business action and Cortex `/v1/trace/project` endpoint were physically removed.

Validation and deploy evidence:

```bash
cd novaic-agent-runtime && PYTHONPATH=. pytest -q tests/test_pr193_activity_projection.py tests/test_context_read_by_ids.py tests/test_pr165c_notification_lifecycle_guardrails.py
cd novaic-business && PYTHONPATH=.:../novaic-common:../Entangled/packages/server-python pytest -q tests/test_pr193_no_activity_timeline_action.py tests/test_pr100_app_entity_schema_contract.py tests/test_schema_invariants.py
cd novaic-common && PYTHONPATH=. pytest -q tests/test_pr166c_entangled_app_entities.py
cd novaic-cortex && PYTHONPATH=. pytest -q tests/test_pr193_no_trace_projection_http_path.py tests/test_step_result_projection.py tests/test_payload_inspection_api.py tests/test_context_engine_dfs.py
cd novaic-app && npm run test:unit -- src/components/hooks/useActivityTimeline.test.ts src/components/Visual/ActivityTimeline.guard.test.ts src/components/Chat/ChatPanel.activityTimelineGuard.test.ts src/data/entities/entangledEntityContracts.test.ts src/components/Visual/ActivityTimeline.test.tsx src/components/Visual/SubagentList.test.tsx
cd novaic-app && npm run build
cd novaic-app/src-tauri && cargo check
./deploy services
./deploy frontend 0.3.0
./deploy status
```

Production smoke: `./deploy status` reported Entangled, Gateway, Business, Device, Queue, Blob Service, Cortex, 8 workers, and Relay healthy. Remote Cortex `POST /v1/trace/project` returns `404`; deployed Business schema contains `agent-activity-records` and `agent-activity-participants`, and no longer registers `activity_timeline`.
