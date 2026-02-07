# VNC 状态检测 - 快速参考

## API 端点

```bash
GET /api/vm/vnc/status/{agent_id}
```

## 前端使用

```typescript
import { vmService } from '@/services/vm';

// 检查 VNC 状态
const status = await vmService.getVncStatus(agentId);

if (status.available) {
  // VNC 可用
} else {
  console.warn('VNC not available:', status.reason);
}
```

## 响应字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `available` | boolean | VNC 是否可用 |
| `vm_running` | boolean | VM 进程是否运行 |
| `vnc_socket_exists` | boolean | VNC Socket 是否存在 |
| `vnc_socket_path` | string | Socket 文件路径 |
| `vmcontrol_healthy` | boolean | VmControl 是否健康 |
| `vm_registered` | boolean | VM 是否已注册 |
| `vnc_url` | string | VNC WebSocket URL |
| `reason` | string | 状态说明 |

## 检测流程

1. ✓ VM 进程运行 → 2
2. ✓ VNC Socket 存在 → 3
3. ✓ VmControl 健康 → 4
4. ✓ VM 已注册 → **可用**

任意步骤失败 → **不可用**

## 常见状态

| 状态 | 原因 | 处理 |
|------|------|------|
| ✓ VNC ready | 全部正常 | 可以连接 |
| ✗ VM not started | VM 未启动 | 启动 VM |
| ✗ VNC socket not found | VM 启动中 | 等待几秒 |
| ✗ VmControl not available | 服务未运行 | 启动 VmControl |
| ✗ VM not registered | 未注册 | 重启服务 |

## 测试

```bash
# 快速测试
curl http://localhost:8000/api/vm/vnc/status/<agent_id> | jq

# 使用测试脚本
./test_vnc_status.sh <agent_id>
```

## 使用示例

### 状态轮询

```typescript
useEffect(() => {
  const interval = setInterval(async () => {
    const status = await vmService.getVncStatus(agentId);
    setVncAvailable(status.available);
  }, 5000); // 每 5 秒
  
  return () => clearInterval(interval);
}, [agentId]);
```

### 连接前验证

```typescript
async function connectVnc() {
  const status = await vmService.getVncStatus(agentId);
  if (!status.available) {
    showError(status.reason);
    return;
  }
  openVnc(status.vnc_url);
}
```

## 文件位置

- **后端 API**: `novaic-backend/gateway/api/vm.py`
- **前端服务**: `novaic-app/src/services/vm.ts`
- **测试脚本**: `test_vnc_status.sh`
- **完整文档**: `VNC_STATUS_DETECTION.md`
