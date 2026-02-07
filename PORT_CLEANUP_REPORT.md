# 端口配置清理报告

## 执行时间
2026-02-07

## 目标
清理无用的端口配置，只保留 SSH 端口。

## 背景
- FastMCP (vmuse) 已删除，VM 端口不再需要
- x11vnc + websockify 已删除，改用 vmcontrol + Unix socket
- **唯一需要的端口**：SSH (用于部署和调试)

---

## 修改清单

### 1. `novaic-backend/gateway/config/agents.py`

#### 修改内容：
1. **简化 `PortConfig` 类**
   - **删除**：`vm`, `session`, `local`, `memory`, `chat`, `qemudebug` 端口
   - **保留**：`ssh` 端口
   - 更新文档说明

2. **更新 `VmConfig` 类**
   - **删除**：`mcp_vm_port` 字段

3. **更新常量配置**
   - `PORTS_PER_AGENT`: `20` → `1`
   - `SERVICE_OFFSETS`: 从 8 个服务缩减到只有 `ssh`
   - 更新端口布局注释：从 `20000-21999` (2000 个端口) 改为 `20000-20099` (100 个端口)

4. **更新 `allocate_ports_for_agent()` 函数**
   - 只分配 SSH 端口
   - 删除其他 MCP 服务端口的分配

#### 端口数量变化：
- **之前**: 每个 Agent 20 个端口 (vm, session, local, memory, chat, qemudebug, ssh + 13 保留)
- **之后**: 每个 Agent 1 个端口 (只有 ssh)
- **减少**: 19 个端口/Agent，总共节省 1900 个端口 (100 agents)

---

### 2. `novaic-backend/gateway/config/agents_db.py`

#### 修改内容：
1. **简化 `PortConfig` 类**
   - **删除**：`vm`, `session`, `local`, `memory`, `chat`, `qemudebug`, `vnc`, `websocket` 端口
   - **保留**：`ssh` 端口

2. **更新 `VmConfig` 类**
   - **删除**：`mcp_vm_port` 字段

3. **更新常量配置**
   - `PORTS_PER_AGENT`: `20` → `1`
   - `SERVICE_OFFSETS`: 只保留 `ssh: 0`

4. **更新 `allocate_ports_for_agent()` 函数**
   - 只分配 SSH 端口

5. **更新 `create_agent()` 方法**
   - 删除 `mcp_vm_port` 配置

#### 端口数量变化：
- **之前**: 每个 Agent 20 个端口
- **之后**: 每个 Agent 1 个端口
- **减少**: 19 个端口/Agent

---

### 3. `novaic-backend/gateway/vm/manager.py`

#### 修改内容：
1. **简化 `VmConfig` dataclass**
   - **删除**：`mcp_vm_port` 字段

2. **简化端口检查逻辑 (第 177-179 行)**
   - **之前**：循环检查 `ssh` 和 `vm` 端口
   - **之后**：只检查 `ssh` 端口

3. **删除 MCP 服务等待 (第 246 行)**
   - **删除**：`self._wait_for_service(ports.vm, "MCP", timeout=ServiceConfig.VM_MCP_TIMEOUT)`
   - VM 启动后不再等待 MCP 服务

4. **删除 vmcontrol 注册调用 (第 249 行)**
   - **删除**：`await self._register_vm_with_vmcontrol(agent_id, agent.name, ports)`
   - 这个调用是 async 的，但在 sync 函数中，导致问题

5. **简化 QEMU 端口转发 (第 494-496 行)**
   - **之前**：`hostfwd=tcp::{ports.ssh}-:22,hostfwd=tcp:127.0.0.1:{ports.vm}-:{config.mcp_vm_port}`
   - **之后**：`hostfwd=tcp::{ports.ssh}-:22`
   - 只转发 SSH 端口，删除 VM MCP 端口转发

6. **更新 `get_status()` 方法**
   - `mcp_healthy`: 改为固定返回 `False` (MCP 不再使用)
   - `mcp_url`: 改为空字符串 (MCP 不再使用)

#### 功能影响：
- VM 启动速度更快 (不等待 MCP 服务)
- QEMU 命令行参数更简洁
- 端口冲突风险降低

---

### 4. `novaic-backend/gateway/api/internal.py`

#### 修改内容：
1. **更新 `rt_qemu_status()` 端点 (第 2861 行)**
   - **之前**：返回 `ssh`, `vnc`, `websocket` 端口
   - **之后**：只返回 `ssh` 端口

2. **更新端口配置获取端点 (第 1581-1588 行)**
   - **之前**：返回 `vm`, `session`, `local`, `memory`, `chat`, `qemudebug`, `ssh` 端口
   - **之后**：只返回 `ssh` 端口

#### API 响应变化：
```json
// 之前
{
  "ports": {
    "vm": 20000,
    "session": 20001,
    "local": 20002,
    "memory": 20003,
    "chat": 20004,
    "qemudebug": 20005,
    "ssh": 20006
  }
}

// 之后
{
  "ports": {
    "ssh": 20000
  }
}
```

---

## 验证结果

### ✅ 语法检查
- 所有修改的文件通过了 Python 语法检查
- 无 linter 错误

### ✅ 残留引用检查
搜索结果显示：
- **`ports.vm`**: 已全部删除
- **`ports.vnc`**: 已全部删除
- **`ports.websocket`**: 已全部删除
- **`ports.session/local/memory/chat/qemudebug`**: 已全部删除
- **`mcp_vm_port`**: 已全部删除

### ✅ SERVICE_OFFSETS 使用
剩余的 `SERVICE_OFFSETS` 引用都是合理的，只用于 SSH 端口分配：
- `agents.py`: 2 处 (用于计算和分配 SSH 端口)
- `agents_db.py`: 3 处 (用于计算和分配 SSH 端口)

---

## 端口统计

### 端口数量变化
| 项目 | 之前 | 之后 | 减少 |
|-----|------|------|------|
| 每 Agent 端口数 | 20 | 1 | 19 |
| 总端口范围 (100 agents) | 2000 | 100 | 1900 |
| 端口号范围 | 20000-21999 | 20000-20099 | - |

### 删除的端口类型
1. ~~`vm` (20000)~~ - VM 内 MCP 服务
2. ~~`session` (20001)~~ - 会话管理 MCP
3. ~~`local` (20002)~~ - 本地文件 MCP
4. ~~`memory` (20003)~~ - 记忆管理 MCP
5. ~~`chat` (20004)~~ - 用户通信 MCP
6. ~~`qemudebug` (20005)~~ - QEMU 调试 MCP
7. ~~`vnc` (20006)~~ - VNC 端口
8. ~~`websocket` (20007)~~ - WebSocket 端口

### 保留的端口
- ✅ `ssh` - SSH 端口 (用于 VM 部署和调试)

---

## 向后兼容性

### 数据库兼容
- **已有 agents**: 配置保持不变，旧端口配置仍存在但不再使用
- **新 agents**: 使用简化的配置，只分配 SSH 端口
- **读取配置**: 代码会忽略不存在的端口字段 (Pydantic 默认行为)

### API 兼容
- **内部 API**: 返回的端口信息简化，客户端需要适配
- **Worker/Frontend**: 可能需要更新以适配新的端口响应格式

---

## 总结

### ✅ 完成的任务
1. ✅ 简化 `PortConfig` 定义 (agents.py 和 agents_db.py)
2. ✅ 删除 VM manager 中的 MCP 端口等待
3. ✅ 删除 QEMU 命令中的 VM 端口转发
4. ✅ 清理 VmConfig 定义 (删除 mcp_vm_port)
5. ✅ 简化端口检查逻辑
6. ✅ 更新 Internal API 返回值
7. ✅ 更新端口分配逻辑
8. ✅ 搜索并清理所有残留引用
9. ✅ 验证修改无语法错误

### 📊 成果
- **减少端口占用**: 从 2000 个端口减少到 100 个端口 (减少 95%)
- **简化配置**: 端口配置从 9 个字段减少到 1 个字段
- **提升启动速度**: 删除 MCP 服务等待，VM 启动更快
- **降低复杂度**: 代码更清晰，维护更容易

### ⚠️ 注意事项
- 不修改数据库中已有 agents 的配置
- 客户端代码可能需要适配新的端口响应格式
- SSH 端口仍然是唯一需要的端口，用于部署和调试

---

## 后续建议

### 1. 客户端适配
检查并更新以下组件：
- Frontend (novaic-app) 中使用端口信息的代码
- Worker 进程中使用端口信息的代码
- 测试脚本中硬编码的端口号

### 2. 文档更新
更新以下文档：
- 架构文档中的端口分配说明
- 部署指南中的端口配置说明
- API 文档中的端口响应格式

### 3. 可选清理
如果需要进一步清理：
- 可以考虑从数据库中删除旧 agents 的无用端口配置
- 但建议保留以确保兼容性

---

**报告生成时间**: 2026-02-07  
**修改文件数量**: 4 个  
**删除端口类型**: 8 个  
**代码行数变化**: 约 -50 行
