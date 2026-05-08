# P007 Result

## Summary

Hardened CI/generated-artifact hygiene. Runtime supervision lint disables bytecode generation, the lint workflow exports `PYTHONDONTWRITEBYTECODE=1`, and the canonical test runner disables pytest cache, cleans generated Python artifacts, then runs generated-artifact lint.

## Changes

- Updated `scripts/ci/lint_runtime_worker_supervision.py` with `sys.dont_write_bytecode = True`.
- Updated `.github/workflows/lint.yml` with job-level `PYTHONDONTWRITEBYTECODE: "1"` and a generated-artifact lint step.
- Updated `scripts/run_all_tests.sh` to:
  - export `PYTHONDONTWRITEBYTECODE=1`
  - export `PYTEST_ADDOPTS=... -p no:cacheprovider`
  - clean generated Python/test artifacts
  - run `scripts/ci/lint_generated_artifacts.sh`
- Added `novaic-agent-runtime/tests/test_pr340_ci_generated_artifact_hygiene.py`.

## Verification

Executed:

```bash
find novaic-agent-runtime novaic-common -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
cd novaic-agent-runtime
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/test_pr340_ci_generated_artifact_hygiene.py tests/test_pr343_runtime_worker_roster_ssot.py
cd ..
python3 scripts/ci/lint_runtime_worker_supervision.py
scripts/ci/lint_generated_artifacts.sh
```

Observed:

```text
5 passed in 0.58s
lint_runtime_worker_supervision OK
GENERATED_ARTIFACTS_LINT=PASS
```

## Residual Risk

Ad-hoc local `pytest` commands can still create caches. The canonical runner and CI path now avoid/clean them, and the generated-artifact lint catches residue.
