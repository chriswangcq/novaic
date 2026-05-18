# Queue service worker and FSM role map

## Entrypoint Evidence

- API/process entrypoint: `novaic-agent-runtime/queue_service/main.py` (FastAPI app, health endpoint, CLI main guard).
- Session state/FSM repository: `novaic-agent-runtime/queue_service/session_repo.py`.
- Worker coordination evidence is in queue_service modules and launch scripts; detailed keyword evidence saved in `queue-service-keywords.txt`.

## Source File Inventory

- `novaic-agent-runtime/queue_service/routes.py`
- `novaic-agent-runtime/queue_service/dependencies.py`
- `novaic-agent-runtime/queue_service/session_audit.py`
- `novaic-agent-runtime/queue_service/session_outbox.py`
- `novaic-agent-runtime/queue_service/main.py`
- `novaic-agent-runtime/queue_service/worker/policies.py`
- `novaic-agent-runtime/queue_service/worker/concurrent_worker.py`
- `novaic-agent-runtime/queue_service/worker/reporters.py`
- `novaic-agent-runtime/queue_service/worker/contracts.py`
- `novaic-agent-runtime/queue_service/worker/sources.py`
- `novaic-agent-runtime/queue_service/worker/__init__.py`
- `novaic-agent-runtime/queue_service/worker/effects.py`
- `novaic-agent-runtime/queue_service/worker/generic_worker.py`
- `novaic-agent-runtime/queue_service/saga_outbox_worker.py`
- `novaic-agent-runtime/queue_service/task_fsm.py`
- `novaic-agent-runtime/queue_service/queue_audit.py`
- `novaic-agent-runtime/queue_service/exceptions.py`
- `novaic-agent-runtime/queue_service/saga_fsm.py`
- `novaic-agent-runtime/queue_service/db/schema.py`
- `novaic-agent-runtime/queue_service/db/__init__.py`
- `novaic-agent-runtime/queue_service/queue_db.py`
- `novaic-agent-runtime/queue_service/session_recovery.py`
- `novaic-agent-runtime/queue_service/session_effects.py`
- `novaic-agent-runtime/queue_service/session_wake_plan.py`
- `novaic-agent-runtime/queue_service/fsm/sqlite_store.py`
- `novaic-agent-runtime/queue_service/fsm/core.py`
- `novaic-agent-runtime/queue_service/fsm/__init__.py`
- `novaic-agent-runtime/queue_service/fsm/runner.py`
- `novaic-agent-runtime/queue_service/session_events.py`
- `novaic-agent-runtime/queue_service/session_observed_events.py`
- `novaic-agent-runtime/queue_service/saga_repo.py`
- `novaic-agent-runtime/queue_service/__init__.py`
- `novaic-agent-runtime/queue_service/session_rebuild.py`
- `novaic-agent-runtime/queue_service/lease_fsm.py`
- `novaic-agent-runtime/queue_service/session_ledger.py`
- `novaic-agent-runtime/queue_service/lease_ledger.py`
- `novaic-agent-runtime/queue_service/session_outbox_worker.py`
- `novaic-agent-runtime/queue_service/session_repo.py`
- `novaic-agent-runtime/queue_service/task_ledger.py`
- `novaic-agent-runtime/queue_service/session_fsm.py`
- `novaic-agent-runtime/queue_service/saga_ledger.py`
- `novaic-agent-runtime/queue_service/session_projection.py`

## Role Boundary Draft

- Queue service API: accepts dispatch/session/finalize style requests and stores durable session/queue state.
- FSM/session coordination: pure-ish session decision layer plus repository state; owns active/session generation decisions.
- Durable worker infrastructure: task/saga/outbox/scheduler workers are queue-service execution roles around durable records, not separate business services.
- Health: exposed via queue service app/health path and related config.

## Evidence Samples

novaic-agent-runtime/queue_service/routes.py:4:暴露 TaskQueue 和 Saga 的 HTTP API，供 Worker 进程调用。
novaic-agent-runtime/queue_service/routes.py:5:队列数据库集中在 Queue Service 进程，Worker 只能通过本 API 访问。
novaic-agent-runtime/queue_service/routes.py:11:from fastapi import APIRouter, HTTPException, Depends, Request
novaic-agent-runtime/queue_service/routes.py:15:from queue_service.saga_repo import SagaRepository, SagaOrchestrator
novaic-agent-runtime/queue_service/routes.py:16:from queue_service.session_repo import SessionRepository
novaic-agent-runtime/queue_service/routes.py:17:from queue_service.exceptions import TaskNotFoundError, SagaError
novaic-agent-runtime/queue_service/routes.py:19:from task_queue.saga_creation_policy import (
novaic-agent-runtime/queue_service/routes.py:20:    SagaCreationPolicyError,
novaic-agent-runtime/queue_service/routes.py:21:    reject_session_owned_saga_type,
novaic-agent-runtime/queue_service/routes.py:45:def _recover_sagas_or_defer(
novaic-agent-runtime/queue_service/routes.py:46:    orchestrator: "SagaOrchestrator",
novaic-agent-runtime/queue_service/routes.py:54:        logger.warning("saga_recovery_deferred reason=sqlite_busy")
novaic-agent-runtime/queue_service/routes.py:57:        logger.warning("saga_recovery_deferred reason=queue_busy")
novaic-agent-runtime/queue_service/routes.py:70:    saga_id: Optional[str] = None
novaic-agent-runtime/queue_service/routes.py:81:    worker_id: str
novaic-agent-runtime/queue_service/routes.py:110:class SagaCreateRequest(BaseModel):
novaic-agent-runtime/queue_service/routes.py:111:    saga_type: str
novaic-agent-runtime/queue_service/routes.py:116:class SagaCreateResponse(BaseModel):
novaic-agent-runtime/queue_service/routes.py:117:    saga_id: str
novaic-agent-runtime/queue_service/routes.py:120:class SagaClaimRequest(BaseModel):
novaic-agent-runtime/queue_service/routes.py:121:    saga_types: List[str]
novaic-agent-runtime/queue_service/routes.py:122:    worker_id: str
novaic-agent-runtime/queue_service/routes.py:125:class SagaClaimResponse(BaseModel):
novaic-agent-runtime/queue_service/routes.py:126:    saga: Optional[Dict[str, Any]] = None
novaic-agent-runtime/queue_service/routes.py:129:class SagaResponse(BaseModel):
novaic-agent-runtime/queue_service/routes.py:130:    saga: Optional[Dict[str, Any]] = None
novaic-agent-runtime/queue_service/routes.py:133:class SagaCompleteRequest(BaseModel):
novaic-agent-runtime/queue_service/routes.py:137:class SagaFailRequest(BaseModel):
novaic-agent-runtime/queue_service/routes.py:141:class SagaReleaseRequest(BaseModel):
novaic-agent-runtime/queue_service/routes.py:145:class SagaLaunchedRequest(BaseModel):
novaic-agent-runtime/queue_service/routes.py:186:    orchestrator: Optional[SagaOrchestrator] = None,
novaic-agent-runtime/queue_service/routes.py:187:) -> APIRouter:
novaic-agent-runtime/queue_service/routes.py:193:        orchestrator: SagaOrchestrator 实例（可选）
novaic-agent-runtime/queue_service/routes.py:196:        router: FastAPI Router
novaic-agent-runtime/queue_service/routes.py:201:        orchestrator = SagaOrchestrator(
novaic-agent-runtime/queue_service/routes.py:205:            saga_id_provider=deps.saga_id_provider,
novaic-agent-runtime/queue_service/routes.py:210:    router = APIRouter(tags=["Task Queue"])
novaic-agent-runtime/queue_service/routes.py:224:            saga_id=req.saga_id,
novaic-agent-runtime/queue_service/routes.py:238:                worker_id=req.worker_id,
novaic-agent-runtime/queue_service/routes.py:243:            logger.warning("task_claim_deferred worker=%s reason=sqlite_busy", req.worker_id)
novaic-agent-runtime/queue_service/routes.py:246:            logger.warning("task_claim_deferred worker=%s reason=queue_busy", req.worker_id)
novaic-agent-runtime/queue_service/routes.py:260:            if task.get("saga_id") and task.get("step_name") and orchestrator:
novaic-agent-runtime/queue_service/routes.py:262:                    task["saga_id"], task["step_name"], req.result or {}
novaic-agent-runtime/queue_service/routes.py:264:                orchestrator.check_saga_complete(task["saga_id"])
novaic-agent-runtime/queue_service/routes.py:278:        if task and task.get("saga_id") and final_status == "failed" and orchestrator:
novaic-agent-runtime/queue_service/routes.py:279:            orchestrator.mark_failed(task["saga_id"], req.error)
novaic-agent-runtime/queue_service/routes.py:356:        """获取所有已知的 topics (Task Worker 启动时调用)"""
novaic-agent-runtime/queue_service/routes.py:361:    # Saga APIs (if orchestrator provided)
novaic-agent-runtime/queue_service/routes.py:365:        @router.post("/sagas/create", response_model=SagaCreateResponse)
novaic-agent-runtime/queue_service/routes.py:366:        def create_saga(req: SagaCreateRequest):
novaic-agent-runtime/queue_service/routes.py:367:            """创建 Saga (立即返回，由 SagaWorker 执行)"""
novaic-agent-runtime/queue_service/routes.py:369:                reject_session_owned_saga_type(req.saga_type, surface="/api/queue/sagas/create")
novaic-agent-runtime/queue_service/routes.py:370:                saga_id = orchestrator.create(
novaic-agent-runtime/queue_service/routes.py:371:                    saga_type=req.saga_type,
novaic-agent-runtime/queue_service/routes.py:375:                return SagaCreateResponse(saga_id=saga_id)
novaic-agent-runtime/queue_service/routes.py:376:            except SagaCreationPolicyError as e:
novaic-agent-runtime/queue_service/routes.py:378:            except SagaError as e:
novaic-agent-runtime/queue_service/routes.py:381:        @router.post("/sagas/claim", response_model=SagaClaimResponse)
novaic-agent-runtime/queue_service/routes.py:382:        def claim_saga(req: SagaClaimRequest):
novaic-agent-runtime/queue_service/routes.py:383:            """认领 Saga (SagaWorker 调用)"""
novaic-agent-runtime/queue_service/routes.py:385:                saga = orchestrator.claim(
novaic-agent-runtime/queue_service/routes.py:386:                    saga_types=req.saga_types,
novaic-agent-runtime/queue_service/routes.py:387:                    worker_id=req.worker_id,
novaic-agent-runtime/queue_service/routes.py:392:                logger.warning("saga_claim_deferred worker=%s reason=sqlite_busy", req.worker_id)
novaic-agent-runtime/queue_service/routes.py:393:                saga = None
novaic-agent-runtime/queue_service/routes.py:395:                logger.warning("saga_claim_deferred worker=%s reason=queue_busy", req.worker_id)
novaic-agent-runtime/queue_service/routes.py:396:                saga = None
novaic-agent-runtime/queue_service/routes.py:397:            return SagaClaimResponse(saga=saga)
novaic-agent-runtime/queue_service/routes.py:399:        @router.get("/sagas/{saga_id}", response_model=SagaResponse)
novaic-agent-runtime/queue_service/routes.py:400:        def get_saga(saga_id: str):
novaic-agent-runtime/queue_service/routes.py:401:            """获取 Saga 状态"""
novaic-agent-runtime/queue_service/routes.py:402:            saga = orchestrator.get(saga_id)
novaic-agent-runtime/queue_service/routes.py:403:            if not saga:
novaic-agent-runtime/queue_service/routes.py:404:                raise HTTPException(status_code=404, detail="Saga not found")
novaic-agent-runtime/queue_service/routes.py:405:            return SagaResponse(saga=saga)
novaic-agent-runtime/queue_service/routes.py:407:        @router.post("/sagas/{saga_id}/heartbeat", response_model=SuccessResponse)
novaic-agent-runtime/queue_service/routes.py:408:        def heartbeat_saga(saga_id: str):
novaic-agent-runtime/queue_service/routes.py:409:            """更新 Saga 心跳 (SagaWorker 调用)"""
novaic-agent-runtime/queue_service/routes.py:410:            success = orchestrator.heartbeat(saga_id)
novaic-agent-runtime/queue_service/routes.py:413:        @router.post("/sagas/{saga_id}/launched", response_model=SuccessResponse)
novaic-agent-runtime/queue_service/routes.py:414:        def mark_saga_launched(saga_id: str, req: SagaLaunchedRequest):
novaic-agent-runtime/queue_service/routes.py:415:            """Saga Worker 建完 DAG 后调用，标记 launched 并释放 claim"""
novaic-agent-runtime/queue_service/routes.py:416:            success = orchestrator.mark_launched(saga_id, req.dag_task_count)
novaic-agent-runtime/queue_service/routes.py:419:        @router.post("/sagas/{saga_id}/complete", response_model=SuccessResponse)
novaic-agent-runtime/queue_service/routes.py:420:        def complete_saga(saga_id: str, req: SagaCompleteRequest):
novaic-agent-runtime/queue_service/routes.py:421:            """标记 Saga 完成 (Saga Worker 调用)"""
novaic-agent-runtime/queue_service/routes.py:422:            orchestrator.mark_completed(saga_id, req.step_results)
novaic-agent-runtime/queue_service/routes.py:425:        @router.post("/sagas/{saga_id}/fail", response_model=SuccessResponse)
novaic-agent-runtime/queue_service/routes.py:426:        def fail_saga(saga_id: str, req: SagaFailRequest):
novaic-agent-runtime/queue_service/routes.py:427:            """标记 Saga 失败 (Saga Worker 调用)"""
novaic-agent-runtime/queue_service/routes.py:428:            orchestrator.mark_failed(saga_id, req.error)
novaic-agent-runtime/queue_service/routes.py:439:# execution 在 Runtime Worker 内部执行，产品 mutation 经 Business。
novaic-agent-runtime/queue_service/routes.py:448:# Queue Service 只接收已归一化的 dispatch / task / saga 请求。
novaic-agent-runtime/queue_service/routes.py:458:    sagas_recovered: int = 0
novaic-agent-runtime/queue_service/routes.py:463:    orchestrator: Optional[SagaOrchestrator] = None,
novaic-agent-runtime/queue_service/routes.py:464:) -> APIRouter:
novaic-agent-runtime/queue_service/routes.py:470:        orchestrator: SagaOrchestrator 实例（可选）
novaic-agent-runtime/queue_service/routes.py:473:        router: FastAPI Router
novaic-agent-runtime/queue_service/routes.py:475:    router = APIRouter(tags=["Task Queue Recovery"])
novaic-agent-runtime/queue_service/routes.py:484:        @router.post("/sagas", response_model=RecoveryResponse)
novaic-agent-runtime/queue_service/routes.py:485:        def recover_stale_sagas(timeout_seconds: int = 120):
novaic-agent-runtime/queue_service/routes.py:486:            """恢复超时 Saga"""
novaic-agent-runtime/queue_service/routes.py:487:            recovered = _recover_sagas_or_defer(orchestrator, timeout_seconds)
novaic-agent-runtime/queue_service/routes.py:488:            return RecoveryResponse(sagas_recovered=recovered)
novaic-agent-runtime/queue_service/routes.py:493:        saga_timeout: int = 600,
novaic-agent-runtime/queue_service/routes.py:495:        """恢复所有超时任务和 Saga"""
novaic-agent-runtime/queue_service/routes.py:497:        sagas_recovered = 0
novaic-agent-runtime/queue_service/routes.py:499:            sagas_recovered = _recover_sagas_or_defer(orchestrator, saga_timeout)
novaic-agent-runtime/queue_service/routes.py:502:            sagas_recovered=sagas_recovered,
novaic-agent-runtime/queue_service/routes.py:508:        取消所有 pending/running 的任务和 Saga
novaic-agent-runtime/queue_service/routes.py:513:            agent_id: 可选，只取消指定 agent 的任务/sagas
novaic-agent-runtime/queue_service/routes.py:517:            cancelled_sagas: 取消的 saga 数
novaic-agent-runtime/queue_service/routes.py:520:        cancelled_sagas = 0
novaic-agent-runtime/queue_service/routes.py:522:            cancelled_sagas = orchestrator.cancel_all(agent_id)
novaic-agent-runtime/queue_service/routes.py:525:            "cancelled_sagas": cancelled_sagas,
novaic-agent-runtime/queue_service/routes.py:532:# Session Coordinator Router
novaic-agent-runtime/queue_service/routes.py:543:class SessionEndedRequest(BaseModel):
novaic-agent-runtime/queue_service/routes.py:547:    finalize_reason: str
novaic-agent-runtime/queue_service/routes.py:553:    session_repo: SessionRepository,
novaic-agent-runtime/queue_service/routes.py:554:) -> APIRouter:
