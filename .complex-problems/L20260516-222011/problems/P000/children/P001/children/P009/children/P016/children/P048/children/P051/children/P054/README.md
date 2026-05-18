# Child Problem: display tool output is concise and non-binary

## Problem

The `display` tool result that is written into tool history must stay concise. It should acknowledge loading or projecting the artifact without embedding base64 image bytes, data URLs, or large JSON text.

## Success Criteria

- Active `display` tool handler returns compact tool text for images.
- Display tool observation text never includes raw image base64 or `data:image/*;base64`.
- Focused tests prove the tool-result text contract.
