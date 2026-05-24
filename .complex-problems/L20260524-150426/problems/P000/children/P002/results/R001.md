# T002 Result: API-host runtime is non-conservative

## Summary

Activated `dry_run_default=false` on the API-host release-controller, deployed a new controller image, and proved both manual omitted-`dry_run` and autonomous polling execute real staging releases.

## Done

- Updated `/opt/novaic/release-controller/config.json` to `"dry_run_default": false`.
- Restarted the running controller and verified health.
- Committed and pushed source default/doc change:
  - `dad56939 fix: make release controller non-conservative by default`
- Built and deployed release-controller image from the non-conservative source:
  - `127.0.0.1:5000/novaic/release-controller@sha256:18d99cad9d2a1e659255c868374f361a3d90a1b4185794f8aaef3d750983892c`
- Fixed the release-controller deploy health gate to wait for readiness instead of checking too early.
- Committed and pushed:
  - `31249425 fix: wait for release controller health during deploy`
- Built and deployed latest release-controller image:
  - `127.0.0.1:5000/novaic/release-controller@sha256:078ab06205b3bdc51d61d32b8e3dc8752d94fb41c516dbf90fe0229e7ce1b2dc`

## Verification

- Runtime config inspection on API host:
  - `dry_run_default`: `false`
  - `polling_enabled`: `true`
  - branch rules: `main -> staging`, `preview/* -> preview-{slug}`, `release/* -> candidate_only`
- Omitted-`dry_run` manual trigger:
  - run `20260524-071356-main-312494256d5a`
  - status `succeeded`
  - execution `dry_run=false`
  - all steps succeeded: fetch, checkout, submodule sync/update, verify, build, push, deploy API, deploy Factory, smoke.
- Autonomous polling after policy switch:
  - run `20260524-071042-main-dad56939ae39` succeeded and deployed staging automatically.
  - run `20260524-071515-main-312494256d5a` succeeded and updated `branch_heads.main` to `312494256d5ae0d3d5642b430a3cb231230464c8`.
- Final health checks:
  - `http://127.0.0.1:29999/api/health`: 200.
  - `http://127.0.0.1:29990/health`: 200.
  - `https://staging-api.gradievo.com/api/health`: 200.
  - `http://127.0.0.1:19880/health`: 200.
- Final running staging images:
  - API backend services: `127.0.0.1:5000/novaic/api-backend:sha-312494256d5a`.
  - LLM Factory: `127.0.0.1:5000/novaic/llm-factory:sha-312494256d5a`.

## Known Gaps

- none

## Artifacts

- API-host runtime config: `/opt/novaic/release-controller/config.json`
- Release-controller image: `sha256:078ab06205b3bdc51d61d32b8e3dc8752d94fb41c516dbf90fe0229e7ce1b2dc`
- Main commits: `dad56939`, `31249425`
