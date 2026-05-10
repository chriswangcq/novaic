# Deployment and service registry include sandboxd

## Problem

The new independent server must be first-class infrastructure in local/deploy scripts and service registry; otherwise the code can exist but production still runs the old path.

## Success Criteria

- `services.json` declares sandboxd on a stable port.
- Local startup starts/stops sandboxd and passes its URL into Cortex.
- Deployment rsync/install/start/status/log verification includes `novaic-sandbox-service`.
- No deployment script keeps a hidden fallback to in-process sandbox execution.
