# Move SubAgent spawn behind agentctl shell capability

## Problem Definition

`subagent_spawn` remains a standalone LLM tool even though SubAgent creation is an interface action. Keeping it direct preserves an old business branch outside the shell-boundary design.

## Proposed Solution

- Add `agentctl subagent spawn --task TEXT` and `--task-file PATH` to the shell capability script.
- Route that command to the existing Business `/internal/subagents/{agent_id}/spawn` endpoint.
- Remove `subagent_spawn` from the canonical LLM schema and active Common metadata.
- Update shell schema/help, product semantics, and guard tests.
- Keep the direct executor as internal compatibility until final physical deletion.

## Acceptance Criteria

- Canonical LLM schemas exclude `subagent_spawn`.
- `agentctl subagent spawn` supports `--task`, `--task-file`, `--share-context`, and `--timeout-minutes`.
- Shell capability test proves the command calls Business with the expected payload.
- Runtime tool-path tests exclude `subagent_spawn` through schema-cutover compatibility.

## Verification Plan

- Run Cortex shell capability and schema tests.
- Run Runtime tool-path/tool-surface tests.
- Run Common tool-definition/product-semantics tests.

## Risks

- Existing direct `subagent_spawn` unit behavior must not be broken until the final deletion ticket.

## Assumptions

- This ticket covers `subagent_spawn` only; dynamic device tools and `audio_qa` are separate slices.
