# PR-163C3 — Delete Superseded Direct Communication Tools

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-163C |
| Repos | `novaic-common`, `novaic-agent-runtime`, `novaic-business`, `novaic-app`, docs |
| Depends on | PR-163C2 |

## Goal

Physically remove old direct communication tool paths after Environment IM is the live behavior path.

## Scope

- [x] Remove `chat_reply` schema/executor/monitor mapping after `im_reply` replacement.
- [x] Remove `subagent_send` schema/executor/monitor mapping after `im_send` replacement.
- [x] Delete `chat_history` as an LLM tool path; Environment observation and Cortex scope continuity are the active paths.
- [x] Remove old Business internal HTTP endpoints backing `chat_history` and direct `subagent_send`.
- [x] Add guardrails against old communication tools reappearing as active LLM tools.

## Implementation Notes

- Active LLM schema, Runtime executors, execution-log display mapping, and tool product semantics now share the same ten-tool set:
  `audio_qa`, `display`, `im_read`, `im_reply`, `im_send`, `shell`, `skill_begin`, `skill_end`, `sleep`, `subagent_spawn`.
- The per-wake reply cap moved from the removed direct reply executor to `im_reply`.
- Business keeps lifecycle message type `SUBAGENT_SEND` for existing dispatch semantics; this is a data event type, not an LLM-facing direct send tool.

## Required Tests

- [x] Common active schema contract: `PYTHONPATH=.:../novaic-agent-runtime pytest -q` in `novaic-common` — 113 passed.
- [x] Runtime executor contract: `PYTHONPATH=.:../novaic-common pytest -q` in `novaic-agent-runtime` — 203 passed.
- [x] Business prompt/internal API contracts: `PYTHONPATH=.:../novaic-common pytest -q` in `novaic-business` — 195 passed, 2 warnings.
- [x] Cortex schema/rendering contracts: `PYTHONPATH=.:../novaic-common pytest -q` in `novaic-cortex` — 386 passed, 16 skipped.
- [x] Agent Monitor display contract: `npm run test:unit -- src/components/Visual/executionLogUtils.test.ts src/components/Visual/ExecutionLog.test.tsx` — 12 passed.
- [x] App build: `npm run build` — passed.
- [x] Local smoke: schema/executor/display/semantics names match and contain no superseded direct communication tools.

## Deploy / Git

- [x] Commit affected subrepos separately.
- [x] Deploy via `./deploy services`.
- [x] Deploy App OTA via `./deploy frontend 0.3.0`.
- [x] Production smoke: `./deploy status` shows all backend ports healthy and relay active.
- [x] Production contract smoke: remote schema/executor/display/semantics sets all match the ten active tools and none contains `chat_reply`, `chat_history`, or `subagent_send`.
- [x] Production residue scan: no active non-test source contains the removed tool schemas/executors or old internal endpoints.

## Done Criteria

- No superseded communication tool remains as active LLM schema or Runtime executor.
- Any retained chat-reading tool has an explicit product reason and does not overlap Environment notification observation.
- Deployed 2026-05-02.
