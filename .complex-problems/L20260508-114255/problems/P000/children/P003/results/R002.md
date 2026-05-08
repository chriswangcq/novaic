## Result: P003 Runtime Wiring Deployment And Old-Path Residue Audit

### Done Items

- Checked git status and retired file presence.
- Inspected `main_novaic.py`, worker registry, process runner, command specs, startup scripts, and PyInstaller spec.
- Checked deployed service status and runtime process list on `api.gradievo.com`.
- Checked worker logs for current activity and stale error residue.

### Achieved State

The unified runtime worker entrypoint is live in local wiring and deployed process state:

- `novaic-agent-runtime/main_task.py` is physically absent.
- `novaic-agent-runtime/main_saga.py` is physically absent.
- `main_novaic.py:126-145` builds the runtime worker registry and delegates registered worker modes via `run_worker_registry_command`.
- `main_novaic.py:341` routes unknown built-in service modes to `run_worker_mode_if_registered(mode, sys.argv[1:])`.
- `task_queue/workers/registry.py:31-108` declares six worker modes:
  - `task-worker`
  - `saga-worker`
  - `session-outbox-worker`
  - `saga-outbox-worker`
  - `health`
  - `scheduler`
- `task_queue/workers/process_runner.py:27-47` provides shared signal handling, run, cleanup, and shutdown behavior.
- `scripts/start.sh:228-267` starts task workers, saga workers, session outbox, saga outbox, health, and scheduler via `main_novaic.py`.
- `novaic-app/scripts/start-backends.sh:218-262` does the same for dev mode.
- `novaic-agent-runtime/novaic-agent-runtime.spec:11-54` packages `main_novaic.py`, worker registry/process runner, and current worker handler modules.

### Deployment Evidence

`./deploy status` reported all core ports up and `Workers: 10`.

Remote process inspection showed the intended visible runtime worker set:

- 1 `queue-service`
- 4 `task-worker` processes: 2 `control`, 2 `execution`
- 2 `saga-worker` processes
- 1 `session-outbox-worker`
- 1 `saga-outbox-worker`
- 1 `health`
- 1 `scheduler`
- 1 standalone `main_subscriber.py`

No deployed `main_task.py`, `main_saga.py`, or old app worker process was found. A generic system process named `[watchdogd]` exists on the host, but it is not a NovAIC runtime worker path.

### Remaining Gap

Runtime wiring is now on the unified worker path, but the operational model is still script-spawned subprocesses rather than a stronger process supervisor:

- `scripts/start.sh` starts workers with background `&` and kills with `pkill`; this is visible and simple but not the final resilient process-supervisor model.
- Worker logs can contain stale historical errors. Example: `saga-outbox-worker.log` still has an old `sqlite3.OperationalError: database is locked` line before later successful reconnect lines. This can mislead audits unless logs are timestamp-aware or rotated.
- The packaging usage comment currently lists `session-outbox-worker` but does not show `saga-outbox-worker`, `health`, or `scheduler` in its top usage snippet, although hiddenimports include current worker modules. This is documentation residue, not a live-path blocker.

### Verification

- Local retired files:
  - `ABSENT novaic-agent-runtime/main_task.py`
  - `ABSENT novaic-agent-runtime/main_saga.py`
- Deployed current workers:
  - `main_novaic.py task-worker`
  - `main_novaic.py saga-worker`
  - `main_novaic.py session-outbox-worker`
  - `main_novaic.py saga-outbox-worker`
  - `main_novaic.py health`
  - `main_novaic.py scheduler`
  - `main_novaic.py queue-service`
- Remote health/scheduler logs show fresh May 8 successful HTTP activity.

### Artifacts

- `P003-ticket.md`
- This result file.

### Gaps To Carry Forward

- Add timestamp-aware log checks or log rotation in deployment verification.
- Consider process supervision beyond shell backgrounding if runtime robustness is part of the final target.
- Update PyInstaller spec comments to avoid stale worker list confusion.
