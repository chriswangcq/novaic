# Cortex step storage ref contract mapped

## Summary

Mapped Cortex step storage/projection refs. The storage layer already distinguishes stable `step_ref` from actual `payload_ref`: incoming steps may use `payload_ref == step_ref`, but `Workspace.normalize_step` writes the payload, receives an actual payload ref, updates `step.payload_ref`, mirrors it into `observation.payload_ref`, and preserves `step.step_ref` as the stable lookup identity.

## Source Map

- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`
  - `write_tool_step(...)` seeds `step_ref` and initial `payload_ref` with the stable step ref before calling `/v1/steps/write`.
  - This is a request-side default, not final storage authority.
- `novaic-cortex/novaic_cortex/workspace.py`
  - `write_payload(...)` persists local JSON payloads or externalizes large payloads via blob client, returning the actual payload ref.
  - `normalize_step(...)` rejects inline `result`, requires `payload_ref`, computes `stable_step_ref`, writes payload, updates final `payload_ref`, and mirrors the final ref into `observation.payload_ref`.
  - `write_step(...)` writes the normalized step and indexes `step_ref`, final `payload_ref`, duration, tool, and artifact presence.
  - `read_step_index(...)` raises on corrupt JSONL instead of silently ignoring bad index state.
- `novaic-cortex/novaic_cortex/api.py`
  - `/v1/steps/write` normalizes before writing `ToolStepRecorded`; event payload receives normalized `step_ref` and final `payload_ref`.
  - `_find_step_by_call_id_in_path(...)` can locate by stable `step_ref` even if index `payload_ref` is now a blob ref.
  - `_read_step_payload(...)` reads by final `payload_ref`.
- `novaic-cortex/novaic_cortex/context_event_writer.py`
  - `tool_step_recorded(...)` records both optional `step_ref` and `payload_ref`.
- `novaic-cortex/novaic_cortex/context_event_projection.py`
  - Tool-result messages expose metadata with both refs and use stable `step_ref` as the preferred lookup ref when present.

## Contract

- `step_ref`: stable tool-step identity and lookup key derived from scope/round/tool-call.
- `payload_ref`: final payload storage identity after Cortex normalization; may equal `step_ref` for local payloads or become a blob/external payload ref.
- `source_payload_ref`: manifest link back to the original stable ref when payload is externalized.
- `observation.payload_ref`: must mirror the final payload ref so monitors/context hints point at the actual payload storage.

## Verification

Initial combined Cortex+runtime test command hit a test package import collision, so the suites were rerun separately:

```bash
PYTHONPATH=novaic-cortex:novaic-common:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-cortex/tests/test_step_index_outcome.py \
  novaic-cortex/tests/test_context_event_api_steps_write.py \
  novaic-cortex/tests/test_context_event_api_context_writes.py \
  novaic-cortex/tests/test_context_event_writer.py
```

Result: `41 passed in 0.43s`.

```bash
PYTHONPATH=novaic-agent-runtime:novaic-common:novaic-cortex:novaic-logicalfs:novaic-sandbox-sdk pytest -q \
  novaic-agent-runtime/tests/test_runtime_explicit_contracts.py
```

Result: `13 passed in 0.11s`.

## Findings

- No production code change was needed for this storage leaf.
- Existing tests already cover final blob payload refs, source payload refs, stable step refs, manifest status, artifacts in indexes, and corrupt JSONL fail-closed behavior.
- The request-side `CortexBridge.write_tool_step` still seeds `payload_ref == step_ref`; this is acceptable because Cortex normalization is final authority and is already guarded.

## Residual Notes

Formatted read/display projection is intentionally left to sibling P178, because it tests whether stable lookup still resolves the actual payload in the LLM expansion path.
