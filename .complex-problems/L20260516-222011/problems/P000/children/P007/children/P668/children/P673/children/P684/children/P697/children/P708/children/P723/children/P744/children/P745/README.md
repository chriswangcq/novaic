# Analyze Device screenshot route usage and ownership

## Summary

Find all in-repo references, tests, mounts, and likely external compatibility signals for `/api/vmcontrol/vms/{vm_id}/screenshot`.

## Problem

The route returns inline MCP image content, but changing/removing it safely requires knowing whether any app/runtime/device clients still call it.

## Success Criteria

- Route implementation and mount are identified.
- In-repo callers are identified or proven absent.
- Tests covering the route are identified.
- A concrete disposition recommendation is produced: remove, mark legacy/debug-only, or convert.
