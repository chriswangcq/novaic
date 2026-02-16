# VM 自动注册机制 - 文档索引

## 📋 文档概览

本次完善了 VM 自动注册机制，确保新创建或新启动的 VM 能在所有场景下自动注册到 vmcontrol 服务。

---

## 📚 文档列表

### 1. 快速参考 ⚡
**文件**: `VM_AUTO_REGISTRATION_QUICK_REF.md`

**内容**:
- 核心问题和解决方案总结
- 快速测试方法
- 故障排查步骤
- 关键 API 端点
- 代码位置索引

**适用场景**: 需要快速了解或故障排查

---

### 2. 完整报告 📊
**文件**: `VM_AUTO_REGISTRATION_COMPLETE.md`

**内容**:
- 详细的问题分析
- 完整的实施方案
- 代码修改说明
- 注册流程图
- 容错机制
- 性能考虑
- 潜在改进方向

**适用场景**: 需要深入了解实现细节

---

### 3. 测试脚本 🧪
**文件**: `test_vm_auto_registration.sh`

**功能**:
- 自动化测试所有注册场景
- 生成测试报告
- 彩色输出，易于查看

**使用方法**:
```bash
./test_vm_auto_registration.sh
```

---

## 🎯 快速开始

### 验证修复是否生效

```bash
# 1. 启动 VM 并检查自动注册
curl -X POST http://localhost:19999/api/vm/start \
    -H "Content-Type: application/json" \
    -d '{"agent_id":"your-agent-id"}'

# 2. 等待几秒
sleep 5

# 3. 验证是否已注册
curl http://localhost:8080/api/vms | jq '.[] | select(.id=="your-agent-id")'
```

### 查看日志

```bash
# Gateway 日志
tail -f ~/Library/Application\ Support/com.novaic.app/logs/gateway-*.log | grep -i register

# vmcontrol 日志（如果单独运行）
# 查看终端输出
```

---

## 🔧 修改的文件

### 1. Python 后端
- `novaic-backend/gateway/vm/manager.py`
  - 修改 `start()` 方法（第 241-247 行）
  - 增强 `recover_processes()` 方法（第 429-498 行）

### 2. Rust 服务
- `novaic-app/src-tauri/vmcontrol/src/main.rs`
  - 新增 `auto_register_running_vms()` 函数（第 52-137 行）

---

## ✅ 验证清单

- [ ] Python 代码语法检查通过 ✓
- [ ] Rust 代码编译成功 ✓
- [ ] 运行测试脚本 `test_vm_auto_registration.sh`
- [ ] 验证场景 1: VM 启动时自动注册
- [ ] 验证场景 2: Gateway 重启后重新注册
- [ ] 验证场景 3: vmcontrol 重启后自动发现

---

## 🎨 功能覆盖

| 场景 | 实现位置 | 状态 | 测试 |
|------|----------|------|------|
| VM 启动注册 | `manager.py:start()` | ✅ | ⏳ |
| Gateway 重启重新注册 | `manager.py:recover_processes()` | ✅ | ⏳ |
| vmcontrol 重启自动发现 | `vmcontrol/main.rs:main()` | ✅ | ⏳ |

---

## 📞 故障排查

### 问题：VM 启动后未注册

**可能原因**:
1. vmcontrol 服务未运行
2. QMP socket 未创建
3. 网络连接问题

**排查步骤**:
```bash
# 1. 检查 vmcontrol 健康状态
curl http://localhost:8080/api/health

# 2. 检查 QMP socket
ls -la /tmp/novaic/novaic-qmp-*.sock

# 3. 查看 Gateway 日志
tail -f ~/Library/Application\ Support/com.novaic.app/logs/gateway-*.log
```

### 问题：Gateway 重启后未重新注册

**可能原因**:
1. vmcontrol 未先启动
2. VM 进程已停止
3. 数据库状态不一致

**排查步骤**:
```bash
# 1. 检查运行中的 VM
curl http://localhost:19999/api/vm/running

# 2. 查看 Gateway 启动日志
tail -f ~/Library/Application\ Support/com.novaic.app/logs/gateway-*.log | grep -i recover

# 3. 检查数据库状态
sqlite3 ~/Library/Application\ Support/com.novaic.app/gateway.db "SELECT agent_id, status FROM vm_processes;"
```

### 问题：vmcontrol 重启后未自动发现

**可能原因**:
1. QMP socket 文件权限问题
2. Socket 文件不存在
3. QMP 连接失败

**排查步骤**:
```bash
# 1. 检查 socket 目录和文件
ls -la /tmp/novaic/

# 2. 查看 vmcontrol 启动日志
# 应该看到 "Scanning for running VMs" 和 "Auto-registered VM" 消息

# 3. 测试 QMP 连接
# 使用 QMP 客户端工具测试连接
```

---

## 🚀 后续工作

### 建议的优化（可选）

1. **心跳检测**
   - 定期检查 VM 是否仍在 vmcontrol 中注册
   - 自动重新注册丢失的 VM

2. **事件驱动**
   - 监听 QMP socket 文件系统事件
   - 新 socket 创建时立即触发注册

3. **状态持久化**
   - 在数据库中记录注册状态
   - 避免重复注册

4. **更智能的重试**
   - 注册失败时使用指数退避
   - 区分临时性和永久性失败

---

## 📊 统计信息

- **修改的文件**: 2 个
- **新增代码行**: ~150 行
- **新增功能**: 3 个（启动注册、批量重新注册、自动发现）
- **覆盖场景**: 4 个（新启动、重启、Gateway 重启、vmcontrol 重启）
- **测试脚本**: 1 个

---

## 📝 版本信息

- **版本**: v1.0
- **日期**: 2026-02-07
- **状态**: ✅ 实现完成，等待测试验证
- **兼容性**: 向后兼容，不影响现有功能

---

## 🔗 相关链接

### 相关组件
- Gateway: `novaic-backend/main_gateway.py`
- VmManager: `novaic-backend/gateway/vm/manager.py`
- vmcontrol: `novaic-app/src-tauri/vmcontrol/`

### 相关文档
- VMCONTROL_README.md
- GATEWAY_VMCONTROL_PROXY_IMPLEMENTATION.md
- VMCONTROL_QUICK_REFERENCE.md

---

**生成时间**: 2026-02-07  
**作者**: AI Assistant  
**审核状态**: 待测试验证
