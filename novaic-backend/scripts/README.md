# Backend Scripts

此目录包含用于数据库维护、部署和测试的脚本。

## 迁移脚本

### migrate_agent_index_to_ports.py

将旧的 `agent_index` 字段转换为持久化的 `ports` 配置。

**何时使用**：在部署重构后的代码之前，运行此脚本一次。

**快速开始**：

```bash
# 1. 预览迁移计划（推荐首先运行）
python novaic-backend/scripts/migrate_agent_index_to_ports.py --dry-run

# 2. 执行迁移
python novaic-backend/scripts/migrate_agent_index_to_ports.py
```

更多参数请使用：

```bash
python novaic-backend/scripts/migrate_agent_index_to_ports.py --help
```

## 其他脚本

### deploy_playwright_helper.py

部署 Playwright 辅助工具到 VM。

### playwright_helper.py

Playwright 浏览器控制辅助工具。

### run_vmcontrol_dev.sh

在开发模式下运行 VMControl 服务。

### start_workers_sync.sh

启动同步模式的 Worker 进程。

### start_workers.sh

启动 Worker 进程。

### switch_to_sync.sh

切换到同步模式。

### test_vmcontrol.sh

测试 VMControl 服务。

### verify_subagent_id_fix.sql

验证 sub-agent ID 修复的 SQL 脚本。

### storage_ab_backup.sh

Storage-A/B 备份脚本（文件目录 + tool_results.db + manifest）。

### storage_ab_restore.sh

Storage-A/B 恢复脚本（从指定或最新备份恢复到目标目录）。

### storage_ab_validate_restore.sh

Storage-A/B 一键恢复演练脚本（构造样本、备份、破坏、恢复、校验并生成证据报告）。

### storage_ab_smoke.sh

Storage-A/B 健康与读写冒烟脚本（启动 file_service + tool_result_service 并产出证据报告）。

### storage_ab_contract_diff.sh

Storage-A/B 合同字段对齐脚本（启动服务、采样响应、输出 matched/missing/extra 矩阵证据）。
支持 `--schema-path` 指定合同文件（默认 `contracts/schema/storage-api.v1.schema.json`）。
默认写入 evergreen 证据文件：`contracts/evidence/storage-contract-diff-latest.md`。
可通过 `--report-path` 同时输出 round 报告证据文件（dual-write）。

### smoke_gateway_independent_startup.sh

Gateway 独立启动冒烟脚本（启动 runtime-orchestrator + gateway，执行健康检查并输出 PASS 结果）。

- 端口策略（稳定规则）：`ops-rounds/governance/gateway-smoke-port-strategy.md`
- CI 对应任务：`.github/workflows/ci.yml` 中 `gateway-smoke` job

### tools/runtime_concurrency_stress_replay.sh

Runtime 并发争抢回放脚本。循环执行并发生命周期一致性测试并输出可复现汇总：
- `runtime_stress_replay_rounds`
- `runtime_stress_replay_passed_rounds`
- `runtime_stress_replay_status`
