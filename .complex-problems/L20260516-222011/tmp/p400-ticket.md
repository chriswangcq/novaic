# Subagent wake session generation cleanup ticket

## Problem Definition

`task_queue/sagas/subagent_wake.py` currently converts `ctx["session_generation"]` with inline `int(...)`. Because subagent wake payloads participate in session/wake creation, this must be an explicit boundary rather than a hidden coercion.

## Proposed Solution

Inspect the subagent wake saga context contract and tests. If `session_generation` is live authority, replace the inline conversion with a named validator that rejects missing, bool, malformed, or non-positive generation values. If upstream guarantees the value, document that guarantee and add a focused guard. Prefer fixing at the boundary closest to the saga payload.

## Acceptance Criteria

- No inline `int(ctx["session_generation"])` remains in `subagent_wake.py`.
- Live subagent wake session generation rejects bool/missing/malformed values.
- Focused tests cover the validator or classification.
- Targeted guard for subagent wake generation residue passes.

## Verification Plan

- Inspect `subagent_wake.py` and related tests.
- Patch and add focused tests.
- Run targeted subagent wake/saga tests.
- Run `rg` guard for the old inline coercion.

## Risks

- Existing tests may rely on permissive string coercion.
- Upstream saga context may currently omit generation for some older path; this should fail loudly if still live.

## Assumptions

- No backward compatibility is required for malformed or missing live `session_generation`.
