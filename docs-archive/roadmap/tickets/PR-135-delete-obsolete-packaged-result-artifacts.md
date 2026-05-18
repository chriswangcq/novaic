# PR-135 — Delete obsolete packaged result artifacts

| Field | Value |
| --- | --- |
| Status | `[deployed]` |
| Scope | root scripts/docs, `novaic-app` packaged backend assets, production service filesystem |
| Depends | PR-134 |
| Goal | Physically remove obsolete packaged result artifacts and interaction residue after Cortex became the only tool-result owner. |
| Non-goal | Rename OpenAI-style `tool_result` message concepts or Cortex `step_result_projection`; those are active concepts. |

## Background

PR-134 made Cortex the sole result owner. A follow-up filesystem audit still found residue:

- obsolete root packaged backend binaries;
- obsolete App packaged backend assets;
- dev/validation scripts still referenced a removed sidecar port;
- docs/runbooks still suggested inspecting removed local result storage;
- production still had stale packaged backend files.

## Implementation Checklist

- [x] Delete tracked obsolete packaged service artifacts from root/App assets.
- [x] Remove removed sidecar references from test/build docs and scripts.
- [x] Remove removed sidecar port from desktop fresh-profile validation scripts.
- [x] Update current Entangled/cache docs so App cache is the active debugging target.
- [x] Remove production stale packaged backend directory.

## Unit Test Requirements

- [x] Re-run focused Cortex/Runtime/Common/App tests touched by PR-134 to ensure no removed result path is needed.
- [x] Run static grep guard against active code paths for removed result-path names, removed sidecar names, and the removed sidecar port.

## Smoke Test Requirements

- [x] Verify backend status remains healthy after deleting production stale service residue.
- [x] Verify no removed result process or listening port remains.

## Deploy / GitHub

- [x] Commit root and App cleanup.
- [x] Push affected repos.
- [x] Production evidence: stale packaged backend directory absent and no removed result port listener.

Production evidence recorded 2026-05-01:

- `./deploy status` green for Entangled, Gateway, Business, Device, Queue, File, Cortex, workers, and relay.
- Stale packaged backend directory is absent.
- No removed result port listener or removed sidecar process snapshot.
- Root/App packaged backend asset scan found no removed sidecar/result files.
