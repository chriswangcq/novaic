# ContextEvent API lifecycle endpoint cleanup ticket

## Problem Definition

ContextEvent API lifecycle endpoints are the request-facing boundary for context writes, skill lifecycle, LLM context preparation, and formatted step reads. They must not bypass event-source context, infer stale active state from old file layouts, or return media payloads in the wrong projection mode.

## Proposed Solution

Inspect the API endpoints that call `ContextEventWriter`, `ContextEventReadModel`, `write_step_projection`, `steps_read_formatted`, and skill lifecycle helpers. Patch dangerous defaulting or wrong projection behavior if found.

## Acceptance Criteria

- Context write/prepare/skill lifecycle API paths are inspected.
- Endpoints use explicit root identity and ContextEvent write/read models.
- Current/history/display projection modes remain separated.
- Direct API behavior does not reintroduce inline payload or stale active-state compatibility.
- Focused API lifecycle tests pass.

## Verification Plan

- Inspect relevant `api.py` slices.
- Run context event API lifecycle/write/steps tests.
- Run a targeted guard for `prepare_for_llm`, `steps_read_formatted`, `ContextEventWriter`, and direct workspace/file fallback.

## Risks

- API lifecycle overlaps with P419 API/bridge cleanup; keep this ticket focused on ContextEvent lifecycle and projection mode boundaries.

## Assumptions

- Event-source context is the authority for LLM context preparation.
- Display perception is the only projection allowed to expose visual content.
