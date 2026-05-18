# Local dev backend launcher remediation

## Problem

`novaic-app/scripts/start-backends.sh` is an active dev launcher but appears to start only a subset of current backend services while claiming to start all Python backends. Inspect and fix stale or misleading local dev launcher behavior/wording without live deployment.

## Success Criteria

- The script is inspected against current service topology evidence.
- Misleading comments/status output or stale worker/process assumptions are fixed.
- Shell syntax and relevant guard checks pass.
- Any intentional local-dev subset behavior is documented in the script or result.
