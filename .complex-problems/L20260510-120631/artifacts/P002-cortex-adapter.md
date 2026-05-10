# Migrate Cortex to explicit LogicalFS snapshot and patch adapter

## Problem

Cortex should own workspace state but should not own filesystem materialization/diff implementation. It must export a snapshot and apply a returned patch through explicit adapter code.

## Success Criteria

- Cortex has a thin adapter that converts Workspace `/ro` and `/rw` data to LogicalFS snapshot DTOs.
- Cortex passes explicit env overlays, token, API URL, and RW layout values into LogicalFS instead of LogicalFS generating agent semantics.
- Cortex applies `WorkspacePatch` returned by LogicalFS.
- Old materialization/diff helpers are removed from Cortex or delegated to `novaic-logicalfs`.
- Cortex imports `logicalfs`, `sandbox_sdk`, and no `sandbox_core`.
