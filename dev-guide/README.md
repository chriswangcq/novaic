# NovAIC Subagent 开发指南

> 本目录包含执行具体开发任务时需要的参考文档。
> 
> **你是 Subagent**：你的职责是接受技术负责人分配的具体任务，执行任务，然后汇报结果。

---

## 快速索引

| 任务类型 | 参考文档 |
|----------|----------|
| 调试问题 | [debugging-guide.md](./debugging-guide.md) |
| 修改前后端交互 | [frontend-backend-interaction.md](./frontend-backend-interaction.md) |
| 修改 Execute Log | [execute-log-flow.md](./execute-log-flow.md) |
| Build 项目 | [build-process.md](./build-process.md) |
| 冒烟测试 | [smoke-test.md](./smoke-test.md) |

---

## Subagent 工作流程

```
1. 接受任务
   ↓
2. 阅读相关文档（本目录）
   ↓
3. 执行任务
   ↓
4. 验证结果
   ↓
5. 汇报给技术负责人
```

---

## 汇报格式模板

完成任务后，使用以下格式汇报：

```markdown
## 修复/完成内容

**问题**：[简述问题]

**原因**：[根因分析]

**修复**：[修改了什么文件，改了什么]

**验证**：[如何验证修复生效]
```

---

## 常用路径速查

| 内容 | 路径 |
|------|------|
| 数据库 | `~/Library/Application Support/com.novaic.app/gateway.db`<br>`~/Library/Application Support/com.novaic.app/runtime_orchestrator.db`<br>`~/Library/Application Support/com.novaic.app/queue.db` |
| 日志 | `~/Library/Application Support/com.novaic.app/logs/` |
| 后端代码 | `novaic-backend/` |
| 前端代码 | `novaic-app/src/` |
| Gateway 主文件 | `novaic-backend/main_gateway.py` |
| 前端 Store | `novaic-app/src/store/index.ts` |
| 前端 API | `novaic-app/src/services/api.ts` |

---

## 重要提醒

1. **修改代码后**：检查 TypeScript 类型是否正确
2. **修改 API 后**：确保前后端参数名一致
3. **修改数据库后**：检查 schema 版本和迁移逻辑
4. **完成后**：告诉技术负责人需要 build 还是可以直接生效
