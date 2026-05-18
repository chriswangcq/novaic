# Factory/provider/log projection inventory ticket

## Problem Definition

Factory and provider/log code must preserve structured multimodal request payloads for LLM calls while redacting raw base64 in logs. We need a focused inventory before any cleanup.

## Proposed Solution

Inspect runtime factory client, LLM factory chat routes/provider adapter, and factory log detail/redaction code. Classify suspicious branches and cleanup candidates. Do not edit code.

## Acceptance Criteria

- Covers outbound runtime factory request preservation.
- Covers provider adapter multimodal payload preservation/conversion.
- Covers log detail redaction and UI-facing request/response shape.
- Identifies stale or duplicate code with line references.
- No code changes.

## Verification Plan

Use targeted `rg`/`nl` reads over `novaic-agent-runtime/task_queue/factory_client.py` and `novaic-llm-factory` modules/tests.

## Risks

- Redaction code and provider adapter code may look duplicate but have distinct responsibilities.

## Assumptions

- This ticket is read-only inventory.
