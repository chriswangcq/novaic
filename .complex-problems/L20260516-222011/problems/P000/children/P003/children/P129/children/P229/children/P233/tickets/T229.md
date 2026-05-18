# Verify runtime LLM context expansion avoids full payload reads

## Problem Definition

Normal runtime context preparation must not call explicit full payload read APIs by default. It should expand historical/current tool step refs through compact formatted projections and only allow media injection through explicitly marked current display perception.

## Proposed Solution

Trace `prepare_llm_call`, `expand_messages_for_llm`, `fetch_step_for_llm`, and Cortex bridge formatted-step calls. Search for runtime default context paths calling payload read/search APIs. Run focused runtime tests for no historical image injection, shell context projection, and LLM call preparation.

## Acceptance Criteria

- Runtime context expansion path is mapped with file/function pointers.
- Evidence shows default path calls formatted step projection, not full payload read APIs.
- Focused tests prove historical shell/display outputs stay compact in LLM request messages.

## Verification Plan

Use `rg` and line-numbered inspection across runtime context/client files. Run targeted runtime tests for context expansion and media/history projection.

## Risks

- A separate helper may call payload APIs indirectly; include repository search for payload read usage under runtime.

## Assumptions

- Explicit payload read/search/summarize/qa APIs are allowed only when invoked deliberately, as audited in `P228`.
