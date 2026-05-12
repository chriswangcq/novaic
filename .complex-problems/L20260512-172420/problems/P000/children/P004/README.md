# Commit Deploy And Smoke Verify

## Problem

After implementation and tests, commit the contract changes and deploy them to the production server. Verify deployed services are healthy and the new behavior is smoke-tested enough to catch the previous base64-as-text failure mode.

## Success Criteria

- Git diff is reviewed and committed.
- Deployment completes successfully.
- Service health/status checks pass after deployment.
- A smoke or contract verification confirms the new display path no longer sends raw base64 as tool text.
