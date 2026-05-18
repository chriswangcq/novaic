# Enumerate and classify active projection branches

## Problem Definition

The active projection code still has branches for shell output, display perception, MCP content, data URLs, artifacts, and unknown dictionaries. We need to distinguish intentional contract handling from stale compatibility residue.

## Proposed Solution

Search active projection/runtime/factory paths for projection branch markers, inspect the relevant line ranges, and classify each branch with file/line evidence. If a stale or ambiguous branch is found, either remove it if clearly safe in this ticket or record a follow-up.

## Acceptance Criteria

- Active branch sites are enumerated with file/line evidence.
- Each branch is classified as intentional or follow-up-worthy.
- Search covers Cortex projection, runtime task-queue multimodal projection, and factory provider/log projection surfaces.
- No unclassified branch remains.

## Verification Plan

Run targeted `rg` searches for `_mcp_content`, `display_perception`, `tool-output.v1`, `image_url`, `inlineData`, `artifact`, `unknown`, `projection`, and relevant helper names. Inspect line-numbered source slices and record classifications.

## Risks

- A defensive branch can look like legacy residue; deletion should require proof that no current contract depends on it.
- Search output may include tests; test-only branches should be classified separately from production branches.

## Assumptions

- Branches covered by focused passing tests and tied to documented current contracts are intentional.
