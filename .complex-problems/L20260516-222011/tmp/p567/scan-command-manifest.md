# P567 Scan Command Manifest

## Scope

This manifest makes P567 reproducible from durable file evidence. It records the commands that generate shell fallback/executor bypass scan artifacts, the artifact paths, and the criteria each artifact supports.

## Command 1: Shell Fallback And Executor Scan

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-scan.txt`

Exact reproducible command:

```bash
mkdir -p .complex-problems/L20260516-222011/tmp/p567
{
  printf '%s\n' '## subprocess/process/fallback terms in Cortex code and tests'
  rg -n 'subprocess|Popen|os\.system|fallback|process_runner|sandbox_process_runner|execute|SandboxdClient|executor|conn\.execute' \
    novaic-cortex/novaic_cortex \
    novaic-cortex/tests

  printf '\n%s\n' '## explicit local executor class names'
  rg -n 'SandboxExecutor|sandboxd|SandboxdClient|process_runner|must go through sandboxd|execute local shell processes' \
    novaic-cortex/novaic_cortex \
    novaic-cortex/tests
} > .complex-problems/L20260516-222011/tmp/p567/shell-fallback-scan.txt
```

Criteria supported:

- Records scan output for fallback, subprocess, process runner, and sandbox executor terms.
- Separates production sandboxd wiring from test-only subprocess/capability-script execution.

## Command 2: Shell Fallback Source/Test Slices

Output artifact:

- `.complex-problems/L20260516-222011/tmp/p567/shell-fallback-slices.txt`

Exact reproducible command:

```bash
{
  printf '%s\n' '## cortex main wiring'
  nl -ba novaic-cortex/novaic_cortex/main_cortex.py | sed -n '91,101p'

  printf '\n%s\n' '## api build cortex'
  nl -ba novaic-cortex/novaic_cortex/api.py | sed -n '61,130p;315,331p'

  printf '\n%s\n' '## runtime sandbox construction'
  nl -ba novaic-cortex/novaic_cortex/runtime.py | sed -n '30,64p;178,193p'

  printf '\n%s\n' '## sandbox orchestrator failure and execute path'
  nl -ba novaic-cortex/novaic_cortex/sandbox.py | sed -n '31,152p;155,197p'

  printf '\n%s\n' '## tests fake runner examples'
  nl -ba novaic-cortex/tests/test_sandboxd_wiring.py | sed -n '1,210p'
} > .complex-problems/L20260516-222011/tmp/p567/shell-fallback-slices.txt
```

Criteria supported:

- Reads relevant code slices with line references.
- Confirms production shell execution goes through `SandboxdClient` and fails explicitly when no sandbox executor is configured.
- Shows test-only fake runner usage.

## Classification Conclusion

No production Cortex local execution fallback remains. P567 forwards no remediation candidate to P554. Sandbox-service internals remain covered by sibling P565.
