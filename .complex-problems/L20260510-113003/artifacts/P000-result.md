# Result: Sandbox Core Final Extraction

## Done

- Created `novaic-sandbox-core` as the independent sandbox substrate package.
- Moved sandbox contracts, client, process runner, mount namespace helpers, filesystem helpers, and substrate tests into `novaic-sandbox-core/sandbox_core`.
- Removed the old `novaic-common/common/sandbox` package and the old `novaic-common/tests/test_sandbox_infra.py` test file.
- Rewired active import paths in Cortex and sandboxd from `common.sandbox` to `sandbox_core`.
- Updated `scripts/start.sh` so sandboxd and Cortex explicitly include `novaic-sandbox-core` on `PYTHONPATH`.
- Updated `scripts/run_all_tests.sh` so sandbox-core has its own test step and sandbox-service/Cortex tests include the core package explicitly.
- Updated `deploy` so all backend restart paths sync the sandbox substrate package and sandboxd daemon before `start.sh` is invoked.

## Verification

- `PYTHONPATH=novaic-sandbox-core pytest -q novaic-sandbox-core/tests` passed: 9 tests.
- `PYTHONPATH=novaic-sandbox-core:novaic-common:novaic-sandbox-service pytest -q novaic-sandbox-service/tests` passed: 5 tests.
- `PYTHONPATH=novaic-sandbox-core:novaic-common:novaic-cortex pytest -q novaic-cortex/tests/test_sandboxd_wiring.py novaic-cortex/tests/test_sandbox_requires_mount_namespace.py` passed: 3 tests.
- `PYTHONPATH=novaic-common:novaic-sandbox-core pytest -q novaic-common/tests` passed: 139 tests.
- `bash -n deploy && bash -n scripts/start.sh && python3 scripts/ci/lint_deploy_fresh_smoke.py` passed.
- Import smoke passed for `sandbox_core.SandboxdProcessRunner`, `sandbox_core.BindMountPlan`, and `common.config.ServiceConfig.SANDBOXD_URL`.
- Local sandboxd live smoke passed: `/health` returned OK and `/v1/execute` returned `exit_code=0`.
- Residue scan found no `common.sandbox` or `common/sandbox` references outside ignored generated/cache paths.

## Residual Risk

- This ticket intentionally leaves service config in `novaic-common`; sandbox execution substrate has moved out, but global config ownership remains unchanged.
