# Architecture guard inventory

## Problem

Inventory existing CI/static guard scripts and module-level guard tests that protect old path removal, shell/display/tool-output contracts, lifecycle/session behavior, Blob/LogicalFS boundaries, generated artifacts, and deployment/runtime entrypoints.

## Success Criteria

- Lists relevant guard scripts/tests and the contract each protects.
- Identifies guard surfaces that are intentionally test-only versus CI script enforced.
- Saves inventory evidence in the ledger tmp directory.
