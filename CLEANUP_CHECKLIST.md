# 清理清单：移除 FastMCP 旧代码

## 🎯 清理目标
移除 Phase 6 之前的 FastMCP 相关代码和配置，完成架构迁移。

---

## ✅ 清理步骤

### 第一步：VM 镜像内部清理（在 VM 内执行）

```bash
# 1. 停止并禁用 FastMCP 服务
sudo systemctl stop vmuse-mcp.service
sudo systemctl disable vmuse-mcp.service

# 2. 删除服务文件
sudo rm -f /etc/systemd/system/vmuse-mcp.service
sudo systemctl daemon-reload

# 3. 删除 FastMCP 代码
sudo rm -rf /opt/vmuse/

# 4. 卸载 FastMCP Python 包
pip3 uninstall fastmcp -y

# 5. 验证清理
systemctl status vmuse-mcp.service  # 应该显示 not found
which fastmcp  # 应该没有输出
```

**影响**: 释放 VM 内存和进程资源

---

### 第二步：QEMU 启动参数清理

#### 文件: `novaic-backend/gateway/vm/manager.py`

**位置 1**: ARM64 启动参数（约 548-551 行）
```python
# 删除这两行（MCP chardev）
"-chardev", f"socket,id=mcp,path={socket_path},server=on,wait=off",
"-device", "virtserialport,chardev=mcp,name=mcp",
```

**位置 2**: x86_64 启动参数（约 619-622 行）
```python
# 删除这两行（MCP chardev）
"-chardev", f"socket,id=mcp,path={socket_path},server=on,wait=off",
"-device", "virtserialport,chardev=mcp,name=mcp",
```

**验证**:
```bash
# 启动 VM 后检查进程参数
ps aux | grep qemu-system | grep -o "chardev.*mcp"
# 应该没有输出
```

**影响**: 减少一个 virtio-serial 通道，简化 QEMU 启动

---

### 第三步：删除 MCP Socket 路径变量

#### 文件: `novaic-backend/gateway/vm/manager.py`

**位置**: Socket 路径定义（约 541 行和 599 行）
```python
# 删除这行（不再需要）
socket_path = socket_dir / f"novaic-mcp-{agent_id}.sock"
```

**影响**: 清理未使用的变量

---

### 第四步：简化健康检查

#### 文件: `novaic-backend/gateway/vm/manager.py`

**位置**: `get_status()` 方法（约 368 行）
```python
# 修改前
mcp_healthy = self._is_port_in_use(ports.get("vm", 0))

# 修改后（方案 1：标记为不再使用）
mcp_healthy = True  # No longer checking MCP port (FastMCP removed)

# 或修改后（方案 2：改为检查 Guest Agent）
ga_healthy = self._is_guest_agent_responsive(agent_id)
```

**位置**: `VmStatus` 数据类（约 63-78 行）
```python
# 可选：重命名字段或添加注释
@dataclass
class VmStatus:
    # ...
    mcp_healthy: bool  # Deprecated: was for FastMCP, now always True
    # 或改为
    # guest_agent_healthy: bool
```

**影响**: 移除无效的端口检查

---

### 第五步：删除启动等待逻辑

#### 文件: `novaic-backend/gateway/vm/manager.py`

**位置**: `start()` 方法（约 220 行）
```python
# 删除这行（不再等待 MCP 端口）
# Wait for MCP
self._wait_for_service(ports.vm, "MCP", timeout=ServiceConfig.VM_MCP_TIMEOUT)
```

**可选替换**:
```python
# 改为等待 Guest Agent（如果需要）
logger.info(f"[VmManager] Waiting for Guest Agent...")
self._wait_for_guest_agent(agent_id, timeout=30)
```

**影响**: 加快 VM 启动流程（减少不必要的等待）

---

### 第六步：清理端口配置（需要评估）

#### 文件: `novaic-backend/gateway/config/agents.py`

**⚠️ 警告**: 需要先确认 `ports.vm` 是否还有其他用途！

**检查方法**:
```bash
cd novaic-backend
grep -r "ports\.vm" --include="*.py" | grep -v "manager.py"
```

**如果只用于 FastMCP**:
```python
# 可以考虑删除或标记为废弃
# ports.vm = BASE_PORT + agent_index * PORTS_PER_AGENT + SERVICE_OFFSETS["vm"]
```

**影响**: 释放端口号（每个 Agent 一个端口）

---

### 第七步：清理配置常量

#### 文件: `novaic-backend/common/config.py`

**查找并删除**:
```python
# 如果存在以下常量，可以删除
VM_MCP_TIMEOUT = xxx  # FastMCP 连接超时
```

**影响**: 代码整洁，移除未使用的配置

---

## 🧪 验证清单

### 清理前验证
- [ ] 备份当前代码：`git stash` 或 `git commit -m "backup before cleanup"`
- [ ] 确认当前 VM 工具发现正常工作
- [ ] 确认 vmcontrol API 工作正常

### 清理后验证

#### 1. VM 启动测试
```bash
# 启动 VM
curl -X POST http://localhost:19999/api/vm/start \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"xxx","agent_index":1,"memory":"4096","cpus":4}'

# 检查进程
ps aux | grep qemu-system | grep -v grep

# 应该看到 QEMU 进程正常运行，且没有 "chardev.*mcp" 参数
```

#### 2. Socket 文件检查
```bash
ls -la /tmp/novaic/

# 应该只看到这些 socket（没有 novaic-mcp-*.sock）
# novaic-qmp-{agent_id}.sock
# novaic-ga-{agent_id}.sock
# novaic-vnc-{agent_id}.sock
```

#### 3. 工具发现测试
```bash
# 查看 Tools Server 日志
tail -f ~/Library/Application\ Support/com.novaic.app/logs/tools-server-*.log | grep "VM tools"

# 期望输出：
# [RuntimeManager] Discovered 8 VM tools from Gateway for runtime: rt-xxx
```

#### 4. 工具调用测试
```python
# 测试 VM 工具是否可用
# 调用 browser_navigate, file_read, shell_exec 等
```

#### 5. VNC 连接测试
```bash
# 前端应该能够连接 noVNC
# WebSocket URL: ws://localhost:8080/api/vms/{agent_id}/vnc
```

---

## 📊 清理收益

### 资源释放
- ✅ VM 内存：~50-100MB（FastMCP Server 进程）
- ✅ 端口占用：1 个端口/Agent（MCP 端口）
- ✅ Socket 文件：1 个/Agent（novaic-mcp-*.sock）

### 性能提升
- ✅ VM 启动速度：减少 5-10 秒（不等待 MCP 端口）
- ✅ 健康检查：减少 1 个端口检查

### 代码简化
- ✅ QEMU 启动参数：减少 2 行
- ✅ Socket 路径管理：减少 1 个变量
- ✅ 等待逻辑：删除 1 个端口等待

---

## ⚠️ 注意事项

### 1. 端口配置需要特别小心
```python
# ports.vm 可能还有其他用途，删除前务必确认！
# 建议先注释，测试 1-2 天后再删除
```

### 2. 健康检查字段保留兼容性
```python
# 如果前端/其他服务依赖 mcp_healthy 字段，不要直接删除
# 可以改为返回固定值：True 或改名为 guest_agent_healthy
```

### 3. 分步清理
- **第一次部署**: 只清理 VM 内部和 QEMU 参数（核心清理）
- **测试 1-2 天**: 确认无问题
- **第二次部署**: 清理配置和常量（可选清理）

### 4. 保留旧 VM 镜像
```bash
# 清理前备份 VM 镜像（如果需要回滚）
cp ~/Library/Application\ Support/com.novaic.app/agents/xxx/disk.qcow2 \
   ~/Library/Application\ Support/com.novaic.app/agents/xxx/disk.qcow2.backup
```

---

## 🚀 执行顺序

### 推荐顺序
1. ✅ **第一步** - VM 内部清理（对外部无影响）
2. ✅ **第二步** - QEMU 参数清理（核心清理）
3. ✅ **第三步** - Socket 路径变量（简单清理）
4. ⚠️ **第四步** - 健康检查简化（需要测试）
5. ⚠️ **第五步** - 等待逻辑删除（需要测试）
6. ⚠️ **第六步** - 端口配置（需要仔细评估）
7. ⚠️ **第七步** - 配置常量（可选）

### 快速清理（最小风险）
```bash
# 只执行第一、二、三步
# 1. VM 内清理 FastMCP
# 2. 删除 QEMU MCP chardev 参数
# 3. 删除 socket_path 变量
```

---

## 📝 清理日志

### 清理记录模板
```markdown
### 清理日期: 2026-02-XX

#### 已完成
- [ ] VM 内 FastMCP 清理
- [ ] QEMU MCP chardev 删除
- [ ] socket_path 变量删除
- [ ] 健康检查简化
- [ ] 等待逻辑删除
- [ ] 端口配置评估
- [ ] 配置常量清理

#### 验证结果
- [ ] VM 启动正常
- [ ] Socket 文件正确
- [ ] 工具发现正常
- [ ] VNC 连接正常
- [ ] 无错误日志

#### 问题记录
- 无

#### 回滚计划
- Git 提交: xxxx
- VM 镜像备份: xxx.backup
```

---

## 🆘 如果出现问题

### 回滚步骤
```bash
# 1. 回滚代码
git reset --hard HEAD~1  # 或 git stash pop

# 2. 重启服务
# 停止并重新启动应用

# 3. 如果 VM 无法启动，恢复镜像
cp ~/Library/Application\ Support/com.novaic.app/agents/xxx/disk.qcow2.backup \
   ~/Library/Application\ Support/com.novaic.app/agents/xxx/disk.qcow2
```

### 常见问题
1. **VM 启动失败**: 检查 QEMU stderr 日志
2. **工具发现失败**: 检查 Tools Server 日志和 Gateway API
3. **VNC 无法连接**: 检查 socket 文件是否存在

---

**清理完成标志**: 
- ✅ QEMU 进程中无 MCP chardev 参数
- ✅ /tmp/novaic/ 中无 novaic-mcp-*.sock 文件
- ✅ VM 内无 vmuse-mcp 服务
- ✅ 所有功能验证通过
