# Normalize remaining runtime generation default boundaries

## Problem

The widened cross-repo guard found remaining raw generation/defaulting patterns in runtime session FSM, session repo state adapters, session ledger/audit, and broader task/saga/lease FSM infrastructure. Some may be safe projection/counter adapters, but they are not yet explicitly classified or normalized.

## Success Criteria

- Audit all widened guard hits involving `generation`, `finalize_generation`, `current_generation`, and related control-plane defaults in runtime Queue/task code.
- Replace live control-plane session generation coercions with explicit validators or typed inputs.
- Classify audit/projection/generic counter adapters as safe only with clear file evidence and tests where needed.
- Add focused regression tests for any live generation boundary changed.
- Rerun narrow and widened guards and provide a final clean matrix with no unclassified residue.
