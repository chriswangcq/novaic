# Cortex API CLI and bridge surface cleanup

## Problem

Cortex API, CLI, and runtime bridge surfaces may expose or accept compatibility-shaped payloads even if internal lifecycle code is clean.

## Success Criteria

- Inspect Cortex API/CLI/bridge surfaces from the inventory.
- Ensure live callers must pass explicit generation/session/scope authority where required.
- Remove stale compatibility branches that infer active state from old storage shape.
- Add focused boundary tests for any changed API/CLI/bridge surface.
- Confirm shell/agent-facing behavior still returns pointer-oriented outputs rather than large inline payloads.

