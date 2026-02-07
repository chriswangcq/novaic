# VNC 连接状态检测功能

## 概述

为优化虚拟机状态展示窗口，新增了 VNC 连接状态检测功能。该功能可以在前端展示 VNC 连接前，预先检测 VNC 是否可用，避免出现连接错误或空白屏幕。

## 架构

VNC 连接链路：
```
Frontend → Gateway (WebSocket proxy) → VmControl (port 8080) → QEMU Native VNC (Unix Socket)
```

### 关键组件

1. **QEMU VNC Socket**: `/tmp/novaic/novaic-vnc-{agent_id}.sock`
   - QEMU 通过 Unix Socket 暴露 VNC 接口
   - 每个 Agent 有独立的 Socket 文件

2. **VmControl Service**: `http://localhost:8080`
   - Rust 服务，负责将 Unix Socket 代理为 WebSocket
   - 提供 VNC WebSocket 端点: `ws://localhost:8080/api/vms/{agent_id}/vnc`

3. **Gateway API**: `http://localhost:8000/api/vm/vnc/status/{agent_id}`
   - 新增的 VNC 状态检测端点
   - 执行多层检测，返回详细状态信息

## API 接口

### 后端 API

**端点**: `GET /api/vm/vnc/status/{agent_id}`

**参数**:
- `agent_id`: Agent UUID

**响应**:
```json
{
  "available": true,              // VNC 是否可用
  "vm_running": true,             // VM 进程是否运行
  "vnc_socket_exists": true,      // VNC Socket 是否存在
  "vnc_socket_path": "/tmp/novaic/novaic-vnc-{agent_id}.sock",
  "vmcontrol_healthy": true,      // VmControl 服务是否健康
  "vm_registered": true,          // VM 是否在 VmControl 中注册
  "vnc_url": "ws://localhost:8080/api/vms/{agent_id}/vnc",
  "reason": "VNC ready"           // 状态说明
}
```

**检测逻辑**:
1. ✓ **VM 进程检查**: 从数据库获取 VM 进程信息，检查 PID 是否存活
2. ✓ **VNC Socket 检查**: 检查 Socket 文件是否存在（VM 启动后需要几秒创建）
3. ✓ **VmControl 健康检查**: 调用 VmControl 的 `/api/health` 端点
4. ✓ **VM 注册检查**: 调用 VmControl 的 `/api/vms` 列表，确认 VM 已注册

所有检查通过后，`available` 为 `true`。

### 前端 API

**方法**: `vmService.getVncStatus(agentId: string)`

**使用示例**:
```typescript
import { vmService } from '@/services/vm';

// 检查 VNC 状态
const status = await vmService.getVncStatus(agentId);

if (status.available) {
  // VNC 可用，可以连接
  console.log('VNC is ready:', status.vnc_url);
} else {
  // VNC 不可用，显示原因
  console.warn('VNC not available:', status.reason);
}
```

## 使用场景

### 1. VM 状态展示窗口

在显示 VM 状态时，展示 VNC 连接状态：

```typescript
const status = await vmService.getVncStatus(agentId);

// 显示状态
if (status.available) {
  showStatus('VNC: Ready ✓');
} else if (status.vm_running && !status.vnc_socket_exists) {
  showStatus('VNC: Booting...');
} else if (!status.vmcontrol_healthy) {
  showStatus('VNC: Service Unavailable');
} else {
  showStatus(`VNC: ${status.reason}`);
}
```

### 2. 定期轮询 VNC 状态

在 VNC 连接前，定期检查状态：

```typescript
useEffect(() => {
  const checkVncStatus = async () => {
    const status = await vmService.getVncStatus(agentId);
    setVncAvailable(status.available);
    setVncReason(status.reason);
  };
  
  // 立即检查一次
  checkVncStatus();
  
  // 每 5 秒检查一次
  const interval = setInterval(checkVncStatus, 5000);
  
  return () => clearInterval(interval);
}, [agentId]);
```

### 3. VNC 连接前验证

在用户点击 VNC 连接前，先验证状态：

```typescript
async function connectVnc(agentId: string) {
  // 先检查状态
  const status = await vmService.getVncStatus(agentId);
  
  if (!status.available) {
    showError(`Cannot connect to VNC: ${status.reason}`);
    return;
  }
  
  // 状态正常，打开 VNC 连接
  openVncView(status.vnc_url);
}
```

## 状态说明

### 正常状态
- **"VNC ready"**: 所有检查通过，VNC 可以连接

### 常见错误

| 原因 | 说明 | 解决方案 |
|------|------|----------|
| `VM not started` | VM 未启动 | 先启动 VM |
| `VM process not running` | VM 进程已退出 | 检查 VM 日志，重新启动 |
| `VNC socket not found (VM may still be booting)` | Socket 文件不存在 | 等待几秒，VM 启动需要时间 |
| `VmControl service not available` | VmControl 服务未运行 | 启动 VmControl 服务 |
| `VM not registered in VmControl` | VM 未在 VmControl 注册 | 重启 VmControl 或重启 VM |

## 测试

### 手动测试

使用提供的测试脚本：

```bash
# 测试特定 Agent
./test_vnc_status.sh <agent_id>

# 测试默认 Agent (test-agent-001)
./test_vnc_status.sh
```

测试脚本会显示：
- API 响应的完整 JSON
- 各项检查的结果（✓/✗）
- VNC URL 和状态原因

### API 测试

使用 curl 直接测试：

```bash
# 测试 VNC 状态
curl http://localhost:8000/api/vm/vnc/status/<agent_id> | jq

# 示例响应（VNC 可用）
{
  "available": true,
  "vm_running": true,
  "vnc_socket_exists": true,
  "vnc_socket_path": "/tmp/novaic/novaic-vnc-test-agent-001.sock",
  "vmcontrol_healthy": true,
  "vm_registered": true,
  "vnc_url": "ws://localhost:8080/api/vms/test-agent-001/vnc",
  "reason": "VNC ready"
}

# 示例响应（VM 未启动）
{
  "available": false,
  "vm_running": false,
  "vnc_socket_exists": false,
  "vnc_socket_path": "/tmp/novaic/novaic-vnc-test-agent-001.sock",
  "vmcontrol_healthy": false,
  "vm_registered": false,
  "vnc_url": "ws://localhost:8080/api/vms/test-agent-001/vnc",
  "reason": "VM not started"
}
```

## 实现细节

### 后端实现

文件: `novaic-backend/gateway/api/vm.py`

新增端点: `@router.get("/vnc/status/{agent_id}")`

关键依赖:
- `VmManager`: 获取 VM 进程信息
- `VmControlClient`: 检查 VmControl 服务状态
- `pathlib.Path`: 检查 Socket 文件存在性

### 前端实现

文件: `novaic-app/src/services/vm.ts`

新增方法: `vmService.getVncStatus(agentId: string)`

返回类型:
```typescript
{
  available: boolean;
  vm_running: boolean;
  vnc_socket_exists: boolean;
  vnc_socket_path: string;
  vmcontrol_healthy: boolean;
  vm_registered: boolean;
  vnc_url: string;
  reason: string;
}
```

## 性能考虑

### 响应时间
- VM 进程检查: < 1ms
- Socket 文件检查: < 1ms
- VmControl 健康检查: 10-50ms
- VM 列表查询: 10-100ms
- **总计**: 约 50-200ms

### 缓存策略

建议在前端实现短时间缓存（3-5 秒），避免频繁请求：

```typescript
class VncStatusCache {
  private cache = new Map<string, { status: any, timestamp: number }>();
  private TTL = 3000; // 3 seconds

  async getStatus(agentId: string): Promise<any> {
    const cached = this.cache.get(agentId);
    const now = Date.now();
    
    if (cached && now - cached.timestamp < this.TTL) {
      return cached.status;
    }
    
    const status = await vmService.getVncStatus(agentId);
    this.cache.set(agentId, { status, timestamp: now });
    return status;
  }
}
```

## 未来改进

1. **WebSocket 连接测试**: 尝试建立 WebSocket 连接，验证实际可连接性
2. **VNC 性能指标**: 添加 VNC 延迟、帧率等性能指标
3. **自动重连**: VNC 断开时自动检测并尝试重连
4. **状态变更通知**: 通过 SSE 推送 VNC 状态变更事件

## 相关文档

- [VMCONTROL_PROXY_SUMMARY.md](./VMCONTROL_PROXY_SUMMARY.md) - VmControl 代理架构
- [PHASE_4_1_VNC_INVESTIGATION_REPORT.md](./PHASE_4_1_VNC_INVESTIGATION_REPORT.md) - VNC 技术调研
- [FRONTEND_VNC_MIGRATION.md](./FRONTEND_VNC_MIGRATION.md) - 前端 VNC 迁移

## 更新日期

2026-02-06
