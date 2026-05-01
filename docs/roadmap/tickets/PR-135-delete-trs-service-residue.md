# PR-135 — Delete TRS service residue

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Scope | root scripts/docs, `novaic-app` packaged backend assets, production service filesystem |
| Depends | PR-134 |
| Goal | Physically remove the old TRS service artifacts and interaction residue after Cortex became the only tool-result owner. |
| Non-goal | Rename OpenAI-style `tool_result` message concepts or Cortex `step_result_projection`; those are not the retired TRS service. |

## Background

PR-134 removed active TRS service/client/fallback code from Cortex, Runtime, Common, and App UI. A follow-up filesystem audit still found residue:

- root `dist/novaic-storage-b`;
- root `dist/novaic-tools-server`, whose historical binary still contains TRS code;
- packaged App backend asset `src-tauri/gen/apple/assets/backends/novaic-storage-b`;
- packaged App backend asset `src-tauri/gen/apple/assets/backends/novaic-tools-server`, whose historical binary still contains TRS code;
- dev/validation scripts still referenced `novaic-storage-b` or port `19994`;
- docs/runbooks still suggested inspecting `tool_results.db`;
- production still had stale `/opt/novaic/services/novaic-tools-server` files containing `tools_server/trs.py`.

## Implementation Checklist

- [x] Delete tracked TRS-era packaged service artifacts from root/App assets.
- [x] Remove `storage-b` from test/build docs and scripts.
- [x] Remove port `19994` from desktop fresh-profile validation scripts.
- [x] Update current Entangled/cache docs so `tool_results.db` is marked retired instead of an active debugging target.
- [x] Remove production stale `novaic-tools-server` service directory.

## Unit Test Requirements

- [x] Re-run focused Cortex/Runtime/Common/App tests touched by PR-134 to ensure no TRS code path is needed.
- [x] Run static grep guard against active code paths for `TRS`, `trs:`, `trsid`, `trs_client`, `tool_result_service`, `tool-result-service`, `api/trs`, `novaic-storage-b`, and `19994`.

## Smoke Test Requirements

- [x] Verify backend status remains healthy after deleting production stale service residue.
- [x] Verify no process or listening port remains for the retired TRS service.

## Deploy / GitHub

- [x] Commit root and App cleanup.
- [x] Push affected repos.
- [x] Production evidence: `/opt/novaic/services/novaic-tools-server` absent and no `:19994` listener.

Production evidence recorded 2026-05-01:

- `./deploy status` green for Entangled, Gateway, Business, Device, Queue, File, Cortex, workers, and relay.
- `/opt/novaic/services/novaic-tools-server` is absent.
- No `:19994` listener and no retired TRS/storage-b/tools-server process snapshot.
- Root/App packaged backend asset scan found no `novaic-storage-b`, `novaic-tools-server`, `tool-result`, or `trs` files.
