# Move payload tools behind cortex payload shell capability

## Problem Definition

Payload inspection tools are still direct LLM tools. That keeps a second interface family alive beside `shell`, even though payload inspection is naturally file/pointer-oriented and should be accessed through stable Cortex shell commands.

## Proposed Solution

- Implement `cortex payload read` and `cortex payload search` in the generated shell capability script, backed by existing Cortex `/v1/payload/read` and `/v1/payload/search` endpoints.
- Implement `cortex payload summarize` and `cortex payload qa` through the same capability script, using explicit model/factory env injected at the shell boundary.
- Remove direct payload schemas from `AGENT_BUILTIN_TOOL_SCHEMAS`.
- Update shell schema and tests to advertise the `cortex payload ...` capability path.
- Mark payload direct executors as completed schema-cutover compatibility in Runtime policy/tests.
- Keep direct payload executor implementation temporarily for compatibility tests and to avoid mixing schema cutover with physical deletion.

## Acceptance Criteria

- Canonical LLM schemas exclude `payload_read`, `payload_search`, `payload_summarize`, and `payload_qa`.
- Shell help includes `cortex payload read/search/summarize/qa`.
- Shell capability tests prove `cortex payload read` and `cortex payload search` can inspect a stored payload through stable shell commands.
- Runtime tests prove direct payload executors are not LLM-visible but still internally executable.
- Existing payload endpoint and handler tests continue passing.

## Verification Plan

- Run Cortex shell capability tests.
- Run Cortex schema guard tests.
- Run Common payload/schema/product-semantics tests.
- Run Runtime tool-path and shell-output contract tests.

## Risks

- Summarize/QA require model config. The shell boundary must inject explicit payload interpretation env rather than reading hidden global config inside the script.
- Direct payload executor physical deletion is a later cleanup step after the shell path is proven and remaining tool families are migrated.

## Assumptions

- This ticket covers payload schema cutover, not subagent/audio/device cutover.
