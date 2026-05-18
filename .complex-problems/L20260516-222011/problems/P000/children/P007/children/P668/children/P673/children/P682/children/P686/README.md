# Script and package entrypoint scan

## Problem

Find shell scripts, npm/package scripts, Tauri resources, and repository scripts that start, stop, deploy, supervise, smoke-test, or health-check backend services/workers.

## Success Criteria

- Candidate shell/package/app-resource entrypoint paths are scanned and saved with commands.
- Known launcher surfaces such as local `start-backends.sh`, packaged backend resource launchers, and deployment/start scripts appear or their absence is explained.
- No production code is changed.
