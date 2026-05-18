# P179 success check

## Summary

P179 is successful. Result R164 does not add production code, but it provides a focused cross-layer audit and two focused regression suites proving the externalized-payload contract: stable `step_ref` remains the lookup handle, final `payload_ref` can become an external blob ref, public context stays manifest/text-only, and display/media projection is scoped to the current display perception path.

## Evidence

- R164 reviewed the production handoff points that can conflate `step_ref` and `payload_ref`:
  - runtime action bridge: `novaic-agent-runtime/task_queue/contracts/react_actions.py`
  - runtime Cortex bridge: `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
  - step-result expansion: `novaic-agent-runtime/task_queue/utils/step_result_client.py`
  - Cortex step lookup/read: `novaic-cortex/novaic_cortex/api.py`
  - event projection: `novaic-cortex/novaic_cortex/context_event_projection.py`
  - event writer idempotency: `novaic-cortex/novaic_cortex/context_event_writer.py`
  - payload manifest/externalization: `novaic-cortex/novaic_cortex/workspace.py`
- Existing regression coverage explicitly includes the dangerous paths:
  - `test_steps_write_records_deepest_scope_and_final_blob_payload_ref`
  - `test_steps_read_formatted_resolves_externalized_payload_by_stable_step_ref`
  - `test_steps_write_emits_tool_step_recorded_without_fake_payload_ref`
  - `test_write_step_externalizes_payload_and_indexes_payload_ref`
  - `test_write_step_externalizes_large_payload_to_blob_ref`
  - `test_project_context_events_uses_stable_step_ref_when_payload_is_externalized`
  - `test_no_historical_tool_image_injection`
  - shell/tool output contract tests that keep CLI output manifest/text-only.
- Focused Cortex suite passed: `80 passed in 0.55s`.
- Focused runtime suite passed: `62 passed in 0.19s`.

## Criteria Map

- Inventory tests covering externalized payload refs, artifact refs, public truncation, and display/media projection: satisfied by the explicit test inventory in R164 and the two focused test runs.
- Add missing tests that fail if `step_ref` and `payload_ref` are conflated: satisfied without adding new tests because R164 identified existing tests that already fail on that conflation, especially stable-step lookup with final blob payload refs and historical image non-injection.
- Classify compatibility or legacy branches as active, dead, or stale; remove/fix stale branches where in scope: satisfied. R164 classified the suspicious fallbacks as active-safe, not stale; no removal was in scope because removal would break explicit payload-ref lookup or old event replay.
- Run selected focused runtime and Cortex tests after changes/audit: satisfied. Both suites passed.

## Execution Map

- T168 executed a read-only source audit plus regression test run.
- R164 records no production-code changes, because the audit found no active defect after P176/P177/P178 completed the layer-specific contract checks.
- The known gap is documentation/readability risk only: some fallback expressions can look like legacy compatibility. This is non-blocking for correctness because tests cover the semantics.

## Stress Test

The critical stress case is a tool step whose stable `step_ref` differs from its final `payload_ref` after payload externalization to `blob://cortex-payload/...`. The suite includes explicit tests for stable `step_ref` formatted read in that condition, plus no historical display image injection into later LLM context. That covers the original regression class seen in the product: large media/base64 or blob-like payloads must not re-enter future context as raw text, while current display perception can still resolve the image deliberately.

## Residual Risk

- Non-blocking: the fallback branches are semantically safe but visually ambiguous to future maintainers. If the project later deletes all historical replay support, those fallbacks can be simplified in a separate cleanup ticket.
- No current correctness or integration risk found for the externalized-payload contract.

## Result IDs

- R164
