# Audit agentctl shell CLI output contract

## Problem Definition

`agentctl` exposes IM, subagent, and media commands inside the shell sandbox. These commands need an explicit Blob-contract audit because they can reference attachments and media.

## Proposed Solution

Inspect generated `agentctl` code paths and relevant tests. Confirm artifact bytes are not emitted inline, media input is pulled from Blob by URI, and IM/subagent commands remain text or metadata oriented. Fix any violation found.

## Acceptance Criteria

- Media audio QA accepts only Blob URI input and does not print raw audio bytes.
- IM commands do not download or inline attachment bytes.
- Subagent spawn output is ordinary metadata and does not carry artifact payloads.
- The audit is backed by code pointers and a targeted test run.
- Violations are fixed or recorded as follow-up gaps.

## Verification Plan

- Inspect `shell_capabilities.py` `agentctl` code paths.
- Search tests and code for raw base64/binary output paths under `agentctl`.
- Run relevant `novaic-agent-runtime` user content and shell output contract tests.
- Run relevant `novaic-cortex` shell schema tests.

## Risks

- User messages can contain arbitrary text that resembles base64; that is not itself a Blob contract violation.
- Attachment metadata may include Blob URIs and filenames; that is allowed.

## Assumptions

- `agentctl` may print text summaries and JSON metadata.
- Raw artifact bytes must be transferred through Blob, not stdout.
