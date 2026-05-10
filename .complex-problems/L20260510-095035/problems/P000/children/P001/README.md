# Active Shell Path And Host Capability Audit

## Problem

Before editing, map the current active Cortex shell path, hidden temp-projection dependencies, and local host filesystem capabilities. The implementation must not be based on wishful assumptions about `/cortex`, FUSE, or mount namespace support.

## Success Criteria

- Identify the current entry points and active functions for shell execution.
- Identify all old temp-projection and command-string gating logic to delete or move.
- Identify local host support for true `/cortex` mount semantics.
- Record the exact implementation constraints that child tickets must obey.
