# Ticket: Semantic/app/device service boundary classification

## Problem Definition
Classify Cortex, Gateway, Business, Device, and related wrappers as semantic/app/device-facing services. Verify their concrete entrypoints, launch surfaces, and dependency boundaries relative to Queue/Runtime and the foundational Blob/LogicalFS/Sandbox services.

## Scope
- Cortex: semantic state/context service; must not be treated as the long-term owner of file/sandbox infrastructure.
- Gateway: app/API-facing edge service; distinguish routing/HTTP boundary from runtime/queue workers.
- Business: product/business subscriber/service layer; distinguish business computation from queue/session/FSM ownership.
- Device/devicectl: device-facing service/CLI surfaces; distinguish host device capture/control from display/blob/context projection.
- Wrappers/scripts: launch wrappers and app resource scripts that start or package these services.

## Required Evidence
- Entrypoint files and launch commands for each service category.
- Dependency imports/usages showing what each service consumes and what it owns.
- Any docs or scripts that claim ownership/role boundaries.
- Classification of active vs stale or generated-only references.

## Success Criteria
- Cortex, Gateway, Business, Device, and wrappers each have role, entrypoint, and dependency-boundary evidence.
- Cortex is specifically checked as semantic state/context service, not a long-term owner of file/sandbox infrastructure.
- Gateway/Business/Device launch and wrapper roles are separated from Queue/Runtime worker roles.
- Stale or misleading claims found during classification are either patched if safe or recorded as residual follow-up.

## Constraints
Do not collapse this into a single vague architecture summary. If discovery shows multiple risky service groups or cleanup candidates, split into child problems rather than one-going the whole track.
