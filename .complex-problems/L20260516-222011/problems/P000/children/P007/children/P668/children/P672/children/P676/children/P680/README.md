# Packaged backend launcher remediation

## Problem

`novaic-app/src-tauri/resources/backends/start-backends.sh` and its generated apple copy appear to use an old packaged topology (`AGENT_RUNTIME_PORT=19991`, only Blob/Gateway/Agent Runtime). Determine whether this is still active, then remove/update/guard the stale packaged launcher path without editing generated output blindly.

## Success Criteria

- Source resource and generated packaged launcher copies are inspected.
- If stale and unused, they are removed or guarded against active use; if active, source is updated and generated copy handled consistently.
- No generated-only fix is left without source truth.
- Relevant resource hygiene/static tests or shell syntax checks pass.
