# PR-201 — Unified ResourceRef Blob URI Cutover

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-common`, `novaic-business`, `novaic-agent-runtime`, `novaic-cortex`, `novaic-app`, docs |
| Depends on | PR-199, PR-200 |
| Theme | Resource reference SSOT |

## Goal

Make `blob://{namespace}/{blob_id}` the only new large-object reference shape across services.

## Current-State Analysis

Current paths still include `fs://` for Storage-A files and `payload_ref` values for Cortex payloads. These are separate concepts and should converge through a shared ResourceRef parser and ownership model.

## Small Tickets

- [x] PR-201A — Add shared ResourceRef helpers for BlobRef adoption.
- [x] PR-201B — Update Business/Environment ResourceRef validation and schema constraints to accept BlobRef only for new refs.
- [x] PR-201C — Mark `fs://` as historical/import-only in active docs.
- [x] PR-201D — Add guard tests preventing new Environment ResourceRefs from using storage-a/`fs://`/`oss://` style locators.
- [x] PR-201E — Keep App attachment and Gateway proxy migration explicitly deferred to PR-203/PR-205 rather than half-switching the hot path.

## Done Criteria

- New large-object refs use `blob://`.
- Existing `fs://` reads are either migrated or explicitly isolated behind one import/compat boundary.
- Guardrails prevent new code from producing `fs://` on active paths.

## Deployment Checklist

- [x] `novaic-common` contract tests pass.
- [x] `novaic-business` Environment tests pass.
- [x] Parent docs updated to make File Service historical/import-only.

## Implementation Notes

- Added `common.contracts.resource_ref` as the shared ResourceRef SSOT.
- New ResourceRefs must use owner `blob-service` and a `blob://...` locator.
- Legacy locators such as `fs://`, `/api/files/*`, `oss://`, and raw HTTP URLs are detection-only for migration tooling; they are not valid new ResourceRefs.
- Environment `validate_environment_resource_ref` now delegates to the shared ResourceRef validator.
- Business entity schema now includes guard constraints for `environment-resource-refs`: `owner = 'blob-service'` and `locator LIKE 'blob://%'`.
- App upload/Gateway proxy/runtime display/audio executor migration remains in PR-203/PR-205 because those are live product flows and need separate smoke/deploy closure.

## Verification

- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common python3 -m pytest tests/test_resource_ref_contract.py tests/test_blob_contract.py tests/test_environment_contract.py`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-business python3 -m pytest tests/test_environment_repository.py tests/test_environment_schema_contracts.py`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime:/Users/wangchaoqun/new-build-novaic/novaic-common python3 -m pytest` in `novaic-common` → `130 passed`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-common:/Users/wangchaoqun/new-build-novaic/novaic-business python3 -m pytest` in `novaic-business` → `156 passed`
