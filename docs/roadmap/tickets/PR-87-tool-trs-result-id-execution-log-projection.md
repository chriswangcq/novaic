# PR-87 — Project tool TRS `result_id` into execution logs

| Field | Value |
|---|---|
| **Ticket** | PR-87 |
| **Status** | `[✓ deployed]` |
| **Opened** | 2026-04-29 |
| **Owner** | __ |
| **Severity** | P1 tool result visibility — TRS stores tool results, and the App already knows how to render TRS, but execution logs do not expose the join key. |
| **Depends on** | PR-86 preferred. |
| **Blocks** | Better App execution-log details without duplicating tool result payloads. |
| **Invariant** | Entangled execution logs should carry join keys, not large tool results. |

## Background

Runtime currently derives TRS-like result ids when saving tool steps into Cortex:

```text
trs:{scope_id}:round{round_num}:{tool_call_id}
```

The App has `InlineTrsResult` rendering support, but the synced execution-log row contains only:

```json
{"type": "tool"}
```

So the UI cannot connect a tool log to the full result without parsing unrelated payloads or expanding large data into Entangled.

## Goal

Project the tool result join key into the execution-log lightweight metadata:

```json
{
  "type": "tool",
  "tool": "shell",
  "tool_call_id": "call_x",
  "scope_id": "...",
  "round_id": "round-2",
  "result_id": "trs:..."
}
```

Then wire the App to use `result_id` for existing TRS lazy rendering.

## Non-Goals

- Do not duplicate TRS normalized result content into Entangled.
- Do not fetch TRS automatically for every log row.
- Do not change TRS storage format.

## Implementation Checklist

- [x] Ensure Runtime tool execution result carries a deterministic `result_id` or `trsid` before broadcasting completion.
- [x] Include `result_id` in the execution-log completion row `data`.
- [x] Preserve idempotency across retries: same scope/round/tool call must produce the same `result_id`.
- [x] App maps `data.result_id` into `LogEntry.result` or an explicit field consumed by `InlineTrsResult`.
- [x] App uses TRS lazy fetch only when the user expands/opens result details.

## Unit Test Requirements

- [x] Runtime unit test: tool completion broadcast includes deterministic `result_id`.
- [x] Runtime unit test: retries with same scope/round/tool_call_id keep the same `result_id`.
- [x] App unit/component test: a tool log with `data.result_id` renders an expandable TRS result path.
- [x] App fallback test: a tool log without `result_id` still renders old summary behavior.

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
```

## Smoke Test Requirements

- [x] Run a tool that produces a result.
- [x] Verify `execution_logs.data.result_id` exists.
- [x] Open the App execution log and expand the tool result.
- [x] Verify the result is fetched through TRS / lazy detail, not embedded directly in the Entangled row.

Production smoke captured 2026-04-29:

```json
{"id":1097,"kind":"tool","status":"complete","data":{"type":"tool","scope_id":"0f1af928-8f85-4ec4-b6c7-5648fbdf2819","round_id":"round-1","tool_call_id":"chat_reply:0","tool":"chat_reply","result_id":"trs:0f1af928-8f85-4ec4-b6c7-5648fbdf2819:round1:chat_reply:0"}}
{"id":1099,"kind":"tool","status":"complete","data":{"type":"tool","scope_id":"0f1af928-8f85-4ec4-b6c7-5648fbdf2819","round_id":"round-2","tool_call_id":"skill_end:1","tool":"skill_end","result_id":"trs:0f1af928-8f85-4ec4-b6c7-5648fbdf2819:round2:skill_end:1"}}
```

## Deployment Checklist

- [x] Deploy Runtime.
- [x] Deploy App if UI mapping changes.
- [x] Verify a fresh production/staging tool call produces an execution log with `result_id`.
- [x] Verify App can open the result.

## GitHub / Commit Checklist

- [x] Commit Runtime changes.
- [x] Commit App changes if needed.
- [x] Commit parent submodule pointer updates.
- [x] PR description links this ticket and PR-86.
- [x] PR description includes one row sample and one UI/result smoke artifact.

## Acceptance Criteria

- Tool execution logs can drill into full results using TRS.
- Entangled row remains lightweight.
- App no longer needs to rely on `log-payloads.result` for normal tool output.

## Rollback

Rollback if result drilldown breaks or result ids are non-deterministic. Existing non-TRS rendering fallback must remain available during rollout.
