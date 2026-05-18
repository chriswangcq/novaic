# Result: Cortex workspace step payload persistence audited

## Summary

Cortex workspace persistence is pointer-based for tool payloads. `write_payload` persists payload records or external blob manifests, `normalize_step` rejects inline `result` for tool steps and externalizes any `payload` behind a required `payload_ref`, and `write_step` records `step_ref`/`payload_ref` into the durable step file and `_index.jsonl`.

## Done

- Mapped `write_payload`, `read_payload`, `normalize_step`, `write_step`, and `write_step_projection` in `novaic-cortex/novaic_cortex/workspace.py`.
- Verified `write_payload` stores either local JSON payload records or external blob references and writes operational payload manifests.
- Verified `normalize_step` rejects inline tool `result`, requires an observation percept, requires `payload_ref` when a payload is present, calls `write_payload`, and mirrors the actual `payload_ref` into step and observation metadata.
- Verified `write_step` writes compact step records and indexes `step_ref`/`payload_ref` rather than placing raw payload in the index.
- Ran focused Cortex persistence tests.

## Verification

- Code evidence: `novaic-cortex/novaic_cortex/workspace.py:563-621` for `write_payload` durable record/blob manifest behavior.
- Code evidence: `novaic-cortex/novaic_cortex/workspace.py:623-671` for `read_payload` by payload ref, including blob fetch path and manifest error updates.
- Code evidence: `novaic-cortex/novaic_cortex/workspace.py:700-736` for `normalize_step` rejecting inline `result` and externalizing payloads through required `payload_ref`.
- Code evidence: `novaic-cortex/novaic_cortex/workspace.py:738-789` for `write_step` and index entries preserving `step_ref`/`payload_ref`.
- Test command: `PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q novaic-cortex/tests/test_context_event_api_steps_write.py novaic-cortex/tests/test_step_index_outcome.py`.
- Test result: `28 passed in 0.43s`.

## Known Gaps

- This result covers Cortex workspace persistence only. Runtime/tool handler handoff is handled by sibling problem `P236`.

## Artifacts

- `novaic-cortex/novaic_cortex/workspace.py`
- `novaic-cortex/tests/test_context_event_api_steps_write.py`
- `novaic-cortex/tests/test_step_index_outcome.py`
