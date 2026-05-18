# P566 Scan Command Manifest

## Scope

This manifest makes P566 reproducible from durable file evidence. It records the commands that generate the materialization/direct-file scan artifacts, the artifact paths, and the criteria each artifact supports.

## Command 1: Materialize And Direct File Scan

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p566/materialize-scan.txt`

Exact reproducible command:

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p566
{
  printf '%s\n' '## materialize terms'
  rg -n 'materialize|materialized|Materialize' novaic-cortex/novaic_cortex novaic-cortex/tests

  printf '\n%s\n' '## direct _files access'
  rg -n '_files|list_object_keys|key\(' novaic-cortex/novaic_cortex novaic-cortex/tests

  printf '\n%s\n' '## rw scratch terms'
  rg -n '/rw/scratch|RW_SCRATCH|scratch' novaic-cortex/novaic_cortex novaic-cortex/tests
} > .complex-problems/L20260516-222011/tmp/p566/materialize-scan.txt
```

Criteria supported:

- Records scan output for `Workspace.materialize()`, materialized context terms, direct file authority access, and `/rw/scratch` terms.
- Identifies the remediation bucket forwarded to P554: `Workspace.materialize()` plus legacy root `/rw/scratch`.

## Command 2: Materialize Source/Test Slices

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p566/materialize-slices.txt`

Exact reproducible command:

```bash
{
  printf '%s\n' '## workspace materialize code'
  nl -ba novaic-cortex/novaic_cortex/workspace.py | sed -n '520,560p;563,621p;623,660p;823,850p;995,1005p'

  printf '\n%s\n' '## logical fs materialization code'
  nl -ba novaic-cortex/novaic_cortex/logical_fs.py | sed -n '216,328p'

  printf '\n%s\n' '## workspace materialize tests'
  nl -ba novaic-cortex/tests/test_workspace_materialize.py | sed -n '1,80p'

  printf '\n%s\n' '## shell capabilities scratch code'
  nl -ba novaic-cortex/novaic_cortex/shell_capabilities.py | sed -n '130,147p'
} > .complex-problems/L20260516-222011/tmp/p566/materialize-slices.txt
```

Criteria supported:

- Reads relevant code slices with line references.
- Separates intended LogicalFS materialization from removable `Workspace.materialize()`.
- Shows test-only callers and legacy `/rw/scratch` expectations that P554 should clean.

## Classification Conclusion

`Workspace.materialize()` and the legacy global `/rw/scratch` layout are risky/removable residue. P566 forwards those as P554 remediation candidates. LogicalFS provider materialization and Workspace internal `_files` calls are intended implementation details for this audit.
