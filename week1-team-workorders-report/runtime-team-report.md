# Week 1 Work Report - Runtime Team

## Team
Runtime Team

## Date
2026-02-19

## Mission Alignment
本周围绕 Runtime Team 工单目标，聚焦 runtime 生命周期编排的独立可运行与状态一致性，完成了三项核心落地：
- 明确生命周期状态模型与转换约束
- 补齐重复生命周期操作的幂等性基线验证
- 强化状态查询的确定性（deterministic behavior）

## Completed Work

### 1) Lifecycle State Model Document (D2)
- 新增文档：`novaic-backend/runtime_orchestrator/LIFECYCLE_STATE_MODEL.md`
- 明确 runtime 状态集合与转换规则：
  - `active -> completed`
  - `active -> failed`
  - `completed -> active`（wake/reopen）
- 明确禁止转换（如 `failed -> completed`）与重试语义（CAS/幂等）
- 覆盖工单要求中的“生命周期一致性规则”交付物

### 2) Deterministic State Query Hardening (D3)
- 修改：`novaic-backend/runtime_orchestrator/db/repositories/runtime.py`
- `get_all_active_runtimes()` 排序从单字段 `created_at` 改为稳定排序：
  - `ORDER BY created_at ASC, runtime_id ASC`
- 目标：避免同时间戳场景下返回顺序抖动，提升状态查询 API 的确定性

### 3) Runtime Lifecycle Consistency Baseline Tests (D2 + D3)
- 新增测试：`novaic-backend/tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
- 覆盖场景：
  - `get_or_create_active_runtime` 重复调用幂等（同 `(agent_id, subagent_id)` 返回同一 active runtime）
  - 重复 stop/CAS 状态转换不导致非法回退（`active -> completed` 后重复请求保持 `completed`）
  - 同时间戳 active runtime 列表返回顺序稳定

## Tests and Verification
- 本轮新增测试执行：
  - `pytest -q tests/unit/runtime_orchestrator/test_runtime_lifecycle_consistency.py`
  - 结果：`3 passed`
- 相关契约回归执行：
  - `pytest -q tests/contract/test_internal_api_contract_baseline.py`
  - 结果：通过
- 静态检查：
  - 本轮修改文件无新增 lints

## Acceptance Criteria Mapping
- Runtime service starts independently and passes health checks
  - 当前基线中仍存在 `test_runtime_orchestrator_process_startup.py` 健康探测失败，需继续排查（见 Risks）
- Repeated start/stop calls do not cause invalid states
  - 已通过新增生命周期一致性单测覆盖关键重试/重复操作场景
- State query APIs behave deterministically
  - 已通过稳定排序改造 + 对应测试验证
- CI passes on default branch
  - 本地仅完成本轮相关单测/契约回归，完整 CI 仍待统一流水线验证

## Risks / Gaps
- 进程级 startup contract（`tests/contract/test_runtime_orchestrator_process_startup.py`）在本地仍有健康探测超时失败，属于 P0 级稳定性风险候选
- 当前验证集中在 runtime 生命周期基线，尚未覆盖完整多进程链路下的大并发重复操作压测

## Next Steps
- 优先修复 Runtime Orchestrator 启动健康检查失败问题，确保“独立启动 + health check”达标
- 将 lifecycle contract 的关键转换规则补充到更完整的 contract 测试（含并发重试）
- 继续推进 D4/D5 交付：CI 联通、回归收敛、release note/lifecycle contract summary
