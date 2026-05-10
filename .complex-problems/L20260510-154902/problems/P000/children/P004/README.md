# Phase 3: Write-path cutover to context events

## Problem

Cut Cortex write paths over so context facts are appended as events first. Legacy files may still be generated as projections if needed, but direct file writes must no longer be the source-of-truth path.

## Success Criteria

- `context.append`, `context.batch`, `steps.write`, `skill_begin`, `skill_end`, wake init, and notification input append emit context events as the authoritative fact.
- Workspace projection files, if still present, are explicitly derived/projection-only.
- Old direct-source writes are deleted or routed through event append/projector.
- Tests cover each write endpoint and verify event stream contents.
