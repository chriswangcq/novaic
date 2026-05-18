# Classify LogicalFS Object Authority And Key Prefix Semantics

## Problem Definition

P572 must verify LogicalFS owns realtime `/ro` and `/rw` file semantics while object storage remains an implementation detail. Key-prefix mapping and authority APIs must not leak a blob-as-filesystem semantic boundary upward.

## Proposed Solution

Run targeted scans over `novaic-logicalfs` and Cortex authority tests for logical path normalization, key prefix mapping, object store contracts, snapshot/materialize/diff/writeback behavior, and authority tests. Record output, line slices, command manifest, and classification.

## Acceptance Criteria

- Exact scan commands and outputs are recorded.
- Relevant LogicalFS authority/key-prefix/materialize/diff slices have line references.
- Intended object-store-backed file authority is separated from risky blob-as-filesystem semantics.
- Any P554 remediation candidate is explicitly identified.

## Verification Plan

Inspect `logicalfs/authority.py`, `logicalfs/local.py`, `logicalfs/contracts.py`, relevant tests, and Cortex path adversarial tests. Confirm path normalization, owner prefixes, `/ro` `/rw` gates, and diff/writeback ownership.

## Risks

- Generic object-store language can sound like blob authority; classification must focus on who owns logical file semantics.

## Assumptions

- LogicalFS may use object stores internally, but external business code should interact with logical file semantics rather than raw object keys.
