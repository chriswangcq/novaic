# Audit direct Blob and object API usage

## Problem

Find every direct Blob/object API usage relevant to Cortex, LogicalFS, sandboxd,
runtime, app/display/artifact bytes, and docs. Classify each as allowed or a
blocking live `RO` / `RW` bypass.

## Success Criteria

- Source pointers list all relevant direct Blob/object uses in Cortex and nearby
  services.
- Each usage is classified as allowed cheap-byte use, allowed persistence
  adapter/internal use, test-only use, stale doc/comment, or blocking bypass.
- The result identifies exact cleanup or guardrail follow-up work.
