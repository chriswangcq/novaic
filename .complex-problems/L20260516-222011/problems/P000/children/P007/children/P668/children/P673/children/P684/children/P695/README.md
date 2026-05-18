# Extracted service entrypoint and launch evidence discovery

## Problem

Discover concrete entrypoint files, launch commands, package scripts, generated app resources, deployment configs, and service wrappers for Blob, LogicalFS, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, and related wrappers. The output must be evidence artifacts, not interpretation-only prose.

## Success Criteria

- Candidate service entrypoint files are listed with stable paths.
- Launch commands/configs/package scripts/generated resources are captured with stable evidence.
- Each target service has either at least one candidate evidence pointer or a recorded absence.
- Scan commands and raw summaries are saved under ledger tmp artifacts for later classification.
