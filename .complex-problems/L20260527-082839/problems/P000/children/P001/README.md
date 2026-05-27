# Discover Release Controller deployment contract and current status

## Problem

Before deploying, the exact Release Controller API/config, branch policy, namespaces, health URLs, and current service status must be known so the release is triggered correctly and verified against the right endpoints.

## Success Criteria

- Identify the controller config file, HTTP endpoint/base URL, branch trigger policy, namespace target, and health/smoke URLs.
- Confirm the controller is reachable and report current status/runs.
- Confirm direct deploy scripts are controller internals rather than the deployment path.
- Produce exact commands/URLs to use for the release trigger.
