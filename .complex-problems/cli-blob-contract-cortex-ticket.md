# Audit cortex payload CLI output contract

## Problem Definition

`cortex payload` commands read and interpret Cortex payload references. They must remain bounded text-inspection tools and avoid unbounded payload stdout or binary artifact transport.

## Proposed Solution

Inspect generated `cortex payload` code paths for read/search/summarize/qa. Verify explicit limits, bounded defaults, and absence of artifact-byte emission. Fix any unbounded or artifact-like stdout behavior discovered.

## Acceptance Criteria

- `payload read` enforces maximum bounded output.
- `payload search` enforces bounded match count and context size.
- `payload summarize` and `payload qa` use bounded model input/output limits.
- No `cortex` CLI path emits raw binary/base64 artifacts inline.
- Evidence is backed by code pointers and tests.

## Verification Plan

- Inspect `shell_capabilities.py` cortex payload command handling.
- Search for raw base64/binary output paths in cortex command implementation.
- Run relevant payload client, tool schema, and projection tests.
- Add or adjust tests if a violation is discovered.

## Risks

- Payload read intentionally returns text slices; the audit must separate bounded text inspection from artifact output.
- Very large textual payloads are still possible if limits drift; tests or code inspection must confirm enforced caps.

## Assumptions

- Bounded text output is allowed for inspection commands.
- Binary artifact transport should use Blob manifests, not `cortex payload` stdout.
