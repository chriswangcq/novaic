# Verify Backend Startup Resource And Generated Synchronization

## Problem Definition

After P806-P808, backend startup scripts/config and storage binary copies changed across source resources and generated assets. The final copy boundary must be verified so shipped generated behavior cannot drift from source resources.

## Proposed Solution

Run synchronization checks across backend startup scripts, service config JSON, and backend binary directories. Patch only if copy divergence or stale residues remain. Record intentional binary differences separately from accidental script/config drift.

## Acceptance Criteria

- Resource and generated packaged startup scripts are byte-identical.
- Resource and generated service config JSON files are byte-identical and valid JSON.
- Resource/generated backend binary directory comparison is recorded, including intentional ignored/build-artifact differences.
- All committed startup scripts pass `bash -n`.
- Targeted scans show no stale `PORT_CORTEX`, `vmuse_mcp_url`, `8080/mcp`, or packaged `novaic-blob-service`-only startup residue.

## Verification Plan

- Run `cmp` for packaged scripts and config JSON copies.
- Run `python -m json.tool` on both config JSON files.
- Run `bash -n` on source/dev and packaged startup scripts.
- Run targeted scans for remediated residue terms.
- Compare resource/generated backend directories with `diff -qr` or explicit file lists.

## Risks

- Binary directory differences may be intentional because some source resource binaries are local build artifacts and ignored.
- Generated build output under `gen/apple/build` should not be treated as source-of-truth.

## Assumptions

- Resource and generated `start-backends.sh` and `services.json` should stay synchronized.
- Backend binary copy policy can be documented in the result if it is intentionally not byte-identical for every executable.
