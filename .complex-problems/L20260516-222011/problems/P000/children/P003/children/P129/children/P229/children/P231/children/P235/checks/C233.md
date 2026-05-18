# Check: Cortex workspace step payload persistence is pointer-based

## Summary

`P235` is solved by `R219`. The workspace persistence code and focused tests prove that tool payloads are stored through durable payload records/manifests and that step/index records preserve `step_ref`/`payload_ref` pointer metadata. The sibling runtime handoff boundary remains outside this problem and is not used to inflate this success claim.

## Evidence

- `novaic-cortex/novaic_cortex/workspace.py:563-621` writes payload records or external blob manifests and stores operational payload manifest metadata.
- `novaic-cortex/novaic_cortex/workspace.py:700-736` rejects inline tool `result`, requires observation percepts, requires `payload_ref` for payload writes, calls `write_payload`, and mirrors actual `payload_ref` into normalized step/observation.
- `novaic-cortex/novaic_cortex/workspace.py:738-789` writes step files and indexes `step_ref`/`payload_ref` in `_index.jsonl`.
- Targeted tests passed: `28 passed in 0.43s` for `test_context_event_api_steps_write.py` and `test_step_index_outcome.py`.

## Criteria Map

- Active tool handler to Cortex write path is mapped with file/function pointers: satisfied for the Cortex workspace side by `write_payload`, `normalize_step`, `write_step`, and `write_step_projection`; runtime handoff is explicitly delegated to `P236`.
- Step write implementation evidence shows `payload_ref`/`step_ref` are required, generated, or preserved for heavy tool output: satisfied by `normalize_step` requiring `payload_ref` and `write_step` indexing refs.
- Tests or focused probes verify durable payload refs are emitted for representative shell/display-like output: satisfied by the 28 focused Cortex tests covering step write/index and payload ref behavior.

## Execution Map

- Ticket `T224` ran a bounded one-go workspace-only audit.
- Execution inspected workspace persistence code and ran the focused Cortex persistence tests.
- Result `R219` recorded code pointers, test command, test result, and the sibling boundary gap.

## Stress Test

The main failure mode would be a tool step silently accepting inline `result` and bypassing durable payload refs. The code directly rejects `result` on tool steps and requires observation + `payload_ref` for payload writes, while tests include error expectations around missing `payload/payload_ref` and assertions that index/step metadata contains `payload_ref`.

## Residual Risk

Non-blocking for `P235`: runtime tool handlers could still hand off incorrectly before reaching workspace persistence. That is the explicit scope of `P236` and remains open.

## Result IDs

- `R219`
