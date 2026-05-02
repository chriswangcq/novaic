# PR-180 — Business device proxy route boundary review

Status: `[pending]`

## Goal

Review and clean Business device/VM proxy routes so Business only keeps product-value routes with real callers. Device execution should remain behind the owning Runtime/Business tool path, not as ambiguous historical proxy endpoints.

## Required Process

1. Analyze current callers for QEMU/VM/Mobile/HD proxy endpoints.
2. Create small implementation tickets from the findings.
3. Delete or tighten routes that have no current product owner.
4. Confirm closure with tests, smoke, deploy, and git commit.

## Tests

- Route-level unit tests for kept or removed endpoints.
- Runtime tool smoke for any kept device tool path.
- Static scan proving no deleted route caller remains.

## Deployment / Git

- Deploy affected Business/Runtime services.
- Commit/push each independently mergeable change.
