# Dev Startup Port And Service URL Contract Check

## Summary

Success. R788 removes the app startup graph ambiguity by no longer declaring `PORT_CORTEX` in the local subset script and by changing app service config `19996` from `vmcontrol` to `cortex`.

## Evidence

- R788 removes `PORT_CORTEX=19996`.
- R788 keeps worker `--cortex-url` arguments explicit via `CORTEX_URL="${NOVAIC_CORTEX_URL:-http://127.0.0.1:19996}"`.
- R788 updates startup text to say Cortex is external/not started by the dev subset.
- R788 changes both service config copies to `services.cortex` at `19996`.
- Verification included `bash -n`, JSON parsing, config copy comparison, and targeted scans.

## Criteria Map

- Dev script no longer labels `19996` as Cortex unless it starts/expects Cortex there: satisfied; it now expects external Cortex URL instead of declaring a local port.
- Worker `--cortex-url` remains explicit: satisfied.
- Status/startup text accurately describes the local subset and external Cortex: satisfied.
- Targeted scans show no ambiguous `PORT_CORTEX`/`vmcontrol` startup graph naming: satisfied.
- `bash -n` passes: satisfied.

## Execution Map

- Patched one dev script and two config copies.
- Verified configs remain synchronized.

## Stress Test

- Checked app code for active `services.json`/`vmcontrol` config consumers before changing the config key; no active consumer requiring `services.vmcontrol` was found.

## Residual Risk

- Runtime source still has a VMControl command and Tauri still embeds VMControl, but neither creates the app config/startup ambiguity solved here.

## Result IDs

- R788
