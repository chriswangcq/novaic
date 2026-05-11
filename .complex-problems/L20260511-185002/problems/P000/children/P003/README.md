# Audit and fix agentctl and cortex CLI outputs

## Problem

`agentctl` and `cortex` are shell-exposed CLIs. They need to be checked for commands that return large payloads, file contents, binary data, or embedded blob contents through stdout instead of returning references or bounded text.

## Success Criteria

- `agentctl` command surface is inspected for blob-contract violations.
- `cortex` command surface is inspected for blob-contract violations.
- Any confirmed live violation is fixed or split into a follow-up if it is a distinct large repair.
- Text/payload-inspection commands remain bounded and explicit.
