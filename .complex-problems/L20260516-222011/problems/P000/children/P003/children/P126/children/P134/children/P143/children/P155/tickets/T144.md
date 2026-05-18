# Audit context projection regression tests

## Problem Definition

The workspace `context.jsonl` helpers now sit in a projection/debug role, but that classification must be backed by tests. Without focused regression tests, future changes could silently make materialized projections authoritative again or allow historical/raw payload leakage into context projections.

## Proposed Solution

Map the existing context projection tests across Cortex and Runtime, run the focused suites, and add any missing guard coverage discovered during the audit. Classify the coverage against message append projections, event read-model behavior, corrupt projection handling, and historical/raw payload leakage boundaries.

## Acceptance Criteria

- Existing projection/read-model/leakage guard tests are identified with file pointers.
- Focused Cortex and Runtime tests are run and pass.
- If a real coverage gap is found, a focused test is added.
- The result records whether projection helpers are adequately protected as non-authoritative materialized/debug projections.

## Verification Plan

- Search tests for `read_context`, `append_context`, `context projection`, `ContextEventReadModel`, `payload`, and historical tool/image leakage.
- Run focused Cortex context projection/read-model suites.
- Run focused Runtime history/tool-result leakage suites.
- Add a targeted regression test only if the search exposes an unguarded active risk.

## Risks

- Running too broad a mixed test command can fail due package-local `tests` import collisions; run per package when needed.
- Projection tests may pass while docs remain stale; classify stale docs separately instead of treating them as runtime authority.

## Assumptions

- `P154` already closed the active LLM prepare authority risk.
- This ticket is about regression coverage around projection/helper behavior, not changing the context architecture again.
