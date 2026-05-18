# P693 stale residue scan commands

```bash
rg -n -i '(legacy|compat|fallback|deprecated|obsolete|old runtime|old worker|start all|all backends|AGENT_RUNTIME_PORT|Started Agent Runtime on|full topology|legacy_facade|main_novaic\.py .*queue-service)' novaic-agent-runtime scripts novaic-app/scripts novaic-app/src-tauri/resources/backends novaic-app/src-tauri/gen/apple/assets/backends docs/runbooks scripts/ci
```
