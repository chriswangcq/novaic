# Agent Index → Ports Migration Guide

## 概述

此迁移将旧的 `agent_index` 字段转换为持久化的 `ports` 配置。

**背景**：在重构前，系统使用 `agent_index` 动态计算端口。重构后，端口配置持久化存储在数据库中，提供更好的可靠性和灵活性。

## 何时运行

在部署重构后的代码之前，运行此脚本**一次**。

## 数据目录

脚本默认使用 `~/.local/share/novaic-gateway` 作为数据目录。你可以通过以下方式指定不同的数据目录：

### 方式 1：命令行参数

```bash
python novaic-backend/scripts/migrate_agent_index_to_ports.py --data-dir /path/to/data
```

### 方式 2：环境变量

```bash
NOVAIC_DATA_DIR=/path/to/data python novaic-backend/scripts/migrate_agent_index_to_ports.py
```

### 方式 3：使用默认路径

如果不指定，脚本会自动使用 `~/.local/share/novaic-gateway`。

## 迁移步骤

### 1. 备份数据库（强烈推荐）

```bash
# SQLite 数据库默认位置
# macOS/Linux
cp ~/.local/share/novaic-gateway/novaic.db ~/.local/share/novaic-gateway/novaic.db.backup

# 或者备份整个数据目录
cp -r ~/.local/share/novaic-gateway ~/.local/share/novaic-gateway.backup
```

### 2. 停止所有服务

确保没有进程正在使用数据库：

```bash
# 停止 Gateway
pkill -f main_gateway

# 停止 Tools Server  
pkill -f main_novaic

# 停止 App（如果正在运行）
# 在 App 中选择退出
```

### 3. 预览迁移计划（Dry Run）

在实际修改数据库之前，先预览迁移计划：

```bash
cd /path/to/novaic

# 使用默认数据目录
python novaic-backend/scripts/migrate_agent_index_to_ports.py --dry-run

# 或者指定数据目录
python novaic-backend/scripts/migrate_agent_index_to_ports.py --dry-run --data-dir /path/to/data
```

**输出示例**：

```
============================================================
Agent Index → Ports Migration Script
============================================================
Data directory: /Users/username/.local/share/novaic-gateway

[DRY RUN MODE] - No changes will be made

Found 3 agents

✅ Already migrated: 1
⏳ Needs migration:  2

Migration Plan:
------------------------------------------------------------
  牛马一号 (ID: a1b2c3d4...)
    agent_index: 0
    → vm:       20000
    → session:  20001
    → local:    20002
    → memory:   20003
    → chat:     20004
    → qemudebug: 20005
    → vnc:      20006
    → websocket: 20007
    → ssh:      20008

  牛马二号 (ID: e5f6g7h8...)
    agent_index: 1
    → vm:       20020
    → session:  20021
    → local:    20022
    → memory:   20023
    → chat:     20024
    → qemudebug: 20025
    → vnc:      20026
    → websocket: 20027
    → ssh:      20028

[DRY RUN] Migration not executed. Remove --dry-run to apply changes.
```

**检查事项**：
- ✅ 端口分配是否正确？
- ✅ 所有需要迁移的 agent 都被识别了吗？
- ✅ 没有端口冲突吗？

### 4. 执行迁移

确认迁移计划无误后，执行实际迁移：

```bash
# 使用默认数据目录
python novaic-backend/scripts/migrate_agent_index_to_ports.py

# 或者指定数据目录
python novaic-backend/scripts/migrate_agent_index_to_ports.py --data-dir /path/to/data
```

**成功输出示例**：

```
============================================================
Agent Index → Ports Migration Script
============================================================
Data directory: /Users/username/.local/share/novaic-gateway

Found 3 agents

✅ Already migrated: 1
⏳ Needs migration:  2

Migration Plan:
------------------------------------------------------------
  牛马一号 (ID: a1b2c3d4...)
    agent_index: 0
    → vm:       20000
    → session:  20001
    → local:    20002
    → memory:   20003
    → chat:     20004
    → qemudebug: 20005
    → vnc:      20006
    → websocket: 20007
    → ssh:      20008

  牛马二号 (ID: e5f6g7h8...)
    agent_index: 1
    → vm:       20020
    → session:  20021
    → local:    20022
    → memory:   20023
    → chat:     20024
    → qemudebug: 20025
    → vnc:      20026
    → websocket: 20027
    → ssh:      20028

Executing migration...
------------------------------------------------------------
✅ Migrated: 牛马一号
✅ Migrated: 牛马二号

============================================================
Migration Complete
============================================================
✅ Successfully migrated: 2
```

### 5. 验证结果

检查迁移是否成功：

```bash
# 再次运行 dry-run，应该显示所有 agent 都已迁移
python novaic-backend/scripts/migrate_agent_index_to_ports.py --dry-run
```

**预期输出**：

```
============================================================
Agent Index → Ports Migration Script
============================================================

[DRY RUN MODE] - No changes will be made

Found 3 agents

✅ Already migrated: 3
⏳ Needs migration:  0

✅ All agents are already up to date!
```

### 6. 启动服务

现在可以安全地启动重构后的服务：

```bash
# 启动 Gateway
cd novaic-backend
python main_gateway.py

# 启动 Tools Server
python main_novaic.py
```

## 数据库变化

### 迁移前

```json
{
  "id": "abc123",
  "name": "牛马一号",
  "vm_config": {
    "agent_index": 0,
    "backend": "qemu",
    ...
  },
  "ports": {}
}
```

### 迁移后

```json
{
  "id": "abc123",
  "name": "牛马一号",
  "vm_config": {
    "backend": "qemu",
    ...
  },
  "ports": {
    "vm": 20000,
    "session": 20001,
    "local": 20002,
    "memory": 20003,
    "chat": 20004,
    "qemudebug": 20005,
    "vnc": 20006,
    "websocket": 20007,
    "ssh": 20008
  }
}
```

**变化**：
- ✅ `agent_index` 字段被删除
- ✅ `ports` 对象包含所有端口配置
- ✅ 端口值基于原 `agent_index` 计算得出

## 故障排查

### 问题：找不到模块

**错误**：
```
ModuleNotFoundError: No module named 'gateway'
```

**解决方案**：确保在项目根目录运行脚本：
```bash
cd /path/to/novaic
python novaic-backend/scripts/migrate_agent_index_to_ports.py
```

### 问题：数据库锁定

**错误**：
```
sqlite3.OperationalError: database is locked
```

**解决方案**：停止所有使用数据库的服务：
```bash
# 停止所有相关进程
pkill -f main_gateway
pkill -f main_novaic
pkill -f novaic-app

# 确认没有进程正在使用数据库
lsof ~/.local/share/novaic-gateway/novaic.db

# 然后重新运行迁移
python novaic-backend/scripts/migrate_agent_index_to_ports.py
```

### 问题：迁移部分失败

**错误**：
```
✅ Successfully migrated: 2
❌ Failed:               1
```

**解决方案**：
1. 查看错误详情（脚本会显示具体错误）
2. 如果是数据问题，手动检查数据库中失败的 agent
3. 修复问题后，可以再次运行迁移脚本（已迁移的 agent 会被跳过）

### 问题：端口冲突

**症状**：迁移后服务启动失败，提示端口被占用

**解决方案**：
1. 检查是否有其他进程占用了这些端口：
```bash
lsof -i :20000-20999
```
2. 如果有冲突，需要手动调整端口配置或停止冲突进程

## 回滚

如果迁移后发现问题，需要回滚到旧版本：

### 1. 停止新版本服务

```bash
pkill -f main_gateway
pkill -f main_novaic
```

### 2. 恢复数据库备份

```bash
cp ~/.local/share/novaic-gateway/novaic.db.backup ~/.local/share/novaic-gateway/novaic.db
```

### 3. 切换回旧版本代码

```bash
cd /path/to/novaic
git checkout <old-commit-hash>
```

### 4. 重新启动服务

```bash
cd novaic-backend
python main_gateway.py
```

## 常见问题

### Q: 迁移会影响正在运行的 VM 吗？

**A**：不会。迁移只修改数据库配置，不影响正在运行的 VM 进程。但为了避免数据库锁定，建议在迁移前停止所有服务。

### Q: 可以多次运行迁移脚本吗？

**A**：可以。脚本会自动跳过已经迁移的 agent，只处理需要迁移的 agent。

### Q: 迁移后旧的 `agent_index` 还能用吗？

**A**：不能。迁移后 `agent_index` 字段被删除，系统只使用持久化的 `ports` 配置。

### Q: 如果没有 agent 需要迁移会怎样？

**A**：脚本会显示 "All agents are already up to date!" 并正常退出。

## 技术细节

### 端口分配规则

每个 agent 分配 20 个连续端口，基于以下公式：

```python
BASE_PORT = 20000
PORTS_PER_AGENT = 20

base = BASE_PORT + agent_index * PORTS_PER_AGENT
```

**服务端口偏移**：
- vm: +0
- session: +1
- local: +2
- memory: +3
- chat: +4
- qemudebug: +5
- vnc: +6
- websocket: +7
- ssh: +8

**示例**：
- Agent 0: 20000-20019
- Agent 1: 20020-20039
- Agent 2: 20040-20059

### 数据库表结构

```sql
CREATE TABLE agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    vm_config TEXT NOT NULL,      -- JSON
    ports TEXT NOT NULL,           -- JSON
    setup_complete INTEGER DEFAULT 0
);
```

## 获取帮助

如果遇到问题：

1. 查看脚本输出的详细错误信息
2. 检查 `~/.local/share/novaic-gateway/` 日志文件
3. 在项目 issue 中报告问题，附上：
   - 错误信息
   - 迁移脚本输出
   - 数据库备份（如果可以分享）

## 参考

- 端口分配设计：`novaic-backend/gateway/config/agents_db.py`
- 数据库 Repository：`novaic-backend/gateway/db/repositories/agent.py`
- 相关文档：`PORT_PERSISTENCE_QUICK_REF.md`
