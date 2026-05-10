# Audit Cortex state authority boundaries

## Problem Definition

The user wants to know whether Cortex already matches the desired architecture: Cortex as a state semantics service, with authoritative durable state in Workspace/LogicalFS, and Cortex process memory only used for caches/adapters. The audit must identify real imperfections instead of giving a broad yes.

## Proposed Solution

Perform a bounded source audit of Cortex state-bearing code paths:

- Workspace/LogicalFS file authority and registry wiring.
- Context event store/read model/projection.
- Scope lifecycle, steps, summaries, payloads, and `/ro`/`/rw` files.
- Process memory caches in registry, locks, hook/log paths, and capability/materialized shell views.
- Any persistent state outside Workspace/LogicalFS, including Blob payload storage and scope transition logs.

## Acceptance Criteria

- Produce a state-category table with authority and restart behavior.
- Identify which state is authoritative vs cache vs observability.
- Identify gaps where process state or external state could still affect correctness.
- Cite concrete files/lines or command evidence.

## Verification Plan

- Use `rg`, `sed`, and source inspection over `novaic-cortex/novaic_cortex`.
- Search for file writes, append operations, global caches, registry maps, locks, log paths, and event store usage.
- Run no mutation other than ledger files.

## Risks

- Some authoritative behavior may be in adjacent services such as Blob Service or LogicalFS, so this audit should classify those boundaries rather than re-audit every external service.
- The answer could overstate “stateless” if lock/cache behavior is ignored.

## Assumptions

- Current branch contains the deployed Cortex event-source cutover.
- The question is architectural/audit oriented; no code changes are requested in this turn.
