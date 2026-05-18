# Check: Cortex display step-result projection contract is explicit

## Summary

Success. The audit result maps the display step-result contract to concrete Cortex and runtime code paths, and the remaining legacy inline-data support is not a blocker because ordinary history/current projections suppress display media.

## Evidence

- Result `R578` cites the scan artifact `.complex-problems/L20260516-222011/tmp/p581/projection-contract-scan.txt`.
- `novaic-cortex/novaic_cortex/step_result_projection.py:119-120` confirms durable tool-step payloads are normalized through `llm_content`.
- `novaic-cortex/novaic_cortex/step_result_projection.py:142-188` confirms MCP media items are parsed into `display_files`, including BlobRef `image_ref` items.
- `novaic-cortex/novaic_cortex/step_result_projection.py:212-264` confirms media is emitted only when `include_display=True`, and BlobRef image media is emitted as `image_ref`, not as ordinary text.
- `novaic-cortex/novaic_cortex/step_result_projection.py:267-299` confirms history/current projection use `include_display=False` and display perception uses `include_display=True`.
- `novaic-cortex/novaic_cortex/api.py:1829-1856` confirms the formatted read API requires an explicit projection mode.
- `novaic-agent-runtime/task_queue/utils/step_result_client.py:124-125` confirms runtime resolves image refs only for `display_perception`.
- `novaic-agent-runtime/task_queue/utils/step_result_client.py:205-226` confirms only current-round `display` tool messages select `display_perception`.

## Criteria Map

- Records scan commands for projection code: satisfied by the p581 scan artifact and result references.
- Reads relevant Cortex/runtime bridge slices with line references: satisfied by the cited `step_result_projection.py`, `api.py`, and `step_result_client.py` line ranges.
- Classifies current perception and history projection behavior: satisfied; current `display` can expose media references for perception, while history/current non-display are bounded text/reference-only.
- Forwards ordinary-text replay leaks to P554: no ordinary-text replay path was found, so no follow-up to P554 is required.

## Execution Map

- `T583` executed as a read-only audit and produced `R578`.
- No implementation work was performed in this check step.
- The earlier implementation tickets under P584/P586 already removed the durable display-base64 path, so this problem only needed to verify the active projection contract.

## Stress Test

- Plausible failure mode: an old display step containing image data could be replayed into later LLM context as text.
- Observed behavior: history/current helpers call `_format_mcp_content(... include_display=False ...)`, so parsed display files are not injected into ordinary LLM text. Current-round display uses `display_perception` and runtime resolves BlobRefs into image content only at the provider boundary.

## Residual Risk

- Legacy `data:` image handling remains for explicitly inline visual content, but it is scoped to display perception and does not affect the shell/display BlobRef contract.
- The audit did not run new tests because this problem was a read-only projection audit; focused tests were already run in the parent implementation chain.

## Result IDs

- R578
