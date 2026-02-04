# 开发指南索引

## 快速开始

1. **[smoke-test.md](./smoke-test.md)** - 冒烟测试流程（首次必读）
2. **[run-dev.sh](./run-dev.sh)** - 快速启动所有服务的脚本

## 架构文档

- **[architecture.md](./architecture.md)** - 系统整体架构
- **[services-architecture.md](./services-architecture.md)** - 服务间交互详解
- **[state-machines.md](./state-machines.md)** - Saga状态机详解
- **[task-queue-v2-design.md](./task-queue-v2-design.md)** - Task Queue v2设计

## 调试指南

- **[debugging-dev.md](./debugging-dev.md)** - 开发环境调试
- **[debugging-mcp.md](./debugging-mcp.md)** - MCP相关调试
- **[troubleshooting.md](./troubleshooting.md)** - 常见问题排查

## 修复记录

- **[fixes-20260204.md](./fixes-20260204.md)** - 2026-02-04 完整修复记录
  - ✅ Watchdog原子claim
  - ✅ Agent model参数保存
  - ✅ LLM配置从DB读取
  - ✅ SQLite cursor管理（错误减少92%）
  - ✅ MCP async/sync修复
  - ✅ 完整AI回复流程验证通过

## 案例研究

- **[case-study-agent-id-mismatch.md](./case-study-agent-id-mismatch.md)** - Agent ID不匹配问题分析

## Saga设计

- **[saga-design-principles.md](./saga-design-principles.md)** - Saga设计原则
- **[saga-v2-migration-plan.md](./saga-v2-migration-plan.md)** - Saga v2迁移计划

## 工具列表

- **[tool_list.md](./tool_list.md)** - 可用工具清单

## 构建相关

- **[build-process.md](./build-process.md)** - 构建流程说明

---

## 今日要点（2026-02-04）

### ✅ 全同步架构验证通过

完整流程：
```
用户消息 → Watchdog claim → sent 
  → ReactThink saga → LLM调用(kimi-k2.5) 
  → ReactActions saga → chat_reply工具 
  → AI消息写入DB → 前端显示
```

**响应时间**: 5秒内完成  
**成功率**: 100%  
**稳定性**: cursor错误减少92%

详见 [fixes-20260204.md](./fixes-20260204.md)

### 🚀 快速测试命令

```bash
# 1. 启动所有服务
cd /Users/wangchaoqun/novaic && ./dev-guide/run-dev.sh all

# 2. 初始化DB配置（首次）
# 参见 fixes-20260204.md 的"DB配置初始化流程"部分

# 3. 运行完整测试
# 参见 fixes-20260204.md 的"完整端到端测试"部分
```
