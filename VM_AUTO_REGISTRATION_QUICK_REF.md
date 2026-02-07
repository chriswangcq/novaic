# VM 自动注册机制 - 快速参考

## 核心问题 & 解决方案

### 问题
VM 启动后未自动注册到 vmcontrol 服务。

### 根本原因
`_register_vm_with_vmcontrol()` 方法已定义但从未被调用。

### 解决方案
在 3 个关键位置添加自动注册：
1. ✅ VM 启动时（`manager.py:start()`）
2. ✅ Gateway 重启时（`manager.py:recover_processes()`）
3. ✅ vmcontrol 启动时（`vmcontrol/main.rs:auto_register_running_vms()`）

---

## 完整覆盖场景

| 场景 | 触发点 | 状态 |
|------|--------|------|
| 新启动 VM | `POST /api/vm/start` | ✅ |
| 重启 VM | `POST /api/vm/restart` | ✅ |
| Gateway 重启 | Gateway startup | ✅ |
| vmcontrol 重启 | vmcontrol startup | ✅ |

---

## 快速测试

### 方法 1: 自动化测试脚本
```bash
./test_vm_auto_registration.sh
```

### 方法 2: 手动验证

#### 测试 VM 启动注册
```bash
# 1. 启动 VM
curl -X POST http://localhost:19999/api/vm/start \
    -H "Content-Type: application/json" \
    -d '{"agent_id":"your-agent-id"}'

# 2. 验证注册（等待 5 秒）
sleep 5
curl http://localhost:8080/api/vms | jq '.[] | select(.id=="your-agent-id")'
```

#### 测试 Gateway 重启重新注册
```bash
# 1. 确保 VM 运行中
curl http://localhost:19999/api/vm/running

# 2. 重启 Gateway
# (停止并启动 Gateway)

# 3. 检查日志（应看到 "Re-registering X VMs"）
tail -f ~/Library/Application\ Support/com.novaic.app/logs/gateway-*.log | grep -i register

# 4. 验证
curl http://localhost:8080/api/vms
```

#### 测试 vmcontrol 重启自动发现
```bash
# 1. 确保 VM 运行中
curl http://localhost:19999/api/vm/running

# 2. 重启 vmcontrol
# (停止并启动 vmcontrol)

# 3. 验证（应自动发现并注册）
curl http://localhost:8080/api/vms
```

---

## 关键日志消息

### 成功注册
```
[VmManager] VM abc-123 registered with vmcontrol
[VmManager] Re-registered VM abc-123 with vmcontrol
[vmcontrol] ✓ Auto-registered VM: abc-123
```

### 预期警告（非致命）
```
[VmManager] vmcontrol not available, skipping VM registration
[VmManager] Failed to register VM with vmcontrol (non-fatal): ...
```

---

## 故障排查

### VM 未注册？

1. **检查 vmcontrol 健康状态**
   ```bash
   curl http://localhost:8080/api/health
   ```

2. **检查 QMP socket**
   ```bash
   ls -la /tmp/novaic/novaic-qmp-*.sock
   ```

3. **查看 Gateway 日志**
   ```bash
   tail -f ~/Library/Application\ Support/com.novaic.app/logs/gateway-*.log
   ```

4. **手动注册**
   ```bash
   curl -X POST http://localhost:8080/api/vms \
       -H "Content-Type: application/json" \
       -d '{
           "id": "your-agent-id",
           "name": "your-agent-name",
           "qmp_socket": "/tmp/novaic/novaic-qmp-your-agent-id.sock"
       }'
   ```

---

## 代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| VM 启动注册 | `manager.py` | 241-247 |
| 批量重新注册 | `manager.py` | 457-498 |
| 自动发现 | `vmcontrol/main.rs` | 52-137 |

---

## API 端点

### Gateway
- `POST /api/vm/start` - 启动 VM（触发自动注册）
- `GET /api/vm/running` - 获取运行中的 VM 列表
- `GET /api/vm/status/{agent_id}` - 获取 VM 状态

### vmcontrol
- `GET /api/health` - 健康检查
- `GET /api/vms` - 列出所有已注册的 VM
- `POST /api/vms` - 手动注册 VM
- `GET /api/vms/{id}` - 获取 VM 详情

---

## 注册流程（简化）

```
VM 启动 → QEMU 进程 → QMP Socket 创建 → 自动注册到 vmcontrol
    ↓
Gateway 重启 → 扫描运行中 VM → 批量重新注册
    ↓
vmcontrol 重启 → 扫描 QMP Socket → 自动发现并注册
```

---

## 重要文件

- **完整报告**: `VM_AUTO_REGISTRATION_COMPLETE.md`
- **测试脚本**: `test_vm_auto_registration.sh`
- **核心实现**: `novaic-backend/gateway/vm/manager.py`
- **自动发现**: `novaic-app/src-tauri/vmcontrol/src/main.rs`

---

**状态**: ✅ 实现完成  
**下一步**: 运行测试验证
