# Child Problem: media CLI emits manifests, not bytes

## Problem

Screenshot and media CLI commands must return concise terminal text plus blob/artifact manifests. Active CLI paths must not print raw base64, data URLs, or large binary JSON fields to stdout where they enter shell observations and Cortex step text.

## Success Criteria

- `devicectl` screenshot/media paths emit `tool-output.v1`-style manifests or equivalent blob/artifact pointers.
- No active screenshot/media CLI stdout path contains raw `screenshot` base64 payloads, `data:image/*;base64`, or unbounded media bytes.
- Focused CLI tests or scans prove the stdout contract.
