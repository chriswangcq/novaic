# Ticket: Prove Runtime Live Path Uses New FSM Worker Roster

## Problem Definition

We need evidence, not memory, that the currently committed runtime actually routes worker startup and queue-service execution through the new FSM/worker/roster path. The audit must distinguish live wired code from dead new code that was written but not connected.

## Proposed Solution

Inspect the launch path, runtime worker registry, worker roster, FSM runner, ledger repositories, and CI guards with pointer-sized reads. Then run the smallest targeted tests and lint guards that prove the path is wired. Record concrete file/function evidence and verification output.

## Acceptance Criteria

- Identify the process launch entrypoints that assemble runtime workers.
- Prove `runtime_roster` / registry definitions are consumed by deploy/startup paths.
- Prove session/task/saga FSM infrastructure is referenced by live worker code.
- Prove targeted CI/tests for runtime roster and FSM cutover pass.
- Explicitly label any discovered live-path gap instead of treating new code existence as proof.

## Verification Plan

- Use `rg`, `sed`, and file pointers to trace from deploy/start scripts into runtime worker registry and worker assemblies.
- Run targeted pytest files for FSM/roster cutover.
- Run runtime supervision/deploy guard scripts that prevent old process wiring from reappearing.
- Record the command outputs in a result body.

## Risks

- Some runtime paths may be launched indirectly by supervisor scripts, so the audit must include both Python entrypoints and shell/deploy scripts.
- Passing tests alone is insufficient if production entrypoints still bypass the registry.

## Assumptions

- The current branch and working tree represent the intended deployed code state to audit.
- This ticket is evidence-gathering only; no refactor should be performed here.
