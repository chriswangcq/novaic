# vmcontrol 启动指南

本文档提供 vmcontrol 服务的快速启动指南和验证步骤。

## 快速开始

### 第一步：构建 vmcontrol

```bash
cd novaic-app/src-tauri/vmcontrol
cargo build --release
```

构建完成后，二进制文件位于：
```
novaic-app/src-tauri/vmcontrol/target/release/vmcontrol
```

### 第二步：选择启动方式

#### 方式 1：使用 Python 启动脚本（推荐）

```bash
# 使用默认配置（端口 8080）
python3 novaic-backend/main_vmcontrol.py

# 自定义端口和主机
python3 novaic-backend/main_vmcontrol.py --port 8080 --host 127.0.0.1

# 设置日志级别
python3 novaic-backend/main_vmcontrol.py --log-level debug

# 指定二进制文件路径
python3 novaic-backend/main_vmcontrol.py --binary /path/to/vmcontrol
```

#### 方式 2：使用统一入口

```bash
# 通过 main_novaic.py 启动
python3 novaic-backend/main_novaic.py vmcontrol --port 8080 --host 127.0.0.1

# 查看帮助
python3 novaic-backend/main_novaic.py vmcontrol --help
```

#### 方式 3：开发模式（推荐用于开发）

```bash
# 使用开发脚本（会自动使用 cargo run）
bash novaic-backend/scripts/run_vmcontrol_dev.sh
```

#### 方式 4：直接运行 Rust 二进制

```bash
# 运行 release 版本
./novaic-app/src-tauri/vmcontrol/target/release/vmcontrol --port 8080 --host 127.0.0.1

# 使用环境变量设置日志级别
RUST_LOG=debug ./novaic-app/src-tauri/vmcontrol/target/release/vmcontrol --port 8080
```

## 验证步骤

### 1. 运行测试脚本（推荐）

```bash
bash novaic-backend/scripts/test_vmcontrol.sh
```

测试脚本会自动：
- ✅ 检查二进制文件是否存在
- ✅ 检查端口是否可用
- ✅ 启动 vmcontrol 服务
- ✅ 测试 HTTP 端点
- ✅ 测试 WebSocket 端点
- ✅ 验证 Python 脚本

### 2. 手动验证

#### 2.1 检查服务是否运行

```bash
# 检查进程
ps aux | grep vmcontrol

# 检查端口
lsof -i :8080
# 或
netstat -tlnp | grep 8080
```

#### 2.2 测试 HTTP 端点

```bash
# Health check
curl http://127.0.0.1:8080/health

# 应该返回: {"status":"ok"}

# 列出 VMs
curl http://127.0.0.1:8080/api/vms

# 应该返回 JSON 数组
```

#### 2.3 测试 WebSocket（如果安装了 websocat）

```bash
# 安装 websocat（如果还没有）
cargo install websocat
# 或
brew install websocat

# 测试 WebSocket 连接
websocat ws://127.0.0.1:8080/api/vms/test-vm/vnc
```

## 启动命令对比

| 方式 | 命令 | 适用场景 |
|------|------|----------|
| Python 脚本 | `python3 novaic-backend/main_vmcontrol.py` | 生产环境、自动化部署 |
| 统一入口 | `python3 novaic-backend/main_novaic.py vmcontrol` | 与其他服务集成 |
| 开发脚本 | `bash novaic-backend/scripts/run_vmcontrol_dev.sh` | 开发调试 |
| 直接运行 | `./target/release/vmcontrol --port 8080` | 性能测试、最小依赖 |

## 配置参数

### 环境变量

```bash
# Rust 日志级别（trace, debug, info, warn, error）
export RUST_LOG=info

# 详细的日志配置
export RUST_LOG=vmcontrol=debug,tower_http=debug,axum=info

# 服务配置（通过 common/config.py）
export VMCONTROL_HOST=127.0.0.1
export VMCONTROL_PORT=8080
export VMCONTROL_URL=http://127.0.0.1:8080
```

### 命令行参数

```bash
# Python 脚本参数
--port PORT          # 监听端口（默认：8080）
--host HOST          # 绑定主机（默认：127.0.0.1）
--binary PATH        # vmcontrol 二进制路径（默认：自动查找）
--log-level LEVEL    # 日志级别（默认：info）

# Rust 程序参数
-p, --port PORT      # 监听端口（默认：8080）
--host HOST          # 绑定主机（默认：127.0.0.1）
```

## API 端点

vmcontrol 启动后提供以下端点：

### HTTP 端点

```
GET  /health                  # 健康检查
GET  /api/vms                 # 列出所有 VMs
POST /api/vms                 # 创建新 VM
GET  /api/vms/{id}           # 获取 VM 详情
DELETE /api/vms/{id}         # 删除 VM
```

### WebSocket 端点

```
WS   /api/vms/{id}/vnc       # VNC WebSocket 连接
```

## 故障排查

### 问题 1: 二进制文件未找到

```bash
# 症状
[vmcontrol] ERROR: vmcontrol binary not found

# 解决方案
cd novaic-app/src-tauri/vmcontrol
cargo build --release

# 验证
ls -l target/release/vmcontrol
```

### 问题 2: 端口被占用

```bash
# 症状
Error: Address already in use (os error 48)

# 查找占用进程
lsof -i :8080

# 解决方案 1: 杀死进程
kill -9 <PID>

# 解决方案 2: 使用不同端口
python3 novaic-backend/main_vmcontrol.py --port 8081
```

### 问题 3: 权限问题

```bash
# 症状
Permission denied

# 解决方案
chmod +x novaic-backend/main_vmcontrol.py
chmod +x novaic-backend/scripts/run_vmcontrol_dev.sh
chmod +x novaic-app/src-tauri/vmcontrol/target/release/vmcontrol
```

### 问题 4: 无法连接服务

```bash
# 检查服务是否运行
ps aux | grep vmcontrol

# 检查端口是否监听
lsof -i :8080

# 查看日志
tail -f /tmp/vmcontrol.log

# 或使用更详细的日志级别
RUST_LOG=trace python3 novaic-backend/main_vmcontrol.py
```

## 与其他服务集成

vmcontrol 通常作为 NovAIC 后端服务的一部分运行：

```
服务架构:
┌─────────────────────────────────────────┐
│           NovAIC Backend                │
├─────────────────────────────────────────┤
│ Gateway         (19999) - API + DB      │
│ Tools Server    (19998) - Tools API     │
│ Queue Service   (19997) - Task Queue    │
│ vmcontrol       (8080)  - VM Control    │
│ Workers                 - Task Exec     │
└─────────────────────────────────────────┘
```

### 启动所有服务

```bash
# 1. 启动 Gateway
python3 novaic-backend/main_novaic.py gateway --port 19999 &

# 2. 启动 Tools Server
python3 novaic-backend/main_novaic.py tools-server --port 19998 &

# 3. 启动 Queue Service
python3 novaic-backend/main_novaic.py queue-service --port 19997 &

# 4. 启动 vmcontrol
python3 novaic-backend/main_novaic.py vmcontrol --port 8080 &

# 5. 启动 Workers
python3 novaic-backend/main_novaic.py watchdog &
python3 novaic-backend/main_novaic.py task-worker &
python3 novaic-backend/main_novaic.py saga-worker &
python3 novaic-backend/main_novaic.py health &
```

### 通过 Tauri 自动启动

在 Tauri 应用中，所有服务会自动启动。vmcontrol 的配置在：

```
novaic-app/src-tauri/tauri.conf.json
novaic-app/src/config/index.ts
```

## 生产环境部署

### 使用 systemd（Linux）

```bash
# 1. 复制服务文件
sudo cp deployment/vmcontrol.service /etc/systemd/system/

# 2. 编辑服务文件（如果需要）
sudo vim /etc/systemd/system/vmcontrol.service

# 3. 重新加载 systemd
sudo systemctl daemon-reload

# 4. 启动服务
sudo systemctl start vmcontrol

# 5. 设置开机自启
sudo systemctl enable vmcontrol

# 6. 查看状态
sudo systemctl status vmcontrol

# 7. 查看日志
sudo journalctl -u vmcontrol -f
```

### 使用 Docker（可选）

```dockerfile
# Dockerfile 示例
FROM rust:1.75 as builder
WORKDIR /app
COPY novaic-app/src-tauri/vmcontrol .
RUN cargo build --release

FROM debian:bookworm-slim
COPY --from=builder /app/target/release/vmcontrol /usr/local/bin/
EXPOSE 8080
CMD ["vmcontrol", "--port", "8080", "--host", "0.0.0.0"]
```

```bash
# 构建镜像
docker build -t vmcontrol:latest -f deployment/Dockerfile.vmcontrol .

# 运行容器
docker run -d -p 8080:8080 --name vmcontrol vmcontrol:latest
```

## 性能优化

### 1. 使用 Release 构建

```bash
# Release 构建（优化）
cargo build --release

# 比 Debug 构建快 10-100 倍
```

### 2. 调整日志级别

```bash
# 生产环境使用 info 或 warn
export RUST_LOG=warn

# 开发环境使用 debug
export RUST_LOG=debug
```

### 3. 资源限制（systemd）

```ini
[Service]
# 限制内存
MemoryMax=1G

# 限制 CPU
CPUQuota=50%

# 限制文件描述符
LimitNOFILE=65535
```

## 监控和日志

### 日志位置

```
开发模式:
  - 标准输出/错误
  - /tmp/vmcontrol.log

生产模式 (systemd):
  - journalctl -u vmcontrol

Tauri 集成:
  - $NOVAIC_DATA_DIR/logs/vmcontrol-YYYYMMDD.log
```

### 监控指标

```bash
# 进程状态
ps aux | grep vmcontrol

# 内存使用
top -p $(pgrep vmcontrol)

# 网络连接
netstat -tnp | grep vmcontrol

# HTTP 请求
curl http://127.0.0.1:8080/health
```

## 下一步

- 阅读完整文档：[VMCONTROL_README.md](novaic-backend/VMCONTROL_README.md)
- 查看 API 文档：[novaic-app/src-tauri/vmcontrol/README.md](novaic-app/src-tauri/vmcontrol/README.md)
- 了解 VNC 实现：[VNC_WEBSOCKET_IMPLEMENTATION_COMPLETE.md](VNC_WEBSOCKET_IMPLEMENTATION_COMPLETE.md)
- 运行测试：`bash novaic-backend/scripts/test_vmcontrol.sh`

## 文件清单

创建的文件：

```
✅ novaic-backend/main_vmcontrol.py              # Python 启动脚本
✅ novaic-backend/scripts/run_vmcontrol_dev.sh   # 开发模式脚本
✅ novaic-backend/scripts/test_vmcontrol.sh      # 测试验证脚本
✅ deployment/vmcontrol.service                  # systemd 服务文件
✅ novaic-backend/VMCONTROL_README.md            # 详细文档
✅ VMCONTROL_STARTUP_GUIDE.md                    # 本启动指南
```

修改的文件：

```
✅ novaic-app/src-tauri/vmcontrol/src/main.rs    # 添加命令行参数支持
✅ novaic-app/src-tauri/vmcontrol/Cargo.toml     # 添加 clap 依赖
✅ novaic-backend/main_novaic.py                 # 添加 vmcontrol 模式
```

## 完成标准检查

- ✅ `main_vmcontrol.py` 启动脚本创建
- ✅ vmcontrol 支持命令行参数（`--port`, `--host`）
- ✅ 开发模式脚本创建（`run_vmcontrol_dev.sh`）
- ✅ 集成到 `main_novaic.py`
- ✅ systemd 服务文件创建
- ✅ 可执行权限设置
- ✅ 测试脚本创建
- ✅ 文档完善

全部完成！🎉
