# Audit FSM Worker DSL Boundary

## Problem Definition

The architecture status document claims a specific runtime shape: generic FSM substrate, generic worker substrate, declarative roster/assembly specs, pure policy/spec/plan helpers, plan-first effects, and explicit Python computation hooks. The audit must verify that this statement matches live code.

## Proposed Solution

Cross-check the documentation's live code pointers against the filesystem and inspect imports/usages in action engines and registries. Confirm accepted computation hooks are named rather than hidden fallback paths.

## Acceptance Criteria

- Every live path named in the status document exists.
- `EffectPlanRunner`, `WorkerAssemblySpec`, policy/spec/plan helpers, and handler metadata are used by the expected runtime code.
- Accepted Python computation hooks are explicit and documented.
- Any doc/code mismatch is fixed or converted into a follow-up.

## Verification Plan

- Run targeted path existence and `rg` usage checks.
- Inspect key files with line-numbered slices.
- Reuse the documentation guard test as supporting evidence.

## Risks

- Usage checks can be shallow; inspect representative files around imports and calls.

## Assumptions

- The goal is verifying the implemented spec/plan-driven shape, not requiring all domain behavior to become data-only.
