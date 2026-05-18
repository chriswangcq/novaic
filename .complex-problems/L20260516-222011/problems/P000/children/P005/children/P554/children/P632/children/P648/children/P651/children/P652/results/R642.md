# Remove Cortex API URL Default from Test Helper result

## Summary

Removed the hidden `http://cortex.test` default from `make_cortex_with_store` and updated all Cortex tests using that helper to pass `cortex_api_url="http://cortex.test"` explicitly.

## Changes Made

- `novaic-cortex/cortex_tests/workspace_test_utils.py`: `make_cortex_with_store` now requires keyword-only `cortex_api_url: str` with no default.
- Updated helper call sites across Cortex runtime/path/archive/metrics/engine/skill/compaction tests to pass an explicit fake Cortex API URL.
- Fixed a mechanical replacement issue in `test_hooks_limits.py` where nested `CortexHooks()` needed to remain intact.

## Verification

Helper test suite passed:

```text
cd novaic-cortex && PYTHONPATH="$PWD:$PWD/../novaic-logicalfs:$PWD/../novaic-sandbox-sdk:$PWD/../novaic-common" python -m pytest tests/test_archive_invariants.py tests/test_compaction_meta.py tests/test_context_budget_limits.py tests/test_cortex_chaos.py tests/test_engine_wiring.py tests/test_hooks_limits.py tests/test_paths_adversarial.py tests/test_runtime.py tests/test_runtime_path_abuse.py tests/test_skill_install_limits.py tests/test_suggest_compact.py tests/test_tool_metrics.py tests/test_wave4_metrics.py -q
86 passed in 0.45s
```

Postscan:

```text
rg -n "cortex_api_url: str =|http://localhost:19996|/tmp/.novaic_env" novaic-cortex/novaic_cortex novaic-cortex/cortex_tests novaic-cortex/tests scripts/start.sh docs/cortex/deployment-and-startup.md -g'*.py' -g'*.sh' -g'*.md'
```

Only remaining match is the negative assertion in `tests/test_pr75_proxy_boundary.py` that checks the old `/tmp/.novaic_env.json` fallback is absent from source.

## Residual Risk

Low. Tests now state the fake URL explicitly. There are many long single-line helper calls, but they are test code and did not affect execution; future formatting can clean them if desired.
