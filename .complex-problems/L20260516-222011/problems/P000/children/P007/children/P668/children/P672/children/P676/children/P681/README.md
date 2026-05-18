# Deployment script guard verification and patch

## Problem

Verify that deployment-related guard scripts protect the active launcher contracts discovered by P678/P676, including cloud `deploy`/`scripts/start.sh` and local/package launchers where relevant. Patch guard coverage gaps if low-risk.

## Success Criteria

- Current deployment guard scripts are inspected against remediation findings.
- Guard scripts cover the corrected active launcher contracts or explicitly document why a surface is out of scope.
- Low-risk guard gaps are patched.
- Guard scripts are executed locally and pass.
