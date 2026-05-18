# PR-89 — Expose LLM Factory log join key in think execution logs

| Field | Value |
|---|---|
| **Ticket** | PR-89 |
| **Status** | `[✓ deployed]` |
| **Opened** | 2026-04-29 |
| **Owner** | __ |
| **Severity** | P2 observability simplification — raw LLM calls already belong to LLM Factory; Entangled should only expose the drilldown key. |
| **Depends on** | PR-86 preferred. |
| **Blocks** | Removing accidental raw LLM duplication from execution-log payloads. |
| **Invariant** | LLM Factory is the source of truth for raw LLM request/response; Entangled stores only execution event metadata and optional preview. |

## Background

`llm_handlers.py` currently broadcasts think input payload containing full `messages`, `model`, `tools`, and `provider`. The LLM Factory response already carries `x_factory.log_id`, and the user has confirmed that raw LLM calls can be fetched directly from LLM Factory.

Keeping full LLM request bodies in Entangled was therefore unnecessary and risked another duplicated log system. The later PR-166C cleanup retired the remaining `log-payloads` backend path.

## Goal

Project a Factory join key into think execution-log metadata:

```json
{
  "type": "think",
  "scope_id": "...",
  "round_id": "round-2",
  "factory_log_id": "..."
}
```

The App can use this for drilldown into Factory when needed, while Entangled remains the realtime execution-log index.

## Non-Goals

- Do not build a second LLM-call viewer inside Entangled.
- Do not store raw LLM messages/tools in execution-log stream rows.
- Do not delete reasoning preview if it is useful and intentionally lightweight.

## Implementation Checklist

- [x] Extract `x_factory.log_id` from successful LLM Factory responses.
- [x] Include `factory_log_id` in think completion log `data`.
- [x] Consider including `factory_log_id` in failed think logs if Factory returns one for failures.
- [x] Stop storing full raw LLM request payload in Entangled; PR-166C later removed the retired `log-payloads` path entirely.
- [x] App displays a "Factory log" drilldown affordance when `factory_log_id` exists.
- [x] Keep reasoning preview in execution logs if it remains small and intentionally user-facing.

## Unit Test Requirements

- [x] Runtime unit test: Factory response with `x_factory.log_id` produces think log metadata with `factory_log_id`.
- [x] Runtime unit test: no `factory_log_id` gracefully falls back without crashing.
- [x] Runtime regression test: Entangled does not receive full raw LLM body when Factory id is available.
- [x] App component test: think log with `factory_log_id` exposes a drilldown affordance.

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

- [x] Send a message that triggers one LLM call.
- [x] Verify Factory recorded the call.
- [x] Verify execution-log row contains `factory_log_id`.
- [x] Verify App can navigate/open/copy the Factory log reference.
- [x] Verify Entangled row/payload does not duplicate the full raw LLM request unless explicitly configured.

Production smoke captured 2026-04-29:

```json
{"id":1096,"kind":"think","status":"complete","data":{"type":"think","scope_id":"0f1af928-8f85-4ec4-b6c7-5648fbdf2819","round_id":"round-1","model":"kimi-k2.5","provider":"factory","message_count":11,"tool_count":9,"factory_log_id":"37c85675-36e6-4fbb-b6c4-da68d7b626a0"}}
{"id":1098,"kind":"think","status":"complete","data":{"type":"think","scope_id":"0f1af928-8f85-4ec4-b6c7-5648fbdf2819","round_id":"round-2","model":"kimi-k2.5","provider":"factory","message_count":13,"tool_count":9,"factory_log_id":"03000fa3-6262-4dea-aa6a-50bd0960ef7c"}}
```

## Deployment Checklist

- [x] Deploy Runtime.
- [x] Deploy App if Factory drilldown UI changes.
- [x] Confirm production/staging think row includes `factory_log_id`.
- [x] Confirm Factory can retrieve the referenced raw call.

## GitHub / Commit Checklist

- [x] Commit Runtime changes.
- [x] Commit App changes if any.
- [x] Commit parent submodule pointer updates.
- [x] PR description links this ticket.
- [x] PR description includes one Factory id sample and one Entangled row sample.

## Acceptance Criteria

- Entangled think logs link to Factory instead of duplicating Factory.
- Raw LLM request/response source of truth is unambiguous.
- App still has enough information to explain "Thinking" entries.

## Rollback

Rollback if Factory id extraction is unreliable or the UI loses necessary think details. Keep compatibility fallback for logs without `factory_log_id`.
