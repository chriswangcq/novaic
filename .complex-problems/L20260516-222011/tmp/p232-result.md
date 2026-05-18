# Result: Cortex event projection payload pointer boundary audited

## Summary

Cortex event writer/projection preserves payload pointers and compact observations without expanding durable payload bodies into default event projections. `ToolStepRecorded` events carry observation plus optional `step_ref`/`payload_ref`; projection emits tool messages using observation preview/summary/head and metadata refs. Focused event tests passed.

## Done

- Mapped `ContextEventWriter.tool_step_recorded` in `context_event_writer.py`.
- Mapped `_tool_result_message` and `_tool_result_content` in `context_event_projection.py`.
- Verified event writer payload includes `step_ref`/`payload_ref` only as metadata fields and does not include raw durable payload bodies.
- Verified projection content is derived from observation preview/summary/head/stable JSON, with lookup refs kept in `step_ref` and `_metadata`.
- Ran focused Cortex event tests.

## Verification

- Code evidence: `novaic-cortex/novaic_cortex/context_event_writer.py:201-239` appends `ToolStepRecorded` with call/tool/status/observation and optional `step_ref`/`payload_ref`.
- Code evidence: `novaic-cortex/novaic_cortex/context_event_projection.py:350-380` projects tool messages with compact content and pointer metadata.
- Code evidence: `novaic-cortex/novaic_cortex/context_event_projection.py:383-390` selects observation `preview`, `summary`, or `head` before stable JSON; no full payload read happens here.
- Test evidence: `novaic-cortex/tests/test_context_event_projection.py:604-686` preserves order, `payload_ref`, and stable `step_ref` for externalized payloads.
- Test evidence: `novaic-cortex/tests/test_context_event_api_steps_write.py:101-249` covers ToolStepRecorded event payloads, inline-result rejection, external blob payload refs, and payload manifests.
- Test command: `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_projection.py novaic-cortex/tests/test_context_event_api_steps_write.py`.
- Test result: `35 passed in 0.34s`.

## Known Gaps

- Runtime LLM expansion after event projection is handled by sibling `P233`.
- Workspace payload persistence is already covered by `P235`.

## Artifacts

- `novaic-cortex/novaic_cortex/context_event_writer.py`
- `novaic-cortex/novaic_cortex/context_event_projection.py`
- `novaic-cortex/tests/test_context_event_projection.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
