# Probe live Release Controller status and runs

## Problem

Local config is not enough; the controller must be reachable and its current status/runs must be known before triggering a deployment.

## Success Criteria

- Discover a reachable controller base URL from local config, process list, compose, nginx, or docs.
- Call status/runs/read endpoints successfully or record the exact blocker.
- Capture current latest run/pointers before triggering new release.
