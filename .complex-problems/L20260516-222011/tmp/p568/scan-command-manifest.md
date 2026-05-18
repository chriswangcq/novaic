# P568 Scan Command Manifest

## Scope

This manifest closes P569 by making P568 reproducible from durable file evidence. It records the commands that generate the P568 scan artifacts, the artifact paths, and the success criteria each artifact supports.

## Command 1: Broad Stable/Temp Path Scan

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p568/path-compat-scan.txt`

Exact reproducible command:

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p568
{
  printf '%s\n' '## stable/temp/path compatibility terms in Cortex code and tests'
  rg -n \
    'novaic-cortex-sandbox-|/cortex/ro|/cortex/rw|/cortex|stable|adapter|mount|blob://cortex-payload|write_step' \
    novaic-cortex/novaic_cortex \
    novaic-cortex/tests
} > .complex-problems/L20260516-222011/tmp/p568/path-compat-scan.txt
```

Criteria supported:

- Records Cortex scan output for temp/stable path compatibility terms.
- Finds old backing-path marker references, stable path references, adapter/mount references, and nearby blob-reference hits.

## Command 2: Relevant Code/Test Slices

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p568/path-compat-slices.txt`

Exact reproducible command:

```bash
{
  printf '%s\n' '## stable path constants and capability notes'
  nl -ba novaic-cortex/novaic_cortex/logical_fs.py | sed -n '31,35p;98,108p;259,288p;330,343p'

  printf '\n%s\n' '## ephemeral path rejection'
  nl -ba novaic-cortex/novaic_cortex/sandbox.py | sed -n '31,49p;67,76p'

  printf '\n%s\n' '## logicalfs sanitize output'
  nl -ba novaic-logicalfs/logicalfs/substrate.py | sed -n '57,83p;119,149p;163,171p'

  printf '\n%s\n' '## path abuse tests'
  nl -ba novaic-cortex/tests/test_sandbox_requires_mount_namespace.py | sed -n '1,66p'
  nl -ba novaic-cortex/tests/test_sandboxd_wiring.py | sed -n '35,63p'
} > .complex-problems/L20260516-222011/tmp/p568/path-compat-slices.txt
```

Criteria supported:

- Reads relevant code slices with line references.
- Separates intended guardrails from risky fallback:
  - Intended guardrails: stable `/cortex` constants, sandboxd mount plan, `outer_command_path_adapter=False`, and explicit rejection of `novaic-cortex-sandbox-*`.
  - No risky compatibility fallback found in the inspected Cortex path.

## Classification Conclusion

P568 found no active old compatibility fallback for stable path handling. Stable paths are intentionally exposed as `/cortex/ro` and `/cortex/rw`; leaked `novaic-cortex-sandbox-*` paths are rejected before execution. Therefore P568 forwards no stable-path-specific remediation candidate to P554.

The broad scan also found `blob://cortex-payload/...` references. Those belong to sibling audits P563/P564 and are not stable-path compatibility remediation candidates.
