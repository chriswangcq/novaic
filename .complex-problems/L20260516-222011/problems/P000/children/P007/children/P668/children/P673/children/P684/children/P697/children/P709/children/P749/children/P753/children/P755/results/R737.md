# Runtime Queue Cortex service-code residue discovery result

## Summary

Completed a read-only discovery scan over Runtime/Queue/Cortex code. No service code was modified in this ticket.

The Runtime/Queue/Cortex code is mostly in the desired shape: direct/fallback/legacy hits are predominantly guardrail tests proving old paths stay deleted, while active shell/display/context paths enforce bounded text, Blob manifests, and explicit display projection.

## Scans Performed

- `rg -n -i "(legacy|compat|fallback|old path|old logic|deprecated|shadow|direct|bypass|TODO|FIXME)" novaic-agent-runtime novaic-cortex --glob '*.py'`
- `rg -n -i "(base64|display|image_url|input_image|mcp_content|tool-output|artifact|blob://|payload_ref|sandbox|logicalfs|/cortex/ro|/cortex/rw|novaic-cortex-sandbox)" novaic-agent-runtime novaic-cortex --glob '*.py'`
- Spot-read:
  - `novaic-cortex/novaic_cortex/step_result_projection.py`
  - `novaic-cortex/novaic_cortex/sandbox.py`
  - `novaic-agent-runtime/task_queue/tool_surface_policy.py`
  - `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`

## Classification

Current and acceptable:
- Runtime tool surface policy keeps only final harness tools as direct Runtime executors and classifies migrated interface tools as shell capabilities.
- Cortex sandbox code now composes `MountNamespaceLogicalFS` with a sandboxd SDK executor, rejects ephemeral `novaic-cortex-sandbox-*` backing paths, and fails explicitly if sandboxd is not configured.
- Queue/session/saga legacy/fallback/direct hits are mostly tests that assert old paths remain deleted.
- Cortex context/event/projection tests verify history remains text/manifest-only and display perception is explicit.

Remediation candidates:
- `novaic-agent-runtime/task_queue/utils/cortex_bridge.py`: module docstring says “Cortex is the single gateway to agent storage.” That is stale/too broad after LogicalFS/Blob separation. It should say Cortex is the HTTP boundary for scope/context/tool observation semantics, while bytes/file authority follow Cortex/LogicalFS/Blob contracts.
- `novaic-cortex/novaic_cortex/step_result_projection.py`: `parse_tool_result()` still accepts direct MCP `{"type": "image", "data": ...}` and converts it to a `data:*;base64,...` display file; `format_for_display_perception_llm()` then converts data URLs to provider image content. This does not leak into history/current non-display projections, but it is a compatibility surface for direct inline image data. If the final desired contract is BlobRef-only display/media inputs, this should be removed or narrowed in the remediation child with tests updated.

Intentional survivors:
- `base64` in auth/token or provider multimodal tests is not a shell/history artifact leak.
- `direct` and `legacy` in guardrail tests are intentional assertions.
- `payload_ref` and `blob://` handling in Cortex payload and projection code is current contract.

## Verification

This child produced classification only. Runtime/Queue/Cortex code changes should be handled by the remediation child, then verified with focused tests around `test_tool_output_projection.py`, `test_step_result_projection.py`, `test_no_historical_tool_image_injection.py`, `test_tool_handlers_display_chat_history.py`, and relevant CortexBridge/runtime boundary tests.
