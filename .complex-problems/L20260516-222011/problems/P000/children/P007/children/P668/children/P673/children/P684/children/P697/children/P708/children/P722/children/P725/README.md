# Shell artifact manifest output contract discovery

## Problem

Discover the active shell/tool output contract for screenshot/artifact-producing CLI commands, especially `devicectl hd screenshot`, and verify whether shell stdout is constrained to terminal text plus artifact manifests instead of raw media bytes.

## Success Criteria

- Active shell output wrapping code for screenshot/artifact commands is identified with file pointers.
- Tests or docs proving raw media bytes/base64 are excluded from shell stdout are identified.
- Any active shell command path still printing raw screenshot/base64 bytes is listed as a remediation candidate.
- The result distinguishes current active shell behavior from historical archived outputs.
