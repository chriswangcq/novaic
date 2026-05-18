# Audit generic dict JSON fallback projection branch

## Problem

`parse_tool_result` falls back to JSON serialization for unknown dict payloads. This may be useful for diagnostics or may hide stale unstructured contracts. Decide whether to retain, narrow, or remove it.

## Success Criteria

- The fallback has a documented safety reason or is replaced by a narrower projection.
- Unknown dict handling cannot silently become media/image injection.
- Tests cover retained or changed behavior.
