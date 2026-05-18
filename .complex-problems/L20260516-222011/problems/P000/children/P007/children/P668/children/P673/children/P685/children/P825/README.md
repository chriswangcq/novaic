# Runbook topology alignment

## Problem

Operational runbooks (cloud-production.md, local-backends.md, local-dev.md) describe how to start/stop/monitor services. These must match the current 8-service topology and entrypoint paths.

## Success Criteria

- Each runbook's service references are compared against start.sh and service classification.
- Stale operational instructions are patched.
- No runbook references a service, port, or entrypoint that doesn't exist.
