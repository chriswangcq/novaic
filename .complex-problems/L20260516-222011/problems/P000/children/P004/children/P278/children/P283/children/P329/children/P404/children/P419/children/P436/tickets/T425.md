# Ticket: Audit and clean Cortex runtime bridge surface

## Problem Definition

The runtime-to-Cortex bridge still has callers for context projection endpoints such as `/v1/context/read`, `/v1/context/append`, and `/v1/context/batch`. After the context event/source model and shell-first tool contract changes, these endpoints may be intentional operational APIs, stale compatibility, or a live bypass of the new LLM prepare path. The bridge surface must be audited and cleaned so old materialized projection paths cannot silently feed LLM context.

## Proposed Solution

- Inventory runtime bridge callers for context projection, payload readback, and tool-result projection endpoints.
- Trace the agent loop / LLM prepare path to identify whether it uses event-source snapshots, materialized context projections, or both.
- Patch or split any live old projection path that still feeds LLM context through compatibility logic.
- Preserve only endpoints with explicit current ownership, such as notification injection, debugging, or bounded payload inspection.
- Add or run focused runtime/Cortex bridge tests and guards.

## Acceptance Criteria

- Runtime bridge callers for `/v1/context/read`, `/v1/context/append`, `/v1/context/batch`, payload readback, and tool-result projection are inventoried.
- Agent loop / LLM prepare path is traced to determine whether it uses event-source snapshots, materialized context projections, or both.
- Any live old projection path is removed or migrated, or split into explicit follow-up tickets if too broad.
- Focused runtime/Cortex bridge tests or guards pass.
- The result explicitly states which bridge endpoints remain, why they remain, and whether they are serving LLM context, notification injection, debugging, or compatibility only.

## Verification Plan

- Run targeted `rg` over runtime bridge, handlers, sagas, workers, and Cortex API tests for `/v1/context/*`, `read_context`, `append_context`, `batch_context`, `prepare_for_llm`, and tool-result projection calls.
- Inspect representative source slices for the live agent loop and bridge helpers.
- Run focused runtime prepare/bridge tests and Cortex projection/tool-result tests.
- Add or update regression tests if a live compatibility bypass is found.

## Risks

- Some context endpoints may be legitimate for notification append or debug inspection. Do not delete them blindly; classify the owner and prove they do not bypass the authoritative prepare path.

## Assumptions

- Complete historical context remains available through Cortex workspace events/payloads; the bridge should not need to reconstruct LLM context from stale compatibility projections unless explicitly justified.
