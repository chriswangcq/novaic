# Map runtime Cortex prepare handler and bridge contract

## Problem Definition

The runtime Cortex prepare boundary spans the handler (`handle_cortex_prepare_llm_context`) and the `CortexBridge.prepare_for_llm` client. We need to prove the handler calls the ContextEvent-backed prepare endpoint, returns a stable prepared snapshot, and does not fall back to `read_context`/local continuity for provider-message authority.

## Proposed Solution

Split this into handler response mapping and bridge endpoint mapping. The handler child will map payload input, output fields, tool merging/filtering, active stack/no-tool warning injection, and local read side paths. The bridge child will map HTTP endpoint selection and response passthrough/error behavior. Each child will run focused runtime tests or add guards if needed.

## Acceptance Criteria

- `cortex_handlers.py` prepare handler is mapped with source pointers and response fields.
- `cortex_bridge.py` `prepare_for_llm` is mapped with endpoint and payload fields.
- Any `read_context`/local continuity fallback inside this boundary is classified.
- Focused handler/bridge tests are run.

## Verification Plan

- Inspect `cortex_handlers.py` around `handle_cortex_prepare_llm_context`.
- Inspect `cortex_bridge.py` around `prepare_for_llm`.
- Run `test_pr85_llm_context_smoke_guardrails.py`, `test_pr67_wake_child_scope.py`, `test_no_tool_warning.py`, and `test_runtime_explicit_contracts.py`.

## Risks

- Handler and bridge can each be correct independently but still ambiguous together; split evidence must be re-aggregated at parent check.
- Do not conflate tool-surface policy with prepare endpoint authority unless it affects returned LLM messages/tools.

## Assumptions

- Cortex `/v1/context/prepare_for_llm` remains the authoritative context endpoint.
