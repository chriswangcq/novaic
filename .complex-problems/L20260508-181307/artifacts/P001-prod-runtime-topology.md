# Production Runtime Topology Verification

## Problem

Verify that the just-deployed production backend is running the expected Queue Service and runtime worker topology, including the role-level worker roster and fresh logs.

## Success Criteria

- `./deploy status` or equivalent remote status confirms expected service and worker processes.
- Fresh-smoke evidence confirms logs are current after the deployment.
- The deployed runtime worker roster matches the code-defined roster.
- Any mismatch is recorded with concrete process/log evidence.
