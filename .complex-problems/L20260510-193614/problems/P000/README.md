# Cortex State Authority Remediation Implementation

## Problem

Implement the remediation plan from `L20260510-192637` in phases rather than leaving it as architecture prose. The implementation should move Cortex control state toward a clean model:

- SQLite for durable operational state and projections.
- LogicalFS/Workspace for file/document authority and trace projection.
- Redis for coordination only.
- Blob for raw bytes with semantic manifests.
- Process memory for cache/config/client wiring only.

Do not attempt a huge one-go rewrite. Design construction first, then implement phase by phase with tests and cleanup.

## Success Criteria

- Create a phased implementation ledger and construction plan.
- Implement at least the first safe phase with tests.
- Each phase must have explicit authority boundary, migration/cleanup, and verification.
- Do not silently keep old runtime paths as active authority after a cutover phase.
- Use strict success checks; if a phase reveals unexpected complexity, split follow-up tickets.
