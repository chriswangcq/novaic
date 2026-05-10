# Extract sandbox execution into an independent base service

## Problem

The user wants business-agnostic infrastructure capabilities to become independent servers, not only shared modules. The current shell execution still runs inside Cortex: Cortex materializes LogicalFS and directly executes commands through common sandbox primitives in-process.

We need to design and implement a real `sandboxd` service boundary without creating a fake half-migration. The service should own generic execution environment mechanics while Cortex keeps business semantics: Workspace, `/ro`/`/rw`, agent identity, shell capabilities, and Blob mapping.

## Success Criteria

- A service boundary is defined for generic sandbox execution with stable request/response contracts.
- The service does not know Cortex Workspace, Blob, agent, skill, or `/ro`/`/rw` semantics beyond caller-provided mount/env/cwd data.
- Cortex uses a client path to call the service rather than directly running subprocesses when configured.
- Tests cover the service contract, client, and Cortex integration path.
- Local direct runner remains only as an explicitly named test/dev adapter if needed, not as an ambiguous current production path.
- Residue scans make it clear which path is active.
