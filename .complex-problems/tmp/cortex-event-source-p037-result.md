# Verify tool step cutover boundaries result

## Summary

Audited the tool-step cutover boundary after P035/P036. Focused and full tests pass, and static scans show no remaining direct-only tool-result write path outside `steps_write -> ToolStepRecorded -> legacy write_step projection`.

## Done

- Re-ran focused tests for the step event path:
  - `tests/test_context_event_api_steps_write.py`
  - `tests/test_context_event_writer.py`
  - `tests/test_step_index_outcome.py`
- Re-ran the full Cortex suite.
- Scanned Cortex runtime code for:
  - `write_step(` call sites;
  - direct `steps/_index.jsonl` writes;
  - `steps/*.json` and `payloads/*.json` path writes.
- Classified remaining write sites:
  - `novaic_cortex/api.py:steps_write` is the only runtime `write_step(` caller and now emits `ToolStepRecorded` first.
  - `Workspace.write_step` is the transitional file projection behind the event path.
  - `Workspace.write_payload` / `read_payload` are payload-store support for final event payload refs.
  - `Workspace.create_scope` still initializes child scope `steps/_index.jsonl` and parent scope index rows; that belongs to skill/scope lifecycle cutover, not tool result bypass.
  - Read/format/preview endpoints inspect legacy step files for transitional compatibility and do not write tool results.

## Evidence

- Static scan: `rg -n "write_step\\(" novaic_cortex -g '*.py'` returned only `Workspace.write_step` and `api.py:steps_write`.
- Static scan: `rg -n "_sys_write_json\\([^\\n]*(steps|payloads)|_sys_append_line\\([^\\n]*steps|steps/_index\\.jsonl|/payloads/" novaic_cortex -g '*.py'` returned only Workspace scope/index/payload support paths.
- Focused tests: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest tests/test_context_event_api_steps_write.py tests/test_context_event_writer.py tests/test_step_index_outcome.py -q` → `23 passed`.
- Full suite: `PYTHONPATH=../novaic-logicalfs:../novaic-sandbox-sdk pytest -q` → `445 passed`.

## Residual Risk

- Scope lifecycle still has legacy child-scope index writes; P027 owns the event cutover for skill begin/end lifecycle.
- Legacy step read endpoints remain by design until read cutover and cleanup phases.
- No P037 follow-up is required for tool-step write bypass.
