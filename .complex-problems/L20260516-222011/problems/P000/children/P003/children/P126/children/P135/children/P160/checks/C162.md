# Runtime Cortex prepare handler contract map check

## Summary

`P160` is solved. Its split children cover both sides of the runtime prepare boundary: the handler response shape (`P166`) and the bridge HTTP endpoint contract (`P167`). The evidence shows provider messages come from the prepared Cortex snapshot, while `read_context` remains a separate notification/projection path and is not used as LLM message authority.

## Evidence

- `C160` maps `cortex_handlers.py:296-356` and `llm_assembly.py:115-139`, `llm_assembly.py:233-273`.
- `C160` records handler tests with `31 passed` and classifies `handle_context_read` as notification-hint ingestion, not provider-message authority.
- `C161` maps `cortex_bridge.py:474` and `cortex_bridge.py:482`, adds a direct endpoint regression at `test_runtime_explicit_contracts.py:304`, and records `26 passed`.
- `R148` summarizes closed child results `R146` and `R147`.

## Criteria Map

- Handler and bridge mapped around `prepare_for_llm`: satisfied by `C160` and `C161`.
- Response fields documented: satisfied by `C160`, including messages, tools, active stack metadata, warning, and provider payload fields.
- Fallback to `read_context` or local continuity classified/fixed: satisfied by `C160` and `C161`; no active provider-message fallback remains in handler/bridge prepare path.
- Focused tests identified/run: satisfied by child test evidence (`31 passed`, `26 passed`).

## Execution Map

- `T150` was classified as split.
- `P166` closed handler response shape with `R146` and `C160`.
- `P167` closed bridge endpoint contract with `R147` and `C161`.
- Parent result `R148` consolidates both child outcomes.

## Stress Test

The combined checks cover two plausible regressions: handler code accidentally using `context.read` as provider authority, and bridge code accidentally posting prepare requests to `/v1/context/read` or mutating the returned snapshot. Existing and newly added tests would fail on those paths.

## Residual Risk

- `P160` does not attempt to prove the entire runtime LLM payload handoff or all historical continuity residue is clean. Those are deliberately separate sibling problems (`P161`, `P162`, `P163`) and remain open.

## Result IDs

- R148
