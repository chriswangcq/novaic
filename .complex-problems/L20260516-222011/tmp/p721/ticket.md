# Device/devicectl surface discovery ticket

## Problem Definition

Device service and devicectl are hardware/capture/control surfaces. Before remediation, we need evidence for service entrypoints, CLI commands, launch paths, and where screenshot/control data crosses into shell/output/blob/display layers.

## Proposed Solution

Run read-only scans over `novaic-device`, `novaic-mcp-vmuse`, `scripts/start.sh`, `docs`, and runtime/tool contract files for device service, devicectl, HD screenshot, VM/mobile/host desktop, CloudBridge, and hardware command terms. Produce a boundary map and cleanup candidate list.

## Acceptance Criteria

- Device service launch/entrypoints are listed with evidence.
- devicectl command surfaces are listed with evidence, including screenshot/capture commands if present.
- Boundary conclusions separate hardware control from Blob/display/context projection.
- Cleanup candidates are listed for P723.

## Verification Plan

Use `rg`, `find`, `sed`, and `nl` read-only commands. Preserve scan output pointers in the result rather than dumping huge logs.

## Risks

- devicectl may live outside `novaic-device`; scan runtime/Cortex/MCP code too.
- Some docs may be historical; classify carefully.

## Assumptions

- No source changes should be made in this discovery ticket.
