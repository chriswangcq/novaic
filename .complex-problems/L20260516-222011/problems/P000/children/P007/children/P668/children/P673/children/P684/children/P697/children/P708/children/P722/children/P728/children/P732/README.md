# Active non-test media-byte surface classification

## Problem

Classify non-test production code paths that emit or transform base64/image media content across Runtime, Cortex, Device, and standalone MCP/plugin packages.

## Success Criteria

- Non-test base64/image emission paths are listed with file pointers.
- Each path is classified as active shell/runtime, display-current-round, standalone MCP/plugin, internal auth/encoding, or remediation candidate.
- Any active violation of the shell/history contract is listed for remediation.
