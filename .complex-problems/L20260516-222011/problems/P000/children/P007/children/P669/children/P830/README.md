# Health endpoint inventory and contract verification

## Problem

Backend services expose health endpoints. Verify they exist, are consistent, and return meaningful diagnostics. Cross-check against any health check configuration in deploy scripts or systemd units.

## Success Criteria

- Health endpoints across all services are located and listed.
- Endpoint contracts (paths, response shapes) verified against code.
- Any stale or broken health paths identified.
