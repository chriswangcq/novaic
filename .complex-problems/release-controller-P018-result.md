# P018 Result

## Summary

Wired the deployed release-controller to its branch polling path and redeployed it on the API host with a verified poll-once endpoint.

## Done

- Added a service-level `POST /v1/polls/once` endpoint that invokes `BranchPoller`.
- Added `PollOutcome.to_mapping()` so poll results are returned as structured API data.
- Allowed `create_app()` to receive an injected `BranchHeadProvider` for deterministic tests.
- Added service coverage proving `/v1/polls/once` invokes branch polling and returns outcomes.
- Updated release-controller documentation with the poll-once verification command.
- Updated deployment/runbook documentation with an explicit API-host worktree bootstrap command.
- Rebuilt and redeployed the release-controller image on the API host.
- Changed the API-host controller repo URL to `https://github.com/chriswangcq/novaic.git` so branch listing does not depend on host SSH credentials.

## Verification

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: `32 passed`.
- `python3 -m pytest -q scripts/ci/test_release_controller_ci.py`
  - Passed: `6 passed`.
- `python3 -m pytest -q`
  - Passed: `11 passed`.
- `bash -n deploy`
  - Passed.
- API host deployment:
  - Container: `novaic-release-controller-release_controller-1`.
  - Image: `127.0.0.1:5000/novaic/release-controller@sha256:97cd1948122732a6aa6b973a714f33493b075d75dda8edd8fdd386078d4edeb5`.
  - Container health: `healthy`.
  - Local bind: `127.0.0.1:19880`.
  - Nginx references to `release-controller` or `19880`: `0`.
- API host branch polling:
  - `POST http://127.0.0.1:19880/v1/polls/once` with `{"dry_run": true}` returned branch outcomes.
  - `main` at `b3b9d0187a81035a9692b440d5db290022f05bd6` returned `status=planned` with run id `20260524-043122-main-b3b9d0187a81`.
  - Other unmatched branches returned `status=skipped` with reason `unmatched branch`.
- API host health:
  - `curl -fsS http://127.0.0.1:19880/health` returned `{"status":"healthy"}`.

## Known Gaps

- Runtime config still keeps `dry_run_default=true`; this is deliberate until the non-dry-run worktree bootstrap is executed and reviewed.
- The branch polling path is exposed as a poll-once control-plane endpoint; a background timer loop is still optional future hardening rather than required for this ticket.

## Artifacts

- `novaic-release-controller/release_controller/service.py`
- `novaic-release-controller/release_controller/poller.py`
- `novaic-release-controller/tests/test_service.py`
- `docs/architecture/release-controller.md`
- `docs/runbooks/deploy.md`
- API-host image digest: `sha256:97cd1948122732a6aa6b973a714f33493b075d75dda8edd8fdd386078d4edeb5`
