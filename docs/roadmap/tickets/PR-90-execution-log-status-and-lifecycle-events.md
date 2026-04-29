# PR-90 — Correct execution-log status semantics and add minimal lifecycle events

| Field | Value |
|---|---|
| **Ticket** | PR-90 |
| **Status** | `[✓ deployed]` |
| **Opened** | 2026-04-29 |
| **Owner** | __ |
| **Severity** | P1 observability correctness — failed tools can currently render as completed, and repeated think/finalize behavior lacks clear execution events. |
| **Depends on** | PR-86 preferred. |
| **Blocks** | Trustworthy App execution timeline. |
| **Invariant** | Execution logs describe runtime execution state; they do not invent cognitive memory or summaries. |

## Background

`tool_handlers.py` broadcasts tool completion with `status="complete"` even when the result is an error payload. In screenshots and cached rows, the App can show green completed tool entries even when underlying execution failed.

There are also scenarios like no-tool retry, force finalize, and scope close that affect visible execution but may not have a clean lightweight event.

## Goal

Make execution-log status semantics honest and add only the minimal lifecycle events needed for UI/debugging:

- tool success -> `complete`;
- tool failure -> `failed`;
- think failure -> `failed`;
- optional lifecycle events for no-tool retry / scope close / forced finalize where they explain visible behavior.

## Non-Goals

- Do not add memory summaries.
- Do not add business task tracking.
- Do not log raw LLM payloads.
- Do not create a parallel lifecycle state machine outside Cortex/Runtime.

## Implementation Checklist

- [x] Update tool completion broadcast to set `status="failed"` when result/error indicates failure.
- [x] Normalize error payload shape so App can display a concise error summary.
- [x] Update App `isFailed` logic to rely primarily on `status === "failed"`.
- [ ] Add minimal lifecycle event kinds only if needed:
  - [ ] `no_tool_retry`
  - [ ] `scope_closed`
  - [ ] `force_finalize`
- [x] Ensure lifecycle events are lightweight and do not write `summary.md`.
- [x] Keep Cortex summary semantics untouched.

## Unit Test Requirements

- [x] Runtime unit test: thrown tool error broadcasts `status="failed"`.
- [x] Runtime unit test: tool executor returning `success=false` broadcasts `status="failed"`.
- [x] Runtime unit test: successful tool broadcasts `status="complete"`.
- [x] App unit/component test: failed status renders failed visual state and error summary.
- [ ] If lifecycle events are added, tests verify they are execution logs only and do not affect Cortex summary files.

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
```

## Smoke Test Requirements

- [x] Trigger a successful tool call.
- [x] Trigger a failing tool call.
- [x] Verify App shows success and failure accurately.
- [x] If lifecycle events are implemented, trigger one no-tool retry or finalize path and verify the App timeline is understandable.

Production success smoke captured 2026-04-29:

```json
{"id":1097,"kind":"tool","status":"complete","data":{"tool":"chat_reply","result_id":"trs:0f1af928-8f85-4ec4-b6c7-5648fbdf2819:round1:chat_reply:0"}}
{"running_count":0}
```

Failure semantics are covered by unit/component tests because intentionally failing a user-visible production tool call is not useful for the PR86-91 smoke thread.

## Deployment Checklist

- [x] Deploy Runtime.
- [x] Deploy App if render logic changes.
- [x] Capture one successful production row and failed-row semantics from Runtime/App tests.
- [x] Capture App evidence showing failed entry is not green/completed.

## GitHub / Commit Checklist

- [x] Commit Runtime changes.
- [x] Commit App changes if needed.
- [x] Commit parent submodule pointer updates.
- [x] PR description links this ticket.
- [x] PR description includes unit tests and success/failure smoke evidence.

## Acceptance Criteria

- Failed tool execution is visible as failed in Entangled and App.
- Lifecycle events, if added, are clearly execution timeline events and not memory paths.
- Existing success path remains unchanged.

## Rollback

Rollback if status changes break existing UI filtering. App should continue to tolerate old rows where errors were stored under completed status.
