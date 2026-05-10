# Implement pure ToolOutputV1 contract module

## Problem Definition

Later migration phases need a stable output envelope, but current Runtime tool execution still treats arbitrary dicts as JSON content. Phase 1 should introduce the pure contract and tests without changing existing behavior.

## Proposed Solution

Add `task_queue/tool_output.py` with frozen dataclasses and pure helper constructors:

- `ArtifactManifest`
- `ToolEventManifest`
- `ToolDiagnostics`
- `ToolOutputV1`
- `tool_text`
- `tool_error`
- `artifact_manifest`
- `event_manifest`

Add unit tests under `tests/unit/task_queue/test_tool_output_contract.py`.

## Acceptance Criteria

- The module is deterministic and has no hidden time/id/env/io dependencies.
- `ToolOutputV1.to_dict()` is JSON-serializable.
- Text truncation is deterministic and records diagnostics.
- Artifact validation rejects bad data.
- Error outputs preserve machine-readable error string and bounded text.
- Existing tool execution behavior is untouched.

## Verification Plan

- Run `python -m pytest tests/unit/task_queue/test_tool_output_contract.py -q`.
- Re-run Phase 0 guard test.
- Review diff for scope.

## Risks

- Over-designing the schema could slow implementation; keep fields minimal but extensible.
- Using mutable defaults could create cross-test leakage; use frozen dataclasses and tuples.

## Assumptions

- This phase adds substrate only; Runtime `_ok()` normalization happens in a later phase.
