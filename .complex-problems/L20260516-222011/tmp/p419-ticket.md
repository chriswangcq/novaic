# Ticket: Clean Cortex API, CLI, and bridge surfaces

## Goal

Audit and clean Cortex API/CLI/bridge entry points so they use the intended explicit contracts and do not retain old compatibility paths that bypass ContextEvent, payload, or projection boundaries.

## Acceptance Criteria

- API, shell CLI capabilities, and runtime bridge clients are inventoried.
- Live compatibility/bypass paths are removed, routed, or split.
- Focused tests/guards cover the current entry points.
- No unclassified API/CLI/bridge residue remains.
