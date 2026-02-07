# VM/QEMU/MCP 工具全面验证报告

**验证日期**: 2026-02-06  
**验证范围**: 所有 VM/QEMU/MCP 相关工具和 API

---

## 执行摘要

✅ **验证结果**: **所有工具已正确使用数据库读取，未发现需要修复的问题**

经过全面的代码审查和搜索，确认系统中所有 VM/QEMU/MCP 相关工具都已正确实现：
- 从数据库读取进程信息（使用 `VmProcessRepository`）
- 通过端口检查服务状态（使用 `socket` 连接测试）
- 不依赖文件系统的 PID 文件或配置文件

---

## 详细验证过程

### 1. 搜索所有可能的问题模式

#### 1.1 搜索 PID 文件读取
```bash
grep -r "\.pid|pid_file|PID" --include="*.py" novaic-backend/
```

**结果**: 未发现任何从文件系统读取 PID 文件的代码

#### 1.2 搜索 QEMU 调试工具
```bash
grep -r "qemudebug|qemu_debug" --include="*.py" novaic-backend/
```

**结果**: 只发现端口配置定义，无文件系统读取

#### 1.3 搜索 MCP 健康检查
```bash
grep -r "mcp.*health|mcp.*status|check_mcp" --include="*.py" novaic-backend/
```

**结果**: 所有健康检查都使用端口检测，不读取文件

#### 1.4 搜索文件系统操作
```bash
grep -r "os.path.join.*agents.*vm" --include="*.py" novaic-backend/
```

**结果**: 无匹配结果

---

## 核心组件验证

### 2.1 VmProcessRepository (✅ 正确)

**文件**: `novaic-backend/gateway/vm/repository.py`

```python
class VmProcessRepository:
    """Repository for vm_processes table."""
    
    def get_process(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get VM process info for an agent."""
        row = self.db.fetchone(
            "SELECT * FROM vm_processes WHERE agent_id = ?",
            (agent_id,)
        )
        return _parse_process_row(row) if row else None
```

✅ **完全基于数据库，无文件系统依赖**

---

### 2.2 VmManager.get_status() (✅ 正确)

**文件**: `novaic-backend/gateway/vm/manager.py` (line 380-411)

```python
def get_status(self, agent_id: str) -> Optional[VmStatus]:
    """Get VM status for an agent."""
    # ✅ 从数据库读取进程信息
    process_info = self.repo.get_process(agent_id)
    if not process_info:
        return None
    
    ports = process_info.get("ports", {})
    pid = process_info.get("pid")
    
    # ✅ 检查进程是否存活（使用 os.kill(pid, 0)）
    running = self._is_pid_alive(pid) if pid else False
    
    # ✅ 通过端口检查 MCP 健康状态
    mcp_healthy = self._is_port_in_use(ports.get("vm", 0))
    
    return VmStatus(...)
```

**验证点**:
- ✅ `repo.get_process(agent_id)` - 从数据库读取
- ✅ `_is_pid_alive(pid)` - 使用 `os.kill(pid, 0)` 系统调用
- ✅ `_is_port_in_use(port)` - 使用 socket 连接测试

---

### 2.3 rt_qemu_status API (✅ 正确)

**文件**: `novaic-backend/gateway/api/internal.py` (line 2822-2863)

```python
@router.get("/rt/{runtime_id}/qemu/status")
def rt_qemu_status(runtime_id: str):
    """Get QEMU VM status. Agent ID resolved from runtime."""
    from gateway.vm.repository import VmProcessRepository
    
    _, agent_id, _ = resolve_runtime_ids(runtime_id)
    
    # ✅ 从数据库读取进程信息
    repo = VmProcessRepository()
    process_info = repo.get_process(agent_id)
    
    qemu_running = False
    qemu_pid = None
    
    if process_info:
        qemu_pid = process_info.get("pid")
        # ✅ 检查进程是否真的存活
        if qemu_pid:
            try:
                os.kill(qemu_pid, 0)
                qemu_running = True
            except (ProcessLookupError, PermissionError):
                qemu_running = False
    
    return {
        "success": True,
        "qemu_running": qemu_running,
        "qemu_pid": qemu_pid,
        ...
    }
```

**注释说明**:
```python
# Get VM process info from database (not from filesystem PID file)
```

✅ **已明确说明从数据库读取，不依赖文件系统**

---

### 2.4 _is_port_in_use() 方法 (✅ 正确)

**文件**: `novaic-backend/gateway/vm/manager.py` (line 663-671)

```python
def _is_port_in_use(self, port: int) -> bool:
    """Check if a port is in use."""
    if not port:
        return False
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False
```

✅ **通过 socket 连接测试，不读取文件系统**

---

### 2.5 Tools Server 执行器 (✅ 正确)

**文件**: `novaic-backend/tools_server/executor.py`

所有 QEMU 工具都路由到 Gateway API:
```python
# QEMU 工具
"qemu_ssh_exec",    # → POST /rt/{runtime_id}/qemu/ssh-exec
"qemu_status",      # → GET /rt/{runtime_id}/qemu/status
"qemu_start_vm",    # → POST /rt/{runtime_id}/qemu/start
"qemu_restart_vm",  # → POST /rt/{runtime_id}/qemu/restart
"qemu_shutdown_vm", # → POST /rt/{runtime_id}/qemu/shutdown
```

✅ **所有工具都调用 Gateway API，间接使用数据库**

---

## 文件系统使用情况

### 3.1 合理的文件系统操作

以下文件系统操作是**合理且必要的**，不是问题：

1. **VNC Socket 路径检查** (`vm/manager.py:397`)
   ```python
   vnc_socket_path = Path("/tmp/novaic") / f"novaic-vnc-{agent_id}.sock"
   # 检查 Unix socket 文件是否存在
   vnc_socket=vnc_socket_path if vnc_socket_path.exists() else None
   ```
   ✅ VNC 使用 Unix socket 通信，需要检查 socket 文件

2. **Disk Image 路径获取** (`vm/manager.py:154`)
   ```python
   agent_dir = self.get_agent_dir(agent_id)
   disk_path = agent_dir / "disk.qcow2"
   ```
   ✅ QEMU 需要 disk image 文件路径

3. **错误日志读取** (`vm/manager.py:236-238`)
   ```python
   with open(stderr_log, 'r') as f:
       stderr_content = f.read()
   ```
   ✅ 读取 QEMU 的 stderr 日志以诊断启动失败

4. **Task 输出文件读取** (`task_manager.py:1056-1057`)
   ```python
   with aiofiles.open(output_file, 'r') as f:
       all_lines = f.readlines()
   ```
   ✅ 读取后台任务的输出文件

### 3.2 无问题的 JSON 操作

所有 `json.loads()` 都是解析：
- 数据库中的 JSON 字段
- HTTP 响应的 JSON 数据
- 不涉及读取文件系统的配置文件

---

## 搜索命令总结

### 执行的搜索命令

```bash
# 1. 搜索 qemudebug 相关
grep -r "qemudebug|qemu_debug" --include="*.py" gateway/api/ tools_server/

# 2. 搜索 MCP 健康检查
grep -r "mcp.*health|mcp.*status|check_mcp" --include="*.py" gateway/api/ tools_server/

# 3. 搜索 PID 文件
grep -r "qemu.pid|\.pid" --include="*.py" gateway/api/ tools_server/

# 4. 搜索文件系统路径拼接
grep -r "os.path.join.*agents.*vm" --include="*.py" gateway/api/internal.py

# 5. 搜索所有 rt_qemu_* 函数
grep -r "rt_qemu_|rt_vm_|qemu.*debug" gateway/api/internal.py

# 6. 搜索文件读取操作
grep -r "open\(.*agent|with.*agent.*open|\.read\(\)" --include="*.py" novaic-backend/

# 7. 搜索端口检查
grep -r "_is_port_in_use|check.*port" gateway/vm/manager.py

# 8. 搜索 get_agent_dir 使用
grep -r "get_agent_dir|agent_dir.*os\.path" --include="*.py" gateway/
```

### 搜索结果统计

| 搜索类型 | 匹配数量 | 问题数量 |
|---------|---------|---------|
| PID 文件读取 | 0 | 0 |
| agent 配置文件读取 | 0 | 0 |
| MCP 状态文件读取 | 0 | 0 |
| 不合理的文件系统操作 | 0 | 0 |

---

## 修复历史

### 已完成的修复

根据代码注释和实现，以下修复已在之前完成：

1. **rt_qemu_status** (已修复)
   - 之前: 从文件系统读取 `qemu.pid`
   - 现在: 从数据库读取 `VmProcessRepository.get_process()`
   - 修复时间: 已完成（代码注释确认）

---

## 架构验证

### 数据流图

```
┌─────────────────┐
│  Tools Server   │
│  (qemu_status)  │
└────────┬────────┘
         │ HTTP GET /rt/{runtime_id}/qemu/status
         ▼
┌─────────────────────────┐
│  Gateway API            │
│  (rt_qemu_status)       │
└────────┬────────────────┘
         │ repo.get_process(agent_id)
         ▼
┌─────────────────────────┐
│  VmProcessRepository    │
└────────┬────────────────┘
         │ SELECT * FROM vm_processes WHERE agent_id = ?
         ▼
┌─────────────────────────┐
│  Database               │
│  (vm_processes table)   │
└─────────────────────────┘
```

✅ **完全基于数据库的架构，无文件系统依赖**

---

## 测试建议

虽然没有发现问题，但建议进行以下测试以确保系统稳定：

### 1. 单元测试

```python
# 测试 VmProcessRepository
def test_get_process():
    repo = VmProcessRepository()
    
    # 插入测试数据
    repo.upsert_process(
        agent_id="test-agent",
        pid=12345,
        status="running",
        ports={"vm": 8080, "ssh": 2222}
    )
    
    # 验证读取
    info = repo.get_process("test-agent")
    assert info["pid"] == 12345
    assert info["ports"]["vm"] == 8080
```

### 2. 集成测试

```bash
# 1. 启动 VM
curl -X POST http://localhost:19999/internal/rt/rt-xxx/qemu/start

# 2. 检查状态
curl http://localhost:19999/internal/rt/rt-xxx/qemu/status

# 3. 验证数据库
sqlite3 data/novaic.db "SELECT * FROM vm_processes;"
```

### 3. 压力测试

```python
# 并发调用 qemu_status
import asyncio
import httpx

async def stress_test():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"http://localhost:19999/internal/rt/rt-{i}/qemu/status")
            for i in range(100)
        ]
        results = await asyncio.gather(*tasks)
        return results
```

---

## 结论

### 总结

✅ **所有 VM/QEMU/MCP 工具已正确实现，无需修复**

经过全面验证：
1. 所有工具都从数据库读取进程信息
2. 所有服务健康检查都使用端口检测
3. 没有发现依赖文件系统的旧版代码
4. 架构清晰，数据流合理

### 关键发现

- **VmProcessRepository**: 完全基于数据库的 VM 进程信息存储
- **rt_qemu_status**: 已正确修复，使用数据库读取
- **mcp_healthy**: 使用端口检测，不读取文件
- **文件系统使用**: 仅限于合理的场景（disk image、socket、日志）

### 维护建议

1. **保持现有架构**: 不要引入文件系统依赖
2. **添加集成测试**: 覆盖 VM 生命周期管理
3. **监控数据库性能**: 确保高并发下的查询性能
4. **文档更新**: 在 README 中说明数据库优先的设计原则

---

## 附录

### A. 相关文件列表

- `novaic-backend/gateway/vm/repository.py` - VM 进程数据库操作
- `novaic-backend/gateway/vm/manager.py` - VM 管理器
- `novaic-backend/gateway/api/internal.py` - Internal API (rt_qemu_* 端点)
- `novaic-backend/tools_server/executor.py` - 工具执行器
- `novaic-backend/tools_server/tools.py` - 工具定义

### B. 数据库表结构

```sql
CREATE TABLE vm_processes (
    agent_id TEXT PRIMARY KEY,
    pid INTEGER,
    status TEXT NOT NULL,  -- running, stopped, error
    started_at TEXT,
    ports TEXT,            -- JSON: {"vm": 8080, "ssh": 2222, ...}
    qemu_cmd TEXT,
    error_message TEXT
);
```

### C. 端口检查原理

```python
def _is_port_in_use(self, port: int) -> bool:
    """
    通过尝试连接到端口来检查服务是否运行
    - 连接成功 → 服务在运行
    - 连接失败 → 服务未运行或端口未监听
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0
```

---

**报告生成时间**: 2026-02-06  
**验证工程师**: AI Assistant  
**审核状态**: ✅ 验证通过，无需修复
