# Explicit Cortex API URL for Shell LogicalFS Environment result

## Summary

Removed the remaining runtime `http://localhost:19996` fallback path from the Cortex shell LogicalFS environment. `Cortex`, `Sandbox`, and `MountNamespaceLogicalFS` now require an explicit `cortex_api_url`, and `main_cortex.py` requires `--cortex-api-url` at startup before shell capability scripts can receive `NOVAIC_API`.

## Changes Made

- `novaic-cortex/novaic_cortex/logical_fs.py`: `MountNamespaceLogicalFS` now requires `cortex_api_url` explicitly and injects that value into shell capability env/config.
- `novaic-cortex/novaic_cortex/sandbox.py`: `Sandbox` now requires `cortex_api_url` and passes it into LogicalFS.
- `novaic-cortex/novaic_cortex/runtime.py`: `Cortex` now requires and stores the explicit URL, passing it through every sandbox construction path.
- `novaic-cortex/novaic_cortex/api.py`: HTTP app construction now refuses to build `Cortex` without `set_cortex_api_url`; the setter also supports explicit test cleanup via `None`.
- `novaic-cortex/novaic_cortex/main_cortex.py`: Cortex service startup requires `--cortex-api-url` and installs it into the API boundary.
- `scripts/start.sh`: production startup passes `--cortex-api-url "$CORTEX_URL"`.
- `docs/cortex/deployment-and-startup.md`: startup documentation records the explicit URL contract.
- `novaic-cortex/tests/test_sandboxd_wiring.py` and `novaic-cortex/tests/test_sandbox_requires_mount_namespace.py`: tests now pass explicit fake Cortex API URLs rather than relying on runtime defaults.

## Verification

Focused regression suite passed:

```text
cd novaic-cortex && PYTHONPATH="$PWD:$PWD/../novaic-logicalfs:$PWD/../novaic-sandbox-sdk:$PWD/../novaic-common" python -m pytest tests/test_pr75_proxy_boundary.py tests/test_shell_capabilities_blob_contract.py tests/test_shell_capabilities_internal_auth.py tests/test_sandbox_requires_mount_namespace.py tests/test_sandboxd_wiring.py -q
20 passed in 2.45s
```

Runtime fallback scan:

```text
rg -n "http://localhost:19996|/tmp/.novaic_env|cortex_api_url: str =" novaic-cortex scripts/start.sh docs/cortex/deployment-and-startup.md -g'*.py' -g'*.sh' -g'*.md'
```

Observed no active `http://localhost:19996` fallback and no `/tmp/.novaic_env` runtime path. Remaining matches are limited to a test assertion that the old tmp fallback is absent, plus a test helper fake URL default (`http://cortex.test`) outside production runtime.

## Residual Risk

The production runtime path is explicit. The only remaining URL default is the test utility `make_cortex_with_store(..., cortex_api_url="http://cortex.test")`; if the checker wants absolute no-default purity even in test helpers, that should be a follow-up rather than hiding it in this result.
