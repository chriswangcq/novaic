# Release through controller

## Problem Definition

Ship commit `83fe6bb4bc20a0af96674fd71ea2d9b97e058059` through the central Release Controller path so staging and prod run the fixed immutable backend image.

## Proposed Solution

Use Release Controller autonomous polling or `/v1/triggers` for staging and `/v1/promotions/prod` for prod. Verify run records, current release pointers, and image tags.

## Acceptance Criteria

- Staging run succeeds for `83fe6bb4bc20`.
- Prod promotion run succeeds with the same `sha-83fe6bb4bc20` images.
- Current release pointers for staging and prod reference `83fe6bb4bc20`.
- Deployment did not use the guarded manual `deploy services-image` path directly.

## Verification Plan

Inspect `/v1/runs/<run_id>`, `/v1/status`, and prod/staging container images.

## Risks

- A long-running compose recreate can temporarily show mixed old/new staging services.

## Assumptions

- Release Controller is healthy on API host loopback `127.0.0.1:19880`.
