# Cortex Materialization And Local Fallback Residue Inventory

## Problem

Search Cortex code for stale direct materialization APIs, local shell execution fallbacks, temporary sandbox path leakage, old `/tmp/novaic-cortex-sandbox-*` assumptions, and compatibility paths that could bypass the intended `Workspace -> MountNamespaceLogicalFS -> sandboxd` boundary. This belongs under P553 because Cortex is the semantic owner of RO/RW and any fallback here can undermine the whole layering model.

## Success Criteria

- Records exact static scan commands and outputs.
- Classifies Cortex hits as intended, risky, removable, or follow-up.
- Specifically classifies `Workspace.materialize()` and any shell/local execution fallback terms.
- Captures any high-confidence risky residue for P554 remediation.
