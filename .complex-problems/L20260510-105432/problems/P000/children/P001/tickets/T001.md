# Classify stable sandbox primitives

## Problem Definition

We need a precise extraction boundary so base modules stay business-agnostic and Cortex keeps product semantics.

## Proposed Solution

Inspect current `sandbox_exec.py`, `logical_fs.py`, `sandbox.py`, and tests. Classify each helper/dataclass/class as common or Cortex-specific. Define target common APIs.

## Acceptance Criteria

- Extraction candidates are listed with reasons.
- Non-candidates are listed with reasons.
- Target module/API names are stable.

## Verification Plan

- Read-only code inspection.
- Record result before implementation.

## Risks

- Moving too much into common could pollute base infrastructure with Cortex concepts.

## Assumptions

- Common module location is `novaic-common/common/sandbox`.
