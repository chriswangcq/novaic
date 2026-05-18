# Queue service launch command supplement

## Command Evidence Summary

- Raw targeted scan: `launch-command-scan.txt`.
- Queue service API process references are expected around service config and local/package launchers.
- Task/saga/session-outbox/saga-outbox workers appear mainly as agent-runtime worker modes or queue_service worker modules, not necessarily direct queue_service process commands.

## Presence Checks
- present: queue_service
- present: queue-service
- present: saga
- present: task
- present: session-outbox
- present: saga-outbox
- present: scheduler

## Evidence Head
novaic-common/config/services.json:12:    "queue_service_internal_key": "queue-internal-dev",
novaic-common/config/services.json:24:    "queue_service":      { "url": "http://127.0.0.1:19997" },
novaic-common/config/services.json:81:    "scheduler_poll_interval_seconds": 1.0
novaic-agent-runtime/queue_service/routes.py:5:队列数据库集中在 Queue Service 进程，Worker 只能通过本 API 访问。
novaic-agent-runtime/queue_service/routes.py:14:from queue_service.queue_db import TaskQueue
novaic-agent-runtime/queue_service/routes.py:15:from queue_service.saga_repo import SagaRepository, SagaOrchestrator
novaic-agent-runtime/queue_service/routes.py:16:from queue_service.session_repo import SessionRepository
novaic-agent-runtime/queue_service/routes.py:17:from queue_service.exceptions import TaskNotFoundError, SagaError
novaic-agent-runtime/queue_service/routes.py:356:        """获取所有已知的 topics (Task Worker 启动时调用)"""
novaic-agent-runtime/queue_service/routes.py:415:            """Saga Worker 建完 DAG 后调用，标记 launched 并释放 claim"""
novaic-agent-runtime/queue_service/routes.py:421:            """标记 Saga 完成 (Saga Worker 调用)"""
novaic-agent-runtime/queue_service/routes.py:427:            """标记 Saga 失败 (Saga Worker 调用)"""
novaic-agent-runtime/queue_service/routes.py:435:# Handler Execution API - 不属于 Queue Service
novaic-agent-runtime/queue_service/routes.py:438:# Queue Service 是纯调度中间件，不执行业务逻辑；handler/tool
novaic-agent-runtime/queue_service/routes.py:444:# Business Entry API - 不属于 Queue Service
novaic-agent-runtime/queue_service/routes.py:448:# Queue Service 只接收已归一化的 dispatch / task / saga 请求。
scripts/build-all.sh:108:echo "  $BUILD_DIR/novaic-agent-runtime scheduler --business-url http://127.0.0.1:19998 --queue-service-url http://127.0.0.1:19997"
novaic-agent-runtime/README.md:3:Task / Saga workers、队列消费、LLM 调用与工具分发（`task_queue/`、`queue_service/`）。与 Queue Service、Business、Cortex、LLM Factory 通过 HTTP 协作；Gateway 只在边缘广播/信令场景作为配置存在。
novaic-agent-runtime/main_novaic.py:8:  - Queue Service: Task/Saga 队列管理
novaic-agent-runtime/main_novaic.py:9:  - Task Worker: 通用任务执行器
novaic-agent-runtime/main_novaic.py:10:  - Saga Worker: Saga 流程编排
novaic-agent-runtime/main_novaic.py:11:  - Session Outbox Worker: durable session side-effect 投递
novaic-agent-runtime/main_novaic.py:12:  - Saga Outbox Worker: durable saga compensation effect 投递
novaic-agent-runtime/main_novaic.py:14:  - Scheduler Worker: 唯一的定时唤醒 sleeping agents 轮询者
novaic-agent-runtime/main_novaic.py:17:Worker 主要通过 Queue Service、Business、Cortex 和 LLM Factory 通信；Gateway
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
novaic-agent-runtime/main_novaic.py:61:    novaic-backend scheduler [options]     Scheduler Worker (定时唤醒)
novaic-agent-runtime/main_novaic.py:65:    novaic-backend queue-service --host 127.0.0.1 --port 19997 --data-dir /Users/me/.novaic
novaic-agent-runtime/main_novaic.py:66:    novaic-backend gateway --host 127.0.0.1 --port 19999 --data-dir /Users/me/.novaic --queue-service-url http://127.0.0.1:19997 --vmcontrol-url http://127.0.0.1:19996 --blob-service-url http://127.0.0.1:19995
novaic-agent-runtime/main_novaic.py:67:    novaic-backend task-worker --queue-service-url http://127.0.0.1:19997 --num-workers 5 --data-dir /Users/me/.novaic
novaic-agent-runtime/main_novaic.py:80:    parser.add_argument("--queue-service-url", required=True, help="Queue Service URL")
novaic-agent-runtime/main_novaic.py:91:    ServiceConfig.QUEUE_SERVICE_URL = args.queue_service_url
novaic-agent-runtime/main_novaic.py:103:def run_queue_service():
novaic-agent-runtime/main_novaic.py:104:    """Run the Queue Service (Task/Saga queue management)."""
novaic-agent-runtime/main_novaic.py:107:    parser = argparse.ArgumentParser(description="NovAIC Queue Service")
novaic-agent-runtime/main_novaic.py:108:    parser.add_argument("--host", required=True, help="Queue Service host")
novaic-agent-runtime/main_novaic.py:109:    parser.add_argument("--port", required=True, type=int, help="Queue Service port")
novaic-agent-runtime/main_novaic.py:114:    ServiceConfig.QUEUE_SERVICE_HOST = args.host
novaic-agent-runtime/main_novaic.py:115:    ServiceConfig.QUEUE_SERVICE_PORT = args.port
novaic-agent-runtime/main_novaic.py:116:    ServiceConfig.QUEUE_SERVICE_URL = f"http://{args.host}:{args.port}"
novaic-agent-runtime/main_novaic.py:118:    from queue_service.main import app
novaic-agent-runtime/main_novaic.py:121:    print(f"[Queue Service] Starting on {args.host}:{args.port}")
novaic-agent-runtime/main_novaic.py:339:    elif mode == "queue-service":
novaic-agent-runtime/main_novaic.py:340:        run_queue_service()
novaic-agent-runtime/queue_service/task_ledger.py:13:from queue_service.fsm.runner import FsmTransitionRecord, FsmTransitionRunner
novaic-agent-runtime/queue_service/task_ledger.py:14:from queue_service.fsm.sqlite_store import FsmSqliteStore, FsmSqliteStoreConfig
scripts/start.sh:15:#   - Queue Service  :19997  Task/Saga queue management
scripts/start.sh:45:PORT_QUEUE_SERVICE=19997
scripts/start.sh:56:QS_URL="http://$HOST:$PORT_QUEUE_SERVICE"
scripts/start.sh:140:    for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
scripts/start.sh:151:for port in $PORT_ENTANGLED $PORT_GATEWAY $PORT_BUSINESS $PORT_DEVICE $PORT_QUEUE_SERVICE $PORT_BLOB_SERVICE $PORT_SANDBOXD $PORT_CORTEX; do
scripts/start.sh:194:    --queue-service-url "$QS_URL" --blob-service-url "$BLOB_URL" \
scripts/start.sh:212:$(py novaic-agent-runtime) "$BASE/novaic-agent-runtime/main_novaic.py" queue-service \
scripts/start.sh:213:    --host "$HOST" --port "$PORT_QUEUE_SERVICE" --data-dir "$DATA_DIR" \
scripts/start.sh:214:    >> "$LOG_DIR/queue-service.log" 2>&1 &
scripts/start.sh:215:wait_port "$PORT_QUEUE_SERVICE" "Queue Service"
scripts/start.sh:265:TASK_WORKER_ARGS="--business-url $BIZ_URL --queue-service-url $QS_URL --cortex-url $CORTEX_URL --data-dir $DATA_DIR"
scripts/start.sh:266:SAGA_WORKER_ARGS="--queue-service-url $QS_URL --cortex-url $CORTEX_URL --data-dir $DATA_DIR"
scripts/start.sh:267:SCHEDULER_ARGS="--business-url $BIZ_URL --queue-service-url $QS_URL --cortex-url $CORTEX_URL --data-dir $DATA_DIR"
novaic-agent-runtime/queue_service/dependencies.py:1:"""Explicit dependency bundle for Queue Service domain objects."""
novaic-agent-runtime/queue_service/dependencies.py:19:    session_outbox_id_provider: Callable[[], str]
novaic-agent-runtime/queue_service/dependencies.py:29:            session_outbox_id_provider=lambda: f"seff-{uuid.uuid4().hex[:12]}",
novaic-agent-runtime/tests/test_pr334_worker_process_runner.py:75:    assert main_novaic.run_worker_mode_if_registered("task-worker", ["--help"]) is True
novaic-agent-runtime/tests/test_pr334_worker_process_runner.py:76:    assert calls == [(registry, "task-worker", ["--help"], deps)]
novaic-agent-runtime/queue_service/session_ledger.py:13:from queue_service.fsm.runner import (
novaic-agent-runtime/queue_service/session_ledger.py:18:from queue_service.fsm.sqlite_store import FsmSqliteStore, FsmSqliteStoreConfig
novaic-agent-runtime/queue_service/session_ledger.py:19:from queue_service.session_events import (
novaic-agent-runtime/queue_service/session_ledger.py:24:from queue_service.session_fsm import SessionRuntimeStatus
novaic-agent-runtime/queue_service/session_ledger.py:25:from queue_service.session_projection import build_pending_input_projection
novaic-agent-runtime/queue_service/session_ledger.py:31:    outbox_table="tq_session_outbox",
novaic-agent-runtime/queue_service/session_ledger.py:162:            raise ValueError(f"unsupported initial session outbox status: {status}")
novaic-agent-runtime/tests/test_pr325_worker_policies_and_metrics.py:7:from queue_service.worker import (
novaic-agent-runtime/queue_service/session_fsm.py:15:from queue_service.fsm import FsmDecision, FsmEvent, FsmStateSnapshot, decide_transition
novaic-agent-runtime/queue_service/saga_repo.py:2:Saga repository/orchestrator (Queue Service DB implementation).
novaic-agent-runtime/queue_service/saga_repo.py:13:from queue_service.session_events import SessionEventType
novaic-agent-runtime/queue_service/saga_repo.py:14:from queue_service.session_ledger import SessionLedgerRepository
novaic-agent-runtime/queue_service/saga_repo.py:15:from queue_service.lease_fsm import (
novaic-agent-runtime/queue_service/saga_repo.py:24:from queue_service.lease_ledger import (
novaic-agent-runtime/queue_service/saga_repo.py:29:from queue_service.fsm.runner import FsmOutboxRecord
novaic-agent-runtime/queue_service/saga_repo.py:30:from queue_service.saga_fsm import (
novaic-agent-runtime/queue_service/saga_repo.py:37:from queue_service.saga_ledger import SagaLedgerRepository, SagaStateRecord
novaic-agent-runtime/queue_service/saga_repo.py:61:    Saga 仓库 - Queue Service 端
novaic-agent-runtime/queue_service/saga_repo.py:92:            outbox_id_provider=_missing_saga_outbox_id,
novaic-agent-runtime/queue_service/saga_repo.py:390:        Saga Worker 建完 DAG 后调用：设置 status=launched，释放 claim。
novaic-agent-runtime/queue_service/saga_repo.py:1149:    Saga lifecycle coordinator for queue-service-owned failure handling.
novaic-agent-runtime/queue_service/saga_repo.py:1176:            outbox_id_provider=_missing_session_outbox_id,
novaic-agent-runtime/queue_service/saga_repo.py:1181:        """Mark failed and persist compensation intent as saga outbox effects.
novaic-agent-runtime/queue_service/saga_repo.py:1224:        """Publish committed saga outbox effects through boundary adapters."""
novaic-agent-runtime/queue_service/saga_repo.py:1238:                self._publish_saga_outbox_effect(effect)
novaic-agent-runtime/queue_service/saga_repo.py:1251:                    "[SagaOrchestrator] saga outbox effect failed: id=%s type=%s error=%s",
novaic-agent-runtime/queue_service/saga_repo.py:1264:    def _publish_saga_outbox_effect(self, effect: dict[str, Any]) -> None:
novaic-agent-runtime/queue_service/saga_repo.py:1277:        raise ValueError(f"unsupported saga outbox effect_type: {effect_type}")
novaic-agent-runtime/queue_service/saga_repo.py:1408:def _missing_saga_outbox_id() -> str:
novaic-agent-runtime/queue_service/saga_repo.py:1421:    raise RuntimeError("SagaOrchestrator saga outbox publisher must pass session event ids")
novaic-agent-runtime/queue_service/saga_repo.py:1424:def _missing_session_outbox_id() -> str:
novaic-agent-runtime/queue_service/saga_repo.py:1425:    raise RuntimeError("SagaOrchestrator saga outbox publisher must pass session outbox ids")
novaic-agent-runtime/queue_service/lease_ledger.py:1:"""Worker lease ledger adapter for Queue Service.
novaic-agent-runtime/queue_service/lease_ledger.py:13:from queue_service.fsm.sqlite_store import FsmSqliteStore, FsmSqliteStoreConfig
novaic-agent-runtime/tests/test_pr276_session_repository_required_ledger.py:5:    source = Path("queue_service/session_repo.py").read_text(encoding="utf-8")
novaic-agent-runtime/queue_service/saga_ledger.py:14:from queue_service.fsm.runner import (
novaic-agent-runtime/queue_service/saga_ledger.py:19:from queue_service.fsm.sqlite_store import FsmSqliteStore, FsmSqliteStoreConfig
novaic-agent-runtime/queue_service/saga_ledger.py:25:    outbox_table="tq_saga_outbox",
novaic-agent-runtime/queue_service/saga_ledger.py:135:            raise ValueError(f"unsupported initial saga outbox status: {status}")
novaic-agent-runtime/queue_service/__init__.py:2:Queue Service - 独立的任务队列服务
novaic-agent-runtime/queue_service/session_outbox.py:1:"""Durable session outbox dispatcher."""
novaic-agent-runtime/queue_service/session_outbox.py:15:from queue_service.session_ledger import SessionLedgerRepository
novaic-agent-runtime/queue_service/session_outbox.py:16:from queue_service.session_observed_events import SessionObservedEventHandler
novaic-agent-runtime/queue_service/session_outbox.py:101:            raise KeyError(f"session outbox row not found: {outbox_id}")
novaic-agent-runtime/queue_service/session_outbox.py:146:        raise ValueError(f"unsupported session outbox effect_type: {effect_type}")
novaic-agent-runtime/queue_service/session_outbox.py:154:            "create_wake_saga outbox payload requires scope_id",
novaic-agent-runtime/queue_service/session_outbox.py:159:            "create_wake_saga outbox payload requires session_key",
novaic-agent-runtime/queue_service/session_outbox.py:164:            "create_wake_saga outbox payload requires agent_id",
novaic-agent-runtime/queue_service/session_outbox.py:169:            "create_wake_saga outbox payload requires subagent_id",
novaic-agent-runtime/queue_service/session_outbox.py:174:            "create_wake_saga outbox payload requires saga_idempotency_key",
novaic-agent-runtime/queue_service/session_outbox.py:179:            "create_wake_saga outbox payload requires saga_type",
novaic-agent-runtime/queue_service/session_outbox.py:183:            surface="session outbox create_wake_saga",
novaic-agent-runtime/queue_service/session_outbox_worker.py:1:"""Session outbox handler for the generic worker substrate."""
novaic-agent-runtime/queue_service/session_outbox_worker.py:8:from queue_service.session_outbox import SessionOutboxDispatcher
novaic-agent-runtime/queue_service/session_outbox_worker.py:9:from queue_service.worker import (
novaic-agent-runtime/queue_service/session_outbox_worker.py:18:SESSION_OUTBOX_DRAIN_JOB = WorkerJobSpec(kind="session_outbox_drain")
novaic-agent-runtime/queue_service/session_outbox_worker.py:28:            raise ValueError("session outbox worker batch_size must be positive")
novaic-agent-runtime/queue_service/session_outbox_worker.py:32:    """Drain durable session outbox rows through an explicit dispatcher port."""
novaic-agent-runtime/queue_service/session_outbox_worker.py:45:            decode_worker_job(job, (SESSION_OUTBOX_DRAIN_JOB,))
novaic-agent-runtime/queue_service/session_outbox_worker.py:50:            return WorkerResult.success(result, reason="session_outbox_drained")
novaic-agent-runtime/queue_service/session_outbox_worker.py:51:        return WorkerResult.noop(result, reason="session_outbox_empty")
novaic-agent-runtime/queue_service/session_rebuild.py:8:from queue_service.session_ledger import SessionLedgerRepository
novaic-agent-runtime/tests/test_pr269_session_pending_projection_ledger_boundary.py:8:from queue_service.db.schema import init_schema
novaic-agent-runtime/tests/test_pr269_session_pending_projection_ledger_boundary.py:9:from queue_service.session_ledger import (
novaic-agent-runtime/tests/test_pr269_session_pending_projection_ledger_boundary.py:143:    source = Path("queue_service/session_repo.py").read_text(encoding="utf-8")
novaic-agent-runtime/tests/test_pr241_pending_inbox_projection.py:6:from queue_service.db.schema import init_schema
novaic-agent-runtime/tests/test_pr241_pending_inbox_projection.py:7:from queue_service.queue_db import TaskQueue
novaic-agent-runtime/tests/test_pr241_pending_inbox_projection.py:8:from queue_service.saga_repo import SagaOrchestrator
novaic-agent-runtime/tests/test_pr241_pending_inbox_projection.py:9:from queue_service.session_ledger import SessionLedgerRepository
novaic-agent-runtime/tests/test_pr241_pending_inbox_projection.py:10:from queue_service.session_outbox import SessionOutboxDispatcher
novaic-agent-runtime/tests/test_pr241_pending_inbox_projection.py:11:from queue_service.session_repo import SessionRepository
novaic-agent-runtime/tests/test_pr281_session_outbox_wrapper_boundary.py:5:    source = Path("queue_service/session_repo.py").read_text(encoding="utf-8")
novaic-agent-runtime/tests/test_pr281_session_outbox_wrapper_boundary.py:7:    assert "_append_session_outbox_after_transaction" not in source
novaic-agent-runtime/tests/test_pr281_session_outbox_wrapper_boundary.py:8:    assert "_publish_session_outbox_effect" not in source
novaic-agent-runtime/tests/test_pr281_session_outbox_wrapper_boundary.py:25:def test_session_outbox_dispatcher_has_no_unused_wake_sync_wrappers():
novaic-agent-runtime/tests/test_pr281_session_outbox_wrapper_boundary.py:26:    source = Path("queue_service/session_outbox.py").read_text(encoding="utf-8")
novaic-agent-runtime/queue_service/main.py:2:Queue Service - 独立的任务队列服务
novaic-agent-runtime/queue_service/main.py:18:# 添加父目录到 Python 路径（确保可以导入 common 和 queue_service）
novaic-agent-runtime/queue_service/main.py:26:    print("[Queue Service] ERROR: paths.data_dir is required in config/services.json")
novaic-agent-runtime/queue_service/main.py:28:print(f"[Queue Service] Data directory (strict config): {NOVAIC_DATA_DIR}")
novaic-agent-runtime/queue_service/main.py:34:LOG_FILE = os.path.join(LOG_DIR, f"queue-service-{datetime.utcnow().strftime('%Y%m%d')}.log")
novaic-agent-runtime/queue_service/main.py:37:# so ``rg scope_id=$SID queue-service*.log`` works cross-service.
novaic-agent-runtime/queue_service/main.py:46:logger.info("Queue Service Starting")
