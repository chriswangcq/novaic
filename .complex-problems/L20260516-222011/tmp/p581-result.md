# Result: Cortex display step-result projection contract audit

## Summary

The projection contract is now explicit and split by purpose: history/default projections remain text/reference-only, while the current-round `display` tool uses the `display_perception` projection to carry BlobRef image references that runtime resolves into provider image content immediately before the LLM call.

## Done

- Audited the Cortex step-result projection entry points and runtime read path.
- Confirmed `tool-step-payload.v1` is parsed through `llm_content`, so durable tool step payloads are normalized before LLM injection.
- Confirmed tri-shape parsed output is `text`, `files_created`, and `display_files`; display media is not ordinary text by default.
- Confirmed MCP content parsing recognizes `image`, `image_ref`, and `resource`; BlobRef images are represented as `display_files`, not pasted as base64 text.
- Confirmed display formatting emits `image_ref` for BlobRef image files in `display_perception`, while history/current projections call with display disabled.
- Confirmed `/v1/steps/read_formatted` selects one of only three explicit projections: `history`, `current_tool_result`, or `display_perception`.
- Confirmed runtime resolves `image_ref` only when the selected projection is `display_perception`.

## Verification

- Evidence artifact: `.complex-problems/L20260516-222011/tmp/p581/projection-contract-scan.txt`.
- Key code evidence:
  - `novaic-cortex/novaic_cortex/step_result_projection.py:119-120` routes `tool-step-payload.v1` through `llm_content`.
  - `novaic-cortex/novaic_cortex/step_result_projection.py:126-139` preserves `display_files` as the media side channel.
  - `novaic-cortex/novaic_cortex/step_result_projection.py:142-188` parses MCP `image`, `image_ref`, and `resource`.
  - `novaic-cortex/novaic_cortex/step_result_projection.py:212-264` only emits display media when `include_display=True`, and emits BlobRefs as `image_ref`.
  - `novaic-cortex/novaic_cortex/step_result_projection.py:267-294` separates history/current/display projection helpers.
  - `novaic-cortex/novaic_cortex/api.py:1829-1856` exposes explicit projection selection through `/v1/steps/read_formatted`.
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py:124-125` resolves image refs only for `display_perception`.
  - `novaic-agent-runtime/task_queue/utils/step_result_client.py:205-226` selects `display_perception` only for current-round `display` tool messages.

## Known Gaps

- No new blocker found in this audit. The earlier display durable-base64 leak was already handled by the P584/P586 child work.
- Legacy explicit `data:` image URLs are still supported intentionally for compatibility with already-inline visual content, but the shell/display BlobRef path no longer depends on that shape.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p581/projection-contract-scan.txt`
