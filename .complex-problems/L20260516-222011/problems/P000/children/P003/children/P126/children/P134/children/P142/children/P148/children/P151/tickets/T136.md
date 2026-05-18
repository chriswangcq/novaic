# Scan for direct workspace step write bypasses

## Problem Definition

Even with strict workspace/API/runtime producers, active code can still bypass the contract by directly writing `steps/*.json`, appending `_index.jsonl`, or calling low-level storage helpers with ad hoc step shapes. This scan must prove old write branches are gone or safely scoped.

## Proposed Solution

Run repository-wide scans for `write_step`, `write_step_projection`, `_sys_write_json`, `_sys_append_line`, `steps/_index.jsonl`, and raw step path construction. Classify non-test hits as active, helper-internal, or harmless read/test code. Patch any active bypass to use the workspace boundary or add a guard test if the scan proves clean.

## Acceptance Criteria

- Non-test write-step and step-file write sites are listed with source pointers.
- Any direct write to step files is either the workspace boundary itself or assistant/scope-specific behavior that cannot carry tool raw payloads.
- No active non-test code writes tool result data directly to `steps/*.json` or `_index.jsonl` outside workspace methods.
- A residue/scan test or source evidence makes the conclusion repeatable.

## Verification Plan

Use `rg` scans and run existing residue tests if present. Add a focused residue guard only if no current test prevents new bypasses.

## Risks

- Some legitimate helper code may look like a bypass; classification must be precise.
- Over-broad residue tests can become brittle if they flag test fixtures or docs.

## Assumptions

- Tests and ledger artifacts may contain sample step writes; the active-code boundary is what matters.
