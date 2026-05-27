# Verify published server health and close deployment evidence

## Problem

A controller success is not enough without confirming the server endpoints are live after deployment. The deployment needs a final health/smoke pass and a concise evidence package.

## Success Criteria

- API/backend server health or smoke endpoints pass for the deployed namespace.
- Registry/service state is consistent enough to prove server-side services came up.
- Final evidence includes commit SHAs, controller run ID, namespace, health URLs, and residual risks.
- Ledger validates/renders complete after closure.
