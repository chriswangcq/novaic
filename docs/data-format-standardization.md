# NovAIC 数据格式标准化方案

> **版本**: v1.0  
> **日期**: 2026-02-07  
> **状态**: 草案 (Draft)  

---

## 📋 背景

根据 2026-02-07 的系统性调查，项目存在以下问题：

1. **格式不统一**：`{success, result}` vs `{status, ...}` vs 直接返回
2. **嵌套过深**：`vmuse_adapter.py` 存在双层/三层嵌套
3. **错误处理不一致**：`error` 字段位置和格式不统一
4. **Multimodal 数据混乱**：`_mcp_content` 嵌套位置不一致

### 影响

- 🐛 **功能性 Bug**：Multimodal 图片识别失败（Token 超限）
- 🔧 **可维护性差**：新开发者需要猜测不同端点的返回格式
- 🧪 **测试困难**：需要为不同格式编写不同的测试用例

---

## 标准格式定义

### 成功响应

```typescript
{
  "success": true,
  "result": T  // 实际数据
}
```

### 失败响应

```typescript
{
  "success": false,
  "error": string | ErrorObject
}
```

### Multimodal 数据

```typescript
{
  "success": true,
  "result": { /* metadata */ },
  "_mcp_content": [
    {
      "type": "image",
      "data": "base64...",
      "mimeType": "image/png"
    }
  ]
}
```

---

## 分阶段迁移计划

### 阶段 1：修复 P0 关键问题（2-3 天）✅

**已完成**：
- ✅ 修复 `context.py` 中的嵌套解包逻辑
- ✅ Screenshot 工具图片正确识别
- ✅ LLM Token 不再超限

**待完成**：
- [ ] 修复 `vmuse_adapter.py` 双层嵌套（移除二次包装）
- [ ] 修复 `_mcp_content` 嵌套位置

### 阶段 2：统一工具返回格式（3-5 天）

- [ ] `playwright_helper.py` 使用 `{success, result}` 格式
- [ ] vmcontrol Rust API 统一格式
- [ ] 所有内置工具格式审查

### 阶段 3：统一 API 端点格式（5-7 天）

- [ ] 创建响应装饰器
- [ ] 迁移 Gateway API
- [ ] 前端兼容层实现

### 阶段 4：清理与优化（2-3 天）

- [ ] 移除兼容层
- [ ] 性能优化
- [ ] 文档更新

---

## 相关文档

- **调查报告**：由 subagent 39fab1fa 生成的完整调查报告
- **技术指南**：`tech-lead-guide/data-consistency-and-cascade-deletion.md`

---

**最后更新**: 2026-02-07  
**批准状态**: 待批准
