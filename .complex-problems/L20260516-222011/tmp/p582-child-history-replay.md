# Historical Display Replay Text-Only Test Coverage

## Problem

Verify that historical display tool results are covered by regression tests that prevent image bytes or visual MCP content from being replayed into later LLM context.

## Success Criteria

- Records exact `rg` scan commands and focused test commands for historical display replay.
- Cites tests proving historical `display` results use `history` projection instead of `display_perception`.
- Cites tests proving historical image refs remain text/reference-only and do not become image MCP content.
- Creates a concrete follow-up if historical replay coverage is missing or weak.
- Explains why this belongs under the display regression inventory split.
