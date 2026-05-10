# Build sandboxd service and migrate Cortex execution to it

## Problem Definition

Shell process execution is still in-process inside Cortex. We need to extract the generic execution environment into an independent service without moving Cortex business semantics into that service.

## Proposed Solution

Create a `sandboxd` service with a stable HTTP contract. Move execution RPC contracts/client into common, implement the service in a new `novaic-sandbox-service`, wire deployment/start configuration, and migrate Cortex `Sandbox` to use the service runner in production while preserving explicit test injection for local unit tests.

## Acceptance Criteria

- Common defines sandboxd request/response/client types.
- `novaic-sandbox-service` exposes health and execute endpoints.
- `sandboxd` owns process execution and mount namespace command wrapping from caller-provided mount spec.
- Cortex can call sandboxd through a client runner.
- Production config/start scripts include sandboxd as an independent backend service.
- Tests cover common contract/client, service behavior, and Cortex integration.
- Active path is explicit; no hidden fallback.

## Verification Plan

- Run common tests.
- Run sandbox service tests.
- Run Cortex tests.
- Run residue scans for direct in-process production assumptions.

## Risks

- A real network service adds latency and failure modes; the contract must preserve byte output and timeouts.
- Fully removing direct in-process runner from tests would make local test suite require a running service; keep direct runner only as explicit dependency injection/test adapter.

## Assumptions

- First implementation is same-host HTTP service; distributed remote sandbox can be a later transport layer.
