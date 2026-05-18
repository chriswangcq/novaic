# Check P422 against R402

## Verdict

success

## Skeptical Review

P422 found a live projection leak risk and patched the actual projection path, not just tests. The dangerous fallback `stable_json(observation)` was removed from `_tool_result_content()`, so unknown dict observations can no longer dump embedded media/base64 payloads into LLM history.

## Criteria Review

- Projection/read-model inspected: satisfied by saved source inspections.
- Remaining generation/archive/context hits classified or patched: the relevant payload projection leak was patched; other read-model behavior remains focused and tested.
- LLM context projection remains pointer-oriented: satisfied by the new fallback using `payload_ref` and observation keys only.
- Dangerous compatibility behavior patched: yes, unknown dict observation full serialization was removed.
- Focused tests pass: satisfied by `53 passed`.

## Stress Test

The test uses image-shaped `_mcp_content` with a large base64-like payload and verifies the projected content includes `payload_ref` and keys but excludes `/9j/` and repeated base64 data. This directly targets the failure mode seen earlier.

## Residual Risk

Workspace step payload normalization and API/display-current projection are not closed by P422; they remain in sibling P423/P424.

## Evidence

- Diff in `novaic-cortex/novaic_cortex/context_event_projection.py`.
- New test `test_project_context_events_unknown_tool_observation_does_not_inline_payload`.
- Focused pytest: `53 passed in 0.13s`.
- Post-fix guard: no `stable_json(observation)` fallback remains.
