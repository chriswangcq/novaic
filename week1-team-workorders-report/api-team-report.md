# Week 1 Work Report - API Team

## Team
API Team

## Date
2026-02-19

## Mission Alignment
本次围绕 Week 1 工单目标，聚焦 `gateway` 作为 public API owner 的稳定性与独立性，完成了两条主线：
- 恢复对外行为兼容（避免已有调用方回归）
- 消除跨服务源码级依赖（向独立 repo/客户端边界收敛）

## Completed Work

### 1) Gateway Public Behavior Compatibility Fixes (D3 + D4)
- 修复 `novaic-backend/gateway/clients/vmuse_adapter.py` 的返回契约与错误语义漂移：
  - 恢复关键工具返回中的 `result` 字段（同时保留 `content`，兼容新旧消费者）
  - `shell_exec` 成功语义恢复为 `exit_code == 0`
  - 错误文案统一恢复 `HTTP error` / `Adapter error` 前缀
  - 移除 `shell_exec` 的命令注入改写（不再强制追加 `DISPLAY=:0`）
  - `screenshot` 返回补齐 `result.format/width/height/image_data`
- 目标：保持 Week 1 baseline 下核心调用链对外行为稳定，避免已有测试和调用方破坏性变化

### 2) Remove Cross-Repo Source Imports in Gateway (D2 + D3)
- 清理 `gateway` 中对 `task_queue` / `runtime_orchestrator` 的源码级 import：
  - `novaic-backend/gateway/api/internal/llm.py`
  - `novaic-backend/gateway/api/internal/message.py`
  - `novaic-backend/gateway/api/skills.py`
  - `novaic-backend/gateway/api/internal/runtime_orchestrator.py`
- 新增 gateway 本地能力模块，替代原有跨模块依赖：
  - `novaic-backend/gateway/core/message_context.py`
  - `novaic-backend/gateway/core/prompt_builder.py`
- 目标：将 `gateway` 的内部实现收敛到网关本域代码和 API 边界，符合独立构建方向

### 3) Internal Compatibility Wiring Hardening (D4)
- `gateway/api/internal/runtime_orchestrator.py` 从“直接导入 runtime_orchestrator router”调整为 gateway 内部兼容导出，避免进程级源码耦合
- 保持兼容入口存在，避免迁移期间老引用路径失效

## Tests and Verification
- Gateway 相关回归测试执行：
  - `pytest tests/unit/gateway tests/unit/task_queue/test_gateway_api.py tests/unit/task_queue/test_gateway_internal_client_routing.py tests/contract/test_internal_api_contract_baseline.py tests/unit/gateway/test_public_api_runtime_orchestrator_forwarding.py -q`
  - 结果：`70 passed`
- 跨模块源码依赖扫描（`gateway/**/*.py`）：
  - 无 `from task_queue...` / `from runtime_orchestrator...` / `from tools_server...` 的有效代码引用残留
- 代码静态检查：
  - 本轮改动文件无新增 lints

## Impact Assessment
- **稳定性**：修复适配层行为漂移后，网关对外工具调用契约恢复，降低集成侧回归风险
- **独立性**：清理源码级跨服务 import，网关边界更清晰，向独立仓/独立构建演进
- **可维护性**：把通用预处理与 prompt 构建能力落到 gateway 本地模块，后续变更路径更可控

## Risks / Gaps
- 当前 `gateway/core/prompt_builder.py` 为网关本地实现，与 runtime 侧 builder 仍存在并行实现风险，后续需通过 shared-kernel/contract 对齐
- 本次验证覆盖了 unit/contract 基线，尚未包含完整多进程端到端联调场景
- Week 1 交付中 `environment variable spec` 与 `API surface inventory` 文档仍需补齐到目标位置

## Next Steps
- 输出并落地 `gateway` 环境变量/下游 URL 配置规范文档（Week 1 deliverable）
- 生成 API surface inventory（按对外稳定性 owner 视角标注 stable/compat/deprecated）
- 增加一轮 gateway 独立启动 smoke 测试脚本，验证“无跨仓源码依赖”前提下的启动与核心路由可用性
