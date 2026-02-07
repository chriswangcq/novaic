# vmcontrol 快速参考

## 一行命令启动

```bash
# 方式 1: Python 脚本（推荐）
python3 novaic-backend/main_vmcontrol.py

# 方式 2: 统一入口
python3 novaic-backend/main_novaic.py vmcontrol

# 方式 3: 开发模式
bash novaic-backend/scripts/run_vmcontrol_dev.sh

# 方式 4: 直接运行
./novaic-app/src-tauri/vmcontrol/target/release/vmcontrol --port 8080
```

## 构建

```bash
cd novaic-app/src-tauri/vmcontrol
cargo build --release
```

## 测试

```bash
# 自动化测试
bash novaic-backend/scripts/test_vmcontrol.sh

# 手动测试
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/vms
```

## 常用参数

```bash
--port 8080              # 端口
--host 127.0.0.1         # 主机
--log-level debug        # 日志级别
--binary /path/to/bin    # 二进制路径
```

## 环境变量

```bash
export RUST_LOG=debug
export VMCONTROL_PORT=8080
export VMCONTROL_HOST=127.0.0.1
```

## API 端点

```
GET  /health                  # 健康检查
GET  /api/vms                 # 列出 VMs
POST /api/vms                 # 创建 VM
WS   /api/vms/{id}/vnc       # VNC WebSocket
```

## 故障排查

```bash
# 检查进程
ps aux | grep vmcontrol

# 检查端口
lsof -i :8080

# 查看日志
RUST_LOG=debug python3 novaic-backend/main_vmcontrol.py
```

## 文件位置

```
novaic-backend/main_vmcontrol.py              # 启动脚本
novaic-backend/scripts/run_vmcontrol_dev.sh   # 开发脚本
novaic-backend/scripts/test_vmcontrol.sh      # 测试脚本
deployment/vmcontrol.service                  # systemd 服务
```

## 完整文档

- [VMCONTROL_STARTUP_GUIDE.md](VMCONTROL_STARTUP_GUIDE.md) - 启动指南
- [novaic-backend/VMCONTROL_README.md](novaic-backend/VMCONTROL_README.md) - 完整文档
- [VMCONTROL_INDEPENDENT_STARTUP_COMPLETE.md](VMCONTROL_INDEPENDENT_STARTUP_COMPLETE.md) - 完成报告
