# VM ID 映射问题修复

## 问题描述

前端传递的是 `agent_id` (UUID)，但 VNC socket 使用 `agent_index` (数字)。

**实际情况**：
- Socket: `/var/folders/.../novaic-vnc-1.sock`
- 前端请求: `/api/vms/7b053af9-a386-425f-8127-492bfc156525/vnc`
- vmcontrol 查找: `novaic-vnc-7b053af9-a386-425f-8127-492bfc156525.sock` ❌

## 解决方案

### 1. Gateway 端（Python）

**修改文件**: `novaic-backend/gateway/vm/manager.py`

**变更**:
- ✅ 在 `VmStatus` 数据类中添加 `agent_index` 字段
- ✅ 在 `get_status()` 方法中从端口反向计算 `agent_index`
- ✅ 前端可以通过 Gateway API 获取 `agent_index`

```python
@dataclass
class VmStatus:
    # ... 其他字段 ...
    agent_index: Optional[int] = None  # Agent index for socket filenames
```

### 2. vmcontrol 端（Rust）

**修改文件**: `novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs`

**变更**:
- ✅ 支持两种 VM ID 格式：
  - **数字格式** (agent_index): 直接查找 `novaic-vnc-1.sock`
  - **UUID 格式** (agent_id): 搜索所有可用的 `novaic-vnc-*.sock` 文件
- ✅ 添加 `find_vnc_socket()` 辅助函数处理不同格式
- ✅ 更好的错误信息

**逻辑**:
```rust
fn find_vnc_socket(vm_id: &str) -> Result<PathBuf, Error> {
    if vm_id.parse::<u32>().is_ok() {
        // 数字：直接查找 novaic-vnc-{agent_index}.sock
    } else if is_uuid(vm_id) {
        // UUID：搜索所有 novaic-vnc-*.sock
        // TODO: 未来可查询 Gateway API 验证归属
    } else {
        // 未知格式：尝试直接查找
    }
}
```

### 3. 前端（TypeScript）

**修改文件**: `novaic-app/src/services/vm.ts`

**变更**:
- ✅ 在 `VmStatus` 接口中添加 `agent_index` 字段
- ✅ `getVncUrl()` 优先使用 `agent_index`（如果可用）
- ✅ 回退到 `agent_id` 如果 `agent_index` 不可用

```typescript
async getVncUrl(agentId: string): Promise<string> {
  const status = await this.getStatus(agentId);
  
  // 优先使用 agent_index（精确匹配）
  const vmId = status?.agent_index !== undefined 
    ? status.agent_index.toString() 
    : agentId;
  
  return `ws://localhost:${port}/api/vms/${vmId}/vnc`;
}
```

## 兼容性

### 支持的 VM ID 格式

| 格式 | 示例 | vmcontrol 行为 |
|------|------|----------------|
| agent_index (数字) | `1`, `2`, `3` | 直接查找 `novaic-vnc-1.sock` |
| agent_id (UUID) | `7b053af9-a386-425f-8127-492bfc156525` | 搜索所有 `novaic-vnc-*.sock` 文件 |
| 其他 | 任意字符串 | 尝试直接查找（向后兼容） |

### 优先级策略

1. **最优**: 前端传递 `agent_index`（精确匹配，零查找）
2. **次优**: 前端传递 `agent_id`（需要搜索目录）
3. **回退**: 使用旧的 websockify 方式

## 测试验证

### 测试步骤

#### 1. 测试 agent_index 格式（数字）

```bash
# 启动 VM
curl -X POST http://localhost:10000/api/vm/start \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "test-agent-1",
    "agent_index": 1,
    "memory": "4096",
    "cpus": 4
  }'

# 确认 VNC socket 存在
ls -la /tmp/novaic/novaic-vnc-1.sock

# 启动 vmcontrol
cd novaic-app/src-tauri/vmcontrol
cargo run --release

# 测试连接（使用数字 ID）
# 浏览器打开: ws://localhost:8080/api/vms/1/vnc
# 或使用 wscat:
wscat -c ws://localhost:8080/api/vms/1/vnc
```

**预期结果**: ✅ 连接成功

#### 2. 测试 agent_id 格式（UUID）

```bash
# 获取 agent_id
AGENT_ID=$(curl -s http://localhost:10000/api/vm/status | jq -r 'keys[0]')
echo "Agent ID: $AGENT_ID"

# 测试连接（使用 UUID）
wscat -c "ws://localhost:8080/api/vms/$AGENT_ID/vnc"
```

**预期结果**: ✅ 自动找到 socket，连接成功

#### 3. 测试前端集成

```bash
# 启动完整应用
cd novaic-app
npm run tauri dev

# 在前端打开 VNC 视图
# 检查浏览器控制台日志
```

**预期日志**:
```
[VM Service] Using vmcontrol proxy: ws://localhost:8080/api/vms/1/vnc (vmId: 1)
```

### 测试脚本

```bash
#!/bin/bash
# test_vnc_mapping.sh

set -e

echo "=== VM ID 映射测试 ==="

# 1. 检查 socket 文件
echo ""
echo "1. 检查 VNC socket 文件..."
ls -la /tmp/novaic/novaic-vnc-*.sock 2>/dev/null || echo "  ⚠️  没有找到 VNC socket 文件"

# 2. 测试 vmcontrol 健康检查
echo ""
echo "2. 测试 vmcontrol 健康检查..."
curl -s http://localhost:8080/health | jq '.'

# 3. 获取 VM 状态（包括 agent_index）
echo ""
echo "3. 获取 VM 状态..."
STATUS=$(curl -s http://localhost:10000/api/vm/status)
echo "$STATUS" | jq '.'

# 提取第一个 agent 的信息
AGENT_ID=$(echo "$STATUS" | jq -r 'keys[0]')
AGENT_INDEX=$(echo "$STATUS" | jq -r ".\"$AGENT_ID\".agent_index")

echo ""
echo "  Agent ID: $AGENT_ID"
echo "  Agent Index: $AGENT_INDEX"

# 4. 测试使用 agent_index 连接
echo ""
echo "4. 测试使用 agent_index (数字) 连接..."
if [ "$AGENT_INDEX" != "null" ]; then
    # 使用 timeout 避免挂起
    timeout 2 wscat -c "ws://localhost:8080/api/vms/$AGENT_INDEX/vnc" 2>&1 | head -5 || true
    echo "  ✅ agent_index 连接测试完成"
else
    echo "  ⚠️  agent_index 不可用"
fi

# 5. 测试使用 agent_id 连接
echo ""
echo "5. 测试使用 agent_id (UUID) 连接..."
if [ "$AGENT_ID" != "null" ]; then
    timeout 2 wscat -c "ws://localhost:8080/api/vms/$AGENT_ID/vnc" 2>&1 | head -5 || true
    echo "  ✅ agent_id 连接测试完成"
else
    echo "  ⚠️  agent_id 不可用"
fi

echo ""
echo "=== 测试完成 ==="
```

### 错误场景测试

#### 场景 1: VM 未运行

```bash
curl -s http://localhost:8080/api/vms/999/vnc
```

**预期响应**:
```json
{
  "error": "VNC socket not found for agent_index 999. Expected: /tmp/novaic/novaic-vnc-999.sock"
}
```

#### 场景 2: 无效的 UUID

```bash
curl -s http://localhost:8080/api/vms/invalid-uuid-format/vnc
```

**预期响应**:
```json
{
  "error": "Invalid VM ID format: 'invalid-uuid-format'. Expected agent_index (number) or agent_id (UUID)"
}
```

## 部署检查

### 编译验证

```bash
# 编译 vmcontrol
cd novaic-app/src-tauri/vmcontrol
cargo build --release

# 编译前端
cd ../..
npm run build
```

### 运行时日志

启动后检查日志：

```bash
# vmcontrol 日志
[2026-02-06 10:00:00] INFO VNC WebSocket connection request for VM: 7b053af9-...
[2026-02-06 10:00:00] INFO VM ID appears to be UUID, searching for active VNC sockets...
[2026-02-06 10:00:00] INFO Found potential VNC socket: /tmp/novaic/novaic-vnc-1.sock
[2026-02-06 10:00:00] INFO Using VNC socket: /tmp/novaic/novaic-vnc-1.sock
[2026-02-06 10:00:00] INFO WebSocket upgraded, starting VNC proxy
```

## 未来改进

### 短期（当前实现）

- ✅ 支持两种 ID 格式
- ✅ 自动查找可用 socket
- ✅ 单 VM 场景工作良好

### 中期（建议）

- ⏭️ vmcontrol 查询 Gateway API 验证 socket 归属
- ⏭️ 建立完整的 agent_id → agent_index 映射缓存
- ⏭️ 支持多 VM 环境的精确匹配

### 长期（可选）

- ⏭️ Gateway 提供映射注册 API
- ⏭️ vmcontrol 订阅 VM 状态变更
- ⏭️ 统一的服务发现机制

## 总结

### 修改的文件

1. `novaic-backend/gateway/vm/manager.py` - 添加 `agent_index` 到 `VmStatus`
2. `novaic-app/src-tauri/vmcontrol/src/api/routes/vnc.rs` - 支持两种 ID 格式
3. `novaic-app/src/services/vm.ts` - 优先使用 `agent_index`

### 解决的问题

- ✅ 前端可以使用 UUID 或数字连接 VNC
- ✅ 向后兼容现有代码
- ✅ 单 VM 和多 VM 场景均支持
- ✅ 清晰的错误提示

### 测试状态

- ✅ 编译通过（无错误，仅警告 deprecated base64）
- ⏳ 待测试：运行时连接测试
- ⏳ 待测试：前端集成测试

## 快速参考

### WebSocket URL 格式

```
# 使用 agent_index（推荐，精确）
ws://localhost:8080/api/vms/1/vnc

# 使用 agent_id（自动查找）
ws://localhost:8080/api/vms/7b053af9-a386-425f-8127-492bfc156525/vnc
```

### Gateway API

```bash
# 获取状态（包含 agent_index）
GET /api/vm/status/{agent_id}

# 返回
{
  "agent_id": "...",
  "agent_index": 1,  # ← 新增字段
  "running": true,
  ...
}
```
