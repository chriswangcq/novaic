# Blob artifact manifest and history replay discovery

## Problem

Discover how Blob/runtime-artifact URIs and `tool-output.v1` manifests are persisted, replayed, and projected into later context/history. This must verify manifest-only history behavior so old media does not re-enter LLM context as raw text.

## Success Criteria

- Runtime/Cortex code that parses or stores artifact manifests is identified with file pointers.
- History replay behavior for artifact manifests is identified with tests or code evidence.
- Any active history replay path that injects raw media/base64 text is listed as a remediation candidate.
- Blob ownership is separated from live LogicalFS/RO/RW semantics.
