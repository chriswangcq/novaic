# Week 1 工作汇报 - Tools Team

## 团队
Tools Team

## 对应工作单
`week1-team-workorders/tools-team.md`

## 本周目标
围绕工具执行服务的可靠性，落地超时策略与隔离/清理机制，确保行为可预测、失败可恢复、资源不泄漏。

## 已完成工作

### 1) 可靠性策略模块（timeout + isolation）
- 新增 `novaic-backend/tools_server/reliability.py`。
- 定义统一策略对象 `ToolsReliabilityPolicy`，包含：
  - `request_timeout_seconds`（请求超时，默认 300s）
  - `execution_timeout_seconds`（执行超时，默认关闭）
  - `global_timeout_seconds`（全局上限，默认 1800s）
  - `max_concurrent_tools_per_runtime`（每 runtime 并发上限，默认 4）
- 支持通过 `NOVAIC_TOOLS_*` 环境变量覆盖。

### 2) Runtime 级隔离控制
- 在 `novaic-backend/tools_server/runtime_manager.py` 的 `RuntimeContext` 增加 `execution_semaphore`。
- Runtime 创建与恢复时都初始化 semaphore，实现每 runtime 并发隔离，避免单 runtime 抢占全部执行资源。

### 3) 执行超时与失败路径清理
- 在 `novaic-backend/tools_server/executor.py` 中：
  - `ToolExecutor.execute()` 增加执行超时控制（`asyncio.wait_for`）。
  - 超时后返回确定性错误信息，避免无限挂起。
  - 超时时主动关闭 HTTP 客户端连接，降低连接泄漏风险。
- 在 `novaic-backend/tools_server/api.py` 中：
  - `POST /internal/runtimes/{runtime_id}/tools/call` 增加请求超时控制。
  - 调用路径接入 runtime semaphore。
  - 统一通过 `finally` 执行 executor `close()`，覆盖成功/失败/超时路径。

### 4) 文档交付
- 新增 `novaic-backend/tools_server/RELIABILITY_POLICY.md`，沉淀 timeout 分层、隔离规则、cleanup 规则与推荐生产配置。

## 测试与验证
- 新增单测：
  - `novaic-backend/tests/unit/tools_server/test_reliability_policy.py`
  - `novaic-backend/tests/unit/tools_server/test_api_reliability_controls.py`
- 回归验证：
  - `novaic-backend/tests/unit/tools_server/test_executor_qemu_contract.py`
- 本地执行结果：`10 passed`
  - 命令：`pytest -q tests/unit/tools_server/test_reliability_policy.py tests/unit/tools_server/test_api_reliability_controls.py tests/unit/tools_server/test_executor_qemu_contract.py`

## 与工作单验收项对齐
- Service independently deployable and health-check: 本次聚焦可靠性内核，未阻断独立部署路径。
- Timeout deterministic and test-covered: 已落地策略与单测覆盖，行为可预测。
- Failed runs leave no leaked resource: 已在 timeout/cancel 路径执行 close 与清理。
- CI green: 已完成本地定向测试验证，待合入后走完整 CI。

## 风险与待办
- 当前策略参数基于环境变量，下一步建议纳入服务配置 schema，便于集中治理。
- 需要补充更完整的压力/并发场景测试报告（例如同 runtime 大量并发调用下的排队与超时行为）。
- Week1 后续需继续推进独立 CI 与 release 流水线，满足 `v0.1.0-rc1` 交付目标。
