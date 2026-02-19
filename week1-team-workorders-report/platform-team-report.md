# Week 1 Work Report - Platform Team

## Team
Platform Team

## Date
2026-02-19

## Mission Alignment
本次执行聚焦 `week1-team-workorders/platform-team.md` 定义的 Week 1 基建目标，优先完成可跨仓复用的“统一底座”四件套：
- installable shared kernel 包骨架
- contracts 基线目录与初始文件
- compatibility matrix
- 可复用 CI 模板与 CI 消费接入

## Completed Work

### 1) Shared Kernel Bootstrap (D1 + D2 baseline)
- 新建 `novaic-shared-kernel` 作为可安装 Python 包入口：
  - `novaic-shared-kernel/pyproject.toml`
  - `novaic-shared-kernel/src/common/__init__.py`
  - `novaic-shared-kernel/README.md`
  - `novaic-shared-kernel/MIGRATION.md`
- 当前版本标记：`0.1.0rc1`（Week 1 bootstrap）
- 设计说明：保留 `from common...` 既有导入路径，先通过包层 bridge 兼容现状，避免影响并行开发

### 2) Contracts Baseline Skeleton (D3)
- 新建 `contracts/` 基线目录并落地首批合同文件：
  - `contracts/README.md`
  - `contracts/openapi/gateway-public.v1.yaml`
  - `contracts/openapi/runtime-orchestrator-internal.v1.yaml`
  - `contracts/schema/task-message.v1.schema.json`
  - `contracts/schema/subagent-status.v1.schema.json`
- 目标：先固定目录结构、版本命名和最小可验证内容，为后续 API/Runtime 团队迭代提供统一基线

### 3) Compatibility Matrix Delivery (D4 baseline)
- 新增顶层 `compatibility.yaml`，包含：
  - 统一 runtime/toolchain 约束（Python/Node/Rust）
  - 至少 5 个 repo 的矩阵条目
  - 与 CI template / contract set 的映射

### 4) Reusable CI Templates + CI Consumption (D4)
- 新增可复用模板目录 `.github/ci-templates/`：
  - `python-service.yml`
  - `rust-service.yml`
  - `frontend-app.yml`
  - `README.md`（模板接入说明）
- 更新 `.github/workflows/ci.yml`：
  - 新增 `compatibility-matrix` job
  - 将其纳入 `ci-success` 汇总 gate
  - 校验 `compatibility.yaml` 存在、repo 条目数、模板完整性

### 5) Compliance Artifact
- 输出 Platform Team 本轮合规文档：
  - `week1-team-workorders/platform-team-week1-compliance-report.md`

## Tests and Verification
- Shared kernel bridge 导入 smoke test：
  - 验证 `common` 与 `common.config.ServiceConfig` 可被包路径成功导入
  - 结果：通过
- Lint/诊断检查：
  - 新增与修改的关键文件（CI/pyproject/yaml/python）无新增 lints

## Acceptance Criteria Mapping
- `novaic-shared-kernel` 可安装：**已完成（bootstrap）**
- `compatibility.yaml` 存在并在 CI 消费：**已完成（当前仓）**
- CI templates 发布：**已完成**
- 消除所有相对共享代码依赖：**进行中（Week 1 采用 bridge，Week 2 去桥接）**

## Risks / Gaps
- “至少 6 个 repo 采用模板、至少 5 个 repo 在 CI 实际消费 matrix”仍需跨仓提 PR 才能闭环
- shared-kernel 目前为迁移过渡形态，`common` 实体代码尚未完全搬入包内

## Next Steps
- 执行 D2 深化：将 `novaic-backend/common` 实体迁入 `novaic-shared-kernel/src/common`
- 在各 repo 发起模板接入/矩阵校验 PR，补齐 adoption 指标
- 增加 shared-kernel 发布流水线（构建、版本、发布、回滚策略）
