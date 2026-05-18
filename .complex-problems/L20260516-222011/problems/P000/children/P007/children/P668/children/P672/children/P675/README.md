# Deployment script discovery and classification

## Problem

Find repository scripts/configs related to deployment, startup, supervision, smoke, and health checks. Classify high-signal candidates as active, test-only, generated, or historical so later remediation does not edit the wrong surface.

## Success Criteria

- Reproducible search artifacts list candidate script/config files.
- High-signal active scripts are identified with evidence pointers.
- Historical/test-only/generated candidates are explicitly separated.
- No code changes are made except writing ledger evidence artifacts.
