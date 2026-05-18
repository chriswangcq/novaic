# Audit runtime context client and history expansion projection boundaries

## Problem Definition

Runtime LLM preparation expands Cortex `step_ref` tool results and processes multimodal content. This can accidentally bypass Cortex payload externalization if historical display/shell/blob results are expanded as raw media or if current display images are ordered incorrectly around system messages.

## Proposed Solution

Map runtime LLM preparation, step result expansion, multimodal processing, and active-stack/system insertion. Verify current display media is available exactly for the current turn, while historical and non-display tool results remain bounded text/manifest. Tighten tests if any gap is found.

## Acceptance Criteria

- Runtime context preparation and step-result client paths are mapped with file/function pointers.
- Current-round display/media projection is distinguished from historical manifest-only replay.
- Shell/payload/blob bytes are not expanded beyond bounded terminal text and references.
- Active skill stack/system-message ordering is checked against current display media projection.
- Targeted runtime tests prove no historical image/base64 injection and correct current display image availability.

## Verification Plan

Inspect `task_queue/utils/step_result_client.py`, `task_queue/utils/context.py`, `task_queue/utils/multimodal.py`, and relevant tests. Run targeted runtime projection/multimodal tests and add/adjust tests only if a real gap is found.

## Risks

- A superficially correct projection can still fail if system-message insertion changes the relative order of generated image messages.
- Historical step expansion must remain text-only even when durable payloads contain media.

## Assumptions

- Cortex projection formatting already enforces current/history projection modes; runtime must call it with the right projection and preserve the contract.
