# Cortex display projection preserves media references

## Problem

Cortex step-result projection currently understands data URLs as display images and degrades normal URLs to text. After runtime durable payloads become BlobRef-only, Cortex must preserve BlobRef display media references for `display_perception` while keeping history and summary projections text/reference-only.

## Success Criteria

- `parse_tool_result` recognizes explicit display media references such as `image_ref` or BlobRef-backed `display_files`.
- `format_for_display_perception_llm` can emit an unresolved image reference item without embedding base64.
- `format_for_history_llm` and preview paths remain text/reference-only.
- Shell/tool artifact manifest projection remains unchanged and does not become visual perception by accident.
