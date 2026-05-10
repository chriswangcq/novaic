# Research RO/RW Mount Optimization Architecture

## Problem Definition

RO/RW filesystem ergonomics are central to the agent shell contract, but the current disposable sandbox may repeat too much work per command. We need a deep research pass that audits the current code, compares architectural options, and recommends a staged optimization plan without making runtime changes yet.

## Proposed Solution

Split the work into focused research subproblems:

- Audit the current mount/materialization path and identify repeated work and correctness assumptions.
- Compare optimization architectures against this system's constraints.
- Produce a recommended phased design and follow-up implementation tickets.

## Acceptance Criteria

- Current code path is described with file/function evidence.
- Bottlenecks and hidden costs are separated from confirmed facts.
- Candidate optimizations are compared with pros, cons, and fit.
- Final recommendation is staged and implementable.
- No code implementation is performed in this research pass.

## Verification Plan

- Use local code inspection with focused `rg`, `nl`, and test references.
- Cross-check recommendations against existing tests and constraints.
- Record a problem-level success check mapping results to all success criteria.

## Risks

- A too-aggressive optimization could break shell freshness or RW durability if implemented later.
- A FUSE-like direction may be operationally heavier than the current architecture can justify.
- Persistent cache can introduce invalidation complexity if not designed around manifests/generations.

## Assumptions

- This pass is research/design only.
- The current user priority is shell reliability and ergonomic `/cortex/ro` / `/cortex/rw`, not maximal filesystem performance at the cost of complexity.
