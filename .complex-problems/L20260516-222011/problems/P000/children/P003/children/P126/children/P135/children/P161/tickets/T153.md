# Map runtime LLM payload handoff from prepared snapshot

## Problem Definition

The runtime LLM request must be assembled from Cortex's prepared snapshot, not stale `context.read` projections, continuity fields, or locally reconstructed message lists. `react_think` contracts and `llm_handlers` need explicit mapping and guard coverage for the final handoff into `llm.call`.

## Proposed Solution

Map the handoff in two slices: the `react_think` contract/builders that move prepare-context output into `llm.call`, and the `llm_handlers`/LLM contract layer that turns that payload into the provider request. Add or tighten focused tests if any final provider messages/tools can be sourced outside the prepared snapshot.

## Acceptance Criteria

- `contracts/react_think.py` and `handlers/llm_handlers.py` have evidence pointers for `build_llm_call_payload`, `LLMCallInput`, and final provider-message/tool assembly.
- The exact fields copied from prepare-context result into `llm.call` are documented.
- Tests or static guards prove provider messages/tools come from the prepared snapshot.
- Any legacy local context source that can still reach provider messages is fixed or split into a smaller follow-up problem.

## Verification Plan

Use targeted source mapping plus runtime tests around explicit contracts, LLM context smoke guardrails, no-tool warning behavior, and saga DAG ordering. Treat any ambiguous source of `messages`/`tools` as a gap until covered by a direct test or split child.

## Risks

- `messages` and `tools` are generic field names and may appear in unrelated contexts; naive text search can overcount or miss a real data path.
- Existing tests may assert that builders copy fields without proving that handlers don't rehydrate old context later.

## Assumptions

- If mapping reveals separable gaps between saga builder and provider handler, this ticket should be classified as `split` rather than forced through one-go.
