# T000 Result: Release-controller is non-conservative by default

## Summary

Completed the policy switch from conservative dry-run default to clean real-execution default for the centered release-controller.

## Done

- P001 changed source defaults, tests, and docs:
  - `ControllerConfig.dry_run_default` now defaults to `False`.
  - `config.sample.json` uses `"dry_run_default": false`.
  - docs describe omitted `dry_run` as real staging execution and explicit `dry_run=true` as observation.
- P002 activated runtime:
  - API-host `/opt/novaic/release-controller/config.json` has `dry_run_default=false`.
  - controller was restarted/redeployed.
  - latest controller digest deployed: `sha256:078ab06205b3bdc51d61d32b8e3dc8752d94fb41c516dbf90fe0229e7ce1b2dc`.
  - omitted-`dry_run` trigger succeeded with `dry_run=false`.
  - autonomous polling also succeeded with real staging deployment.
- Prod remains promotion-only.

## Verification

- P001 check `C000` passed.
- P002 check `C001` passed.
- Test matrix:
  - release-controller tests: 36 passed.
  - release-controller CI guard: 6 passed.
  - repo pytest: 11 passed.
  - `bash -n deploy`: passed.
- Runtime proof:
  - manual omitted-`dry_run` run `20260524-071356-main-312494256d5a` succeeded.
  - poll run `20260524-071515-main-312494256d5a` succeeded.
  - final staging API/Factory/public HTTPS/controller health checks returned 200.

## Known Gaps

- none

## Artifacts

- Main commits:
  - `dad56939 fix: make release controller non-conservative by default`
  - `31249425 fix: wait for release controller health during deploy`
- Runtime image:
  - `127.0.0.1:5000/novaic/release-controller@sha256:078ab06205b3bdc51d61d32b8e3dc8752d94fb41c516dbf90fe0229e7ce1b2dc`
