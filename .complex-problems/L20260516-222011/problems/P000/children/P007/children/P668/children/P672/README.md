# Deployment and start script topology inventory

## Problem

Inventory repository scripts and configs that start, deploy, supervise, or smoke backend services. Determine which scripts are active, which are guard/test-only, and whether any active script uses stale process names or unclear worker roles.

## Success Criteria

- Start/deploy/supervision/smoke script files are located and inspected with evidence.
- Active scripts are distinguished from historical/test-only scripts.
- Stale process names or unclear role labels in active scripts are patched when low-risk.
- Script syntax or relevant static checks are run for any changed script.
