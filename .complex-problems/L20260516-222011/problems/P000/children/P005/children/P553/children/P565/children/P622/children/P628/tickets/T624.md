# Classify Sandbox Wire Base64 Public-History Residue

## Problem Definition

P628 must verify that base64 byte payloads remain private wire/durable payload artifacts and do not enter public LLM history/tool text through shell/display/projection paths.

## Proposed Solution

Scan SDK/service/Cortex/runtime projection code for base64/stdout_b64/stderr_b64/data URL/image payload terms, cite relevant wire/projection slices, classify each hit, and run focused shell/artifact/no-history tests.

## Acceptance Criteria

- Exact scans and outputs are recorded.
- Base64 wire encode/decode surfaces are cited and classified private.
- Public LLM-history/tool-text projection surfaces are cited and shown bounded/manifest-only.
- Focused shell/artifact/no-history tests pass.
- Any raw base64 public-history path creates a follow-up.

## Verification Plan

Run SDK tests, Cortex projection tests, runtime shell output and no historical image injection tests, and frontend timeline raw payload redaction tests if relevant.

## Risks

- Tests may include sample base64 strings intentionally.
- Provider/request logs may show BlobRef or display tool calls without embedding image bytes; classify carefully.

## Assumptions

- Display multimodal internals are not shell terminal output; this ticket focuses on public text/history leakage.
