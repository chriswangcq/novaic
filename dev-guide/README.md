# NovAIC 开发调试指南

本目录包含开发和调试相关的文档和脚本。

## 目录结构

```
dev-guide/
├── README.md                    # 本文件
├── architecture.md              # 架构说明
├── debugging-mcp.md             # MCP 调试心得
├── run-dev.sh                   # 开发环境启动脚本
└── troubleshooting.md           # 常见问题排查
```

## 快速开始

```bash
# 启动开发环境（Gateway + MCP Gateway + Master + Worker）
./dev-guide/run-dev.sh

# 或分步启动
./dev-guide/run-dev.sh gateway      # 只起 Gateway
./dev-guide/run-dev.sh mcp-gateway  # 只起 MCP Gateway
./dev-guide/run-dev.sh master       # 只起 Master
./dev-guide/run-dev.sh worker       # 只起 Worker
```

## 相关文档

- [架构说明](./architecture.md) - Backend 四组件架构
- [MCP 调试心得](./debugging-mcp.md) - MCP 相关问题排查
- [常见问题](./troubleshooting.md) - FAQ 和解决方案
