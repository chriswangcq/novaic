# Config and deployment launch reference scan

## Problem

Find service launch references in configs, Docker/deploy files, process supervision metadata, app service manifests, and runtime worker configuration that may define actual backend topology.

## Success Criteria

- Candidate config/deploy launch references are scanned and saved with commands.
- Service/worker names from queue, saga, outbox, scheduler, health, Blob, LogicalFS, Sandbox, Cortex, Gateway, Business, and Device are searched with evidence.
- No production code is changed.
