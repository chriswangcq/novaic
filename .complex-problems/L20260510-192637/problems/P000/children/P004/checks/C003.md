# Blob Payload Contract Check

## Summary

success

## Evidence

- Result distinguishes raw bytes from semantic manifests and lifecycle.

## Criteria Map

- Blob raw byte authority -> defined.
- Semantic metadata location -> SQLite/Workspace manifest.
- Missing/corrupt handling -> structured errors and hash checks.
- Retention -> manifest-driven sweeper.

## Execution Map

- T004 -> R003 produced the Blob payload contract plan.

## Stress Test

- Failure mode: Blob object exists without manifest. Treat as orphan raw bytes; not semantic state.
- Failure mode: manifest exists but blob missing. Runtime returns structured missing payload and can trigger repair/expiry.

## Residual Risk

- Needs implementation to prevent current direct `blob_ref` usage from bypassing manifest.

## Result IDs

- R003

## Blocking Gaps

- none
