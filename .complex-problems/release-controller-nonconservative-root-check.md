# P000 Check: Success

## Summary

The release-controller is now in the requested clean, non-conservative operating state.

## Evidence

- Source defaults are non-conservative:
  - `ControllerConfig.dry_run_default` defaults to `False`.
  - `novaic-release-controller/config.sample.json` has `"dry_run_default": false`.
- Docs now say omitted `dry_run` follows the runtime default and current runtime default is real staging execution.
- API-host runtime config reports `dry_run_default=false`.
- Running controller image is `sha256:078ab06205b3bdc51d61d32b8e3dc8752d94fb41c516dbf90fe0229e7ce1b2dc`.
- Omitted-`dry_run` trigger run `20260524-071356-main-312494256d5a` succeeded and reported `dry_run=false`.
- Autonomous poll run `20260524-071515-main-312494256d5a` succeeded and updated `branch_heads.main`.
- Final staging API, staging LLM Factory, public staging HTTPS, and release-controller health checks all returned 200.
- Branch rules still keep prod out of automatic branch deployment.

## Criteria Map

- Repository defaults and docs no longer describe dry-run as normal operation -> P001/R000/C000.
- Sample config uses `dry_run_default=false` -> P001/R000/C000.
- API-host runtime config uses `dry_run_default=false` -> P002/R001/C001.
- Running controller restarted/redeployed after config change -> P002/R001/C001.
- Omitted `dry_run` trigger executes `dry_run=false` -> run `20260524-071356-main-312494256d5a`.
- Staging health passes after execution -> final health checks 200.
- Prod remains protected -> branch rules inspection: `main -> staging`, `preview/* -> preview-{slug}`, `release/* -> candidate_only`.
- Ledger closes -> this check plus final validate/render/status.

## Execution Map

- T000 split the root into P001 and P002.
- T001/R000 updated source defaults/docs/tests and passed source verification.
- T002/R001 activated API-host runtime, deployed controller image, ran manual omitted-`dry_run`, observed autonomous polling, and verified runtime health.
- R002 summarized closed child results.

## Stress Test

- Stale source fallback to conservative dry-run: fixed by model default and sample config.
- Stale docs implying dry-run default: removed and searched in target docs/config.
- Runtime config drift from source: checked directly on API host.
- Omitted trigger silently dry-runs: rejected by execution result `dry_run=false`.
- Autonomous polling remains observe-only: rejected by successful poll-triggered staging deploy.
- Prod accidentally auto-deploys from branch: rejected by branch rules.
- Health gate false negative on controller redeploy: fixed by bounded health wait in `deploy`.

## Residual Risk

The system now really deploys staging on matching branch head changes. That is the requested non-conservative state and is not treated as a residual gap. Prod remains protected by promotion-only rules.

## Result IDs

- R002

## Blocking Gaps

- none
