# 开发指南索引

## 快速开始

1. **[smoke-test.md](./smoke-test.md)** - 冒烟测试流程（首次必读）
2. **[run-dev.sh](./run-dev.sh)** - 快速启动所有服务的脚本

## 调试指南

- **[debugging-guide.md](./debugging-guide.md)** - 开发调试指南

## 修复记录

- **[fixes-20260204.md](./fixes-20260204.md)** - 2026-02-04 完整修复记录
  - ✅ Watchdog原子claim
  - ✅ Agent model参数保存
  - ✅ LLM配置从DB读取
  - ✅ SQLite cursor管理（错误减少92%）
  - ✅ Tools Server async/sync修复
  - ✅ 完整AI回复流程验证通过

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
