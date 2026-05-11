# Audit and fix agentctl CLI Blob contract

## Problem

`agentctl` shell capability commands must not emit raw binary artifact content inline. This child problem audits IM, subagent, and media commands, and fixes any output path that violates the Blob contract.

## Success Criteria

- `agentctl media audio-qa` requires `blob://` input and does not print raw audio bytes.
- `agentctl im` command output is text/metadata only and does not inline attachment bytes.
- `agentctl subagent spawn` output is ordinary text/metadata only.
- Any violation discovered in active code is fixed and verified.
- Evidence references concrete code paths and test results.
