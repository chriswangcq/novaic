# Migrate CI/CD docs and clean stale branches

## Problem

The repository and local git workspace should reflect the controller as the primary long-term CI/CD path, with GitHub Actions demoted to optional verification/fallback. Stale local branches should be cleaned without losing current work.

## Success Criteria

- Deployment/runbook docs explain release-controller as the primary path.
- GitHub Actions docs are updated as secondary or optional.
- Local stale branches are reviewed and safe stale branches are deleted.
- Current dirty work and active branch are preserved.
- Final git branch/status summary is recorded.
