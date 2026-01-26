# NovAIC VM

> QEMU Linux 虚拟机，为 AI 提供完整的桌面环境

NovAIC VM 是一个预配置的 Ubuntu 虚拟机，内置桌面环境和 MCP Server，让 AI 可以像人一样操作计算机。

## 系统要求

- **操作系统**: macOS (Apple Silicon 或 Intel)
- **内存**: 8GB+ (VM 使用 4GB)
- **磁盘**: 50GB+ 可用空间
- **软件**: Homebrew

## 快速开始

### 1. 一键安装

```bash
cd novaic-vm
./setup.sh
```

这会自动：
- 安装 QEMU 和依赖
- 下载 Ubuntu Cloud Image
- 创建并启动虚拟机

### 2. 等待系统配置

首次启动需要 5-10 分钟完成 cloud-init 配置。

检查进度：
```bash
ssh -p 2222 ubuntu@localhost
# 密码: ubuntu
tail -f /var/log/cloud-init-output.log
```

### 3. 部署 MCP Server

```bash
./scripts/deploy.sh
```

### 4. 连接使用

| 服务 | 地址 | 凭证 |
|------|------|------|
| VNC | `vnc://localhost:5900` | 密码: `novaic` |
| SSH | `ssh -p 2222 ubuntu@localhost` | 密码: `ubuntu` |
| MCP | `http://localhost:8081/sse` | - |

## 管理命令

```bash
# 启动 VM
./scripts/start-vm.sh

# 后台启动
./scripts/start-vm.sh -d

# 停止 VM
./scripts/stop-vm.sh

# 查看状态
./scripts/status-vm.sh

# 部署/更新 MCP Server
./scripts/deploy.sh
```

## 配置选项

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `NOVAIC_VM_MEMORY` | 4096 | VM 内存 (MB) |
| `NOVAIC_VM_CPUS` | 4 | VM CPU 核心数 |
| `NOVAIC_VNC_PORT` | 5900 | VNC 端口 |
| `NOVAIC_MCP_PORT` | 8081 | MCP Server 端口 |
| `NOVAIC_SSH_PORT` | 2222 | SSH 端口 |

### 自定义镜像源

```bash
export UBUNTU_MIRROR="https://mirrors.tuna.tsinghua.edu.cn/ubuntu-cloud-images"
./scripts/create-vm.sh
```

## 在 Cursor 中使用

配置 `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "novaic": {
      "url": "http://localhost:8081/sse"
    }
  }
}
```

然后就可以让 AI 使用以下工具：

- `screenshot` - 截取屏幕
- `mouse` - 鼠标操作
- `keyboard` - 键盘输入
- `browser_navigate` - 浏览器导航
- `run_command` - 执行命令
- ... 共 44+ 工具

## 目录结构

```
novaic-vm/
├── setup.sh              # 一键安装脚本
├── scripts/
│   ├── create-vm.sh      # 创建 VM
│   ├── start-vm.sh       # 启动 VM
│   ├── stop-vm.sh        # 停止 VM
│   ├── status-vm.sh      # 查看状态
│   └── deploy.sh         # 部署 MCP Server
├── config/
│   ├── cloud-init.yaml   # cloud-init 配置 (可选自定义)
│   ├── user-data         # 生成的 user-data
│   └── meta-data         # 生成的 meta-data
├── images/               # VM 磁盘镜像
├── iso/                  # Ubuntu Cloud Image 和 seed ISO
├── firmware/             # UEFI 固件 (ARM64)
└── docs/                 # 文档
```

## 故障排查

### VNC 黑屏

```bash
ssh -p 2222 ubuntu@localhost
sudo systemctl restart lightdm
sudo systemctl restart x11vnc
```

### MCP Server 无法连接

```bash
ssh -p 2222 ubuntu@localhost
sudo systemctl status novaic
sudo journalctl -u novaic -f
```

### 重新创建 VM

```bash
./scripts/stop-vm.sh
rm -rf images/ iso/cloud-init-seed.iso
./scripts/create-vm.sh
./scripts/start-vm.sh
```

## 架构说明

```
┌─────────────────────────────────────────────────────────────┐
│  macOS 宿主机                                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  QEMU VM (Ubuntu 24.04)                             │   │
│  │                                                     │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │   │
│  │  │   XFCE4     │  │   x11vnc    │  │  novaic    │  │   │
│  │  │  Desktop    │  │  :5901      │  │  MCP:8080  │  │   │
│  │  └─────────────┘  └─────────────┘  └────────────┘  │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│         ↑                  ↑                 ↑              │
│    SSH:2222           VNC:5900          MCP:8081           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Cursor IDE + AI                                    │   │
│  │  → MCP Client → http://localhost:8081/sse          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## License

MIT
