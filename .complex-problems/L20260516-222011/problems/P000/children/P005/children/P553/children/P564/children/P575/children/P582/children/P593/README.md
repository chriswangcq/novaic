# Current Display Image Injection Test Coverage

## Problem

Verify that current-round `display` tool results are covered by regression tests that prove BlobRef image references are resolved into provider image content for the active LLM call.

## Success Criteria

- Records exact `rg` scan commands and focused test commands for current display image injection.
- Cites the runtime tests that assert `display_perception` projection is selected for current display tool messages.
- Cites the runtime tests that assert BlobRef `image_ref` content is resolved to image MCP content for the provider call.
- Creates a concrete follow-up if this current-turn perception path lacks direct coverage.
- Explains why this belongs under the display regression inventory split.
