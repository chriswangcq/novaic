# Split full event-source cutover into design and implementation phases

## Problem Definition

The user explicitly wants a one-step full cutover to an event-sourced Cortex context source model, with old data allowed to be deleted and no compatibility burden. This is high-risk and touches Cortex source-of-truth semantics, Runtime prepare flow, projections, tests, and old-code cleanup.

## Proposed Solution

Classify this root ticket as `split` and create child problems for:

- Phase 0: final design document and construction plan.
- Phase 1: event schema and event store substrate.
- Phase 2: projection/replay model for LLM context and workspace views.
- Phase 3: write-path cutover for context, steps, scope begin/end, notification hints.
- Phase 4: prepare/read-path cutover and old DFS source-path cleanup.
- Phase 5: comprehensive tests, no-compat reset behavior, and final residue audit.

## Acceptance Criteria

- The root ticket is split, not one-go.
- Each phase has a concrete child problem with success criteria.
- Child problems collectively cover design, implementation, cleanup, and verification.
- The plan explicitly avoids permanent double truth.

## Verification Plan

- Use the ledger `split-ticket` flow to create child problems.
- Let `ledger.py next` drive execution of child problems one at a time.
- Do not run implementation before the design/construction child is complete.

## Risks

- Event source cutover can create dual-source ambiguity if legacy DFS writes remain active.
- Full cutover may require more repository changes than a single response can safely finish.
- Tests may need substantial rewrite because existing fixtures assume direct workspace file source state.

## Assumptions

- Old Cortex context history can be reset/deleted during cutover.
- Runtime still needs enough projected RO/workspace shape for shell/audit tools, but that shape becomes a projection, not source.
