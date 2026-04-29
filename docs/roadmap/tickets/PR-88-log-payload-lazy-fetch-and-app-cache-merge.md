# PR-88 — Complete `log-payloads` lazy fetch and merge into App log view

| Field | Value |
|---|---|
| **Ticket** | PR-88 |
| **Status** | `[✓ deployed]` |
| **Opened** | 2026-04-29 |
| **Owner** | __ |
| **Severity** | P1 details panel correctness — heavy payloads are stored separately, but the App only has a partial input fetch path and does not merge it back into the visible log entry. |
| **Depends on** | PR-86 preferred. |
| **Blocks** | Reliable LLM input/details modal and execution-log drilldown. |
| **Invariant** | Heavy payloads stay out of stream rows and are fetched on demand through explicit payload APIs. |

## Background

Business already moves heavy fields out of `execution_logs.data` into `log-payloads`:

```text
input -> execution_log_payloads.input
result -> execution_log_payloads.result
error -> execution_log_payloads.error
```

But the active action surface only exposes `log-payloads.get_input`, and App code fetches input into a separate cache without consistently merging it into the `LogEntry` consumed by the details UI.

## Goal

Make payload lazy fetch symmetric and usable:

- expose a payload fetch API that can return `input`, `result`, and `error`;
- merge fetched payload into the App log view model/cache;
- keep stream rows light.

## Non-Goals

- Do not subscribe the App to all `log-payloads` rows by default.
- Do not make `log-payloads` part of the hot stream path.
- Do not duplicate LLM Factory raw call storage.

## Implementation Checklist

- [x] Add Business action, likely `log-payloads.get_payload`, returning `{input, result, error}` for `agent_id + log_id`.
- [x] Keep `get_input` as compatibility shim if callers still exist, or migrate callers and retire it deliberately.
- [x] Update App payload cache store to cache payload by log id, not only input.
- [x] Update `useLogs` to merge cached payload fields into `LogEntry` before rendering.
- [x] Update `ExecutionLog` modal/detail code to read merged `log.input`, `log.result`, and `log.error`.
- [x] Ensure missing payload returns a clean empty state, not a broken modal.

## Unit Test Requirements

- [x] Business unit test: `get_payload` returns input/result/error for an authorized agent.
- [x] Business unit test: unauthorized agent/user is rejected.
- [x] Business unit test: missing payload returns explicit empty values.
- [x] App unit test: fetched payload is merged into `LogEntry`.
- [x] App component test: LLM input modal opens after lazy fetch.

Suggested commands:

```bash
pytest novaic-business/tests -q
npm --prefix novaic-app run test:unit
```

Evidence captured 2026-04-29:

```bash
pytest novaic-business/tests/test_pr88_log_payload_actions.py \
  novaic-business/tests/test_schema_invariants.py -q
# 9 passed in 0.05s

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

- [x] Produce a think log with LLM input/result payload.
- [x] Click/open details in the App.
- [x] Verify payload is lazy-fetched and displayed.
- [x] Produce a tool log with result/error payload and verify detail rendering.

Production smoke captured 2026-04-29:

```http
POST /internal/entities/log-payloads/action/get_payload
```

```json
{"success":true,"data":{"input":{"tool":"skill_end","args":{"scope_id":"0f1af928-8f85-4ec4-b6c7-5648fbdf2819","report":"用户PR86-91 smoke测试消息，已简短回复\"收到！✅\"完成日志链路验证。"}},"result":{"content":"{\"ok\": true, \"child_path\": \"/ro/active/agent-root-main-415f6cfd/steps/0022_scope_0f1af928-8f85-4ec4-b6c7-5648fbdf2819\", \"scope_id\": \"0f1af928-8f85-4ec4-b6c7-5648fbdf2819\", \"summary\": \"用户PR86-91 smoke测试消息，已简短回复\\\"收到！✅\\\"完成日志链路验证。\", \"stack\": [], \"stack_depth\": 0}"},"error":null}}
```

## Deployment Checklist

- [x] Deploy Business action changes.
- [x] Deploy App changes.
- [x] If `get_input` is retired, verify no active client still calls it before removal.
- [x] Capture network/action evidence for `log-payloads.get_payload`.
- [x] Capture App details panel evidence.

## GitHub / Commit Checklist

- [x] Commit Business changes.
- [x] Commit App changes.
- [x] Commit parent submodule pointer updates.
- [x] PR description links this ticket.
- [x] PR description includes unit tests and smoke payload evidence.

## Acceptance Criteria

- App can display lazily fetched input/result/error payloads.
- Payload cache is actually consumed by rendered log entries.
- Stream rows remain lightweight.

## Rollback

Rollback if payload fetch causes authorization or performance regressions. During rollback, retain old `get_input` behavior if it is still used by released clients.
