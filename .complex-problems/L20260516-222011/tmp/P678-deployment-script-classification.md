# P678 Deployment Script Candidate Classification

## Source Artifacts

- Candidate files: `.complex-problems/L20260516-222011/tmp/P677-candidate-files.txt` (139 lines)
- Keyword scan: `.complex-problems/L20260516-222011/tmp/P677-keyword-scan.txt` (13128 lines)
- Scan summary: `.complex-problems/L20260516-222011/tmp/P677-scan-summary.txt`

## Active Cloud / Production Deployment Surfaces

- `deploy`: root unified deployment entry. Evidence: syncs services to `/opt/novaic/services`, deploys backend infra substrate, syncs `start.sh`, restarts remote backends through `/opt/novaic/start.sh`, and runs fresh backend log smoke. Uses runtime worker roster at `/opt/novaic/services/novaic-agent-runtime/scripts/runtime_worker_roster.py`.
- `scripts/start.sh`: cloud backend start script. Evidence: declares canonical backend ports for Entangled, Gateway, Business, Device, Queue Service, Blob Service, Sandboxd, and Cortex; launches runtime workers through `runtime_roster launch-commands`; verifies required runtime subprocesses through `runtime_roster process-checks`.
- `novaic-agent-runtime/scripts/runtime_worker_roster.py`: CLI adapter over `task_queue.workers.runtime_roster`; active SSOT bridge consumed by `deploy` and `scripts/start.sh`.
- `scripts/ci/check_start_config_contract.py`, `scripts/ci/lint_deploy_fresh_smoke.py`, `scripts/ci/lint_runtime_worker_supervision.py`: active CI/static guards for deployment config, fresh log smoke, and worker supervision assumptions.

## Active / High-Signal Local Development Backend Surfaces

- `novaic-app/scripts/start-backends.sh`: dev-mode backend launcher. Evidence: starts Gateway, Queue Service, Blob Service, and multiple runtime workers. It should be remediated/checked because its header says "all Python backends" while the inspected body did not show Entangled, Business, Device, Cortex, or Sandboxd startup.
- `novaic-app/scripts/split/launch_split_only.sh`, `novaic-app/scripts/split/stop_split_only.sh`, `novaic-app/scripts/split/build_split_only.sh`, `novaic-app/scripts/split/Launch-NovAIC-Split.command`: active-ish split local app helpers; inspect only if local split dev path is in scope.
- `novaic-agent-runtime/scripts/run_split_replay_smoke.sh`: focused split runtime smoke wrapper; active test helper rather than deploy launcher.

## Packaged / Generated Resource Backend Launchers Requiring Caution

- `novaic-app/src-tauri/resources/backends/start-backends.sh`: packaged resource launcher. Evidence: starts only Blob Service, Gateway, and `novaic-agent-runtime` on `AGENT_RUNTIME_PORT=19991`; this appears stale relative to current queue-service/Cortex/Sandboxd/worker topology and should be inspected by remediation.
- `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh`: generated copy of the packaged launcher; do not edit directly unless generation source is intentionally regenerated. Treat as generated/stale evidence.

## Active Ops / Peripheral Deploy Scripts

- `novaic-app/scripts/deploy-frontend.sh`: active frontend OTA deploy script for relay static assets.
- `novaic-blob-service/scripts/smoke_blob_service.sh`: active Blob service smoke script; relevant to smoke ergonomics more than process topology.
- `novaic-blob-service/scripts/blob_service_backup.sh`, `novaic-blob-service/scripts/blob_service_restore.sh`, `novaic-blob-service/scripts/verify_contract_version_blob.sh`: active Blob ops/verification helpers.
- `novaic-quic-service/deploy/deploy.sh`, `novaic-quic-service/deploy/*.service`, `novaic-quic-service/deploy/setup-*.sh`: relay/quic deployment scripts; peripheral to core backend process topology.
- `novaic-gateway/nginx/deploy-nginx.sh`: nginx config deploy helper; peripheral ops script.
- `scripts/build-all.sh`, `scripts/run_all_tests.sh`, `scripts/check-ota-sync.sh`: active root build/test/sync helpers, not backend process topology launchers.

## Test-Only / Guard-Only Candidates

- `novaic-agent-runtime/tests/test_pr*_worker*`, `test_scheduler_dispatch.py`, `test_health_dispatch.py`, and similar tests: test-only validation surfaces, not deployment scripts.
- `Entangled/packages/server-python/tests/test_health_readiness.py`, `novaic-blob-service/tests/test_blob_service.py`, `novaic-sandbox-service/tests/test_sandbox_service.py`, and common tests: test-only.
- `scripts/ci/*`: active guard scripts, but not runtime launch scripts except where explicitly validating deployment/start contracts.

## Docs / Historical / Roadmap Candidates

- `docs/cortex/deployment-and-startup.md`, `docs/runbooks/deploy.md`, `docs/runbooks/local-backends.md`, `docs/runbooks/cloud-production.md`, and architecture docs: documentation surfaces; P674 should verify their consistency with code evidence.
- `docs/roadmap/tickets/*`: historical roadmap/ticket archaeology; do not treat old process names there as active bugs unless current docs/scripts reference them.

## Example / Unrelated Candidates

- `examples/tauri-ios-hello/scripts/*`: example app scripts, unrelated to backend process topology.
- `novaic-app/scripts/build-dmg.sh`, iOS patch/build helpers, emulator trimming, STUN helpers: app/platform tooling, not core backend process topology.
- Source entrypoint files such as `main_blob_service.py`, `main_sandbox_service.py`, worker Python modules, and health API files belong primarily to P673 entrypoint topology inventory rather than P676 script remediation.

## Remediation Inputs for P676

Prioritize these files in P676:

1. `novaic-app/scripts/start-backends.sh` - active dev launcher appears incomplete/stale versus current service topology.
2. `novaic-app/src-tauri/resources/backends/start-backends.sh` - packaged launcher appears stale and may be active in app resources.
3. `novaic-app/src-tauri/gen/apple/assets/backends/start-backends.sh` - generated copy of stale packaged launcher; update via source/regeneration if required.
4. `scripts/start.sh` and `deploy` - current cloud path looks well-aligned with runtime roster, but should be inspected for syntax and guard verification rather than assumed correct.
5. `scripts/ci/check_start_config_contract.py`, `scripts/ci/lint_deploy_fresh_smoke.py`, `scripts/ci/lint_runtime_worker_supervision.py` - verify they cover the active launchers and do not only guard cloud script paths.
