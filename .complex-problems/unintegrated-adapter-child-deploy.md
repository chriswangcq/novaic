# Audit deployment process and compatibility residue

## Problem

Find any deployment/startup/process wiring that can still run old services, old workers, fallback packages, or stale branch implementations despite the new architecture being present.

## Success Criteria

- Inspect deploy script, start script, package sync/exclude rules, service startup commands, worker process modes, and retired package cleanup.
- Compare with current service status where useful.
- Identify stale or ambiguous compatibility residue that could make production run old logic.
