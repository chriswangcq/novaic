# Complex Problem Ledger

Ledger: L20260511-152523
Schema: v6
Root: P000 - Agent loop stalls after one round
Status: done
Updated: 2026-05-11T08:13:36+00:00

## Problem Tree
- [done] P000: Agent loop stalls after one round
  - [done] P001: Live production stall diagnosis
  - [done] P002: Code repair for identified stall cause
    - [done] P004: Shell capability Cortex internal auth repair
    - [done] P005: Tool result step_ref projection repair
    - [done] P006: Wake finalize compensation context repair
  - [done] P003: Deploy and verify stall repair
    - [done] P007: Deploy repaired backend code
    - [done] P008: Verify live agent loop recovery

## Active

## Blocked

## Done
- [x] P000: Agent loop stalls after one round
- [x] P001: Live production stall diagnosis
- [x] P002: Code repair for identified stall cause
- [x] P003: Deploy and verify stall repair
- [x] P004: Shell capability Cortex internal auth repair
- [x] P005: Tool result step_ref projection repair
- [x] P006: Wake finalize compensation context repair
- [x] P007: Deploy repaired backend code
- [x] P008: Verify live agent loop recovery

## Tickets
- [done] T000: Diagnose and repair deployed agent loop stall -> P000 (split)
- [done] T001: Inspect live queue/runtime stall evidence -> P001 (one_go)
- [done] T002: Repair chained agent-loop stall defects -> P002 (split)
- [done] T003: Pass Cortex internal key to shell capabilities -> P004 (one_go)
- [done] T004: Project top-level step_ref for tool results -> P005 (one_go)
- [done] T005: Preserve wake finalize compensation context -> P006 (one_go)
- [done] T006: Deploy and verify repaired agent loop -> P003 (split)
- [done] T007: Deploy repaired backend services -> P007 (one_go)
- [done] T008: Verify live repaired agent loop path -> P008 (one_go)

## Latest Checks
- [success] C000: P001 The diagnosis ticket successfully identified a concrete, code-backed failure chain for the production stall. It does not claim the system is fixed; it proves why the current agent loop got stuck and defines the repair targets for subsequent tickets.
- [success] C001: P004 The shell internal-auth repair satisfies P004: runtime now passes an explicit Cortex internal key to the capability env, and the generated capability script uses it only for Cortex internal POSTs.
- [success] C002: P005 The step-ref projection repair satisfies P005: projected tool-result messages now expose the durable tool-step join key exactly where runtime expects it.
- [success] C003: P006 The compensation-context repair satisfies P006: failure compensation now keeps the explicit data needed for Cortex archive and session finalization instead of narrowing the context to scope/user ids.
- [success] C004: P002 The code repair problem is solved at the implementation level: all three diagnosed code defects were patched and covered by focused regression tests.
- [success] C005: P007 P007 is successful: production has the repaired code synced and all backend services/workers restarted and healthy.
- [success] C006: P008 P008 is successful. Production is no longer wedged in active state, the repaired `agentctl` meta-read path works, and no recent post-deploy logs show the old failure signatures.
- [success] C007: P003 P003 is successful: the repaired code is deployed, services are healthy, the old active-session wedge is cleared, and the exact broken shell/meta path now succeeds.
- [success] C008: P000 The root problem is solved. The production stall was traced to a concrete three-part failure chain, all three code defects were fixed, and production is deployed with the affected session no longer active.
