## T006 Result: CI full matrix 与架构守卫门禁接入

### Done

- Added `python3 scripts/ci/lint_retired_runtime_vocabulary.py` to `.github/workflows/lint.yml`.
- Added runtime architecture guard checks to `scripts/run_all_tests.sh` before package pytest suites:
  - `lint_runtime_worker_supervision.py`
  - `lint_deploy_fresh_smoke.py`
  - `lint_retired_runtime_vocabulary.py`
  - `check_start_config_contract.py`
- Kept the CI boundary explicit: each guard is invoked by name, with no hidden shell state or soft-fail wrapper.

### Verification

- `bash -n scripts/run_all_tests.sh`
- `python3 scripts/ci/lint_runtime_worker_supervision.py`
- `python3 scripts/ci/lint_deploy_fresh_smoke.py`
- `python3 scripts/ci/lint_retired_runtime_vocabulary.py`
- `python3 scripts/ci/check_start_config_contract.py`
- `python3 -m pytest -q`
- `rg -n "lint_retired_runtime_vocabulary|runtime-worker-supervision-lint|deploy-fresh-smoke-lint|start-config-contract-lint" .github/workflows/lint.yml scripts/run_all_tests.sh`

### Artifacts

- `.github/workflows/lint.yml`
- `scripts/run_all_tests.sh`

### Gaps

- The complete package matrix remains for P006 final verification so failures are triaged at the global closure layer rather than inside this CI-wiring ticket.
