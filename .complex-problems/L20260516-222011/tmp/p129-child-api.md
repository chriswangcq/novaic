# Audit explicit Cortex payload inspection APIs

## Problem

Payload read/search/summarize/qa APIs must be explicit, bounded, and pointer-addressed.

## Success Criteria

- Payload API entrypoints are mapped with file/function pointers.
- Read/search behavior is bounded by explicit mode/limit/query inputs.
- Summarize/qa behavior is classified as explicit payload interpretation, not default context assembly.
- Tests verify bounded retrieval behavior.
