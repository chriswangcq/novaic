# x11vnc & websockify 清理 - 变更列表

## 文件修改清单

### 1. novaic-backend/gateway/vm/setup.py
**类型**: VM 设置脚本 (cloud-init 配置生成)

**删除内容**:
- [ ] 第 468 行: `x11vnc` 包
- [ ] 第 470 行: `python3-websockify` 包
- [ ] 第 496-513 行: `x11vnc.service` 配置块
- [ ] 第 515-530 行: `websockify.service` 配置块
- [ ] 第 554 行: `systemctl enable x11vnc`
- [ ] 第 555 行: `systemctl enable websockify`
- [ ] 第 558 行: `systemctl start x11vnc`
- [ ] 第 560 行: `systemctl start websockify`
- [ ] 第 570 行: "VNC: 5900" 和 "WebSocket: 6080" 说明

**保留内容**:
- ✅ SSH 端口说明
- ✅ lightdm 桌面环境服务

---

### 2. novaic-backend/gateway/vm/manager.py
**类型**: VM 生命周期管理器

**删除内容**:
- [ ] 第 58-59 行: `vnc_vm_port` 和 `ws_vm_port` 字段 (VmConfig)
- [ ] 第 69 行: `websockify_running` 字段 (VmStatus)
- [ ] 第 172 行: 端口检查列表中的 "vnc" 和 "websocket"
- [ ] 第 241 行: 等待 websockify 服务的代码
- [ ] 第 391 行: `websockify_running` 检查
- [ ] 第 399 行: `websockify_running` 参数传递
- [ ] 第 486-487 行: VNC 和 WebSocket 端口转发配置

**更新内容**:
- ✅ 第 401 行: `vnc_url` 改为 vmcontrol WebSocket URL
- ✅ 添加 `vnc_socket` 字段，指向 Unix socket 路径

---

### 3. novaic-backend/gateway/api/vm.py
**类型**: VM REST API

**删除内容**:
- [ ] 第 56 行: `websockify_running` 字段 (VmStatusResponse)
- [ ] 第 174-186 行: 返回时的 `websockify_running` 参数
- [ ] 第 196-208 行: 返回时的 `websockify_running` 参数

**更新内容**:
- ✅ 第 58 行: 更新 `vnc_url` 注释

---

### 4. novaic-backend/gateway/api/routes.py
**类型**: Gateway 主 API 路由

**删除内容**:
- [ ] 第 888-903 行: `_get_vnc_ports()` 辅助函数
- [ ] VNC 状态检查中的端口检查逻辑
- [ ] VNC 启动中的端口等待逻辑

**更新内容**:
- ✅ 重写 `vnc_status()` - 检查 vmcontrol 服务健康状态
- ✅ 重写 `start_vnc()` - 返回 vmcontrol WebSocket 信息

---

### 5. novaic-backend/gateway/api/internal.py
**类型**: 内部 API (Worker 使用)

**删除内容**:
- [ ] 第 1586 行: `"vnc": ports.vnc`
- [ ] 第 1587 行: `"websocket": ports.websocket`

---

### 6. novaic-backend/common/config.py
**类型**: 服务配置

**删除内容**:
- [ ] 第 76 行: `VM_WEBSOCKIFY_TIMEOUT` 配置项

---

### 7. novaic-backend/gateway/config/agents.py
**类型**: Agent 配置管理 (端口分配)

**删除内容**:
- [ ] 第 34 行: 端口布局文档中的 "6: vnc"
- [ ] 第 35 行: 端口布局文档中的 "7: websocket"
- [ ] 第 46 行: `vnc: int = 20006` (PortConfig)
- [ ] 第 47 行: `websocket: int = 20007` (PortConfig)
- [ ] 第 62 行: `vnc_vm_port: int = 5900` (VmConfig)
- [ ] 第 63 行: `ws_vm_port: int = 6080` (VmConfig)
- [ ] 第 98 行: `"vnc": 6` (SERVICE_OFFSETS)
- [ ] 第 99 行: `"websocket": 7` (SERVICE_OFFSETS)
- [ ] 第 145 行: `vnc=base + SERVICE_OFFSETS["vnc"]`
- [ ] 第 146 行: `websocket=base + SERVICE_OFFSETS["websocket"]`

**更新内容**:
- ✅ SSH 端口偏移从 8 改为 6
- ✅ `ssh: int = 20006` (原来是 20008)
- ✅ `"ssh": 6` (SERVICE_OFFSETS, 原来是 8)
- ✅ 更新文档示例中的端口号

---

### 8. novaic-backend/gateway/config/agents_db.py
**类型**: Agent 数据库配置

**删除内容**:
- [ ] 第 65 行: `vnc_vm_port: int = 5900`
- [ ] 第 66 行: `ws_vm_port: int = 6080`
- [ ] 第 201 行: `"vnc_vm_port": 5900`
- [ ] 第 202 行: `"ws_vm_port": 6080`

---

### 9. novaic-backend/mcp_client/skills/agent-bootstrap/SKILL.md
**类型**: 文档

**删除内容**:
- [ ] 第 243 行: "启动 lightdm/x11vnc" 中的 "x11vnc"

**更新内容**:
- ✅ 改为 "启动 lightdm"

---

## 端口映射变化

### 旧端口布局 (Agent 0)
```
20000: vm (MCP)
20001: session
20002: local
20003: memory
20004: chat
20005: qemudebug
20006: vnc          ❌ 删除
20007: websocket    ❌ 删除
20008: ssh          → 移动到 20006
```

### 新端口布局 (Agent 0)
```
20000: vm (MCP)
20001: session
20002: local
20003: memory
20004: chat
20005: qemudebug
20006: ssh          ✅ 优化
20007-20019: 预留
```

### 优势
- 每个 Agent 仍然使用 20 个端口
- SSH 端口前移，减少无用端口占用
- 为未来扩展预留更多连续端口

---

## 验证检查清单

### 语法验证
- [x] novaic-backend/gateway/vm/setup.py
- [x] novaic-backend/gateway/vm/manager.py
- [x] novaic-backend/gateway/api/vm.py
- [x] novaic-backend/gateway/api/routes.py
- [x] novaic-backend/gateway/api/internal.py
- [x] novaic-backend/common/config.py
- [x] novaic-backend/gateway/config/agents.py
- [x] novaic-backend/gateway/config/agents_db.py

### 完整性验证
- [x] 无 `x11vnc` 引用残留
- [x] 无 `websockify` 引用残留
- [x] 无 `5900` 端口引用残留
- [x] 无 `6080` 端口引用残留

### 新架构验证
- [x] QEMU VNC Unix socket 配置保留
- [x] vmcontrol 客户端调用保留
- [x] QMP socket 配置保留
- [x] Guest Agent socket 配置保留

---

## 测试建议

### 单元测试
1. 测试端口分配函数 `allocate_ports_for_agent()`
   - 验证 Agent 0 的 SSH 端口是 20006
   - 验证不再分配 vnc 和 websocket 端口
   - 验证端口范围仍在 20000-21999

2. 测试 VmConfig 初始化
   - 验证不再有 `vnc_vm_port` 和 `ws_vm_port` 字段
   - 验证只有 `mcp_vm_port = 8080`

### 集成测试
1. VM 启动流程
   - 启动 VM，确认无 x11vnc/websockify 错误
   - 检查 cloud-init 日志，确认跳过相关服务
   - 验证 QEMU VNC Unix socket 已创建

2. VNC 连接测试
   - 通过 vmcontrol 连接 VNC
   - URL: `ws://localhost:8080/api/vms/{agent_id}/vnc`
   - 验证屏幕显示正常

3. API 测试
   - GET `/api/vm/status/{agent_id}` - 无 `websockify_running` 字段
   - GET `/api/vnc/status` - 返回 vmcontrol 状态
   - POST `/api/vnc/start` - 返回正确的 WebSocket URL

### 回归测试
1. 确认 SSH 仍然正常工作 (端口已改变)
2. 确认 MCP 服务仍然正常工作
3. 确认其他 VM 操作不受影响 (stop, restart 等)

---

## 回滚计划

如果需要回滚，可以使用以下步骤：

1. 使用 git 恢复修改的文件
2. 重启 Gateway 服务
3. 重新创建 VM (或使用旧的 cloud-init 配置)

**注意**: 建议先在测试环境验证，再在生产环境部署。

---

**最后更新**: 2026-02-06  
**变更状态**: ✅ 完成并验证
