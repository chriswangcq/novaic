# Agent runtime loop and worker role map

## Entrypoint Evidence

- Main CLI/process wrapper: `novaic-agent-runtime/main_novaic.py`.
- Queue-service API process can be launched through runtime wrapper mode `queue-service`, but durable queue state lives in `queue_service/*`.
- Runtime worker modes include task-worker, saga-worker, session-outbox-worker, saga-outbox-worker, health, and scheduler.
- Runtime execution/tool/shell responsibilities are in agent-runtime modules and interact with Cortex/Business/Blob/Sandbox/LLM Factory over service boundaries.

## Role Boundary Draft

- Runtime process/CPU: runs agent loops and worker computations.
- Queue Service DB/ledger/outbox: durable coordination state, not process memory.
- Shell/tool execution: runtime invokes shell/devicectl/agentctl style tools and records bounded outputs; file/media objects are externalized through service contracts.
- Scheduler/health worker modes: runtime-side worker roles that call queue/business/cortex URLs, not standalone product services.

## Worker Mode Evidence Head
novaic-agent-runtime/main_novaic.py:21:    novaic-backend gateway --host HOST --port PORT --data-dir PATH --queue-service-url URL --vmcontrol-url URL --blob-service-url URL
novaic-agent-runtime/main_novaic.py:22:    novaic-backend queue-service --host HOST --port PORT --data-dir PATH
novaic-agent-runtime/main_novaic.py:23:    novaic-backend task-worker --queue-service-url URL --num-workers N --data-dir PATH
novaic-agent-runtime/main_novaic.py:24:    novaic-backend saga-worker --queue-service-url URL --max-concurrent N --data-dir PATH
novaic-agent-runtime/main_novaic.py:25:    novaic-backend session-outbox-worker --data-dir PATH
novaic-agent-runtime/main_novaic.py:26:    novaic-backend saga-outbox-worker --data-dir PATH
novaic-agent-runtime/main_novaic.py:27:    novaic-backend health --queue-service-url URL --task-timeout N --saga-timeout N --data-dir PATH
novaic-agent-runtime/main_novaic.py:28:    novaic-backend scheduler --business-url URL --queue-service-url URL --data-dir PATH
novaic-agent-runtime/main_novaic.py:38:# (task/saga/health/scheduler + queue_service when launched here) pick
novaic-agent-runtime/main_novaic.py:55:    novaic-backend queue-service [options] Queue Service (Task/Saga 队列)
novaic-agent-runtime/main_novaic.py:56:    novaic-backend task-worker [options]   Task Worker (任务执行)
novaic-agent-runtime/main_novaic.py:57:    novaic-backend saga-worker [options]   Saga Worker (流程编排)
novaic-agent-runtime/main_novaic.py:58:    novaic-backend session-outbox-worker [options] Session Outbox Worker (session durable side effects)
novaic-agent-runtime/main_novaic.py:59:    novaic-backend saga-outbox-worker [options] Saga Outbox Worker (saga durable compensation effects)
novaic-agent-runtime/main_novaic.py:60:    novaic-backend health [options]        Health Worker (超时回收)
novaic-agent-runtime/main_novaic.py:61:    novaic-backend scheduler [options]     Scheduler Worker (定时唤醒)
novaic-agent-runtime/main_novaic.py:65:    novaic-backend queue-service --host 127.0.0.1 --port 19997 --data-dir /Users/me/.novaic
novaic-agent-runtime/main_novaic.py:66:    novaic-backend gateway --host 127.0.0.1 --port 19999 --data-dir /Users/me/.novaic --queue-service-url http://127.0.0.1:19997 --vmcontrol-url http://127.0.0.1:19996 --blob-service-url http://127.0.0.1:19995
novaic-agent-runtime/main_novaic.py:67:    novaic-backend task-worker --queue-service-url http://127.0.0.1:19997 --num-workers 5 --data-dir /Users/me/.novaic
novaic-agent-runtime/main_novaic.py:80:    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
novaic-agent-runtime/main_novaic.py:138:def run_worker_mode_if_registered(mode: str, argv: list[str]) -> bool:
novaic-agent-runtime/main_novaic.py:233:                    f"http://{args.host}:{args.port}/api/health",
novaic-agent-runtime/main_novaic.py:339:    elif mode == "queue-service":
novaic-agent-runtime/main_novaic.py:341:    elif run_worker_mode_if_registered(mode, sys.argv[1:]):
novaic-agent-runtime/queue_service/main.py:34:LOG_FILE = os.path.join(LOG_DIR, f"queue-service-{datetime.utcnow().strftime('%Y%m%d')}.log")
novaic-agent-runtime/queue_service/main.py:37:# so ``rg scope_id=$SID queue-service*.log`` works cross-service.
novaic-agent-runtime/queue_service/main.py:108:# ``X-Internal-Key``. ``/health`` and ``/`` remain open for LB probes.
novaic-agent-runtime/queue_service/main.py:110:_QUEUE_PUBLIC_PATHS = ("/health", "/ready", "/")
novaic-agent-runtime/queue_service/main.py:224:@app.get("/health")
novaic-agent-runtime/queue_service/main.py:225:def health_check():
novaic-agent-runtime/queue_service/main.py:228:        "status": "healthy",
novaic-agent-runtime/queue_service/main.py:229:        "service": "queue-service",
novaic-agent-runtime/queue_service/main.py:237:    """Readiness probe — deep health (P3-8).
novaic-agent-runtime/queue_service/main.py:309:        "service": "queue-service",
novaic-agent-runtime/queue_service/main.py:327:            "health": "/health",
novaic-agent-runtime/queue_service/worker/generic_worker.py:4:is a task, saga, outbox effect, scheduler tick, or health tick.
novaic-agent-runtime/queue_service/saga_repo.py:1149:    Saga lifecycle coordinator for queue-service-owned failure handling.
novaic-agent-runtime/main_novaic.py:21:    novaic-backend gateway --host HOST --port PORT --data-dir PATH --queue-service-url URL --vmcontrol-url URL --blob-service-url URL
novaic-agent-runtime/main_novaic.py:22:    novaic-backend queue-service --host HOST --port PORT --data-dir PATH
novaic-agent-runtime/main_novaic.py:23:    novaic-backend task-worker --queue-service-url URL --num-workers N --data-dir PATH
novaic-agent-runtime/main_novaic.py:24:    novaic-backend saga-worker --queue-service-url URL --max-concurrent N --data-dir PATH
novaic-agent-runtime/main_novaic.py:25:    novaic-backend session-outbox-worker --data-dir PATH
novaic-agent-runtime/main_novaic.py:26:    novaic-backend saga-outbox-worker --data-dir PATH
novaic-agent-runtime/main_novaic.py:27:    novaic-backend health --queue-service-url URL --task-timeout N --saga-timeout N --data-dir PATH
novaic-agent-runtime/main_novaic.py:28:    novaic-backend scheduler --business-url URL --queue-service-url URL --data-dir PATH
novaic-agent-runtime/main_novaic.py:38:# (task/saga/health/scheduler + queue_service when launched here) pick
novaic-agent-runtime/main_novaic.py:55:    novaic-backend queue-service [options] Queue Service (Task/Saga 队列)
novaic-agent-runtime/main_novaic.py:56:    novaic-backend task-worker [options]   Task Worker (任务执行)
novaic-agent-runtime/main_novaic.py:57:    novaic-backend saga-worker [options]   Saga Worker (流程编排)
novaic-agent-runtime/main_novaic.py:58:    novaic-backend session-outbox-worker [options] Session Outbox Worker (session durable side effects)
novaic-agent-runtime/main_novaic.py:59:    novaic-backend saga-outbox-worker [options] Saga Outbox Worker (saga durable compensation effects)
novaic-agent-runtime/main_novaic.py:60:    novaic-backend health [options]        Health Worker (超时回收)
novaic-agent-runtime/main_novaic.py:61:    novaic-backend scheduler [options]     Scheduler Worker (定时唤醒)
novaic-agent-runtime/main_novaic.py:65:    novaic-backend queue-service --host 127.0.0.1 --port 19997 --data-dir /Users/me/.novaic
novaic-agent-runtime/main_novaic.py:66:    novaic-backend gateway --host 127.0.0.1 --port 19999 --data-dir /Users/me/.novaic --queue-service-url http://127.0.0.1:19997 --vmcontrol-url http://127.0.0.1:19996 --blob-service-url http://127.0.0.1:19995
novaic-agent-runtime/main_novaic.py:67:    novaic-backend task-worker --queue-service-url http://127.0.0.1:19997 --num-workers 5 --data-dir /Users/me/.novaic
novaic-agent-runtime/main_novaic.py:80:    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
novaic-agent-runtime/main_novaic.py:138:def run_worker_mode_if_registered(mode: str, argv: list[str]) -> bool:
novaic-agent-runtime/main_novaic.py:233:                    f"http://{args.host}:{args.port}/api/health",
novaic-agent-runtime/main_novaic.py:339:    elif mode == "queue-service":
novaic-agent-runtime/main_novaic.py:341:    elif run_worker_mode_if_registered(mode, sys.argv[1:]):
novaic-agent-runtime/task_queue/workers/command_specs.py:65:class WorkerRegistry:
novaic-agent-runtime/task_queue/workers/scheduled_wake.py:12:from task_queue.workers.scheduler_action_specs import (
novaic-agent-runtime/task_queue/workers/runtime_roster.py:23:    "task-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:24:    "saga-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:25:    "session-outbox-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:26:    "saga-outbox-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:27:    "health",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:28:    "scheduler",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:34:        label="task-worker control",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:35:        pattern="main_novaic.py task-worker .*--pool control",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:37:        log_files=("task-worker-control-1.log", "task-worker-control-2.log"),
novaic-agent-runtime/task_queue/workers/runtime_roster.py:39:            '$PY $MAIN task-worker $TASK_WORKER_ARGS '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:41:            '>> "$LOG_DIR/task-worker-control-1.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:42:            '$PY $MAIN task-worker $TASK_WORKER_ARGS '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:44:            '>> "$LOG_DIR/task-worker-control-2.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:48:        label="task-worker execution",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:49:        pattern="main_novaic.py task-worker .*--pool execution",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:51:        log_files=("task-worker-execution-1.log", "task-worker-execution-2.log"),
novaic-agent-runtime/task_queue/workers/runtime_roster.py:53:            '$PY $MAIN task-worker $TASK_WORKER_ARGS '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:55:            '>> "$LOG_DIR/task-worker-execution-1.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:56:            '$PY $MAIN task-worker $TASK_WORKER_ARGS '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:58:            '>> "$LOG_DIR/task-worker-execution-2.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:62:        label="saga-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:63:        pattern="main_novaic.py saga-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:65:        log_files=("saga-worker-1.log", "saga-worker-2.log"),
novaic-agent-runtime/task_queue/workers/runtime_roster.py:67:            '$PY $MAIN saga-worker $SAGA_WORKER_ARGS --max-concurrent 4 '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:68:            '>> "$LOG_DIR/saga-worker-1.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:69:            '$PY $MAIN saga-worker $SAGA_WORKER_ARGS --max-concurrent 4 '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:70:            '>> "$LOG_DIR/saga-worker-2.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:74:        label="session-outbox-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:75:        pattern="main_novaic.py session-outbox-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:77:        log_files=("session-outbox-worker.log",),
novaic-agent-runtime/task_queue/workers/runtime_roster.py:79:            '$PY $MAIN session-outbox-worker --data-dir "$DATA_DIR" '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:80:            '>> "$LOG_DIR/session-outbox-worker.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:84:        label="saga-outbox-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:85:        pattern="main_novaic.py saga-outbox-worker",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:87:        log_files=("saga-outbox-worker.log",),
novaic-agent-runtime/task_queue/workers/runtime_roster.py:89:            '$PY $MAIN saga-outbox-worker --data-dir "$DATA_DIR" '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:90:            '>> "$LOG_DIR/saga-outbox-worker.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:94:        label="health",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:95:        pattern="main_novaic.py health",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:97:        log_files=("health.log",),
novaic-agent-runtime/task_queue/workers/runtime_roster.py:99:            '$PY $MAIN health --queue-service-url "$QS_URL" --data-dir "$DATA_DIR" '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:100:            '>> "$LOG_DIR/health.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:104:        label="scheduler",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:105:        pattern="main_novaic.py scheduler",
novaic-agent-runtime/task_queue/workers/runtime_roster.py:107:        log_files=("scheduler.log",),
novaic-agent-runtime/task_queue/workers/runtime_roster.py:109:            '$PY $MAIN scheduler $SCHEDULER_ARGS '
novaic-agent-runtime/task_queue/workers/runtime_roster.py:110:            '>> "$LOG_DIR/scheduler.log" 2>&1 &',
novaic-agent-runtime/task_queue/workers/runtime_roster.py:127:            '--queue-service-url "$QS_URL" '
novaic-agent-runtime/task_queue/workers/health_effects.py:25:            "health.recover_all": self._recover_all,
novaic-agent-runtime/task_queue/workers/health_effects.py:40:                service_name="runtime-health",
novaic-agent-runtime/task_queue/workers/health_action_specs.py:1:"""Pure health recovery action specs."""
novaic-agent-runtime/task_queue/workers/health_action_specs.py:31:        "health.recover_all",
novaic-agent-runtime/task_queue/workers/scheduler_effects.py:23:            "scheduler.get_due_for_wake": self._get_due_for_wake,
novaic-agent-runtime/task_queue/workers/scheduler_effects.py:24:            "scheduler.dispatch_wake": self._dispatch_wake,
novaic-agent-runtime/task_queue/workers/registry.py:11:    WorkerRegistry,
novaic-agent-runtime/task_queue/workers/registry.py:17:    assemble_health_worker,
novaic-agent-runtime/task_queue/workers/registry.py:20:    assemble_scheduler_worker,
novaic-agent-runtime/task_queue/workers/registry.py:26:def build_runtime_worker_registry() -> WorkerRegistry:
novaic-agent-runtime/task_queue/workers/registry.py:29:    return WorkerRegistry(_runtime_worker_commands())
novaic-agent-runtime/task_queue/workers/registry.py:34:        "task-worker": WorkerSpec(
novaic-agent-runtime/task_queue/workers/registry.py:35:            mode="task-worker",
novaic-agent-runtime/task_queue/workers/registry.py:39:                WorkerOption(("--queue-service-url",), default=config_default("QUEUE_SERVICE_URL"), help="Queue Service URL"),
novaic-agent-runtime/task_queue/workers/registry.py:52:        "saga-worker": WorkerSpec(
novaic-agent-runtime/task_queue/workers/registry.py:53:            mode="saga-worker",
novaic-agent-runtime/task_queue/workers/registry.py:56:                WorkerOption(("--queue-service-url",), default=config_default("QUEUE_SERVICE_URL"), help="Queue Service URL"),
novaic-agent-runtime/task_queue/workers/registry.py:63:        "session-outbox-worker": WorkerSpec(
novaic-agent-runtime/task_queue/workers/registry.py:64:            mode="session-outbox-worker",
novaic-agent-runtime/task_queue/workers/registry.py:73:        "saga-outbox-worker": WorkerSpec(
novaic-agent-runtime/task_queue/workers/registry.py:74:            mode="saga-outbox-worker",
novaic-agent-runtime/task_queue/workers/registry.py:83:        "health": WorkerSpec(
novaic-agent-runtime/task_queue/workers/registry.py:84:            mode="health",
novaic-agent-runtime/task_queue/workers/registry.py:87:                WorkerOption(("--queue-service-url",), default=config_default("QUEUE_SERVICE_URL"), help="Queue Service URL"),
novaic-agent-runtime/task_queue/workers/registry.py:94:            build_process=assemble_health_worker,
novaic-agent-runtime/task_queue/workers/registry.py:96:        "scheduler": WorkerSpec(
novaic-agent-runtime/task_queue/workers/registry.py:97:            mode="scheduler",
novaic-agent-runtime/task_queue/workers/registry.py:101:                WorkerOption(("--queue-service-url",), default=config_default("QUEUE_SERVICE_URL"), help="Queue Service URL"),
novaic-agent-runtime/task_queue/workers/registry.py:107:            build_process=assemble_scheduler_worker,
novaic-agent-runtime/task_queue/workers/registry.py:114:    registry: WorkerRegistry,
novaic-agent-runtime/task_queue/workers/__init__.py:11:from .health_worker import HealthRecoveryHandler
novaic-agent-runtime/task_queue/workers/__init__.py:12:from .scheduler_worker import ScheduledWakeHandler
novaic-agent-runtime/task_queue/workers/task_worker.py:34:    name = "task-worker"
novaic-agent-runtime/task_queue/workers/scheduler_worker.py:17:    name = "scheduler"
novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py:1:"""Process-wide DispatchAssembler factory for the runtime scheduler worker."""
novaic-agent-runtime/task_queue/workers/wake/assembler_factory.py:28:        service_name="runtime-scheduler",
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:16:    assemble_health_worker as _assemble_health_worker,
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:19:    assemble_scheduler_worker as _assemble_scheduler_worker,
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:36:    WorkerAssemblySpec(mode="task-worker", build_process=_assemble_task_worker),
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:37:    WorkerAssemblySpec(mode="saga-worker", build_process=_assemble_saga_worker),
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:38:    WorkerAssemblySpec(mode="session-outbox-worker", build_process=_assemble_session_outbox_worker),
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:39:    WorkerAssemblySpec(mode="saga-outbox-worker", build_process=_assemble_saga_outbox_worker),
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:40:    WorkerAssemblySpec(mode="health", build_process=_assemble_health_worker),
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:41:    WorkerAssemblySpec(mode="scheduler", build_process=_assemble_scheduler_worker),
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:67:    return assemble_worker_process("task-worker", args, deps)
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:74:    return assemble_worker_process("saga-worker", args, deps)
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:81:    return assemble_worker_process("session-outbox-worker", args, deps)
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:88:    return assemble_worker_process("saga-outbox-worker", args, deps)
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:91:def assemble_health_worker(
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:95:    return assemble_worker_process("health", args, deps)
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:98:def assemble_scheduler_worker(
novaic-agent-runtime/task_queue/workers/worker_assemblies.py:102:    return assemble_worker_process("scheduler", args, deps)
novaic-agent-runtime/task_queue/workers/assembly_factories.py:63:    deps.setup_worker_logging("task-worker")
novaic-agent-runtime/task_queue/workers/assembly_factories.py:75:    deps.printer(f"[task-worker] Pool={args.pool}, subscribed to {len(topics)} topics: {sorted(topics)}")
novaic-agent-runtime/task_queue/workers/assembly_factories.py:77:    bundle = WorkerRuntimeBundle.system("task-worker")
novaic-agent-runtime/task_queue/workers/assembly_factories.py:134:        label="task-worker",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:137:            "[task-worker] Starting...",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:138:            f"[task-worker] Worker ID: {worker_id}",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:139:            f"[task-worker] Pool: {args.pool}",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:140:            f"[task-worker] Business URL: {args.business_url}",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:141:            f"[task-worker] Queue Service URL: {args.queue_service_url}",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:142:            f"[task-worker] Num workers: {args.num_workers} (reserved)",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:158:    deps.setup_worker_logging("saga-worker")
novaic-agent-runtime/task_queue/workers/assembly_factories.py:174:    bundle = WorkerRuntimeBundle.system("saga-worker")
novaic-agent-runtime/task_queue/workers/assembly_factories.py:203:        deps.printer(f"[saga-worker] Registered: {saga_def.name} ({len(saga_def.steps)} steps)")
novaic-agent-runtime/task_queue/workers/assembly_factories.py:223:        label="saga-worker",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:226:            "[saga-worker] Starting...",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:227:            f"[saga-worker] Worker ID: {worker_id}",
novaic-agent-runtime/task_queue/workers/assembly_factories.py:228:            f"[saga-worker] Queue Service URL: {args.queue_service_url}",
