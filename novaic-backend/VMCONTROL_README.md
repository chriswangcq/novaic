# vmcontrol 独立启动脚本

本文档说明如何独立运行 vmcontrol 服务。

## 概述

vmcontrol 是用 Rust 编写的 VM 控制服务，提供 VNC WebSocket 支持和 VM 管理功能。它可以像其他后端组件一样独立运行。

## 文件结构

```
novaic-backend/
├── main_vmcontrol.py              # vmcontrol 独立启动脚本
├── main_novaic.py                 # 统一入口（包含 vmcontrol）
└── scripts/
    └── run_vmcontrol_dev.sh       # 开发模式启动脚本

novaic-app/src-tauri/vmcontrol/
├── src/main.rs                    # Rust 主程序（支持 --port 和 --host）
└── Cargo.toml                     # 依赖配置（包含 clap）

deployment/
└── vmcontrol.service              # systemd 服务文件
```

## 构建 vmcontrol

在使用之前，需要先构建 Rust 二进制文件：

```bash
# 开发版本
cd novaic-app/src-tauri/vmcontrol
cargo build

# 生产版本（优化构建）
cargo build --release
```

构建后的二进制文件位置：
- Debug: `novaic-app/src-tauri/vmcontrol/target/debug/vmcontrol`
- Release: `novaic-app/src-tauri/vmcontrol/target/release/vmcontrol`

## 使用方法

### 1. 通过 main_vmcontrol.py 独立运行

```bash
# 使用默认配置（端口 8080）
python3 novaic-backend/main_vmcontrol.py

# 指定端口和主机
python3 novaic-backend/main_vmcontrol.py --port 8080 --host 127.0.0.1

# 指定二进制文件路径
python3 novaic-backend/main_vmcontrol.py --binary /path/to/vmcontrol

# 设置日志级别
python3 novaic-backend/main_vmcontrol.py --log-level debug
```

### 2. 通过 main_novaic.py 统一入口运行

```bash
# 使用默认配置
python3 novaic-backend/main_novaic.py vmcontrol

# 自定义配置
python3 novaic-backend/main_novaic.py vmcontrol --port 8080 --host 127.0.0.1

# 指定二进制文件
python3 novaic-backend/main_novaic.py vmcontrol --vmcontrol-bin /path/to/vmcontrol
```

### 3. 开发模式（推荐用于开发）

```bash
# 使用开发脚本（自动使用 cargo run）
bash novaic-backend/scripts/run_vmcontrol_dev.sh
```

开发脚本会：
- 自动切换到 vmcontrol 目录
- 设置 `RUST_LOG=debug`
- 使用 `cargo run` 启动服务

### 4. 直接运行 Rust 二进制

```bash
# 运行 release 版本
./novaic-app/src-tauri/vmcontrol/target/release/vmcontrol --port 8080 --host 127.0.0.1

# 查看帮助
./novaic-app/src-tauri/vmcontrol/target/release/vmcontrol --help
```

## 命令行参数

### main_vmcontrol.py 参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--port` | 监听端口 | 8080 |
| `--host` | 绑定主机 | 127.0.0.1 |
| `--binary` | vmcontrol 二进制路径 | 自动查找 |
| `--log-level` | 日志级别（trace/debug/info/warn/error） | info |

### vmcontrol Rust 程序参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-p, --port` | 监听端口 | 8080 |
| `--host` | 绑定主机 | 127.0.0.1 |

## 环境变量

### Rust 日志配置

```bash
# 设置整体日志级别
export RUST_LOG=info

# 详细日志配置
export RUST_LOG=vmcontrol=debug,tower_http=debug,axum=debug

# Python 脚本会自动设置 RUST_LOG（通过 --log-level 参数）
```

### 服务配置（通过 common/config.py）

```bash
# vmcontrol 主机和端口
export VMCONTROL_HOST=127.0.0.1
export VMCONTROL_PORT=8080
export VMCONTROL_URL=http://127.0.0.1:8080
```

## 生产环境部署

### 使用 systemd

1. 复制服务文件：

```bash
sudo cp deployment/vmcontrol.service /etc/systemd/system/
```

2. 修改服务文件中的路径（如果需要）：

```ini
[Service]
WorkingDirectory=/opt/novaic
ExecStart=/opt/novaic/bin/vmcontrol --port 8080 --host 127.0.0.1
```

3. 启动服务：

```bash
# 重新加载 systemd 配置
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start vmcontrol

# 开机自启
sudo systemctl enable vmcontrol

# 查看状态
sudo systemctl status vmcontrol

# 查看日志
sudo journalctl -u vmcontrol -f
```

## API 端点

vmcontrol 启动后提供以下端点：

```
# Health check
GET http://127.0.0.1:8080/health

# VNC WebSocket
WS  ws://127.0.0.1:8080/api/vms/{vm_id}/vnc

# VM 管理 API
GET    http://127.0.0.1:8080/api/vms
POST   http://127.0.0.1:8080/api/vms
GET    http://127.0.0.1:8080/api/vms/{id}
DELETE http://127.0.0.1:8080/api/vms/{id}
```

## 测试验证

### 1. 检查服务是否启动

```bash
# 检查进程
ps aux | grep vmcontrol

# 检查端口
lsof -i :8080
netstat -tlnp | grep 8080
```

### 2. 测试 HTTP 端点

```bash
# Health check
curl http://127.0.0.1:8080/health

# 列出 VMs
curl http://127.0.0.1:8080/api/vms
```

### 3. 测试 WebSocket 连接

```bash
# 使用 websocat
websocat ws://127.0.0.1:8080/api/vms/test-vm/vnc

# 或使用浏览器开发者工具
```

## 故障排查

### 二进制文件未找到

```bash
# 确认文件存在
ls -l novaic-app/src-tauri/vmcontrol/target/release/vmcontrol

# 如果不存在，重新构建
cd novaic-app/src-tauri/vmcontrol
cargo build --release
```

### 端口已被占用

```bash
# 查找占用端口的进程
lsof -i :8080

# 使用不同端口
python3 novaic-backend/main_vmcontrol.py --port 8081
```

### 查看详细日志

```bash
# 开发模式（最详细）
RUST_LOG=trace cargo run --manifest-path novaic-app/src-tauri/vmcontrol/Cargo.toml -- --port 8080

# Python 脚本设置日志级别
python3 novaic-backend/main_vmcontrol.py --log-level trace
```

### 权限问题

```bash
# 确保脚本可执行
chmod +x novaic-backend/main_vmcontrol.py
chmod +x novaic-backend/scripts/run_vmcontrol_dev.sh

# 确保二进制文件可执行
chmod +x novaic-app/src-tauri/vmcontrol/target/release/vmcontrol
```

## 与其他服务集成

vmcontrol 通常与其他 NovAIC 后端服务一起运行：

```bash
# 启动所有服务（由 Tauri 自动管理）
# Gateway (19999)
# Tools Server (19998)
# Queue Service (19997)
# Workers (watchdog, task-worker, saga-worker, health)
# vmcontrol (8080)

# Gateway 会调用 vmcontrol 的 API
# 前端通过 Gateway 代理访问 vmcontrol
```

## 开发指南

### 修改 Rust 代码

```bash
# 1. 编辑代码
vim novaic-app/src-tauri/vmcontrol/src/main.rs

# 2. 运行测试（如果有）
cd novaic-app/src-tauri/vmcontrol
cargo test

# 3. 运行开发服务器
cargo run -- --port 8080

# 4. 或使用开发脚本
bash novaic-backend/scripts/run_vmcontrol_dev.sh
```

### 添加新的命令行参数

1. 在 `src/main.rs` 中的 `Args` 结构体添加字段
2. 在 `main_vmcontrol.py` 中添加对应参数
3. 更新本文档

### 添加新的 API 端点

修改 `novaic-app/src-tauri/vmcontrol/src/api/routes.rs`

## 配置示例

### 开发环境

```bash
export RUST_LOG=debug
python3 novaic-backend/main_vmcontrol.py --port 8080 --host 127.0.0.1 --log-level debug
```

### 测试环境

```bash
export RUST_LOG=info
python3 novaic-backend/main_vmcontrol.py --port 8080 --host 0.0.0.0
```

### 生产环境

使用 systemd 服务，配置文件见 `deployment/vmcontrol.service`

## 相关文档

- [PHASE_4_1_README.md](../PHASE_4_1_README.md) - Phase 4.1 完整文档
- [VNC_WEBSOCKET_IMPLEMENTATION_COMPLETE.md](../VNC_WEBSOCKET_IMPLEMENTATION_COMPLETE.md) - VNC WebSocket 实现
- [novaic-app/src-tauri/vmcontrol/README.md](../novaic-app/src-tauri/vmcontrol/README.md) - vmcontrol Rust 代码文档

## 总结

vmcontrol 现在可以：

✅ 独立启动（通过 `main_vmcontrol.py`）
✅ 集成到 `main_novaic.py` 统一入口
✅ 支持命令行参数（`--port`, `--host`）
✅ 支持开发模式（`run_vmcontrol_dev.sh`）
✅ 支持生产部署（systemd 服务）
✅ 自动查找二进制文件
✅ 完善的日志配置
✅ 与其他后端服务一致的启动方式
