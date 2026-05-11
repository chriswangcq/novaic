# Audit agentctl and cortex CLI output contracts

## Problem Definition

`agentctl` and `cortex` are also exposed through the shell capability layer. They need to be audited for Blob contract compliance so binary or large payload content is not emitted inline through shell stdout.

## Proposed Solution

Inspect generated `agentctl` and `cortex` command implementations, classify their outputs by modality, and fix any command that emits binary/blob-sized content inline. Verify that text-only commands are bounded and artifact-consuming commands require Blob URIs where appropriate.

## Acceptance Criteria

- `agentctl media audio-qa` consumes `blob://` inputs and does not print raw audio bytes.
- `agentctl im` commands do not emit binary attachment bytes inline.
- `cortex payload` commands remain bounded text inspection tools and do not dump unbounded payload content by default.
- Any discovered raw binary/base64 stdout path is fixed or recorded as a follow-up gap.
- Evidence is backed by code pointers and/or tests.

## Verification Plan

- Search generated shell capability code for base64/raw payload handling in `agentctl` and `cortex`.
- Inspect command implementations and output shaping.
- Run relevant existing tests for user content, payload client, tool schemas, and shell output contract.
- Add or adjust tests if a violation is found.

## Risks

- Some IM messages can contain user-provided text that looks like base64; the audit should distinguish arbitrary text from binary artifact contract violations.
- `cortex payload read` intentionally returns bounded text slices; it must not be incorrectly classified as an artifact path.

## Assumptions

- Artifact-producing CLI commands should return Blob manifests, but bounded text-inspection commands can continue returning text.
- Attachment transfer should happen through Blob URIs rather than inline bytes.
