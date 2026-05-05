# PR-220 Cortex Payload / Base64 Residue Review

| Field | Value |
| --- | --- |
| Status | `[closed]` |
| Type | Cortex payload contract cleanup |
| Created | 2026-05-05 |
| Scope | `novaic-cortex/novaic_cortex` |
| Dependencies | Blob Service cutover, PR-218 |

## Goal

Confirm whether remaining base64 usage in Cortex is protocol-local encoding or a
retired payload data-plane branch. Remove or rename anything that implies Cortex
stores large/raw payloads directly instead of using Blob-backed refs.

## Small Tickets

### 1. Blob Payload Encoding Review

- Objective: inspect `blob_payload.py` and classify each base64 use.
- Scope: payload serialization/deserialization and tests.
- Expected result: allowed encoding is named as transport/manifest encoding;
  retired direct payload paths are removed.
- Verification: payload tests and targeted residue scan.

### 2. Legacy Skill Endpoint Review

- Objective: verify whether old skill endpoint comments/aliases remain in
  Cortex API code.
- Scope: `api.py`, route tests, docs references.
- Expected result: active API names match current skill contract without legacy
  alias guidance.
- Verification: route tests and targeted `rg`.

### 3. Prompt/Payload Guard Review

- Objective: ensure raw payloads do not re-enter prompt/context builders by
  default.
- Scope: payload refs, prompt/context assembly tests.
- Expected result: tests make Blob ref boundary explicit.
- Verification: Cortex test suite and guard script.

## Acceptance

- Cortex base64 usage is either gone or explicitly protocol-local.
- No Cortex code path implies direct large payload storage.
- Skill API comments/routes do not advertise retired aliases as current.

## Verification

- `cd novaic-cortex && pytest -q`
- `cd novaic-cortex && python scripts/check_cortex_boundary.py`
- targeted `rg` for `base64`, `legacy`, `compat`, and raw payload wording.

## Closure Notes

- Replaced Cortex JSON/base64 blob writes with Blob Service multipart upload.
- Added a guard test to keep `HttpBlobPayloadClient.put_payload()` on
  `/v1/blobs/uploads` and out of `base64` encoding.
- Reworded Cortex comments around skill and storage boundaries so they describe
  the current contract rather than retired aliases.
