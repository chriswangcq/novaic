# Classify Cortex BlobObjectStore Adapter Boundary

## Problem Definition

P571 must determine whether Cortex `BlobObjectStore` and registry/store adapter usage are intended below-LogicalFS object storage or risky direct blob workspace authority.

## Proposed Solution

Run targeted scans over Cortex and LogicalFS for `BlobObjectStore`, `ObjectStore`, `object adapter`, registry/store usage, and direct blob object calls. Record scan outputs, line-numbered slices, a command manifest, and a classification.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- Relevant code slices have line references.
- `BlobObjectStore` and related registry/store hits are classified.
- Any P554 remediation candidate is explicitly identified.

## Verification Plan

Read scan outputs and code slices. Confirm whether object storage is hidden below Workspace/LogicalFS authority or bypasses it.

## Risks

- Blob terms may include payload/artifact references unrelated to file authority; classify by layer role.

## Assumptions

- Object storage below LogicalFS can be intended if LogicalFS remains the realtime filesystem authority.
