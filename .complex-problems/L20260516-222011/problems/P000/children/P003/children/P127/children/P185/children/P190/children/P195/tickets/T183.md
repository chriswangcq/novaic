# Audit factory provider multimodal adapter preservation

## Problem Definition

LLM Factory receives structured multimodal messages from runtime. Its provider adapter must preserve image content in the provider API request schema and logging/detail views must not misleadingly flatten media into plain text or hide all useful request structure.

## Proposed Solution

Locate the LLM Factory service in the workspace, inspect request schema handling, provider adapter code, and log/detail serialization. Verify or add focused tests that pass an OpenAI-style `image_url` message through the adapter/request logging path and assert media stays structured while text fields remain text-only.

## Acceptance Criteria

- Factory service/provider adapter code path is mapped.
- OpenAI-compatible multimodal message content is preserved in provider request payloads.
- Raw image base64 is not placed into plain text fields.
- Request/detail logging behavior remains useful and does not silently collapse multimodal content into `{}` or unhelpful placeholders.
- Focused factory/provider tests pass.

## Verification Plan

Search the repository for Factory service modules, `chat/completions`, provider clients, and log APIs. Run focused factory tests; add a regression test if no existing test covers multimodal adapter preservation.

## Risks

- Factory service may live outside `novaic-agent-runtime`; avoid assuming runtime tests cover it.
- Some providers may not support images; unsupported providers should fail explicitly or stay outside active model routing rather than silently flattening.

## Assumptions

- Runtime-to-factory preservation is covered by P194.
