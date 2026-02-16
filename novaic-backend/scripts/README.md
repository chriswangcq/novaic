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
