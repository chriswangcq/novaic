# Round 002 Desktop Startup Triage Matrix

## Scope
Startup diagnostics events emitted by desktop bootstrap in `novaic-app/src-tauri/src/main.rs`.

## Event-to-Triage Mapping

| Event stage | status | Typical symptom | Primary cause class | First actions |
|---|---|---|---|---|
| `port-preflight` | `error` | Startup aborts before services | Local port conflict | Stop conflicting process; retry app launch |
| `runtime-orchestrator` | `error` | No internal runtime API | Binary/path/runtime boot failure | Check backend binary path and app data permissions |
| `runtime-orchestrator-health` | `timeout` | Gateway not started | Runtime orchestrator started but unhealthy | Inspect runtime logs; verify DB/data-dir writeability |
| `gateway` | `error` | API unavailable at `127.0.0.1:19999` | Gateway startup argument/config issue | Check gateway startup args and resource dir resolution |
| `gateway-health` | `timeout` | UI cannot use API routes | Gateway alive but health endpoint not ready | Check migration/boot latency and startup logs |
| `vmcontrol` | `error` | VM control API unavailable | vmcontrol binary not found or boot failed | Verify `NOVAIC_VMCONTROL_BIN` / bundled binary / log output |
| `tool-result-service` | `error` | Tools chain degraded | TRS process boot failure | Inspect TRS service logs and env wiring |
| `tool-result-service-health` | `timeout` | Tools server blocked from startup | TRS dependency unhealthy | Verify TRS `/api/health` and binding |
| `tools-server` | `error` | Tool execution API unavailable | Tools server startup failure | Check backend subcommand availability and args |
| `tools-server-health` | `timeout` | Workers not started | Tools server running but unhealthy | Check tools server health endpoint and upstream deps |
| `queue-service` | `error` | No queue processing | Queue service startup failure | Check queue service startup parameters |
| `queue-service-health` | `timeout` | Workers not started | Queue service not ready in timeout window | Verify queue health endpoint and db connectivity |
| `file-service` | `error` | File API unavailable | File service startup failure | Check file service startup args and data dir |

## Evidence Sources
- Startup event log: app data `logs/startup-diagnostics.jsonl`
- VmControl log: app data `logs/vmcontrol.log`
- Startup code path: `novaic-app/src-tauri/src/main.rs`

## Notes
- If any `timeout` event appears, classify as dependency chain risk and stop further rollout.
- For Gate C, clean-machine validation must include at least one successful run with no `error` or `timeout` events.
