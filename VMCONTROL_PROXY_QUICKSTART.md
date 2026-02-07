# VmControl 代理快速开始

## 📦 新增功能

Gateway 现在可以代理 vmcontrol 服务（Rust），提供统一的 API 入口。

## 🚀 快速开始

### 1. 启动服务

```bash
# 启动 vmcontrol（如果还没运行）
cd novaic-app/src-tauri/vmcontrol
cargo run --release

# 启动 Gateway
cd novaic-backend
python main_gateway.py
```

### 2. 验证服务

```bash
# 运行测试脚本
./test_vmcontrol_proxy.sh

# 或手动测试
curl http://127.0.0.1:19999/api/health
curl http://127.0.0.1:19999/api/vmcontrol/health
```

## 📡 API 端点

### REST API

```bash
# 获取 VM 列表
GET /api/vmcontrol/vms

# 获取 VM 信息
GET /api/vmcontrol/vms/{vm_id}

# 截图
POST /api/vmcontrol/vms/{vm_id}/screenshot

# 发送按键
POST /api/vmcontrol/vms/{vm_id}/keys
Body: {"keys": "ret"}

# 鼠标操作
POST /api/vmcontrol/vms/{vm_id}/mouse/move
Body: {"x": 100, "y": 200}

POST /api/vmcontrol/vms/{vm_id}/mouse/click
Body: {"button": "left"}

# 健康检查
GET /api/vmcontrol/health
```

### WebSocket

```javascript
// VNC 连接
const ws = new WebSocket('ws://127.0.0.1:19999/api/vmcontrol/vms/{vm_id}/vnc');
```

## 🔧 配置

默认配置在 `novaic-backend/common/config.py`：

```python
VMCONTROL_HOST = "127.0.0.1"
VMCONTROL_PORT = 8080
VMCONTROL_URL = "http://127.0.0.1:8080"
```

通过环境变量覆盖：

```bash
export VMCONTROL_HOST="192.168.1.100"
export VMCONTROL_PORT="9090"
# 或
export VMCONTROL_URL="http://192.168.1.100:9090"
```

## 📂 文件结构

```
novaic-backend/
├── gateway/
│   ├── clients/
│   │   ├── __init__.py          # 新增
│   │   └── vmcontrol.py         # 新增 - 客户端
│   └── api/
│       ├── vmcontrol.py         # 新增 - 代理 API
│       ├── routes.py            # 修改 - 健康检查
│       └── schemas.py           # 修改 - HealthResponse
└── main_gateway.py              # 修改 - 注册路由
```

## 🧪 测试

### 自动测试

```bash
./test_vmcontrol_proxy.sh
```

### 手动测试

```bash
# 1. 健康检查
curl http://127.0.0.1:19999/api/vmcontrol/health

# 2. VM 列表
curl http://127.0.0.1:19999/api/vmcontrol/vms

# 3. WebSocket (需要 wscat)
npm install -g wscat
wscat -c ws://127.0.0.1:19999/api/vmcontrol/vms/{vm_id}/vnc
```

## 🐛 故障排查

### vmcontrol 服务未运行

**症状：**
- `curl http://127.0.0.1:19999/api/vmcontrol/health` 返回 unhealthy
- Gateway 健康检查显示 `vmcontrol_healthy: false`

**解决：**
```bash
# 启动 vmcontrol
cd novaic-app/src-tauri/vmcontrol
cargo run --release
```

### WebSocket 连接失败

**症状：**
- WebSocket 连接立即关闭（code 1011）

**解决：**
1. 确认 vmcontrol 服务运行：`curl http://127.0.0.1:8080/api/health`
2. 确认 VM ID 正确：`curl http://127.0.0.1:19999/api/vmcontrol/vms`
3. 检查日志：`~/.novaic/logs/gateway-*.log`

### 端口冲突

**症状：**
- 服务启动失败，提示端口占用

**解决：**
```bash
# 检查端口占用
lsof -i :8080  # vmcontrol
lsof -i :19999 # gateway

# 修改端口
export VMCONTROL_PORT=8081
export GATEWAY_PORT=20000
```

## 📖 更多文档

- 完整实现报告：[GATEWAY_VMCONTROL_PROXY_IMPLEMENTATION.md](./GATEWAY_VMCONTROL_PROXY_IMPLEMENTATION.md)
- API 文档：http://127.0.0.1:19999/docs

## ✅ 验证清单

- [ ] Gateway 启动成功
- [ ] VmControl 服务运行
- [ ] 健康检查返回正常
- [ ] VM 列表可以获取
- [ ] WebSocket 可以连接
- [ ] 前端可以显示 VNC

---

**实现日期：** 2026-02-06  
**版本：** v0.3.0
