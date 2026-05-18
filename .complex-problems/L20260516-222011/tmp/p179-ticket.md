# Audit externalized payload regression and ambiguity cleanup

## Problem Definition

After wrapper, storage, and formatted-read layers are individually mapped, the remaining risk is cross-layer ambiguity: legacy compatibility branches may still treat `step_ref` and `payload_ref` as interchangeable, or tests may miss externalized payload/blob artifact regressions.

## Proposed Solution

Inventory production and test coverage for `step_ref`/`payload_ref`, externalized payload refs, artifact refs, public truncation, and display/media projection. Add or tighten missing tests, and remove/fix stale compatibility paths if found.

## Acceptance Criteria

- Cross-layer coverage is mapped across runtime and Cortex.
- Any live compatibility branches that intentionally match both `step_ref` and `payload_ref` are classified.
- Missing regression tests are added or the result explains why existing tests cover the risk.
- Focused runtime and Cortex tests are run after the inventory.

## Verification Plan

Use `rg` to inventory refs, inspect suspicious branches, run focused Cortex/runtime tests from P176-P178 plus any new tests.

## Risks

Compatibility matching by `payload_ref == step_ref` may be safe for old/local payloads but dangerous if allowed to mask externalized payload lookup failures.

## Assumptions

No backward compatibility is required unless it is still necessary for active in-memory messages produced by the current runtime.
