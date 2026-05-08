# P007 Check

## Summary

P007 is successful. CI and the canonical test runner now avoid or clean generated Python/test artifacts, and generated-artifact lint is part of the normal hygiene path.

## Evidence

- Runtime supervision lint sets `sys.dont_write_bytecode = True`.
- Lint workflow sets `PYTHONDONTWRITEBYTECODE=1` and runs generated-artifact lint.
- Canonical test runner sets `PYTHONDONTWRITEBYTECODE=1`, disables pytest cache provider, cleans caches, and runs generated-artifact lint.
- Guard tests cover these entrypoint expectations.

## Criteria Map

- CI guard scripts/wrappers use `PYTHONDONTWRITEBYTECODE=1`: satisfied.
- Generated-artifact lint passes after normal cleanup/check sequence: satisfied.
- Generated cache artifacts from local verification are cleaned: satisfied.

## Execution Map

Verified with:

```bash
PYTHONDONTWRITEBYTECODE=1 pytest -q -p no:cacheprovider tests/test_pr340_ci_generated_artifact_hygiene.py tests/test_pr343_runtime_worker_roster_ssot.py
python3 scripts/ci/lint_runtime_worker_supervision.py
scripts/ci/lint_generated_artifacts.sh
```

Observed:

```text
5 passed in 0.58s
lint_runtime_worker_supervision OK
GENERATED_ARTIFACTS_LINT=PASS
```

## Stress Test

The previous failure mode was reproduced once with bare pytest, then closed by adding no-cache provider handling to the canonical runner and verifying generated-artifact lint passes after cleanup.

## Residual Risk

No blocker for P007.

## Result IDs

- `R006`
