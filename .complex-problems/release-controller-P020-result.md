# P020 Result

## Summary

Added a configurable autonomous branch polling loop to the release-controller service.

## Done

- Added `release_controller.polling.BranchPollingLoop`.
- Added `ControllerConfig.polling_enabled`, defaulting to `false`.
- Wired the loop into the FastAPI lifespan so it starts on service startup and stops on shutdown.
- Exposed polling state in `/v1/status`.
- Updated `config.sample.json` with `polling_enabled: false`.
- Added tests for enabled polling, disabled polling, and invalid config.

## Verification

- `PYTHONPATH=novaic-release-controller python3 -m pytest novaic-release-controller/tests -q`
  - Passed: `35 passed`.
- `python3 -m pytest -q scripts/ci/test_release_controller_ci.py`
  - Passed: `6 passed`.

## Known Gaps

- The API-host runtime config has not been changed yet; enabling the loop on the host belongs to the deployment child problem.

## Artifacts

- `novaic-release-controller/release_controller/polling.py`
- `novaic-release-controller/release_controller/models.py`
- `novaic-release-controller/release_controller/service.py`
- `novaic-release-controller/tests/test_service.py`
- `novaic-release-controller/tests/test_config_models.py`
- `novaic-release-controller/config.sample.json`
