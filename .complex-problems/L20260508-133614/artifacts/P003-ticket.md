# P003 Ticket - Cortex registry 显式依赖边界收口

## Problem Definition
`WorkspaceRegistry` still creates default collaborators internally, including payload policy from environment and wall-clock time. That makes registry behavior depend on hidden process state instead of explicit constructor inputs.

## Proposed Solution
Move payload policy and clock construction to explicit boundary helpers. Keep a convenience factory for production wiring if needed, but make the registry constructor require explicit dependencies and keep domain behavior deterministic.

## Acceptance Criteria
- `WorkspaceRegistry.__init__()` does not call `BlobPayloadPolicy.from_env()`.
- `WorkspaceRegistry.__init__()` does not use `time.time` or any clock default internally.
- Production wiring still has a clear factory/boundary where env/time are read once.
- Tests verify the constructor is explicit and deterministic.

## Verification Plan
- Inspect `novaic-cortex` registry and callers.
- Refactor constructor/factory.
- Add/update focused tests.
- Run Cortex tests around workspace registry/shell if present.

## Risks
- Callers that relied on zero-argument defaults must be updated to pass explicit dependencies or call the production factory.

## Assumptions
- Backward compatibility for implicit constructor behavior is not required.
