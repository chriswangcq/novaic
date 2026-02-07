# VM ID 映射修复 - 快速参考

## 🎯 问题
前端传递 `agent_id` (UUID)，但 VNC socket 使用 `agent_index` (数字)

## ✅ 解决方案

### 修改的文件（3个）

1. **Gateway**: `novaic-backend/gateway/vm/manager.py`
   - 添加 `agent_index` 到 `VmStatus`

2. **vmcontrol**: `novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs`
   - 支持两种 ID 格式：数字 + UUID

3. **前端**: `novaic-app/src/services/vm.ts`
   - 优先使用 `agent_index`

### 工作原理

```
前端请求 → Gateway (获取 agent_index) → vmcontrol (查找 socket)
```

**支持的 VM ID 格式**:
- ✅ `1` (agent_index) → 直接查找 `novaic-vnc-1.sock`
- ✅ `7b053af9-...` (UUID) → 搜索所有 `novaic-vnc-*.sock`

## 🧪 快速测试

```bash
# 1. 运行测试脚本
./test_vnc_mapping.sh

# 2. 手动测试
curl -s http://localhost:10000/api/vm/status | jq '.[].agent_index'  # 应返回数字
ls -la /tmp/novaic/novaic-vnc-*.sock  # 应显示 socket 文件
```

## 📦 重新编译

```bash
# vmcontrol
cd novaic-app/src-tauri/vmcontrol && cargo build --release

# 前端（可选）
cd ../.. && npm run build
```

## 🔗 WebSocket URL

```javascript
// 推荐：使用 agent_index（精确快速）
ws://localhost:8080/api/vms/1/vnc

// 兼容：使用 agent_id（自动查找）
ws://localhost:8080/api/vms/7b053af9-a386-425f-8127-492bfc156525/vnc
```

## ✨ 状态

- ✅ 代码修改完成
- ✅ 编译成功
- ✅ 无 linter 错误
- ⏳ 待运行时测试

## 📚 详细文档

- [VM_ID_MAPPING_FIX_SUMMARY.md](VM_ID_MAPPING_FIX_SUMMARY.md) - 完整总结
- [VM_ID_MAPPING_FIX.md](VM_ID_MAPPING_FIX.md) - 技术细节
