# P627 Success Check

## Summary

P627 is solved. The one-go classification was broad, but the evidence maps the plausible risky hits and separates user shell execution from process supervision/test harness code. No active runtime local shell bypass remains visible.

## Evidence

- `p627-runtime-residue-scan.txt` records exact runtime risky-term scans and generated-residue counts.
- `p627-runtime-residue-slices.txt` cites VMControl subprocess supervision, runtime roster, shell handler, bridge path, and guard tests.
- `p627-runtime-residue-classification.md` classifies production/test/risky hits.
- `p627-runtime-residue-tests-rerun.txt` shows 17 focused tests passed from correct cwd.
- `p627-tool-path-contract-tests.txt` shows 9 tool path contract tests passed.

## Criteria Map

- Exact scans recorded: satisfied.
- Representative production/test slices cited: satisfied.
- Direct execution/fallback-looking production hits classified: satisfied.
- Risky active shell bypass follow-up: not needed; none found.
- Focused guard tests pass: satisfied after correct cwd rerun.

## Execution Map

- Set P627/T621 executing.
- Captured risky-term scan and pycache tracking checks.
- Captured production/test slices.
- Ran focused tests once from root, observed invocation failure, reran from correct runtime cwd.
- Ran tool path contract tests.
- Recorded R615.

## Stress Test

The skeptical case is that `subprocess.Popen` in `main_novaic.py` could hide a shell bypass. The cited slice shows it launches the Rust VMControl service with explicit args and streams service logs; the active tool shell path remains `_exec_shell -> CortexBridge.shell_exec -> /v1/internal/shell`. Tests also assert direct executor names remain limited to final harness tools and migrated interface tools stay shell capabilities.

## Residual Risk

Generated untracked `__pycache__` files remain as workspace hygiene; they are not tracked and not runtime source. Clean before final status or commit. No active runtime bypass follow-up is needed.

## Result IDs

- R615
