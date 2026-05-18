# Dev Startup Cortex And VMControl URL Contract Result

## Summary

Removed the ambiguous app-local `19996` naming. The dev startup script now treats Cortex as an explicit external URL (`NOVAIC_CORTEX_URL` override, defaulting to `http://127.0.0.1:19996`) instead of declaring `PORT_CORTEX`. App service config now names port `19996` as `cortex`, matching the backend architecture and the worker `--cortex-url` contract.

## Done

- Updated `novaic-app/scripts/start-backends.sh`:
  - removed `PORT_CORTEX=19996`
  - added startup text for external Cortex URL
  - derives worker `CORTEX_URL` from `NOVAIC_CORTEX_URL` with explicit default
- Updated app service config copies:
  - `novaic-app/src-tauri/resources/config/services.json`
  - `novaic-app/src-tauri/gen/apple/assets/config/services.json`
  - replaced `services.vmcontrol` with `services.cortex` for port `19996`

## Verification

- `bash -n novaic-app/scripts/start-backends.sh`
- `python -m json.tool` for both service config copies.
- `cmp -s` confirmed resource and generated service config copies are identical.
- Targeted scan for `PORT_CORTEX`, `CORTEX_URL`, `NOVAIC_CORTEX_URL`, `vmcontrol`, `cortex`, `--cortex-url`, and `19996` shows:
  - no `PORT_CORTEX`
  - worker `--cortex-url` remains explicit
  - app configs now expose `cortex:19996`
  - no `vmcontrol` entry remains in the app startup/config graph

## Known Gaps

- The broader runtime still has VMControl concepts and code, but that is unrelated to the app startup graph: Tauri embeds VMControl and the dev script does not start it.

## Artifacts

- Modified dev startup script and both app service config copies.
