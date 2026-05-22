# Add Entangled Migration Target Schema Preparation And Clean-Target Execution

## Problem

The offline migration command can plan, copy rows, reset identities, and write reports, but it still assumes Postgres target tables already exist. Add the missing target preparation layer so the command can safely prepare a clean target before copy: create/ensure required schemas through Entangled DDL/support-table helpers and perform confirmed clean-target cleanup without leaking secrets.

## Success Criteria

- Migration code can create or ensure Postgres target tables for planned dynamic entity tables and support tables before copying rows.
- Dynamic table schema preparation uses Entangled DDL helpers or the existing `SqlEntityDef`/support-table dialect helpers rather than unrelated handwritten table-only shortcuts.
- Confirmed clean-target execution clears only planned target tables/support tables and refuses to run without explicit confirmation.
- Cleanup and schema preparation run inside the target transaction boundary used by the migration command.
- Migration reports include target preparation and cleanup evidence without DSNs, passwords, tokens, or env-file contents.
- CLI non-dry-run path invokes target preparation before copy.
- Focused tests cover schema preparation SQL, cleanup refusal and execution, support-table preparation, report evidence, and secret redaction.
- `python -m py_compile` and full Entangled server-python pytest pass.
