## Ticket: 全局残留扫描与最终验证

### Problem Definition

All local GAP tickets are done, but the repository still needs a final global closure pass to prove the new FSM substrate / business DSL / worker roster direction is the live path and that no obvious retired branch, stale vocabulary, or hidden dependency residue remains in active code.

### Proposed Solution

- Run global residue scans for retired session, worker, prompt continuity, transitional, compatibility, and legacy branch terms.
- Run canonical guards and targeted package test groups covering FSM substrate, session/task/saga reducers, worker DSL/roster, Cortex explicit dependency boundary, and cleanup guards.
- Run the canonical full matrix if feasible; otherwise run enough deterministic subsets to identify concrete follow-up tickets and record the exact gap.
- Inspect current git diff stats so additions/removals are understood and no generated/cache artifacts are accidentally included.

### Acceptance Criteria

- Global scans have no untriaged active-code residue.
- Architecture guards pass.
- Targeted FSM/DSL package tests pass.
- Any failure is converted into a follow-up ticket instead of being hand-waved.
- If all checks pass, root problem can be checked against all child results.

### Verification Plan

- Run CI guard scripts and residue scans.
- Run targeted pytest groups across affected packages.
- Run `scripts/run_all_tests.sh` unless it proves too slow or fails with a concrete issue.
- Check `git status`/`git diff --stat` and remove accidental artifacts.

### Risks

- Full matrix may expose unrelated pre-existing failures; those must be identified precisely and either fixed if in scope or split into follow-up tickets.

### Assumptions

- Network-dependent deployment is not part of P006 unless explicitly requested; P006 validates repository state and runtime architecture wiring.
