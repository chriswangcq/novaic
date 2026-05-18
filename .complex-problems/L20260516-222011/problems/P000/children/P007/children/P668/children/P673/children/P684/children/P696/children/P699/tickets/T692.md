# Blob service boundary map implementation

## Problem Definition

P699 needs an evidence-backed Blob service boundary map. Blob should be classified as a cheap byte/object storage service, not the realtime RO/RW workspace authority and not Cortex semantic state.

## Proposed Solution

Inspect Blob service entrypoints, start scripts, docs, and known consumers from P695 evidence. Produce a boundary map artifact that records entrypoint, launch evidence, role, dependencies, consumers, and any misleading boundary claims. Patch only safe documentation or guard residue if clearly wrong.

## Acceptance Criteria

- Blob service entrypoint and launch evidence are listed with stable paths.
- Blob role is explicitly differentiated from LogicalFS realtime file authority and Cortex semantic state.
- Consumers are identified as consumers/facades, not owners.
- Any safe misleading claims are patched or explicitly recorded as residual risk.
- Focused checks are run if files change.

## Verification Plan

- Inspect `novaic-blob-service`, `scripts/start.sh`, relevant docs, and P695 artifacts.
- Run targeted scans for Blob/LogicalFS/Cortex boundary language.
- Save boundary map and verification artifacts under ledger tmp.
- Run docs/CI guard if a patch is made.

## Risks

- Blob docs may discuss Cortex integration; that is not automatically a boundary violation.
- Some historical roadmap tickets may contain old terms and should not be over-cleaned unless active docs/scripts are misleading.

## Assumptions

- This ticket may be one-go if inspection shows only classification or small docs cleanup is needed.
