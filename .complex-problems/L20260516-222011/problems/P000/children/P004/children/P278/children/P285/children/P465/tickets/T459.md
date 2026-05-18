# Session legacy residue inventory ticket

## Problem Definition

P465 needs a broad, read-only inventory of session legacy residue before any cleanup decisions. The target is queue/session code and nearby tests where stale compatibility branches, old active-session concepts, direct side-effect bypasses, or retired observed-wake terms may still exist.

## Proposed Solution

Run explicit `rg` guard groups over `novaic-agent-runtime/queue_service`, `novaic-agent-runtime/task_queue`, and `novaic-agent-runtime/tests`. Save raw outputs under `.complex-problems/L20260516-222011/tmp/p465/`, then inspect representative hits and produce a concise residue classification: safe retained infrastructure, test-only historical fixtures, and any actionable production cleanup candidates. This ticket is inventory only and will not edit source.

## Acceptance Criteria

- Guard artifacts are saved under `.complex-problems/L20260516-222011/tmp/p465/`.
- The inventory covers legacy/compat/fallback terms, old active-session terms, session side-effect names, and matching test residue.
- The result names any actionable production residue or explicitly states that no source changes are made in this child.
- Any discovered cleanup need is routed to downstream ledger work instead of being fixed inside this inventory ticket.

## Verification Plan

Review the saved guard output and representative source slices for false positives. Confirm no tracked source file changed while executing this inventory. Record the artifact paths and hit classification in the ticket result.

## Risks

- Keyword-based guards can produce false positives from documentation, tests, or intentionally named compatibility fixtures.
- Keyword-based guards can miss a legacy path if it uses new names but old behavior.

## Assumptions

- This child problem is allowed to be one-go because it is read-only, bounded, and has strict artifact evidence.
- Actual remediation belongs in sibling or follow-up problems after classification.
