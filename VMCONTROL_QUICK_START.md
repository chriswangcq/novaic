# VMControl 快速开始指南

## 🚀 快速启动

### 1. 构建 vmcontrol (首次使用)

```bash
cd novaic-app/src-tauri/vmcontrol
cargo build --release
```

### 2. 启动服务

```bash
cd novaic-backend

# 方式 1: 使用默认配置 (127.0.0.1:8080)
python3 main_novaic.py vmcontrol

# 方式 2: 自定义端口
python3 main_novaic.py vmcontrol --port 9090

# 方式 3: 查看帮助
python3 main_novaic.py vmcontrol --help
```

### 3. 验证服务

```bash
# 健康检查
curl http://127.0.0.1:8080/api/health

# 获取 VM 列表
curl http://127.0.0.1:8080/api/vms
```

## 📋 常用命令

### 启动选项

```bash
# 默认配置
python3 main_novaic.py vmcontrol

# 自定义端口和主机
python3 main_novaic.py vmcontrol --port 8080 --host 127.0.0.1

# 指定二进制路径
python3 main_novaic.py vmcontrol --vmcontrol-bin /path/to/vmcontrol
```

### 环境变量

```bash
# 设置默认端口
export VMCONTROL_PORT=9090
export VMCONTROL_HOST=0.0.0.0

# 设置日志级别
export RUST_LOG=vmcontrol=debug

# 运行
python3 main_novaic.py vmcontrol
```

### 测试命令

```bash
# 运行完整测试套件
./test-vmcontrol-service.sh

# 手动测试健康端点
curl -v http://127.0.0.1:8080/api/health

# 测试 VM 列表端点
curl -v http://127.0.0.1:8080/api/vms

# 测试 VNC WebSocket (需要 websocat 或浏览器)
websocat ws://127.0.0.1:8080/api/vms/{vm-id}/vnc
```

## 🔧 配置说明

### 端口配置

| 方式 | 优先级 | 示例 |
|------|--------|------|
| 命令行参数 | 最高 | `--port 9090` |
| 环境变量 | 中等 | `export VMCONTROL_PORT=9090` |
| 默认值 | 最低 | `8080` |

### 日志配置

```bash
# 最小日志 (仅错误)
export RUST_LOG=error

# 标准日志 (推荐)
export RUST_LOG=vmcontrol=info,tower_http=debug

# 详细日志 (调试)
export RUST_LOG=vmcontrol=debug,tower_http=trace

# 完整日志 (开发)
export RUST_LOG=trace
```

## 🐛 故障排除

### 服务无法启动

**问题**: `vmcontrol binary not found`

**解决**:
```bash
# 检查二进制是否存在
ls -la novaic-app/src-tauri/target/release/vmcontrol

# 如果不存在，重新构建
cd novaic-app/src-tauri/vmcontrol
cargo build --release
```

---

**问题**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8080

# 杀死进程或使用其他端口
python3 main_novaic.py vmcontrol --port 9090
```

### 服务无响应

**问题**: 健康检查超时

**检查步骤**:
```bash
# 1. 检查服务是否运行
ps aux | grep vmcontrol

# 2. 检查端口是否监听
lsof -i :8080
netstat -an | grep 8080

# 3. 查看日志
tail -f /tmp/vmcontrol-test.log

# 4. 测试连接
curl -v http://127.0.0.1:8080/api/health
```

### 无法优雅关闭

**问题**: Ctrl+C 后进程仍在运行

**解决**:
```bash
# 查找进程
ps aux | grep vmcontrol

# 强制终止
kill -9 <PID>

# 或批量终止
pkill -9 vmcontrol
```

## 📊 性能监控

### 检查资源使用

```bash
# CPU 和内存使用
ps aux | grep vmcontrol

# 详细监控
top -pid $(pgrep vmcontrol)

# 端口和连接
lsof -i :8080
```

### 日志监控

```bash
# 实时查看日志 (服务前台运行时)
python3 main_novaic.py vmcontrol

# 后台运行时的日志
python3 main_novaic.py vmcontrol > vmcontrol.log 2>&1 &
tail -f vmcontrol.log
```

## 🔒 安全建议

### 生产环境配置

```bash
# 仅监听本地 (默认，推荐)
python3 main_novaic.py vmcontrol --host 127.0.0.1

# 监听所有接口 (谨慎使用)
python3 main_novaic.py vmcontrol --host 0.0.0.0

# 使用非标准端口
python3 main_novaic.py vmcontrol --port 18080
```

### 防火墙规则

```bash
# 仅允许本地访问 (推荐)
# 无需配置防火墙，127.0.0.1 默认不可外部访问

# 如需远程访问，限制来源 IP
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

## 📚 API 端点参考

### 核心端点

```bash
# 健康检查
GET /api/health
# 响应: {"status":"ok"}

# VM 列表
GET /api/vms
# 响应: {"vms":[...]}

# VM 状态
GET /api/vms/{id}/status
# 响应: {"id":"...", "status":"running"}

# 启动 VM
POST /api/vms/{id}/start
# 响应: {"success":true}

# 停止 VM
POST /api/vms/{id}/stop
# 响应: {"success":true}

# VNC WebSocket
WS /api/vms/{id}/vnc
# 协议: VNC over WebSocket
```

### 使用示例

```bash
# 使用 curl
curl http://127.0.0.1:8080/api/health
curl http://127.0.0.1:8080/api/vms
curl -X POST http://127.0.0.1:8080/api/vms/vm1/start

# 使用 httpie (更友好)
http GET http://127.0.0.1:8080/api/health
http GET http://127.0.0.1:8080/api/vms
http POST http://127.0.0.1:8080/api/vms/vm1/start

# 使用 Python
import requests
response = requests.get('http://127.0.0.1:8080/api/health')
print(response.json())
```

## 🔄 与其他服务集成

### 架构概览

```
┌─────────────────────────────────────────────────┐
│                   Tauri 主进程                   │
└─────────┬───────────────────────────────────────┘
          │
          ├── Gateway (19999)
          ├── Tools Server (19998)
          ├── Queue Service (19997)
          ├── Watchdog
          ├── Task Worker
          ├── Saga Worker
          ├── Health Worker
          └── VMControl (8080) ← 新增
```

### 服务间通信

```python
# Gateway 调用 VMControl
import httpx

VMCONTROL_URL = "http://127.0.0.1:8080"

async def get_vms():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{VMCONTROL_URL}/api/vms")
        return response.json()
```

## 📖 相关文档

- [完整集成报告](VMCONTROL_SERVICE_INTEGRATION.md)
- [API 文档](novaic-app/src-tauri/vmcontrol/API.md)
- [VNC WebSocket 文档](novaic-app/src-tauri/vmcontrol/VNC_WEBSOCKET_PROXY.md)
- [Guest Agent 文档](novaic-app/src-tauri/vmcontrol/GUEST_AGENT_README.md)

## 💡 最佳实践

1. **开发环境**: 使用 debug 构建和详细日志
   ```bash
   export RUST_LOG=debug
   cargo build
   python3 main_novaic.py vmcontrol --vmcontrol-bin target/debug/vmcontrol
   ```

2. **生产环境**: 使用 release 构建和适当日志级别
   ```bash
   export RUST_LOG=info
   cargo build --release
   python3 main_novaic.py vmcontrol
   ```

3. **测试环境**: 使用自动化测试脚本
   ```bash
   ./test-vmcontrol-service.sh
   ```

4. **监控**: 配置健康检查和告警
   ```bash
   # 简单监控脚本
   while true; do
       curl -f http://127.0.0.1:8080/api/health || echo "Service down!"
       sleep 30
   done
   ```

## ❓ 常见问题

**Q: 如何修改默认端口？**

A: 三种方式:
- 命令行: `--port 9090`
- 环境变量: `export VMCONTROL_PORT=9090`
- 配置文件: 修改 `common/config.py`

**Q: 服务启动很慢怎么办？**

A: 
- 使用 release 构建 (更快)
- 检查网络连接 (健康检查)
- 查看日志定位问题

**Q: 如何同时运行多个实例？**

A: 使用不同端口:
```bash
python3 main_novaic.py vmcontrol --port 8080 &
python3 main_novaic.py vmcontrol --port 8081 &
```

**Q: 如何集成到 systemd？**

A: 创建 service 文件:
```ini
[Unit]
Description=NovAIC VMControl Service
After=network.target

[Service]
Type=simple
User=novaic
ExecStart=/usr/bin/python3 /path/to/novaic-backend/main_novaic.py vmcontrol
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## 🎯 总结

VMControl 服务现已完全集成到 novaic-backend 统一架构中，提供了：

✅ 统一的启动和管理方式  
✅ 灵活的配置选项  
✅ 完善的健康检查  
✅ 优雅的关闭机制  
✅ 丰富的文档和测试工具  

开始使用: `python3 main_novaic.py vmcontrol`
