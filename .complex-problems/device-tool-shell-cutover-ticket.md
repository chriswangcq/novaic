# Move mounted HD device tools behind devicectl shell capability

## Problem Definition

Mounted HD device tools are dynamically merged into the LLM tool list at context-prepare time. This bypasses the static schema cleanup and leaves direct device tools as active LLM-visible tools.

## Proposed Solution

- Add `devicectl hd <command>` shell capability with generic JSON/JSON-file arguments.
- Route commands to existing Device Service `/internal/agents/{agent_id}/hd/...` endpoints.
- Stop merging mounted device schemas into the LLM request.
- Keep direct device executors as compatibility until final deletion.
- Update tests to assert mounted device tools are not LLM-visible and `devicectl` works.

## Acceptance Criteria

- `handle_cortex_prepare_llm_context` returns static tools only and does not include `hd_screenshot` from Business mounted tools.
- `devicectl hd screenshot` and `devicectl hd shell-exec --command ...` style commands are documented.
- A shell capability test verifies Device proxy request path/payload.
- Runtime direct device executor tests still pass.

## Verification Plan

- Run Runtime prepare-context/device tests.
- Run Cortex shell capability tests.
- Run tool surface contract tests.

## Risks

- Device command ergonomics are generic in this ticket; richer subcommands can be layered later without changing LLM tool schema.

## Assumptions

- Physical deletion of direct device executors remains a final cleanup step.
