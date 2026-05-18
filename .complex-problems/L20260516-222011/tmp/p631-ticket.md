# Classify and Remove Legacy Root RW Scratch Layout

## Problem Definition

Current LogicalFS execution env exposes subagent-aware writable paths such as `RW_SCRATCH=/cortex/rw/subagents/{subagent}/scratch`, but Cortex workspace initialization and many tests still use root `/rw/scratch`. Some hits are generic RW path tests; others may preserve the old global scratch convention. The remediation must classify and remove high-confidence legacy assumptions without breaking valid arbitrary `/rw` file semantics.

## Proposed Solution

Scan `/rw/scratch`, `RW_SCRATCH`, `/rw/subagents`, and `scratch` usage across Cortex and LogicalFS. Classify hits into: current subagent-aware scratch contract, generic RW path fixture, and removable global scratch layout. Remove the default `/rw/scratch` initialization and update tests that only require a writable scratch-like path to the current `subagents/main/scratch` convention or a neutral `/rw/tmp`/`/rw/public` path where appropriate.

## Acceptance Criteria

- Exact scans and classifications are recorded.
- Root `/rw/scratch` is no longer created as a default Workspace layout unless explicitly justified.
- Tests no longer encode global root scratch as the preferred scratch contract.
- `RW_SCRATCH` remains subagent-aware through LogicalFS execution env.
- Focused Cortex/LogicalFS tests pass.

## Verification Plan

Run static scans for `/rw/scratch`, `RW_SCRATCH`, `/rw/subagents`, and `initialize_layout`. Run focused Cortex workspace/path/runtime/sandboxd tests and LogicalFS layout tests if relevant.

## Risks

- `/rw/scratch` may be used in tests as a generic writable path, not necessarily a semantic scratch contract; update carefully.
- Removing initialization should not break arbitrary writes under `/rw/...`.
- LogicalFS package has independent authority tests that may use `/rw/scratch` generically and should not be rewritten unless they encode Cortex's default layout.

## Assumptions

- Subagent-aware `RW_SCRATCH` is the intended scratch contract for shell execution.
- Global root `/rw/scratch` should not be advertised or initialized as the default scratch path.
