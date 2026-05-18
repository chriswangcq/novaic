# Launch scripts cross-verification against service topology

## Problem

Three launch scripts (start.sh, start-backends.sh, launch_split_only.sh) must match current service topology. After auditing individual service entrypoints, verify these scripts reference correct ports, correct service names, and no stale services.

## Success Criteria

- Each launch script's service list is mapped against the actual service topology.
- Stale port/service references are identified and fixed.
- Scripts launch only services that exist with correct entrypoints.
