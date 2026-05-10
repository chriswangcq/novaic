# Move audio QA behind agentctl media shell capability

## Problem Definition

`audio_qa` is still a direct LLM tool. It performs interface work: fetch a user Blob audio file, ask the configured audio model, and return text. This can be expressed as a shell media command with explicit file URL and prompt inputs.

## Proposed Solution

- Add `agentctl media audio-qa --file-url URL [--prompt TEXT|--prompt-file PATH]`.
- Implement Blob fetch, audio model config lookup, Factory call, and JSON output in the generated capability script.
- Inject only explicit service env needed by the shell script.
- Remove `audio_qa` from canonical LLM-facing schemas and active Common multimodal metadata.
- Keep direct Runtime executor as compatibility until final deletion.

## Acceptance Criteria

- Canonical LLM schemas exclude `audio_qa`.
- Shell help advertises `agentctl media audio-qa`.
- Shell capability test proves the command calls Blob, Business config, and Factory endpoints.
- Runtime/Common/Cortex schema tests pass.

## Verification Plan

- Run Cortex shell capability/schema tests.
- Run Runtime tool-surface tests.
- Run Common schema/product-semantics tests.

## Risks

- This duplicates a small amount of audio execution logic in shell capability code until direct executor deletion can remove the old branch.

## Assumptions

- `display` remains an LLM-visible perception tool outside shell.
