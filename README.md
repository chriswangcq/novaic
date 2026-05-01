# NovAIC

AI-powered agent platform with mobile (iOS/Android) and desktop (macOS/Windows/Linux) clients.

## Architecture

```
novaic/
├── novaic-app/                  # Tauri v2 前端 (React + TypeScript)
├── novaic-agent-runtime/        # Agent 运行时
├── novaic-gateway/              # API 网关
├── novaic-control-plane/        # 控制面板
├── novaic-contracts/            # 共享协议/类型定义
├── novaic-shared-kernel/        # 共享核心库
├── novaic-shared-runtime-common/# 共享运行时公共库
├── novaic-storage-a/            # 存储服务 A
├── novaic-mcp-vmuse/            # MCP VMuse 集成
├── novaic-quic-service/         # QUIC relay 服务
├── docs/                        # 父仓文档（HANDOVER 纲要：README.md、architecture/、reference/、runbooks/）
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
