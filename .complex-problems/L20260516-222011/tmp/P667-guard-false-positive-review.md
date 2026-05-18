# P667 Guard False-Positive and Stale-Assumption Review

## Reviewed guards

- `scripts/ci/lint_blob_workspace_boundary.py`
  - Scan roots are active runtime source roots only: Cortex runtime, LogicalFS runtime, Sandbox Service runtime.
  - Policy has explicit allowed object-authority and BlobRef paths in `novaic-cortex/cortex_tests/blob_boundary_policy.py`.
  - Retained: precise enough; avoids docs/tests and allows LogicalFS adapter boundary.
- `scripts/ci/lint_generated_artifacts.sh`
  - Broad by design, but only generated cache/artifact types: `__pycache__`, `.pytest_cache`, `*.egg-info`, `*.pyc`.
  - Retained: appropriate physical cleanup guard; P666 cleaned current residues.
- `scripts/ci/lint_retired_runtime_vocabulary.py`
  - Uses specific retired tokens rather than broad `legacy` ban.
  - Retained: protects exact retired runtime paths while allowing historical test names/docs outside scan scope.
- `scripts/ci/lint_lifecycle_loop_ownership.sh`
  - Scans subscriber/runtime ownership paths and checks for required ownership functions.
  - Retained: contract-specific; not a broad ban on lifecycle words.
- `scripts/ci/lint_wake_continuity_contract.sh`
  - Scans active source paths, excludes tests, and bans two retired implicit-continuity field names.
  - Retained: precise vocabulary guard.
- `scripts/ci/test_no_legacy_file_hot_paths.py`
  - Scans active runtime code/resource paths for retired file-service/storage tokens.
  - Retained: has explicit active path list and avoids broad whole-repo docs/roadmap scanning.
- `scripts/ci/lint_cortex_boundary.sh`
  - Delegates to Cortex boundary checker; dry-run passes.
  - Retained: current Cortex boundary guard.
- `scripts/ci/lint_deploy_fresh_smoke.py`
  - Checks concrete deploy/runbook/workflow strings for fresh-smoke and retired package cleanup.
  - Retained: specific to deploy contract.

## Dry-run evidence

- `.complex-problems/L20260516-222011/tmp/P667-guard-dry-runs.txt`
- `.complex-problems/L20260516-222011/tmp/P667-adjacent-guard-dry-runs.txt`
- `.complex-problems/L20260516-222011/tmp/P667-generated-artifacts-final.txt`

## Patch decision

No guard source patch needed. The only concrete failing condition was generated artifact residue, already physically cleaned in P666. The reviewed broad-looking terms are either scoped to active paths or intentionally exact retired-token checks.
