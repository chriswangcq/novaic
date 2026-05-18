# Queue/runtime stale entrypoint residue scan

## Problem

Search queue-service and agent-runtime source, scripts, docs, and tests for stale/duplicate entrypoint names, retired worker labels, legacy runtime assumptions, or misleading process role descriptions. Produce evidence before editing anything.

## Success Criteria

- Targeted stale/residue scans are saved with commands and counts.
- Findings are classified as safe-to-edit, intentionally retained test/docs guard, or risky/uncertain.
- No production code is changed in this scan child.
