# Runtime and factory projection inventory ticket

## Problem Definition

Runtime and factory layers determine whether projected tool/display content becomes model request text, structured image content, or log UI payload. We need to classify suspicious branches before deleting or preserving them.

## Proposed Solution

Inspect runtime message expansion, multimodal preparation, shell output contract, factory client/provider conversion, and log detail redaction. Record exact file/line evidence and classify branches as active, compatibility, test-only, or stale. Do not edit code.

## Acceptance Criteria

- Covers runtime `expand_messages_for_llm`, projection selection, `process_multimodal_messages`, shell output contract, factory client, provider adapter, and log detail redaction.
- Identifies stale or duplicate projection branches with exact line evidence.
- Distinguishes active current display media handling from historical/generic tool image rejection.
- No production/test code changes.

## Verification Plan

Use targeted `rg`/`nl` reads over runtime and factory modules. Result is an inventory for downstream cleanup.

## Risks

- Some conversion branches may look duplicated but are intentionally at separate boundaries: runtime request construction, provider adapter, and log UI redaction.

## Assumptions

- This ticket is read-only inventory.
