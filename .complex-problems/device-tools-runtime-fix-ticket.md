# Wire mounted device tools through Runtime

## Problem Definition

The mounted-device tool path is split across services: Business resolves mounted tools, Device enforces and proxies operations, but Runtime's LLM context assembly and tool execution paths only know static tools. This breaks 小马's Host Desktop tools.

## Proposed Solution

Add Runtime-side helpers to fetch and normalize Business dynamic mounted device tools, merge them with Cortex static schemas during `cortex.prepare_llm_context`, and add a generic Host Desktop device executor mapping for all `hd_*` tool names. Keep Cortex static tool schemas unchanged.

## Acceptance Criteria

- `handle_cortex_prepare_llm_context` includes `hd_*` tools from Business when Business returns them.
- Dynamic schemas use `parameters`, even when Business returns `inputSchema`.
- Business stale/non-executable static names are not blindly imported into Runtime context.
- `_EXECUTORS` includes Host Desktop `hd_*` tool names with a common executor.
- Host Desktop tool calls route to `/internal/agents/{agent_id}/hd/...` paths on Device Service.
- Tests cover dynamic schema merge, inputSchema normalization, and device executor routing.

## Verification Plan

- Run focused Runtime tests for LLM context and tool path contracts.
- Run focused Common/Cortex tool schema tests to ensure static schema contracts remain stable.
- Review git diff to ensure no broad legacy churn.

## Risks

- Device proxy path mapping may diverge from PC client expectations.
- Business endpoint includes stale static tools; Runtime must filter to known dynamic device tools.
- Live services are not available in this Codex environment, so smoke test is unit-level unless deployment is requested.

## Assumptions

- 小马's current requested device surface is Host Desktop (`hd_*`).
- Dynamic VM/mobile tools can follow the same pattern later, but this ticket fixes the active Host Desktop issue.
