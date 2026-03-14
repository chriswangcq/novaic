# NovAIC

AI-powered agent platform with mobile (iOS/Android) and desktop (macOS/Windows/Linux) clients.

## Architecture

```
novaic/
├── novaic-app/                  # Tauri v2 前端 (React + TypeScript)
├── novaic-agent-runtime/        # Agent 运行时
├── novaic-gateway/              # API 网关
├── novaic-runtime-orchestrator/ # 运行时编排器
├── novaic-control-plane/        # 控制面板
├── novaic-contracts/            # 共享协议/类型定义
├── novaic-shared-kernel/        # 共享核心库
├── novaic-shared-runtime-common/# 共享运行时公共库
├── novaic-storage-a/            # 存储服务 A
├── novaic-storage-b/            # 存储服务 B
├── novaic-tools-server/         # 工具服务
├── novaic-mcp-vmuse/            # MCP VMuse 集成
├── novaic-quic-service/         # QUIC relay 服务
├── docs/                        # 文档
│   ├── design/                  # 系统设计文档
│   ├── device/                  # 设备管理相关
│   ├── vnc/                     # VNC 连接相关
│   ├── ota/                     # OTA 热更新相关
│   ├── p2p/                     # P2P 连接相关
│   ├── research/                # 技术调研/分析
│   ├── review/                  # 代码审查/报告
│   └── misc/                    # 其他文档
├── scripts/                     # 构建/部署/运维脚本
└── examples/                    # 示例项目
```

## Getting Started

```bash
# Clone with all submodules
git clone --recurse-submodules git@github.com:chriswangcq/novaic.git

# If already cloned, init submodules
git submodule update --init --recursive
```

## Submodules

All services are independent Git repos managed as submodules. See `.gitmodules` for details.
