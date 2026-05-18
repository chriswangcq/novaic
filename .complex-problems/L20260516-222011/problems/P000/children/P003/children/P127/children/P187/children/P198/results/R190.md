# Projection branch inventory and classification parent result

## Summary

Completed projection branch inventory across Cortex, runtime/factory, and tests. The inventory found one stale production/test island and one active provider gap.

## Child Results

- `R185` / `P202`: Cortex projection branch inventory.
- `R188` / `P203`: Runtime and factory projection branch inventory.
- `R189` / `P204`: Projection test branch inventory.

## Consolidated Classifications

- Active:
  - `tool-output.v1` artifact manifest projection.
  - Explicit `history`, `current_tool_result`, and `display_perception` step projections.
  - Runtime `_projection` marker and display-only image conversion.
  - Shell bounded terminal text with durable raw payload.
  - OpenAI structured `image_url` preservation.
  - Anthropic `image_url` -> native image source conversion.
  - Factory log redaction preserving structured shape.
- Compatibility / defensive:
  - Cortex nested `result` unwrapping.
  - Cortex generic dict JSON fallback.
  - Runtime latest-tool-call fallback for missing `_round_id`.
  - Runtime generic unstructured executor fallback.
  - Negative tests for legacy content/nested wrappers that assert they do not become image projections.
- Stale candidates:
  - `novaic-cortex/novaic_cortex/step_result_projection.py:330-415` `resolve_for_llm`.
  - `novaic-cortex/tests/test_resolve_for_llm.py`.
- Active gap:
  - Google/Gemini provider does not preserve/convert multimodal request list content.

## Downstream Work Required

- Remove stale `resolve_for_llm` production helper and tests if cleanup verification confirms no live callers.
- Fix Google/Gemini multimodal request conversion and add tests.
- Re-check generic fallback/nested wrapper branches and remove only if no persisted-data or safety role remains.

## Code Changes

None. This parent ticket summarized inventory child results.
