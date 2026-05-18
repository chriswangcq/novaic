# Semantic, app, and device service boundary classification

## Problem

Classify Cortex, Gateway, Business, Device, and related wrappers as semantic/app/device-facing services. Verify their entrypoints, launch surfaces, and dependency boundaries relative to Queue/Runtime and the foundational Blob/LogicalFS/Sandbox services.

## Success Criteria

- Cortex, Gateway, Business, Device, and wrappers each have role, entrypoint, and dependency-boundary evidence.
- Cortex is checked specifically as a semantic state/context service, not a long-term owner of file/sandbox infrastructure.
- Gateway/Business/Device launch and wrapper roles are separated from queue/runtime worker roles.
- Any stale or misleading claims found during classification are patched or recorded.
