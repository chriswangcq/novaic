# Build novaic-sandbox-service

## Problem Definition

Sandbox execution must move out of Cortex into an independent base service. The service should be small, generic, and depend only on `novaic-common` sandbox primitives.

## Proposed Solution

Create `novaic-sandbox-service` with a FastAPI app, `/health`, `/api/health`, and `/v1/execute`. The execute route parses the common contract, validates explicit cwd/mount inputs, runs through `AsyncProcessRunner`, and returns the common byte-safe response contract.

## Acceptance Criteria

- New service package and entrypoint exist.
- Health endpoints identify the service as `sandboxd`.
- Execute endpoint uses common contract and common process runner.
- No Cortex/workspace/blob/agent imports appear in the service.
- Tests cover health, successful execution, timeout, invalid mount source, and route contract.

## Verification Plan

- Run `PYTHONPATH=novaic-common:novaic-sandbox-service pytest -q novaic-sandbox-service/tests`.
- Run residue import scan for forbidden business/runtime imports.

## Risks

- FastAPI/TestClient dependency availability may vary, but existing services already rely on them.

## Assumptions

- `sandboxd` should not own logical workspace hydration or blob sync; it only executes an explicit process spec.
