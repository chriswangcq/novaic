# PR-199 — Blob Service Contract / Domain Model

| Field | Value |
| --- | --- |
| Status | `[done]` |
| Owner | Codex |
| Created | 2026-05-04 |
| Repos | `novaic-common`, docs |
| Depends on | PR-170, PR-198 |
| Theme | Blob infrastructure boundary |

## Goal

Define the shared Blob Service contract before changing any runtime path. The contract must make Blob Service a byte/object infrastructure, not a business file service and not a Cortex replacement.

## Current-State Analysis

The old product-file service shape has been removed from active code and
deployment. The remaining contract is the shared BlobRef boundary in
`novaic-common`, while Cortex keeps its own work-trace store and externalizes
large payload bytes only through Blob Service refs.

## Small Tickets

- [x] PR-199A — Add common BlobRef contract and parser helpers.
- [x] PR-199B — Add namespace and metadata invariant tests.
- [x] PR-199C — Add reference documentation for Blob Service boundaries.

## Done Criteria

- Shared contract defines `blob://{namespace}/{blob_id}`.
- Allowed namespaces include `user-file`, `cortex-payload`, `runtime-artifact`, and `audio-input`.
- Blob metadata is infrastructure-only: tenant, namespace, blob id, MIME, size, hash, timestamps.
- Contract rejects malformed refs and raw payload embedding.
- Tests pass in `novaic-common`.

## Deployment Checklist

- [x] Code merged to `novaic-common` main.
- [x] Parent repo submodule pointer bumped if needed.
- [x] No runtime deploy required unless a service imports the new contract in this PR.

## Result

Added `common.contracts.blob` with `BlobRef`, `make_blob_ref`,
`parse_blob_ref`, and metadata invariant validation. Added
`common/contracts/blob.json` as the contract source and
`docs/reference/blob-service.md` as the product boundary note.

## Verification

- `python3 -m pytest tests/test_blob_contract.py tests/test_cortex_observation_contract.py tests/test_environment_contract.py`
- `python3 -m compileall -q common tests`
- `PYTHONPATH=/Users/wangchaoqun/new-build-novaic/novaic-agent-runtime:/Users/wangchaoqun/new-build-novaic/novaic-common python3 -m pytest` (`127 passed`)
