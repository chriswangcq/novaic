# Frontend runtime log and observability hooks audit

## Problem

The frontend (novaic-app) may contain observability hooks, log viewers, or diagnostic components that reference backend log/health APIs. Verify these components reference valid endpoints and don't expose raw payloads.

## Success Criteria

- Frontend observability/log-related hooks and components located.
- Backend endpoint references verified against actual routes.
- No raw payload exposure or stale API references in observability UI.
- Relevant tests/lints pass after any fixes.
