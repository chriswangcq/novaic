# Extracted service entrypoint classification and boundary audit

## Problem Definition

The repository has several independently deployed or extracted service concepts: Blob, LogicalFS, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, plus wrappers and generated launch assets. P684 needs a concrete, evidence-backed classification of each service's entrypoint, launch path, role, and dependency boundary. The audit must verify that foundational file/sandbox services are exposed as separate services rather than hidden Cortex internals, and must identify stale, duplicate, or misleading entrypoints that either need cleanup or explicit recording.

## Proposed Solution

Build a classification ledger for extracted service entrypoints in small subproblems:

1. Discover and classify concrete service entrypoints and launch references for Blob, LogicalFS, Sandbox/Sandboxd, Cortex, Gateway, Business, Device, and wrappers.
2. For each service, map current role, dependency boundary, and whether it is a foundational service, semantic service, app/gateway service, or device bridge.
3. Compare current implementation against the intended architecture: Blob as cheap file store, LogicalFS as realtime RO/RW file view service, Sandbox/Sandboxd as execution boundary, Cortex as semantic state/context service using file/logical stores rather than owning them.
4. Scan for stale or duplicate service entrypoints and misleading docs/scripts. Patch only when the removal or wording change is safe; otherwise record the residue with a follow-up.
5. Run focused syntax/import/static tests only for files changed, plus targeted grep/guard checks for stale topology claims.

## Acceptance Criteria

- Every target service has a recorded entrypoint and launch/config evidence, or an explicit explanation that no active entrypoint exists.
- Every target service has a concise role and dependency-boundary classification.
- Cortex ownership is checked specifically: foundational Blob/LogicalFS/Sandbox responsibilities must not be misrepresented as Cortex internals.
- Stale or duplicate service entrypoints are either safely cleaned up or documented as residual risk with evidence.
- If code/docs/scripts are changed, relevant syntax/static tests and targeted residue scans pass.
- Results cite stable artifact files under the ledger tmp tree, not broad memory claims.

## Verification Plan

- Use `rg`, `find`, package scripts, deployment configs, service configs, and Python entrypoint idiom scans to identify launch surfaces.
- Create per-service classification artifacts for entrypoint, launch command/config, role, and boundary.
- Run targeted stale-claim scans for phrases that collapse service boundaries, especially Cortex owning Blob/LogicalFS/Sandbox responsibilities.
- Run `bash -n`, Python import/syntax checks, and existing CI guard scripts only for touched surfaces.
- Record a parent result that aggregates child evidence and a strict success check that rejects missing service evidence.

## Risks

- Generated packaged assets can duplicate active launch scripts; changing only one copy can leave stale runtime behavior.
- Some service names appear in tests/docs/compat layers, so naive grep cleanup could delete intentional guard coverage.
- Service boundaries may be aspirational in design docs but not fully reflected in launch topology; this must be reported honestly rather than papered over.

## Assumptions

- No backwards compatibility is required for stale launch paths unless active deployment evidence proves they are still used.
- It is acceptable to create follow-up subproblems when classification exposes cleanup that is too large or risky for one ticket.
- Foundational service boundary clarity is more important than minimizing one-time audit effort.
