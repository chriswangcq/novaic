# Run focused cross-repo reasoning streaming verification

## Problem

The streaming path touches Factory, Runtime, and App. The final pass needs concrete test evidence across all touched repos, including Factory SSE, Runtime aggregation/projection/handler integration, and App timeline/contract behavior.

## Success Criteria

- Focused tests pass in `novaic-llm-factory` for streaming chat route/provider behavior.
- Focused tests pass in `novaic-agent-runtime` for Factory stream parsing, activity projection, and LLM handler integration.
- Focused tests pass in `novaic-app` for ActivityTimeline, hook normalization, entity contract, and guard behavior.
- Any failure is recorded with exact command output and either fixed or escalated as a follow-up.
