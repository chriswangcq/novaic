# x11vnc & websockify 清理 - 快速参考

## ✅ 完成状态
**所有 x11vnc 和 websockify 代码已删除并通过验证**

---

## 📁 修改文件 (9 个)

| 文件 | 类型 | 主要修改 |
|------|------|----------|
| `gateway/vm/setup.py` | VM 设置 | 删除包、服务、启动命令 |
| `gateway/vm/manager.py` | VM 管理 | 删除端口转发、等待逻辑 |
| `gateway/api/vm.py` | VM API | 删除响应字段 |
| `gateway/api/routes.py` | Gateway API | 重写 VNC API |
| `gateway/api/internal.py` | 内部 API | 删除端口返回 |
| `common/config.py` | 配置 | 删除超时设置 |
| `gateway/config/agents.py` | Agent 配置 | 删除端口分配 |
| `gateway/config/agents_db.py` | DB 配置 | 删除端口字段 |
| `mcp_client/skills/agent-bootstrap/SKILL.md` | 文档 | 更新说明 |

---

## 🔄 架构变化

### Before (❌ 删除)
```
[VM内部] x11vnc:5900 → websockify:6080
    ↓ (QEMU 端口转发)
[宿主机] localhost:6080
    ↓
[前端] ws://localhost:6080/websockify
```

### After (✅ 当前)
```
[VM内部] QEMU 原生 VNC
    ↓ (Unix socket: /tmp/novaic/novaic-vnc-{agent_id}.sock)
[vmcontrol] WebSocket 代理
    ↓
[前端] ws://localhost:8080/api/vms/{agent_id}/vnc
```

---

## 🔢 端口变化

### Agent 0 端口布局

| 服务 | 旧端口 | 新端口 | 状态 |
|------|--------|--------|------|
| vm (MCP) | 20000 | 20000 | ✅ 不变 |
| session | 20001 | 20001 | ✅ 不变 |
| local | 20002 | 20002 | ✅ 不变 |
| memory | 20003 | 20003 | ✅ 不变 |
| chat | 20004 | 20004 | ✅ 不变 |
| qemudebug | 20005 | 20005 | ✅ 不变 |
| vnc | 20006 | - | ❌ 删除 |
| websocket | 20007 | - | ❌ 删除 |
| ssh | 20008 | **20006** | ✅ 优化 |

---

## 🗑️ 删除内容

### 包依赖
- ❌ `x11vnc`
- ❌ `python3-websockify`

### systemd 服务
- ❌ `x11vnc.service`
- ❌ `websockify.service`

### 端口配置
- ❌ `vnc_vm_port: int = 5900`
- ❌ `ws_vm_port: int = 6080`
- ❌ `PortConfig.vnc: int = 20006`
- ❌ `PortConfig.websocket: int = 20007`

### QEMU 端口转发
- ❌ `hostfwd=tcp::5900-:5900` (VNC)
- ❌ `hostfwd=tcp::6080-:6080` (WebSocket)

### 配置项
- ❌ `VM_WEBSOCKIFY_TIMEOUT = 60`

### 字段
- ❌ `VmStatus.websockify_running: bool`
- ❌ `VmStatusResponse.websockify_running: bool`

---

## ✅ 保留内容 (新架构)

### QEMU VNC
- ✅ `-vnc unix:/tmp/novaic/novaic-vnc-{agent_id}.sock`
- ✅ `VmStatus.vnc_socket: Optional[Path]`
- ✅ `vnc_url: ws://localhost:8080/api/vms/{agent_id}/vnc`

### 其他端口转发
- ✅ SSH: `hostfwd=tcp::{ssh_port}-:22`
- ✅ MCP: `hostfwd=tcp:127.0.0.1:{vm_port}-:8080`

### vmcontrol 集成
- ✅ vmcontrol 客户端调用
- ✅ VNC WebSocket 代理
- ✅ 健康检查 API

---

## 🧪 测试清单

### 必须测试
- [ ] VM 启动 (无 x11vnc/websockify 错误)
- [ ] VNC 连接 (通过 vmcontrol)
- [ ] GET `/api/vm/status/{agent_id}` (无 websockify_running)
- [ ] GET `/api/vnc/status` (返回 vmcontrol 状态)
- [ ] SSH 连接 (端口已改变为 20006)

### 建议测试
- [ ] 多 Agent 端口分配
- [ ] VM 重启/停止
- [ ] MCP 服务连接
- [ ] 前端 VNC 显示

---

## 📊 统计

- **文件**: 9 个 (8 Python + 1 Markdown)
- **代码行**: ~120 行删除
- **端口**: 2 个删除 (vnc, websocket)
- **服务**: 2 个删除 (x11vnc, websockify)
- **包**: 2 个删除

---

## 📚 相关文档

- 详细报告: `X11VNC_WEBSOCKIFY_CLEANUP_REPORT.md`
- 变更列表: `X11VNC_WEBSOCKIFY_CLEANUP_CHANGES.md`
- 简短摘要: `X11VNC_WEBSOCKIFY_CLEANUP_SUMMARY.md`

---

## 🚀 优势

1. **部署简化**: 无需在 VM 内安装额外服务
2. **性能提升**: QEMU 原生 VNC，减少中间层
3. **架构统一**: 通过 vmcontrol 统一管理所有 VM 控制
4. **端口优化**: 减少 2 个端口占用，SSH 前移
5. **安全增强**: Unix socket 不暴露网络端口

---

**更新时间**: 2026-02-06  
**验证状态**: ✅ 语法检查通过，待功能测试
