# Workspace step and payload normalization cleanup ticket

## Problem Definition

Workspace step writing and payload normalization decide what is persisted in `steps/*.json`, what is stored as payload, and what is projected into LLM context. This layer must enforce pointer-oriented payloads and reject stale inline result compatibility.

## Proposed Solution

Inspect `workspace.py` step/payload methods and related tests. Patch dangerous branches that allow inline tool result payloads, ambiguous payload references, or large payload leakage through step normalization.

## Acceptance Criteria

- `write_payload`, `read_payload`, `normalize_step`, and `write_step` behavior is inspected.
- Tool steps must reject inline `result`.
- Tool payloads must require explicit `payload_ref` when payload is written.
- Externalized payload manifests must stay pointer-oriented.
- Focused workspace/payload/step projection tests pass.

## Verification Plan

- Run focused tests around workspace, payload inspection API, step result projection, step index outcome, and tool output projection.
- Run a guard for inline result compatibility and payload fallback behavior.

## Risks

- Workspace is a large file with archive behavior too; keep this ticket limited to step/payload normalization and leave archive semantics to P418.

## Assumptions

- Old inline `result` compatibility is intentionally unsupported.
