# Cortex API materialization call-site map success check

## Summary

`P144` is successful. The one-go result earned the shortcut: it maps the relevant API call sites with source pointers, classifies event/projection/retrieval roles, runs focused API tests, and stress-checks for duplicate active projection write paths. The only remaining issue is naming clarity around `/v1/context/read`, which is non-blocking because current runtime authority is guarded through `prepare_for_llm`.

## Evidence

- Result `R141` maps context append/batch, context read, prepare-for-LLM, step write/list/read/index, formatted/preview step reads, and payload read/search endpoints.
- `novaic-cortex/novaic_cortex/api.py:853` and `:876` show context append/batch event writes paired with projection writes under `_scope_lock_cm`.
- `novaic-cortex/novaic_cortex/api.py:925` shows `prepare_for_llm` as the authoritative ContextEvent read model path.
- `novaic-cortex/novaic_cortex/api.py:1526` shows `/v1/steps/write` normalizes a step, records `ToolStepRecorded`, then calls `ws.write_step_projection(...)`.
- `novaic-cortex/novaic_cortex/workspace.py:787` shows `write_step_projection(...)` delegates to the normalized `write_step(...)` projection path.
- Stress search for `append_context_projection`, `append_context_batch_projection`, `write_step_projection`, `_append_context_message_event`, `tool_step_recorded`, and `write_step(` found no second active Cortex API write path diverging from ContextEvents.
- Focused tests passed: `20 passed` for Cortex context-write, step-write, payload-inspection, and API contract tests.

## Criteria Map

- API call sites for context message writes, batch writes, tool step writes, and payload reads are mapped with source pointers: satisfied by `R141` source pointers for `api.py:840`, `:853`, `:876`, `:925`, `:1526`, `:1573`, `:1580`, `:1591`, `:1776`, `:1815`, `:1885`, and `:1912`.
- Each call site is classified as authoritative event append, materialized projection write, explicit payload retrieval, or legacy/stale path: satisfied by `R141` classification bullets.
- Tests covering API context writes and step writes are identified and run: satisfied by the focused pytest command in `R141`, result `20 passed`.
- Any duplicate active write path that can diverge from ContextEvents is fixed or split: satisfied because the stress search found no duplicate divergent active write path; no follow-up split is required for this problem.

## Execution Map

- Ticket `T145` was classified `one_go` because the task was bounded to mapping API call sites and running focused tests.
- Execution inspected Cortex API endpoints and Workspace projection helpers.
- Execution recorded result `R141` with source pointers, test evidence, and known residual risks.
- This check treats the one-go path skeptically by requiring a secondary residual write-path search before accepting success.

## Stress Test

- Plausible failure mode: a hidden API or runtime path still writes `context.jsonl`, `steps/*.json`, `_index.jsonl`, or payload projections without a paired ContextEvent, so the project appears event-sourced while old authority still leaks through files.
- Stress command: `rg -n "append_context_projection|append_context_batch_projection|write_step_projection|_append_context_message_event|tool_step_recorded|write_step\\(" novaic-cortex/novaic_cortex novaic-agent-runtime/task_queue -S`.
- Result: active projection writes are limited to the known API pairings plus Workspace implementation helpers; runtime uses `CortexBridge.write_step`, which posts to `/v1/steps/write`.

## Residual Risk

- `/v1/context/read` remains a confusing API name because it reads a projection. This is non-blocking for `P144` because it is explicitly classified, runtime LLM authority is guarded separately, and broader API cleanup can be handled by parent/cleanup problems.
- This check does not claim all repo old-code cleanup is complete; it only closes the API materialization call-site map problem.

## Result IDs

- R141
