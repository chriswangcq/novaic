# Deploy persisted-result controller image and verify remote run record

## Problem

The API-host controller must be upgraded to an immutable image built from the persistence commit, and a remote verification run must prove `/v1/runs/{run_id}` exposes persisted `execution_result.results` after the request completes.

## Success Criteria

- A new `novaic/release-controller` image is built and pushed on the API host from the persistence commit.
- The controller is deployed by immutable digest through the existing release-controller image path.
- A safe remote verification run creates or observes a persisted run with non-empty `execution_result.results` from `/v1/runs/{run_id}`.
- Polling is restored and `/v1/status` reports `polling.last_error=null`.
- Prod/staging release pointers are checked after deployment and any intentional staging movement is recorded.
