# PR-86 — Define execution-log lightweight metadata contract

| Field | Value |
|---|---|
| **Ticket** | PR-86 |
| **Status** | `[✓ deployed]` |
| **Opened** | 2026-04-29 |
| **Owner** | __ |
| **Severity** | P1 observability / UI correctness — Entangled sync works, but execution-log rows are too thin for the App to render without guessing from `event_key`. |
| **Depends on** | PR-78+ active wake scope path stable. |
| **Blocks** | PR-87, PR-88, PR-89, PR-90. |
| **Invariant** | Entangled carries lightweight execution metadata only; heavy payloads remain lazy-fetched or owned by TRS / LLM Factory. |

## Background

Client cache inspection in:

```text
~/Library/Application Support/com.novaic.app/entangled_cache.db
```

showed that `execution-logs` is syncing correctly, but recent rows look like:

```text
kind=tool  status=complete  event_key=tool:<scope>:chat_reply:0  data={"type":"tool"}
kind=think status=complete  event_key=think:<scope>:round-2        data={"type":"think"}
```

This forces the App to parse `event_key` to recover the tool name, scope id, and round. That is brittle and wastes the fact that Entangled is already the UI-facing realtime read model.

## Goal

Define and implement the minimal metadata carried in `execution_logs.data` for think/tool events.

Expected shape:

```json
{
  "type": "tool",
  "scope_id": "...",
  "round_id": "round-1",
  "tool": "chat_reply",
  "tool_call_id": "chat_reply:0"
}
```

Think logs should similarly include:

```json
{
  "type": "think",
  "scope_id": "...",
  "round_id": "round-1"
}
```

Later tickets may add `result_id` and `factory_log_id`; this ticket establishes the base contract and removes App dependence on parsing `event_key`.

## Non-Goals

- Do not put raw LLM request/response bodies in Entangled rows.
- Do not put full tool results in Entangled rows.
- Do not change Cortex scope semantics.
- Do not introduce a new logging system.

## Implementation Checklist

- [x] Update Runtime `sync_broadcast_log` call sites for tool running/complete logs to include `scope_id`, `round_id`, `tool`, and `tool_call_id` in lightweight `data`.
- [x] Update Runtime think running/complete logs to include `scope_id` and `round_id`.
- [x] Keep `event_key` for idempotent upsert identity, but stop treating it as the UI data source.
- [x] Update App `ExecutionLogEntity` / `LogEntry` mapping if needed so these metadata fields flow through.
- [x] Update App rendering to prefer `log.data.tool` / `tool_call_id` over `event_key` parsing.
- [x] Keep backward-compatible display fallback for already-cached old rows.

## Unit Test Requirements

- [x] Runtime unit test: tool broadcast row contains `data.tool`, `data.tool_call_id`, `data.scope_id`, and `data.round_id`.
- [x] Runtime unit test: think broadcast row contains `data.scope_id` and `data.round_id`.
- [x] App unit test or component-level test: tool label uses `data.tool` when available.
- [x] App regression test: old row with only `event_key` still renders a reasonable fallback.

Suggested commands:

```bash
pytest novaic-agent-runtime/tests -q
npm --prefix novaic-app run test:unit
```

Evidence captured 2026-04-29:

```bash
pytest novaic-agent-runtime/tests/test_pr86_execution_log_metadata.py \
  novaic-agent-runtime/tests/unit/task_queue/test_tool_handlers_failure_event.py \
  novaic-agent-runtime/tests/test_pr71_no_tool_retry_context_cleanup.py \
  novaic-agent-runtime/tests/test_pr85_llm_context_smoke_guardrails.py -q
# 18 passed in 0.08s

npm --prefix novaic-app run test:unit -- \
  src/components/Visual/executionLogUtils.test.ts \
  src/components/hooks/useLogs.test.ts \
  src/components/Visual/ExecutionLog.test.tsx
# 3 test files passed, 10 tests passed

npm --prefix novaic-app run build
# built successfully; existing Vite chunk-size/dynamic-import warnings only

python -m compileall -q novaic-agent-runtime/task_queue/handlers \
  novaic-agent-runtime/tests novaic-business/business novaic-business/tests
# passed
```

## Smoke Test Requirements

- [x] Start local Business + Runtime + App.
- [x] Send a message that produces one `think` and one `chat_reply` tool call.
- [x] Inspect Entangled `execution-logs` row from App cache / production Entangled and verify metadata exists in `data`.
- [x] Verify the App no longer needs to display labels derived only from `event_key`.

Production smoke captured 2026-04-29 after `./deploy services` + `./deploy frontend`:

```sql
SELECT id,kind,status,event_key,data FROM execution_logs WHERE id IN (1096,1097);
```

```json
{"id":1096,"kind":"think","status":"complete","data":{"type":"think","scope_id":"0f1af928-8f85-4ec4-b6c7-5648fbdf2819","round_id":"round-1","model":"kimi-k2.5","provider":"factory","message_count":11,"tool_count":9,"factory_log_id":"37c85675-36e6-4fbb-b6c4-da68d7b626a0"}}
{"id":1097,"kind":"tool","status":"complete","data":{"type":"tool","scope_id":"0f1af928-8f85-4ec4-b6c7-5648fbdf2819","round_id":"round-1","tool_call_id":"chat_reply:0","tool":"chat_reply","result_id":"trs:0f1af928-8f85-4ec4-b6c7-5648fbdf2819:round1:chat_reply:0"}}
```

## Deployment Checklist

- [x] Deploy affected services:
  - [x] runtime
  - [x] business only if schema/entity code changes are needed
  - [x] app if UI mapping/rendering changes
- [x] After deploy, send one smoke message in production/staging.
- [x] Capture one `execution_logs.data` sample showing lightweight metadata.
- [x] Capture one App screenshot or log proving display remains correct.

## GitHub / Commit Checklist

- [x] Commit subrepo changes in `novaic-agent-runtime`.
- [x] Commit App changes in `novaic-app` if changed.
- [x] Commit parent submodule pointer updates.
- [x] PR description links this ticket.
- [x] PR description includes unit test output and smoke evidence.

## Acceptance Criteria

- New execution-log rows expose minimal UI metadata without parsing `event_key`.
- Heavy payload remains outside the Entangled row.
- Existing old rows continue to render with fallback behavior.

## Rollback

Rollback if execution logs stop upserting idempotently or if App log rendering regresses. Since the old `event_key` fallback remains, rollback should be isolated to metadata projection and UI preference logic.
