# Compare RO/RW Optimization Architecture Options

## Problem Definition

We need to compare credible RO/RW mount optimization models before recommending a target design. The comparison must fit this product's shell contract and not blindly import heavy filesystem infrastructure.

## Proposed Solution

Evaluate the candidate models against current code constraints: lazy RO, manifest/delta sync, persistent per-agent cache, OverlayFS-style lower/upper, FUSE/virtual filesystem, CLI-native object access, and hybrid staging.

## Acceptance Criteria

- Each option has performance upside, correctness risks, and implementation complexity.
- The comparison preserves stable `/cortex/ro` and `/cortex/rw` ergonomics.
- Poor-fit options are explicitly rejected or deferred.
- No code implementation is performed.

## Verification Plan

- Use local code audit from P001.
- Use primary documentation for filesystem primitives where relevant.
- Produce a comparative matrix and recommendation signal.

## Risks

- Overvaluing elegant filesystem machinery over product fit.
- Underestimating invalidation and concurrent write semantics.

## Assumptions

- The target environment can run normal shell commands but should not depend on privileged mounts unless the benefit is overwhelming.
