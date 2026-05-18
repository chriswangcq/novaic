# Map Cortex context assembly source and event boundary

## Problem Definition

The active context assembly path now involves ContextEvents, workspace materialized projections, step/payload references, runtime prepare-context handlers, and active skill stack messages. We need a concrete source map before optimizing deeper projection behavior, otherwise a fix can land in a compatibility path while the live path keeps leaking or dropping information.

## Proposed Solution

Audit and document the active path with file/function pointers:

- Context event write/read:
  - `novaic-cortex/novaic_cortex/context_event_store.py`
  - `novaic-cortex/novaic_cortex/context_event_projection.py`
  - `novaic-cortex/novaic_cortex/context_event_read_model.py`
- Workspace materialized projections and payload write/read:
  - `novaic-cortex/novaic_cortex/workspace.py`
- Runtime context append and prepare handlers:
  - `novaic-agent-runtime/task_queue/handlers/context_handlers.py`
  - `novaic-agent-runtime/task_queue/handlers/runtime_handlers.py`
  - `novaic-agent-runtime/task_queue/handlers/cortex_handlers.py`
- React saga prepare-context entrypoint:
  - `novaic-agent-runtime/task_queue/sagas/react_think.py`
  - `novaic-agent-runtime/task_queue/contracts/react_think.py`
- Step result references used by tool result events:
  - `novaic-agent-runtime/task_queue/handlers/tool_handlers.py`
  - `novaic-agent-runtime/task_queue/contracts/react_actions.py`

Classify each path as active, test-only, compatibility-only, or stale/dead. If a duplicate active path is found, either remove it if clearly dead or create a smaller follow-up problem.

## Acceptance Criteria

- A result document maps the current write/read path from user notification and tool result writes to prepared LLM messages.
- The map explains how `step_ref`, `payload_ref`, materialized `context.jsonl`, ContextEvents, and active skill stack injection relate.
- Any duplicate or stale path discovered is explicitly classified and either fixed or split into a follow-up child problem.
- The audit is backed by source pointers and targeted tests/static checks, not broad claims.

## Verification Plan

- Inspect the files listed above with narrow `rg`, `sed`, and tests.
- Run relevant Cortex event/projection tests:
  - `novaic-cortex/tests/test_context_event_projection.py`
  - `novaic-cortex/tests/test_context_event_read_model.py`
  - `novaic-cortex/tests/test_context_event_api_context_writes.py`
  - `novaic-cortex/tests/test_context_event_api_steps_write.py`
- Run relevant runtime context tests if source classification touches runtime behavior.

## Risks

- Some materialized workspace projections may be debug/readability outputs rather than source of truth; misclassifying them could cause unnecessary rewrites.
- Active skill stack injection may happen late as a system message, so it must be mapped separately from ContextEvent message projection.
- Legacy comments may be correct historical notes but no longer active behavior.

## Assumptions

- ContextEvent stream is intended to be authoritative for cross-wake LLM context.
- Materialized `context.jsonl` and step files still matter for observability and step replay, but should not be assumed to be the sole source of LLM context.
- Mapping can be completed before making code changes; implementation fixes should be split if the map reveals deeper structural gaps.
