# PR-202 — Cortex Payload Blob Externalization

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-cortex`, `novaic-agent-runtime`, `novaic-common`, docs |
| Depends on | PR-201 |
| Theme | Cortex trace stays semantic |

## Goal

Keep Cortex as the work-trace and scope system, while storing large raw payload bytes in Blob Service and retaining only observation summaries plus `payload_ref`.

## Current-State Analysis

Cortex currently writes payload records into its own scope-local payload store through `Workspace.write_payload`. This means Cortex owns large payload storage directly unless it externalizes large bytes to Blob Service.

## Small Tickets

- [x] PR-202A — Define size thresholds and blob payload policy.
- [x] PR-202B — Write large tool payloads to Blob Service and store `blob://cortex-payload/...` in Cortex.
- [x] PR-202C — Update payload read/search/summarize/qa resolver to support BlobRef through `Workspace.read_payload`.
- [x] PR-202D — Add invariants: default prompt context never includes raw Blob payload.
- [x] PR-202E — Configure production start path to provide Cortex with Blob Service URL.

## Done Criteria

- Small bounded observations remain in Cortex.
- Large payloads are externalized to Blob Service.
- Payload tools can resolve BlobRef explicitly.
- No automatic payload summary or fallback path is added.

## Deployment Checklist

- [x] Cortex tests pass.
- [x] Runtime payload tool tests pass.
- [x] Start config passes local guard.
- [x] Smoke-level unit: large payload produces observation plus `blob://cortex-payload/...`.

## Implementation Notes

- Added `novaic_cortex.blob_payload` as the narrow Cortex ↔ Blob Service adapter.
- `Workspace.write_payload` now serializes payloads to JSON bytes, keeps small payloads in the existing scope-local store, and externalizes payloads larger than `CORTEX_PAYLOAD_BLOB_THRESHOLD_BYTES` to Blob Service.
- Large payload externalization requires `CORTEX_BLOB_SERVICE_URL`; if a payload crosses the threshold and the Blob URL is missing, Cortex fails fast instead of silently falling back.
- `Workspace.write_step` updates both `step.payload_ref` and `step.observation.payload_ref` to the returned `blob://cortex-payload/...` ref when externalized.
- `Workspace.read_payload` resolves external BlobRefs explicitly through Blob Service, so payload read/search/summarize/qa continue to use the same Cortex payload API.
- `scripts/start.sh` exports `CORTEX_BLOB_SERVICE_URL` from the Blob Service URL before starting Cortex.

## Verification

- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-cortex python3 -m pytest` in `novaic-cortex` → `396 passed, 16 skipped`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime python3 -m pytest tests/unit/task_queue/test_payload_tool_handlers.py tests/test_pr85_llm_context_smoke_guardrails.py tests/test_pr71_no_tool_retry_context_cleanup.py` → `19 passed`
- `python3 scripts/ci/check_start_config_contract.py` → `start_config_contract OK`
