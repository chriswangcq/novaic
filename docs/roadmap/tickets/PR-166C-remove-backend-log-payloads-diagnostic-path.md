# PR-166C — Remove Backend `log-payloads` Diagnostic Payload Path

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Owner | Codex |
| Created | 2026-05-02 |
| Parent | PR-166 |
| Repos | `novaic-common`, `novaic-business`, `novaic-agent-runtime`, `novaic-app`, docs |

## Goal

Physically remove the remaining backend `log-payloads` entity/action/write path so the normal Agent Monitor cannot grow back into a raw execution payload inspector.

## Current-State Analysis

PR-154A removed the App-side lazy payload cache and App entity contract, but the backend still has an active diagnostic branch:

- Common still declares `log-payloads` in `entangled_app_entities.json`.
- Business still registers `LOG_PAYLOADS_DEF` and `log-payloads.get_payload`.
- `/internal/logs/broadcast` still writes `input` / `result` / `error` into `execution_log_payloads`.
- Business tests still preserve the old lazy-fetch action.
- App contract tests still expect the backend schema to contain `log-payloads` even though App does not consume it.

## Implementation Plan

1. Remove `log-payloads` from the shared Entangled App entity contract.
2. Remove `LOG_PAYLOADS_DEF`, `ENTITY_ACTIONS["log-payloads"]`, and Business action registration.
3. Remove `get_payload_action`; keep only `execution-logs.clear`.
4. Change `/internal/logs/broadcast` to discard heavy diagnostic `input` / `result` / `error` instead of writing `log-payloads`.
5. Stop Runtime from sending `input_data` / `result_data` to the execution-log broadcast API; monitor rows must be lightweight at source.
6. Replace old PR-88 tests with guardrails that assert `log-payloads` is absent from active schema/actions and broadcast logging does not write it.
7. Update docs that described `log-payloads` as an active path; keep historical ticket notes only when explicitly marked retired.

## Unit / Guardrail Tests

- [x] Common/App contract test: backend App contract no longer declares `log-payloads`.
- [x] Business schema test: `log-payloads` is absent from `ALL_BUSINESS_ENTITIES` and `ENTITY_ACTIONS`.
- [x] Business action test: `execution-logs.clear` only deletes `execution-logs`.
- [x] Business broadcast test: `input_data` / `result_data` do not create `log-payloads` writes.
- [x] Runtime test: execution-log broadcasts no longer include raw `input_data` / `result_data`.

## Smoke / Deploy / Git

- [x] Run focused Common/App/Business tests.
- [x] Run full Business/Runtime/Common tests and App build.
- [x] Deploy affected services.
- [x] Smoke remote schema/action/source absence.
- [ ] Commit each affected repo and parent pointer/docs.

## Evidence

Focused tests:

```bash
cd novaic-common && PYTHONPATH=. pytest -q \
  tests/test_pr166c_entangled_app_entities.py \
  tests/test_execution_log_display_contract.py
# 3 passed

cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr166c_no_log_payloads.py \
  tests/test_schema_invariants.py
# 8 passed, 1 warning

cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q \
  tests/test_pr86_execution_log_metadata.py \
  tests/unit/task_queue/test_tool_handlers_failure_event.py
# 9 passed

cd novaic-app && npm run test:unit -- --run \
  src/data/entities/entangledEntityContracts.test.ts \
  src/components/Visual/executionLogUtils.test.ts \
  src/components/Visual/ExecutionLog.test.tsx \
  src/components/hooks/useLogs.test.ts
# 4 files, 17 tests passed
```

Full/affected validation:

```bash
cd novaic-common && PYTHONPATH=.:../novaic-agent-runtime pytest -q
# 120 passed

cd novaic-business && PYTHONPATH=.:../novaic-common pytest -q
# 196 passed, 2 warnings

cd novaic-agent-runtime && PYTHONPATH=.:../novaic-common pytest -q
# 198 passed

cd novaic-app && npm run build
# passed; existing Vite dynamic-import/chunk-size warnings only
```

Deploy / smoke:

```bash
./deploy services
# all backend services restarted healthy

./deploy status
# ports 19900/19999/19998/19993/19997/19995/19996 healthy; relay active
```

Remote source smoke:

```text
Business: has_log_payloads_entity False; has_log_payloads_action False
Business internal log source: no log-payloads / execution_log_payloads / input_data / result_data
Runtime broadcast/client/tool/llm source: no input_data= / result_data=
```

## Acceptance Criteria

- [x] `rg "log-payloads|get_payload|execution_log_payloads"` only finds historical/retired documentation or guardrail tests, not active code paths.
- [x] Entangled schema push no longer registers `log-payloads`.
- [x] Runtime log broadcast source no longer sends raw monitor payload fields.
- [x] No normal user-facing path can lazy-fetch raw execution payloads from Business.
