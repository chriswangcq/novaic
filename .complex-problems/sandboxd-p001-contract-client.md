# Sandboxd common contract and client

## Problem

The sandbox execution boundary needs a stable, business-agnostic contract so Cortex can call an independent sandboxd server without importing server internals or passing ad hoc dictionaries. The contract must preserve byte output losslessly and must make mount execution explicit.

## Success Criteria

- `novaic-common` exposes reusable sandboxd request/response types and encode/decode helpers.
- `ProcessSpec` can carry an explicit mount plan without Cortex pre-wrapping shell commands.
- A reusable sandboxd client implements the same process-runner port used by Cortex.
- Unit tests cover byte-safe stdout/stderr transport, mount-plan serialization, timeout/result mapping, and no hidden Cortex/business dependencies.
