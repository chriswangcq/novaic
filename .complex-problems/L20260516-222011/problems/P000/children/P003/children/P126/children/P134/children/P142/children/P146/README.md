# write_step payload_ref mirroring audit

## Problem

`write_step` must externalize raw payload data through the workspace payload store and mirror the actual `payload_ref` back into the stored observation. If this fails, step JSON can point at stale refs, miss full-output recovery, or retain large payload data inline.

This child belongs under `P142` because payload pointer integrity is the core boundary between compact step records and full reconstructable tool output.

## Success Criteria

- Source pointers map where `write_step` detects observation payloads and calls payload storage.
- Evidence proves raw payload writes require or produce a `payload_ref`.
- Evidence proves the stored step observation contains the actual persisted `payload_ref`.
- Tests cover local payload and external blob-backed payload behavior where relevant.
