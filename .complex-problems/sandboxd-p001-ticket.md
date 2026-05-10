# Implement sandboxd common contract and runner client

## Problem Definition

`novaic-common` has process and filesystem primitives, but there is no explicit service contract for moving sandbox execution out of Cortex. Cortex also still relies on command pre-wrapping instead of passing a declarative mount plan to a runner port.

## Proposed Solution

Add business-agnostic sandboxd models to `common.sandbox`, extend `ProcessSpec` with an optional mount plan, teach `AsyncProcessRunner` to apply the mount plan, and add an HTTP client runner that converts `ProcessSpec` to the service contract.

## Acceptance Criteria

- Common contract supports command, cwd, env, timeout, optional mount plan, exit code, duration, and byte-safe stdout/stderr.
- `AsyncProcessRunner` and the HTTP client share the same `ProcessSpec` port.
- No Cortex/business imports are introduced into `novaic-common`.
- Unit tests cover contract serialization, byte roundtrip, mount wrapping, and client response mapping.

## Verification Plan

- Run focused `novaic-common` sandbox tests.
- Run import/residue checks for Cortex/business imports under `common/sandbox`.

## Risks

- If mount wrapping moves into `AsyncProcessRunner`, existing Cortex tests may need adjustment because commands should no longer be pre-wrapped upstream.

## Assumptions

- The service transport can use JSON with base64-encoded byte streams.
- HTTP client can depend on `urllib` from the standard library to avoid adding a new common dependency.
