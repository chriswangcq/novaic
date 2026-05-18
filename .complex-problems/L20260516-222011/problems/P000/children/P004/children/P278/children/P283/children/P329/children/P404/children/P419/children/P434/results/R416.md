# Result: P434 / T423 Cortex API surface cleanup

## Summary

Audited the Cortex API surface. Endpoint inventory and focused API tests passed. No unclassified API bypass remains inside this ticket; the live materialized context endpoints are classified and routed to P436 for bridge usage review.

## Verification

- Focused test command:
  - `PYTHONPATH=.:../novaic-common:../novaic-logicalfs:../novaic-sandbox-sdk pytest -q tests/test_context_event_api_lifecycle.py tests/test_context_event_api_skill_lifecycle.py tests/test_context_event_api_steps_write.py tests/test_context_event_api_context_writes.py tests/test_payload_inspection_api.py tests/test_context_event_read_source_guards.py`
- Result: `47 passed in 0.60s`

## API Surface Classification

- Scope lifecycle: `/v1/scope/create`, `/v1/scope/end`, `/v1/scope/history`; verified by P418/P432.
- Event/read model context: `/v1/context/prepare_for_llm`, `/v1/context/status`; event-backed and no-DFS guarded.
- Materialized context projection: `/v1/context/read`, `/v1/context/append`, `/v1/context/batch`; live projection API that appends ContextEvent records and context projection. Runtime bridge usage is assigned to P436.
- Skill lifecycle: `/v1/context/skill_begin`, `/v1/context/skill_end`; explicit stack projection and ContextEvent writer.
- Steps: `/v1/steps/write`, `/v1/steps/read_formatted`, `/v1/steps/read_preview`; payload-ref and explicit projection-mode based.
- Payload inspection: `/v1/payload/read`, `/v1/payload/search`, `/v1/payload/summarize`, `/v1/payload/qa`; explicit payload_ref only.
- Internal tools/shell/reindex/token/health/metrics/ready: operational/internal surfaces.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p434/api-surface-inventory.txt`
- `.complex-problems/L20260516-222011/tmp/p434/focused-pytest.with-status.txt`
- `.complex-problems/L20260516-222011/tmp/p434/api-context-endpoints-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p434/api-steps-write-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p434/api-payload-endpoints-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p434/context-projection-callers.txt`
- `.complex-problems/L20260516-222011/tmp/p434/runtime-context-handlers-slice.txt`
- `.complex-problems/L20260516-222011/tmp/p434/runtime-cortex-bridge-context-slice.txt`

## Residual Routing

The API endpoint inventory shows runtime bridge callers still use materialized context projection endpoints. Whether those should be retained, replaced, or narrowed is explicitly routed to P436, the bridge surface cleanup ticket.
