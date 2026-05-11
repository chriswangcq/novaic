# Complex Problem Ledger

Ledger: L20260511-165032
Schema: v6
Root: P000 - Audit unintegrated adapter paths after infrastructure cutovers
Status: done
Updated: 2026-05-11T09:12:32+00:00

## Problem Tree
- [done] P000: Audit unintegrated adapter paths after infrastructure cutovers
  - [done] P001: Audit Cortex LogicalFS and Sandbox adapter cutover
  - [done] P002: Audit Queue FSM Saga and session adapter cutover
  - [done] P003: Audit shell capability and tool CLI migration
  - [done] P004: Audit Cortex context event source cutover
  - [done] P005: Audit deployment process and compatibility residue

## Active

## Blocked

## Done
- [x] P000: Audit unintegrated adapter paths after infrastructure cutovers
- [x] P001: Audit Cortex LogicalFS and Sandbox adapter cutover
- [x] P002: Audit Queue FSM Saga and session adapter cutover
- [x] P003: Audit shell capability and tool CLI migration
- [x] P004: Audit Cortex context event source cutover
- [x] P005: Audit deployment process and compatibility residue

## Tickets
- [done] T000: Split audit by integration boundary -> P000 (split)
- [done] T001: Audit LogicalFS shell integration residue -> P001 (one_go)
- [done] T002: Audit Queue FSM Saga session cutover residue -> P002 (one_go)
- [done] T003: Audit shell capability and tool CLI migration residue -> P003 (one_go)
- [done] T004: Audit Context Event Source Cutover -> P004 (one_go)
- [done] T005: Audit Deployment and Compatibility Residue -> P005 (one_go)

## Latest Checks
- [success] C000: P001 Audit succeeded for this boundary: the full `/ro` shell miss is no longer present, no local sandbox fallback is live, and the remaining analogous risk is clearly identified as full `/rw/` materialization.
- [success] C001: P002 Audit succeeded for this boundary: the primary session path is on the session-ledger/outbox route, and the remaining live bypass surface is explicitly identified as unrestricted generic saga creation.
- [success] C002: P003 Success. The audit proved the live tool boundary is connected to the intended final shape: final harness tools remain direct, while IM/subagent/audio/payload/device have moved behind shell capability commands.
- [success] C003: P004 Success. The live LLM preparation path is ContextEvent-backed and the audit found no active legacy DFS fallback. The remaining issues are stale comments/docstrings and projection/debug endpoints, not unintegrated active context assembly.
- [success] C004: P005 Success. The deployment/process wiring audit found no active old sandbox-core or retired worker path. The current remote deployment is healthy and matches the intended service/process roster.
- [success] C005: P000 Success. The audit covered the requested infrastructure boundaries, separated live gaps from residue, and produced a prioritized fix list with evidence. The problem was an audit problem, so discovered gaps do not make the audit unsuccessful; they are the audit output.
