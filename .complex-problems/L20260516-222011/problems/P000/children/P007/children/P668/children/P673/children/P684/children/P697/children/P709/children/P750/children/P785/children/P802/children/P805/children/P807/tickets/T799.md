# Clarify Dev Startup Cortex And VMControl URLs

## Problem Definition

The dev source startup script uses `PORT_CORTEX=19996`, but app service config reserves `19996` for VMControl. The same dev script passes `--cortex-url "$CORTEX_URL"` to runtime workers even though it explicitly does not start Cortex. This creates a misleading graph where one port is named as both Cortex and VMControl.

## Proposed Solution

Patch `novaic-app/scripts/start-backends.sh` so the worker Cortex URL is explicitly an external dependency with its own override/default, and reserve `19996` naming for VMControl only if needed. Update startup/status text to make the dev subset boundary clear.

## Acceptance Criteria

- No `PORT_CORTEX=19996` ambiguity remains in the dev startup script.
- Worker `--cortex-url` arguments still receive an explicit URL value.
- Startup text clearly says Cortex is external/not started by this script.
- Targeted scans for `PORT_CORTEX`, `CORTEX_URL`, `vmcontrol`, and `--cortex-url` are understandable.
- `bash -n novaic-app/scripts/start-backends.sh` passes.

## Verification Plan

- Inspect the dev script and runtime worker CLI requirements.
- Run `bash -n novaic-app/scripts/start-backends.sh`.
- Run targeted scans over the dev script and app config.

## Risks

- Runtime workers may require a Cortex URL even when Cortex is unavailable, so the fix must preserve explicit worker arguments.
- Choosing the wrong default Cortex port would encode another hidden assumption.

## Assumptions

- The dev script should not pretend to start Cortex.
- Environment override is acceptable for services that the script explicitly does not start.
