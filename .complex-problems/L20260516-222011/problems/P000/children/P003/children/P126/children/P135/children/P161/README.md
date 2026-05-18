# Runtime LLM payload handoff map

## Problem

The final LLM request should be assembled from the prepared Cortex snapshot, not from stale context projections or ad hoc local fields. The exact handoff through `react_think` contracts and LLM handlers must be mapped and guarded.

## Success Criteria

- `novaic-agent-runtime/task_queue/contracts/react_think.py` and `novaic-agent-runtime/task_queue/handlers/llm_handlers.py` are mapped for `build_llm_call_payload` and final provider-message assembly.
- The fields copied from prepare-context result into `llm.call` input are documented.
- Tests or static guards prove final provider messages/tools come from the prepared snapshot.
- Any legacy local context input that still reaches provider messages is fixed or split.
