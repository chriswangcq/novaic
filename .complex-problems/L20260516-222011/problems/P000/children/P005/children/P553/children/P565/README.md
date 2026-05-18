# Sandbox Service SDK Compatibility Residue Inventory

## Problem

Search sandbox service, sandbox core, and sandbox SDK code for compatibility branches, direct host path exposure, mount bypasses, or legacy execution paths that could bypass the sandboxd boundary. This belongs under P553 because sandboxd should be the only process execution service while LogicalFS supplies the mounted file view.

## Success Criteria

- Records exact static scan commands and outputs.
- Classifies sandbox service/core/SDK compatibility and path-mount hits as intended, risky, removable, or follow-up.
- Confirms stdout/stderr base64 is only sandboxd wire encoding, not public LLM history.
- Captures any high-confidence risky residue for P554 remediation.
