# Register and deploy sandboxd as a first-class backend service

## Problem Definition

The new sandboxd service must be part of service configuration, startup, stop, status, logs, requirements install, and deploy sync. Otherwise the production Cortex server cannot satisfy its new required `--sandboxd-url`.

## Proposed Solution

Add sandboxd to `services.json`, `scripts/start.sh`, deployment sync/install/log/status/help commands, and build/service lists where relevant. Start sandboxd before Cortex and pass `--sandboxd-url` into Cortex.

## Acceptance Criteria

- Sandboxd has a stable service URL/port in configuration.
- `start.sh` starts, stops, waits for, and logs sandboxd.
- Cortex startup receives `--sandboxd-url`.
- `deploy services`, `deploy sandboxd`, fresh log smoke, status, and logs include sandboxd.
- No hidden fallback is introduced.

## Verification Plan

- Run syntax checks for changed shell scripts.
- Run source scans for sandboxd URL wiring and Cortex command arg.

## Risks

- Remote deployment has not happened until explicitly run; this ticket prepares the deployment path.

## Assumptions

- Sandboxd should run on localhost port `19994`, between blob `19995` and device `19993`.
