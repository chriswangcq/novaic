# Define Blob Boundary Guardrail Allowlist

## Problem

The guardrail must distinguish legitimate Blob byte flows from live `RO` / `RW` authority bypasses. Without an explicit allowlist, the scanner will either block valid payload/display/audio/artifact paths or miss dangerous Workspace/API/runtime/sandbox direct object-store calls.

This child belongs under T006 because it defines the precise dependency boundary before implementation.

## Success Criteria

- Allowed cheap-byte patterns are explicit: `blob://...`, `/v1/blobs/...`, payload externalization, display bytes, audio bytes, attachments, artifacts, and tests for those flows.
- Transitional persistence internals are explicitly named and limited.
- Forbidden live-file authority patterns are explicit for Workspace/API/runtime/sandbox code.
- The allowlist is encoded in a form that the implementation child can consume directly.
