# Enforce sandboxd as process-only execution boundary

## Problem

Sandboxd should execute processes over a filesystem view. It must not own Cortex
workspace semantics, subagent layout semantics, Blob persistence semantics, or
display/download semantics.

## Success Criteria

- Sandbox service and SDK contracts are process/view oriented and do not expose
  Cortex Workspace or Blob persistence decisions.
- Deployment/start scripts run the sandbox service and do not reference removed
  sandbox-core packages or old local fallback execution.
- Tests prove sandboxd can execute commands through the intended contract.
- Residue scans show no sandbox-local ownership of `/ro` / `/rw` semantics.
