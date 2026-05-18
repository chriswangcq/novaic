# Dev Startup Port And Service URL Contract Remediation

## Problem

The dev startup script names port `19996` as `PORT_CORTEX`, while app service config names the same port `vmcontrol`. Runtime worker commands also pass `--cortex-url "$CORTEX_URL"`, so the dev graph is ambiguous about whether `19996` is Cortex or VMControl.

## Success Criteria

- `novaic-app/scripts/start-backends.sh` no longer labels `19996` as Cortex unless it actually starts or expects Cortex there.
- Worker `--cortex-url` arguments remain explicit and are either derived from an explicitly named Cortex URL override/default or documented as requiring an external Cortex service.
- The status/startup text accurately describes what the dev script starts and what must run separately.
- Targeted scans for `PORT_CORTEX`, `CORTEX_URL`, `vmcontrol`, and `--cortex-url` show no ambiguous port naming.
- `bash -n novaic-app/scripts/start-backends.sh` passes.
