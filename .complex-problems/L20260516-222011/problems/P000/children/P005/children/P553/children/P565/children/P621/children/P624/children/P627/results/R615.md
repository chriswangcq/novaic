# Runtime Legacy Execution Residue Classification Result

## Summary

Classified runtime-wide direct execution/fallback/host/mount residue. No active runtime user-shell bypass was found; direct subprocess usage is limited to service/process supervision or test harness code, while active shell execution routes through Cortex `/v1/internal/shell`.

## Done

- Recorded risky-term scan in `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-scan.txt`.
- Captured production/test slices in `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-slices.txt`.
- Classified hits in `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-classification.md`.
- Ran focused runtime guard suites and tool path tests.

## Verification

- Initial root-cwd run showed 4 path-related failures in `test_pr315_queue_fsm_final_residue_guard.py`; this was a test invocation issue because that test reads repo-relative paths.
- Correct cwd rerun from `novaic-agent-runtime` passed 17 tests: `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-tests-rerun.txt`.
- `tests/test_runtime_tool_path_contract.py` passed 9 tests: `.complex-problems/L20260516-222011/tmp/p627-tool-path-contract-tests.txt`.

## Known Gaps

- Generated untracked `__pycache__` files should be removed during final workspace hygiene.
- No active runtime execution-bypass follow-up is needed.

## Artifacts

- `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-scan.txt`
- `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-slices.txt`
- `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-classification.md`
- `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-tests.txt`
- `.complex-problems/L20260516-222011/tmp/p627-runtime-residue-tests-rerun.txt`
- `.complex-problems/L20260516-222011/tmp/p627-tool-path-contract-tests.txt`
